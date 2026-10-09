"""Check ordinary Queen brood cap across real persistent official-engine turns."""
from pathlib import Path
import argparse,json,re,hashlib
from tools.verify_candidate import build
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS
from unswbc.sandbox import SandboxBot,WasmPool
OUT=Path('test-results/oct9-final-sprint');OUT.mkdir(parents=True,exist_ok=True)
raw=('MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT 5\n'+''.join(f'TILE {x} 5 1 1\n' for x in range(6,11))+'EDGE_COUNT 0\nDRAGON_COUNT 3\nDRAGON 0 4 5 5 4 5 3 5 2 5\nDRAGON 1 2 18 18 19 18\nDRAGON 0 2 1 15 0 15\n').encode()
def run(candidate):
 wasm,digest=build(candidate);pool=WasmPool([str(wasm)],key='queen-once-'+digest[:20]);live={};rows=[];deaths=[]
 def spawn(i,init):
  if i==0:live[i]=SandboxBot(pool,init=init,name=str(i))
 def reply(i,block):
  rnd=int(re.search(rb'^ROUND (\d+)',block,re.M)[1])
  if rnd>=6:return b'LOG intentional fixture stop after six rounds\nENDTURN\n'
  if i!=0:return b'MOVE W\nENDTURN\n' if i>=3 else b'MOVE N\nENDTURN\n'
  output=live[i].ask(block).decode();rows.append(dict(round=rnd,length=int(re.search(rb'^LENGTH (\d+)',block,re.M)[1]),output=output,error=live[i].error,points=live[i].live[0]));return output.encode()
 def death(i,r,reason):
  if r<6:deaths.append(dict(id=i,round=r,reason=reason))
  if i in live:live.pop(i).stop()
 try:
  engine=EngineModule();engine.run(raw,reply,death,spawn,lambda _:None,DEBUG_ALL|DEBUG_LIMITS,202610090411)
  (OUT/(candidate.name+'-queen-once.replay')).write_bytes(engine.replay(candidate.name,'fixed-B'))
 finally:
  for bot in live.values():bot.stop()
  pool.close()
 report=dict(candidate=str(candidate),source_hash=digest,scope='Six official-engine turns. Only Queen runs candidate; other units fixed clear routes. Same Queen process persists; deliberate stops from round6 excluded. Not strength test.',rows=rows,deaths_before_stop=deaths,ordinary_split_rounds=[r['round'] for r in rows if ' FLOOD ' in r['output'] and 'SPLIT ' in r['output']])
 (OUT/(candidate.name+'-queen-once.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);a=p.parse_args();run(a.candidate)
