"""Paired audit contracts using real ledger APIs; no engine or bot launch."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import oct7_compare_external as compare
from tools.audit_online import load_replay
from tools.panel_trajectory import analyze_result
from tests import panel_trajectory_test as ledger_fixtures

fixture, action, update, pearl = (ledger_fixtures.fixture, ledger_fixtures.action,
                                ledger_fixtures.update, ledger_fixtures.pearl)


def compact(data):
    data = copy.deepcopy(data)
    data['map'] = 'MAP 10 10\n'
    with tempfile.TemporaryDirectory() as temp:
        path, _ = ledger_fixtures.PanelTrajectoryTest().write(Path(temp), data)
        decoded = load_replay(path.parent / 'raw.replay')
        return compare.compact_report(analyze_result(path), decoded)


def arm(report, *, eligible=True, gross=True):
    report = copy.deepcopy(report)
    report['eligible_for_mechanism_comparison'] = eligible
    report['gross_ledger_verified'] = gross
    row = {'phase':'discovery', 'opponent_id':'external', 'map':'sample', 'seed':1,
           'candidate_team':'A', 'job_id':'discovery/external/sample-1-A', 'result_source':'result.json',
           'official_outcome':report['official_outcome'], 'formal_result':report['terminal'],
           'invalid_runtime_events':{'A':0,'B':0}, 'map_sha256':'map', 'engine_sha256':'engine',
           'opponent_source_sha256':'source', 'opponent_wasm_sha256':'wasm', 'initial_signature':'initial',
           'report':report}
    return {'panel':'fixture', 'scheduled':1, 'completed':1, 'official_outcomes':{}, 'failures':[], 'rows':[row]}


class Oct7CompareExternalTest(unittest.TestCase):
    def test_paid_growth_and_sprint_window_are_real_updates(self):
        data = fixture()
        data['events'] += action(0,['W','W'])
        data['events'] += [pearl(9,0,True),pearl(9,0,False),update(0,9,2),
                           pearl(8,0,True),pearl(8,0,False),update(0,8,1)]
        report = compact(data)
        m = compare.view(report,0)['metrics']
        self.assertEqual((m['food'],m['paid'],m['net_income']), (2,1,1))
        self.assertEqual((m['successful_updates'],m['unique_movement_head_cells']), (2,2))
        self.assertEqual(m['unique_turn_window_cells'],49)  # Sprint does not supply two new observations.
        self.assertEqual(m['food_per_1000_successful_updates'],1000)
        self.assertEqual(m['queen_net_update_growth'],1)

    def test_common_prefix_does_not_hide_later_queen_death(self):
        early = fixture();early['events'].append({'type':'roundStart','round':1})
        late = copy.deepcopy(early)
        late['events'] += [{'type':'roundStart','round':2},*action(0,['W']),
                           {'type':'dragonDeath','id':0,'reason':'W'}]
        report = compare.compare_panels(arm(compact(early)),arm(compact(late)))
        p = report['pairs'][0]
        self.assertEqual(p['common_prefix']['candidate']['end_round'],1)
        self.assertEqual(p['common_prefix']['eligible_deltas']['queen_length'],0)
        self.assertEqual(p['whole_match']['eligible_deltas']['queen_length'],-3)
        self.assertEqual(p['whole_match']['eligible_deltas']['queen_death_length'],3)
        self.assertEqual(p['whole_match']['eligible_deltas']['net_retained_length'],-3)

    def test_missing_gross_keeps_net_but_excludes_resource_delta(self):
        r = compact(fixture())
        report = compare.compare_panels(arm(r),arm(r,gross=False))
        p = report['pairs'][0]
        self.assertTrue(p['eligible_pair']);self.assertFalse(p['gross_eligible_pair'])
        self.assertIn('net_retained_length',p['whole_match']['eligible_deltas'])
        self.assertNotIn('food',p['whole_match']['eligible_deltas'])
        self.assertNotIn('food_per_1000_successful_updates',p['whole_match']['eligible_deltas'])

    def test_single_side_invalid_retains_both_outcomes(self):
        r = compact(fixture());b,c = arm(r),arm(r,eligible=False)
        c['rows'][0]['official_outcome']='loss';c['rows'][0]['invalid_runtime_events']['A']=1
        report = compare.compare_panels(b,c);p=report['pairs'][0]
        self.assertEqual(p['candidate_outcome'],'loss')
        self.assertFalse(p['eligible_pair']);self.assertEqual(p['whole_match']['eligible_deltas'],{})
        self.assertEqual(p['candidate_invalid_runtime_events']['A'],1)

    def test_environment_change_refuses_pair_not_formal_result(self):
        r=compact(fixture());b,c=arm(r),arm(r)
        c['rows'][0]['opponent_wasm_sha256']='different'
        report=compare.compare_panels(b,c);p=report['pairs'][0]
        self.assertIn('opponent_wasm_sha256',p['issues'][0]);self.assertFalse(p['eligible_pair'])
        self.assertIn('candidate_formal_result',p)

    def test_unmatched_seed_and_duplicate_are_not_extra_successes(self):
        r=compact(fixture());b,c=arm(r),arm(r)
        c['rows'][0]['seed']=2
        report=compare.compare_panels(b,c)
        self.assertEqual(report['denominators']['matched_keys'],0)
        self.assertEqual(report['denominators']['unmatched'],2)
        b['rows'].append(copy.deepcopy(b['rows'][0]))
        report=compare.compare_panels(b,arm(r))
        self.assertEqual(report['denominators']['duplicate_key_conflicts'],1)
        self.assertEqual(report['denominators']['both_mechanism_eligible'],0)

    def test_split_birth_head_is_not_movement_or_income(self):
        data=fixture();data['initial_dragons'][2]['body']=[{'x':x,'y':2} for x in range(6)]
        data['events'] += [{'type':'turnStart','id':2},
                          {'type':'dragonSplit','parentId':2,'childId':4,'team':'A',
                           'parentBody':[[0,2],[1,2]],'childBody':[[5,2],[4,2],[3,2],[2,2]]}]
        m=compare.view(compact(data),0)['metrics']
        self.assertEqual((m['splits'],m['food'],m['net_body_update_growth']), (1,0,0))
        self.assertEqual((m['successful_updates'],m['unique_movement_head_cells']), (0,0))

    def test_zero_step_efficiency_is_unknown(self):
        m=compare.view(compact(fixture()),0)['metrics']
        self.assertIsNone(m['food_per_1000_successful_updates'])

    def test_paired_median_is_median_of_differences(self):
        pairs=[{'key':['discovery','external','map',1,'A'],'eligible_pair':True,'gross_eligible_pair':True,
                'whole_match':{'eligible_deltas':{'net_income':x}},'common_prefix':{'eligible_deltas':{}}}
               for x in (-100,1,2)]
        m=compare.summarize(pairs)['all']['whole_match']['net_income']
        self.assertEqual(m['paired_delta_median'],1)
        self.assertEqual((m['positive'],m['zero'],m['negative']),(2,0,1))

    def test_captured_official_replay_compact_identical_arm(self):
        folder=Path('test-results/external-panel-v5-20261006/games/holdout/sas-987/arena-2026100695-A')
        if not (folder/'result.json').exists():
            self.skipTest('Optional captured Oct6 raw replay not installed')
        data=load_replay(folder/'raw.replay')
        report=compare.compact_report(analyze_result(folder/'result.json'),data)
        pairs=compare.compare_panels(arm(report),arm(report))
        self.assertTrue(pairs['pairs'][0]['gross_eligible_pair'])
        self.assertTrue(all(v==0 for v in pairs['pairs'][0]['whole_match']['eligible_deltas'].values()))
        self.assertGreater(report['frames'][-1]['metrics']['unique_turn_window_cells'],0)

    def test_cached_analysis_refuses_modified_raw_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            data=fixture();data['map']='MAP 10 10\n'
            path,row=ledger_fixtures.PanelTrajectoryTest().write(folder,data)
            cache=folder/'cache'
            compare.analyze_compact(path,row,cache,{'test':'frozen'})
            self.assertEqual(len(list(cache.glob('*.json'))),1)
            (folder/'raw.replay').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Replay bytes differ'):
                compare.analyze_compact(path,row,cache,{'test':'frozen'})

    def test_infrastructure_attempt_is_unscored_and_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            panel=Path(temp);candidate=panel/'candidate';candidate.mkdir()
            frozen={'source_bundle_sha256':'source-frozen','wasm_sha256':'wasm-frozen'}
            (candidate/'freeze.json').write_text(json.dumps(frozen),encoding='utf-8')
            game=panel/'games/discovery/external/sample-A';game.mkdir(parents=True)
            path,row=ledger_fixtures.PanelTrajectoryTest().write(game,fixture())
            row.update(environment={'engine_wasm_sha256':'engine'}, peak={'A':{'points':0}},
                       invalid_runtime_events={'A':0,'B':0},map_evidence='observed',
                       opponent={'source_bundle_sha256':'external','wasm_sha256':'wasm'},formal_result=None)
            del row['official_outcome'];del row['replay']
            path.write_text(json.dumps(row),encoding='utf-8')
            job={k:row[k] for k in ('id','phase','map','map_evidence','seed','candidate_team','opponent_team')}
            job['opponent']='external'
            plan={'jobs':[job],'maps':{'sample':{'sha256':'map-frozen','initial_dragons':row['initial_dragons']}},
                  'environment':row['environment'],'opponents':{'external':row['opponent']}}
            with patch.object(compare.oct7_external_panel,'read_plan',return_value=plan):
                report=compare.load_panel(panel,'discovery',None,{'test':'frozen'})
            self.assertEqual((report['completed'],report['unscored_results']),(0,1))
            self.assertEqual(len(report['rows']),1)
            self.assertEqual(len(report['failures']),1)


if __name__=='__main__':
    unittest.main()
