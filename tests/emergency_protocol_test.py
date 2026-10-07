"""Official metered emergency protocol fixtures; no strength matches."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import verify_candidate as verifier
from external_panel import source_bundle

def added():
 spec=importlib.util.spec_from_file_location('emergency_frames',ROOT/'external-benchmarks/smoke_external.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 cases=[]
 for identity in (0,2):
  for body,edges,label in [([(5,5),(4,5),(3,5),(2,5)],[],'two-L2-closed'),
       ([(5,5),(4,5),(3,5),(3,6),(4,6),(5,6)],[((5,5),(5,6)),((5,6),(6,6)),((6,6),(7,6))],'waiting-hook')]:
   packet=module.frame(identity,body,round_num=100,units=3,edges=edges)
   cases.append({'name':f'emergency-{label}-id{identity}','init':f'ID {identity}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n','turns':[packet],'constructed':True})
 return cases
if __name__=='__main__':
 original=verifier.fixtures;verifier.fixtures=lambda:original()+added()
 candidate=ROOT/'opponents/generalist-emergency-v1';out=ROOT/'test-results/emergency-v1-final-protocol.json'
 verifier.run(candidate,out)
 report=json.loads(out.read_text(encoding='utf-8'));report['protocol_source_content_sha256']=report['source_bundle_sha256']
 report['source_bundle_sha256']=source_bundle(candidate)[0]
 report['additional_fixture_driver_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 report['additional_fixture_scope']='Complete physical current-body closure and waiting rescue; 49 visible cells; no match'
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
