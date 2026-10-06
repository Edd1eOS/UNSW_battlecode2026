"""Actual captured online panel manifest, UI, and official raw integration."""
import json
from pathlib import Path
import unittest

from tools.audit_online import audit_match, load_replay
from tools.audit_online_panel import read_ui, selected_matches
from tools.import_online_replays import initial_checks, sha, validate_ui
from tools.panel_trajectory import executed_details
from tools.trajectory_metrics import analyze_replay

ROOT = Path(__file__).resolve().parents[1]


class Online51EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "docs/oct6-online51-manifest.json").read_text(encoding="utf-8"))

    def test_public_manifest_preserves_all_actual_links_and_denominators(self):
        rows = self.manifest["matches"]
        self.assertEqual(len(rows), 51)
        self.assertEqual(len({r["match_id"] for r in rows}), 51)
        for row in rows:
            parsed = selected_matches({"series": [{**{k: v for k, v in row["selection"].items()
                if k not in ("match_id", "selected_game_link", "selected_table_row", "outcome")},
                "links": [row["selection"]["selected_game_link"]]}]})
            self.assertEqual(parsed[0]["match_id"], row["match_id"])
            self.assertEqual(parsed[0]["outcome"], row["metrics"]["outcome"])
            self.assertTrue(row["metrics"]["UI_verified"])
            self.assertEqual(row["validation_issues"], [])
            self.assertEqual({s["replay_sha256"] for s in row["sources"]}, {row["replay_sha256"]})
        s = self.manifest["summary"]
        self.assertEqual(s["outcomes"], {"loss": 38, "win": 13})
        self.assertEqual(s["full_raw_verified"], 51)
        self.assertEqual(s["terminal_UI_verified"], 51)
        self.assertEqual(s["gross_ledger_verified"], 37)
        self.assertEqual(s["no_recorded_invalid_action_outcomes"], {"loss": 26, "win": 11})
        self.assertEqual(s["opponent_invalid_action_games"], 14)
        self.assertEqual(s["opponent_invalid_action_deaths"], 2483)
        self.assertEqual(s["our_invalid_action_deaths"], 0)
        self.assertEqual(s["loss_axes"], {"longest": 9, "queen": 9, "elimination": 20})

    def test_actual_v19_binary_and_terminal_ui_reconstruct(self):
        identity = 1249231
        row = next(r for r in self.manifest["matches"] if r["match_id"] == identity)
        path = ROOT / f"test-results/online51-raw/M{identity}.replay"
        ui_path = ROOT / f"test-results/online51-ui/{identity}-ui.json"
        if not path.exists() or not ui_path.exists():
            self.skipTest("Original official binary and terminal UI exports are ignored, not committed")
        self.assertEqual(sha(path.read_bytes()), row["replay_sha256"])
        ui, _ = read_ui(ui_path.parent, identity, 1035, 19, row["selection"])
        data = load_replay(path)
        initial_checks(data)
        own = [team for team in "AB" if data["teams"][team].get("botId") == "18674"]
        self.assertEqual(len(own), 1)
        core = analyze_replay(data)
        self.assertTrue(core["quality"]["complete_match_verified"], core["quality"]["issues"])
        detail = executed_details(data, core)
        audit = audit_match(data, {"match_id": identity, "our_team": own[0], "submission": 18674,
                                  "submission_verified": True, "complete": True, "ranked": False})
        validated = validate_ui(data, core, detail, audit, ui, 18674)
        self.assertTrue(validated["verified"], validated["issues"])
        self.assertFalse(ui["ranked"])
        self.assertTrue(detail["gross_ledger_verified"], detail["gross_ledger_issues"])
        for team in "AB":
            self.assertEqual(core["resources"][team]["reconstructed_balance_residual"], 0)
        self.assertEqual(detail["gross_resources"][own[0]], row["metrics"]["gross_resources"])


if __name__ == "__main__":
    unittest.main()
