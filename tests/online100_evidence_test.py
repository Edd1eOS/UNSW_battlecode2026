"""Integrate two offline auditors against the fixed 100 real captured games.

No ignored test-results files, browser, engine, Node, API key or network needed.
The gzip contains original UI JSON text, not a synthetic engine fixture.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_online import audit_ui, manifest_items, selected_table_outcome
from audit_report import build_findings
from ui_trajectory import analyze_ui

FIXTURE = ROOT / "tests/fixtures/oct6-online100-ui.json.gz"
FIXTURE_SHA256 = "1023d9f00bb9a2502db556f00d0143c88375f126bc1c644350d3a83dd6052447"


class Online100EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blob = FIXTURE.read_bytes()
        cls.payload = json.loads(gzip.decompress(cls.blob))
        cls.audits, cls.curves, cls.sources = [], [], {}
        selection = {x["match_id"]: x["selected_table_row"] for x in manifest_items(cls.payload["selection"])}
        cls.provenance = cls.payload["provenance"]
        for exported in cls.payload["ui_exports"]:
            match_id = exported["match_id"]
            source = json.loads(exported["raw_json_utf8"].lstrip("\ufeff"))
            cls.sources[match_id] = source
            source["input_sha256"] = exported["original_sha256"]
            audit = audit_ui(source, {"match_id": match_id, "our_team_id": cls.provenance["our_team_id"],
                                      "platform_version": cls.provenance["platform_version"]})
            audit["selected_table_row"] = selection[match_id]
            audit["selected_table_outcome"] = selected_table_outcome(selection[match_id], cls.provenance["our_team_id"])
            name = audit["team_names"][audit["our_ui_column"]]
            curve = analyze_ui(source, layout_proof=cls.payload["chart_layout_proof"], our_name=name)
            cls.audits.append(audit)
            cls.curves.append(curve)

    def test_immutable_original_exports_and_zero_gzip_timestamp(self):
        self.assertEqual(hashlib.sha256(self.blob).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(struct.unpack("<I", self.blob[4:8])[0], 0)
        p = self.payload
        self.assertEqual(hashlib.sha256(p["selection_raw_json_utf8"].encode("utf-8")).hexdigest(), p["provenance"]["selection_file_original_sha256"])
        self.assertEqual(json.loads(p["selection_raw_json_utf8"].lstrip("\ufeff")), p["selection"])
        self.assertEqual(hashlib.sha256(p["chart_layout_proof_raw_json_utf8"].encode("utf-8")).hexdigest(), p["chart_layout_proof_original_sha256"])
        self.assertEqual([x["match_id"] for x in p["ui_exports"]], [x["match_id"] for x in manifest_items(p["selection"])])
        for exported in p["ui_exports"]:
            with self.subTest(match_id=exported["match_id"]):
                self.assertEqual(hashlib.sha256(exported["raw_json_utf8"].encode("utf-8")).hexdigest(), exported["original_sha256"])
                self.assertEqual(urlparse(exported["source_url"]).hostname, "game.battlecode.au")

    def test_100_version_labels_and_exact_terminal_scoring(self):
        self.assertEqual(len(self.audits), 100)
        self.assertEqual(len({r["match_id"] for r in self.audits}), 100)
        self.assertTrue(all(r["platform_version_verified"] is True for r in self.audits))
        self.assertTrue(all(r["platform_version"] == 14 for r in self.audits))
        self.assertTrue(all(r["ranked"] is True and r["terminal_cursor"] is True for r in self.audits))
        self.assertTrue(all(r["warnings"] == [] for r in self.audits))
        self.assertTrue(all(r["outcome"] == r["selected_table_outcome"] for r in self.audits))
        self.assertEqual(Counter(r["outcome"] for r in self.audits), {"win": 46, "loss": 54})
        self.assertEqual(Counter(r["direct_cause"]["score_axis"] for r in self.audits if r["outcome"] == "loss"),
                         {"longest": 26, "elimination": 20, "queen": 8})

    def test_all_75_queen_death_causes_match_terminal_rounds(self):
        dead = [r for r in self.audits if r["queen"]["terminal_alive"] is False]
        self.assertEqual(len(dead), 75)
        self.assertEqual(Counter(r["queen"]["death"]["reason"] for r in dead),
                         {"head_collision": 51, "wall": 14, "other_body": 10})
        self.assertTrue(all(r["queen"]["death"]["round"] == r["queen_death_rounds"][r["our_ui_column"]] for r in dead))
        self.assertTrue(all(r["queen"]["death"]["evidence"] == "official filtered Queen-death log entry" for r in dead))

    def test_all_100_sampled_curve_endpoints_and_named_mapping(self):
        self.assertEqual(len(self.curves), 100)
        for audit, curve in zip(self.audits, self.curves):
            with self.subTest(match_id=audit["match_id"]):
                self.assertEqual(curve["match_id"], audit["match_id"])
                self.assertEqual(curve["outcome"], audit["outcome"])
                self.assertTrue(curve["quality"]["series_to_named_column_verified"])
                self.assertTrue(curve["quality"]["terminal_endpoints_checked"])
                self.assertEqual(curve["quality"]["issues"], [])
                self.assertFalse(curve["quality"]["round_samples_are_complete"])

    def test_report_has_all_54_losses_and_explicit_series_and_unknowns(self):
        report = build_findings({"matches": self.audits, "selection": self.payload["selection"]},
                                {"matches": self.curves}, self.sources)
        self.assertEqual(len(report["loss_cases"]), 54)
        self.assertEqual(report["denominators"]["usable_sampled_curve_matches"], 100)
        self.assertEqual(report["denominators"]["usable_sampled_curve_losses"], 54)
        self.assertEqual(report["denominators"]["losses_with_any_own_leading_drawn_sample"], 53)
        self.assertEqual(report["denominators"]["verified_linked_series"], 21)
        self.assertEqual(report["denominators"]["matches_without_verified_series"], 0)
        self.assertEqual(sorted(g["selected_games"] for g in report["by_series"].values()), [2, 3] + [5] * 19)
        self.assertEqual(report["summary"]["longest_loss_past_peak_exceeds_rival_terminal"], 5)
        self.assertEqual(report["summary"]["longest_loss_past_peak_equals_rival_terminal"], 1)
        self.assertEqual(report["summary"]["longest_loss_past_peak_below_rival_terminal"], 20)
        self.assertTrue(all(r["unverified"] for r in report["loss_cases"]))

    def test_bundle_scope_excludes_credentials_and_raw_replay_claims(self):
        self.assertEqual(self.provenance["raw_event_replays"], 0)
        self.assertFalse(self.provenance["source_bytes_or_submission_mapping_verified"])
        self.assertFalse(self.provenance["included_auth_material"])
        self.assertTrue(all(r["input_format"] == "terminal_ui" and r["engine_team"] is None for r in self.audits))
        allowed = {"title", "main", "tables", "links", "queen_events", "charts", "chart_note", "input_sha256"}
        for source in self.sources.values():
            self.assertLessEqual(set(source), allowed)
            for link in source.get("links", []):
                parsed = urlparse(link["href"])
                self.assertEqual(parsed.hostname, "game.battlecode.au")
                self.assertIsNone(parsed.username)
                self.assertIsNone(parsed.password)
                self.assertNotIn("token=", parsed.query.lower())


if __name__ == "__main__":
    unittest.main()
