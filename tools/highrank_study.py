"""Frozen public high-rank replay study; no matches or opponent code executed."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import json
from pathlib import Path
from audit_online import load_replay
from trajectory_metrics import analyze_replay
from panel_trajectory import executed_details, phase_metrics
from import_online_replays import scan_downloads, import_candidates


def verified_suicide_ledger(data, core):
    """Old ledger predates recorded suicide. Omit only proven effect-free actions.

    A recorded suicide must be followed by that actor's A death in the same
    turn, with no successful body/split/food mutation in between. Death remains
    in the ledger; this does not turn deaths into income or hide runtime errors.
    """
    removed = set()
    for i, event in enumerate(data['events']):
        if event['type'] != 'dragonAction' or (event.get('action') or {}).get('kind') != 'suicide':
            continue
        for follow in data['events'][i+1:]:
            if follow['type'] == 'dragonDeath':
                if follow['id'] != event['id'] or follow['reason'] != 'A':
                    raise ValueError('Suicide did not immediately kill its actor')
                removed.add(i)
                break
            if follow['type'] in ('turnStart','roundStart','dragonUpdate','dragonSplit','tileChange','dragonAction'):
                raise ValueError('Suicide had unexpected state effects')
        else:
            raise ValueError('Unresolved suicide action')
    result = executed_details({**data, 'events': [e for i,e in enumerate(data['events']) if i not in removed]}, core)
    result['verified_recorded_suicide_actions'] = len(removed)
    return result


def behavior(data, core, detail):
    teams = {int(d['id']):d['team'] for d in detail['dragons']}
    lengths = {int(d['id']):len(d['body']) for d in data['initial_dragons']}
    bodies = {int(d['id']):[(p['x'],p['y']) for p in d['body']] for d in data['initial_dragons']}
    counts = {t:Counter() for t in 'AB'}
    phases = {t:{p:Counter() for p in ('early','middle','late')} for t in 'AB'}
    queens = {t:[] for t in 'AB'}
    suicides = []
    turn, rnd = None, None
    for e in data['events']:
        kind=e['type']
        if kind == 'roundStart': rnd=e['round']
        elif rnd is None: continue
        elif kind == 'turnStart': turn=e['id']
        elif kind == 'dragonAction':
            identity=e['id']; t=teams[identity]; a=e['action'] or {'kind':'invalid_action'}; c=counts[t]
            phase=phases[t]['early' if rnd<100 else 'middle' if rnd<300 else 'late']
            role='queen' if identity<=1 else 'worker'
            keys=['actions',a['kind'],role+'_'+a['kind']]
            if a['kind']=='move':
                n=len(a['steps']); keys += ['steps_requested_'+str(n)]
                if n>1: keys += ['multi_step_actions',role+'_multi_step_actions']
                if n>(lengths[identity]+3)//4: keys += ['paid_intent_actions']
            for key in keys: c[key]+=1;phase[key]+=1
            if a['kind']=='suicide':
                suicides.append({'round':rnd,'id':identity,'team':t,'length':lengths[identity]})
            if identity<=1:
                queens[t].append({'round':rnd,'length':lengths[identity],'action':a,'head':bodies[identity][0]})
        elif kind=='dragonUpdate':
            identity=e['id']; head=(e['head']['x'],e['head']['y']);tail=(e['tail']['x'],e['tail']['y'])
            body=[head,*bodies[identity]]
            while len(body)>1 and body[-1]!=tail: body.pop()
            bodies[identity]=body;lengths[identity]=len(body)
        elif kind=='dragonSplit':
            for identity, key in ((e['parentId'],'parentBody'),(e['childId'],'childBody')):
                bodies[identity]=[(p['x'],p['y']) for p in e[key]];lengths[identity]=len(bodies[identity])
        elif kind=='dragonDeath':
            bodies.pop(e['id']); lengths.pop(e['id'])
    return {'counts':counts,'phases':phases,'queen_actions':queens,'suicides':suicides}


def one(root, row):
    identity=row['match_id']; path=root/'raw'/f'M{identity}.replay'
    raw=path.read_bytes(); data=load_replay(path,node_path='D:/node/node.exe')
    core=analyze_replay(data); detail=verified_suicide_ledger(data,core)
    actions=behavior(data,core,detail)
    winner=data['result']['winner']
    expected_name=row['teams']['AB'.index(winner)]['name'] if winner else None
    ui_consistent=expected_name in row['text'] if expected_name else 'Draw' in row['text']
    if row.get('our_team_id'):
        own=next('AB'[i] for i,t in enumerate(row['teams']) if t['url']==f"/teams/{row['our_team_id']}")
        tags=[line.strip() for line in row['text'].split('\n') if line.strip() in ('W','L','D')]
        tag=tags[0] if len(tags)==1 else ''
        ui_consistent=(tag=='W' and winner==own) or (tag=='L' and winner not in (own,None)) or (tag=='D' and winner is None)
    report={'match_id':identity,'metadata':row,'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'decoder_sha256':data.get('decoder_bundle_sha256'),'public_header_teams':data.get('teams'),
            'ui_winner_consistent':ui_consistent,'core':core,'details':detail,'behavior':actions,
            'phase_metrics':{t:phase_metrics(core,detail,t) for t in 'AB'}}
    (root/'reports'/f'M{identity}.json.gz').write_bytes(gzip.compress(json.dumps(report,separators=(',',':')).encode()))
    concise={k:v for k,v in report.items() if k not in ('core','details','behavior','phase_metrics')}
    concise.update(quality=core['quality'],final=core['final'],resources=core['resources'],
                   gross=detail['gross_resources'],gross_verified=detail['gross_ledger_verified'],
                   gross_issues=detail['gross_ledger_issues'],counts=actions['counts'],
                   snapshots=[f for f in core['trajectory'] if f['round'] in (49,99,199,299,399,499)],
                   splits=core['splits'],queen_deaths=[x for x in core['deaths'] if x['is_queen']],
                   suicides=actions['suicides'],advantage=core['advantage'],
                   queen_summary={t:{'first_action':v[0] if v else None,'last_action':v[-1] if v else None,
                    'unique_heads':len({tuple(x['head']) for x in v}),
                    'lengths':dict(Counter(x['length'] for x in v))} for t,v in actions['queen_actions'].items()})
    return concise


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('test-results/oct7-highrank-study'));args=ap.parse_args();root=args.root
    series=json.loads((root/'series-ui.json').read_text(encoding='utf8'))
    rows=[{'match_id':int(g['url'].split('/')[-1]),'series':s.get('series',s['games'][0]['url']),'teams':s['teams'],**g} for s in series for g in s['games']]
    ids=[r['match_id'] for r in rows]
    if len(ids)!=len(set(ids)) or not 70<=len(ids)<=150:raise ValueError('Invalid sample size or duplicate games')
    for sub in ('raw','reports'): (root/sub).mkdir(exist_ok=True)
    candidates,inventory,issues,ignored=scan_downloads(Path('D:/edge下载'),set(ids))
    imports=import_candidates(candidates,ids,root/'raw')
    (root/'imports.json').write_text(json.dumps(imports,indent=2),encoding='utf8')
    missing=[r for r in imports if r['import_status']!='imported']
    if missing:print('MISSING', [r['match_id'] for r in missing],flush=True)
    summaries=[];errors=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(one,root,r):r for r in rows if (root/'raw'/f"M{r['match_id']}.replay").exists()}
        for f in as_completed(jobs):
            try:summaries.append(f.result());print('DONE',jobs[f]['match_id'],len(summaries),flush=True)
            except Exception as error:errors.append({'match_id':jobs[f]['match_id'],'error':str(error)});print('ERROR',errors[-1],flush=True)
    result={'selected':len(ids),'analyzed':len(summaries),'errors':errors,'missing':[r['match_id'] for r in missing],'scan_issues':issues,'matches':sorted(summaries,key=lambda r:r['match_id'])}
    (root/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('FINISHED',len(summaries),'errors',len(errors),flush=True)


if __name__=='__main__':main()
