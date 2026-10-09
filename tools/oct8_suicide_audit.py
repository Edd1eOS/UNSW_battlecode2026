"""Classify public replay suicides from physical pre-action state, not policy intent."""
import argparse,json
from collections import Counter
from pathlib import Path
from audit_online import load_replay
from oct7_exploration_death_audit import Board,point

def audit(path):
 r=load_replay(path,node_path='D:/node/node.exe');board=Board(r['map'])
 live={v['id']:{'team':v['team'],'body':list(map(point,v['body']))} for v in r['initial_dragons']}
 rows=[];rnd=0
 for e in r['events']:
  k=e['type']
  if k=='roundStart':rnd=e['round']
  elif k=='dragonAction' and e['action']['kind']=='suicide':
   i=e['id'];v=live[i];head=v['body'][0];occupied={p for x in live.values() for p in x['body']}
   safe=[d for d in 'NESW' if (p:=board.step(head,d)) is not None and p not in occupied]
   queen=next((x for q,x in live.items() if q<2 and x['team']==v['team']),None)
   qhead=queen['body'][0] if queen else None
   adjacent=qhead is not None and any(board.step(qhead,d) in v['body'] for d in 'NESW')
   rows.append({'id':i,'team':v['team'],'round':rnd,'length':len(v['body']),'free_directions':safe,
                'queen_adjacent_to_body':adjacent,'queen_visible':qhead is not None and board.visible(head,qhead),
                'body':v['body'][:],'queen_head':qhead})
  elif k=='dragonUpdate':
   v=live[e['id']];v['body'].insert(0,point(e['head']));tail=point(e['tail'])
   while len(v['body'])>1 and v['body'][-1]!=tail:v['body'].pop()
  elif k=='dragonSplit':
   live[e['parentId']]['body']=list(map(point,e['parentBody']))
   live[e['childId']]={'team':e['team'],'body':list(map(point,e['childBody']))}
  elif k=='dragonDeath':live.pop(e['id'],None)
 summaries={}
 for team in 'AB':
  rr=[x for x in rows if x['team']==team]
  summaries[team]={'suicides':len(rr),'with_free_move':sum(bool(x['free_directions']) for x in rr),
   'queen_adjacent':sum(x['queen_adjacent_to_body'] for x in rr),
   'free_and_queen_adjacent':sum(bool(x['free_directions']) and x['queen_adjacent_to_body'] for x in rr),
   'lengths':dict(Counter(x['length'] for x in rr))}
 return {'path':str(path),'teams':r['teams'],'summary':summaries,'rows':rows}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('files',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 results=[audit(f) for f in a.files];a.out.write_text(json.dumps(results,indent=2),encoding='utf8')
 print(json.dumps([{k:v for k,v in x.items() if k!='rows'} for x in results]))
