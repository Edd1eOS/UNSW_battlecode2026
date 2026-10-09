"""Quick actual-online Queen growth and split-count summary; no engine rerun."""
import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from audit_online import load_replay


def pt(p):
    return p['x'], p['y']


def audit(path):
    d = load_replay(path, node_path='D:/node/node.exe')
    live = {v['id']: {'team': v['team'], 'body': list(map(pt, v['body']))} for v in d['initial_dragons']}
    s = {t: {'queen_id': next(i for i, v in live.items() if i <= 1 and v['team'] == t),
             'queen_length_initial': next(len(v['body']) for i, v in live.items() if i <= 1 and v['team'] == t),
             'queen_max_length': 0, 'snapshots': {}, 'queen_split_rounds': [], 'ordinary_splits': 0,
             'queen_food': 0, 'queen_paid_steps_requested': 0, 'queen_death': None,
             'instruction_peak': 0, 'instruction_exceeded': 0} for t in 'AB'}
    for t in s:
        s[t]['queen_max_length'] = s[t]['queen_length_initial']
    rnd = -1
    actor = None
    for e in d['events']:
        k = e['type']
        if k == 'roundStart':
            rnd = e['round']
            actor = None
            if rnd in (20, 50, 100, 200):
                for team, stat in s.items():
                    bodies = [v['body'] for v in live.values() if v['team'] == team]
                    q = live.get(stat['queen_id'])
                    stat['snapshots'][str(rnd)] = {'queen_length': len(q['body']) if q else 0,
                                                 'units': len(bodies), 'total_length': sum(map(len, bodies)),
                                                 'longest': max(map(len, bodies), default=0)}
        elif k == 'turnStart':
            actor = e['id']
        elif k == 'dragonAction':
            who = e['id']
            stat = s[live[who]['team']]
            ins = e.get('instructions', {})
            stat['instruction_peak'] = max(stat['instruction_peak'], ins.get('count', 0))
            stat['instruction_exceeded'] += bool(ins.get('exceeded'))
            if who <= 1 and e['action'] and e['action']['kind'] == 'move':
                stat['queen_paid_steps_requested'] += max(0, len(e['action']['steps']) - (len(live[who]['body']) + 3) // 4)
        elif k == 'tileChange' and not e['hasPearl'] and actor is not None and actor <= 1 and actor in live:
            s[live[actor]['team']]['queen_food'] += 1
        elif k == 'dragonUpdate':
            if rnd < 0:
                continue
            v = live[e['id']]
            v['body'].insert(0, pt(e['head']))
            tail = pt(e['tail'])
            while len(v['body']) > 1 and v['body'][-1] != tail:
                v['body'].pop()
            if e['id'] <= 1:
                s[v['team']]['queen_max_length'] = max(s[v['team']]['queen_max_length'], len(v['body']))
        elif k == 'dragonSplit':
            stat = s[e['team']]
            if e['parentId'] <= 1:
                stat['queen_split_rounds'].append(rnd)
            else:
                stat['ordinary_splits'] += 1
            live[e['parentId']]['body'] = list(map(pt, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(pt, e['childBody']))}
        elif k == 'dragonDeath':
            if e['id'] <= 1:
                s[live[e['id']]['team']]['queen_death'] = {'round': rnd, 'reason': e['reason']}
            live.pop(e['id'], None)
    for team, stat in s.items():
        stat['final'] = d['result']['team' + team]
    return {'path': str(path), 'sha256': d['input_sha256'], 'teams': d['teams'],
            'map': next(x[9:] for x in d['map'].splitlines() if x.startswith('MAP_NAME ')),
            'result': d['result'], 'rounds': rnd + 1, 'stats': s,
            'scope': 'Public online replay measurements. Snapshots at start of zero-based round; missing snapshot means game ended earlier. No controlled win-rate inference.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(audit, sorted(a.directory.glob('*.replay'))))
    a.out.write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(json.dumps(r), flush=True)
