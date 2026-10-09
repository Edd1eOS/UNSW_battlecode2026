"""Quantify local long-unit choices and emergency transfers across completed games."""
from pathlib import Path
from collections import Counter
import argparse
import json
import math
import re
from tools.audit_online import load_replay
from tools.oct7_exploration_death_audit import Board, DIRS


def one(path, team):
    replay = load_replay(path, node_path='D:/node/node.exe')
    board = Board(replay['map'])
    live = {d['id']: {'team': d['team'], 'body': [(p['x'], p['y']) for p in d['body']]}
            for d in replay['initial_dragons']}
    notes, past, knowledge = {}, {}, {}
    rnd = -1
    counts = Counter()
    emergencies, deaths, turns = [], [], []
    actor = None
    actor_team = None
    current = None

    def physical_degree(point):
        return sum(board.step(point, direction) is not None for direction in DIRS)

    for index, event in enumerate(replay['events']):
        kind = event['type']
        if kind == 'roundStart':
            rnd = event['round']
        elif kind == 'turnStart':
            actor = event['id']
            unit = live[actor]
            actor_team = unit['team']
            body = unit['body']
            known = knowledge.setdefault(actor, set())
            known.update(((body[0][0] + dx) % board.W, (body[0][1] + dy) % board.H)
                         for dy in range(-3, 4) for dx in range(-3, 4))
            current = {'round': rnd, 'id': actor, 'length': len(body), 'head': body[0],
                       'body': body.copy(), 'free': math.ceil(len(body) / 4),
                       'map_degree': physical_degree(body[0])}
            if unit['team'] == team:
                turns.append(current)
        elif kind == 'dragonIndicator':
            notes[event['id']] = event['text']
        elif kind == 'dragonAction':
            ident = event['id']
            if live[ident]['team'] != team:
                continue
            current['action'] = event['action']
            current['note'] = notes.get(ident, '')
            past.setdefault(ident, []).append(current)
            if current['length'] >= 8:
                counts['long8_turns'] += 1
                if ' FLANK ' in current['note']:
                    counts['long8_flank_turns'] += 1
                risk_match = re.search(r'contact=(\d+)', current['note'])
                if risk_match and int(risk_match.group(1)) >= 10:
                    counts['long8_known_enemy_contact_turns'] += 1
                if event['action']['kind'] == 'move':
                    counts['long8_moves'] += 1
                    steps = len(event['action']['steps'])
                    counts['long8_steps'] += steps
                    counts['long8_available_free'] += current['free']
                    if steps < current['free']:
                        counts['long8_underuse_free'] += 1
                    if current['free'] > 7:
                        counts['long8_quota_over7'] += 1
            if event['action']['kind'] == 'split' and 'EMERGENCY' in current['note']:
                blocked = []
                for direction in DIRS:
                    nxt = board.step(current['head'], direction)
                    if nxt is None:
                        blocked.append('wall')
                    elif nxt == current['body'][1]:
                        blocked.append('own_neck')
                    elif nxt in current['body']:
                        blocked.append('own_other')
                    else:
                        occupier = next((i for i, u in live.items() if nxt in u['body']), None)
                        blocked.append('empty' if occupier is None else 'ally' if live[occupier]['team'] == team else 'enemy')
                row = dict(current)
                row['blockers'] = blocked
                row['prior_turns'] = [{k: v for k, v in t.items() if k != 'body'} for t in past[ident][-6:-1]]
                # Full geometry only, not a claim of what the bot knew.
                row['map_culdesac'] = current['map_degree'] == 1
                row['all_wall_or_neck'] = all(b in ('wall', 'own_neck') for b in blocked)
                row['last_turn_trap0'] = len(past[ident]) >= 2 and 'trap=0' in past[ident][-2]['note']
                emergencies.append(row)
                counts['emergency'] += 1
                counts['emergency_map_culdesac'] += row['map_culdesac']
                counts['emergency_sealed'] += row['all_wall_or_neck']
                counts['emergency_preceded_trap0'] += row['last_turn_trap0']
                if current['length'] >= 8:
                    counts['long8_emergency'] += 1
                    counts['long8_emergency_culdesac'] += row['map_culdesac']
                    counts['long8_emergency_preceded_trap0'] += row['last_turn_trap0']
        elif kind == 'dragonUpdate' and rnd >= 0:
            body = [(event['head']['x'], event['head']['y'])] + live[event['id']]['body']
            tail = event['tail']['x'], event['tail']['y']
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            assert body[-1] == tail
            live[event['id']]['body'] = body
        elif kind == 'dragonSplit':
            for ident, key in ((event['parentId'], 'parentBody'), (event['childId'], 'childBody')):
                live[ident] = {'team': event['team'], 'body': [(p['x'], p['y']) for p in event[key]]}
        elif kind == 'dragonDeath':
            ident = event['id']
            unit = live[ident]
            if unit['team'] == team and len(unit['body']) >= 8:
                counts['long8_death_' + event['reason']] += 1
                deaths.append(dict(round=rnd, id=ident, length=len(unit['body']), reason=event['reason'],
                                   note=notes.get(ident), actor=actor, actor_team=actor_team,
                                   latest_choice_round=past.get(ident, [{}])[-1].get('round')))
            del live[ident]
    return dict(replay=str(path), candidate_team=team, counts=counts, emergencies=emergencies, long_deaths=deaths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('panels', type=Path, nargs='+')
    args = parser.parse_args()
    rows = []
    for panel in args.panels:
        for meta in sorted((panel / 'games').glob('*/result.json')):
            info = json.loads(meta.read_text())
            row = one(meta.parent / 'raw.replay', info['candidate_team'])
            rows.append(row)
            print(json.dumps(dict(game=str(meta.parent), counts=row['counts'])), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(scope='Observational cross-game mechanics audit; geometry counts are hindsight unless explicitly visible, not an online strength claim.', games=rows), indent=2), encoding='utf-8')
