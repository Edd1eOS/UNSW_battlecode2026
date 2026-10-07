"""Protect the distinction between a recorded suicide and an unknown action."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import highrank_study as study

class SuicideLedgerTest(unittest.TestCase):
    def data(self,events):return {'events':events}
    def action(self):return {'type':'dragonAction','id':7,'action':{'kind':'suicide'}}
    def death(self,identity=7):return {'type':'dragonDeath','id':identity,'reason':'A'}
    def test_keep_death_and_other_actions(self):
        events=[self.action(),self.death(),{'type':'dragonAction','id':8,'action':None}]
        with patch.object(study,'executed_details',return_value={}) as fn:
            result=study.verified_suicide_ledger(self.data(events),{})
        self.assertEqual(fn.call_args.args[0]['events'],events[1:])
        self.assertEqual(result['verified_recorded_suicide_actions'],1)
    def test_do_not_accept_wrong_actor(self):
        with self.assertRaises(ValueError):study.verified_suicide_ledger(self.data([self.action(),self.death(8)]),{})
    def test_do_not_hide_successful_updates(self):
        with self.assertRaises(ValueError):study.verified_suicide_ledger(self.data([self.action(),{'type':'dragonUpdate','id':7},self.death()]),{})
    def test_require_same_turn_death(self):
        with self.assertRaises(ValueError):study.verified_suicide_ledger(self.data([self.action(),{'type':'turnStart','id':8},self.death()]),{})
    def test_unresolved_is_error(self):
        with self.assertRaises(ValueError):study.verified_suicide_ledger(self.data([self.action()]),{})

if __name__=='__main__':unittest.main()
