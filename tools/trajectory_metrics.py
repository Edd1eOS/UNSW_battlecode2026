"""Audit whole-match score retention from complete, official replay events.

The input is the normalized output of audit_online.load_replay(), or a JSON
copy of that output. This module never runs a match or reads a bot's local
vision. Length changes are measured, not inferred from requested move costs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


TEAMS = ("A", "B")
REASONS = {"W": "wall", "S": "self", "O": "other_body",
           "H": "head_to_head", "A": "invalid_action"}
NONSTATE_DRAGON_EVENTS = {"dragonAction", "dragonLog", "dragonIndicator"}


class ReplayValidationError(ValueError):
    """A complete global state cannot be reconstructed from these events."""


def _position(value: Any) -> tuple[int, int]:
    if isinstance(value, dict) and "x" in value and "y" in value:
        return int(value["x"]), int(value["y"])
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return int(value[0]), int(value[1])
    raise ReplayValidationError(f"Invalid position: {value!r}")


def _team(value: Any) -> str:
    if value in TEAMS:
        return str(value)
    raise ReplayValidationError(f"Expected team A or B, got {value!r}")


def _length(dragon: dict[str, Any]) -> int:
    return dragon["length"] if "length" in dragon else len(dragon["body"])


def scores(dragons: dict[int, dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Fixed Queens have IDs 0 and 1; team comes from the map declaration."""
    result = {}
    for team in TEAMS:
        lengths = [_length(d) for d in dragons.values() if d["team"] == team]
        queens = [_length(d) for i, d in dragons.items() if i <= 1 and d["team"] == team]
        result[team] = {
            "dragon_count": len(lengths),
            "queen_length": max(queens, default=0),
            "longest_dragon": max(lengths, default=0),
            "total_length": sum(lengths),
        }
    return result


def advantage(score: dict[str, dict[str, int]]) -> dict[str, Any]:
    """Elimination first, then Queen, Longest, Total; no weighted sum."""
    a, b = score["A"], score["B"]
    delta = {key: a[key] - b[key] for key in a}
    if bool(a["dragon_count"]) != bool(b["dragon_count"]):
        leader = "A" if a["dragon_count"] else "B"
        return {"leader": leader, "criterion": "elimination", "margin": 1, "delta": delta}
    for criterion, key in (("queen", "queen_length"), ("longest", "longest_dragon"),
                           ("total", "total_length")):
        if delta[key]:
            return {"leader": "A" if delta[key] > 0 else "B", "criterion": criterion,
                    "margin": abs(delta[key]), "delta": delta}
    return {"leader": None, "criterion": "tie", "margin": 0, "delta": delta}


def _view(dragons: dict[int, dict[str, Any]]) -> dict[str, Any]:
    score = scores(dragons)
    return {"scores": score, **advantage(score)}


def _trajectory_summary(frames: list[dict[str, Any]]) -> dict[str, Any]:
    segments: list[dict[str, Any]] = []
    missing_rounds: list[int] = []
    for frame in frames:
        if segments and frame["round"] > segments[-1]["end_round"] + 1:
            missing_rounds.extend(range(segments[-1]["end_round"] + 1, frame["round"]))
        if (segments and segments[-1]["leader"] == frame["leader"]
                and frame["round"] == segments[-1]["end_round"] + 1):
            segments[-1]["end_round"] = frame["round"]
            segments[-1]["round_count"] += 1
        else:
            segments.append({"leader": frame["leader"], "start_round": frame["round"],
                             "end_round": frame["round"], "round_count": 1})
    changes = []
    for before, after in zip(frames, frames[1:]):
        if before["leader"] != after["leader"]:
            changes.append({"round": after["round"], "from": before["leader"],
                            "to": after["leader"], "criterion": after["criterion"],
                            "adjacent_rounds": after["round"] == before["round"] + 1})
    by_team = {}
    for team in TEAMS:
        own = [segment for segment in segments if segment["leader"] == team]
        first_lead = next((f["round"] for f in frames if f["leader"] == team), None)
        losses = [c for c in changes if c["from"] == team and c["adjacent_rounds"]]
        by_team[team] = {
            "leading_rounds": sum(s["round_count"] for s in own),
            "longest_continuous_lead": max((s["round_count"] for s in own), default=0),
            "first_lead_round": first_lead,
            "lead_losses": len(losses),
            "first_lead_loss_round": losses[0]["round"] if losses else None,
        }
    final_leader = frames[-1]["leader"] if frames else None
    final_change = next((c for c in reversed(changes) if c["to"] == final_leader), None)
    return {"sampled_rounds": len(frames), "tied_rounds": sum(f["leader"] is None for f in frames),
            "missing_rounds": missing_rounds, "by_team": by_team, "segments": segments,
            "lead_changes": changes, "last_change_to_final_leader": final_change}


