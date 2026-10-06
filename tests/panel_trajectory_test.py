"""Panel ledger/provenance checks; no engine or bot execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.panel_trajectory import analyze_result, PanelValidationError
from tools.trajectory_metrics import analyze_replay


def dragon(identity, team, length):
    return {"id": identity, "team": team,
            "body": [{"x": x, "y": identity} for x in range(length)]}


def fixture():
    return {"formatVersion": 2, "initial_dragons": [dragon(0, "A", 3), dragon(1, "B", 3),
            dragon(2, "A", 4), dragon(3, "B", 4)],
            "events": [{"type": "roundStart", "round": 0}], "result": None}


def action(identity, steps):
    return [{"type": "turnStart", "id": identity},
            {"type": "dragonAction", "id": identity, "action": {"kind": "move", "steps": steps}}]


def update(identity, head, tail):
    return {"type": "dragonUpdate", "id": identity, "facing": "W",
            "head": {"x": head, "y": identity}, "tail": {"x": tail, "y": identity}}


def pearl(x, y, present):
    return {"type": "tileChange", "tile": {"x": x, "y": y}, "hasPearl": present}


class PanelTrajectoryTest(unittest.TestCase):
    def write(self, folder, data):
        core = analyze_replay(data)
        stats = core["final"]["scores"]
        result = {"terminated": True, "winner": core["final"]["leader"], "endReason": "roundLimit",
                  "engine_last_round_index": core["trajectory"][-1]["round"]}
        for team in "AB":
            result["team" + team] = {"dragonCount": stats[team]["dragon_count"], "queenLength": stats[team]["queen_length"],
                                     "longestDragon": stats[team]["longest_dragon"], "totalLength": stats[team]["total_length"]}
        data = copy.deepcopy(data);data["result"] = result
        raw = json.dumps(data).encode()
        replay = folder / "raw.replay";replay.write_bytes(raw)
        row = {"id": "discovery/external/sample-A", "phase": "discovery", "map": "sample", "seed": 1,
               "candidate_team": "A", "opponent_team": "B", "opponent": {"path": "external/sample"},
               "candidate": {"source_bundle_sha256": "source-frozen", "wasm_sha256": "wasm-frozen"},
               "map_sha256": "map-frozen", "initial_dragons": data["initial_dragons"], "formal_result": result,
               "official_outcome": "draw" if result["winner"] is None else "win" if result["winner"] == "A" else "loss",
               "eligible_mechanism_result": True, "candidate_budget_margin_passed": True,
               "replay": {"path": str(replay), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}}
        path = folder / "result.json";path.write_text(json.dumps(row), encoding="utf-8")
        return path, row

    def run_data(self, data):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = self.write(Path(temp), data)
            return analyze_result(path)

    def test_paid_neutral_food_and_fixed_start_quota(self):
        data = fixture()
        data["events"] += action(0, ["W", "W"])
        data["events"] += [pearl(-1, 0, True), pearl(-1, 0, False), update(0, -1, 2),
                           pearl(-2, 0, True), pearl(-2, 0, False), update(0, -2, 1)]
        report = self.run_data(data)
        self.assertTrue(report["details"]["gross_ledger_verified"])
        ledger = report["details"]["gross_resources"]["A"]
        self.assertEqual((ledger["food_collected"], ledger["paid_step_cost"]), (2, 1))
        self.assertEqual(report["trajectory"]["resources"]["A"]["recorded_update_net"], 1)
        self.assertEqual(report["provenance"]["candidate_source_bundle_sha256"], "source-frozen")

    def test_fatal_paid_attempt_does_not_consume_another_length(self):
        data = fixture();data["events"] += action(0, ["W", "W", "W"])
        data["events"] += [update(0, -1, 1), update(0, -2, -1), {"type": "dragonDeath", "id": 0, "reason": "A"}]
        report = self.run_data(data)
        self.assertTrue(report["details"]["gross_ledger_verified"])
        self.assertEqual(report["details"]["gross_resources"]["A"]["paid_step_cost"], 1)
        self.assertEqual(report["details"]["gross_resources"]["A"]["successful_steps"], 2)
        self.assertEqual(report["trajectory"]["resources"]["A"]["queen_length_removed_on_death"], 2)

    def test_missing_action_preserves_net_but_refuses_gross(self):
        data = fixture();data["events"] += [update(0, -1, 2)]
        report = self.run_data(data)
        self.assertEqual(report["trajectory"]["resources"]["A"]["recorded_update_net"], 1)
        self.assertFalse(report["details"]["gross_ledger_verified"])
        self.assertIsNone(report["details"]["gross_resources"]["A"]["food_collected"])

    def test_surviving_action_missing_neutral_updates_refuses_gross(self):
        data = fixture();data["events"] += action(0, ["W", "W"])
        data["events"] += [update(0, -1, 1)]
        report = self.run_data(data)
        self.assertFalse(report["details"]["gross_ledger_verified"])
        self.assertTrue(any("missing successful" in issue for issue in report["details"]["gross_ledger_issues"]))

    def test_clearance_without_known_pearl_refuses_gross(self):
        data = fixture();data["events"] += action(0, ["W"])
        data["events"] += [pearl(-1, 0, False), update(0, -1, 2)]
        report = self.run_data(data)
        self.assertFalse(report["details"]["gross_ledger_verified"])
        self.assertIsNone(report["details"]["dragons"][0]["food"])

    def test_split_is_birth_capital_not_income(self):
        data = fixture();data["initial_dragons"][2] = dragon(2, "A", 6)
        data["events"] += [{"type": "turnStart", "id": 2},
            {"type": "dragonSplit", "parentId": 2, "childId": 4, "team": "A",
             "parentBody": [[0, 2], [1, 2]], "childBody": [[5, 2], [4, 2], [3, 2], [2, 2]]}]
        report = self.run_data(data)
        child = next(d for d in report["details"]["dragons"] if d["id"] == 4)
        self.assertEqual((child["birth_capital"], child["peak_length"], child["net_update_growth"]), (4, 4, 0))
        self.assertEqual(report["details"]["gross_resources"]["A"]["food_collected"], 0)

    def test_init_arrays_and_objects_compare_equally(self):
        with tempfile.TemporaryDirectory() as temp:
            path, row = self.write(Path(temp), fixture())
            for d in row["initial_dragons"]:
                d["body"] = [[p["x"], p["y"]] for p in d["body"]]
            path.write_text(json.dumps(row), encoding="utf-8")
            self.assertTrue(analyze_result(path)["eligible_for_mechanism_comparison"])

    def test_modified_replay_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path, row = self.write(Path(temp), fixture())
            Path(row["replay"]["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(PanelValidationError, "hash/size"):
                analyze_result(path)

    def test_mismatched_initial_body_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path, row = self.write(Path(temp), fixture())
            row["initial_dragons"][0]["body"][0]["x"] = 999
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(PanelValidationError, "initial bodies"):
                analyze_result(path)

    def test_mismatched_formal_terminal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path, row = self.write(Path(temp), fixture())
            row["formal_result"]["teamA"]["queenLength"] = 999
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(PanelValidationError, "terminal result"):
                analyze_result(path)

    def test_runtime_ineligibility_separate_from_state_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            path, row = self.write(Path(temp), fixture())
            row["eligible_mechanism_result"] = False
            path.write_text(json.dumps(row), encoding="utf-8")
            report = analyze_result(path)
            self.assertFalse(report["eligible_for_mechanism_comparison"])
            self.assertTrue(report["trajectory"]["quality"]["complete_match_verified"])

    def test_phase_transition_and_final_longest_loss(self):
        data = fixture();data["initial_dragons"][2] = dragon(2, "A", 8)
        data["events"] += [{"type": "roundStart", "round": 1}, {"type": "turnStart", "id": 0},
                           {"type": "dragonDeath", "id": 0, "reason": "H"},
                           {"type": "dragonDeath", "id": 1, "reason": "H"},
                           {"type": "roundStart", "round": 2}, {"type": "turnStart", "id": 2},
                           {"type": "dragonDeath", "id": 2, "reason": "W"}]
        report = self.run_data(data)
        whole = report["whole_match"]
        self.assertEqual([p["queen_state"] for p in whole["phases"]], ["both_queens_alive", "both_queens_dead"])
        self.assertEqual(len(whole["queen_deaths"]), 2)
        self.assertEqual(whole["unique_longest_losses"][-1]["longest_length_loss"], 8)
        self.assertEqual(whole["final_advantage"]["criterion"], "elimination")


if __name__ == "__main__":
    unittest.main()
