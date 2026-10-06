"""Offline evidence audit; never executes bots, matches, or browser actions.

Examples:
  python tools/audit_online.py --input match.replay --team B --out audit.json
  python tools/audit_online.py --manifest selected.json --expected-count 100 --out audit.json
  python tools/audit_online.py --manifest selected.json --ui-dir exported-ui --our-team-id 1035 --platform-version 14 --expected-count 100 --out audit.json

Manifest: {"selection": {...}, "matches": [{"match_id": 123, "our_team": "B",
"submission": 15719, "source_hash": "...", "ranked": true, "replay": "123.replay"}]}.
Paths are relative to the manifest. A row can use "log" instead of "replay";
text logs need initial_dragons or identity_teams to attribute non-Queen IDs.
Optional result is an explicitly declared platform result, not recovered proof.
Source/submission values are declarations: replay names do not verify source bytes.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import zipfile

REASONS = {"W": "wall", "S": "self_body", "O": "other_body",
           "H": "head_collision", "A": "invalid_action"}
TEXT_REASONS = {"hit a wall": "W", "hit kelp": "W", "hit itself": "S",
                "hit another dragon": "O", "hit a body": "O",
                "head-on collision": "H", "lost a head-to-head": "H",
                "gave no valid action": "A", "no valid action": "A"}
_DECODER_SOURCE = {}


def initial_dragons(map_text):
    """Map declaration order defines IDs; team is declared, never ID parity."""
    result = []
    for line in map_text.splitlines():
        parts = line.split()
        if not parts or parts[0] not in ("DRAGON", "SNAKE"):
            continue
        values = list(map(int, parts[1:]))
        if len(values) != 2 + values[1] * 2:
            raise ValueError("Malformed initial dragon body")
        result.append({"id": len(result), "team": "A" if values[0] == 0 else "B",
                       "body": [{"x": values[i], "y": values[i + 1]}
                                for i in range(2, len(values), 2)]})
    return result


def load_ui(path):
    """Read a saved official terminal UI export, never event reconstruction."""
    raw = Path(path).read_bytes()
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data.get("main"), str) or not isinstance(data.get("tables"), list):
        raise ValueError("UI export needs main text and tables")
    data["input_format"] = "terminal_ui"
    data["input_sha256"] = hashlib.sha256(raw).hexdigest()
    return data


def audit_ui(data, metadata=None):
    """Attribute the terminal score; event/intent details remain unknown.

    A/B labels here mean UI table columns, not verified engine sides. The Queen
    death round and cumulative counts are official rendered observations, not
    a claim that the corresponding event sequence was downloaded.
    """
    metadata = metadata or {}
    text = data["main"]
    warnings = []
    match = re.search(r"\bMatch\s+(\d+)\b", text)
    match_id = int(match[1]) if match else None
    if metadata.get("match_id") is not None and match_id != int(metadata["match_id"]):
        raise ValueError("UI match ID differs from selected match ID")
    tables = {t.get("label"): t.get("rows", []) for t in data["tables"]}
    current = tables.get("Current team statistics")
    cumulative = tables.get("Cumulative team events")
    if not current or len(current[0]) != 3:
        raise ValueError("UI needs two current-statistics team columns")
    names = {"A": current[0][1].strip(), "B": current[0][2].strip()}
    our_team = metadata.get("our_team")
    if metadata.get("our_team_id") is not None:
        team_links = [x for x in data.get("links", []) if re.search(
            r"/teams/" + re.escape(str(metadata["our_team_id"])) + r"(?:$|[/?#])", x.get("href", ""))]
        linked_names = {x.get("text", "").strip() for x in team_links}
        matching = [t for t, n in names.items() if n in linked_names]
        if len(matching) != 1:
            raise ValueError("Cannot resolve our team ID to one statistics column")
        if our_team is not None and our_team != matching[0]:
            raise ValueError("Declared UI column disagrees with official team identity")
        our_team = matching[0]
    if our_team not in ("A", "B"):
        raise ValueError("UI attribution requires our_team_id or explicit table-column our_team")
    def metric_rows(table):
        result = {}
        for r in table[1:]:
            if len(r) != 3: raise ValueError("Malformed UI statistics row")
            if r[0] in result: raise ValueError("Duplicate UI statistics metric")
            result[r[0]] = r[1:]
        return result
    stats = metric_rows(current)
    events = metric_rows(cumulative) if cumulative else {}
    if cumulative and cumulative[0][1:] != current[0][1:]:
        raise ValueError("Cumulative table team order differs from current statistics")
    def number(value):
        if not re.fullmatch(r"\d[\d,]*", str(value).strip()):
            raise ValueError("Non-numeric UI metric: " + str(value))
        return int(str(value).replace(",", ""))
    final, queen_deaths, peaks, counts = {}, {}, {}, {}
    mapping = {"Dragons lost": "deaths", "Kelp deaths": "death_wall",
        "Self-collisions": "death_self_body", "Other-body deaths": "death_other_body",
        "Head-to-head deaths": "death_head_collision", "No-valid-action deaths": "death_invalid_action",
        "Sprint attempts": "sprint_attempts", "Successful splits": "splits", "Sonar pings": "sonar_pings"}
    for i, team in enumerate(("A", "B")):
        queen_value = stats["Queen"][i].strip()
        dead = re.fullmatch(r"Dead\s*\(r(\d+)\)", queen_value)
        queen_length = 0 if dead else number(queen_value)
        queen_deaths[team] = int(dead[1]) if dead else None
        final["team" + team] = {"queenLength": queen_length,
            "dragonCount": number(stats["Dragons alive"][i]),
            "longestDragon": number(stats["Longest now"][i]),
            "totalLength": number(stats["Total length"][i])}
        peaks[team] = number(stats["Longest so far"][i]) if "Longest so far" in stats else None
        counts[team] = {key: number(events[label][i]) for label, key in mapping.items() if label in events}
        s = final["team" + team]
        if not (0 <= s["queenLength"] <= s["longestDragon"] <= s["totalLength"]):
            warnings.append(f"{team}: inconsistent terminal length hierarchy")
        if (s["dragonCount"] == 0) != (s["totalLength"] == 0):
            warnings.append(f"{team}: terminal dragon count/length inconsistency")
        if peaks[team] is not None and peaks[team] < s["longestDragon"]:
            warnings.append(f"{team}: displayed peak below terminal longest")
        death_keys = ("death_wall", "death_self_body", "death_other_body", "death_head_collision", "death_invalid_action")
        if "deaths" in counts[team] and all(k in counts[team] for k in death_keys):
            if counts[team]["deaths"] != sum(counts[team][k] for k in death_keys):
                warnings.append(f"{team}: cumulative death categories do not sum to dragons lost")
    cursors = re.findall(r"\bRound\s+(\d+)\s*/\s*(\d+)\b", text)
    round_no, last_round = tuple(map(int, cursors[-1])) if cursors else (None, None)
    eliminated = any(s["dragonCount"] == 0 for s in final.values())
    terminal = round_no is not None and round_no == last_round and (last_round == 500 or eliminated)
    if not terminal: warnings.append("UI is not a proven terminal cursor; no score attribution")
    a, b = final["teamA"], final["teamB"]
    if eliminated:
        winner = "B" if a["dragonCount"] == 0 and b["dragonCount"] else "A" if b["dragonCount"] == 0 and a["dragonCount"] else None
    else:
        ka, kb = tuple(a[k] for k in ("queenLength", "longestDragon", "totalLength")), tuple(b[k] for k in ("queenLength", "longestDragon", "totalLength"))
        winner = "A" if ka > kb else "B" if kb > ka else None
    result = {"terminated": terminal, "endReason": "teamEliminated" if eliminated else "roundLimit",
              "winner": winner if terminal else None, **final}
    reason = score_reason(result)
    outcome = "unknown" if not terminal else "draw" if winner is None else "win" if winner == our_team else "loss"
    current_links = [x for x in data.get("links", []) if re.search(
        r"/battles/" + str(match_id) + r"(?:$|[/?#])", x.get("href", ""))]
    link_text = current_links[0].get("text", "") if len(current_links) == 1 else None
    link_outcome_match = re.search(r"(?:^|\n)\s*([WLDT])\s*(?:\n|$)", link_text or "")
    link_outcome = {"W": "win", "L": "loss", "D": "draw", "T": "draw"}.get(link_outcome_match[1]) if link_outcome_match else None
    if terminal and link_outcome and link_outcome != outcome:
        warnings.append("Current game link outcome disagrees with terminal scoring")
    link_reason_match = re.search(r"\(by\s+([^)]*)\)", link_text or "", re.I)
    reason_names = {"elimination": "elimination", "queen length": "queen", "queenlength": "queen",
                    "longest dragon": "longest", "longest": "longest", "total length": "total_length"}
    link_reason = reason_names.get(link_reason_match[1].strip().lower()) if link_reason_match else None
    if terminal and link_reason and link_reason != reason:
        warnings.append("Current game link scoring axis disagrees with terminal statistics")
    version = re.search(r"Your bot:\s*v(\d+)\s*[^\n]*", text)
    platform_version = int(version[1]) if version else None
    expected_version = metadata.get("platform_version")
    verified = platform_version == int(expected_version) if expected_version is not None else None
    if verified is False: warnings.append("UI bot version differs from required same-version sample")
    map_match = re.search(r"Map:\s*([^\n]+)", text)
    seed_match = re.search(r"\bSeed\s*\n\s*(0x[0-9a-fA-F]+)", text)
    ours = final["team" + our_team]
    qround = queen_deaths[our_team]
    observed_queen_events = []
    queen_event_details = {}
    for event in data.get("queen_events", []):
        if not isinstance(event, dict):
            warnings.append("Queen event has no separate round/text fields")
            continue
        event_text = event.get("text", "")
        death_match = re.fullmatch(r"dragon\s+([01])\s+\(queen\)\s+dies\.\s*Reason:\s*(.+)", event_text.strip())
        if not death_match or not re.fullmatch(r"\d+", str(event.get("round", "")).strip()):
            warnings.append("Unrecognized filtered Queen event")
            continue
        event_round = int(event["round"])
        matching_columns = [t for t, r in queen_deaths.items() if r == event_round]
        team = matching_columns[0] if len(matching_columns) == 1 else None
        raw_reason = death_match[2].strip()
        reason_code = TEXT_REASONS.get(raw_reason)
        detail = {"id": int(death_match[1]), "team": team, "round": event_round,
                  "reason": REASONS.get(reason_code), "reason_raw": raw_reason,
                  "identity_evidence": "unique terminal Queen death round" if team else "unresolved UI column",
                  "evidence": "official filtered Queen-death log entry"}
        observed_queen_events.append(detail)
        if not matching_columns:
            warnings.append("Filtered Queen death event disagrees with terminal Queen rows")
        elif team is None:
            warnings.append("Filtered Queen death event cannot be assigned to a unique UI table column")
        elif team in queen_event_details:
            warnings.append(f"{team}: duplicate filtered Queen death event")
        else:
            queen_event_details[team] = detail
    queen_death = queen_event_details.get(our_team)
    if qround is not None and queen_death is None:
        queen_death = {"round": qround, "reason": None, "evidence": "official rendered Queen death round"}
    return {"match_id": match_id, "submission": metadata.get("submission"), "source_hash": metadata.get("source_hash"),
        "version_evidence": version[0] if version else None, "platform_version": platform_version,
        "platform_version_verified": verified, "submission_verified": metadata.get("submission_verified"),
        "our_team": our_team, "our_ui_column": our_team, "engine_team": None,
        "team_label_basis": "A/B are UI statistics columns; engine side is unverified",
        "our_team_id": metadata.get("our_team_id"), "team_names": names,
        "opponent": names["B" if our_team == "A" else "A"], "ranked": bool(re.search(r"\bRanked\b", text)),
        "map": map_match[1].strip() if map_match else None, "seed": seed_match[1] if seed_match else None,
        "input_format": "terminal_ui", "input_sha256": data.get("input_sha256"),
        "evidence_scope": "terminal_and_cumulative_only", "full_event_replay_available": False,
        "last_round": round_no, "ui_final_round": last_round, "terminal_cursor": terminal,
        "result": result, "outcome": outcome,
        "direct_cause": {"score_axis": reason, "evidence": "official terminal UI statistics", "current_game_link_reason": link_reason},
        "proximate_evidence": [], "strategy_inferences": [],
        "queen": {"id": queen_death.get("id") if queen_death else None, "team": our_team, "peak_length": None,
                  "last_observed_length": ours["queenLength"], "terminal_length": ours["queenLength"] if terminal else None,
                  "terminal_alive": ours["queenLength"] > 0 if terminal else None,
                  "death": queen_death},
        "queen_death_rounds": queen_deaths, "filtered_queen_events": observed_queen_events,
        "observed_peak_workers": [], "team_longest_so_far": peaks,
        "teams": counts, "head_collision_pairs": [], "reconstructed_final": {"A": None, "B": None},
        "final_reconciliation": {"A": None, "B": None}, "current_game_link_outcome": link_outcome,
        "warnings": warnings, "measurement_limits": [
            "Terminal UI has no complete action/event sequence: peak-worker IDs/deaths and strategic intent are unknown; Queen death reason requires an explicit matching filtered log event.",
            "Longest so far includes every dragon and initial/split inheritance; it does not identify a grown worker or Queen peak.",
            "Other-body/head deaths do not distinguish friendly versus enemy collisions in this UI.",
            "Sprint attempts are requests, not executed paid steps; food pickups, paid losses, and CPU errors are unavailable.",
            "Displayed bot version verifies the platform label only; source hash/submission mapping requires independent provenance."]}


def _viewer_default():
    spec = importlib.util.find_spec("unswbc")
    if not spec or not spec.origin:
        raise ValueError("Install/use the existing unswbc environment, or pass --viewer")
    return Path(spec.origin).parent / "replay-viewer.vsix"


def load_replay(path, *, viewer_path=None, node_path=None):
    """Return official normalized events/result/map, plus initial_dragons.

    The installed official viewer's Cap'n Proto codec and schema converters are
    evaluated without its UI. Only trusted installed code is evaluated; replay
    bytes remain data. No engine, network, map replay, or bot code is launched.
    Raw roundStart.round is zero-based; audit human rounds add one.
    """
    path = Path(path)
    raw = path.read_bytes()
    if raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    if raw.lstrip().startswith(b"{"):
        data = json.loads(raw)
        if not isinstance(data.get("events"), list):
            raise ValueError("JSON replay needs an events list")
        if data.get("formatVersion", 2) > 2:
            raise ValueError("Unsupported replay format version")
    else:
        viewer = Path(viewer_path) if viewer_path else _viewer_default()
        key = (str(viewer.resolve()), viewer.stat().st_mtime_ns)
        if key not in _DECODER_SOURCE:
            with zipfile.ZipFile(viewer) as archive:
                bundle = archive.read("extension/dist/webview/webview.js")
            text = bundle.decode("utf-8")
            # Stable markers in the installed 1.2.7 viewer. An incompatible
            # upgrade fails explicitly rather than interpreting bytes silently.
            start = text.index("var q=")
            end = text.index("var Xf=V", start)
            source = ('var Na={HitWall:"W",HitSelf:"S",HitOtherBody:"O",'
                      'HitHeadToHead:"H",NoValidAction:"A"},Pa={Line:0,Dot:1};'
                      + text[start:end])
            _DECODER_SOURCE[key] = source, hashlib.sha256(bundle).hexdigest()
        source, digest = _DECODER_SOURCE[key]
        node = node_path or shutil.which("node")
        if not node:
            raise ValueError("Node is required to use the installed official replay codec")
        script = r'''
const input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
try {
 eval(input.source);
 const root=qf(Buffer.from(input.data,"base64"));
 const r=root.result;
 const out={formatVersion:root.formatVersion,map:root.map,
  seed:root.seed._isValue?root.seed.value:null,
  teams:{A:Kf("A",root.botA),B:Kf("B",root.botB)},
  events:[...root.events].map(e=>Lf(e,root.formatVersion)),
  result:{terminated:r.terminated,endReason:Wf[r.endReason],
   winner:r._isWinner?Mf(r.winner):null,teamA:Gf(r.teamA),teamB:Gf(r.teamB)}};
 if(out.result.endReason===undefined)throw Error("Unsupported result enum");
 process.stdout.write(JSON.stringify(out,(_,v)=>typeof v==="bigint"?v.toString():v));
}catch(e){process.stderr.write(e.name+": "+e.message);process.exit(1);}
'''
        proc = subprocess.run([node, "-e", script], input=json.dumps({"source": source,
            "data": base64.b64encode(raw).decode("ascii")}), text=True,
            encoding="utf-8", capture_output=True, timeout=60)
        if proc.returncode:
            raise ValueError("Official replay decoder: " + proc.stderr.strip())
        data = json.loads(proc.stdout)
        data["decoder_bundle_sha256"] = digest
    data.setdefault("initial_dragons", initial_dragons(data.get("map", "")))
    data["input_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    data["input_format"] = "official_replay"
    return data


def load_log(path, metadata=None):
    """Parse exported one-based viewer logs or partial official run console logs.

    A missing terminal result stays missing. Death-only console output cannot
    supply growth, actions, split births, or friendly collision counterparts.
    """
    metadata = metadata or {}
    text = Path(path).read_text(encoding="utf-8-sig")
    events = []
    last_round = None
    terminal = None
    for line_no, line in enumerate(text.splitlines(), 1):
        row = re.match(r"^(\d+)\s+(.+)$", line)
        if row:
            human_round, message = int(row[1]), row[2]
            if last_round != human_round:
                events.append({"type": "roundStart", "round": human_round - 1,
                               "source_line": line_no})
                last_round = human_round
            event = None
            m = re.fullmatch(r"dragon (\d+) asks to move ([NESW]+)", message)
            if m:
                events.append({"type": "turnStart", "id": int(m[1]), "source_line": line_no})
                event = {"type": "dragonAction", "id": int(m[1]),
                         "action": {"kind": "move", "steps": list(m[2])}}
            m = re.fullmatch(r"dragon (\d+) asks to split off (\d+) cells", message)
            if m:
                events.append({"type": "turnStart", "id": int(m[1]), "source_line": line_no})
                event = {"type": "dragonAction", "id": int(m[1]),
                         "action": {"kind": "split", "size": int(m[2])}}
            m = re.match(r"dragon (\d+) moves ([NESW]) to \((\d+),(\d+)\)(.*)", message)
            if m:
                length = re.search(r"length (\d+)", m[5])
                paid = re.search(r"pays (\d+)", m[5])
                event = {"type": "logMove", "id": int(m[1]), "direction": m[2],
                         "head": {"x": int(m[3]), "y": int(m[4])},
                         "food": "eats a pearl" in m[5], "paid": int(paid[1]) if paid else 0,
                         "length": int(length[1]) if length else None}
            m = re.fullmatch(r"dragon (\d+) splits off dragon (\d+), (\d+) cells", message)
            if m:
                event = {"type": "logSplit", "parentId": int(m[1]),
                         "childId": int(m[2]), "size": int(m[3])}
            m = re.fullmatch(r"dragon (\d+)(?: \(queen\))? dies\. Reason: (.+)", message)
            if m:
                event = {"type": "dragonDeath", "id": int(m[1]),
                         "reason": TEXT_REASONS.get(m[2], m[2])}
            m = re.match(r"dragon (\d+) pings ", message)
            if m:
                event = {"type": "sonarPing", "senderId": int(m[1])}
            if event:
                event["source_line"] = line_no
                events.append(event)
        else:
            m = re.match(r"round (\d+): bot (\d+) \(team ([AB])\) died: (.+)", line)
            if m:
                events.extend([{"type": "roundStart", "round": int(m[1]), "source_line": line_no},
                               {"type": "dragonDeath", "id": int(m[2]), "team": m[3],
                                "reason": TEXT_REASONS.get(m[4], m[4]), "source_line": line_no}])
            m = re.search(r"team ([AB]) wins after (\d+) rounds \(([^)]+)\)", line)
            if m:
                reason = m[3].split(",")[0]
                terminal = {"terminated": True, "winner": m[1], "rounds": int(m[2]),
                            "reported_reason": {"by elimination": "elimination",
                            "longer queen": "queen", "longest dragon": "longest",
                            "total length": "total_length"}.get(reason, "unknown")}
    return {"events": events, "initial_dragons": metadata.get("initial_dragons", []),
            "identity_teams": metadata.get("identity_teams", {}),
            "result": terminal or metadata.get("result"), "input_format": "text_log",
            "terminal_provenance": "log_verdict" if terminal else "manifest" if metadata.get("result") else "missing",
            "input_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def score_reason(result):
    """Elimination precedes the official Queen/Longest/Total lexicographic score."""
    if not result or not result.get("terminated"):
        return None
    if "reported_reason" in result:
        return result["reported_reason"]
    if result.get("endReason") == "teamEliminated":
        return "elimination" if result.get("winner") else "both_eliminated"
    a, b = result.get("teamA"), result.get("teamB")
    if not a or not b:
        return None
    for key, label in [("queenLength", "queen"), ("longestDragon", "longest"),
                       ("totalLength", "total_length")]:
        if a[key] != b[key]:
            return label
    return "draw"


def audit_match(data, metadata=None):
    metadata = metadata or {}
    our_team = metadata.get("our_team")
    replay_teams = data.get("teams") or {}
    if metadata.get("our_team_id") is not None and replay_teams:
        matching = [t for t in ("A", "B") if str((replay_teams.get(t) or {}).get("id")) == str(metadata["our_team_id"])]
        if len(matching) != 1:
            raise ValueError("Replay header does not identify our team ID uniquely")
        if our_team is not None and our_team != matching[0]:
            raise ValueError("Declared engine side disagrees with replay team ID")
        our_team = matching[0]
    if our_team not in ("A", "B"):
        raise ValueError("our_team must be explicitly A or B")
    states, counters = {}, defaultdict(Counter)
    for item in data.get("initial_dragons", []):
        body = [dict(p) for p in item.get("body", [])]
        states[int(item["id"])] = {"id": int(item["id"]), "team": item["team"],
            "body": body, "length": len(body) if body else item.get("length"),
            "peak_length": len(body) if body else item.get("length"), "death": None,
            "head": body[0] if body else None}
    for identity, team in data.get("identity_teams", {}).items():
        states.setdefault(int(identity), {"id": int(identity), "team": team, "body": [],
            "length": None, "peak_length": None, "death": None, "head": None})
    # Only Queen identity/team is globally fixed; other initial IDs need evidence.
    for identity, team in [(0, "A"), (1, "B")]:
        states.setdefault(identity, {"id": identity, "team": team, "body": [],
            "length": None, "peak_length": None, "death": None, "head": None})
    round_no, active, turn, collisions, pending_food = 0, None, None, [], []
    warnings, pearls, head_deaths = [], set(), []

    def get(identity):
        return states.setdefault(identity, {"id": identity, "team": None, "body": [],
            "length": None, "peak_length": None, "death": None, "head": None})

    def bump(identity, key, amount=1):
        counters[get(identity)["team"] or "unknown"][key] += amount

    def finish_turn():
        nonlocal head_deaths
        if len(head_deaths) == 2 and active in head_deaths:
            a, b = [get(i) for i in head_deaths]
            kind = "friendly" if a["team"] and a["team"] == b["team"] else "enemy" if a["team"] and b["team"] else "unknown"
            collisions.append({"round": round_no, "ids": head_deaths[:], "kind": kind,
                               "evidence": "two head deaths in the same explicit action"})
            for i in head_deaths:
                get(i)["death"]["counterpart_id"] = next(j for j in head_deaths if j != i)
                get(i)["death"]["collision_kind"] = kind
                bump(i, kind + "_head_deaths")
        elif head_deaths:
            for i in head_deaths:
                bump(i, "unpaired_head_deaths")
        head_deaths = []

    for event_index, event in enumerate(data["events"]):
        kind = event["type"]
        if kind == "roundStart":
            finish_turn()
            next_round = int(event["round"]) + 1
            if data.get("input_format") == "text_log" and round_no and next_round > round_no + 1:
                # An excerpt cannot carry a previously observed length over
                # omitted turns and then present paid allowance as known.
                for state in states.values():
                    if not state["death"]: state["length"] = None
                warnings.append(f"Missing rounds {round_no + 1}..{next_round - 1}; later starting lengths unknown")
            round_no = next_round
            active, turn, pending_food = None, None, []
        elif kind == "turnStart":
            finish_turn(); active = int(event["id"])
            turn = {"start_length": get(active)["length"], "updates": 0, "action": None}
            pending_food = []; bump(active, "turns")
        elif kind == "dragonAction":
            identity = int(event["id"]); action = event.get("action")
            if not turn or active != identity:
                finish_turn(); active = identity
                turn = {"start_length": get(identity)["length"], "updates": 0, "action": None}
            turn["action"] = action
            if action and action.get("kind") == "move":
                requested = len(action.get("steps", [])); bump(identity, "move_requests")
                bump(identity, "requested_move_steps", requested)
                if turn["start_length"] is not None:
                    bump(identity, "requested_paid_steps", max(0, requested - (turn["start_length"] + 3) // 4))
            if event.get("tle") or event.get("instructions", {}).get("exceeded"):
                bump(identity, "cpu_limit_events")
        elif kind in ("dragonSplit", "logSplit"):
            parent, child = int(event["parentId"]), int(event["childId"])
            source = get(parent)
            if kind == "dragonSplit":
                source["body"] = [dict(p) for p in event["parentBody"]]
                source["length"] = len(source["body"])
                body = [dict(p) for p in event["childBody"]]; size = len(body)
                team = event["team"]
            else:
                body, size, team = [], event["size"], source["team"]
                if source["length"] is not None: source["length"] -= size
            states[child] = {"id": child, "team": team, "body": body, "length": size,
                             "peak_length": size, "death": None, "head": body[0] if body else None}
            bump(parent, "splits"); bump(parent, "split_segments", size)
        elif kind == "dragonUpdate":
            if round_no == 0:  # official initEvents duplicate initial head/tail
                continue
            identity = int(event["id"]); state = get(identity)
            body = [dict(event["head"])] + state["body"]
            while len(body) > 1 and body[-1] != event["tail"]: body.pop()
            if body[-1] != event["tail"]:
                warnings.append(f"event {event_index}: tail absent from reconstructed body for {identity}")
                state["length"] = None
            else:
                state["body"], state["length"] = body, len(body)
            state["head"] = event["head"]; bump(identity, "completed_move_updates")
            if active == identity and turn:
                turn["updates"] += 1
                if turn["start_length"] is not None and turn["updates"] > (turn["start_length"] + 3) // 4:
                    bump(identity, "completed_extra_steps")
                p = (event["head"]["x"], event["head"]["y"])
                if p in pending_food:
                    pending_food.remove(p); bump(identity, "confirmed_pearl_pickups")
        elif kind == "logMove":
            identity = int(event["id"]); state = get(identity)
            state["head"] = event["head"]; bump(identity, "completed_move_updates")
            bump(identity, "explicit_paid_segments", event["paid"])
            if event["food"]: bump(identity, "confirmed_pearl_pickups")
            if event["length"] is not None: state["length"] = event["length"]
            elif state["length"] is not None: state["length"] += int(event["food"]) - event["paid"]
        elif kind == "tileChange":
            p = (event["tile"]["x"], event["tile"]["y"])
            if event["hasPearl"]:
                pearls.add(p)
            else:
                if p in pearls and active is not None and turn and (turn.get("action") or {}).get("kind") == "move":
                    head = get(active)["head"]
                    if head and (head["x"], head["y"]) == p:
                        bump(active, "confirmed_pearl_pickups")
                    else: pending_food.append(p)
                pearls.discard(p)
        elif kind == "dragonDeath":
            identity = int(event["id"]); state = get(identity)
            if event.get("team"): state["team"] = event["team"]
            state["death"] = {"round": round_no, "reason": REASONS.get(event["reason"], event["reason"]),
                "event_index": event_index, "source_line": event.get("source_line"),
                "pre_death_observed_length": state["length"], "head": state["head"]}
            bump(identity, "deaths"); bump(identity, "death_" + state["death"]["reason"])
            if event["reason"] == "H": head_deaths.append(identity)
        elif kind == "sonarPing":
            bump(int(event["senderId"]), "sonar_pings")
        if kind in ("dragonUpdate", "logMove", "dragonSplit"):
            identity = int(event.get("id", event.get("parentId")))
            state = get(identity)
            if state["length"] is not None:
                state["peak_length"] = max(state["peak_length"] or 0, state["length"])
    finish_turn()
    result = data.get("result")
    reason = score_reason(result)
    outcome = "unknown" if reason is None else "draw" if not result.get("winner") else "win" if result["winner"] == our_team else "loss"
    leaders = sorted((s for s in states.values() if s["team"] == our_team and s["id"] > 1 and s["peak_length"] is not None),
                     key=lambda s: (-s["peak_length"], s["id"]))[:5]
    queen = next((s for s in states.values() if s["team"] == our_team and s["id"] <= 1), None)
    reconstructed = {}
    for team in ("A", "B"):
        living = [s for s in states.values() if s["team"] == team and not s["death"]]
        if living and any(s["length"] is None for s in living):
            reconstructed[team] = None; continue
        lengths = [s["length"] for s in living]
        reconstructed[team] = {"dragonCount": len(living), "longestDragon": max(lengths, default=0),
            "totalLength": sum(lengths), "queenLength": next((s["length"] for s in living if s["id"] <= 1), 0)}
    reconciliation = {}
    for team in ("A", "B"):
        official = (result or {}).get("team" + team)
        reconciliation[team] = None if not official or reconstructed[team] is None else reconstructed[team] == official
        if reconciliation[team] is False: warnings.append(f"{team}: reconstructed final ledger differs from official result")
    if not result or not result.get("terminated"): warnings.append("No explicit complete terminal result; no score attribution")
    if counters.get("unknown"): warnings.append("Some identities lack team attribution; team totals are incomplete")
    near = []
    if outcome == "loss" and reason == "queen" and queen and queen["death"]:
        near.append({"type": "queen_death_before_terminal_queen_deficit", "death": queen["death"],
                     "scope": "event association, not proof a different move would win"})
    if outcome == "loss" and reason == "longest":
        near.extend({"type": "observed_peak_worker_died", "id": s["id"],
                     "observed_peak": s["peak_length"], "death": s["death"],
                     "scope": "candidate retention evidence, not autonomous growth or counterfactual victory"}
                    for s in leaders if s["death"])
    def compact(s):
        if not s: return None
        return {"id": s["id"], "team": s["team"], "peak_length": s["peak_length"],
                "last_observed_length": s["length"], "death": s["death"]}
    terminal_team = (result or {}).get("team" + our_team)
    queen_report = compact(queen)
    if queen_report:
        queen_report["terminal_length"] = terminal_team.get("queenLength") if terminal_team else None
        queen_report["terminal_alive"] = terminal_team["queenLength"] > 0 if terminal_team else None
    return {"match_id": metadata.get("match_id"), "submission": metadata.get("submission"),
        "source_hash": metadata.get("source_hash"),
        "version_evidence": metadata.get("version_evidence", "manifest declaration"),
        "submission_verified": metadata.get("submission_verified"),
        "opponent": metadata.get("opponent"), "ranked": metadata.get("ranked"), "our_team": our_team,
        "replay_team_metadata": replay_teams,
        "input_format": data.get("input_format"), "input_sha256": data.get("input_sha256"),
        "declared_complete": metadata.get("complete"),
        "round_numbering": "one-based; official raw roundStart is zero-based", "last_round": round_no,
        "result": result, "outcome": outcome,
        "direct_cause": {"score_axis": reason, "evidence": data.get("terminal_provenance", "official_replay_result")},
        "proximate_evidence": near, "strategy_inferences": [],
        "queen": queen_report, "observed_peak_workers": [compact(s) for s in leaders],
        "teams": {team: dict(counters[team]) for team in ("A", "B", "unknown")},
        "head_collision_pairs": collisions, "reconstructed_final": reconstructed,
        "final_reconciliation": reconciliation, "warnings": warnings,
        "measurement_limits": ["Peaks include initial/split inheritance, not independent growth.",
            "requested_paid_steps is not executed cost; completed_extra_steps excludes unobserved fatal-step cost.",
            "Explicit paid_segments is available only from text pays records; absent counters are unknown/unsupported, not zero proof.",
            "Friendly head pairs require two deaths in the same explicit action; body victim/intent remains unknown.",
            "Final scoring cause and earlier death events do not prove a strategic or counterfactual cause."]}


def aggregate(rows):
    good = [r for r in rows if "error" not in r]
    outcomes = Counter(r["outcome"] for r in good)
    causes = Counter(r["direct_cause"]["score_axis"] for r in good if r["outcome"] == "loss")
    terminal = [r for r in good if r["outcome"] != "unknown" and r.get("result", {}).get("teamA")]
    def terminal_profile(items):
        ours = [r["result"]["team" + r["our_team"]] for r in items]
        rivals = [r["result"]["team" + ("B" if r["our_team"] == "A" else "A")] for r in items]
        return {"games": len(items), "outcomes": dict(Counter(r["outcome"] for r in items)),
            "loss_score_axes": dict(Counter(r["direct_cause"]["score_axis"] for r in items if r["outcome"] == "loss")),
            "our_queen_alive": sum(s["queenLength"] > 0 for s in ours),
            "opponent_queen_alive": sum(s["queenLength"] > 0 for s in rivals),
            "our_terminal_queen_length_median": statistics.median(s["queenLength"] for s in ours) if ours else None,
            "our_terminal_longest_median": statistics.median(s["longestDragon"] for s in ours) if ours else None,
            "opponent_terminal_longest_median": statistics.median(s["longestDragon"] for s in rivals) if rivals else None,
            "our_queen_death_reasons": dict(Counter(((r.get("queen") or {}).get("death") or {}).get("reason") or "unknown"
                for r in items if r["result"]["team" + r["our_team"]]["queenLength"] == 0))}
    by_map, by_opponent = defaultdict(list), defaultdict(list)
    for r in terminal:
        by_map[r.get("map") or "unknown"].append(r)
        by_opponent[r.get("opponent") or "unknown"].append(r)
    return {"records": len(rows), "parsed": len(good), "errors": len(rows) - len(good),
            "parsed_subset_only": len(good) != len(rows),
            "terminal_attributed": sum(r["outcome"] != "unknown" for r in good),
            "reconciliation_failures": sum(False in r["final_reconciliation"].values() for r in good),
            "fully_reconciled": sum(all(v is True for v in r["final_reconciliation"].values()) for r in good),
            "submission_verified_records": sum(r.get("submission_verified") is True for r in good),
            "platform_version_verified_records": sum(r.get("platform_version_verified") is True for r in good),
            "terminal_ui_only_records": sum(r.get("input_format") == "terminal_ui" for r in good),
            "full_event_replay_records": sum(r.get("input_format") == "official_replay" for r in good),
            "outcomes": dict(outcomes), "loss_score_axes": dict(causes),
            "selected_table_outcomes": dict(Counter(r.get("selected_table_outcome") or "unknown" for r in rows)),
            "by_ranked_status": dict(Counter(str(r.get("ranked")) for r in good)),
            "terminal_profile": terminal_profile(terminal),
            "by_map": {k: terminal_profile(v) for k, v in sorted(by_map.items())},
            "by_opponent": {k: terminal_profile(v) for k, v in sorted(by_opponent.items())},
            "records_with_warnings": sum(bool(r.get("warnings")) for r in good),
            "strategy_inference_policy": "No automatic intent/feeding/counter classification from event counts."}


def manifest_items(manifest):
    """Accept downloaded manifests or a fixed browser selection not yet fetched.

    Selection-only rows remain missing-input errors, never fabricated audits.
    Table left/right order is NOT assumed to be engine team A/B.
    """
    if "matches" in manifest:
        return manifest["matches"]
    if "rows" not in manifest:
        raise ValueError("Manifest needs matches, or a selection rows list")
    result = []
    for row in manifest["rows"]:
        ids = [re.search(r"/battles/(\d+)(?:$|[/?#])", link.get("href", ""))
               for link in row.get("links", [])]
        ids = [int(m[1]) for m in ids if m]
        if len(ids) != 1: raise ValueError("Selection row needs one unambiguous battle ID")
        result.append({"match_id": ids[0], "selected_table_row": row})
    return result


def selected_table_outcome(row, our_team_id):
    """Read the fixed selection's named columns, without inferring engine side."""
    cells = row.get("cells", [])
    if len(cells) < 5 or our_team_id is None: return None
    links = [link for link in row.get("links", []) if re.search(r"/teams/\d+(?:$|[/?#])", link.get("href", ""))]
    if len(links) != 2: return None
    our_positions = [i for i, link in enumerate(links) if re.search(
        r"/teams/" + re.escape(str(our_team_id)) + r"(?:$|[/?#])", link.get("href", ""))]
    if len(our_positions) != 1: return None
    verdict = re.fullmatch(r"\s*([WLDT])\s*[–−-]\s*([WLDT])\s*", cells[3])
    if not verdict: return None
    return {"W": "win", "L": "loss", "D": "draw", "T": "draw"}[verdict[our_positions[0] + 1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", nargs="+"); group.add_argument("--manifest", type=Path)
    parser.add_argument("--team", choices=("A", "B")); parser.add_argument("--out", type=Path)
    parser.add_argument("--expected-count", type=int); parser.add_argument("--submission", type=int)
    parser.add_argument("--source-hash"); parser.add_argument("--viewer", type=Path); parser.add_argument("--node")
    parser.add_argument("--ui-dir", type=Path, help="Fallback saved UI exports named {match_id}-ui.json; path relative to cwd")
    parser.add_argument("--our-team-id", type=int, help="Resolve official UI team links to engine statistics columns")
    parser.add_argument("--platform-version", type=int, help="Verify every available UI export has this Your bot version")
    args = parser.parse_args()
    if args.manifest:
        raw_manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        if isinstance(raw_manifest, list):
            # fetch_online's saved bare-list paths are relative to workspace cwd.
            manifest = {"matches": raw_manifest, "selection": {"source_manifest_format": "downloaded bare list; paths relative to cwd"}}
            items, base = manifest_items(manifest), Path.cwd()
        else:
            manifest = raw_manifest
            items, base = manifest_items(manifest), args.manifest.resolve().parent
    else:
        if not args.team and not args.our_team_id: parser.error("--input requires --team or --our-team-id")
        manifest, base = {}, Path.cwd()
        items = [{"replay" if Path(p).suffix in (".replay", ".json") else "log": p,
                  "our_team": args.team} for p in args.input]
    ids = [str(i["match_id"]) for i in items if i.get("match_id") is not None]
    selection_errors = []
    if len(ids) != len(set(ids)): selection_errors.append("Duplicate match IDs; cannot count as independent matches")
    if args.expected_count is not None and len(set(ids)) != args.expected_count:
        selection_errors.append(f"Expected {args.expected_count} distinct match IDs, found {len(set(ids))}")
    for name, expected in [("submission", args.submission), ("source_hash", args.source_hash)]:
        if expected is not None and any(i.get(name) != expected for i in items):
            selection_errors.append(f"Not every manifest row declares {name}={expected}")
    rows = []
    for item in items:
        item = dict(item)
        if args.our_team_id is not None: item.setdefault("our_team_id", args.our_team_id)
        if args.platform_version is not None: item.setdefault("platform_version", args.platform_version)
        selected_outcome = selected_table_outcome(item.get("selected_table_row", {}), item.get("our_team_id"))
        try:
            name = item.get("replay") or item.get("log")
            ui_path = item.get("ui")
            if not name and not ui_path and args.ui_dir and item.get("match_id") is not None:
                ui_path = args.ui_dir.resolve() / f"{item['match_id']}-ui.json"
            if ui_path:
                path = base / ui_path
                row = audit_ui(load_ui(path), item)
            elif name:
                path = base / name
                if item.get("replay") and path.suffix.lower() == ".json":
                    raw = json.loads(path.read_text(encoding="utf-8-sig"))
                    if "main" in raw and "tables" in raw:
                        row = audit_ui(load_ui(path), item)
                    else:
                        row = audit_match(load_replay(path, viewer_path=args.viewer, node_path=args.node), item)
                else:
                    data = load_replay(path, viewer_path=args.viewer, node_path=args.node) if item.get("replay") else load_log(path, item)
                    row = audit_match(data, item)
            else:
                raise ValueError("Missing replay/log/UI path")
            if row.get("platform_version_verified") is False:
                selection_errors.append(f"Match {item.get('match_id')}: platform version mismatch")
            row["input_path"] = str(path.resolve())
            row["selected_table_outcome"] = selected_outcome
            if selected_outcome and row["outcome"] != "unknown" and row["outcome"] != selected_outcome:
                row["warnings"].append("Terminal outcome disagrees with fixed selection table")
                selection_errors.append(f"Match {item.get('match_id')}: fixed selection outcome mismatch")
            if item.get("selected_table_row"): row["selected_table_row"] = item["selected_table_row"]
            rows.append(row)
        except (ValueError, OSError, KeyError, TypeError, IndexError, AttributeError, subprocess.SubprocessError) as error:
            rows.append({"match_id": item.get("match_id"), "error": str(error),
                         "evidence_scope": "input_unavailable", "outcome": "unknown",
                         "selected_table_outcome": selected_outcome,
                         "selected_table_row": item.get("selected_table_row")})
    selection = manifest.get("selection", {k: v for k, v in manifest.items() if k not in ("matches", "rows")})
    report = {"selection": selection, "selection_errors": selection_errors,
              "summary": aggregate(rows), "matches": rows}
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(output + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report["summary"].items() if k not in ("by_map", "by_opponent")}, ensure_ascii=False))
    else: print(output)
    return int(bool(selection_errors or report["summary"]["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
