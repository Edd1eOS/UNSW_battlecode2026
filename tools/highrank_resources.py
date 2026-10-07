"""Trace naturally spawned and recycled corpse pearls separately in study data."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip,json
from pathlib import Path
from audit_online import load_replay

ROOT=Path('test-results/oct7-highrank-study')

def analyze(path):
    data=load_replay(path,node_path='D:/node/node.exe')
    bodies={d['id']:[(p['x'],p['y']) for p in d['body']] for d in data['initial_dragons']}
    teams={d['id']:d['team'] for d in data['initial_dragons']}
    pearls={};expected={};counts={t:Counter() for t in 'AB'};drop=Counter();issues=[]
    rnd=actor=None;action=None
    for e in data['events']:
        kind=e['type']
        if kind=='roundStart': rnd=e['round'];actor=None;action=None;expected={}
        elif kind=='turnStart':actor=e['id'];action=None;expected={}
        elif kind=='dragonAction':action=e.get('action')
        elif kind=='tileChange':
            p=(e['tile']['x'],e['tile']['y'])
            if e['hasPearl']:
                origin=expected.pop(p,None)
                pearls[p]=origin
                drop['corpse' if origin else 'natural']+=1
            else:
                if p not in pearls:issues.append('clearance without source')
                origin=pearls.pop(p,None)
                if actor is None:issues.append('clearance outside actor turn');continue
                t=teams[actor];source='natural'
                if origin:
                    source=('own' if origin['team']==t else 'enemy')+('_suicide' if origin['suicide'] else '_other_death')
                counts[t][source]+=1
                if actor<=1:counts[t]['queen_'+source]+=1
        elif rnd is None:continue
        elif kind=='dragonUpdate':
            i=e['id'];head=(e['head']['x'],e['head']['y']);tail=(e['tail']['x'],e['tail']['y']);body=[head,*bodies[i]]
            while len(body)>1 and body[-1]!=tail:body.pop()
            bodies[i]=body
        elif kind=='dragonSplit':
            for i,key in ((e['parentId'],'parentBody'),(e['childId'],'childBody')):
                bodies[i]=[(p['x'],p['y']) for p in e[key]];teams[i]=e['team']
        elif kind=='dragonDeath':
            i=e['id'];tag={'team':teams[i],'suicide':i==actor and bool(action) and action.get('kind')=='suicide'}
            expected={p:tag for p in bodies.pop(i)[::2]}
    cached=json.loads(gzip.decompress((ROOT/'reports'/f'{path.stem}.json.gz').read_bytes()))
    for t in 'AB':
        gross=cached['details']['gross_resources'][t]['food_collected']
        total=sum(n for key,n in counts[t].items() if not key.startswith('queen_'))
        if gross is not None and total!=gross:issues.append('gross mismatch')
    return {'match_id':int(path.stem[1:]),'counts':counts,'spawn_events':drop,'issues':issues,
            'interpretation':'suicide is a recorded action kind, not proof of programmer intent; resources are observed collections, not causal strategy value'}

if __name__=='__main__':
    out=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        fs={pool.submit(analyze,p):p for p in (ROOT/'raw').glob('*.replay')}
        for f in as_completed(fs):out.append(f.result());print('resource',len(out),flush=True)
    (ROOT/'resource-provenance.json').write_text(json.dumps(sorted(out,key=lambda r:r['match_id']),indent=2),encoding='utf8')
