"""Captured evidence integration, with optional ignored official binary replays.

The committed UI fixture is always checked. Real binary reconstruction checks
are skipped explicitly when the user has not supplied the original downloads.
No engine or bot is launched.
"""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_online import audit_match, audit_ui, load_replay, manifest_items
from tools.import_online_replays import initial_checks, validate_ui
from tools.panel_trajectory import executed_details
from tools.trajectory_metrics import analyze_replay

ROOT = Path(__file__).resolve().parents[1]


class OnlineRawReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads(gzip.decompress((ROOT / "tests/fixtures/oct6-online100-ui.json.gz").read_bytes()))
        cls.manifest = json.loads((ROOT / "docs/oct6-online100-raw-manifest.json").read_text(encoding="utf-8"))

    def test_raw_manifest_remains_the_actual_fixed_ui_selection(self):
        selected = manifest_items(self.bundle["selection"])
        rows = self.manifest["matches"]
        self.assertEqual([r["match_id"] for r in rows], [r["match_id"] for r in selected])
        self.assertEqual(len(rows), 100)
        exports = {r["match_id"]: r for r in self.bundle["ui_exports"]}
        for row in rows:
            ui = audit_ui(json.loads(exports[row["match_id"]]["raw_json_utf8"].lstrip("\ufeff")),
                          {"match_id": row["match_id"], "our_team_id": 1035, "platform_version": 14})
            self.assertEqual(ui["warnings"], [])
            self.assertEqual(row["metrics"]["outcome"], ui["outcome"])
            self.assertEqual(row["metrics"]["map"], ui["map"])
            self.assertEqual(row["metrics"]["terminal_longest"], ui["result"]["team" + ui["our_ui_column"]]["longestDragon"])
            self.assertEqual(row["validation_issues"], [])
            self.assertEqual(len(row["replay_sha256"]), 64)
            self.assertEqual({s["replay_sha256"] for s in row["sources"]}, {row["replay_sha256"]})
        self.assertEqual(self.manifest["summary"]["verified_outcomes"], {"loss": 54, "win": 46})
        self.assertEqual(self.manifest["summary"]["verified_loss_score_axes"], {"elimination": 20, "longest": 26, "queen": 8})

    def reconstruct_actual(self, identity):
        row = next(r for r in self.manifest["matches"] if r["match_id"] == identity)
        path = ROOT / "test-results/online100-raw" / f"M{identity}.replay"
        if not path.exists():
            self.skipTest("Original official binary replay is not committed; supply the fixed downloads to reconstruct")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["replay_sha256"])
        data = load_replay(path)
        self.assertTrue(initial_checks(data)["verified"])
        core = analyze_replay(data)
        self.assertTrue(core["quality"]["complete_match_verified"], core["quality"]["issues"])
        detail = executed_details(data, core)
        export = next(x for x in self.bundle["ui_exports"] if x["match_id"] == identity)
        ui = audit_ui(json.loads(export["raw_json_utf8"].lstrip("\ufeff")),
                      {"match_id": identity, "our_team_id": 1035, "platform_version": 14})
        own = next(team for team in "AB" if data["teams"][team].get("botId") == "15719")
        audit = audit_match(data, {"match_id": identity, "our_team": own, "submission": 15719,
                                   "submission_verified": True, "complete": True})
        validated = validate_ui(data, core, detail, audit, ui, 15719)
        self.assertTrue(validated["verified"], validated["issues"])
        for team in "AB":
            self.assertEqual(core["resources"][team]["reconstructed_balance_residual"], 0)
        return row, core, detail, own, audit

    def test_actual_complete_replay_agrees_with_ui_and_executed_ledger(self):
        row, core, detail, own, audit = self.reconstruct_actual(1239660)
        self.assertTrue(detail["gross_ledger_verified"], detail["gross_ledger_issues"])
        self.assertEqual(detail["gross_resources"][own], row["metrics"]["gross_resources"])
        self.assertEqual(audit["teams"][own]["friendly_head_deaths"], row["metrics"]["event_counts"]["friendly_head_deaths"])

    def test_actual_unsupported_action_preserves_net_but_refuses_gross(self):
        row, core, detail, own, _ = self.reconstruct_actual(1237739)
        self.assertFalse(detail["gross_ledger_verified"])
        self.assertIn("Unsupported recorded action kind", detail["gross_ledger_issues"])
        self.assertIsNone(detail["gross_resources"][own]["food_collected"])
        self.assertIsNone(detail["gross_resources"][own]["paid_step_cost"])
        self.assertEqual(core["resources"][own]["final_retained_length"], row["metrics"]["resources"]["final_retained_length"])


if __name__ == "__main__":
    unittest.main()
