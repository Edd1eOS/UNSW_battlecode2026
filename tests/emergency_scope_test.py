import unittest
from tools.oct7_emergency_scope import selected_records,summarize

class EmergencyScopeTest(unittest.TestCase):
 def test_zero_rejected_regular_turn_is_not_retained(self):
  data={'initial_dragons':[{'id':2,'team':'A'}],'events':[{'type':'roundStart','round':0},{'type':'turnStart','id':2},
   {'type':'dragonIndicator','id':2,'text':'GENERALIST HARVEST emergency_rejected=0'},
   {'type':'dragonAction','id':2,'action':{'kind':'move','steps':['N']}}]}
  rows,_=selected_records(data,'A');self.assertEqual(rows,[])
 def test_current_indicator_not_previous_turn_and_birth_not_income(self):
  data={'initial_dragons':[{'id':2,'team':'A'}],'events':[
   {'type':'roundStart','round':0},{'type':'turnStart','id':2},
   {'type':'dragonIndicator','id':2,'text':'GENERALIST SPLIT emergency_child_no_move=1 emergency_rejected=0'},
   {'type':'dragonAction','id':2,'action':{'kind':'split','size':2}},
   {'type':'dragonSplit','parentId':2,'childId':4,'team':'A'},
   {'type':'turnStart','id':4},{'type':'dragonAction','id':4,'action':{'kind':'split','size':2}},
   {'type':'roundStart','round':1},{'type':'turnStart','id':2},{'type':'dragonAction','id':2,'action':{'kind':'move','steps':['N']}}]}
  rows,first=selected_records(data,'A');self.assertEqual(len(rows),1);self.assertEqual(first[4]['kind'],'split')
  self.assertEqual(summarize(rows)['reported_child_no_first_move'],1)
  self.assertNotIn('food',summarize(rows))
 def test_rejected_fallback_count_is_not_saved_child(self):
  data={'initial_dragons':[{'id':2,'team':'A'}],'events':[{'type':'roundStart','round':0},{'type':'turnStart','id':2},
   {'type':'dragonIndicator','id':2,'text':'GENERALIST FALLBACK emergency_rejected=1'},
   {'type':'dragonAction','id':2,'action':{'kind':'move','steps':['N']}},{'type':'dragonDeath','id':2,'reason':'S'}]}
  rows,_=selected_records(data,'A');s=summarize(rows)
  self.assertEqual((s['selected_emergency'],s['reported_rejected_proposals']),(0,1))
 def test_truncated_cohort_excluded_and_unknown_not_dead(self):
  rows=[{'selected_emergency':True,'flags':{'emergency_child_unknown':1},'two_round':{'truncated':True,'net_retained':-8,'live_count':0}}]
  s=summarize(rows);self.assertEqual(s['complete_two_round_cohorts'],0);self.assertEqual(s['reported_child_no_first_move'],0)

if __name__=='__main__':unittest.main()
