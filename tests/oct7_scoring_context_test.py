"""Official scoring priority and conditional comparison; no engines."""
import copy
import unittest

from tools import oct7_scoring_context as c


def result(a,b,winner):
    keys=('dragonCount','queenLength','longestDragon','totalLength')
    return {'terminated':True,'winner':winner,'teamA':dict(zip(keys,a)),'teamB':dict(zip(keys,b))}


class ScoringContextTest(unittest.TestCase):
    def test_larger_longest_loses_to_queen(self):
        r=c.context(result((4,0,6,13),(4,3,3,11),'B'),'A')
        self.assertEqual(r['axis'],'queen')
        self.assertFalse(r['longest_rule_reached'])
        self.assertEqual(r['longest_margin'],3)

    def test_queen_tie_reaches_longest_and_then_total(self):
        r=c.context(result((2,3,3,5),(3,3,3,9),'B'),'A')
        self.assertTrue(r['longest_rule_reached'])
        self.assertEqual(r['axis'],'total')

    def test_elimination_precedes_equal_queens(self):
        r=c.context(result((0,0,0,0),(3,0,3,9),'B'),'A')
        self.assertEqual(r['axis'],'elimination')
        self.assertTrue(r['queen_equal'])
        self.assertFalse(r['longest_rule_reached'])

    def test_wrong_winner_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'winner'):
            c.context(result((2,3,3,5),(3,3,3,9),'A'),'A')

    def test_scoring_context_preserves_trade_and_relative_margin(self):
        b=result((5,0,40,90),(5,0,30,70),'A')
        cc=result((5,0,20,60),(5,0,5,50),'A')
        q1=result((5,9,89,230),(3,0,5,12),'A')
        q2=result((4,17,17,109),(3,0,6,13),'A')
        pairs=[{'key':['discovery','external','map',1,'A'],'eligible_pair':True,
                'baseline_formal_result':x,'candidate_formal_result':y,'baseline_outcome':'win','candidate_outcome':'win'}
               for x,y in ((b,cc),(q1,q2))]
        report=c.build({'actual_scope':'complete','pairs':pairs})
        s=report['summaries']['paired_eligible']
        self.assertEqual(s['pairs'],2)
        self.assertEqual(s['longest_rule_both_arms']['own_longest_delta']['paired_delta_median'],-20)
        self.assertEqual(s['longest_rule_both_arms']['own_minus_rival_longest_margin_delta']['paired_delta_median'],5)
        self.assertEqual(s['queen_decided_both_arms']['queen_margin_delta']['paired_delta_median'],8)

    def test_partial_scope_and_single_invalid_preserved(self):
        r=result((1,3,3,3),(1,0,3,3),'A')
        p={'key':['discovery','external','map',1,'A'],'eligible_pair':False,
           'baseline_formal_result':r,'candidate_formal_result':r,'baseline_outcome':'win','candidate_outcome':'win'}
        report=c.build({'actual_scope':'partial','pairs':[p]})
        self.assertEqual(report['actual_scope'],'partial')
        self.assertEqual(report['summaries']['all_formal']['pairs'],1)
        self.assertEqual(report['summaries']['paired_eligible']['pairs'],0)


if __name__=='__main__':
    unittest.main()
