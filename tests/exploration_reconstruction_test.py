"""Pure replay-export contract checks; no engine or bot execution."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ReconstructionTest(unittest.TestCase):
    def test_import_does_not_parse_args_or_decode_a_replay(self):
        for name in ("oct7_reconstruct_portals", "oct7_exploration_death_audit"):
            self.assertTrue(callable(module(name).main))

    def test_disabled_bed_uses_maximum_gap_not_minimum(self):
        for name in ("oct7_reconstruct_portals", "oct7_exploration_death_audit"):
            exporter = module(name)
            self.assertEqual(exporter.initial_countdowns("TILE 1 2 9 0\nTILE 3 4 2 5"), {(3, 4): 0})
            with self.assertRaises(ValueError):
                exporter.initial_countdowns("TILE 1 2 0 5")

    def test_sonar_is_rejected_instead_of_inventing_empty_inbox(self):
        for name in ("oct7_reconstruct_portals", "oct7_exploration_death_audit"):
            exporter = module(name)
            exporter.assert_no_sonar({"events": [{"type": "roundStart", "round": 0}]})
            with self.assertRaises(ValueError):
                exporter.assert_no_sonar({"events": [{"type": "sonarPing", "senderId": 99}]})


if __name__ == "__main__":
    unittest.main()
