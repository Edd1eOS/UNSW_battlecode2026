"""Test simple packed-field hypotheses against public replay sonar values."""
import argparse,json
from pathlib import Path
from audit_online import load_replay
def analyse(path,team):
    d=load_replay(path,node_path='D:/node/node.exe')
    teams={x['id']:x['team'] for x in d['initial_dragons']}
    bodies={x['id']:[(p['x'],p['y']) for p in x['body']] for x in d['initial_dragons']}
    rows=[];seen=set();rnd=0
    for e in d['events']:
        k=e['type']
        if k=='roundStart':rnd=e['round']
        elif k=='dragonSplit':
            for i,key in [(e['parentId'],'parentBody'),(e['childId'],'childBody')]:
                teams[i]=e['team'];bodies[i]=[(p['x'],p['y']) for p in e[key]]
        elif k=='dragonUpdate':
            i=e['id'];tail=(e['tail']['x'],e['tail']['y']);b=[(e['head']['x'],e['head']['y']),*bodies[i]]
            while len(b)>1 and b[-1]!=tail:b.pop()
            bodies[i]=b
        elif k=='dragonDeath':bodies.pop(e['id'],None)
        elif k=='sonarPing' and teams.get(e['senderId'])==team:
            key=(rnd,e['senderId'],e['value'])
            if key in seen:continue
            seen.add(key);i=e['senderId'];body=bodies.get(i,[])
            rows.append({'word':int(e['value']),'round':rnd,'id':i,'x':e['origin']['x'],'y':e['origin']['y'],
                         'length':len(body),'head_x':body[0][0] if body else -1,'head_y':body[0][1] if body else -1})
    result=[]
    for field,width in [('round',9),('id',12),('x',6),('y',6),('head_x',6),('head_y',6),('length',7)]:
        if not rows:continue
        scores=sorted([(sum(((r['word']>>shift)&((1<<width)-1))==r[field] for r in rows)/len(rows),shift) for shift in range(65-width)],reverse=True)
        result.append({'field':field,'width':width,'best_matches':[{'fraction':v,'shift':s} for v,s in scores[:3]]})
    return {'path':str(path),'team':team,'distinct_turn_messages':len(rows),'hypotheses':result,'samples':rows[:8]}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--team',default='B');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=analyse(a.path,a.team);a.out.write_text(json.dumps(r,indent=2));print(json.dumps(r))
