"""Online external-panel evidence boundaries; no engines or matches."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from tools import audit_online_panel as panel

ROOT = Path(__file__).resolve().parents[1]


class OnlinePanelTest(unittest.TestCase):
    def test_actual_rendered_links_are_not_expanded_as_consecutive_ids(self):
        manifest = {"series": [{"series_id": 1249231, "opponent_team_id": 190, "opponent": "risq-v", "links": [
            {"href": "/battles/1249231", "text": "Game 1· Around UNSWL(longest dragon)"},
            {"href": "/battles/1249259", "text": "Game 2· MazeW"}]}]}
        rows = panel.selected_matches(manifest)
        self.assertEqual([r["match_id"] for r in rows], [1249231, 1249259])
        self.assertEqual([r["outcome"] for r in rows], ["loss", "win"])
        self.assertEqual([r["opponent_team_id"] for r in rows], [190, 190])

    def test_duplicate_or_missing_real_id_is_refused(self):
        for manifest in ({"matches": [{"match_id": 1}, {"match_id": 1}]},
                         {"series": [{"links": [{"href": "/teams/190"}]}]},
                         {"matches": []}):
            with self.assertRaises(ValueError):
                panel.selected_matches(manifest)

    def test_missing_terminal_ui_has_no_identity_or_terminal_ui_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui, evidence = panel.read_ui(Path(temporary), 1, 1035, 19, {})
        self.assertIsNone(ui)
        self.assertFalse(evidence["available"])
        self.assertIsNone(evidence["input_sha256"])

    def test_wrong_submission_proof_is_refused_before_source_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text(json.dumps({"submission_id": 15719, "platform_version": 14}), encoding="utf-8")
            (root / "freeze.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                panel.verify_source_record(root / "proof.json", root / "freeze.json", 18674, 19)

    def test_actual_ranked_ui_cannot_be_claimed_as_unranked_panel(self):
        bundle = json.loads(gzip.decompress((ROOT / "tests/fixtures/oct6-online100-ui.json.gz").read_bytes()))
        export = bundle["ui_exports"][0]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / f"{export['match_id']}-ui.json").write_text(export["raw_json_utf8"], encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unranked"):
                panel.read_ui(directory, export["match_id"], 1035, 14, {})

    def test_complete_official_raw_with_missing_ui_keeps_distinct_denominator(self):
        manifest = json.loads((ROOT / "docs/oct6-online100-raw-manifest.json").read_text(encoding="utf-8"))
        row = next(r for r in manifest["matches"] if r["match_id"] == 1239660)
        raw = ROOT / "test-results/online100-raw/M1239660.replay"
        if not raw.exists():
            self.skipTest("Original official replay is not committed")
        proof = {"submission_id": 15719, "platform_version": 14,
                 "source_bundle_sha256": manifest["source_proof"]["source_bundle_sha256"], "source_bytes_verified": True}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / raw.name
            path.write_bytes(raw.read_bytes())
            record, cached = panel.reconstruct(path, {"match_id": 1239660, "outcome": row["metrics"]["outcome"]}, None,
                {"available": False, "input_sha256": None}, proof, {"test": "captured evidence integration"})
        self.assertFalse(cached)
        self.assertTrue(record["metrics"]["whole_match_verified"])
        self.assertIsNone(record["metrics"]["UI_verified"])
        summary = panel.summarize([{"audit_status": "verified", "import_status": "imported", "metrics": record["metrics"]}], 1)
        self.assertEqual(summary["full_raw_verified"], 1)
        self.assertEqual(summary["terminal_UI_verified"], 0)
        self.assertEqual(summary["gross_ledger_verified"], 1)


if __name__ == "__main__":
    unittest.main()
