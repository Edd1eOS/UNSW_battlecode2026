"""Oct7 evaluation boundaries; no candidate or strength match executes."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import external_panel as yesterday
from tools import oct7_external_panel as panel


class Oct7ExternalPanelTest(unittest.TestCase):
    def test_all_maps_and_both_sides_are_in_each_phase(self):
        maps = {p.stem: panel.map_record(p) for p in (panel.ROOT / "maps/current").glob("*.map")}
        jobs = panel.jobs_for(maps)
        self.assertEqual(len(maps), 22)
        self.assertEqual(len(jobs), 264)
        self.assertEqual(len({j["id"] for j in jobs}), len(jobs))
        for phase, seeds in panel.SEEDS.items():
            subset = [j for j in jobs if j["phase"] == phase]
            self.assertEqual({(j["map"], j["seed"], j["opponent"], j["candidate_team"]) for j in subset},
                             {(m, s, o, t) for m in maps for s in seeds for o in panel.REGISTRY for t in "AB"})
        self.assertFalse(set(panel.SEEDS["discovery"]) & set(panel.SEEDS["holdout"]))
        self.assertFalse(set(sum(panel.SEEDS.values(), ())) & set(sum(yesterday.SEEDS.values(), ())))

    def test_schedule_cannot_include_an_own_policy_as_external_opponent(self):
        records = panel.external_records()
        self.assertEqual(records, yesterday.external_records())
        self.assertEqual(set(records), {"sas-987", "official-murder"})
        for record in records.values():
            self.assertEqual(record["license"], "MIT")

    def test_incomplete_discovery_blocks_holdout_before_any_game(self):
        progress = {"complete": False, "candidate_runtime_events": 0, "infrastructure_errors": 0,
                    "candidate_budget_margin_failures": 0}
        with patch.object(panel, "read_plan", return_value={}), patch.object(panel, "candidate_record", return_value={}), \
             patch.object(panel, "status", return_value={"phases": {"discovery": progress}}), \
             patch.object(panel, "run_game") as game:
            with self.assertRaisesRegex(ValueError, "completed discovery"):
                panel.run_panel(Path("unused"), "holdout", None)
            game.assert_not_called()

    def test_same_holdout_seed_cannot_be_claimed_by_a_redesign(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            one, two = root / "one", root / "two"
            for directory in (one, two):
                directory.mkdir()
                (directory / "plan.json").write_text('{"fixed":true}', encoding="utf-8")
            first = {"source_bundle_sha256": "one", "wasm_sha256": "wasm-one"}
            second = {"source_bundle_sha256": "two", "wasm_sha256": "wasm-two"}
            ledger = root / "external-panel-holdout-exposure-one.json"
            panel.reserve_holdout(one, first, ledger, [2026100791])
            panel.reserve_holdout(one, first, ledger, [2026100791])
            with self.assertRaisesRegex(ValueError, "already opened"):
                panel.reserve_holdout(two, second, root / "external-panel-holdout-exposure-two.json", [2026100791])


if __name__ == "__main__":
    unittest.main()
