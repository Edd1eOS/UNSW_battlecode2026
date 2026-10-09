"""Opening resource audit from completed official-engine replays."""
from pathlib import Path
from collections import Counter
import json
from tools.audit_online import load_replay
BASE=Path('test-results/oct9-aggressive/v258-runtime-smoke')
def one(directory):
    meta=json.loads((directory/'result.json').read_text(encoding='utf-8'))
    d=load_replay(directory/'raw.replay',node_path='D:/node/node.exe')
    bodies={e['id']:[(p['x'],p['y']) for p in e['body']] for e in d['initial_dragons']}
    teams={e['id']:e['team'] for e in d['initial_dragons']}
    first4={str(i):(-1 if len(bodies[i])>=4 else None) for i in bodies};firstsplit={str(i):None for i in bodies}
    totals={t:Counter() for t in 'AB'};r=-1;active=None;step=0;startlen=0;snaps={};notes={};deaths=[]
    def snapshot():
      return {t:dict(units=sum(teams[i]==t for i in bodies),length=sum(len(b) for i,b in bodies.items() if teams[i]==t),queen=len(bodies.get(0 if t=='A' else 1,[])),**dict(totals[t])) for t in 'AB'}
    for e in d['events']:
      k=e['type']
      if k=='roundStart':
        if r in (9,24,49,99):snaps[str(r)]=snapshot()
        r=e['round']
      elif k=='turnStart':active=e['id'];step=0;startlen=len(bodies[active])
      elif k=='dragonIndicator':notes[e['id']]=e['text']
      elif k=='dragonUpdate' and r>=0:
        i=e['id'];old=len(bodies[i]);b=[(e['head']['x'],e['head']['y'])]+bodies[i];tail=(e['tail']['x'],e['tail']['y'])
        while len(b)>1 and b[-1]!=tail:b.pop()
        assert b[-1]==tail
        step+=1;paid=int(step>(startlen+3)//4);food=len(b)-old+paid
        assert food in (0,1),(directory,i,r,food)
        totals[teams[i]]['food']+=food;totals[teams[i]]['paid']+=paid;totals[teams[i]]['net_growth']+=food-paid
        bodies[i]=b
        if str(i) in first4 and first4[str(i)] is None and len(b)>=4:first4[str(i)]=r
      elif k=='dragonSplit':
        i=e['parentId'];child=e['childId'];totals[teams[i]]['splits']+=1
        if str(i) in firstsplit and firstsplit[str(i)] is None:firstsplit[str(i)]=r
        for who,key in ((i,'parentBody'),(child,'childBody')):bodies[who]=[(p['x'],p['y']) for p in e[key]];teams[who]=e['team']
      elif k=='dragonDeath':
        i=e['id'];totals[teams[i]]['deaths']+=1;totals[teams[i]]['death_'+e['reason']]+=1
        deaths.append(dict(id=i,team=teams[i],round_index=r,reason=e['reason'],last_note=notes.get(i),body=bodies[i]));bodies.pop(i)
    return dict(game=directory.name,candidate_team=meta['candidate_team'],first_length4_round_index=first4,first_split_round_index=firstsplit,snapshots_at_end_round_index=snaps,final=snapshot(),deaths=deaths,invalid_runtime_events=meta['invalid_runtime_events'],peak=meta['peak'][meta['candidate_team']],official_outcome=meta['official_outcome'])
if __name__=='__main__':
    rows=[one(p.parent) for p in sorted((BASE/'games').glob('*/result.json'))]
    out=BASE.parent/'opening-runtime-audit.json';out.write_text(json.dumps(dict(scope='Local runtime smoke vs previous own v257. Zero-based round indices. Food and paid calculated per completed movement update. Not online evidence or rating prediction.',games=rows),indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k in ('game','candidate_team','first_length4_round_index','first_split_round_index','snapshots_at_end_round_index','peak','invalid_runtime_events')} for r in rows],indent=2))
