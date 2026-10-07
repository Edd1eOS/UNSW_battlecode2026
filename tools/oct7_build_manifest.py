"""Bind completed Oct7 evidence bytes; read-only except the requested JSON file.

This collector neither runs bots nor promotes candidates. It verifies frozen
sources, maps, result identities and replay bytes. Full scoring/ledger audits
remain in the separately fingerprinted comparison reports.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

import oct7_external_panel as panel_driver

ROOT = Path(__file__).resolve().parents[1]


def within(path):
    path = (ROOT / path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Evidence path outside workspace")
    return path


def binding(path):
    path = within(path)
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def collect_panel(path):
    path = within(path)
    plan = panel_driver.read_plan(path)
    frozen = panel_driver.candidate_record(path)
    rows = []
    for job in plan["jobs"]:
        file = path / "games" / job["id"] / "result.json"
        if not file.exists():
            continue
        result = json.loads(file.read_text(encoding="utf-8"))
        if result["id"] != job["id"] or result["candidate"] != frozen:
            raise ValueError("Result candidate/job differs from its frozen plan")
        if any(result[key] != job[key] for key in job if key != "opponent"):
            raise ValueError("Result schedule fields differ from the frozen job")
        if result["environment"] != plan["environment"]:
            raise ValueError("Result execution environment differs")
        if result["map_sha256"] != plan["maps"][job["map"]]["sha256"]:
            raise ValueError("Result map identity differs")
        if result["opponent"] != plan["opponents"][job["opponent"]]:
            raise ValueError("Result external identity differs")
        raw = binding(file.parent / "raw.replay") if result.get("replay") else None
        if raw and raw["sha256"] != result["replay"]["sha256"]:
            raise ValueError("Replay bytes differ from result")
        rows.append({"id": job["id"], "result": binding(file), "replay": raw,
                     "official_outcome": result.get("official_outcome"),
                     "eligible_mechanism_result": result["eligible_mechanism_result"],
                     "formal_result": result.get("formal_result"),
                     "candidate_peak": result["peak"][job["candidate_team"]],
                     "candidate_runtime_events": result["invalid_runtime_events"][job["candidate_team"]],
                     "opponent_runtime_events": result["invalid_runtime_events"][job["opponent_team"]]})
    return {"plan": binding(path / "plan.json"), "freeze": binding(path / "candidate/freeze.json"),
            "candidate": frozen, "seeds": plan["seeds"], "environment": plan["environment"],
            "opponents": plan["opponents"], "maps": plan["maps"],
            "actual_status": panel_driver.status(path, plan), "result_bindings": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", action="append", type=Path, default=[])
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--evidence", action="append", type=Path, default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reports = []
    for path in args.report:
        data = json.loads(within(path).read_text(encoding="utf-8"))
        reports.append({"binding": binding(path), "actual_scope": data.get("actual_scope"),
                        "denominators": data.get("denominators"),
                        "all_paired_summary": data.get("summary", {}).get("all"),
                        "analysis_dependencies": data.get("analyzer_dependencies_sha256")})
    result = {"recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Evidence bindings; no self matches, strength adoption or Elo conversion",
              "collector": binding(Path(__file__)), "panels": [collect_panel(p) for p in args.panel],
              "comparison_reports": reports, "other_evidence": [binding(p) for p in args.evidence]}
    out = within(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"panels": len(result["panels"]), "reports": len(reports),
                      "results_bound": sum(len(p["result_bindings"]) for p in result["panels"]),
                      "manifest": binding(out)}))


if __name__ == "__main__":
    main()
