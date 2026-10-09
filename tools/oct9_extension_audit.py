"""Outcome-level Queen and scorer survival audit of official online replays."""
import argparse
import json
from collections import Counter, deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from audit_online import load_replay
from oct7_exploration_death_audit import Board, point


def audit(path):
    data = load_replay(path, node_path='D:/node/node.exe')
    board = Board(data['map'])
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))} for v in data['initial_dragons']}
    hist = {i: deque(maxlen=12) for i in live}
    queen_turns = {i: [] for i in live if i <= 1}
    stats = {t: {'deaths': [], 'splits': [], 'long_turns': 0, 'long_trap_turns': 0,
                 'instruction_peak': 0, 'instruction_exceeded': 0, 'null_actions': 0, 'snapshots': {}, 'unit_turns': 0,
                 'queen_food': 0, 'queen_paid': 0, 'queen_shed_to_children': 0} for t in 'AB'}
    pearls = set()
    rnd = -1
    active = None

    def finish():
        nonlocal active
        if active is None:
            return
        who = active['id']
        after = live.get(who)
        active['end_length'] = len(after['body']) if after else 0
        if active.get('action', {}).get('kind') == 'move' and after:
            active['net_growth'] = len(after['body']) - active['length']
            active['executed_paid'] = active['food'] - active['net_growth']
            if who <= 1:
                stats[active['team']]['queen_food'] += active['food']
                stats[active['team']]['queen_paid'] += active['executed_paid']
        if active['length'] >= 8:
            stats[active['team']]['long_turns'] += 1
            stats[active['team']]['long_trap_turns'] += 'trap=1' in active.get('note', '')
        active = None

    for e in data['events']:
        kind = e['type']
        if kind == 'tileChange':
            p = point(e['tile'])
            if e['hasPearl']:
                pearls.add(p)
            else:
                pearls.discard(p)
                if active:
                    active['food'] += 1
        elif kind == 'roundStart':
            finish()
            rnd = e['round']
            if rnd in (20, 50, 100, 200):
                for team, stat in stats.items():
                    bodies = [v['body'] for v in live.values() if v['team'] == team]
                    stat['snapshots'][str(rnd)] = {'units': len(bodies), 'total_length': sum(map(len, bodies)),
                                                  'longest': max(map(len, bodies), default=0),
                                                  'queen_length': next((len(v['body']) for i, v in live.items() if i <= 1 and v['team'] == team), 0)}
        elif kind == 'turnStart':
            finish()
            who = e['id']
            unit = live[who]
            stats[unit['team']]['unit_turns'] += 1
            head = unit['body'][0]
            active = {'round': rnd, 'id': who, 'team': unit['team'], 'head': head,
                      'length': len(unit['body']), 'food': 0}
            if who <= 1:
                occupied = {p: {'id': i, 'team': v['team'], 'head': n == 0}
                            for i, v in live.items() for n, p in enumerate(v['body']) if board.visible(p, head)}
                visited = {head}
                todo = deque([head])
                boundary = False
                while todo:
                    p = todo.popleft()
                    for dd in 'NESW':
                        q = board.step(p, dd)
                        if q is None:
                            continue
                        if not board.visible(q, head):
                            boundary = True
                            continue
                        if q in visited or q in occupied:
                            continue
                        visited.add(q)
                        todo.append(q)
                active.update(body=unit['body'].copy(), static_visible_free_region=len(visited)-1,
                              region_touches_unseen=boundary,
                              neighbours={dd: {'destination': board.step(head, dd), 'occupant': occupied.get(board.step(head, dd))} for dd in 'NESW'},
                              visible_pearls=[p for p in pearls if board.visible(p, head)])
                queen_turns[who].append(active)
            hist[who].append(active)
        elif kind == 'dragonIndicator' and active and e['id'] == active['id']:
            active['note'] = e['text']
        elif kind == 'dragonAction' and active:
            active['action'] = e.get('action') or {}
            stat = stats[active['team']]
            ins = e.get('instructions', {})
            stat['instruction_peak'] = max(stat['instruction_peak'], ins.get('count', 0))
            stat['instruction_exceeded'] += bool(ins.get('exceeded'))
            stat['null_actions'] += e.get('action') is None
        elif kind == 'dragonUpdate':
            if rnd < 0:
                continue
            v = live[e['id']]
            v['body'].insert(0, point(e['head']))
            tail = point(e['tail'])
            while len(v['body']) > 1 and v['body'][-1] != tail:
                v['body'].pop()
        elif kind == 'dragonSplit':
            parent = e['parentId']
            stats[e['team']]['splits'].append({'round': rnd, 'id': parent, 'child': e['childId'],
                                              'before_length': len(live[parent]['body']), 'child_length': len(e['childBody']),
                                              'note': active.get('note', '') if active else ''})
            if parent <= 1:
                stats[e['team']]['queen_shed_to_children'] += len(e['childBody'])
            live[parent]['body'] = list(map(point, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(point, e['childBody']))}
            hist[e['childId']] = deque(maxlen=12)
        elif kind == 'dragonDeath':
            who = e['id']
            victim = live[who]
            row = {'round': rnd, 'id': who, 'length': len(victim['body']), 'reason': e['reason'],
                   'actor': active['id'] if active else None,
                   'actor_team': active['team'] if active else None,
                   'last_turns': list(hist[who])}
            stats[victim['team']]['deaths'].append(row)
            del live[who]
    finish()
    for team, stat in stats.items():
        longdead = [x for x in stat['deaths'] if x['length'] >= 8]
        emergencies = [x for x in stat['splits'] if 'EMERGENCY' in x['note']]
        emergencyids = {(x['id'], x['round']) for x in emergencies}
        stat['summary'] = {'deaths': len(stat['deaths']), 'death_reasons': dict(Counter(x['reason'] for x in stat['deaths'])),
                           'long_deaths': len(longdead), 'long_death_reasons': dict(Counter(x['reason'] for x in longdead)),
                           'long_deaths_enemy_turn': sum(x['actor_team'] != team for x in longdead),
                           'long_head_deaths_enemy_turn': sum(x['reason'] == 'H' and x['actor_team'] != team for x in longdead),
                           'long_head_length_lost_enemy_turn': sum(x['length'] for x in longdead if x['reason'] == 'H' and x['actor_team'] != team),
                           'emergency_splits': len(emergencies),
                           'emergency_long_splits': sum(x['before_length'] >= 8 for x in emergencies),
                           'emergency_parent_dies_within_two_rounds': sum(any(d['id'] == x['id'] and 0 <= d['round']-x['round'] <= 2 for d in stat['deaths']) for x in emergencies),
                           'long_deaths_previous_food_action': sum(bool(x['last_turns']) and ' FOOD ' in x['last_turns'][-1].get('note', '') for x in longdead),
                           'queen_split_details': [x for x in stat['splits'] if x['id'] <= 1],
                           'queen_deaths': [{k: v for k, v in x.items() if k != 'last_turns'} for x in stat['deaths'] if x['id'] <= 1],
                           'total_splits': len(stat['splits'])}
        stat['final'] = data['result']['team' + team]
    return {'path': str(path), 'map': next(x[9:] for x in data['map'].splitlines() if x.startswith('MAP_NAME ')),
            'teams': data['teams'], 'stats': stats, 'queen_turns': queen_turns, 'result': data['result'],
            'scope': 'Official recorded outcome audit. Local region uses visible walls/current occupants with all bodies static; it is a diagnostic hazard feature, not a proof of inevitable death or a counterfactual win.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--compact', action='store_true', help='Keep outcome summaries and Queen death windows, not every unit history.')
    a = p.parse_args()
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(audit, sorted(a.directory.glob('*.replay'))))
    if a.compact:
        for row in rows:
            row['queen_turns'] = {k: v[-20:] for k, v in row['queen_turns'].items()}
            for stat in row['stats'].values():
                stat.pop('deaths')
                stat.pop('splits')
    a.out.write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(json.dumps({'map': r['map'], 'stats': {t: {k: v for k, v in s.items() if k not in ('deaths', 'splits')} for t, s in r['stats'].items()}}))
