"""Read-only strategy inference from the frozen high-rank replay cohort."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip, json, re, statistics
from audit_online import load_replay

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'test-results/oct7-highrank-study'
OUT=ROOT/'test-results/oct8-strategy-study'
OUT.mkdir(exist_ok=True)

def read(path): return json.loads(path.read_text(encoding='utf8'))
def phase(r): return str(min(4,r//100)*100)
def one(path):
    report=json.loads(gzip.decompress((STUDY/'reports'/f'{path.stem}.json.gz').read_bytes()))
    data=load_replay(path,node_path='D:/node/node.exe')
    width,height=map(int,re.search(r'^MAP (\d+) (\d+)',data['map']).groups())
    def distance(a,b):
        dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
        return min(dx,width-dx)+min(dy,height-dy)
    bodies={d['id']:[(p['x'],p['y']) for p in d['body']] for d in data['initial_dragons']}
    teams={d['id']:d['team'] for d in data['initial_dragons']}
    queens={d['team']:d['id'] for d in data['initial_dragons'] if d['id']<=1}
    history=defaultdict(list);birth={i:0 for i in bodies};pearls={};expected={};associations={t:Counter() for t in 'AB'}
    phases={t:{str(r):Counter() for r in range(0,500,100)} for t in 'AB'}
    receipts=[];scoring_receipts=[];deaths=[];round_no=None;actor=None;action=None;source_counts={t:Counter() for t in 'AB'}
    for e in data['events']:
        k=e['type']
        if k=='roundStart':round_no=e['round'];actor=None;action=None;expected={}
        elif k=='turnStart':actor=e['id'];action=None;expected={}
        elif k=='dragonAction':
            action=e.get('action'); i=e['id']
            if i>1 and len(bodies[i])<=3 and action:
                head=bodies[i][0];t=teams[i]
                def visible(p):
                    dx,dy=abs(p[0]-head[0]),abs(p[1]-head[1])
                    return min(dx,width-dx)<=3 and min(dy,height-dy)<=3
                marker=action['kind']=='suicide' or (action['kind']=='split' and action['childSegmentCount']==1)
                local_queen=any(j<=1 and teams[j]==t and visible(b[0]) for j,b in bodies.items())
                larger=any(j!=i and teams[j]==t and visible(b[0]) and sum(visible(p) for p in b)>len(bodies[i]) for j,b in bodies.items())
                enemy=any(teams[j]!=t and visible(b[0]) for j,b in bodies.items())
                group=('late' if round_no>=250 else 'early')+(':marker' if marker else ':other')
                associations[t][group+':all']+=1
                associations[t][group+':queen_visible']+=local_queen
                associations[t][group+':larger_head_visible']+=larger
                associations[t][group+':queen_or_larger']+=local_queen or larger
                associations[t][group+':enemy_head_visible']+=enemy
            history[i].append({'round':round_no,'head':bodies[i][0],'length':len(bodies[i]),'action':action})
            history[i]=history[i][-8:]
            phases[teams[i]][phase(round_no)]['actions']+=1
            if action and action['kind']=='suicide':phases[teams[i]][phase(round_no)]['recorded_suicide_actions']+=1
        elif k=='tileChange':
            p=(e['tile']['x'],e['tile']['y'])
            if e['hasPearl']:pearls[p]=expected.pop(p,None)
            else:
                assert p in pearls,(path,round_no,p)
                origin=pearls.pop(p);t=teams[actor];bucket=phases[t][phase(round_no)]
                source='natural' if origin is None else ('own' if origin['team']==t else 'enemy')
                source_counts[t][source]+=1;bucket['food_'+source]+=1
                if actor<=1:bucket['queen_food_'+source]+=1
                if origin and origin['team']==t:
                    bucket['own_food_from_'+origin['action_kind']]+=1
                    if actor>1 and len(bodies[actor])>=8:
                        scoring_receipts.append({'round':round_no,'recipient':actor,'recipient_length':len(bodies[actor]),
                                                 'cell':p,'lag':round_no-origin['round'],'donor':origin})
                    if actor<=1:
                        lag=round_no-origin['round'];bucket['queen_own_food_lag_sum']+=lag
                        bucket['queen_own_food_lag_le1']+=lag<=1
                        bucket['queen_own_food_lag_le3']+=lag<=3
                        receipts.append({'round':round_no,'recipient':actor,'cell':p,'lag':lag,'donor':origin})
        elif round_no is None:continue
        elif k=='dragonUpdate':
            i=e['id'];body=[(e['head']['x'],e['head']['y']),*bodies[i]];tail=(e['tail']['x'],e['tail']['y'])
            while len(body)>1 and body[-1]!=tail:body.pop()
            bodies[i]=body
        elif k=='dragonSplit':
            i=e['parentId'];before=len(bodies[i]);child=len(e['childBody']);bucket=phases[teams[i]][phase(round_no)]
            bucket['splits']+=1;bucket['split_at4']+=before==4;bucket['child2']+=child==2
            bucket['tail_handoff']+=before>=8 and child>=before-2
            bucket['tail_handoff_capital']+=child if before>=8 and child>=before-2 else 0
            for who,key in ((i,'parentBody'),(e['childId'],'childBody')):
                bodies[who]=[(p['x'],p['y']) for p in e[key]];teams[who]=e['team']
            birth[e['childId']]=round_no
        elif k=='dragonDeath':
            i=e['id'];t=teams[i];body=bodies.pop(i);q=queens[t];qb=bodies.get(q)
            kind=action.get('kind','unknown') if i==actor and action else 'other_actor'
            tag={'id':i,'team':t,'round':round_no,'length':len(body),'reason':e['reason'],'action_kind':kind,
                 'queen_distance':distance(body[0],qb[0]) if qb else None,'queen_head':qb[0] if qb else None,
                 'age':round_no-birth[i],'history':history[i][-5:],
                 'strong_heads':{j:b[0] for j,b in bodies.items() if teams[j]==t and len(b)>=8}}
            if qb:tag['distance_history_to_queen_at_death']=[distance(h['head'],qb[0]) for h in history[i][-5:]]
            deaths.append({k:v for k,v in tag.items() if k not in ('history','distance_history_to_queen_at_death','strong_heads')})
            expected={p:tag for p in body[::2]}
    issues=[]
    for t in 'AB':
        gross=report['details']['gross_resources'][t]['food_collected']
        if gross is not None and sum(source_counts[t].values())!=gross:issues.append('food count mismatch '+t)
    assert not issues,(path,issues)
    sides={}
    dragons={d['id']:d for d in report['details']['dragons']}
    for t in 'AB':
        live=[d for d in dragons.values() if d['team']==t and d['final_length']>0]
        champion=max(live,key=lambda d:d['final_length']) if live else None
        lineage=[];cur=champion
        while cur:
            lineage.append({k:cur[k] for k in ['id','is_queen','birth_round','birth_parent','birth_capital','food','paid','peak_length','final_length']})
            cur=dragons.get(cur['birth_parent'])
        sides[t]={'name':report['metadata']['teams']['AB'.index(t)]['name'],'phases':phases[t],'local_action_associations':associations[t],
                  'final_champion_lineage':lineage,'queen_actions':report['behavior']['queen_actions'][t],
                  'final':report['core']['final']['scores'][t]}
    return {'match_id':report['match_id'],'metadata':report['metadata'],'source_sha256':data['input_sha256'],
            'winner':report['core']['final']['leader'],'sides':sides,'queen_own_corpse_receipts':receipts,
            'worker_scoring_corpse_receipts':scoring_receipts,
            'deaths':deaths,'food_events_reconcile':not issues}

if __name__=='__main__':
    paths=sorted((STUDY/'raw').glob('*.replay'));rows=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(one,paths):
            (OUT/f"M{row['match_id']}.json.gz").write_bytes(gzip.compress(json.dumps(row).encode()))
            rows.append({k:row[k] for k in ['match_id','metadata','source_sha256','winner','sides','food_events_reconcile']})
            print('analyzed',row['match_id'],flush=True)
    (OUT/'summary.json').write_text(json.dumps({'scope':'Observed replay strategy traces, no bots run, no interventions, no causal wins. Recorded suicide does not prove intent.','matches':rows},ensure_ascii=False,indent=2),encoding='utf8')
    print('complete',len(rows),flush=True)
