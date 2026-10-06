"""Panel checks; no compiler, candidate, upstream bot or strength match.

Two engine-interface tests use fixed replies for one synthetic collision turn.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import external_panel as panel


def result(**changes):
    raw = dict(rounds=499, winner="A", end_reason=1, a_dragons=2, b_dragons=3,
               a_queen=5, b_queen=4, a_longest=6, b_longest=40, a_length=11, b_length=84, events=50)
    raw.update(changes)
    return raw


class ExternalPanelTest(unittest.TestCase):
    def test_actual_engine_debug_is_replay_data_not_notice_stderr(self):
        from unswbc.engine import EngineModule, DEBUG_ALL, DEBUG_LIMITS
        map_bytes = (b"MAP 8 8\nUNIT_LIMIT 64\nTILE_COUNT 0\nEDGE_COUNT 0\n"
                     b"DRAGON_COUNT 2\nDRAGON 0 2 3 3 2 3\nDRAGON 1 2 4 3 5 3\n")
        notices, deaths = [], []
        engine = EngineModule()
        outcome = engine.run(map_bytes,
                             lambda identity, block: b"LOG ordinary debug fixture\nINDICATOR ordinary fixture\nMOVE E\nENDTURN\n",
                             on_death=lambda *event: deaths.append(event),
                             on_notice=notices.append, debug=DEBUG_ALL | DEBUG_LIMITS, seed=77)
        self.assertEqual(outcome.rounds, 0)
        self.assertEqual((outcome.a_dragons, outcome.b_dragons), (0, 0))
        self.assertEqual(len(deaths), 2)
        self.assertEqual(notices, [])
        self.assertGreater(len(engine.replay("fixed-protocol-A", "fixed-protocol-B")), 0)

    def test_actual_engine_rejects_defective_map_before_any_reply(self):
        from unswbc.engine import EngineModule, DEBUG_ALL, DEBUG_LIMITS
        map_bytes = (b"MAP 8 8\nUNIT_LIMIT 64\nTILE_COUNT 0\nEDGE_COUNT 1\nEDGE 0 2 7\n"
                     b"DRAGON_COUNT 2\nDRAGON 0 2 3 3 2 3\nDRAGON 1 2 4 3 5 3\n")
        reply = unittest.mock.Mock(return_value=b"MOVE E\nENDTURN\n")
        with self.assertRaisesRegex(RuntimeError, "portal 7 has 1 end"):
            EngineModule().run(map_bytes, reply, on_notice=lambda line: None,
                               debug=DEBUG_ALL | DEBUG_LIMITS, seed=77)
        reply.assert_not_called()

    def test_only_two_registered_external_policies_and_nonoverlapping_seeds(self):
        maps = {p.stem: panel.map_record(p) for p in (panel.ROOT / "maps/current").glob("*.map")}
        jobs = panel.jobs_for(maps)
        self.assertEqual({j["opponent"] for j in jobs}, {"sas-987", "official-murder"})
        discovery, holdout = ([j for j in jobs if j["phase"] == phase] for phase in ("discovery", "holdout"))
        self.assertEqual(len(discovery), 16)
        self.assertEqual(len(holdout), len(maps) * 4)
        self.assertFalse({j["seed"] for j in discovery} & {j["seed"] for j in holdout})
        for name in maps:
            self.assertEqual({(j["opponent"], j["candidate_team"]) for j in holdout if j["map"] == name},
                             {(o, side) for o in panel.REGISTRY for side in "AB"})

    def test_elimination_precedes_larger_queen_and_longest(self):
        official = panel.terminal_result(result(end_reason=0, a_dragons=0, a_queen=0,
                                                a_longest=0, a_length=0, b_queen=0, winner="B"))
        self.assertEqual((official["winner"], official["decisive_axis"]), ("B", "elimination"))

    def test_queen_precedes_swarm_and_longest(self):
        official = panel.terminal_result(result())
        self.assertEqual((official["winner"], official["decisive_axis"]), ("A", "queen"))
        self.assertEqual(official["round_count"], 500)

    def test_dead_queens_use_longest_then_total(self):
        longest = panel.terminal_result(result(a_queen=0, b_queen=0, winner="B"))
        total = panel.terminal_result(result(a_queen=0, b_queen=0, a_longest=40, a_length=50, winner="B"))
        self.assertEqual(longest["decisive_axis"], "longest")
        self.assertEqual(total["decisive_axis"], "total_length")

    def test_formal_tie_and_disagreeing_result(self):
        raw = result(a_queen=4, a_longest=40, a_length=84, winner=None)
        self.assertEqual(panel.terminal_result(raw)["decisive_axis"], "tie")
        with self.assertRaisesRegex(ValueError, "winner disagrees"):
            panel.terminal_result({**raw, "winner": "A"})

    def test_initial_sides_follow_map_declarations_not_id_parity(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "swapped.map"
            path.write_text("MAP 8 8\nDRAGON 1 2 7 7 6 7\nDRAGON 0 2 0 0 1 0\n")
            dragons = panel.map_record(path)["initial_dragons"]
            self.assertEqual([(d["id"], d["team"]) for d in dragons], [(0, "B"), (1, "A")])

    def test_outside_dependency_is_rejected_and_header_change_invalidates_freeze(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "candidate"
            project.mkdir()
            (root / "shared.hpp").write_text("#pragma once\nconstexpr int x=1;\n")
            source = project / "main.cpp"
            source.write_text('#include "../shared.hpp"\nint main(){return x;}\n')
            first = panel.source_bundle(project, root)[0]
            (root / "shared.hpp").write_text("#pragma once\nconstexpr int x=2;\n")
            self.assertNotEqual(first, panel.source_bundle(project, root)[0])
            source.write_text('#include "../../outside.hpp"\nint main(){}\n')
            with self.assertRaisesRegex(ValueError, "outside permitted"):
                panel.source_bundle(project, root)

    def test_external_source_and_wasm_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            freeze = json.loads((panel.EXTERNAL / "FREEZE.json").read_text())
            for relative in freeze["files"]:
                target = base / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(panel.EXTERNAL / relative, target)
            shutil.copyfile(panel.EXTERNAL / "FREEZE.json", base / "FREEZE.json")
            for name in panel.REGISTRY:
                for source in ("main.cpp", "helper.hpp", "bot.toml", "LICENSE"):
                    shutil.copyfile(panel.EXTERNAL / name / source, base / name / source)
            self.assertEqual(set(panel.external_records(base)), set(panel.REGISTRY))
            header = base / "sas-987/helper.hpp"
            original = header.read_bytes()
            header.write_bytes(original + b"\n// changed\n")
            with self.assertRaisesRegex(ValueError, "Upstream bytes changed"):
                panel.external_records(base)
            header.write_bytes(original)
            wasm = base / "official-murder/bot.wasm"
            wasm.write_bytes(wasm.read_bytes() + b"\0")
            with self.assertRaisesRegex(ValueError, "External freeze changed"):
                panel.external_records(base)

    def test_opened_holdout_cannot_be_reused_after_redesign(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "one", root / "two"
            first.mkdir(); second.mkdir()
            for directory in (first, second):
                (directory / "plan.json").write_text('{"plan":"fixed"}')
            ledger = root / "exposure.json"
            frozen = {"source_bundle_sha256": "candidate1", "wasm_sha256": "binary1"}
            panel.reserve_holdout(first, frozen, ledger)
            panel.reserve_holdout(first, frozen, ledger)
            with self.assertRaisesRegex(ValueError, "already opened"):
                panel.reserve_holdout(second, {**frozen, "source_bundle_sha256": "candidate2"}, ledger)

    def test_incomplete_discovery_cannot_start_holdout_or_any_game(self):
        progress = {"complete": False, "candidate_runtime_events": 0, "infrastructure_errors": 0,
                    "candidate_budget_margin_failures": 0}
        with patch.object(panel, "read_plan", return_value={}), patch.object(panel, "candidate_record", return_value={}), \
             patch.object(panel, "status", return_value={"phases": {"discovery": progress}}), \
             patch.object(panel, "run_game") as game:
            with self.assertRaisesRegex(ValueError, "completed discovery"):
                panel.run_panel(Path("unused"), "holdout", None)
            game.assert_not_called()

    def test_fresh_sas_child_first_frame_is_protocol3_and_contains_parent(self):
        case = panel.child_protocol_fixtures()["sas-987"]
        self.assertIn("ID 8\n", case["init"])
        self.assertIn("ECHOES 0 0 0 0 0\n", case["turn"])
        self.assertIn("DRAGON_BODIES 4\n", case["turn"])
        self.assertIn("A 0 2 5 W 1\n", case["turn"])

    def test_official_result_and_raw_replay_survive_ineligible_opponent_failure(self):
        # Pure callback doubles exercise the runner; no engine or bot executes.
        from unswbc.engine import MatchResult
        class FakePool:
            created = []
            def __init__(self, argv, key):
                self.created.append((argv, key))
            def close(self):
                pass
        class FakeBot:
            def __init__(self, pool, init, name):
                self.team = "A" if b"TEAM A" in init else "B"
                self.error = None
                self.live = (1234, 65536)
            def ask(self, block):
                self.error = "fixture opponent timeout" if self.team == "A" else None
                return b"MOVE E\n"
            def take_stderr(self):
                return b""
            def stop(self):
                pass
        class FakeEngine:
            names = None
            def run(self, map_bytes, reply, death, spawn, notice, debug, seed):
                self.seed = seed
                for identity, team in enumerate("AB"):
                    spawn(identity, f"ID {identity}\nTEAM {team}\nMAP 8 8\nUNIT_LIMIT 64\n".encode())
                    reply(identity, b"ROUND 0\nLENGTH 4\n")
                return MatchResult(**result(winner="B", a_queen=4, b_queen=5))
            def replay(self, a, b):
                self.names = (a, b)
                return b"callback-fixture-replay-not-a-real-game"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "maps").mkdir()
            data = b"MAP 8 8\n"
            (root / "maps/test.map").write_bytes(data)
            plan = {"maps": {"test": {"sha256": panel.digest(data), "initial_dragons": []}},
                    "opponents": {"sas-987": {"path": str(root / "external")}},
                    "environment": {}, "candidate_budget_margin_points": 90_000_000}
            job = {"id": "discovery/sas-987/test-123-B", "phase": "discovery", "opponent": "sas-987",
                   "map": "test", "seed": 123, "candidate_team": "B", "opponent_team": "A"}
            engine = FakeEngine()
            with patch("unswbc.engine.EngineModule", return_value=engine), \
                 patch("unswbc.sandbox.WasmPool", FakePool), patch("unswbc.sandbox.SandboxBot", FakeBot):
                row = panel.run_game(root, plan, {"label": "frozen-candidate"}, job)
            self.assertEqual(engine.names, ("sas-987", "frozen-candidate"))
            self.assertEqual(row["official_outcome"], "win")
            self.assertFalse(row["eligible_mechanism_result"])
            self.assertEqual(row["formal_result"]["decisive_axis"], "queen")
            self.assertEqual(row["runtime_errors"][0]["team"], "A")
            self.assertEqual(row["replay"]["sha256"], panel.digest(Path(row["replay"]["path"]).read_bytes()))
            self.assertIn(str(root / "external/bot.wasm"), FakePool.created[0][0])


if __name__ == "__main__":
    unittest.main()
