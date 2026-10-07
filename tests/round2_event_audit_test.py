import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import round2_event_audit as audit


class EventAuditTests(unittest.TestCase):
    def test_diagnostic_only_changes_do_not_change_gameplay(self):
        base = {'events': [{'type': 'roundStart', 'round': 0},
                           {'type': 'dragonIndicator', 'id': 0, 'text': 'old'},
                           {'type': 'dragonAction', 'id': 0, 'action': {'kind': 'move', 'steps': ['N']}}]}
        new = {'events': [dict(e) for e in base['events']]}
        new['events'][1]['text'] = 'new diagnostics'
        new['events'].insert(1, {'type': 'dragonLog', 'id': 0, 'text': 'debug'})
        self.assertEqual(audit.events(base), audit.events(new))
        new['events'][-1] = {'type': 'dragonAction', 'id': 0, 'action': {'kind': 'move', 'steps': ['E']}}
        self.assertNotEqual(audit.events(base), audit.events(new))

    def test_resources_deaths_and_order_are_not_ignored(self):
        base = {'events': [{'type': 'tileChange', 'tile': {'x': 1, 'y': 2}, 'hasPearl': True},
                           {'type': 'dragonDeath', 'id': 2, 'reason': 'H'}]}
        self.assertEqual(audit.events(base), base['events'])
        self.assertNotEqual(audit.events(base), audit.events({'events': base['events'][::-1]}))

    def test_indicator_is_reset_at_each_turn_and_round_is_preserved(self):
        data = {'events': [{'type': 'roundStart', 'round': 4}, {'type': 'turnStart', 'id': 0},
                           {'type': 'dragonIndicator', 'id': 0, 'text': 'one'},
                           {'type': 'dragonAction', 'id': 0, 'action': {'kind': 'move', 'steps': ['N']}},
                           {'type': 'roundStart', 'round': 5}, {'type': 'turnStart', 'id': 0},
                           {'type': 'dragonAction', 'id': 0, 'action': {'kind': 'move', 'steps': ['E']}}]}
        rows = audit.turns(data)
        self.assertEqual([(r['round'], r['indicator']) for r in rows], [(4, 'one'), (5, '')])


if __name__ == '__main__':
    unittest.main()
