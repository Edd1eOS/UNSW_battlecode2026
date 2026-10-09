"""Quantify executed resource conversion and newborn escape/death, read only."""
import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from audit_online import load_replay
from oct7_exploration_death_audit import Board, point


def audit(path):
    d = load_replay(path, node_path='D:/node/node.exe')
    board = Board(d['map'])
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))} for v in d['initial_dragons']}
    stats = {t: {'surviving_move_food': 0, 'surviving_move_net_growth': 0, 'inferred_executed_paid_steps': 0,
                 'zero_net_paid_food_moves': 0, 'fatal_moves': 0, 'accounting_inconsistencies': 0,
                 'consumed_origin': Counter(), 'queen': Counter(), 'births': []} for t in 'AB'}
    births = {}
    pearl_origin = {}
    rnd = -1
    active = None

    def finish():
        nonlocal active
        if active is None or active['kind'] != 'move':
            active = None
            return
        s = stats[active['team']]
        who = active['id']
        if who not in live:
            s['fatal_moves'] += 1
        else:
            net = len(live[who]['body']) - active['before']
            cost = active['food'] - net
            zero = active['food'] > 0 and cost > 0 and net <= 0
            s['surviving_move_food'] += active['food']
            s['surviving_move_net_growth'] += net
            s['inferred_executed_paid_steps'] += cost
            s['zero_net_paid_food_moves'] += zero
            s['accounting_inconsistencies'] += cost < 0
            if who <= 1:
                s['queen'].update({'food': active['food'], 'net_growth': net, 'paid_steps': cost, 'zero_net_paid_food_moves': int(zero)})
        active = None

    for e in d['events']:
        k = e['type']
        if k == 'roundStart':
            finish()
            rnd = e['round']
        elif k == 'turnStart':
            finish()
            who = e['id']
            if who in births and 'first_turn_round' not in births[who]:
                head = live[who]['body'][0]
                occupied = {p for v in live.values() for p in v['body']}
                exits = [dd for dd in 'NESW' if (n := board.step(head, dd)) is not None and n not in occupied]
                births[who].update(first_turn_round=rnd, first_turn_free_exits=len(exits), first_turn_exit_directions=exits)
        elif k == 'dragonAction':
            a = e.get('action')
            if a:
                who = e['id']
                active = {'id': who, 'team': live[who]['team'], 'kind': a['kind'], 'before': len(live[who]['body']), 'food': 0}
        elif k == 'tileChange':
            tile = point(e['tile'])
            if e['hasPearl']:
                pearl_origin[tile] = 'turn_drop' if active else 'round_spawn'
            else:
                source = pearl_origin.pop(tile, 'unobserved_source')
                if active:
                    active['food'] += 1
                    stats[active['team']]['consumed_origin'][source] += 1
        elif k == 'dragonUpdate':
            if rnd < 0:
                continue
            v = live[e['id']]
            v['body'].insert(0, point(e['head']))
            tail = point(e['tail'])
            while len(v['body']) > 1 and v['body'][-1] != tail:
                v['body'].pop()
        elif k == 'dragonSplit':
            live[e['parentId']]['body'] = list(map(point, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(point, e['childBody']))}
            r = {'id': e['childId'], 'parent': e['parentId'], 'born_round': rnd, 'length': len(e['childBody'])}
            births[e['childId']] = r
            stats[e['team']]['births'].append(r)
        elif k == 'dragonDeath':
            if e['id'] in births:
                births[e['id']].update(death_round=rnd, death_reason=e['reason'])
            live.pop(e['id'], None)
    finish()
    for s in stats.values():
        mature = [b for b in s['births'] if b['born_round'] <= rnd - 3]
        first = [b for b in s['births'] if 'first_turn_round' in b]
        s['birth_summary'] = {'births': len(s['births']), 'first_turn_observed': len(first),
                              'first_turn_no_free_exit': sum(b['first_turn_free_exits'] == 0 for b in first),
                              'first_turn_only_one_free_exit': sum(b['first_turn_free_exits'] == 1 for b in first),
                              'eligible_three_round_followup': len(mature),
                              'died_within_three_rounds': sum(b.get('death_round', 10000) <= b['born_round'] + 3 for b in mature)}
    return {'path': str(path), 'map': next(s[9:] for s in d['map'].splitlines() if s.startswith('MAP_NAME ')),
            'sha256': d['input_sha256'], 'teams': d['teams'], 'stats': stats,
            'scope': 'Executed paid cost inferred only for movement actions surviving their own turn: food minus length change. Fatal turns excluded. Pearl origin round_spawn vs turn_drop is event-phase classification (ordinary spawn vs corpse/suicide drops), not hidden map inference. Newborn exits use actual current board, including remote portal occupancy; this is an outcome metric, not claimed available sensing.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(audit, sorted(a.directory.glob('*.replay'))))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(json.dumps({'map': r['map'], 'stats': {t: {k: v for k, v in s.items() if k != 'births'} for t, s in r['stats'].items()}}), flush=True)
