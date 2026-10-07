"""Offline lineage conservation against the existing strict replay tools."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tests import panel_trajectory_test as fixtures
from tools import oct7_family_capital as family
from tools import audit_online
from tools.panel_trajectory import analyze_result


def split(parent=2, child=4, pb=None, cb=None):
    return {'type': 'dragonSplit', 'team': 'A', 'parentId': parent, 'childId': child,
            'parentBody': pb or [[0,2],[1,2],[2,2],[3,2]], 'childBody': cb or [[5,2],[4,2]]}


def sample():
    data = fixtures.fixture()
    data['initial_dragons'][2] = fixtures.dragon(2, 'A', 6)
    data['events'] += [{'type':'turnStart','id':2},split()]
    data['events'] += [{'type':'roundStart','round':1}, *fixtures.action(4,['E']),
                       fixtures.pearl(6,2,True), fixtures.pearl(6,2,False),
                       {'type':'dragonUpdate','id':4,'facing':'E','head':[6,2],'tail':[4,2]}]
    return data


def audit(data):
    with tempfile.TemporaryDirectory() as folder:
        path,_ = fixtures.PanelTrajectoryTest().write(Path(folder), data)
        capture={}
        def decode(raw):
            capture['data']=audit_online.load_replay(raw)
            return capture['data']
        strict=analyze_result(path,decoder=decode)
        return family.audit_families(capture['data'],strict['trajectory'],strict['details'])


class FamilyCapitalTest(unittest.TestCase):
    def test_split_birth_is_transfer_and_founders_disjoint(self):
        result = audit(sample())
        root = next(f for f in result['families'] if f['founder_id']==2)
        self.assertEqual(root['lifetime_count'],2)
        self.assertEqual(root['terminal']['food'],1)
        self.assertEqual(root['terminal']['paid'],0)
        self.assertEqual(root['terminal']['net_update_growth'],1)
        self.assertEqual(root['terminal']['total_length'],7)
        self.assertEqual(root['terminal']['net_retained'],1)
        self.assertEqual(sum(f['terminal']['total_length'] for f in result['families'] if f['team']=='A'),10)
        cohort = result['splits'][0]['whole_after_split']
        self.assertEqual((cohort['net_update_growth'],cohort['retained_capital']),(1,7))
        self.assertIsNone(cohort['food'])

    def test_two_round_window_excludes_later_death(self):
        data=sample();data['events'] += [{'type':'roundStart','round':2}, {'type':'dragonDeath','id':4,'reason':'W'}]
        result=audit(data)
        s=result['splits'][0]
        self.assertEqual(s['two_round']['death_length_loss'],0)
        self.assertEqual(s['two_round']['net_retained'],1)
        self.assertEqual(s['whole_after_split']['death_length_loss'],3)
        self.assertEqual(s['whole_after_split']['net_retained'],-2)

    def test_cohort_excludes_children_born_before_that_split(self):
        data=sample();data['events'] += [split(2,6,[[0,2],[1,2]],[[3,2],[2,2]])]
        result=audit(data)
        s=result['splits'][1]
        self.assertEqual(s['capital_before'],4)
        self.assertEqual(s['whole_after_split']['descendant_count'],2)
        self.assertEqual(s['whole_after_split']['retained_capital'],4)
        self.assertEqual(s['whole_after_split']['net_update_growth'],0)
        root=next(f for f in result['families'] if f['founder_id']==2)
        self.assertEqual(root['terminal']['total_length'],7)
        self.assertEqual(root['lifetime_count'],3)

    def test_cohort_includes_later_descendant_capital_without_birth_income(self):
        data=sample();data['events'] += [{'type':'roundStart','round':2}, *fixtures.action(4,['E']),
            fixtures.pearl(7,2,True),fixtures.pearl(7,2,False),
            {'type':'dragonUpdate','id':4,'facing':'E','head':[7,2],'tail':[4,2]},
            {'type':'roundStart','round':3}, {'type':'turnStart','id':4},
            split(4,6,[[7,2],[6,2]],[[4,2],[5,2]])]
        result=audit(data)
        first=result['splits'][0]['whole_after_split']
        self.assertEqual((first['descendant_count'],first['retained_capital'],first['net_update_growth']),(3,8,2))

    def test_last_round_split_window_is_explicitly_truncated(self):
        data=sample();data['events'] += [split(2,6,[[0,2],[1,2]],[[3,2],[2,2]])]
        s=audit(data)['splits'][-1]['two_round']
        self.assertTrue(s['truncated'])
        self.assertEqual((s['requested_end_round'],s['end_round']),(2,1))

    def test_forecast_is_telemetry_and_not_real_income(self):
        data=sample();data['events'].insert(2,{'type':'dragonIndicator','id':2,
            'text':'GENERALIST SPLIT joint_food_est=4 joint_paid_est=1 joint_complete=1'})
        result=audit(data);s=result['splits'][0]
        self.assertEqual(s['reported_forecast_net'],3)
        self.assertEqual(s['two_round']['net_update_growth'],1)
        data['events'][2]['text']='GENERALIST SPLIT joint_complete=1'
        self.assertIsNone(audit(data)['splits'][0]['reported_forecast_net'])

    def test_incomplete_actions_refuse_gross_but_preserve_body_proof(self):
        data=sample();data['events']=[e for e in data['events'] if e['type']!='dragonAction']
        result=audit(data)
        self.assertFalse(result['gross_ledger_verified'])
        root=next(f for f in result['families'] if f['founder_id']==2)
        self.assertIsNone(root['terminal']['food'])
        self.assertEqual(root['terminal']['net_update_growth'],1)

    def test_nonpartitioned_split_is_rejected_even_if_lengths_match(self):
        data=sample();data['events'][2]['childBody']=[[7,2],[4,2]]
        with self.assertRaisesRegex(ValueError,'partition'):
            audit(data)

    def test_initial_founders_align_and_later_ids_do_not(self):
        data=sample();b=audit(data)
        cdata=copy.deepcopy(data)
        for e in cdata['events']:
            if e.get('id')==4:e['id']=40
            if e.get('childId')==4:e['childId']=40
        c=audit(cdata)
        for arm in (b,c):arm.update(candidate_team='A',eligible=True)
        result=family.compare_family_reports(b,c)
        self.assertTrue(all(v==0 for f in result['families'] for v in f['whole_match']['eligible_deltas'].values()))
        c['initial_signature'][0]=(100,'A',((0,0),))
        with self.assertRaisesRegex(ValueError,'alignment'):
            family.compare_family_reports(b,c)

    def test_cache_checks_raw_bytes_before_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory)
            path,row=fixtures.PanelTrajectoryTest().write(directory,sample())
            report=family.analyze_path(path,directory/'cache')
            self.assertTrue(report['gross_ledger_verified'])
            cached=family.analyze_path(path,directory/'cache')
            compared=family.compare_family_reports(report,cached)
            self.assertTrue(all(v==0 for f in compared['families'] for v in f['whole_match']['eligible_deltas'].values()))
            Path(row['replay']['path']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'declared hash'):
                family.analyze_path(path,directory/'cache')

    def test_actual_official_replay_integration(self):
        path=Path('test-results/oct7-v5-panel/games/discovery/sas-987/slithery_fight-2026100701-B/result.json')
        if not path.exists():self.skipTest('Ignored captured replay unavailable in this checkout')
        result=family.analyze_path(path)
        self.assertTrue(result['gross_ledger_verified'])
        self.assertEqual(result['rounds_verified'],500)
        self.assertEqual(sum(f['terminal']['total_length'] for f in result['families'] if f['team']=='B'),374)
        self.assertEqual(sum(f['terminal']['net_update_growth'] for f in result['families'] if f['team']=='B'),1203)
        self.assertEqual(sum(f['terminal']['death_length_loss'] for f in result['families'] if f['team']=='B'),876)


if __name__=='__main__':
    unittest.main()
