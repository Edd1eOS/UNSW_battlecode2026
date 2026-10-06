"""Sampled UI curve attribution and uncertainty, without browser/engine runs."""
import copy
import unittest

from tools.ui_trajectory import UIValidationError, aggregate, analyze_ui, parse_path, validate_layout


PROOF = {"viewBox": "0 0 100 42", "svgHeight": 42, "svgTopWithinPlot": 0,
         "ticks": [{"topPixels": "7px", "value": "10"},
                   {"topPixels": "22px", "value": "5"},
                   {"topPixels": "37px", "value": "0"}]}
LABELS = {"dragons": "Dragons alive", "queen": "Queen length",
          "longest": "Longest dragon alive", "total": "Total team length"}


def path(values, maximum, xs):
    return " ".join(f"{'M' if i == 0 else 'L'}{x:.2f},{37 - v * 30 / maximum:.2f}"
                    for i, (x, v) in enumerate(zip(xs, values)))


def fixture():
    xs = [5, 50, 95]
    values = {"dragons": [[2, 2, 2], [2, 3, 2]], "queen": [[3, 6, 0], [3, 4, 5]],
              "longest": [[3, 6, 5], [3, 4, 5]], "total": [[6, 8, 7], [6, 10, 8]]}
    maxima = {"dragons": 20, "queen": 10, "longest": 10, "total": 20}
    charts = [{"label": LABELS[metric], "viewBox": "0 0 100 42",
               "axis_text": f"{maximum}\n{maximum / 2:g}\n0\n0\n500",
               "paths": [{"class": "axis", "d": "M5 4V37H96"},
                         *[{"class": "series svelte-123", "style": "stroke: " + color,
                            "d": path(line, maximum, xs)} for color, line in zip(("red", "blue"), values[metric])]]}
              for metric, maximum in maxima.items()]
    return {"main": "Match 42\nSTATS\nRound 500 / 500", "charts": charts,
            "tables": [{"label": "Current team statistics", "rows": [
                ["", "Mine", "Enemy"], ["Queen", "Dead (r400)", "5"],
                ["Dragons alive", "2", "2"], ["Longest now", "5", "5"], ["Total length", "7", "8"]]}]}


