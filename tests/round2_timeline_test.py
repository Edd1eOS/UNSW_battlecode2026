import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import round2_timeline as timeline


class TimelineTests(unittest.TestCase):
    def test_only_actual_common_rounds_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            pair={'key':['discovery','external','map',1,'A'],'issues':[],'gross_eligible_pair':True}
            reports={}
            for arm,values in [('baseline',[0,0,100]),('candidate',[1,3])]:
                path=folder/(arm+'.json');path.write_text('{}',encoding='utf-8')
                provenance={'result_json_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                pair[arm+'_result']=str(path);pair[arm+'_provenance']=provenance
                reports[str(path)]={'provenance':provenance,'frames':[
                    {'round':r,'leader':0,'metrics':{k:v for k in timeline.KEYS}}
                    for r,v in enumerate(values)]}
            comparison=folder/'comparison.json'
            comparison.write_text(json.dumps({'analyzer_dependencies_sha256':{},'pairs':[pair]}),encoding='utf-8')
            with patch.object(timeline.primary,'dependencies',return_value={}),patch.object(
                    timeline.primary,'analyze_compact',side_effect=lambda p,*args:reports[str(p)]):
                result=timeline.build(comparison,folder/'cache')
            row=result['pairs'][0]
            self.assertEqual(row['common_last_round'],1)
            self.assertEqual(row['rounds_observed'],2)
            self.assertEqual(row['mean_over_actual_common_rounds']['queen_length'],2)
            self.assertEqual(result['checkpoint_summary']['0']['queen_length']['pairs'],1)
            self.assertEqual(result['checkpoint_summary']['49']['queen_length']['pairs'],0)
            self.assertIsNone(result['checkpoint_summary']['49']['queen_length']['mean'])

    def test_empty_stats_do_not_invent_zero_effect(self):
        self.assertEqual(timeline.stats([])['pairs'],0)
        self.assertIsNone(timeline.stats([])['mean'])
        self.assertEqual(timeline.stats([0,0])['mean'],0)


if __name__=='__main__':unittest.main()
