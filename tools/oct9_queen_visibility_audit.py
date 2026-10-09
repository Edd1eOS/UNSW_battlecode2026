"""Classify killer visibility at the Queen's last actual decision, without synthesizing input."""
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import argparse
import json
import re
from tools.audit_online import load_replay
from tools.oct7_exploration_death_audit import Board, point


def one(path, bot_id='21677'):
    replay = load_replay(path, node_path='D:/node/node.exe')
    board = Board(replay['map'])
    team = next(t for t in 'AB' if replay['teams'][t]['botId'] == bot_id)
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))} for v in replay['initial_dragons']}
    qid = next(i for i, v in live.items() if i <= 1 and v['team'] == team)
    born = {i: {'round': -1, 'event_index': -1} for i in live}
    rnd = -1
    actor = None
    actor_team = None
    actor_head = None
    action = None
    steps = 0
    snapshot = None
    turn_h_deaths = []
    result = None
    for index, event in enumerate(replay['events']):
        kind = event['type']
        if kind == 'roundStart':
            rnd = event['round']
        elif kind == 'turnStart':
            actor = event['id']
            actor_team = live[actor]['team']
            actor_head = live[actor]['body'][0]
            action = None
            steps = 0
            turn_h_deaths = []
            if actor == qid:
                head = live[qid]['body'][0]
                snapshot = {'round': rnd, 'event_index': index, 'head': head,
                            'queen_body': live[qid]['body'].copy(),
                            'units': {i: {'team': v['team'], 'head': v['body'][0],
                                          'head_visible': board.visible(v['body'][0], head),
                                          'visible_segments': sum(board.visible(p, head) for p in v['body'])}
                                      for i, v in live.items()}}
        elif kind == 'dragonIndicator' and event['id'] == qid and snapshot:
            snapshot['note'] = event['text']
        elif kind == 'dragonAction':
            action = event.get('action')
            if event['id'] == qid and snapshot:
                snapshot['action'] = action
        elif kind == 'dragonUpdate' and rnd >= 0:
            body = [point(event['head'])] + live[event['id']]['body']
            tail = point(event['tail'])
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            assert body[-1] == tail
            live[event['id']]['body'] = body
            if event['id'] == actor:
                actor_head = body[0]
                steps += 1
        elif kind == 'dragonSplit':
            for ident, key in ((event['parentId'], 'parentBody'), (event['childId'], 'childBody')):
                live[ident] = {'team': event['team'], 'body': list(map(point, event[key]))}
            born[event['childId']] = {'round': rnd, 'event_index': index, 'parent': event['parentId']}
        elif kind == 'dragonDeath':
            ident = event['id']
            dying = live[ident]
            if event['reason'] == 'H':
                turn_h_deaths.append({'id': ident, 'team': dying['team'], 'head': dying['body'][0]})
            if ident == qid:
                result = {'map': next(line[9:] for line in replay['map'].splitlines() if line.startswith('MAP_NAME ')),
                          'replay': str(path), 'team': team, 'queen_id': qid, 'death_round': rnd,
                          'reason': event['reason'], 'length_at_death': len(dying['body']),
                          'actor': actor, 'actor_team': actor_team, 'actor_action': action,
                          'attack_steps_until_collision': steps + 1, 'queen_last_decision': snapshot}
                if event['reason'] == 'H':
                    killer = actor
                    if actor == qid:
                        destination = None
                        if action and action['kind'] == 'move' and steps < len(action['steps']):
                            destination = board.step(actor_head, action['steps'][steps])
                        others = [d['id'] for d in turn_h_deaths if d['id'] != qid and d['head'] == destination]
                        others += [i for i, v in live.items() if i != qid and v['body'][0] == destination]
                        killer = others[0] if others else None
                    prior = snapshot['units'].get(killer) if snapshot and killer is not None else None
                    birth = born.get(killer)
                    born_after = bool(snapshot and birth and birth['event_index'] > snapshot['event_index'])
                    if born_after and birth['round'] == rnd:
                        category = 'newborn_after_queen_decision_same_death_round'
                    elif born_after:
                        category = 'newborn_after_queen_decision_previous_round'
                    elif prior and prior['head_visible']:
                        category = 'head_visible_at_last_queen_decision'
                    elif prior:
                        category = 'head_outside_last_queen_view'
                    else:
                        category = 'unresolved'
                    match = re.search(r'contact=(\d+)', snapshot.get('note', '')) if snapshot else None
                    result.update(killer_id=killer, killer_birth=birth, killer_at_queen_decision=prior,
                                  visibility_category=category, queen_reported_contact=int(match[1]) if match else None)
                break
            del live[ident]
    if result is None:
        result = {'replay': str(path), 'team': team, 'queen_id': qid, 'reason': 'alive_at_end',
                  'map': next(line[9:] for line in replay['map'].splitlines() if line.startswith('MAP_NAME '))}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--bot-id', default='21677')
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(partial(one,bot_id=args.bot_id), sorted(args.directory.glob('*.replay'))))
    summary = dict(scope='Actual event chronology and toroidal 7x7 geometry only. Sonar is not synthesized or suppressed; no bot input replay is claimed.',
                   maps=len(rows), queen_outcomes=dict(Counter(r['reason'] for r in rows)),
                   H_visibility=dict(Counter(r['visibility_category'] for r in rows if r['reason'] == 'H')),
                   games=rows)
    args.out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'games'}))
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if k != 'queen_last_decision'}))
