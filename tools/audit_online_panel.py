"""Audit an explicitly selected external online panel; never starts matches.

Uses official replay downloads plus optional terminal UI exports. Raw completeness,
UI coverage and gross-ledger coverage have separate denominators. No inferred IDs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

try:
    from .audit_online import audit_match, audit_ui, load_replay, manifest_items
    from .import_online_replays import (ROOT, compact_metrics, dependency_hashes, import_candidates,
                                      initial_checks, scan_downloads, sha, validate_ui, write_json)
    from .panel_trajectory import executed_details, phase_metrics
    from .trajectory_metrics import analyze_replay
except ImportError:
    from audit_online import audit_match, audit_ui, load_replay, manifest_items
    from import_online_replays import (ROOT, compact_metrics, dependency_hashes, import_candidates,
                                     initial_checks, scan_downloads, sha, validate_ui, write_json)
    from panel_trajectory import executed_details, phase_metrics
    from trajectory_metrics import analyze_replay


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def selected_matches(manifest):
    if "series" not in manifest:
        items = manifest_items(manifest)
    else:
        items = []
        for series in manifest["series"]:
            if "matches" in series:
                observed = series["matches"]
            else:
                observed = []
                for link in series["links"]:
                    match_id = re.search(r"/battles/(\d+)(?:$|[/?#])", link.get("href", ""))
                    if not match_id:
                        raise ValueError("Actual series link does not identify a match")
                    verdict = re.search(r"([WLDT])(?:\([^)]*\))?\s*$", link.get("text", ""))
                    observed.append({"match_id": int(match_id[1]), "selected_game_link": link,
                                     "outcome": {"W": "win", "L": "loss", "D": "draw", "T": "draw"}.get(verdict[1]) if verdict else None})
            for match in observed:
                match = {"match_id": match} if isinstance(match, int) else dict(match)
                items.append({**{k: v for k, v in series.items() if k not in ("matches", "links")}, **match})
    rows = []
    for item in items:
        row = dict(item)
        identity = row.get("match_id", row.get("id"))
        if identity is None or str(identity) != str(int(identity)) or int(identity) < 1:
            raise ValueError("Every selected match needs its actual positive integer ID")
        row["match_id"] = int(identity)
        row.setdefault("selected_table_row", {})
        rows.append(row)
    if not rows or len({r["match_id"] for r in rows}) != len(rows):
        raise ValueError("Selection is empty or contains duplicate match IDs")
    return rows


def verify_source_record(proof_path, freeze_path, submission, platform_version):
    """Verify the trusted visible-download record against immutable local members.

    No source import/extraction/execution. The source-record JSON is a root-observed
    provenance statement; an optional actual ZIP may be independently checked by
    the earlier importer. Candidate source hash here uses external_panel's frozen
    canonical path/hash/size record, not compare.py's filename+bytes method.
    """
    raw = proof_path.read_bytes()
    proof = json.loads(raw.decode("utf-8-sig"))
    freeze_raw = freeze_path.read_bytes()
    freeze = json.loads(freeze_raw.decode("utf-8-sig"))
    if proof["submission_id"] != submission or proof["platform_version"] != platform_version:
        raise ValueError("Submission proof does not match requested candidate/version")
    if (not proof["all_source_members_identical"] or
            proof["local_zip_sha256"] != proof["downloaded_zip_sha256"]):
        raise ValueError("Official downloaded source record does not match the local ZIP")
    members = proof["downloaded_members"]
    records = freeze["source_files"]
    if not records or not any(Path(name).suffix in (".cpp", ".cc", ".c") for name in records):
        raise ValueError("Frozen record contains no candidate source")
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    if sha(canonical) != freeze["source_bundle_sha256"]:
        raise ValueError("Frozen source-record hash disagrees")
    if {Path(name).name for name in records} != set(members):
        raise ValueError("Downloaded and frozen source member sets differ")
    for name, expected in records.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or path.is_symlink():
            raise ValueError("Frozen source member escapes workspace or is symlinked")
        body = path.read_bytes()
        if sha(body) != expected["sha256"] or len(body) != expected["bytes"] or sha(body) != members[path.name]:
            raise ValueError("Frozen source member differs from downloaded proof: " + path.name)
    return {"source_bytes_verified": True, "submission_id": submission, "platform_version": platform_version,
            "source_bundle_sha256": freeze["source_bundle_sha256"],
            "source_hash_method": "SHA256 of canonical sorted JSON of workspace-relative source path -> hash/size records",
            "zip_sha256": proof["downloaded_zip_sha256"], "submission_proof_sha256": sha(raw),
            "freeze_record_sha256": sha(freeze_raw), "wasm_sha256": freeze["wasm_sha256"],
            "downloaded_member_sha256": members,
            "basis": "Trusted root observation of official source download, recorded ZIP equality, frozen local member bytes",
            "limit": "This function does not independently re-download the source or verify the platform binary"}


def read_ui(directory, identity, our_team_id, platform_version, item):
    path = directory / f"{identity}-ui.json"
    if not path.exists():
        return None, {"available": False, "status": "missing", "input_sha256": None}
    body = path.read_bytes()
    data = json.loads(body.decode("utf-8-sig"))
    data["input_sha256"] = sha(body)
    ui = audit_ui(data, {"match_id": identity, "our_team_id": our_team_id, "platform_version": platform_version})
    if item.get("opponent_team_id") is not None:
        links = [link for link in data.get("links", []) if re.search(
            r"/teams/" + re.escape(str(item["opponent_team_id"])) + r"(?:$|[/?#])", link.get("href", ""))]
        if ui["opponent"] not in {link.get("text", "").strip() for link in links}:
            raise ValueError("Actual UI opponent link differs from selected opponent ID")
    if item.get("opponent") is not None and item["opponent"] != ui["opponent"]:
        raise ValueError("Actual UI opponent name differs from selected name")
    if ui["platform_version_verified"] is not True or not ui["terminal_cursor"]:
        raise ValueError("UI does not prove requested platform version and terminal cursor")
    if ui["ranked"]:
        raise ValueError("Preregistered external panel is unranked; actual UI displays Ranked")
    return ui, {"available": True, "status": "captured", "input_sha256": sha(body),
                "platform_version_verified": True}


def reconstruct(path, row, ui, ui_evidence, proof, dependencies, refresh=False):
    key = {"replay_sha256": sha(path.read_bytes()), "ui_sha256": ui_evidence["input_sha256"],
           "selection_row": row, "source_proof": proof, "analyzer_dependencies": dependencies}
    cache_path = path.with_suffix(".analysis.json")
    if cache_path.exists() and not refresh:
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached["cache_inputs"] == key:
                return cached, True
        except (OSError, ValueError, KeyError):
            pass
    data = load_replay(path)
    ours = [team for team in "AB" if str(data["teams"][team].get("botId")) == str(proof["submission_id"])]
    if len(ours) != 1:
        raise ValueError("Replay does not uniquely identify the frozen candidate botId")
    own = ours[0]
    initial = initial_checks(data)
    core = analyze_replay(data)
    detail = executed_details(data, core)
    audit = audit_match(data, {"match_id": row["match_id"], "our_team": own, "submission": proof["submission_id"],
        "submission_verified": True, "source_hash": proof["source_bundle_sha256"], "ranked": False,
        "opponent": ui["opponent"] if ui else row.get("opponent"), "complete": True})
    if ui:
        validation = validate_ui(data, core, detail, audit, ui, proof["submission_id"])
    else:
        validation = {"verified": None, "issues": [], "engine_team": own,
                      "identity_basis": "Official replay botId plus selected actual series ID; terminal UI unavailable"}
    if row.get("outcome") and row["outcome"] != audit["outcome"]:
        validation["issues"].append("Fixed rendered series outcome disagrees with official replay")
        validation["verified"] = False
    map_name = next((line[9:].strip() for line in data["map"].splitlines() if line.startswith("MAP_NAME ")), None)
    audit.update(map=ui["map"] if ui else map_name, seed=data["seed"],
                 platform_version=proof["platform_version"],
                 platform_version_verified=ui["platform_version_verified"] if ui else None,
                 source_bytes_verified=True)
    record = {"schema_version": 1, "match_id": row["match_id"], "cache_inputs": key,
        "provenance": {"source_bytes_verified": True, "replay_sha256": key["replay_sha256"],
                       "source_bundle_sha256": proof["source_bundle_sha256"],
                       "decoder_bundle_sha256": data.get("decoder_bundle_sha256")},
        "replay_teams": data["teams"], "initial_validation": initial, "ui_evidence": ui_evidence,
        "ui_validation": validation, "quality": core["quality"], "audit": audit,
        "initial": core["initial"], "final": core["final"], "resources": core["resources"],
        "advantage": core["advantage"], "trajectory": core["trajectory"],
        "deaths": [{k: v for k, v in d.items() if k not in ("before", "after")} for d in core["deaths"]],
        "splits": core["splits"], "gross_ledger_verified": detail["gross_ledger_verified"],
        "gross_ledger_issues": detail["gross_ledger_issues"], "gross_resources": detail["gross_resources"],
        "workers": {t: {**detail["workers"][t], "highest_recorded_workers": detail["workers"][t]["highest_recorded_workers"][:5]} for t in "AB"},
        "queens": [d for d in detail["dragons"] if d["is_queen"]],
        "queen_state_phases": phase_metrics(core, detail, own), "strategy_inferences": []}
    metric = compact_metrics(record)
    # Full official raw completion and optional UI consistency are separate evidence.
    metric["whole_match_verified"] = bool(core["quality"]["complete_match_verified"])
    metric["UI_verified"] = validation["verified"]
    metric["opponent_invalid_action_deaths"] = audit["teams"]["B" if own == "A" else "A"].get("death_invalid_action", 0)
    record["metrics"] = metric
    write_json(cache_path, record)
    return record, False


def summarize(rows, expected):
    full = [r for r in rows if r.get("audit_status") == "verified"]
    games = [r["metrics"] for r in full]
    gross = [g for g in games if g["gross_ledger_verified"]]
    no_invalid = [g for g in games if not g["opponent_invalid_action_deaths"] and not g["event_counts"].get("death_invalid_action", 0)]
    groups = {}
    for opponent in sorted({g["opponent"] or "unknown" for g in games}):
        t = [g for g in games if (g["opponent"] or "unknown") == opponent]
        groups[opponent] = {"games": len(t), "outcomes": dict(Counter(g["outcome"] for g in t)),
            "queen_alive": sum(g["queen_alive"] for g in t),
            "opponent_invalid_action_games": sum(g["opponent_invalid_action_deaths"] > 0 for g in t),
            "opponent_invalid_action_deaths": sum(g["opponent_invalid_action_deaths"] for g in t),
            "no_recorded_invalid_action_outcomes": dict(Counter(g["outcome"] for g in t
                if not g["opponent_invalid_action_deaths"] and not g["event_counts"].get("death_invalid_action", 0))),
            "terminal_longest_median": statistics.median(g["terminal_longest"] for g in t),
            "loss_axes": dict(Counter(g["score_axis"] for g in t if g["outcome"] == "loss"))}
    return {"expected_panel_games": expected, "explicit_selected_ids": len(rows),
        "import_status": dict(Counter(r["import_status"] for r in rows)),
        "audit_status": dict(Counter(r["audit_status"] for r in rows)), "full_raw_verified": len(games),
        "terminal_UI_verified": sum(g["UI_verified"] is True for g in games),
        "gross_ledger_verified": len(gross), "outcomes": dict(Counter(g["outcome"] for g in games)),
        "no_recorded_invalid_action_games": len(no_invalid),
        "no_recorded_invalid_action_outcomes": dict(Counter(g["outcome"] for g in no_invalid)),
        "opponent_invalid_action_games": sum(g["opponent_invalid_action_deaths"] > 0 for g in games),
        "opponent_invalid_action_deaths": sum(g["opponent_invalid_action_deaths"] for g in games),
        "loss_axes": dict(Counter(g["score_axis"] for g in games if g["outcome"] == "loss")),
        "queen_alive": sum(g["queen_alive"] for g in games),
        "queen_death_codes": dict(Counter(g["queen_death"]["reason"] for g in games if g["queen_death"])),
        "queen_head_collision_relations": dict(Counter(g["queen_head_collision_relation"] or "unresolved"
            for g in games if g["queen_death"] and g["queen_death"]["reason"] == "H")),
        "our_invalid_action_deaths": sum(g["event_counts"].get("death_invalid_action", 0) for g in games),
        "full_panel_complete": len(games) == len(rows) == expected,
        "by_opponent": groups,
        "scope": "Preregistered external online unranked panel; correlated series, no Elo conversion"}


def publish_report(report, directory):
    """Small public numeric/provenance manifest; no raw or source payloads."""
    rows = report["matches"]
    games = [r["metrics"] for r in rows if r.get("audit_status") == "verified"]
    summary = report["summary"]
    payload = {key: report[key] for key in ("schema_version", "generated_utc", "manifest_sha256", "source_proof",
                "analyzer_dependencies", "dependencies_unchanged_during_run", "summary", "limitations")}
    payload["matches"] = [{"match_id": r["match_id"], "selection": r["selection"],
        "replay_sha256": r.get("replay_sha256"), "replay_bytes": r.get("replay_bytes"),
        "sources": r["sources"], "import_status": r["import_status"], "audit_status": r["audit_status"],
        "validation_issues": r.get("validation_issues", []), "gross_ledger_issues": r.get("gross_ledger_issues", []),
        "metrics": {key: r["metrics"][key] for key in
            ("our_team", "outcome", "score_axis", "map", "opponent", "UI_verified", "gross_ledger_verified",
             "queen_alive", "queen_length", "queen_peak_length", "queen_head_collision_relation", "opponent_invalid_action_deaths", "terminal_longest",
             "opponent_terminal_longest", "historical_event_longest", "resources", "gross_resources", "continuous_lead", "event_counts")}
            if "metrics" in r else None} for r in rows]
    directory.mkdir(parents=True, exist_ok=True)
    manifest_name = "oct6-online51-manifest.json"
    (directory / manifest_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    safe = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["# 2026-10-06 Generalist-v3：真实外部线上51场", "",
        f"记录UTC `{report['generated_utc']}`。预先计划见[线上外部计划](oct6-online-external-plan.md)，逐场哈希与完整数值见[证据清单]({manifest_name})。原v14的[固定100场发现证据](oct6-online100-raw-findings.md)保留不覆盖；这是新冻结候选对三个真实外部队伍的Unranked系列。", "",
        "## 证据覆盖与结果", "",
        f"- 实际rendered链接明确选中{summary['explicit_selected_ids']}个ID，计划分母{summary['expected_panel_games']}；不从series first ID猜连续区间、不按胜负换局。原始回放完整核对{summary['full_raw_verified']}/{summary['explicit_selected_ids']}，终局UI核对{summary['terminal_UI_verified']}/{summary['explicit_selected_ids']}，gross账{summary['gross_ledger_verified']}/{summary['explicit_selected_ids']}；分母分开。",
        f"- 我方唯一官方回放botId `{report['source_proof']['submission_id']}`，来源记录对应平台v{report['source_proof']['platform_version']}，冻结源码包SHA `{report['source_proof']['source_bundle_sha256']}`。根代理官方源码下载记录ZIP SHA `{report['source_proof']['zip_sha256']}`，所有下载成员与冻结本地成员哈希一致。源码包哈希为路径/哈希/大小JSON口径，不能与旧compare文件名+字节口径混用。未独立取得平台二进制SHA；匿名对手header不证明其提交或私有源码。",
        f"- 正式结果：{summary['outcomes']}。败场直接规则：{summary['loss_axes']}。我方Queen终局存活{summary['queen_alive']}/{summary['full_raw_verified']}；死亡原因代码{summary['queen_death_codes']}，头碰头关系{summary['queen_head_collision_relations']}。H=头碰头、S=自身身体、W=墙/海带、O=其他身体。",
        f"- 我方记录的无效动作死亡{summary['our_invalid_action_deaths']}；该数字不自动等于独立核实全部线上CPU/预算正常。没有完整可证gross的场次保留unknown和原结果，不能用请求步数填付费或删局。", "",
        f"- 对手无效动作死亡共{summary['opponent_invalid_action_deaths']}条，发生于{summary['opponent_invalid_action_games']}场；所有正式胜负保留，但这些场不作为可靠强度证据。双方均无记录此类死亡的{summary['no_recorded_invalid_action_games']}场正式结果为{summary['no_recorded_invalid_action_outcomes']}。此分组与gross可证性分别检查；对手无效动作不将其真实净身体或资源自动归零。", "",
        "| 对手 | 完整回放局数 | 正式结果 | Queen存活 | 终局Longest中位 | 败场直接规则 |",
        "| --- | --- | --- | --- | --- | --- |"]
    for opponent, group in summary["by_opponent"].items():
        lines.append(f"| {safe(opponent)} | {group['games']} | {safe(group['outcomes'])} | {group['queen_alive']}/{group['games']} | {group['terminal_longest_median']:g} | {safe(group['loss_axes'])} |")
    lines += ["", "无记录双方No-valid-action死亡的分组："]
    for opponent, group in summary["by_opponent"].items():
        lines += ["", f"- {safe(opponent)}：{group['no_recorded_invalid_action_outcomes']}；对手此类死亡{group['opponent_invalid_action_deaths']}条/{group['opponent_invalid_action_games']}场。无该记录不等于已独立核验所有运行与预算字段。"]
    lines += ["", "## 全部败场：直接判负与观测分开", "",
        "回合为网页1起算。Longest峰值含初始/分裂继承；峰值→终局差不自动等于某个单位的死亡损失。`独L死`是当时唯一最长单位死亡条数。没有根据计数倒推对手意图或私有代码。", "",
        "| Match | 对手 / 地图 | 直接规则 | Queen终局或死亡 | Longest峰→末 / 对方末 | 独L死 | 连续领先轮数 | gross可证 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for game in games:
        if game["outcome"] != "loss":
            continue
        q = f"活，L{game['queen_length']}" if game["queen_alive"] else f"r{game['queen_death']['round'] + 1} {game['queen_death']['reason']}"
        if game["queen_head_collision_relation"]:
            q += " " + game["queen_head_collision_relation"]
        lines.append(f"| [M{game['match_id']}](https://game.battlecode.au/battles/{game['match_id']}) | {safe(game['opponent'])} / {safe(game['map'])} | {game['score_axis']} | {q} | {game['historical_event_longest']}→{game['terminal_longest']} / {game['opponent_terminal_longest']} | {len(game['unique_longest_deaths'])} | {game['continuous_lead']['longest_continuous_lead']} | {'是' if game['gross_ledger_verified'] else '未知'} |")
    lines += ["", "## 解释边界", "",
        "这是三个对手、每队一次全17地图系列；系列内相关，51局不能当作51个独立成熟对手。平台种子与先后手并非受控配对；与v14发现100场或本地弱基准的胜率不能直接比较来归因改进。Unranked结果不产生可报告的earned Elo升级；初始提交评分也不是提升。", "",
        "Queen保命、资源兑现和消灭失败都需解释，不能用单一Longest峰值或曾领先掩盖正式终局。具体根本因果需已执行动作、长度账与场景验证；当前清单提供直接规则和观测，策略推断保持假说。没有取得的UI/预算/对手版本字段保持未知。", "",
        "原始下载仅按明确ID从给定目录安全读取，原始回放与逐轮大型缓存留在忽略目录，不入Git。清单无源码内容、token、cookie、认证头或私密下载参数。", "",
        "## 复现（仅离线解码）", "", "```powershell",
        ".venv\\Scripts\\python.exe tools\\audit_online_panel.py --manifest test-results\\generalist-v3-online51-selection.json --download-dir '<下载目录>' --ui-dir test-results\\online51-ui --docs-out docs",
        ".venv\\Scripts\\python.exe -m unittest tests.audit_online_panel_test",
        "```", ""]
    (directory / "oct6-online51-findings.md").write_text("\n".join(lines), encoding="utf-8")


def run(args):
    if not args.out.resolve().is_relative_to(ROOT / "test-results") or args.out.resolve() == (ROOT / "test-results/online100-raw"):
        raise ValueError("Output must be a distinct ignored workspace test-results directory")
    manifest_raw = args.manifest.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8-sig"))
    selected = selected_matches(manifest)
    proof = verify_source_record(args.submission_proof, args.freeze_record, args.submission_id, args.platform_version)
    dependencies = dependency_hashes()
    dependencies[Path(__file__).name] = sha(Path(__file__).read_bytes())
    candidates, inventory, issues, ignored = scan_downloads(args.download_dir, {r["match_id"] for r in selected})
    rows = import_candidates(candidates, [r["match_id"] for r in selected], args.out)
    candidates.clear()
    for position, (row, item) in enumerate(zip(rows, selected)):
        row["selection"] = item
        row["audit_status"] = "not_audited"
        if row["import_status"] != "imported":
            continue
        try:
            ui, evidence = read_ui(args.ui_dir, row["match_id"], args.our_team_id, args.platform_version, item)
            record, cached = reconstruct(args.out / row["replay_path"], item, ui, evidence, proof, dependencies, args.refresh)
            metric = record["metrics"]
            problems = record["quality"]["issues"] + record["ui_validation"]["issues"]
            row.update(audit_status="verified" if metric["whole_match_verified"] and not problems else "validation_issue",
                cached=cached, metrics=metric, validation_issues=problems,
                gross_ledger_issues=record["gross_ledger_issues"], analysis_path=f"M{row['match_id']}.analysis.json")
        except Exception as error:
            row.update(audit_status="failed", error=f"{type(error).__name__}: {error}")
        if (position + 1) % 5 == 0:
            print(json.dumps({"position": position + 1, "status": row["audit_status"]}), flush=True)
    end_dependencies = dependency_hashes()
    end_dependencies[Path(__file__).name] = sha(Path(__file__).read_bytes())
    report = {"schema_version": 1, "generated_utc": utc_now(), "manifest_sha256": sha(manifest_raw),
        "source_proof": proof, "analyzer_dependencies": dependencies,
        "dependencies_unchanged_during_run": dependencies == end_dependencies,
        "summary": summarize(rows, args.expected_count), "matches": rows,
        "scan_issues": issues, "download_inventory": inventory, "ignored_nonselected": ignored,
        "limitations": ["Only explicit selected IDs; no assumed consecutive IDs or replacement games",
            "Missing terminal UI stays unknown and does not masquerade as UI verification",
            "Gross refused for unsupported/incomplete execution; exact net body ledger retained",
            "Anonymous opponent header is not opponent private-source or submission proof",
            "Ranked status/identity/seed/map only independently UI-verified when a terminal capture is available",
            "No automated strategy-intent or causal-strength inference"]}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_json(args.out / f"audit-{stamp}.json", report)
    write_json(args.out / "index.json", report)
    if args.docs_out:
        publish_report(report, args.docs_out)
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--ui-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "test-results/online51-raw")
    parser.add_argument("--submission-proof", type=Path, default=ROOT / "test-results/generalist-v3-submission-proof.json")
    parser.add_argument("--freeze-record", type=Path, default=ROOT / "test-results/external-panel-v3-20261006/candidate/freeze.json")
    parser.add_argument("--submission-id", type=int, default=18674)
    parser.add_argument("--platform-version", type=int, default=19)
    parser.add_argument("--our-team-id", type=int, default=1035)
    parser.add_argument("--expected-count", type=int, default=51)
    parser.add_argument("--docs-out", type=Path, help="Optional small numeric/provenance JSON and Markdown; no raw payload")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