def analyze_replay(replay: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct every body using the official viewer's update reducer.

    Events before the first roundStart are initialization events. Map bodies
    already include them, so applying their dragonUpdates would duplicate heads.
    """
    dragons: dict[int, dict[str, Any]] = {}
    initial_dragons = replay.get("initial_dragons")
    if not isinstance(initial_dragons, list) or not initial_dragons:
        raise ReplayValidationError("Full initial_dragons are required; local input is insufficient")
    for initial in initial_dragons:
        identity = int(initial["id"])
        if identity in dragons:
            raise ReplayValidationError(f"Duplicate initial dragon {identity}")
        body = [_position(p) for p in initial["body"]]
        if not body:
            raise ReplayValidationError(f"Empty initial body {identity}")
        dragons[identity] = {"team": _team(initial["team"]), "body": body}
    initial = _view(dragons)
    resources = {team: {
        "initial_capital": initial["scores"][team]["total_length"],
        "recorded_positive_updates": 0, "recorded_shrink_updates": 0,
        "queen_positive_updates": 0, "queen_shrink_updates": 0,
        "initial_queen_capital": initial["scores"][team]["queen_length"],
        "queen_length_transferred_by_split": 0,
        "last_recorded_length_removed_on_death": 0,
        "queen_length_removed_on_death": 0,
        "split_length_delta": 0, "splits": 0,
        "food_collected": None, "paid_step_cost": None,
    } for team in TEAMS}
    frames, deaths, splits, groups, issues = [], [], [], [], []
    log_mode = replay.get("input_format") == "text_log"
    if log_mode:
        for resource in resources.values():
            resource["food_collected"] = 0
            resource["paid_step_cost"] = 0
            resource["queen_food_collected"] = 0
            resource["queen_paid_step_cost"] = 0
    ignored = Counter()
    round_num: int | None = None
    turn_id: int | None = None
    turn_serial = 0
    group: dict[str, Any] | None = None
    init_events = 0

    def finish_group() -> None:
        nonlocal group
        if group is not None:
            group["observed_after"] = _view(dragons)
            # This counterfactual removes the recorded deaths together. It does
            # not assign the intervening action's food/cost changes to deaths.
            hypothetical = {i: d for i, d in group.pop("before_dragons").items()
                            if i not in group["dead_ids"]}
            group["death_only_after"] = _view(hypothetical)
            before_leader = group["before"]["leader"]
            group["erased_lead"] = (before_leader is not None
                and group["death_only_after"]["leader"] != before_leader)
            group["reversed_lead"] = (before_leader is not None
                and group["death_only_after"]["leader"] not in (None, before_leader))
            groups.append(group)
            group = None

    events = replay.get("events")
    if not isinstance(events, list):
        raise ReplayValidationError("events must be a complete normalized list")
    for event_index, event in enumerate(events):
        kind = event.get("type", event.get("kind"))
        if kind == "roundStart":
            finish_group()
            next_round = int(event.get("round", event.get("roundNum", -1)))
            if next_round < 0 or (round_num is not None and next_round <= round_num):
                raise ReplayValidationError(f"Invalid roundStart at event {event_index}: {event!r}")
            if round_num is not None:
                frames.append({"round": round_num, **_view(dragons)})
            round_num, turn_id = next_round, None
            continue
        if round_num is None:
            init_events += 1
            continue
        if kind == "turnStart":
            finish_group()
            turn_serial += 1
            turn_id = int(event["id"])
            continue
        if kind == "logMove":
            if not log_mode:
                raise ReplayValidationError("logMove requires a declared text_log input")
            identity = int(event["id"])
            if identity not in dragons:
                raise ReplayValidationError(f"Executed move of absent dragon {identity} at event {event_index}")
            dragon = dragons[identity]
            food, paid = int(bool(event["food"])), int(event["paid"])
            if paid < 0:
                raise ReplayValidationError(f"Negative executed cost at event {event_index}")
            new_length = _length(dragon) + food - paid
            if new_length <= 0:
                raise ReplayValidationError(f"Executed move leaves nonpositive length at event {event_index}")
            declared = event.get("length")
            if declared is not None and int(declared) != new_length:
                raise ReplayValidationError(f"Executed length mismatch for dragon {identity} at event {event_index}: computed={new_length}, logged={declared}")
            # The log proves length but contains no tail. Retain no invented body.
            dragon["body"], dragon["length"] = None, new_length
            resource = resources[dragon["team"]]
            resource["food_collected"] += food
            resource["paid_step_cost"] += paid
            delta = food - paid
            resource["recorded_positive_updates" if delta >= 0 else "recorded_shrink_updates"] += abs(delta)
            if identity <= 1:
                resource["queen_food_collected"] += food
                resource["queen_paid_step_cost"] += paid
                resource["queen_positive_updates" if delta >= 0 else "queen_shrink_updates"] += abs(delta)
            if group is not None:
                group["coincident_updates_after_first_death"] += 1
            continue
        if kind == "dragonUpdate":
            identity = int(event["id"])
            if identity not in dragons:
                raise ReplayValidationError(f"Update of absent dragon {identity} at event {event_index}")
            dragon = dragons[identity]
            if dragon["body"] is None:
                raise ReplayValidationError("Full body update cannot follow a tail-free text log move")
            old_length = _length(dragon)
            head, tail = _position(event["head"]), _position(event["tail"])
            body = [head, *dragon["body"]]
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            if body[-1] != tail:
                raise ReplayValidationError(f"Tail absent from body for dragon {identity} at event {event_index}")
            dragon["body"] = body
            delta = len(body) - old_length
            resource = resources[dragon["team"]]
            resource["recorded_positive_updates" if delta >= 0 else "recorded_shrink_updates"] += abs(delta)
            if identity <= 1:
                resource["queen_positive_updates" if delta >= 0 else "queen_shrink_updates"] += abs(delta)
            if group is not None:
                group["coincident_updates_after_first_death"] += 1
            continue
        if kind in ("dragonSplit", "logSplit"):
            parent, child = int(event["parentId"]), int(event["childId"])
            if parent not in dragons or child in dragons:
                raise ReplayValidationError(f"Invalid split identities at event {event_index}")
            team = _team(event["team"]) if kind == "dragonSplit" else dragons[parent]["team"]
            if team != dragons[parent]["team"]:
                raise ReplayValidationError(f"Split changes team at event {event_index}")
            old_length = _length(dragons[parent])
            if kind == "dragonSplit":
                parent_body = [_position(p) for p in event["parentBody"]]
                child_body = [_position(p) for p in event["childBody"]]
                parent_length, child_length = len(parent_body), len(child_body)
            else:
                if not log_mode:
                    raise ReplayValidationError("logSplit requires a declared text_log input")
                child_length = int(event["size"])
                parent_length = old_length - child_length
                parent_body = child_body = None
            if parent_length <= 0 or child_length <= 0:
                raise ReplayValidationError(f"Split creates empty body at event {event_index}")
            delta = parent_length + child_length - old_length
            if delta:
                issues.append(f"Nonconserving split at event {event_index}: length delta {delta}")
            dragons[parent]["body"] = parent_body
            dragons[child] = {"team": team, "body": child_body}
            if kind == "logSplit":
                dragons[parent]["length"] = parent_length
                dragons[child]["length"] = child_length
            resources[team]["split_length_delta"] += delta
            resources[team]["splits"] += 1
            if parent <= 1:
                resources[team]["queen_length_transferred_by_split"] += old_length - parent_length
            splits.append({"round": round_num, "event_index": event_index, "team": team,
                           "parent_id": parent, "child_id": child, "before_length": old_length,
                           "parent_length": parent_length, "child_length": child_length,
                           "length_delta": delta})
            if group is not None:
                group["coincident_updates_after_first_death"] += 1
            continue
        if kind == "dragonDeath":
            identity = int(event["id"])
            if identity not in dragons:
                raise ReplayValidationError(f"Death of absent dragon {identity} at event {event_index}")
            dragon = dragons[identity]
            team, length = dragon["team"], _length(dragon)
            before = _view(dragons)
            peers = [_length(d) for i, d in dragons.items() if i != identity and d["team"] == team]
            longest = before["scores"][team]["longest_dragon"]
            if group is None:
                group = {"round": round_num, "turn_id": turn_id, "turn_serial": turn_serial,
                         "before": before, "before_dragons": {
                             i: {"team": d["team"], "length": _length(d)} for i, d in dragons.items()},
                         "dead_ids": [], "coincident_updates_after_first_death": 0}
            group["dead_ids"].append(identity)
            del dragons[identity]
            after = _view(dragons)
            queen = identity <= 1
            resources[team]["last_recorded_length_removed_on_death"] += length
            if queen:
                resources[team]["queen_length_removed_on_death"] += length
            deaths.append({"round": round_num, "event_index": event_index, "turn_id": turn_id,
                           "turn_serial": turn_serial, "id": identity, "team": team,
                           "reason": REASONS.get(event.get("reason"), event.get("reason", "unknown")),
                           "last_recorded_length": length, "is_queen": queen,
                           "was_longest": length == longest,
                           "was_unique_longest": length > max(peers, default=0),
                           "longest_length_loss": longest - after["scores"][team]["longest_dragon"],
                           "before": before, "after": after,
                           "erased_own_lead_immediately": before["leader"] == team and after["leader"] != team,
                           "reversed_own_lead_immediately": before["leader"] == team
                               and after["leader"] not in (None, team)})
            continue
        ignored[str(kind)] += 1
        if (isinstance(kind, str) and kind.startswith("dragon")
                and kind not in NONSTATE_DRAGON_EVENTS and ignored[str(kind)] == 1):
            issues.append(f"Unrecognized state event {kind!r}, first seen at event {event_index}")
    if round_num is None:
        raise ReplayValidationError("No roundStart: this is not a complete match event stream")
    finish_group()
    frames.append({"round": round_num, **_view(dragons)})
    final = _view(dragons)
    trajectory = _trajectory_summary(frames)
    if frames[0]["round"] != 0:
        issues.append(f"First round is {frames[0]['round']}, expected official zero-based round 0")
    if trajectory["missing_rounds"]:
        issues.append("Missing roundStart events; continuous lead is not claimed across gaps")

    official = replay.get("result")
    terminal_verified: bool | None = None
    if isinstance(official, dict):
        complete_terminal = True
        terminal_mismatch = False
        for team in TEAMS:
            actual = official.get("team" + team)
            if not isinstance(actual, dict):
                complete_terminal = False
                continue
            for normalized, raw in (("dragon_count", "dragonCount"), ("queen_length", "queenLength"),
                                    ("longest_dragon", "longestDragon"), ("total_length", "totalLength")):
                if raw not in actual:
                    complete_terminal = False
                elif int(actual[raw]) != final["scores"][team][normalized]:
                    terminal_mismatch = True
                    issues.append(f"Terminal {team}.{raw} differs: replay={final['scores'][team][normalized]}, official={actual[raw]}")
        if official.get("terminated") and "winner" in official and official["winner"] != final["leader"]:
            terminal_mismatch = True
            issues.append(f"Terminal winner differs: replay={final['leader']}, official={official['winner']}")
        terminal_verified = False if terminal_mismatch else True if complete_terminal and official.get("terminated") else None
    if replay.get("formatVersion") is not None and int(replay["formatVersion"]) < 2:
        issues.append("Historical formatVersion<2: official Queen score semantics are not verified; modern score trajectory is diagnostic only")
    for team in TEAMS:
        resource = resources[team]
        resource["final_retained_length"] = final["scores"][team]["total_length"]
        resource["net_retained_length"] = resource["final_retained_length"] - resource["initial_capital"]
        resource["final_queen_length"] = final["scores"][team]["queen_length"]
        resource["queen_net_retained_length"] = resource["final_queen_length"] - resource["initial_queen_capital"]
        resource["queen_reconstructed_balance_residual"] = resource["queen_net_retained_length"] - (
            resource["queen_positive_updates"] - resource["queen_shrink_updates"]
            - resource["queen_length_transferred_by_split"] - resource["queen_length_removed_on_death"])
        resource["recorded_update_net"] = resource["recorded_positive_updates"] - resource["recorded_shrink_updates"]
        resource["reconstructed_balance_residual"] = resource["net_retained_length"] - (
            resource["recorded_update_net"] + resource["split_length_delta"]
            - resource["last_recorded_length_removed_on_death"])
        if log_mode:
            resource["executed_resource_balance_residual"] = resource["net_retained_length"] - (
                resource["food_collected"] - resource["paid_step_cost"]
                + resource["split_length_delta"] - resource["last_recorded_length_removed_on_death"])
        resource["death_reasons"] = dict(Counter(d["reason"] for d in deaths if d["team"] == team))
        resource["queen_deaths"] = sum(d["is_queen"] for d in deaths if d["team"] == team)
        resource["unique_longest_deaths"] = sum(d["was_unique_longest"] for d in deaths if d["team"] == team)
        resource["death_groups_erasing_own_lead"] = sum(g["erased_lead"] and g["before"]["leader"] == team for g in groups)
    return {
        "schema_version": 1, "round_base": 0,
        "replay_format_version": replay.get("formatVersion"),
        "quality": {"issues": issues, "complete_round_coverage": not trajectory["missing_rounds"] and frames[0]["round"] == 0,
                    "terminal_score_verified": terminal_verified, "ignored_initialization_events": init_events,
                    "complete_match_verified": terminal_verified is True and not issues,
                    "ignored_nonstate_events": dict(ignored),
                    "global_bodies_reconstructed": not log_mode,
                    "initial_state_provenance": replay.get("initial_state_provenance", "embedded_replay_map"),
                    "terminal_verdict_present": isinstance(official, dict) and bool(official.get("terminated")),
                    "resource_detail": "executed_log_food_and_cost" if log_mode else "recorded_net_only"},
        "initial": initial, "final": final, "official_result": official,
        "advantage": trajectory, "resources": resources, "trajectory": frames,
        "deaths": deaths, "death_groups": groups, "splits": splits,
        "interpretation": [
            "Each trajectory sample is the state at the end of an official zero-based round.",
            "Dense round coverage alone does not prove that a log includes the whole match; an absent terminal verdict stays unknown.",
            "Death effects are immediate counterfactual score changes, not claims about the cause of a whole-match loss.",
            "Grouped deaths prevent a transient head-to-head trade from being labeled a lasting lead reversal.",
            "Split offspring inherit length; splits are transfers, not food income.",
            "Positive and negative body updates are net changes, not independently verified gross food or paid-step counts.",
            "Death loss uses the last replay-recorded body; an unrecorded failed paid step cannot be separated from that loss.",
        ],
    }


def analyze_partial_log(data: dict[str, Any]) -> dict[str, Any]:
    """Useful executed-event evidence, with no invented initial team capital."""
    if data.get("input_format") != "text_log":
        raise ReplayValidationError("Full initial_dragons are required for a replay score trajectory")
    identity_teams = {int(i): _team(t) for i, t in data.get("identity_teams", {}).items()}
    counts = {team: {"executed_moves": 0, "food_collected": 0, "paid_step_cost": 0,
                     "split_births": 0, "deaths": 0} for team in (*TEAMS, "unknown")}
    rounds = set()
    for event in data.get("events", []):
        kind = event.get("type")
        if kind == "roundStart":
            rounds.add(int(event["round"]))
        elif kind == "logSplit":
            team = identity_teams.get(int(event["parentId"]), "unknown")
            if team != "unknown":
                identity_teams[int(event["childId"])] = team
            counts[team]["split_births"] += 1
        elif kind == "logMove":
            count = counts[identity_teams.get(int(event["id"]), "unknown")]
            count["executed_moves"] += 1
            count["food_collected"] += int(bool(event["food"]))
            count["paid_step_cost"] += int(event["paid"])
        elif kind == "dragonDeath":
            team = event.get("team", identity_teams.get(int(event["id"]), "unknown"))
            counts[team]["deaths"] += 1
    return {"schema_version": 1, "round_base": 0,
            "quality": {"issues": ["Missing initial bodies/lengths: no global score or net-capital claim"],
                        "complete_round_coverage": None, "terminal_score_verified": None,
                        "global_bodies_reconstructed": False, "initial_state_provenance": "missing",
                        "terminal_verdict_present": bool(data.get("result", {}).get("terminated")) if data.get("result") else False,
                        "resource_detail": "partial_executed_event_counts"},
            "initial": None, "final": None, "trajectory": None, "advantage": None,
            "official_result": data.get("result"), "executed_counts": counts,
            "sampled_rounds": sorted(rounds), "resources": None,
            "interpretation": ["Missing initial team capital prevents a score trajectory or total-length ledger.",
                               "Unknown initial worker teams stay unattributed; ID parity is never used.",
                               "Only executed logMove food/cost fields are counted; requested actions are excluded."]}


def load_input(path: Path, initial_map: Path | None = None) -> dict[str, Any]:
    if path.suffix.lower() in (".replay", ".log"):
        try:
            if __package__:
                from .audit_online import load_replay, load_log, initial_dragons
            else:
                from audit_online import load_replay, load_log, initial_dragons
        except ImportError as error:
            raise ReplayValidationError("Official decoder tools/audit_online.py is required") from error
        if path.suffix.lower() == ".log":
            metadata = {}
            if initial_map:
                raw_map = initial_map.read_bytes()
                metadata["initial_dragons"] = initial_dragons(raw_map.decode("utf-8-sig"))
            data = load_log(path, metadata)
            data["initial_state_provenance"] = ({"declared_map": str(initial_map.resolve()),
                "sha256": hashlib.sha256(raw_map).hexdigest()} if initial_map else "missing")
            return data
        return load_replay(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Official .replay or normalized full-replay JSON")
    parser.add_argument("--out", type=Path, help="Save JSON; otherwise print it")
    parser.add_argument("--team", choices=TEAMS, help="Mark the externally evaluated bot's side")
    parser.add_argument("--initial-map", type=Path, help="Declared initial map for text logs; never treated as embedded replay evidence")
    parser.add_argument("--summary-only", action="store_true", help="Omit individual rounds, deaths, groups and splits")
    args = parser.parse_args()
    reports = []
    for path in args.inputs:
        data = load_input(path, args.initial_map)
        report = analyze_replay(data) if data.get("initial_dragons") else analyze_partial_log(data)
        report["source"] = {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if args.team:
            report["evaluated_team"] = args.team
            official = report["official_result"]
            winner = official.get("winner") if official else None
            report["outcome"] = ("unknown" if not official or not official.get("terminated") else
                "draw" if winner is None else "win" if winner == args.team else "loss")
        if args.summary_only:
            for field in ("trajectory", "deaths", "death_groups", "splits"):
                report.pop(field, None)
        reports.append(report)
    text = json.dumps(reports[0] if len(reports) == 1 else reports, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
