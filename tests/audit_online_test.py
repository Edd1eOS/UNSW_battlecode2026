"""Offline parser/accounting checks; no bots or engine are launched."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_online import audit_match, audit_ui, initial_dragons, load_log, load_replay, load_ui, manifest_items, score_reason, selected_table_outcome


class AuditTests(unittest.TestCase):
    def test_real_terminal_ui_identity_and_unknown_event_details(self):
        data = load_ui(ROOT / "tests/fixtures/online-1239660-terminal-ui.json")
        row = audit_ui(data, {"match_id": 1239660, "our_team_id": 1035, "platform_version": 14})
        self.assertEqual(row["our_ui_column"], "B")
        self.assertIsNone(row["engine_team"])  # UI column order need not be engine order
        self.assertEqual(row["outcome"], "loss")
        self.assertEqual(row["direct_cause"]["score_axis"], "elimination")
        self.assertTrue(row["platform_version_verified"])
        self.assertEqual(row["queen"]["death"]["round"], 32)
        self.assertIsNone(row["queen"]["death"]["reason"])
        self.assertFalse(row["queen"]["terminal_alive"])
        self.assertEqual(row["teams"]["B"]["death_head_collision"], 25)
        self.assertEqual(row["teams"]["B"]["splits"], 28)
        self.assertEqual(row["observed_peak_workers"], [])
        self.assertNotIn("explicit_paid_segments", row["teams"]["B"])
        self.assertNotIn("friendly_head_deaths", row["teams"]["B"])
        self.assertEqual(row["strategy_inferences"], [])
        self.assertEqual(row["warnings"], [])

    def test_real_ui_column_order_is_not_queen_id_order(self):
        data = load_ui(ROOT / "tests/fixtures/online-1230137-terminal-ui.json")
        row = audit_ui(data, {"our_team_id": 1035, "platform_version": 14})
        self.assertEqual(row["our_ui_column"], "A")
        self.assertEqual(row["queen"]["id"], 1)  # real Queen 1 belongs to first named UI column
        self.assertEqual(row["queen"]["death"]["round"], 111)
        self.assertEqual(row["queen"]["death"]["reason"], "head_collision")
        self.assertEqual(row["outcome"], "win")
        self.assertEqual(row["direct_cause"]["score_axis"], "longest")
        self.assertEqual(row["warnings"], [])

    def test_ui_cursor_version_identity_and_filtered_event_guards(self):
        data = load_ui(ROOT / "tests/fixtures/online-1239660-terminal-ui.json")
        data["main"] = data["main"].replace("Round 176 / 176", "Round 100 / 176")
        row = audit_ui(data, {"our_team_id": 1035, "platform_version": 15})
        self.assertEqual(row["outcome"], "unknown")
        self.assertIsNone(row["direct_cause"]["score_axis"])
        self.assertFalse(row["platform_version_verified"])
        with self.assertRaisesRegex(ValueError, "disagrees"):
            audit_ui(data, {"our_team_id": 1035, "our_team": "A"})
        data["queen_events"] = [{"round": "031", "text": "dragon 1 (queen) dies. Reason: head-on collision"}]
        row = audit_ui(data, {"our_team_id": 1035})
        self.assertIsNone(row["queen"]["death"]["reason"])  # event at wrong round not accepted
        self.assertTrue(any("Queen death event disagrees" in w for w in row["warnings"]))
        data["queen_events"][0]["round"] = "032"
        row = audit_ui(data, {"our_team_id": 1035})
        self.assertEqual(row["queen"]["death"]["reason"], "head_collision")

    def test_real_excerpt_keeps_cause_levels_separate(self):
        fixture = json.loads((ROOT / "tests/fixtures/online-957659-audit-excerpt.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "excerpt.log"
            path.write_text(fixture["log"], encoding="utf-8")
            row = audit_match(load_log(path, fixture), fixture)
        self.assertEqual(row["queen"]["death"]["round"], 46)
        self.assertEqual(row["queen"]["death"]["counterpart_id"], 8)
        self.assertEqual(row["queen"]["death"]["collision_kind"], "enemy")
        self.assertEqual(row["queen"]["peak_length"], 17)
        self.assertEqual(row["teams"]["B"]["explicit_paid_segments"], 1)
        self.assertEqual(row["teams"]["B"]["confirmed_pearl_pickups"], 2)
        self.assertEqual(row["outcome"], "unknown")  # no terminal result in excerpt
        self.assertIsNone(row["direct_cause"]["score_axis"])
        self.assertEqual(row["strategy_inferences"], [])
        self.assertNotIn("requested_paid_steps", row["teams"]["B"])  # omitted rounds invalidate length

    def test_real_excerpt_provenance_when_original_available(self):
        fixture = json.loads((ROOT / "tests/fixtures/online-957659-audit-excerpt.json").read_text())
        path = ROOT / fixture["origin"]
        if not path.exists(): self.skipTest("ignored original is not present")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), fixture["origin_sha256"])
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual("\n".join(lines[n - 1] for n in fixture["source_lines"]) + "\n", fixture["log"])

    def test_real_full_log_friendly_head_deaths(self):
        path = ROOT / "test-results/r3-online-957659-full.log"
        if not path.exists(): self.skipTest("ignored full real log is not present")
        data = load_log(path, {"initial_dragons": initial_dragons((ROOT / "maps/current/trophy.map").read_text())})
        row = audit_match(data, {"our_team": "B", "match_id": 957659})
        self.assertEqual(row["teams"]["B"]["death_head_collision"], 28)
        self.assertEqual(row["teams"]["B"]["friendly_head_deaths"], 4)
        self.assertEqual(row["teams"]["B"]["enemy_head_deaths"], 24)
        self.assertEqual(row["teams"]["A"]["splits"], 79)
        self.assertEqual(row["teams"]["B"]["splits"], 26)
        self.assertEqual(row["queen"]["death"]["round"], 46)
        self.assertEqual(row["outcome"], "unknown")  # never invent terminal metadata

    def test_official_score_order(self):
        a = {"queenLength": 2, "longestDragon": 3, "totalLength": 5, "dragonCount": 2}
        b = {"queenLength": 1, "longestDragon": 100, "totalLength": 1000, "dragonCount": 20}
        result = {"terminated": True, "endReason": "roundLimit", "winner": "A", "teamA": a, "teamB": b}
        self.assertEqual(score_reason(result), "queen")
        b["queenLength"] = 2
        self.assertEqual(score_reason(result), "longest")
        b["longestDragon"] = 3
        self.assertEqual(score_reason(result), "total_length")
        result["endReason"] = "teamEliminated"
        self.assertEqual(score_reason(result), "elimination")
        result["terminated"] = False
        self.assertIsNone(score_reason(result))

    def test_selection_does_not_invent_inputs_or_engine_side(self):
        rows = {"rows": [{"cells": ["date", "Ranked", "ours", "W – L", "opponent", "Maze"],
                          "links": [{"href": "https://game.battlecode.au/battles/1239660"}]}]}
        items = manifest_items(rows)
        self.assertEqual(items[0]["match_id"], 1239660)
        self.assertNotIn("our_team", items[0])
        self.assertNotIn("replay", items[0])
        self.assertNotIn("result", items[0])
        named_row = {"cells": ["date", "Ranked", "opponent", "W\n–\nL", "ours", "Maze"],
                     "links": [{"href": "https://game.battlecode.au/teams/711"},
                               {"href": "https://game.battlecode.au/teams/1035"}]}
        self.assertEqual(selected_table_outcome(named_row, 1035), "loss")

    def test_replay_side_requires_verified_header_identity(self):
        data = {"events": [], "teams": {"A": {"id": 711}, "B": {"id": 1035}}}
        row = audit_match(data, {"our_team_id": 1035})
        self.assertEqual(row["our_team"], "B")
        with self.assertRaisesRegex(ValueError, "disagrees"):
            audit_match(data, {"our_team_id": 1035, "our_team": "A"})
        with self.assertRaisesRegex(ValueError, "uniquely"):
            audit_match(data, {"our_team_id": 999})

    def test_official_codec_and_body_reducer_from_saved_replays(self):
        # Archived LOCAL replays validate the official codec only; they are
        # never counted as true online samples or candidate strength evidence.
        paths = [ROOT / "test-results/cooperation-engine/feeding.replay",
                 ROOT / "test-results/v8-frontier-v4/maze-823-A.replay"]
        if not shutil.which("node") or not all(p.exists() for p in paths):
            self.skipTest("Node or ignored archived codec samples unavailable")
        for path in paths:
            with self.subTest(path=path.name):
                data = load_replay(path)
                row = audit_match(data, {"our_team": "A"})
                self.assertEqual(row["final_reconciliation"], {"A": True, "B": True})
                self.assertEqual(row["warnings"], [])
                if path.name == "feeding.replay":
                    self.assertEqual(row["teams"]["A"]["confirmed_pearl_pickups"], 2)
                    self.assertEqual(row["teams"]["A"]["death_self_body"], 1)


if __name__ == "__main__":
    unittest.main()
