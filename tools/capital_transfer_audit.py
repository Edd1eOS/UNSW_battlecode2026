"""Read actual releases and corpse-pearl receipts, not indicator promises."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from audit_online import load_replay


def trace(data, team):
    bodies={d['id']:[(p['x'],p['y']) for p in d['body']] for d in data['initial_dragons']}
    teams={d['id']:d['team'] for d in data['initial_dragons']}
    offers=[]; releases=[]; receipts=[]; issues=[]
    pearls={}; expected={}; rnd=actor=None; release_request=None
    for e in data['events']:
        kind=e['type']
        if kind=='roundStart':rnd=e['round'];actor=None;expected={};release_request=None
        elif kind=='turnStart':actor=e['id'];expected={};release_request=None
        elif kind=='dragonIndicator' and teams.get(e['id'])==team:
            offer=re.search(r'CAPITAL_OFFER donor=(\d+)',e['text'])
            release=re.search(r'CAPITAL_RELEASE length=(\d+)',e['text'])
            if offer:offers.append({'round':rnd,'queen':e['id'],'donor':int(offer[1])})
            if release:release_request=(e['id'],int(release[1]))
        elif kind=='dragonDeath':
            i=e['id'];body=bodies.pop(i);origin=None
            if release_request and release_request[0]==i:
                if i!=actor or i<=1 or e['reason']!='S' or len(body)!=release_request[1] or not 2<=len(body)<=3:
                    issues.append('release physical mismatch')
                grant=next((o for o in reversed(offers) if o['round']==rnd and o['donor']==i),None)
                if not grant:issues.append('release without matching candidate offer')
                origin=len(releases)
                releases.append({'round':rnd,'donor':i,'length':len(body),'death_reason':e['reason'],
                                 'expected_queen':grant['queen'] if grant else None})
            expected={p:origin for p in body[::2]}
        elif kind=='tileChange':
            p=(e['tile']['x'],e['tile']['y'])
            if e['hasPearl']:pearls[p]=expected.pop(p,None)
            else:
                origin=pearls.pop(p,None)
                if origin is not None:
                    release=releases[origin]
                    receipts.append({'round':rnd,'collector':actor,'team':teams[actor],
                                     'release_index':origin,'position':p,
                                     'intended_queen':actor==release['expected_queen'],
                                     'next_round_queen':actor==release['expected_queen'] and rnd==release['round']+1})
        elif rnd is None:continue
        elif kind=='dragonUpdate':
            i=e['id'];tail=(e['tail']['x'],e['tail']['y']);body=[(e['head']['x'],e['head']['y']),*bodies[i]]
            while len(body)>1 and body[-1]!=tail:body.pop()
            bodies[i]=body
        elif kind=='dragonSplit':
            for i,key in ((e['parentId'],'parentBody'),(e['childId'],'childBody')):
                bodies[i]=[(p['x'],p['y']) for p in e[key]];teams[i]=e['team']
    return {'offers':offers,'releases':releases,'receipts':receipts,'issues':issues,
            'counts':{'offers':len(offers),'releases':len(releases),'released_length':sum(r['length'] for r in releases),
                      'queen_received':sum(r['intended_queen'] for r in receipts),
                      'queen_received_next_round':sum(r['next_round_queen'] for r in receipts),
                      'ally_received':sum(r['team']==team and not r['intended_queen'] for r in receipts),
                      'enemy_received':sum(r['team']!=team for r in receipts)}}


def one(path):
    row=json.loads(path.read_text());raw=path.parent/'raw.replay'
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==row['replay']['sha256']
    result=trace(load_replay(raw,node_path='D:/node/node.exe'),row['candidate_team'])
    return {'id':row['id'],'replay_sha256':row['replay']['sha256'],'source_sha256':row['candidate']['source_bundle_sha256'],
            'eligible':row['eligible_mechanism_result'],**result}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--panel',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();paths=sorted((args.panel/'games').rglob('result.json'))
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,paths))
    all_counts=Counter();eligible_counts=Counter()
    for row in rows:
        all_counts.update(row['counts'])
        if row['eligible']:eligible_counts.update(row['counts'])
    result={'games':len(rows),'all_counts':all_counts,'eligible_counts':eligible_counts,
            'games_with_release':sum(bool(r['releases']) for r in rows),'issues':sum(len(r['issues']) for r in rows),'rows':rows,
            'scope':'Actual own-neck releases and first-generation corpse receipts; not causal utility, does not count later recycling as original delivery.'}
    args.out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    if result['issues']:raise SystemExit(1)


if __name__=='__main__':main()
