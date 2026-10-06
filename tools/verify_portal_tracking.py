"""Protocol-only two-frame portal/body regressions; no matches.

The first forced portal hop has an unseen endpoint. The second observation
shows the new head, but its true neck is the old head outside the window.
An ordinary east step remains legal; reversing the portal hits that neck.
The next terrain is deliberately finite: the check is immediate body safety,
not a claim of indefinite survival in the constructed corridor.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import verify_candidate as checker


def portal_fixtures():
    spec = importlib.util.spec_from_file_location("portal_protocol_frames", ROOT / "external-benchmarks/smoke_external.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DIM = 20

    def edge_and_parts(raw, row, column, remove_neck=False):
        lines = raw.splitlines()
        marker = next(i for i, line in enumerate(lines) if line.startswith("DRAGON_BODIES "))
        count = int(lines[marker].split()[1])
        if remove_neck:
            # The packet builder's synthetic adjacent neck is only used to
            # establish heading E. The real neck is (5,5), outside this window.
            parts = [line for line in lines[marker + 1:marker + 1 + count]
                     if line.split()[2:4] != ["14", "15"]]
            assert len(parts) == 1
            lines[marker:marker + 1 + count] = [f"DRAGON_BODIES {len(parts)}", *parts]
            count = len(parts)
        vertical_start = marker + 1 + count + 8
        values = lines[vertical_start + row].split()
        values[column] = "7"
        lines[vertical_start + row] = " ".join(values)
        return "\n".join(lines) + "\n"

    cases = []
    for identity in (0, 2):
        for food in (False, True):
            # Vertical mouths (6,5) and (15,15) preserve heading E. Only
            # mouth (6,5) is seen in frame one; frame two reveals its partner.
            first = module.frame(identity, [(5, 5), (4, 5)], round_num=100,
                                 units=64, edges=[((5, 5), (6, 5))])
            first = edge_and_parts(first, 3, 4)
            second = module.frame(identity, [(15, 15), (14, 15)],
                                  length=3 if food else 2, round_num=101,
                                  units=64, protocol=3,
                                  edges=[((15, 15), (16, 15))])
            second = edge_and_parts(second, 3, 3, remove_neck=True)
            cases.append({"name": f"portal-neck-id{identity}-unseen-{'food' if food else 'dry'}",
                          "init": f"ID {identity}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n",
                          "turns": [first, second], "constructed": True,
                          "expected_actions": ["MOVE E", "MOVE E"],
                          "actual_bodies": [[(5, 5), (4, 5)],
                                            [(15, 15), (5, 5), (4, 5)] if food
                                            else [(15, 15), (5, 5)]],
                          "scope": "The two observations are consistent with the forced first action; the east step in frame two survives immediately, without claiming future corridor escape."})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, nargs="?")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fixtures-only", action="store_true")
    args = parser.parse_args()
    cases = checker.fixtures() + portal_fixtures()
    if args.fixtures_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"matches_run": 0, "bot_executions": 0, "fixtures": cases}, indent=2), encoding="utf-8")
        return
    if args.candidate is None:
        parser.error("candidate is required unless --fixtures-only is selected")
    checker.fixtures = lambda: cases
    checker.run(args.candidate, args.out)
    report = json.loads(args.out.read_text(encoding="utf-8"))
    report["portal_tracking_driver_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["portal_expected_actions"] = {case["name"]: case["expected_actions"] for case in portal_fixtures()}
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
