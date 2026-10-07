"""Official fixed-reply birth contract, not a strength match."""
import unittest
from tests.investment_engine_contract_test import scene,length_at

class EmergencyBirthQuotaTest(unittest.TestCase):
    def test_long_child_has_length_based_fixed_free_quota_in_birth_turn(self):
        body=[(5,5),(4,5),(3,5),(2,5),(1,5),(1,6),(2,6),(3,6),(4,6),(5,6)]
        observed,replay=scene(body,6,child_action='EE')
        self.assertEqual(length_at(observed,1,2),4)
        self.assertEqual(length_at(observed,1,3),6)
        split=next(e for e in replay['events'] if e['type']=='dragonSplit')
        self.assertEqual((len(split['childBody']),split['childFacing']),(6,'E'))

if __name__=='__main__':unittest.main()
