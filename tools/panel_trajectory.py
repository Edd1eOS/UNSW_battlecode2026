"""Read-only whole-match accounting for frozen external panel results.

No matches, bot inputs or source mutations are performed. The result JSON,
replay bytes, initial bodies and formal terminal score are checked together.
Gross food/payment is reported only when every executed update reconciles.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

try:
    from .audit_online import load_replay
    from .trajectory_metrics import analyze_replay, ReplayValidationError
except ImportError:
    from audit_online import load_replay
    from trajectory_metrics import analyze_replay, ReplayValidationError


class PanelValidationError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pos(value: Any) -> tuple[int, int]:
    return (int(value["x"]), int(value["y"])) if isinstance(value, dict) else tuple(map(int, value))


def normalized_initial(items):
    return sorted((int(d["id"]), d["team"], tuple(pos(p) for p in d["body"])) for d in items)


def terminal_signature(result):
    keys = ("dragonCount", "queenLength", "longestDragon", "totalLength")
    if not isinstance(result, dict) or not result.get("terminated"):
        raise PanelValidationError("Terminated formal result is required")
    try:
        return (result["winner"], result["endReason"],
                *(tuple(int(result["team" + team][k]) for k in keys) for team in "AB"))
    except (KeyError, TypeError, ValueError) as error:
        raise PanelValidationError("Incomplete formal terminal scores") from error


def executed_details(data, core):
    """Official actions.cc sequence, correlated with complete replay updates.

    A failed step emits no update and consumes no food/payment. The free quota
    is fixed at action-start length; successful paid updates each cost one.
    Pearl clearance must agree with the head and the complete body delta.
    """
    live, lives = {}, {}
    for d in data["initial_dragons"]:
        identity, body = int(d["id"]), [pos(p) for p in d["body"]]
        live[identity] = {"team": d["team"], "body": body}
        lives[identity] = {"id": identity, "team": d["team"], "is_queen": identity <= 1,
                           "birth_round": None, "birth_parent": None, "birth_capital": len(body),
                           "peak_length": len(body), "net_update_growth": 0, "food": 0,
                           "paid": 0, "successful_steps": 0, "death": None}
    pearls, pending = set(), set()
    issues, rounds = [], []
    round_num, actor, action = None, None, None

    def issue(message):
        if message not in issues and len(issues) < 30:
            issues.append(message)

    def close_turn():
        if pending:
            issue("Pearl clearance without a matching successful head update")
            pending.clear()

    def frame():
        if round_num is None:
            return
        rounds.append({"round": round_num, "teams": {
            team: {"worker_count": sum(i > 1 and d["team"] == team for i, d in live.items()),
                   "longest_worker": max((len(d["body"]) for i, d in live.items()
                                           if i > 1 and d["team"] == team), default=0),
                   "recorded_food": sum(d["food"] for d in lives.values() if d["team"] == team),
                   "recorded_paid": sum(d["paid"] for d in lives.values() if d["team"] == team),
                   "recorded_net_update_growth": sum(d["net_update_growth"] for d in lives.values() if d["team"] == team),
                   "recorded_death_length": sum(d["death"]["last_recorded_length"] for d in lives.values()
                                                if d["team"] == team and d["death"])}
            for team in "AB"}})

    for index, event in enumerate(data["events"]):
        kind = event.get("type", event.get("kind"))
        if kind == "roundStart":
            close_turn();frame()
            round_num, actor, action = int(event["round"]), None, None
        elif kind == "tileChange":
            cell = pos(event["tile"])
            if event["hasPearl"]:
                pearls.add(cell)
            else:
                if cell not in pearls:
                    issue("Pearl clearance had no previously recorded present pearl")
                pearls.discard(cell)
                if round_num is not None:
                    pending.add(cell)
        elif round_num is None:
            continue  # Map bodies already include initialization updates.
        elif kind == "turnStart":
            close_turn();actor, action = int(event["id"]), None
        elif kind == "dragonIndicator":
            if int(event["id"]) in lives:
                lives[int(event["id"])]["last_indicator"] = event.get("text")
        elif kind == "dragonAction":
            identity = int(event["id"])
            raw = event.get("action")
            if identity in lives:
                lives[identity]["last_action"] = raw
            if identity != actor or identity not in live or not isinstance(raw, dict):
                issue("Action does not match a live current-turn dragon")
                action = None
            elif raw.get("kind") == "move" and isinstance(raw.get("steps"), list):
                steps = raw["steps"]
                if not steps or any(d not in "NESW" or len(d) != 1 for d in steps):
                    issue("Malformed recorded movement steps")
                action = {"id": identity, "steps": steps, "free": (len(live[identity]["body"]) + 3) // 4,
                          "successful": 0}
            else:
                action = None
        elif kind == "dragonUpdate":
            identity = int(event["id"])
            dragon = live[identity]
            old = len(dragon["body"])
            head, tail = pos(event["head"]), pos(event["tail"])
            body = [head, *dragon["body"]]
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            if body[-1] != tail:
                raise PanelValidationError(f"Unreconstructable tail at event {index}")
            delta = len(body) - old
            food = int(head in pending)
            pending.discard(head)
            paid = 0
            if action is None or action["id"] != identity or actor != identity:
                issue("Successful body update lacks its complete move action")
            else:
                step = action["successful"]
                if step >= len(action["steps"]):
                    issue("More successful updates than recorded action steps")
                elif event.get("facing") is not None and event["facing"] != action["steps"][step]:
                    issue("Successful update facing differs from its recorded step")
                paid = int(step >= action["free"])
                if paid and old <= 2:
                    issue("Successful paid step at unaffordable pre-step length")
                action["successful"] += 1
            if head in pearls:
                issue("Head update reached a pearl without a recorded clearance")
            if delta != food - paid:
                issue("Executed food/payment does not reconcile with a body update")
            dragon["body"] = body
            life = lives[identity]
            life["peak_length"] = max(life["peak_length"], len(body))
            life["net_update_growth"] += delta
            life["food"] += food;life["paid"] += paid;life["successful_steps"] += 1
        elif kind == "dragonSplit":
            parent, child = int(event["parentId"]), int(event["childId"])
            pb, cb = [pos(p) for p in event["parentBody"]], [pos(p) for p in event["childBody"]]
            if len(pb) + len(cb) != len(live[parent]["body"]):
                issue("Split does not conserve length")
            live[parent]["body"] = pb
            live[child] = {"team": event["team"], "body": cb}
            lives[child] = {"id": child, "team": event["team"], "is_queen": child <= 1,
                            "birth_round": round_num, "birth_parent": parent, "birth_capital": len(cb),
                            "peak_length": len(cb), "net_update_growth": 0, "food": 0,
                            "paid": 0, "successful_steps": 0, "death": None}
        elif kind == "dragonDeath":
            identity = int(event["id"])
            lives[identity]["death"] = {"round": round_num, "reason": event.get("reason"),
                                        "last_recorded_length": len(live[identity]["body"]),
                                        "last_indicator": lives[identity].get("last_indicator"),
                                        "last_action": lives[identity].get("last_action")}
            del live[identity]
    close_turn();frame()
    for identity, life in lives.items():
        life["final_length"] = len(live[identity]["body"]) if identity in live else 0
    if not core["quality"]["complete_match_verified"]:
        issue("Complete match state/terminal verification did not pass")
    for team in "AB":
        own = [d for d in lives.values() if d["team"] == team]
        net = sum(d["food"] - d["paid"] for d in own)
        if net != core["resources"][team]["recorded_update_net"]:
            issue("Gross ledger differs from the verified net body-update ledger")
    verified = not issues
    ledger, workers = {}, {}
    for team in "AB":
        own = [d for d in lives.values() if d["team"] == team]
        worker = [d for d in own if not d["is_queen"]]
        queens = [d for d in own if d["is_queen"]]
        ledger[team] = {"food_collected": sum(d["food"] for d in own) if verified else None,
                        "paid_step_cost": sum(d["paid"] for d in own) if verified else None,
                        "queen_food_collected": sum(d["food"] for d in queens) if verified else None,
                        "queen_paid_step_cost": sum(d["paid"] for d in queens) if verified else None,
                        "successful_steps": sum(d["successful_steps"] for d in own) if verified else None}
        workers[team] = {"recorded_peak_worker": max((d["peak_length"] for d in worker), default=0),
                         "final_longest_worker": max((d["final_length"] for d in worker), default=0),
                         "worker_net_update_growth": sum(d["net_update_growth"] for d in worker),
                         "worker_death_length": sum(d["death"]["last_recorded_length"] for d in worker if d["death"]),
                         "highest_recorded_workers": sorted(worker, key=lambda d: d["peak_length"], reverse=True)[:5]}
    if not verified:
        for life in lives.values():
            life["food"] = life["paid"] = life["successful_steps"] = None
        for f in rounds:
            for stats in f["teams"].values():
                stats["recorded_food"] = stats["recorded_paid"] = None
    return {"gross_ledger_verified": verified, "gross_ledger_issues": issues,
            "gross_resources": ledger, "workers": workers, "worker_trajectory": rounds,
            "dragons": list(lives.values()),
            "ledger_basis": "Correlated successful dragonUpdates, fixed action-start quota and present-pearl clearance; fatal attempts consume no payment",
            "peak_warning": "Worker peaks include inherited split capital; net_update_growth excludes birth/split transfers"}


def phase_metrics(core, detail, team):
    opponent = "B" if team == "A" else "A"
    phases = []
    previous = {t: {"recorded_food": 0, "recorded_paid": 0, "recorded_net_update_growth": 0,
                    "recorded_death_length": 0} for t in "AB"}
    for state, extra in zip(core["trajectory"], detail["worker_trajectory"]):
        if state["round"] != extra["round"]:
            raise PanelValidationError("Independent worker trajectory round alignment failed")
        own_q = state["scores"][team]["queen_length"] > 0
        enemy_q = state["scores"][opponent]["queen_length"] > 0
        name = ("both_queens_alive" if own_q and enemy_q else "candidate_queen_only" if own_q
                else "opponent_queen_only" if enemy_q else "both_queens_dead")
        if not phases or phases[-1]["queen_state"] != name:
            phases.append({"queen_state": name, "start_round": state["round"], "end_round": state["round"],
                           "round_count": 0, "candidate_leading_rounds": 0, "opponent_leading_rounds": 0,
                           "teams": {t: {"start_cumulative": previous[t].copy(), "end_cumulative": {},
                                         "recorded_peak_longest": 0, "recorded_peak_worker": 0} for t in "AB"}})
        phase = phases[-1]
        phase["end_round"] = state["round"];phase["round_count"] += 1
        phase["candidate_leading_rounds"] += state["leader"] == team
        phase["opponent_leading_rounds"] += state["leader"] == opponent
        for t in "AB":
            stats = phase["teams"][t]
            stats["end_cumulative"] = extra["teams"][t].copy()
            stats["recorded_peak_longest"] = max(stats["recorded_peak_longest"], state["scores"][t]["longest_dragon"])
            stats["recorded_peak_worker"] = max(stats["recorded_peak_worker"], extra["teams"][t]["longest_worker"])
            stats["end_scores"] = state["scores"][t]
        previous = extra["teams"]
    for phase in phases:
        for stats in phase["teams"].values():
            before, after = stats.pop("start_cumulative"), stats.pop("end_cumulative")
            for key in ("recorded_food", "recorded_paid", "recorded_net_update_growth", "recorded_death_length"):
                stats[key + "_in_phase"] = after[key] - before[key] if after[key] is not None and before[key] is not None else None
    return {"phases": phases,
            "basis": "Dense end-of-round Queen-state intervals; transition round is included in its ending phase, not an exact within-round partition",
            "queen_deaths": [d for d in core["deaths"] if d["is_queen"]],
            "queen_splits": [s for s in core["splits"] if s["parent_id"] <= 1],
            "unique_longest_losses": [d for d in core["deaths"] if d["was_unique_longest"] and d["longest_length_loss"] > 0],
            "final_advantage": core["final"],
            "candidate_continuous_lead": core["advantage"]["by_team"][team]}


def analyze_result(result_path: Path, *, decoder=load_replay):
    result_path = Path(result_path)
    raw_result = result_path.read_bytes()
    row = json.loads(raw_result)
    formal = row.get("formal_result")
    terminal_signature(formal)
    initial = row.get("initial_dragons")
    if not isinstance(initial, list) or not initial:
        raise PanelValidationError("Panel result has no full initial bodies")
    record = row.get("replay", {})
    replay_path = Path(record.get("path", "raw.replay"))
    if not replay_path.is_absolute():
        replay_path = result_path.parent / replay_path
    raw_replay = replay_path.read_bytes()
    if sha(raw_replay) != record.get("sha256") or len(raw_replay) != record.get("bytes"):
        raise PanelValidationError("Raw replay hash/size differs from immutable result record")
    data = decoder(replay_path)
    if data.get("input_sha256") is not None and data["input_sha256"] != sha(raw_replay):
        raise PanelValidationError("Decoder input hash differs from replay bytes")
    if data.get("initial_dragons") and normalized_initial(data["initial_dragons"]) != normalized_initial(initial):
        raise PanelValidationError("Embedded replay map differs from panel initial bodies")
    if terminal_signature(data.get("result")) != terminal_signature(formal):
        raise PanelValidationError("Replay terminal result differs from panel formal result")
    data = {**data, "initial_dragons": initial, "result": formal,
            "initial_state_provenance": "frozen_panel_result_initial_dragons_verified_against_embedded_replay"}
    core = analyze_replay(data)
    if "engine_last_round_index" in formal and core["trajectory"][-1]["round"] != int(formal["engine_last_round_index"]):
        raise PanelValidationError("Recorded final round differs from engine terminal round index")
    team = row["candidate_team"]
    if team not in "AB" or len(team) != 1:
        raise PanelValidationError("Invalid declared candidate team")
    detail = executed_details(data, core)
    return {"schema_version": 1, "job_id": row["id"], "phase": row["phase"], "map": row["map"],
            "seed": row["seed"], "candidate_team": team, "opponent_team": row["opponent_team"],
            "opponent": row["opponent"], "official_outcome": row["official_outcome"],
            "provenance": {"result_json_sha256": sha(raw_result), "replay_sha256": sha(raw_replay),
                           "map_sha256": row["map_sha256"], "decoder_bundle_sha256": data.get("decoder_bundle_sha256"),
                           "candidate_source_bundle_sha256": row["candidate"]["source_bundle_sha256"],
                           "candidate_wasm_sha256": row["candidate"]["wasm_sha256"]},
            "eligible_for_mechanism_comparison": bool(row["eligible_mechanism_result"] and core["quality"]["complete_match_verified"]),
            "runtime_eligibility": {"panel_eligible": row["eligible_mechanism_result"],
                                    "invalid_runtime_events": row.get("invalid_runtime_events"),
                                    "candidate_budget_margin_passed": row.get("candidate_budget_margin_passed")},
            "trajectory": core, "details": detail, "whole_match": phase_metrics(core, detail, team)}


def summary(reports):
    usable = [r for r in reports if r["eligible_for_mechanism_comparison"]]
    groups = {}
    for label, games in (("eligible", usable), ("runtime_ineligible", [r for r in reports if not r["eligible_for_mechanism_comparison"]])):
        values = {"games": len(games), "outcomes": dict(Counter(r["official_outcome"] for r in games))}
        for role in ("candidate", "opponent"):
            observations = []
            for r in games:
                t = r[role + "_team"]
                resource = r["trajectory"]["resources"][t]
                end = r["trajectory"]["final"]["scores"][t]
                gross = r["details"]["gross_resources"][t]
                observations.append({"net_body_update_growth": resource["recorded_update_net"],
                                     "death_length_loss": resource["last_recorded_length_removed_on_death"],
                                     "net_retained_length": resource["net_retained_length"],
                                     "final_longest": end["longest_dragon"], "final_total": end["total_length"],
                                     "recorded_peak_worker": r["details"]["workers"][t]["recorded_peak_worker"],
                                     "gross_food": gross["food_collected"], "gross_paid": gross["paid_step_cost"]})
            values[role] = {key + "_median": statistics.median([v[key] for v in observations if v[key] is not None])
                            if any(v[key] is not None for v in observations) else None
                            for key in ("net_body_update_growth", "death_length_loss", "net_retained_length", "final_longest", "final_total", "recorded_peak_worker", "gross_food", "gross_paid")}
            values[role]["final_queen_survivors"] = sum(r["trajectory"]["final"]["scores"][r[role + "_team"]]["queen_length"] > 0 for r in games)
            deaths = [d["death"] for r in games for d in r["details"]["dragons"]
                      if d["team"] == r[role + "_team"] and d["death"]]
            values[role]["death_reasons"] = dict(Counter(d["reason"] for d in deaths))
            values[role]["self_after_fallback"] = sum(d["reason"] == "S" and "FALLBACK" in (d.get("last_indicator") or "") for d in deaths)
            values[role]["self_after_normal_move"] = sum(d["reason"] == "S" and "GENERALIST MOVE" in (d.get("last_indicator") or "") for d in deaths)
        groups[label] = values
    return {"completed_replays": len(reports), "eligible_mechanism_replays": len(usable),
            "eligible_outcomes": dict(Counter(r["official_outcome"] for r in usable)),
            "gross_ledgers_verified": sum(r["details"]["gross_ledger_verified"] for r in reports),
            "candidate_source_hashes": sorted({r["provenance"]["candidate_source_bundle_sha256"] for r in reports}),
            "by_runtime_eligibility": groups,
            "scope": "Actual completed external games only; no rating conversion or causal strength claim"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--phase", choices=("discovery", "holdout", "all"), default="discovery")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reports, failures = [], []
    for path in sorted((args.panel / "games").rglob("result.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if args.phase != "all" and row.get("phase") != args.phase:
            continue
        try:
            reports.append(analyze_result(path))
        except (PanelValidationError, ReplayValidationError, OSError, ValueError, KeyError) as error:
            failures.append({"result_path": str(path), "error": f"{type(error).__name__}: {error}"})
    report = {"schema_version": 1, "summary": summary(reports), "validation_failures": failures, "games": reports}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**report["summary"], "validation_failures": len(failures)}), flush=True)


if __name__ == "__main__":
    main()
