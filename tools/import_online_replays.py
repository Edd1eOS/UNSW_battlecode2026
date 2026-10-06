"""Import only fixed selected official replay downloads, then audit offline.

Never starts matches or executes downloaded code. ZIP members are read by their
ZipInfo; only a flat M<ID>.replay name in the immutable selection is accepted.
Conflicting bytes remain a conflict, never a replacement game. The original
online UI fixture is read without modification. Raw output stays in test-results.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import statistics
from typing import Any
import zipfile

try:
    from .audit_online import (REASONS, _viewer_default, audit_match, audit_ui, load_replay, manifest_items,
                               selected_table_outcome)
    from .trajectory_metrics import analyze_replay
    from .panel_trajectory import executed_details, phase_metrics
except ImportError:
    from audit_online import (REASONS, _viewer_default, audit_match, audit_ui, load_replay, manifest_items,
                              selected_table_outcome)
    from trajectory_metrics import analyze_replay
    from panel_trajectory import executed_details, phase_metrics

ROOT = Path(__file__).resolve().parents[1]
REPLAY_NAME = re.compile(r"M(\d+)\.replay")
DOWNLOAD_REPLAY_NAME = re.compile(r"M(\d+)(?: \(\d+\))?\.replay")
SERIES_NAME = re.compile(r"battle-M(\d+)-replays(?: \(\d+\))?\.zip")
MAX_REPLAY_BYTES = 256 * 1024 * 1024
SCORE_KEYS = ("queenLength", "dragonCount", "longestDragon", "totalLength")
SOURCE_EXTENSIONS = {".cpp", ".hpp", ".h", ".toml"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def safe_flat_member(info: zipfile.ZipInfo, pattern=REPLAY_NAME) -> bool:
    name = info.filename
    mode = info.external_attr >> 16
    return (bool(pattern.fullmatch(name)) and not info.is_dir()
            and not PurePosixPath(name).is_absolute() and "\\" not in name
            and "/" not in name and not stat.S_ISLNK(mode)
            and not (info.flag_bits & 1) and 0 <= info.file_size <= MAX_REPLAY_BYTES
            and (not info.file_size or info.compress_size > 0)
            and info.file_size <= max(info.compress_size, 1) * 1000)


def scan_downloads(directory: Path, selected_ids: set[int]):
    """Return byte candidates with all duplicate origins; no ZIP extraction."""
    candidates = defaultdict(list)
    inventory, issues, ignored = [], [], []
    for path in sorted(directory.iterdir(), key=lambda p: p.name):
        direct, series = DOWNLOAD_REPLAY_NAME.fullmatch(path.name), SERIES_NAME.fullmatch(path.name)
        if not path.is_file() or path.is_symlink() or not (direct or series):
            continue
        entry = {"filename": path.name, "bytes": path.stat().st_size,
                 "filesystem_modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}
        try:
            raw = path.read_bytes()
            entry["sha256"] = sha(raw)
            inventory.append(entry)
            if direct:
                identity = int(direct[1])
                if identity not in selected_ids:
                    ignored.append({"filename": path.name, "match_id": identity, "reason": "not in fixed selection"})
                elif len(raw) > MAX_REPLAY_BYTES:
                    issues.append({"filename": path.name, "reason": "oversized replay"})
                else:
                    candidates[identity].append({"bytes": raw, "provenance": {**entry,
                        "kind": "individual_replay", "replay_sha256": sha(raw)}})
                continue
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for ordinal, info in enumerate(archive.infolist()):
                    name_match = REPLAY_NAME.fullmatch(info.filename)
                    if not safe_flat_member(info):
                        issues.append({"filename": path.name, "member": info.filename, "reason": "rejected unsafe or unexpected ZIP member"})
                        continue
                    identity = int(name_match[1])
                    if identity not in selected_ids:
                        ignored.append({"filename": path.name, "member": info.filename,
                                        "match_id": identity, "reason": "not in fixed selection"})
                        continue
                    try:
                        body = archive.read(info)  # ZipInfo keeps duplicate names distinct and checks CRC.
                        candidates[identity].append({"bytes": body, "provenance": {**entry,
                            "kind": "series_zip_member", "member": info.filename, "member_index": ordinal,
                            "replay_bytes": len(body), "replay_sha256": sha(body),
                            "source_page_url": f"https://game.battlecode.au/battles/{series[1]}",
                            "source_page_basis": "series ID in visible UI download filename; no authenticated URL stored"}})
                    except Exception as error:
                        issues.append({"filename": path.name, "member": info.filename, "reason": str(error)})
        except Exception as error:
            issues.append({"filename": path.name, "reason": str(error)})
    return candidates, inventory, issues, ignored


def import_candidates(candidates, selected_ids: list[int], output: Path):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for identity in selected_ids:
        entries = candidates.get(identity, [])
        digests = sorted({x["provenance"]["replay_sha256"] for x in entries})
        row = {"match_id": identity, "source_count": len(entries), "distinct_sha256": digests,
               "sources": [x["provenance"] for x in entries], "import_status": "missing"}
        destination = output / f"M{identity}.replay"
        if len(digests) > 1:
            row["import_status"] = "conflict"
        elif entries:
            body = entries[0]["bytes"]
            if destination.exists() and sha(destination.read_bytes()) != digests[0]:
                row["import_status"] = "conflict_with_existing_output"
                row["existing_sha256"] = sha(destination.read_bytes())
            else:
                if not destination.exists():
                    destination.write_bytes(body)
                row.update(import_status="imported", replay_path=destination.name,
                           replay_sha256=digests[0], replay_bytes=len(body),
                           identical_duplicate_sources=max(0, len(entries) - 1))
        rows.append(row)
    return rows


def source_proof(source_zip: Path | None, archived: Path | None, submission_id: int,
                 link_confirmed: bool = False):
    if source_zip is None:
        return {"available": False, "source_bytes_verified": False}
    raw_zip = source_zip.read_bytes()
    proof = {"available": True, "zip_filename": source_zip.name,
             "zip_sha256": sha(raw_zip), "zip_bytes": len(raw_zip),
             "submission_id": submission_id, "visible_download_link_confirmed": link_confirmed,
             "source_url": f"https://game.battlecode.au/submissions/{submission_id}/download",
             "link_observation": "Root agent observed Active v14 and the exact Download v14 Guard v66 link, then used link.downloadMedia" if link_confirmed else None,
             "source_bytes_verified": False, "members": []}
    files = {}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if (len(path.parts) != 1 or path.is_absolute() or "\\" in info.filename
                    or path.suffix not in SOURCE_EXTENSIONS or info.is_dir()
                    or stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1
                    or info.file_size > 8 * 1024 * 1024 or info.filename in files):
                raise ValueError("Unsafe, duplicate or unexpected source ZIP member; source was not extracted")
            files[info.filename] = archive.read(info)
    proof["source_bundle_sha256"] = sha(b"".join(name.encode() + body for name, body in sorted(files.items())))
    archived_files = {p.name: p.read_bytes() for p in archived.iterdir()
                      if p.is_file() and p.suffix in SOURCE_EXTENSIONS} if archived else {}
    for name, body in sorted(files.items()):
        proof["members"].append({"name": name, "bytes": len(body), "sha256": sha(body),
                                 "archived_byte_match": name in archived_files and body == archived_files[name]})
    proof["archived_source_bundle_sha256"] = sha(b"".join(name.encode() + body for name, body in sorted(archived_files.items()))) if archived else None
    proof["archived_file_set_matches"] = set(files) == set(archived_files) if archived else None
    proof["source_bytes_verified"] = bool(link_confirmed and archived and proof["archived_file_set_matches"]
                                            and all(x["archived_byte_match"] for x in proof["members"]))
    proof["scope"] = "ZIP/source byte hashes only; no source text exported, extraction, compilation, execution or upload"
    return proof


def frozen_inputs(selection_path: Path, ui_fixture: Path, our_team_id: int, platform_version: int):
    raw = selection_path.read_bytes()
    selection = json.loads(raw.decode("utf-8-sig"))
    bundle = json.loads(gzip.decompress(ui_fixture.read_bytes()))
    if sha(raw) != bundle["provenance"]["selection_file_original_sha256"] or selection != bundle["selection"]:
        raise ValueError("Selection is not the immutable captured UI fixture selection")
    selected = manifest_items(selection)
    ids = [x["match_id"] for x in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate selected match IDs")
    exports = bundle["ui_exports"]
    if [x["match_id"] for x in exports] != ids:
        raise ValueError("Fixed UI export order/IDs differ from selected matches")
    sources, audits = {}, {}
    for item in exports:
        encoded = item["raw_json_utf8"].encode("utf-8")
        if sha(encoded) != item["original_sha256"]:
            raise ValueError("Captured UI export hash differs")
        identity = item["match_id"]
        source = json.loads(item["raw_json_utf8"].lstrip("\ufeff"))
        source["input_sha256"] = item["original_sha256"]
        sources[identity] = source
        audits[identity] = audit_ui(source, {"match_id": identity, "our_team_id": our_team_id,
                                           "platform_version": platform_version})
    return selection, selected, sources, audits, {"selection_sha256": sha(raw),
        "ui_fixture_sha256": sha(ui_fixture.read_bytes())}


def position(value):
    return (int(value["x"]), int(value["y"])) if isinstance(value, dict) else tuple(map(int, value))


def initial_checks(data):
    expected = {int(d["id"]): d for d in data["initial_dragons"]}
    recorded = {}
    for event in data["events"]:
        if event.get("type") == "roundStart":
            break
        if event.get("type") == "dragonUpdate":
            identity = int(event["id"])
            if identity in recorded:
                raise ValueError("Duplicate initialization body update")
            recorded[identity] = event
    if set(expected) != set(recorded):
        raise ValueError("Embedded-map initial IDs differ from initialization updates")
    for identity, dragon in expected.items():
        body = dragon["body"]
        if not body or (position(body[0]), position(body[-1])) != (position(recorded[identity]["head"]), position(recorded[identity]["tail"])):
            raise ValueError("Embedded-map initial head/tail differs from initialization event")
    return {"verified": True, "dragon_count": len(expected),
            "basis": "Embedded map declaration order, explicit teams and all initial head/tail updates agree"}


def validate_ui(data, core, detail, audit, ui, submission_id):
    issues = []
    if ui["warnings"]:
        issues.extend("UI: " + s for s in ui["warnings"])
    matching = [team for team in "AB" if str(data["teams"][team].get("botId")) == str(submission_id)]
    if len(matching) != 1:
        raise ValueError("Replay header must uniquely identify our expected submission botId")
    ours = matching[0]
    our_column = ui["our_ui_column"]
    mapping = {ours: our_column, "B" if ours == "A" else "A": "B" if our_column == "A" else "A"}
    result = data["result"]
    if not result.get("terminated"):
        issues.append("Replay has no formal terminal")
    if int(data["seed"]) != int(ui["seed"], 0):
        issues.append("Replay seed differs from fixed UI")
    map_name = next((line[9:].strip() for line in data["map"].splitlines() if line.startswith("MAP_NAME ")), None)
    normalized = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").casefold())
    if normalized(map_name) != normalized(ui["map"]):
        issues.append(f"Embedded map name {map_name!r} differs from UI {ui['map']!r}")
    if core["trajectory"][-1]["round"] + 1 != ui["last_round"]:
        issues.append("Last official zero-based round +1 differs from UI terminal round")
    expected_winner = next((team for team, column in mapping.items() if column == ui["result"]["winner"]), None)
    if result["winner"] != expected_winner or result["endReason"] != ui["result"]["endReason"]:
        issues.append("Formal winner/end reason differs from fixed UI")
    for team, column in mapping.items():
        if any(int(result["team" + team][key]) != int(ui["result"]["team" + column][key]) for key in SCORE_KEYS):
            issues.append(f"Terminal {team} score differs from mapped UI column {column}")
        queens = [d for d in detail["dragons"] if d["team"] == team and d["is_queen"]]
        if len(queens) != 1:
            issues.append(f"{team}: embedded map does not identify one fixed Queen")
            continue
        queen = queens[0]
        death = queen["death"]
        if (death["round"] + 1 if death else None) != ui["queen_death_rounds"][column]:
            issues.append(f"{team}: Queen death round differs from fixed UI")
        filtered = [d for d in ui["filtered_queen_events"] if d["team"] == column]
        if filtered:
            if (len(filtered) != 1 or not death or filtered[0]["id"] != queen["id"]
                    or REASONS.get(death["reason"]) != filtered[0]["reason"]):
                issues.append(f"{team}: filtered Queen identity/reason differs from replay")
        # The viewer's historical score is sampled at round boundaries. A unit
        # can grow and die within a round without appearing in that UI peak.
        peak = max(core["initial"]["scores"][team]["longest_dragon"],
                   *(frame["scores"][team]["longest_dragon"] for frame in core["trajectory"]))
        if ui["team_longest_so_far"][column] is not None and peak != ui["team_longest_so_far"][column]:
            issues.append(f"{team}: initial/end-of-round peak differs from UI Longest so far")
        for key in ("deaths", "death_wall", "death_self_body", "death_other_body", "death_head_collision", "death_invalid_action", "splits"):
            if key in ui["teams"][column] and audit["teams"][team].get(key, 0) != ui["teams"][column][key]:
                issues.append(f"{team}: cumulative {key} differs from UI")
    return {"verified": not issues, "issues": issues, "engine_team": ours,
            "engine_to_ui_column": mapping, "map_name": map_name,
            "identity_basis": "Unique replay botId, fixed captured UI identity, seed, terminal, Queen events and cumulative counts"}


def dependency_hashes():
    files = {name: sha((ROOT / "tools" / name).read_bytes()) for name in
             ("import_online_replays.py", "audit_online.py", "trajectory_metrics.py", "panel_trajectory.py")}
    files["installed_official_replay_viewer_vsix"] = sha(_viewer_default().read_bytes())
    return files


def analyze_one(path, ui, row, proof, submission_id, dependencies, refresh=False):
    provenance = {"replay_sha256": sha(path.read_bytes()), "ui_sha256": ui["input_sha256"],
                  "source_zip_sha256": proof.get("zip_sha256"),
                  "source_bundle_sha256": proof.get("source_bundle_sha256"),
                  "source_bytes_verified": proof["source_bytes_verified"], "dependencies": dependencies}
    cached_path = path.with_suffix(".analysis.json")
    if cached_path.exists() and not refresh:
        try:
            cached = json.loads(cached_path.read_text(encoding="utf-8"))
            if all(cached.get("provenance", {}).get(key) == value for key, value in provenance.items()):
                return cached, True
        except (OSError, ValueError):
            pass  # A partial previous cache is not evidence; decode the intact raw again.
    data = load_replay(path)
    initial = initial_checks(data)
    own = [t for t in "AB" if str(data["teams"][t].get("botId")) == str(submission_id)]
    if len(own) != 1:
        raise ValueError("Replay botId does not uniquely identify submission")
    core = analyze_replay(data)
    detail = executed_details(data, core)
    audit = audit_match(data, {"match_id": row["match_id"], "our_team": own[0],
        "submission": submission_id, "submission_verified": True,
        "source_hash": proof.get("source_bundle_sha256") if proof["source_bytes_verified"] else None,
        "ranked": ui["ranked"], "opponent": ui["opponent"], "complete": True,
        "version_evidence": "Captured v14 UI plus unique official replay botId and separately observed source download"})
    validation = validate_ui(data, core, detail, audit, ui, submission_id)
    audit.update(platform_version=ui["platform_version"], platform_version_verified=ui["platform_version_verified"],
                 source_bytes_verified=proof["source_bytes_verified"], map=ui["map"], seed=data["seed"],
                 selected_table_row=row["selected_table_row"],
                 selected_table_outcome=selected_table_outcome(row["selected_table_row"], ui["our_team_id"]))
    death_keys = ("round", "event_index", "turn_id", "turn_serial", "id", "team", "reason",
                  "last_recorded_length", "is_queen", "was_longest", "was_unique_longest",
                  "longest_length_loss", "erased_own_lead_immediately", "reversed_own_lead_immediately")
    record = {"schema_version": 1, "match_id": row["match_id"], "provenance": {**provenance,
        "decoder_bundle_sha256": data.get("decoder_bundle_sha256")}, "replay_teams": data["teams"],
        "initial_validation": initial, "ui_validation": validation, "quality": core["quality"],
        "audit": audit, "initial": core["initial"], "final": core["final"],
        "resources": core["resources"], "advantage": core["advantage"], "trajectory": core["trajectory"],
        "deaths": [{k: d[k] for k in death_keys if k in d} for d in core["deaths"]],
        "splits": core["splits"], "gross_ledger_verified": detail["gross_ledger_verified"],
        "gross_ledger_issues": detail["gross_ledger_issues"], "gross_resources": detail["gross_resources"],
        "workers": detail["workers"], "queens": [d for d in detail["dragons"] if d["is_queen"]],
        "queen_state_phases": phase_metrics(core, detail, own[0]),
        "round_numbering": "trajectory/deaths use official zero-based rounds; audit/UI human rounds add one",
        "strategy_inferences": [], "measurement_limits": [
            "Observed terminal and event effects do not prove the strategic root cause or a better counterfactual action.",
            "Worker peak includes initial/split inherited length; net update growth excludes transfers.",
            "Food/payment remains null unless all correlated execution ledgers pass.",
            "Anonymous opponent replay headers do not independently verify opponent submission or source."]}
    # Decoder digest is evidence, not an additional cache input; validate all actual inputs above.
    write_json(cached_path, record)
    return record, False


def compact_metrics(record):
    ours = record["ui_validation"]["engine_team"]
    opponent = "B" if ours == "A" else "A"
    own = record["final"]["scores"][ours]
    queen = next(d for d in record["queens"] if d["team"] == ours)
    queen_head_pairs = [p for p in record["audit"]["head_collision_pairs"]
                        if queen["id"] in p["ids"] and queen["death"]
                        and p["round"] == queen["death"]["round"] + 1]
    queen_head_relation = queen_head_pairs[0]["kind"] if len(queen_head_pairs) == 1 else None
    own_deaths = [d for d in record["deaths"] if d["team"] == ours]
    return {"match_id": record["match_id"], "our_team": ours,
        "outcome": record["audit"]["outcome"], "score_axis": record["audit"]["direct_cause"]["score_axis"],
        "map": record["audit"]["map"], "opponent": record["audit"]["opponent"],
        "submission_verified": True, "source_bytes_verified": record["provenance"]["source_bytes_verified"],
        "whole_match_verified": record["quality"]["complete_match_verified"] and record["ui_validation"]["verified"],
        "gross_ledger_verified": record["gross_ledger_verified"], "queen_alive": own["queen_length"] > 0,
        "queen_length": own["queen_length"], "queen_death": queen["death"],
        "queen_peak_length": queen["peak_length"], "queen_net_update_growth": queen["net_update_growth"],
        "queen_head_collision_relation": queen_head_relation,
        "terminal_longest": own["longest_dragon"], "opponent_terminal_longest": record["final"]["scores"][opponent]["longest_dragon"],
        "historical_round_longest": max(record["initial"]["scores"][ours]["longest_dragon"],
            *(frame["scores"][ours]["longest_dragon"] for frame in record["trajectory"])),
        "historical_event_longest": max(queen["peak_length"], record["workers"][ours]["recorded_peak_worker"]),
        "unique_longest_deaths": [d for d in own_deaths if d["was_unique_longest"]],
        "resources": record["resources"][ours], "gross_resources": record["gross_resources"][ours],
        "workers": record["workers"][ours], "event_counts": record["audit"]["teams"][ours],
        "continuous_lead": record["advantage"]["by_team"][ours]}


def run(args):
    output = args.out.resolve()
    if not output.is_relative_to(ROOT / "test-results"):
        raise ValueError("Raw output must remain within this workspace's ignored test-results directory")
    selection, selected, _, uis, fixed = frozen_inputs(args.selection, args.ui_fixture, args.our_team_id, args.platform_version)
    ids = [x["match_id"] for x in selected]
    if args.expected_count is not None and len(ids) != args.expected_count:
        raise ValueError("Fixed selected count differs from expected count")
    proof = source_proof(args.source_zip, args.archive_source, args.submission_id, args.source_link_confirmed)
    candidates, inventory, scan_issues, ignored = scan_downloads(args.download_dir, set(ids))
    rows = import_candidates(candidates, ids, output)
    candidates.clear()  # release download bytes before whole-match reconstruction
    dependencies = dependency_hashes()
    allowed = set(ids[:args.limit] if args.limit is not None else ids)
    metrics, errors, cache_hits = [], [], 0
    for index, (row, item) in enumerate(zip(rows, selected)):
        row["audit_status"] = "missing_raw" if row["import_status"] == "missing" else "not_audited"
        if row["import_status"] != "imported" or row["match_id"] not in allowed:
            continue
        try:
            record, cached = analyze_one(output / row["replay_path"], uis[row["match_id"]], item,
                                          proof, args.submission_id, dependencies, args.refresh)
            cache_hits += cached
            metric = compact_metrics(record)
            row.update(audit_status="verified" if metric["whole_match_verified"] else "validation_issue",
                       analysis_path=f"M{row['match_id']}.analysis.json", metrics=metric,
                       validation_issues=record["ui_validation"]["issues"] + record["quality"]["issues"],
                       gross_ledger_issues=record["gross_ledger_issues"])
            metrics.append(metric)
        except Exception as error:
            row.update(audit_status="failed", error=f"{type(error).__name__}: {error}")
            errors.append({"match_id": row["match_id"], "error": row["error"]})
        if (index + 1) % 5 == 0:
            print(json.dumps({"selected_position": index + 1, "audited": len(metrics), "failures": len(errors)}, ensure_ascii=False), flush=True)
    verified = [x for x in metrics if x["whole_match_verified"]]
    summary = {"selected": len(ids), "fixed_UI_records": len(uis),
        "import_status": dict(Counter(x["import_status"] for x in rows)),
        "audit_status": dict(Counter(x["audit_status"] for x in rows)), "audited": len(metrics),
        "whole_match_verified": len(verified), "gross_ledger_verified": sum(x["gross_ledger_verified"] for x in verified),
        "submission_id_verified": sum(x["submission_verified"] for x in verified),
        "source_bytes_verified": sum(x["source_bytes_verified"] for x in verified),
        "verified_outcomes": dict(Counter(x["outcome"] for x in verified)),
        "verified_loss_score_axes": dict(Counter(x["score_axis"] for x in verified if x["outcome"] == "loss")),
        "our_queen_alive": sum(x["queen_alive"] for x in verified),
        "our_terminal_longest_median": statistics.median(x["terminal_longest"] for x in verified) if verified else None,
        "cache_hits": cache_hits, "decoder_or_audit_failures": len(errors), "scan_issues": len(scan_issues),
        "complete_selected_raw_audit": len(verified) == len(ids),
        "scope": "Fixed online discovery sample; no candidate matches or strength validation"}
    summary["our_queen_death_codes"] = dict(Counter(x["queen_death"]["reason"] for x in verified if x["queen_death"]))
    summary["our_queen_head_collision_relations"] = dict(Counter(x["queen_head_collision_relation"] or "unresolved"
        for x in verified if x["queen_death"] and x["queen_death"]["reason"] == "H"))
    summary["our_recorded_head_deaths"] = {
        key: sum(x["event_counts"].get(key, 0) for x in verified)
        for key in ("death_head_collision", "friendly_head_deaths", "enemy_head_deaths")}
    summary["our_queen_split_length_transferred"] = sum(x["resources"]["queen_length_transferred_by_split"] for x in verified)
    summary["queen_split_games"] = sum(x["resources"]["queen_length_transferred_by_split"] > 0 for x in verified)
    summary["dependencies_unchanged_during_run"] = dependencies == dependency_hashes()
    report = {"schema_version": 1, "generated_utc": utc_now(), "summary": summary,
        "selection": selection, "fixed_evidence": fixed, "source_proof": proof,
        "analyzer_dependencies": dependencies,
        "download_inventory": inventory, "scan_issues": scan_issues, "ignored_nonselected": ignored,
        "failures": errors, "matches": rows, "limits": [
            "Only selected IDs were imported; missing/conflicting/failed games were not replaced.",
            "Current observed raw provenance extends the fixed UI evidence; the UI fixture remains untouched.",
            "Different series and repeated opponents remain correlated discovery evidence.",
            "No automatic strategic intent, feeding or opponent private-code inference."]}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_json(output / f"import-audit-{stamp}.json", report)
    write_json(output / "index.json", report)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=ROOT / "test-results/online100-selection.json")
    parser.add_argument("--ui-fixture", type=Path, default=ROOT / "tests/fixtures/oct6-online100-ui.json.gz")
    parser.add_argument("--out", type=Path, default=ROOT / "test-results/online100-raw")
    parser.add_argument("--expected-count", type=int, default=100)
    parser.add_argument("--limit", type=int, help="Audit only the first N fixed selection positions; preserve all records")
    parser.add_argument("--our-team-id", type=int, default=1035)
    parser.add_argument("--platform-version", type=int, default=14)
    parser.add_argument("--submission-id", type=int, default=15719)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--archive-source", type=Path)
    parser.add_argument("--source-link-confirmed", action="store_true",
                        help="Trusted root observation of exact official v14 submission download link")
    parser.add_argument("--refresh", action="store_true", help="Ignore matching per-game audit cache")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error("--limit cannot be negative")
    run(args)


if __name__ == "__main__":
    main()
