"""Read-only opening and Queen-death audit of public online replay files."""
import argparse
import json
from collections import Counter, deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from audit_online import load_replay
from oct7_exploration_death_audit import Board, point


def audit(path):
    d = load_replay(path, node_path='D:/node/node.exe')
    b = Board(d['map'])
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))} for v in d['initial_dragons']}
    stats = {t: {'splits': 0, 'pearls': 0, 'paid_steps_requested': 0, 'death_reasons': Counter(),
                 'first_length4': {}, 'first_split': None, 'instruction_peak': 0, 'instruction_exceeded': 0,
                 'null_actions': 0, 'snapshots': {}, 'queen_death': None} for t in 'AB'}
    queen_history = {0: deque(maxlen=14), 1: deque(maxlen=14)}
    rnd = -1
    actor = None
    action = None
    steps_done = 0
    for e in d['events']:
        k = e['type']
        if k == 'roundStart':
            rnd = e['round']
            actor = None
            if rnd in (20, 50):
                for team, s in stats.items():
                    bodies = [v['body'] for v in live.values() if v['team'] == team]
                    s['snapshots'][str(rnd)] = {'units': len(bodies), 'total_length': sum(map(len, bodies)),
                                              'queen_length': next((len(v['body']) for i, v in live.items() if i <= 1 and v['team'] == team), 0)}
        elif k == 'turnStart':
            actor = e['id']
            action = None
            steps_done = 0
            if actor <= 1:
                v = live[actor]
                head = v['body'][0]
                parts = {p: {'id': i, 'team': vv['team'], 'head': n == 0, 'position': p}
                         for i, vv in live.items() for n, p in enumerate(vv['body']) if b.visible(p, head)}
                queen_history[actor].append({'round': rnd, 'body': v['body'].copy(),
                                             'neighbours': {dd: {'destination': b.step(head, dd), 'occupant': parts.get(b.step(head, dd))} for dd in 'NESW'},
                                             'visible_heads': [v for v in parts.values() if v['head']],
                                             'visible_parts': list(parts.values())})
        elif k == 'dragonIndicator' and e['id'] <= 1 and queen_history[e['id']]:
            queen_history[e['id']][-1]['note'] = e['text']
        elif k == 'dragonAction':
            actor = e['id']
            action = e.get('action')
            s = stats[live[actor]['team']]
            length = len(live[actor]['body'])
            if actor < 4 and length >= 4:
                s['first_length4'].setdefault(str(actor), rnd)
            if action is None:
                s['null_actions'] += 1
            elif action['kind'] == 'move':
                s['paid_steps_requested'] += max(0, len(action['steps']) - (length + 3) // 4)
            ins = e.get('instructions', {})
            s['instruction_peak'] = max(s['instruction_peak'], ins.get('count', 0))
            s['instruction_exceeded'] += bool(ins.get('exceeded'))
            if actor <= 1 and queen_history[actor]:
                queen_history[actor][-1]['action'] = action
        elif k == 'dragonUpdate':
            if rnd < 0:
                continue
            v = live[e['id']]
            v['body'].insert(0, point(e['head']))
            tail = point(e['tail'])
            while len(v['body']) > 1 and v['body'][-1] != tail:
                v['body'].pop()
            if e['id'] == actor:
                steps_done += 1
        elif k == 'dragonSplit':
            stats[e['team']]['splits'] += 1
            if stats[e['team']]['first_split'] is None:
                stats[e['team']]['first_split'] = rnd
            live[e['parentId']]['body'] = list(map(point, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(point, e['childBody']))}
        elif k == 'tileChange' and not e['hasPearl'] and actor in live:
            stats[live[actor]['team']]['pearls'] += 1
        elif k == 'dragonDeath':
            who = e['id']
            v = live[who]
            s = stats[v['team']]
            s['death_reasons'][e['reason']] += 1
            if who <= 1:
                dst = None
                occupant = None
                if actor in live and action and action['kind'] == 'move' and steps_done < len(action['steps']):
                    dst = b.step(live[actor]['body'][0], action['steps'][steps_done])
                    occupant = next(({'id': i, 'team': vv['team'], 'head': vv['body'][0] == dst}
                                     for i, vv in live.items() if dst in vv['body']), None)
                s['queen_death'] = {'round': rnd, 'reason': e['reason'], 'id': who, 'actor': actor,
                                    'actor_action': action, 'steps_completed': steps_done,
                                    'attempted_target': dst, 'target_occupant': occupant,
                                    'last_turns': list(queen_history[who])}
            del live[who]
    return {'path': str(path), 'sha256': d['input_sha256'], 'teams': d['teams'],
            'map': next(x[9:] for x in d['map'].splitlines() if x.startswith('MAP_NAME ')),
            'result': d['result'], 'rounds': rnd + 1, 'stats': stats,
            'limits': 'Replay observations only. Requested paid steps may not all execute. No causal win claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(audit, sorted(a.directory.glob('*.replay'))))
    a.out.write_text(json.dumps(rows, indent=2))
    for row in rows:
        compact = {k: v for k, v in row.items() if k != 'stats'}
        compact['stats'] = {team: {**s, 'queen_death': {k: v for k, v in s['queen_death'].items() if k != 'last_turns'} if s['queen_death'] else None} for team, s in row['stats'].items()}
        print(json.dumps(compact), flush=True)
