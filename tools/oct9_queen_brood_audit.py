"""Quantify Queen growth versus brood investment in existing replays only."""
from pathlib import Path
from collections import Counter
import json,statistics
from tools.audit_online import load_replay
OUT=Path('test-results/oct9-final-sprint');OUT.mkdir(parents=True,exist_ok=True)
def one(path,version,candidate_team=None):
 r=load_replay(path,node_path='D:/node/node.exe')
 if candidate_team is None:candidate_team=next(t for t in 'AB' if (r['teams'].get(t) or {}).get('botId')=='21052')
 live={d['id']:{'team':d['team'],'body':[(p['x'],p['y']) for p in d['body']]} for d in r['initial_dragons']}
 q=next(i for i,v in live.items() if i<=1 and v['team']==candidate_team)
 initial=len(live[q]['body']);rnd=-1;actor=None;startlen=0;step=0;notes={};turns=[];splits=[];food80=paid80=0;food=paid=0;death=None
 first5=-1 if initial>=5 else None
 for e in r['events']:
  k=e['type']
  if k=='roundStart':rnd=e['round']
  elif k=='turnStart':
   actor=e['id'];startlen=len(live[actor]['body']);step=0
   if actor==q:turns.append(dict(round=rnd,length=startlen,units=sum(v['team']==candidate_team for v in live.values())))
  elif k=='dragonIndicator':notes[e['id']]=e['text']
  elif k=='dragonAction' and e['id']==q:turns[-1]['action']=e['action'];turns[-1]['note']=notes.get(q)
  elif k=='dragonUpdate' and rnd>=0:
   i=e['id'];v=live[i];old=len(v['body']);body=[(e['head']['x'],e['head']['y'])]+v['body'];tail=(e['tail']['x'],e['tail']['y'])
   while len(body)>1 and body[-1]!=tail:body.pop()
   assert body[-1]==tail
   step+=1;spent=int(step>(startlen+3)//4);ate=len(body)-old+spent;assert ate in (0,1)
   v['body']=body
   if i==q:
    food+=ate;paid+=spent
    if rnd<80:food80+=ate;paid80+=spent
    if first5 is None and len(body)>=5:first5=rnd
  elif k=='dragonSplit':
   i=e['parentId'];child=e['childId']
   if i==q:splits.append(dict(round=rnd,before=len(live[i]['body']),after=len(e['parentBody']),child=len(e['childBody']),units_before=sum(v['team']==candidate_team for v in live.values()),note=notes.get(q)))
   for j,key in ((i,'parentBody'),(child,'childBody')):live[j]={'team':e['team'],'body':[(p['x'],p['y']) for p in e[key]]}
  elif k=='dragonDeath':
   if e['id']==q:death=dict(round=rnd,reason=e['reason'],length=len(live[q]['body']),last_note=notes.get(q))
   live.pop(e['id'])
 before=[x for x in turns if x['round']<80]
 fin=r['result'];own=fin['team'+candidate_team];other=fin['team'+('B' if candidate_team=='A' else 'A')]
 return dict(path=str(path),version=version,source_sha256=r['input_sha256'],candidate_team=candidate_team,queen_id=q,initial_queen_length=initial,queen_first_length5=first5,queen_food_first80=food80,queen_paid_first80=paid80,queen_split_segments_first80=sum(x['child'] for x in splits if x['round']<80),queen_turns_first80=len(before),queen_length2_turns_first80=sum(x['length']==2 for x in before),queen_length_atleast5_turns_first80=sum(x['length']>=5 for x in before),mean_queen_length_first80=statistics.mean(x['length'] for x in before) if before else None,queen_food_total=food,queen_paid_total=paid,queen_splits=splits,queen_death=death,own_final=own,enemy_final=other,result='win' if fin['winner']==candidate_team else 'loss' if fin['winner'] else 'draw',queen_turns=turns)
if __name__=='__main__':
 rows=[]
 for p in sorted(Path('test-results/oct9-aggressive/online-v33-gitgud').glob('*.replay')):rows.append(one(p,'v258_online'))
 for ver in (258,259):
  for p in sorted(Path(f'test-results/oct9-aggressive/v{ver}-runtime-smoke/games').glob('*/result.json')):
   meta=json.loads(p.read_text());rows.append(one(p.parent/'raw.replay',f'v{ver}_local',meta['candidate_team']))
 (OUT/'queen-brood-audit.json').write_text(json.dumps(dict(scope='Observed existing replays; v258/v259 share v260 brood condition. No claim these are new v260 online observations, no counterfactual growth prediction.',games=rows),indent=2),encoding='utf-8')
 brief=[{k:v for k,v in x.items() if k not in ('queen_turns','source_sha256','queen_splits','queen_death')}|{'qsplit_first80':[(z['round'],z['before'],z['after'],z['units_before']) for z in x['queen_splits'] if z['round']<80]} for x in rows]
 print(json.dumps(brief,indent=2))
