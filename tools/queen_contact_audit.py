"""Observed information available before a Queen's fatal head collision."""
import argparse,hashlib,json,re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from audit_online import load_replay

def one(path):
    d=load_replay(path,node_path='D:/node/node.exe');w,h=map(int,re.search(r'^MAP (\d+) (\d+)',d['map']).groups())
    body={x['id']:[(p['x'],p['y']) for p in x['body']] for x in d['initial_dragons']};teams={x['id']:x['team'] for x in d['initial_dragons']}
    previous={};rows=[];rnd=actor=None
    def visible(a,b):
        x,y=abs(a[0]-b[0]),abs(a[1]-b[1]);return min(x,w-x)<=3 and min(y,h-y)<=3
    for e in d['events']:
        kind=e['type']
        if kind=='roundStart':rnd=e['round']
        elif rnd is None:continue
        elif kind=='turnStart':
            actor=e['id']
            if actor<=1:
                head=body[actor][0]
                previous[actor]={'round':rnd,'head':head,'enemies':{i:{'head_visible':visible(head,b[0]),
                    'all_segments_visible':all(visible(head,p) for p in b),'length':len(b),'head':b[0]}
                    for i,b in body.items() if teams[i]!=teams[actor]}}
        elif kind=='dragonUpdate':
            i=e['id'];tail=(e['tail']['x'],e['tail']['y']);b=[(e['head']['x'],e['head']['y']),*body[i]]
            while len(b)>1 and b[-1]!=tail:b.pop()
            body[i]=b
        elif kind=='dragonSplit':
            for i,key in ((e['parentId'],'parentBody'),(e['childId'],'childBody')):
                body[i]=[(p['x'],p['y']) for p in e[key]];teams[i]=e['team']
        elif kind=='dragonDeath':
            i=e['id']
            if i<=1 and e['reason']=='H':
                prior=previous.get(i);enemy=prior['enemies'].get(actor) if prior else None
                category=('queen_initiated' if actor==i else 'friendly_head_contact' if teams.get(actor)==teams[i] else
                          'no_prior_turn' if not prior else 'new_since_queen_turn' if not enemy else
                          'attacker_head_outside_vision' if not enemy['head_visible'] else
                          'attacker_body_partial' if not enemy['all_segments_visible'] else 'attacker_fully_visible')
                rows.append({'queen':i,'team':teams[i],'death_round':rnd,'actor':actor,'actor_team':teams.get(actor),'category':category,
                             'prior_turn':prior['round'] if prior else None,'attacker_at_prior_turn':enemy})
            body.pop(i)
    return {'match_id':int(path.stem[1:]),'replay_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'collisions':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--team',choices=['A','B']);args=ap.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,sorted((args.root/'raw').glob('*.replay'))))
    counts=Counter(r['category'] for game in rows for r in game['collisions'] if args.team is None or r['team']==args.team)
    out={'games':len(rows),'team':args.team,'counts':counts,'rows':rows,
         'scope':'Actual fatal-action actor relative to the Queen previous turn geometric 7x7 window; full segment visibility is only an upper bound on reply-search eligibility, not proof the new search detects or prevents it.'}
    args.out.write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='rows'}))

if __name__=='__main__':main()
