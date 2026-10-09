"""Official-engine counterexample for counting empty cells behind chamber walls."""
from pathlib import Path
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS
from tools.audit_online import load_replay
import re,json
OUT=Path('test-results/oct9-aggressive/split-room-contract');OUT.mkdir(parents=True,exist_ok=True)
ring=[(5,5),(4,5),(4,6),(5,6),(6,6),(6,5)]
allowed={frozenset((a,b)) for a,b in zip(ring,ring[1:]+ring[:1])}
walls=set()
for x,y in ring:
 for dx,dy in ((0,-1),(1,0),(0,1),(-1,0)):
  if frozenset(((x,y),(x+dx,y+dy))) in allowed:continue
  if dx:walls.add((2*y+1)*21+x+(dx==1))
  else:walls.add(2*(y+(dy==1))*21+x)
raw=('MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT 0\nEDGE_COUNT '+str(len(walls))+'\n'+''.join('EDGE '+str(e)+' 1 -1\n' for e in sorted(walls))+'DRAGON_COUNT 3\nDRAGON 0 2 1 1 0 1\nDRAGON 1 2 18 18 19 18\nDRAGON 0 4 5 5 4 5 4 6 5 6\n').encode()
(OUT/'six-cell-ring.map').write_bytes(raw)
rows=[]
for split in (False,True):
 seen=[]
 def reply(i,block):
  r=int(re.search(rb'^ROUND (\d+)',block,re.M)[1]);seen.append((r,i))
  if r>=2:return b'LOG intentional fixture stop after two rounds\nENDTURN\n'
  if i<2:return b'MOVE N\nENDTURN\n'
  action=('SPLIT 2' if r==0 else 'MOVE E') if i==2 and split else ('MOVE E' if r==0 else 'MOVE N') if i==3 else ('MOVE E' if r==0 else 'MOVE S')
  return (action+'\nENDTURN\n').encode()
 e=EngineModule();e.run(raw,reply,on_notice=lambda _:None,debug=DEBUG_ALL|DEBUG_LIMITS,seed=202610090901)
 path=OUT/('split.replay' if split else 'move.replay');path.write_bytes(e.replay('fixed-A','fixed-B'));d=load_replay(path,node_path='D:/node/node.exe')
 r=-1;deaths=[]
 for x in d['events']:
  if x['type']=='roundStart':r=x['round']
  elif x['type']=='dragonDeath' and r<2 and x['id']>=2:deaths.append(dict(round_index=r,id=x['id'],reason=x['reason']))
 rows.append(dict(split=split,events_before_intentional_stop=deaths,alive_at_round2=[i for r,i in seen if r==2 and i>=2],replay=str(path)))
assert not rows[0]['events_before_intentional_stop'] and rows[0]['alive_at_round2']==[2],rows
assert len(rows[1]['events_before_intentional_stop'])==2 and not rows[1]['alive_at_round2'],rows
(OUT/'result.json').write_text(json.dumps(dict(scope='Two-round official-physics fixture, followed by intentional stops. No match-strength claim.',rows=rows),indent=2),encoding='utf-8')
print(json.dumps(rows))
