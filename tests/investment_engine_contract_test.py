"""Official physics with fixed replies, never own candidate versus own candidate.

The installed official engine executes tiny synthetic scenes. Replies after two
rounds intentionally end the fixture; these are unit checks, not strength games.
Map syntax: https://game.battlecode.au/docs/map-files
Order contract: https://game.battlecode.au/docs/execution-order
"""
from pathlib import Path
import re
import tempfile
import unittest

from unswbc.engine import DEBUG_ALL, DEBUG_LIMITS, EngineModule
from tools.audit_online import load_replay


def scene(parent_body, child_length, *, food=(), child_action="E", parent_next="E", child_next="E"):
    tiles = "\n".join(f"TILE {x} {y} 1 1" for x, y in food)
    body = " ".join(f"{x} {y}" for x, y in parent_body)
    map_bytes = (f"MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT {len(food)}\n{tiles}\nEDGE_COUNT 0\n"
                 "DRAGON_COUNT 3\nDRAGON 0 2 1 1 0 1\nDRAGON 1 2 18 18 19 18\n"
                 f"DRAGON 0 {len(parent_body)} {body}\n").encode()
    observed = []

    def reply(identity, block):
        round_no = int(re.search(rb"^ROUND (\d+)", block, re.M)[1])
        observed.append((round_no, identity, block.decode()))
        if round_no == 0:
            action = f"SPLIT {child_length}" if identity == 2 else "MOVE " + (child_action if identity == 3 else "N")
        elif round_no == 1:
            action = "MOVE " + (parent_next if identity == 2 else child_next if identity == 3 else "N")
        else:
            action = "LOG fixed fixture finished"  # Intentional stop, not bot policy.
        return (action + "\nENDTURN\n").encode()

    engine = EngineModule()
    engine.run(map_bytes, reply, on_notice=lambda _: None, debug=DEBUG_ALL | DEBUG_LIMITS, seed=2026100777)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "fixture.bc26replay"
        path.write_bytes(engine.replay("fixed-A", "fixed-B"))
        replay = load_replay(path)
    return observed, replay


BODY6 = [(5, 5), (4, 5), (3, 5), (3, 6), (4, 6), (5, 6)]
BODY8 = [(5, 5), (4, 5), (3, 5), (2, 5), (2, 6), (3, 6), (4, 6), (5, 6)]


def length_at(observed, round_no, identity):
    block = next(b for r, i, b in observed if (r, i) == (round_no, identity))
    return int(re.search(r"^LENGTH (\d+)", block, re.M)[1])


class InvestmentEngineContractTest(unittest.TestCase):
    def test_parent_stays_and_newborn_acts_in_birth_round_then_parent_precedes_child(self):
        observed, replay = scene(BODY6, 2, food=[(6, 6), (7, 6)], child_action="EE")
        self.assertEqual([(r, i) for r, i, _ in observed if r <= 1],
                         [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)])
        split = next(e for e in replay["events"] if e["type"] == "dragonSplit")
        self.assertEqual((split["parentId"], split["childId"], split["childFacing"]), (2, 3, "E"))
        self.assertEqual([(p["x"], p["y"]) for p in split["parentBody"]], BODY6[:4])
        self.assertEqual([(p["x"], p["y"]) for p in split["childBody"]], BODY6[:3:-1])
        self.assertEqual(length_at(observed, 1, 2), 4)
        self.assertEqual(length_at(observed, 1, 3), 3)  # 2 inherited + 2 food - 1 paid.
        self.assertIn("DIR E\n", next(b for r, i, b in observed if (r, i) == (0, 3)))

    def test_free_quota_is_fixed_at_start_even_when_four_grows_to_five(self):
        observed, _ = scene(BODY8, 4, food=[(6, 6), (7, 6)], child_action="EE")
        self.assertEqual(length_at(observed, 1, 2), 4)
        self.assertEqual(length_at(observed, 1, 3), 5)  # Second step stays paid.

    def test_next_pearl_cannot_pay_for_unaffordable_length_two_step(self):
        observed, replay = scene(BODY6, 2, food=[(7, 6)], child_action="EE")
        child_death = next(e for e in replay["events"] if e["type"] == "dragonDeath" and e["id"] == 3)
        self.assertEqual(child_death["reason"], "A")
        self.assertFalse(any((r, i) == (1, 3) for r, i, _ in observed))
        heads = [(e["head"]["x"], e["head"]["y"]) for e in replay["events"]
                 if e["type"] == "dragonUpdate" and e["id"] == 3]
        self.assertEqual(heads, [(6, 6)])  # First step stands; second never executes.

    def test_parent_cannot_enter_child_tail_before_child_next_turn(self):
        observed, replay = scene(BODY6, 2, parent_next="S")
        # Child first moves E: body becomes [(6,6),(5,6)]. Parent next turn tries
        # S onto that old tail. It is occupied until the child actually moves.
        parent_death = next(e for e in replay["events"] if e["type"] == "dragonDeath" and e["id"] == 2)
        self.assertEqual(parent_death["reason"], "O")
        self.assertTrue(any((r, i) == (1, 3) for r, i, _ in observed))


if __name__ == "__main__":
    unittest.main()
