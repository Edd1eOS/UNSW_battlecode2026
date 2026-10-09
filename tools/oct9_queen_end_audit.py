"""Explain four actual online Queen deaths without assuming a common cause."""
import json
from pathlib import Path
from audit_online import load_replay
from oct7_exploration_death_audit import Board, point

OUT = Path('test-results/oct9-final-sprint')
rows = json.loads((OUT / 'online-v35-bhole-audit.json').read_text())
report = []
for row in rows:
    death = row['stats']['B']['queen_death']
    if not death:
        continue
    data = load_replay(Path(row['path']), node_path='D:/node/node.exe')
    board = Board(data['map'])
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))} for v in data['initial_dragons']}
    rnd = -1
    selected = []
    killed_by = death['actor']
    queen = death['id']
    killer_action = None
    for event in data['events']:
        kind = event['type']
        if kind == 'roundStart':
            rnd = event['round']
        elif kind == 'turnStart' and event['id'] == queen and death['round'] - 4 <= rnd <= death['round']:
            own = live[queen]
            head = own['body'][0]
            attacker = live.get(killed_by)
            selected.append({'round': rnd, 'queen_head': head, 'queen_length': len(own['body']),
                             'killer_at_queen_turn': {'head': attacker['body'][0], 'actual_length': len(attacker['body']),
                                                     'team': attacker['team'], 'head_visible': board.visible(attacker['body'][0], head),
                                                     'visible_body_count': sum(board.visible(p, head) for p in attacker['body']),
                                                     'full_body_visible': all(board.visible(p, head) for p in attacker['body'])} if attacker else None,
                             'actual_free_steps': [dd for dd in 'NESW' if (n := board.step(head, dd)) is not None and not any(n in v['body'] for v in live.values())]})
        elif kind == 'dragonAction':
            if event['id'] == queen and selected and selected[-1]['round'] == rnd:
                action = event['action']
                selected[-1]['action'] = action
                selected[-1]['paid_steps_requested'] = max(0, len(action.get('steps', [])) - (selected[-1]['queen_length'] + 3) // 4)
            if event['id'] == killed_by and rnd == death['round']:
                killer_action = {'head_before': live[killed_by]['body'][0], 'length_before': len(live[killed_by]['body']),
                                 'action': event['action']}
        elif kind == 'dragonIndicator' and event['id'] == queen and selected and selected[-1]['round'] == rnd:
            selected[-1]['note'] = event['text']
        elif kind == 'dragonUpdate':
            if rnd < 0:
                continue
            v = live[event['id']]
            v['body'].insert(0, point(event['head']))
            tail = point(event['tail'])
            while len(v['body']) > 1 and v['body'][-1] != tail:
                v['body'].pop()
        elif kind == 'dragonSplit':
            live[event['parentId']]['body'] = list(map(point, event['parentBody']))
            live[event['childId']] = {'team': event['team'], 'body': list(map(point, event['childBody']))}
        elif kind == 'dragonDeath':
            live.pop(event['id'], None)
    report.append({'map': row['map'], 'replay': row['path'], 'replay_sha256': row['sha256'],
                   'queen_death_round': death['round'], 'queen_id': queen, 'killer_id': killed_by,
                   'last_five_turns': selected, 'killer_action': killer_action,
                   'scope': 'Raw online replay reconstruction. Attacker actual length is diagnostic, not claimed visible information.'})
(OUT / 'v35-queen-last5.json').write_text(json.dumps(report, indent=2))
for r in report:
    print(json.dumps({'map': r['map'], 'last_queen_turn': r['last_five_turns'][-1], 'killer_action': r['killer_action']}))
