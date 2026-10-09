"""Extract exact visible geometry and attack resource accounting, not bot history."""
import copy
import json
from pathlib import Path
from audit_online import load_replay
from oct7_exploration_death_audit import Board, point

OUT = Path('test-results/oct9-queen-four-step')
index = json.loads(Path('test-results/oct9-deep-planning/v267-queen-killer-visibility.json').read_text())
reports = []
for source in index['games']:
    if source['map'] not in ('Around UNSW', 'Devil', 'Trophy'):
        continue
    data = load_replay(Path(source['replay']), node_path='D:/node/node.exe')
    board = Board(data['map'])
    queen, killer, deathround = source['queen_id'], source['actor'], source['death_round']
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body'])), 'facing': v.get('facing')} for v in data['initial_dragons']}
    pearls = set()
    rnd = -1
    actor = None
    snap = None
    attack = None
    for e in data['events']:
        kind = e['type']
        if kind == 'roundStart':
            rnd = e['round']
        elif kind == 'tileChange':
            p = point(e['tile'])
            if e['hasPearl']:
                pearls.add(p)
            else:
                pearls.discard(p)
                if attack and actor == killer:
                    attack['eaten'].append(p)
        elif kind == 'turnStart':
            actor = e['id']
            if actor == queen and rnd == deathround:
                head = live[queen]['body'][0]
                tiles = [((head[0]+dx) % board.W, (head[1]+dy) % board.H) for dy in range(-3, 4) for dx in range(-3, 4)]
                segments = []
                for who, unit in live.items():
                    for i, p in enumerate(unit['body']):
                        if not board.visible(p, head):
                            continue
                        facing = unit['facing'] if i == 0 else next(dd for dd in 'NESW' if board.step(p, dd) == unit['body'][i-1])
                        if facing is None:
                            facing = next(dd for dd in 'NESW' if board.step(unit['body'][1], dd) == p)
                        segments.append({'id': who, 'team': unit['team'], 'head': i == 0, 'position': p, 'facing': facing})
                snap = {'queen': copy.deepcopy(live[queen]), 'queen_id': queen, 'round': rnd,
                        'unit_count': sum(u['team'] == live[queen]['team'] for u in live.values()),
                        'map_width': board.W, 'map_height': board.H,
                        'visible_tiles': [{'position': p, 'pearl': p in pearls,
                                           'edges': {dd: {'kind': board.edges.get(board.edge(p, dd), (0, 0))[0],
                                                          'portal_id': board.edges.get(board.edge(p, dd), (0, 0))[1],
                                                          'destination': board.step(p, dd)} for dd in 'NESW'}} for p in tiles],
                        'visible_segments': segments,
                        'killer_actual_body_audit_only': live[killer]['body'].copy(),
                        'killer_visible_body_length': sum(s['id'] == killer for s in segments)}
            if actor == killer and rnd == deathround:
                attack = {'body_before': live[killer]['body'].copy(), 'length_before': len(live[killer]['body']),
                          'fixed_free_steps': (len(live[killer]['body']) + 3) // 4,
                          'queen_body_after_her_move': live[queen]['body'].copy(), 'pearls_before': list(pearls),
                          'updates': [], 'eaten': []}
        elif kind == 'dragonAction':
            if e['id'] == queen and rnd == deathround:
                snap['queen_action'] = e['action']
            if e['id'] == killer and rnd == deathround:
                attack['action'] = e['action']
        elif kind == 'dragonIndicator' and e['id'] == queen and rnd == deathround:
            snap['queen_note'] = e['text']
        elif kind == 'dragonUpdate' and rnd >= 0:
            unit = live[e['id']]
            unit['body'].insert(0, point(e['head']))
            tail = point(e['tail'])
            while len(unit['body']) > 1 and unit['body'][-1] != tail:
                unit['body'].pop()
            unit['facing'] = e['facing']
            if attack and e['id'] == killer and rnd == deathround:
                attack['updates'].append({'head': unit['body'][0], 'length_after': len(unit['body']), 'body_after': unit['body'].copy()})
        elif kind == 'dragonSplit':
            live[e['parentId']]['body'] = list(map(point, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(point, e['childBody'])), 'facing': e['childFacing']}
        elif kind == 'dragonDeath':
            if e['id'] == queen and rnd == deathround:
                break
            live.pop(e['id'], None)
    position = attack['body_before'][0]
    length = attack['length_before']
    path = []
    consumed = set()
    for i, dd in enumerate(attack['action']['steps']):
        target = board.step(position, dd)
        paid = i >= attack['fixed_free_steps']
        affordable = not paid or length > 2
        pearl = target in map(tuple, attack['pearls_before']) and target not in consumed
        collision = i == len(attack['updates'])
        row = {'step': i+1, 'direction': dd, 'from': position, 'to': target, 'length_before_payment': length,
               'paid': paid, 'affordable_before_target_food': affordable,
               'target_pearl_before_attack': pearl, 'head_collision': collision,
               'target_visible_at_queen_decision': board.visible(target, snap['queen']['body'][0])}
        if not collision:
            length = attack['updates'][i]['length_after']
            row['observed_length_after'] = length
            if pearl:
                consumed.add(target)
        else:
            row['length_after_payment_before_collision'] = length - int(paid)
        path.append(row)
        position = target
    attack['step_accounting'] = path
    attack.pop('pearls_before')
    reports.append({'map': source['map'], 'source': source['replay'], 'source_sha256': data['input_sha256'],
                    'killer_id': killer, 'snapshot': snap, 'actual_attack': attack,
                    'scope': 'Raw replay geometry and executed attack arithmetic only. Visible_tiles and visible_segments are known at the real Queen decision; actual hidden attacker body is separately audit-only. No sonar/inbox/countdown or full strategy Memory is reconstructed, and no complete controller input is asserted.'})
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'three-visible-threats-geometry.json').write_text(json.dumps(reports, indent=2))
for row in reports:
    print(json.dumps({'map': row['map'], 'queen_body': row['snapshot']['queen']['body'],
                      'queen_action': row['snapshot']['queen_action'],
                      'killer_visible_length': row['snapshot']['killer_visible_body_length'],
                      'actual_enemy_length': row['actual_attack']['length_before'],
                      'fixed_free_steps': row['actual_attack']['fixed_free_steps'],
                      'step_accounting': row['actual_attack']['step_accounting']}))