class UITrajectoryTest(unittest.TestCase):
    def test_sampled_lead_then_loss_is_not_a_continuous_round_claim(self):
        result = analyze_ui(fixture(), layout_proof=PROOF, our_name="Mine", include_samples=True)
        self.assertEqual(result["outcome"], "loss")
        self.assertTrue(result["sampled_own_lead_then_terminal_loss"])
        self.assertEqual(result["sample_order_counts_by_name"]["Mine"], 1)
        self.assertEqual(result["first_own_leading_sample"], 1)
        self.assertEqual(result["sampling"]["drawn_samples"], 3)
        self.assertTrue(result["sampling"]["unsampled_intervals_exist"])
        self.assertFalse(result["quality"]["round_samples_are_complete"])
        self.assertNotIn("leading_rounds", result)
        self.assertNotIn("resources", result)
        self.assertEqual(result["rendered_sample_order_changes"][-1]["leader_name"], "Enemy")
        self.assertNotIn("continuous_rounds", result["rendered_sample_order_changes"][-1])
        phase = result["sample_orders_after_displayed_queen_deaths"]["Mine_queen_displayed_dead"]
        self.assertEqual(phase["drawn_samples_after_annotation"], 1)
        self.assertEqual(phase["sample_order_counts"]["Enemy"], 1)

    def test_four_endpoint_metrics_validate_series_to_named_columns(self):
        result = analyze_ui(fixture(), layout_proof=PROOF)
        self.assertEqual(result["series_to_ui_column"], [0, 1])
        self.assertTrue(result["quality"]["series_to_named_column_verified"])
        data = fixture()
        for chart in data["charts"]:
            chart["paths"][1:] = list(reversed(chart["paths"][1:]))
        swapped = analyze_ui(data, layout_proof=PROOF, our_name="Mine")
        self.assertEqual(swapped["series_to_ui_column"], [1, 0])
        self.assertTrue(swapped["sampled_own_lead_then_terminal_loss"])

    def test_table_order_is_not_assumed_to_be_engine_order(self):
        data = fixture()
        for row in data["tables"][0]["rows"]:
            row[1:] = list(reversed(row[1:]))
        data["queen_events"] = [{"round": "400", "text": "dragon 0 (queen) dies"}]
        result = analyze_ui(data, layout_proof=PROOF, our_name="Mine")
        self.assertEqual(result["terminal_ui"]["column_names"], ["Enemy", "Mine"])
        self.assertEqual(result["series_to_ui_column"], [1, 0])
        self.assertTrue(result["sampled_own_lead_then_terminal_loss"])
        self.assertNotIn("engine_team", result)

    def test_color_identity_aligns_a_reordered_chart(self):
        data = fixture()
        data["charts"][1]["paths"][1:] = list(reversed(data["charts"][1]["paths"][1:]))
        result = analyze_ui(data, layout_proof=PROOF, our_name="Mine")
        self.assertEqual(result["series_to_ui_column"], [0, 1])
        self.assertTrue(result["sampled_own_lead_then_terminal_loss"])

    def test_queen_zero_is_a_bracket_not_exact_death_length_or_time(self):
        result = analyze_ui(fixture(), layout_proof=PROOF, our_name="Mine")
        q = result["queen_rendered_zero_transitions"][0]
        self.assertEqual(q["displayed_dead_ui_round"], 400)
        self.assertLess(q["ui_axis_transition_bracket"][0], 400)
        self.assertGreater(q["ui_axis_transition_bracket"][1], 400)
        self.assertTrue(q["dead_annotation_within_sample_bracket"])
        self.assertEqual(q["nearest_sample_order_before"]["leader_name"], "Mine")
        self.assertEqual(q["first_zero_sample_order"]["leader_name"], "Enemy")
        self.assertNotIn("pre_death_length", q)

    def test_identical_endpoints_use_distinct_queen_death_brackets(self):
        data = fixture()
        rows = data["tables"][0]["rows"]
        rows[1] = ["Queen", "Dead (r100)", "Dead (r400)"]
        rows[-1] = ["Total length", "7", "7"]
        xs = [5, 23, 50, 77, 95]
        for chart in data["charts"]:
            maximum = float(chart["axis_text"].splitlines()[0])
            if chart["label"] == "Queen length":
                lines = [[3, 0, 0, 0, 0], [3, 3, 3, 0, 0]]
            else:
                value = {"Dragons alive": 2, "Longest dragon alive": 5, "Total team length": 7}[chart["label"]]
                lines = [[value] * 5, [value] * 5]
            for p, values in zip(chart["paths"][1:], lines):
                p["d"] = path(values, maximum, xs)
        result = analyze_ui(data, layout_proof=PROOF)
        self.assertEqual(result["series_to_ui_column"], [0, 1])
        self.assertEqual(result["quality"]["issues"], [])

    def test_equal_endpoints_and_equal_death_times_remain_ambiguous(self):
        data = fixture()
        rows = data["tables"][0]["rows"]
        rows[1] = ["Queen", "Dead (r400)", "Dead (r400)"]
        rows[-1] = ["Total length", "7", "7"]
        for chart in data["charts"]:
            chart["paths"][2]["d"] = chart["paths"][1]["d"]
        result = analyze_ui(data, layout_proof=PROOF, our_name="Mine")
        self.assertIsNone(result["series_to_ui_column"])
        self.assertIsNone(result["sampled_own_lead_then_terminal_loss"])
        self.assertIn("Endpoint attribution is ambiguous", result["quality"]["issues"])

    def test_high_scale_quantization_does_not_force_equal_queen_scores(self):
        data = fixture()
        queen = data["charts"][1]
        queen["axis_text"] = "10000\n5000\n0\n0\n500"
        for p, values in zip(queen["paths"][1:], ([3, 6, 0], [3, 4, 1])):
            p["d"] = path(values, 10000, [5, 50, 95])
        data["tables"][0]["rows"][1] = ["Queen", "Dead (r400)", "1"]
        result = analyze_ui(data, layout_proof=PROOF, include_samples=True)
        self.assertFalse(result["sample_orders"][-1]["order_resolved"])

    def test_no_scale_labels_refuses_silent_numeric_assumptions(self):
        data = fixture()
        del data["charts"][0]["axis_text"]
        with self.assertRaisesRegex(UIValidationError, "axis labels"):
            analyze_ui(data, layout_proof=PROOF)

    def test_stats_text_axis_fallback_is_explicit_label_evidence(self):
        data = fixture()
        lines = []
        for chart in data["charts"]:
            lines += [chart["label"], chart.pop("axis_text")]
        data["main"] = "Match 42\nSTATS\n" + "\n".join(lines) + "\nTOTALS THROUGH ROUND 500\nRound 500 / 500"
        self.assertTrue(analyze_ui(data, layout_proof=PROOF)["quality"]["series_to_named_column_verified"])

    def test_unaligned_samples_are_not_interpolated(self):
        data = fixture()
        data["charts"][0]["paths"][1]["d"] = data["charts"][0]["paths"][1]["d"].replace("50.00", "49.00")
        with self.assertRaisesRegex(UIValidationError, "no interpolation"):
            analyze_ui(data, layout_proof=PROOF)

    def test_axis_top_is_not_mistaken_for_numeric_max(self):
        proof = copy.deepcopy(PROOF)
        proof["ticks"][0]["topPixels"] = "4px"
        with self.assertRaisesRegex(UIValidationError, "max=Y7"):
            validate_layout(proof)

    def test_malformed_curve_does_not_enter_aggregate_usable_subset(self):
        data = fixture()
        data["tables"][0]["rows"][-1][1] = "1000"
        report = analyze_ui(data, layout_proof=PROOF)
        self.assertFalse(report["quality"]["series_to_named_column_verified"])
        summary = aggregate([report, {"error": "unsupported curve"}])
        self.assertEqual(summary["errors_or_missing_charts"], 1)
        self.assertEqual(summary["usable_sampled_ui_records"], 0)

    def test_verified_raw_data_has_priority_over_svg(self):
        raw = {"quality": {"complete_match_verified": True}, "trajectory": [{"round": 0}]}
        result = analyze_ui({}, layout_proof={}, raw_report=raw)
        self.assertEqual(result["source_kind"], "preferred_verified_raw_trajectory")
        self.assertFalse(result["ui_sampling_used_for_analysis"])

    def test_svg_path_parser_rejects_curves_relative_and_unsorted_paths(self):
        for value in ("M0,0 C1,2 3,4 5,6", "m0,0 l1,1", "M5,3 L4,2", "M5,3 L5,2"):
            with self.assertRaises(UIValidationError):
                parse_path(value)


if __name__ == "__main__":
    unittest.main()
