"""KGTS panel contract checks; no matches or upstream host execution."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tools import oct7_kgts_panel as panel


class KgtsPanelTest(unittest.TestCase):
    def test_pinned_python_identity_keeps_gpl_and_no_fake_bot_wasm(self):
        records=panel.external_records()
        self.assertEqual(set(records),{"kgts-protocol-adapted"})
        record=records["kgts-protocol-adapted"]
        self.assertEqual(record["kind"],"python")
        self.assertEqual(record["argv"],["python","main.py"])
        self.assertEqual(record["license"],"GPLv3")
        self.assertIsNone(record["bot_specific_wasm"])
        self.assertEqual(record["source_files"]["main.py"]["sha256"],
                         "6d4faa341d2139d823786fba4cefd6a5c506939b02fd1b11efb7f8e65b13f444")

    def test_schedule_is_only_fixed_44_discovery_jobs(self):
        maps={p.stem:panel.map_record(p) for p in (panel.ROOT/"maps/current").glob("*.map")}
        jobs=panel.jobs_for(maps)
        self.assertEqual(len(jobs),44)
        self.assertEqual({j["seed"] for j in jobs},{2026100703})
        self.assertEqual({j["phase"] for j in jobs},{"discovery"})
        for name in maps:
            self.assertEqual({j["candidate_team"] for j in jobs if j["map"]==name},{"A","B"})
        self.assertEqual(sum(j["map_evidence"]=="online100_name_observed" for j in jobs),34)

    def test_rejects_holdout_and_other_seeds(self):
        for seeds in ({"holdout":[2026100791]}, {"discovery":[2026100701]},
                      {"discovery":[2026100703],"holdout":[2026100791]}):
            with self.assertRaises(ValueError):panel.validate_seeds(seeds)

    def test_added_source_file_cannot_silently_enter_python_pool(self):
        with tempfile.TemporaryDirectory(dir=panel.ROOT/"test-results") as temp:
            root=Path(temp)
            for name in ("kgts-gplv3","kgts-protocol-adapted"):
                shutil.copytree(panel.EXTERNAL/name,root/name,ignore=shutil.ignore_patterns("upstream.git","__pycache__"))
            (root/"kgts-protocol-adapted/source/unregistered.py").write_text("raise RuntimeError('never execute')\n")
            with self.assertRaisesRegex(ValueError,"Unexpected Python source files"):
                panel.external_records(root)

    def test_strict_plan_rejects_changed_schedule_even_with_new_checksum(self):
        with tempfile.TemporaryDirectory(dir=panel.ROOT/"test-results") as temp:
            directory=Path(temp)/"plan"
            panel.plan_panel(directory,panel.ROOT/"maps/current")
            self.assertEqual(len(panel.read_plan(directory)["jobs"]),44)
            wrapper=json.loads((directory/"plan.json").read_text())
            wrapper["plan"]["jobs"][0]["seed"]=2026100701
            wrapper["plan_sha256"]=panel.digest(panel.canonical(wrapper["plan"]))
            panel.write_json(directory/"plan.json",wrapper)
            with self.assertRaisesRegex(ValueError,"schedule"):
                panel.read_plan(directory)

    def test_candidate_cannot_include_gpl_external_headers(self):
        with tempfile.TemporaryDirectory(dir=panel.ROOT/"test-results") as temp:
            root=Path(temp)
            # Include a real, pinned external file solely to test packaging
            # isolation. The file is never compiled or imported.
            (root/"main.cpp").write_text('#include "'+str(panel.EXTERNAL/"kgts-protocol-adapted/source/helper.py").replace('\\','/')+'"\n')
            with self.assertRaisesRegex(ValueError,"isolated external source"):
                panel.source_bundle(root)

    def test_prior_candidate_budget_failure_blocks_resume_without_match(self):
        previous={"candidate_runtime_events":0,"infrastructure_errors":0,
                  "candidate_budget_margin_failures":1,"incomplete_attempts":[]}
        with patch.object(panel,"read_plan",return_value={}),patch.object(panel,"candidate_record",return_value={}),\
             patch.object(panel,"status",return_value={"phases":{"discovery":previous}}),patch.object(panel,"run_game") as run:
            with self.assertRaisesRegex(ValueError,"stopped"):
                panel.run_panel(Path("unused"),"discovery",None)
            run.assert_not_called()

    def test_formal_queen_axis_precedes_longest_and_total(self):
        raw=dict(rounds=499,winner="A",end_reason=1,a_dragons=2,b_dragons=3,
                 a_queen=5,b_queen=4,a_longest=6,b_longest=40,a_length=11,b_length=84,events=10)
        formal=panel.terminal_result(raw)
        self.assertEqual((formal["winner"],formal["decisive_axis"]),("A","queen"))


if __name__=="__main__":unittest.main()
