"""Evidence-review denominator and causality guards; no engines or browser."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_online import audit_ui, load_ui
from audit_report import build_findings, render_markdown


def real_rows():
    inputs = [load_ui(ROOT / "tests/fixtures/online-1239660-terminal-ui.json"),
              load_ui(ROOT / "tests/fixtures/online-1230137-terminal-ui.json")]
    rows = [audit_ui(d, {"our_team_id": 1035, "platform_version": 14}) for d in inputs]
    for row in rows: row["selected_table_outcome"] = row["outcome"]
    return inputs, rows


class AuditReportTest(unittest.TestCase):
    def test_missing_defeat_stays_in_selected_denominator_and_case_list(self):
        inputs, rows = real_rows()
        rows.append({"match_id": 999999, "error": "not acquired", "outcome": "unknown", "selected_table_outcome": "loss"})
        report = build_findings({"matches": rows}, series_sources={r["match_id"]: d for r, d in zip(rows, inputs)})
        d = report["denominators"]
        self.assertEqual(d["selected_matches"], 3)
        self.assertEqual(d["terminal_matches"], 2)
        self.assertEqual(d["selected_losses"], 2)
        self.assertEqual(d["terminal_losses"], 1)
        self.assertEqual(d["queen_deaths_annotated"], 2)
        self.assertEqual(d["queen_death_causes_known"], 1)
        self.assertEqual(d["verified_linked_series"], 2)
        self.assertEqual(d["matches_without_verified_series"], 1)
        self.assertEqual(len(report["loss_cases"]), 2)
        missing = next(c for c in report["loss_cases"] if c["match_id"] == 999999)
        self.assertIsNone(missing["direct_terminal_rule"])
        self.assertEqual(missing["observed_own_cumulative_events"], {})
        self.assertFalse(missing["sampled_curve"]["usable"])
        self.assertIn("终局尚缺", render_markdown(report))

    def test_historical_max_difference_is_not_called_worker_death_or_paid_cost(self):
        _, rows = real_rows()
        report = build_findings({"matches": rows})
        case = report["loss_cases"][0]
        self.assertEqual(case["historical_max_to_terminal"]["historical_team_max"], 13)
        self.assertEqual(case["historical_max_to_terminal"]["terminal_team_max"], 0)
        self.assertEqual(case["historical_max_to_terminal"]["difference"], 13)
        self.assertEqual(case["direct_terminal_rule"], "elimination")
        self.assertNotIn("paid_steps", case)
        self.assertNotIn("peak_worker_death", case)
        self.assertIn("不对应单个单位的死亡损失", render_markdown(report))

    def test_sampled_loss_denominator_and_incompatible_terminal_exclusion(self):
        _, rows = real_rows()
        row = rows[0]
        fields = {"queenLength": "queen", "dragonCount": "dragons", "longestDragon": "longest", "totalLength": "total"}
        curve = {"match_id": row["match_id"], "source_kind": "sampled_ui_svg", "outcome": "loss", "our_name": "Jet2Holiday",
            "quality": {"series_to_named_column_verified": True, "issues": []},
            "terminal_ui": {"terminated": True, "column_names": [row["team_names"][side] for side in ("A", "B")],
                "scores_by_column": [{b: row["result"]["team" + side][a] for a, b in fields.items()} for side in ("A", "B")]},
            "sampling": {"drawn_samples": 10}, "sample_order_counts_by_name": {"Jet2Holiday": 1},
            "sampled_own_lead_then_terminal_loss": True}
        report = build_findings({"matches": rows}, {"matches": [curve]})
        self.assertEqual(report["denominators"]["usable_sampled_curve_losses"], 1)
        self.assertEqual(report["denominators"]["losses_with_any_own_leading_drawn_sample"], 1)
        self.assertEqual(report["loss_cases"][0]["sampled_curve"]["own_leading_samples"], 1)
        self.assertIn("不是持续领先", render_markdown(report))
        wrong = copy.deepcopy(curve)
        wrong["terminal_ui"]["scores_by_column"][0]["longest"] += 1
        report = build_findings({"matches": rows}, {"matches": [wrong]})
        self.assertEqual(report["denominators"]["usable_sampled_curve_matches"], 0)

    def test_duplicate_ids_are_not_independent_samples(self):
        _, rows = real_rows()
        with self.assertRaisesRegex(ValueError, "distinct"):
            build_findings({"matches": [rows[0], rows[0]]})


if __name__ == "__main__":
    unittest.main()
