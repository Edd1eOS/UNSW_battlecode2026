"""Physical Queen death context, including actual triggering actor and prior observation."""
import argparse,json,re
from pathlib import Path
from audit_online import load_replay

def one(path):
    d=load_replay(path,node_path='D:/node/node.exe')
    w,h=map(int,re.search(r'^MAP (\d+) (\d+)',d['map']).groups())
    body={x['id']:[(p['x'],p['y']) for p in x['body']] for x in d['initial_dragons']}
    team={x['id']:x['team'] for x in d['initial_dragons']};prior={};turns={};rnd=actor=None;rows=[]
    def visible(a,b):
        x,y=abs(a[0]-b[0]),abs(a[1]-b[1]);return min(x,w-x)<=3 and min(y,h-y)<=3
    for e in d['events']:
        k=e['type']
        if k=='roundStart':rnd=e['round']
        elif k=='turnStart':
            actor=e['id'];turns[actor]=[]
            if actor<2:
                head=body[actor][0];prior[actor]={'round':rnd,'body':body[actor][:],
                    'nearby':{i:{'team':team[i],'body':b[:]} for i,b in body.items() if i!=actor and any(visible(head,p) for p in b)}}
        elif k=='dragonUpdate':
            i=e['id'];tail=(e['tail']['x'],e['tail']['y']);b=[(e['head']['x'],e['head']['y']),*body[i]]
            while len(b)>1 and b[-1]!=tail:b.pop()
            body[i]=b
        elif k=='dragonSplit':
            for i,key in [(e['parentId'],'parentBody'),(e['childId'],'childBody')]:
                body[i]=[(p['x'],p['y']) for p in e[key]];team[i]=e['team']
        elif k=='dragonDeath':
            i=e['id']
            if i<2:rows.append({'queen':i,'team':team[i],'round':rnd,'reason':e['reason'],'actor':actor,
                'actor_team':team.get(actor),'body':body[i][:],'actor_body':body.get(actor),'prior':prior.get(i),
                'queen_turn':turns.get(i),'actor_turn':turns.get(actor)})
            body.pop(i)
        if actor is not None and k not in ['pearlCountdown','pearlSpawn']:
            turns[actor].append(e)
    return {'path':str(path),'deaths':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[one(x) for x in sorted(a.root.rglob('*.replay'))]
    a.out.write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(json.dumps([{'path':r['path'],'deaths':[{k:d[k] for k in ['queen','round','reason','actor','actor_team']} for d in r['deaths']]} for r in rows]))
