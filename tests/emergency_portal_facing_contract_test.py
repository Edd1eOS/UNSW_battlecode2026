"""Official portal-facing source contract; frozen candidate remains unchanged."""
import hashlib,json,re,sys,tempfile,unittest
from pathlib import Path
from unswbc.engine import DEBUG_ALL,DEBUG_LIMITS,EngineModule,WASM_PATH
from tools.audit_online import load_replay

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/emergency-facing-review'
def edge(x,y,horizontal):return (2*y+(0 if horizontal else 1))*21+x
def run(angled):
    portal=[edge(9,5,False),edge(4,7,True) if angled else edge(4,6,False)]
    raw=('MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT 0\nEDGE_COUNT 2\n'+
         ''.join(f'EDGE {i} 2 7\n' for i in portal)+
         'DRAGON_COUNT 3\nDRAGON 0 2 1 1 0 1\nDRAGON 1 2 18 18 19 18\n'+
         'DRAGON 0 4 5 5 4 5 4 6 8 5\n').encode()
    captured=[]
    def reply(identity,block):
        r=int(re.search(rb'^ROUND (\d+)',block,re.M)[1]);captured.append((r,identity,block.decode()))
        if r>=1:return b'LOG fixed contract stop\nENDTURN\n'
        if identity==2:return b'SPLIT 2\nENDTURN\n'
        return b'MOVE N\nENDTURN\n'
    notices=[];engine=EngineModule()
    result=engine.run(raw,reply,on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100785)
    OUT.mkdir(exist_ok=True)
    path=OUT/'same-orientation.replay';path.write_bytes(engine.replay('fixed-A','fixed-B'))
    return captured,load_replay(path),raw,notices

class EmergencyFacingContractTest(unittest.TestCase):
    def test_rotated_portal_pair_is_not_a_legal_map(self):
        with self.assertRaisesRegex(Exception,'horizontal edge to a vertical'):
            run(True)
    def test_same_orientation_cross_body_split_has_official_inverse_facing(self):
        frames,data,raw,notices=run(False)
        split=next(e for e in data['events'] if e['type']=='dragonSplit')
        self.assertEqual(split['childFacing'],'W')
        parent=next(block for r,i,block in frames if (r,i)==(0,2))
        child=next(block for r,i,block in frames if (r,i)==(0,3))
        self.assertIn('A 2 8 5 E 0',parent);self.assertIn('DIR W\n',child)
        packet='ID 2\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n'+parent
        (OUT/'same-orientation-input.json').write_text(json.dumps({'input':packet,'scope':'Official parent observation; full body supplied separately only in model-contract probe'},indent=2)+'\n',encoding='utf-8')
        report={'matches_run':0,'unit_engine_executions':2,'engine_wasm_sha256':hashlib.sha256(WASM_PATH.read_bytes()).hexdigest(),
                'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'rotated_pair':'official map rejects mixed orientations','valid_child_facing':split['childFacing'],
                'valid_old_tail_body_direction':'E','map_sha256':hashlib.sha256(raw).hexdigest(),
                'replay_sha256':hashlib.sha256((OUT/'same-orientation.replay').read_bytes()).hexdigest(),
                'source_unchanged':True,'passed':True}
        (OUT/'official-contract.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':unittest.main()
