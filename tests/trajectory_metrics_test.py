"""Whole-match accounting regressions; no bot or match execution."""
import unittest

from tools.trajectory_metrics import ReplayValidationError, analyze_partial_log, analyze_replay


def body(length, y=0):
    return [{"x": x, "y": y} for x in range(length)]


def dragon(identity, team, length):
    return {"id": identity, "team": team, "body": body(length, identity)}


def fixture(a_queen=3, b_queen=3, a_worker=4, b_worker=4):
    return {"initial_dragons": [dragon(0, "A", a_queen), dragon(1, "B", b_queen),
                                dragon(2, "A", a_worker), dragon(3, "B", b_worker)],
            "events": [], "result": None}


def start(round_num):
    return {"type": "roundStart", "round": round_num}


def turn(identity):
    return {"type": "turnStart", "id": identity}


def death(identity, reason="H"):
    return {"type": "dragonDeath", "id": identity, "reason": reason}


def grow(identity, old_length):
    return {"type": "dragonUpdate", "id": identity,
            "head": {"x": -1, "y": identity},
            "tail": {"x": old_length - 1, "y": identity}}


class TrajectoryMetricsTest(unittest.TestCase):
    def test_lexicographic_score_does_not_reward_a_swarm_over_queen(self):
        data = fixture(a_queen=4, b_queen=5, a_worker=50, b_worker=2)
        data["events"] = [start(0)]
        result = analyze_replay(data)
        self.assertEqual((result["final"]["leader"], result["final"]["criterion"]), ("B", "queen"))
        self.assertGreater(result["final"]["delta"]["total_length"], 0)
        self.assertEqual(result["advantage"]["by_team"]["A"]["leading_rounds"], 0)

    def test_fixed_queen_team_comes_from_map_declaration(self):
        data = fixture(a_queen=5, b_queen=4)
        data["initial_dragons"][0]["team"] = "B"
        data["initial_dragons"][1]["team"] = "A"
        data["events"] = [start(0), turn(0), death(0)]
        result = analyze_replay(data)
        self.assertEqual(result["initial"]["scores"]["B"]["queen_length"], 5)
        self.assertTrue(result["deaths"][0]["is_queen"])
        self.assertEqual(result["resources"]["B"]["queen_length_removed_on_death"], 5)

    def test_elimination_has_priority_and_both_eliminated_tie(self):
        data = fixture()
        data["events"] = [start(0), turn(0), death(0), death(2)]
        result = analyze_replay(data)
        self.assertEqual(result["final"]["criterion"], "elimination")
        self.assertEqual(result["final"]["leader"], "B")
        data["events"].extend([death(1), death(3)])
        self.assertEqual(analyze_replay(data)["final"]["criterion"], "tie")

    def test_initial_updates_are_not_applied_twice(self):
        data = fixture()
        data["events"] = [grow(0, 3), start(0)]
        result = analyze_replay(data)
        self.assertEqual(result["initial"]["scores"]["A"]["queen_length"], 3)
        self.assertEqual(result["final"]["scores"]["A"]["queen_length"], 3)
        self.assertEqual(result["quality"]["ignored_initialization_events"], 1)

    def test_continuous_lead_phase_change_and_loss(self):
        data = fixture(a_queen=5, b_queen=4, a_worker=8, b_worker=7)
        data["events"] = [start(0), start(1), turn(0), death(0), death(1),
                          start(2), turn(2), death(2), start(3)]
        result = analyze_replay(data)
        self.assertEqual([f["leader"] for f in result["trajectory"]], ["A", "A", "B", "B"])
        self.assertEqual([f["criterion"] for f in result["trajectory"]], ["queen", "longest", "elimination", "elimination"])
        self.assertEqual(result["advantage"]["by_team"]["A"]["longest_continuous_lead"], 2)
        self.assertEqual(result["advantage"]["by_team"]["A"]["first_lead_loss_round"], 2)

    def test_missing_round_splits_streak_and_does_not_claim_loss_time(self):
        data = fixture(a_queen=5)
        data["events"] = [start(0), start(2)]
        result = analyze_replay(data)
        self.assertEqual(result["advantage"]["missing_rounds"], [1])
        self.assertEqual(result["advantage"]["by_team"]["A"]["longest_continuous_lead"], 1)
        self.assertFalse(result["quality"]["complete_round_coverage"])

    def test_split_is_transfer_not_growth(self):
        data = fixture()
        data["events"] = [start(0), turn(2), {"type": "dragonSplit", "parentId": 2,
            "childId": 4, "team": "A", "parentBody": body(2, 2), "childBody": body(2, 4)}]
        result = analyze_replay(data)
        resource = result["resources"]["A"]
        self.assertEqual(result["final"]["scores"]["A"]["dragon_count"], 3)
        self.assertEqual(resource["net_retained_length"], 0)
        self.assertEqual(resource["recorded_positive_updates"], 0)
        self.assertEqual(resource["split_length_delta"], 0)
        self.assertEqual(resource["reconstructed_balance_residual"], 0)

    def test_nonconserving_split_is_an_audit_issue(self):
        data = fixture()
        data["events"] = [start(0), {"type": "dragonSplit", "parentId": 2,
            "childId": 4, "team": "A", "parentBody": body(3, 2), "childBody": body(2, 4)}]
        self.assertIn("Nonconserving split", analyze_replay(data)["quality"]["issues"][0])

    def test_queen_split_reduces_primary_score_without_spending_team_length(self):
        data = fixture(a_queen=5)
        data["events"] = [start(0), {"type": "dragonSplit", "parentId": 0,
            "childId": 4, "team": "A", "parentBody": body(3, 0), "childBody": body(2, 4)}]
        resource = analyze_replay(data)["resources"]["A"]
        self.assertEqual(resource["net_retained_length"], 0)
        self.assertEqual(resource["queen_net_retained_length"], -2)
        self.assertEqual(resource["queen_length_transferred_by_split"], 2)
        self.assertEqual(resource["queen_reconstructed_balance_residual"], 0)

    def test_growth_death_and_initial_capital_balance(self):
        data = fixture()
        data["events"] = [start(0), turn(2), grow(2, 4), start(1), turn(2), death(2, "O")]
        result = analyze_replay(data)
        resource = result["resources"]["A"]
        self.assertEqual(resource["initial_capital"], 7)
        self.assertEqual(resource["recorded_positive_updates"], 1)
        self.assertEqual(resource["last_recorded_length_removed_on_death"], 5)
        self.assertEqual(resource["net_retained_length"], -4)
        self.assertEqual(resource["reconstructed_balance_residual"], 0)
        self.assertIsNone(resource["food_collected"])
        self.assertIsNone(resource["paid_step_cost"])

    def test_unique_longest_loss_is_measured_after_queens_die(self):
        data = fixture(a_worker=9, b_worker=7)
        data["events"] = [start(0), turn(0), death(0), death(1), turn(2), death(2)]
        result = analyze_replay(data)
        worker = next(d for d in result["deaths"] if d["id"] == 2)
        self.assertTrue(worker["was_unique_longest"])
        self.assertTrue(worker["erased_own_lead_immediately"])
        self.assertEqual(worker["before"]["criterion"], "longest")
        self.assertEqual(worker["longest_length_loss"], 9)
        self.assertEqual(result["resources"]["A"]["death_groups_erasing_own_lead"], 1)

    def test_head_trade_group_avoids_transient_loss_claim(self):
        data = fixture(a_queen=5, b_queen=5, a_worker=7, b_worker=7)
        data["events"] = [start(0), turn(0), death(0), death(1)]
        result = analyze_replay(data)
        self.assertTrue(result["deaths"][1]["erased_own_lead_immediately"])
        self.assertFalse(result["death_groups"][0]["erased_lead"])
        self.assertEqual(result["resources"]["B"]["death_groups_erasing_own_lead"], 0)
        self.assertIsNone(result["final"]["leader"])

    def test_coincident_growth_is_not_attributed_to_group_deaths(self):
        data = fixture(a_queen=5, b_queen=4, a_worker=7, b_worker=7)
        data["events"] = [start(0), turn(0), death(0), death(1), grow(2, 7)]
        group = analyze_replay(data)["death_groups"][0]
        self.assertIsNone(group["death_only_after"]["leader"])
        self.assertEqual(group["observed_after"]["leader"], "A")
        self.assertEqual(group["coincident_updates_after_first_death"], 1)

    def test_terminal_scores_are_checked_against_official_result(self):
        data = fixture()
        data["events"] = [start(0)]
        data["result"] = {"terminated": True, "winner": None, "endReason": "roundLimit",
            "teamA": {"dragonCount": 2, "queenLength": 3, "longestDragon": 4, "totalLength": 7},
            "teamB": {"dragonCount": 2, "queenLength": 3, "longestDragon": 4, "totalLength": 7}}
        self.assertTrue(analyze_replay(data)["quality"]["terminal_score_verified"])
        data["result"]["teamB"]["totalLength"] = 99
        result = analyze_replay(data)
        self.assertFalse(result["quality"]["terminal_score_verified"])
        self.assertTrue(any("teamB" not in issue and "B.totalLength" in issue for issue in result["quality"]["issues"]))

    def test_executed_log_accounts_food_and_cost_not_requested_steps(self):
        data = fixture(a_queen=4)
        data["input_format"] = "text_log"
        data["events"] = [start(0), turn(0), {"type": "dragonAction", "id": 0,
            "action": {"kind": "move", "steps": list("EEEEEEEE")}},
            {"type": "logMove", "id": 0, "head": {"x": 10, "y": 0},
             "food": True, "paid": 1, "length": 4},
            turn(2), {"type": "logSplit", "parentId": 2, "childId": 4, "size": 2},
            start(1), turn(0), death(0)]
        result = analyze_replay(data)
        resource = result["resources"]["A"]
        self.assertEqual(resource["queen_food_collected"], 1)
        self.assertEqual(resource["queen_paid_step_cost"], 1)
        self.assertEqual(resource["net_retained_length"], -4)
        self.assertEqual(resource["executed_resource_balance_residual"], 0)
        self.assertFalse(result["quality"]["global_bodies_reconstructed"])
        self.assertFalse(result["quality"]["terminal_verdict_present"])

    def test_executed_length_mismatch_fails_instead_of_filling_gap(self):
        data = fixture()
        data["input_format"] = "text_log"
        data["events"] = [start(0), {"type": "logMove", "id": 2, "head": {"x": 0, "y": 2},
                                   "food": True, "paid": 0, "length": 100}]
        with self.assertRaisesRegex(ReplayValidationError, "length mismatch"):
            analyze_replay(data)

    def test_partial_log_leaves_unknown_worker_team_and_global_scores(self):
        data = {"input_format": "text_log", "identity_teams": {0: "A"}, "events": [start(0),
            {"type": "logMove", "id": 8, "food": True, "paid": 1},
            {"type": "logMove", "id": 0, "food": True, "paid": 0}], "result": None}
        result = analyze_partial_log(data)
        self.assertIsNone(result["final"])
        self.assertIsNone(result["advantage"])
        self.assertEqual(result["executed_counts"]["unknown"]["food_collected"], 1)
        self.assertEqual(result["executed_counts"]["A"]["food_collected"], 1)

    def test_bad_state_data_is_rejected(self):
        for mutation in (lambda d: d.update(initial_dragons=[]),
                         lambda d: d.update(events=[start(0), death(99)]),
                         lambda d: d.update(events=[start(0), {"type": "dragonUpdate", "id": 2,
                            "head": {"x": 7, "y": 7}, "tail": {"x": 100, "y": 100}}])):
            data = fixture()
            mutation(data)
            with self.assertRaises(ReplayValidationError):
                analyze_replay(data)

    def test_normal_logging_events_do_not_raise_state_audit_issues(self):
        data = fixture()
        data["events"] = [start(0), {"type": "dragonLog", "id": 0, "message": "hello"},
                          {"type": "dragonIndicator", "id": 0}]
        self.assertEqual(analyze_replay(data)["quality"]["issues"], [])

    def test_historical_queen_semantics_are_explicitly_unverified(self):
        data = fixture()
        data["formatVersion"] = 1
        data["events"] = [start(0)]
        result = analyze_replay(data)
        self.assertTrue(any("Queen score semantics" in issue for issue in result["quality"]["issues"]))
        self.assertFalse(result["quality"]["complete_match_verified"])


if __name__ == "__main__":
    unittest.main()
