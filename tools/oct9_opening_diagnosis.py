"""Audit concrete opening costs using a public replay and verified observations.

No strength match. Initial update events repeat initialized bodies and must not
be inserted a second time. Food routes below use only the current 7x7 window.
"""
import gzip
import argparse
import json
import re
from collections import Counter, deque
from pathlib import Path

from oct7_exploration_death_audit import Board, point
from unswbc.engine import EngineModule
from unswbc.sandbox import SandboxBot, WasmPool
from verify_candidate import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/oct9-aggressive'


def causal_food_probe(data, reference, candidate=None):
    """Stop at Queen round 4: reproduce only the local consequence, not a match."""
    action_at = {}
    rnd = None
    for event in data['events']:
        if event['type'] == 'roundStart':
            rnd = event['round']
        elif event['type'] == 'dragonAction':
            action_at[(rnd, event['id'])] = event['action']
    name = next(x for x in data['map'].splitlines() if x.startswith('MAP_NAME '))
    paths = [p for p in (ROOT / 'maps/current').glob('*.map') if name in p.read_text().splitlines()]
    assert len(paths) == 1
    tile_lines = {tuple(s.split()[1:3]): s for s in paths[0].read_text().splitlines() if s.startswith('TILE ')}
    source_map = '\n'.join(tile_lines.get(tuple(s.split()[1:3]), s) if s.startswith('TILE ') else s
                           for s in data['map'].splitlines()) + '\n'

    class StopProbe(Exception):
        pass

    cases = {}
    for label in ('recorded_paid_SW', 'free_S_then_W'):
        frames = []

        def reply(who, block):
            r = int(re.search(rb'^ROUND (\d+)', block, re.M)[1])
            if who == 1:
                frames.append({'round': r, 'input': block.decode(),
                               'length': int(re.search(rb'^LENGTH (\d+)', block, re.M)[1])})
                if r >= 4:
                    raise StopProbe()
            action = action_at[(r, who)]
            cmd = 'MOVE ' + ''.join(action['steps']) if action['kind'] == 'move' else (
                'SPLIT ' + str(action['childSegmentCount']) if action['kind'] == 'split' else '')
            if who == 1 and label == 'free_S_then_W' and r in (2, 3):
                cmd = 'MOVE ' + ('S' if r == 2 else 'W')
            if who == 1:
                frames[-1]['action'] = cmd
            return (cmd + '\nPROTOCOL 3\nENDTURN\n').encode()

        try:
            EngineModule().run(source_map.encode(), reply, seed=int(data['seed']), on_notice=lambda _: None)
        except StopProbe:
            pass
        else:
            raise AssertionError('Probe did not reach Queen round 4')
        assert len(frames) == 5
        cases[label] = frames
    expected = reference['queens']['1']['frames']
    assert all(a['input'] == b['input'] for a, b in zip(cases['recorded_paid_SW'], expected))
    assert all(a['input'] == b['input'] for a, b in zip(cases['recorded_paid_SW'][:3], cases['free_S_then_W'][:3]))
    assert cases['recorded_paid_SW'][4]['length'] == 3
    assert cases['free_S_then_W'][4]['length'] == 4
    result = {'only_changes': {'queen_round2': 'MOVE SW -> MOVE S', 'queen_round3': 'MOVE S -> MOVE W'},
              'original_first5_queen_observations_equal': True,
              'counterfactual_observations_equal_until_action_changed': True,
              'original_length_round4': 3, 'free_path_length_round4': 4,
              'cases': cases,
              'scope': 'Official engine local mechanism counterfactual, stopped at round 4. Same map/seed, unchanged other actions; no strength or win inference.'}
    (OUT / 'queen-growth-causal-probe.json').write_text(json.dumps(result, indent=2))
    if candidate is not None:
        wasm, digest = build(candidate)
        pool = WasmPool([str(wasm)], key='oct9-opening-' + digest[:20])
        bot = None
        frames = []

        def spawn(who, block):
            nonlocal bot
            if who == 1:
                bot = SandboxBot(pool, init=block, name='1')

        def candidate_reply(who, block):
            r = int(re.search(rb'^ROUND (\d+)', block, re.M)[1])
            if who == 1:
                output = bot.ask(block).decode()
                frames.append({'round': r, 'input': block.decode(), 'output': output,
                               'length': int(re.search(rb'^LENGTH (\d+)', block, re.M)[1]),
                               'cpu_points': bot.live[0], 'error': bot.error})
                if r >= 4:
                    raise StopProbe()
                return output.encode()
            action = action_at[(r, who)]
            cmd = 'MOVE ' + ''.join(action['steps']) if action['kind'] == 'move' else (
                'SPLIT ' + str(action['childSegmentCount']) if action['kind'] == 'split' else '')
            return (cmd + '\nPROTOCOL 3\nENDTURN\n').encode()

        try:
            try:
                EngineModule().run(source_map.encode(), candidate_reply, bot_spawn=spawn,
                                   seed=int(data['seed']), on_notice=lambda _: None)
            except StopProbe:
                pass
        finally:
            if bot is not None:
                bot.stop()
            pool.close()
        report = {'candidate': str(candidate), 'source_sha256': digest, 'frames': frames,
                  'scope': 'Official-engine first5 Queen decisions, all other units follow original recorded actions. Interrupted before round4 action is applied; no full match or strength assertion.'}
        (OUT / 'candidate-queen-opening.json').write_text(json.dumps(report, indent=2))
        print(json.dumps({'candidate': str(candidate), 'opening': [{'round': f['round'], 'length': f['length'], 'output': f['output']} for f in frames]}, indent=2))
    return {k: v for k, v in result.items() if k != 'cases'}


def audit(candidate=None):
    data = json.loads((ROOT / 'test-results/oct9-imitation/M1474687.decoded.json').read_text())
    board = Board(data['map'])
    live = {v['id']: {'team': v['team'], 'body': list(map(point, v['body']))}
            for v in data['initial_dragons']}
    food = set()
    rnd = -1
    rows = []
    action_row = None
    first_food = {}
    first_growth = {}
    initial_updates = 0
    note = ''

    def visible_food_routes(head):
        window = {((head[0] + dx) % board.W, (head[1] + dy) % board.H)
                  for dx in range(-3, 4) for dy in range(-3, 4)}
        occupied = {p for v in live.values() for p in v['body']}
        queue = deque([(head, '')])
        seen = {head}
        found = []
        while queue:
            at, path = queue.popleft()
            if at in food:
                found.append({'distance': len(path), 'target': at, 'path': path})
            for d in 'NESW':
                nxt = board.step(at, d)
                if nxt is not None and nxt in window and nxt not in occupied and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + d))
        return sorted(found, key=lambda r: (r['distance'], r['target'])), sorted(food & window)

    for event in data['events']:
        kind = event['type']
        if kind == 'roundStart':
            rnd = event['round']
        elif kind == 'turnStart':
            action_row = None
            note = ''
        elif kind == 'dragonIndicator':
            note = event['text']
        elif kind == 'tileChange':
            p = point(event['tile'])
            if event['hasPearl']:
                food.add(p)
            else:
                food.discard(p)
                if action_row is not None:
                    action_row['food_removed'].append(p)
                    first_food.setdefault(action_row['id'], rnd)
        elif kind == 'dragonAction':
            who = event['id']
            dragon = live[who]
            length = len(dragon['body'])
            if length >= 4:
                first_growth.setdefault(who, rnd)
            routes, visible = visible_food_routes(dragon['body'][0])
            action = event['action']
            steps = action.get('steps', [])
            action_row = {'round': rnd, 'id': who, 'team': dragon['team'],
                          'head': dragon['body'][0], 'length_before': length,
                          'action': action, 'paid_steps': max(0, len(steps) - (length + 3) // 4),
                          'visible_food': visible, 'visible_food_routes': routes,
                          'food_removed': [], 'length_after': length, 'note': note}
            rows.append(action_row)
        elif kind == 'dragonUpdate':
            # Header repeats initial head/tail. Do not manufacture a body segment.
            if rnd < 0:
                initial_updates += 1
                continue
            dragon = live[event['id']]
            dragon['body'].insert(0, point(event['head']))
            tail = point(event['tail'])
            while len(dragon['body']) > 1 and dragon['body'][-1] != tail:
                dragon['body'].pop()
            if action_row is not None and event['id'] == action_row['id']:
                action_row['length_after'] = len(dragon['body'])
        elif kind == 'dragonSplit':
            live[event['parentId']]['body'] = list(map(point, event['parentBody']))
            live[event['childId']] = {'team': event['team'], 'body': list(map(point, event['childBody']))}
        elif kind == 'dragonDeath':
            live.pop(event['id'], None)

    checks = json.loads(gzip.decompress((OUT / 'M1474687-observations.json.gz').read_bytes()))
    causal_probe = causal_food_probe(data, checks, candidate)
    report = {
        'source': 'M1474687', 'source_sha256': data['input_sha256'],
        'official_engine_recorded_action_physics_equal': checks['physical_events_equal'],
        'official_engine_verified_events': checks['physical_events'],
        'initial_updates_skipped': initial_updates,
        'causal_probe': causal_probe,
        'first_food_removal_round_initial_ids': {i: first_food.get(i) for i in range(4)},
        'first_length4_round_initial_ids': {i: first_growth.get(i) for i in range(4)},
        'first30_initial_units': [r for r in rows if r['id'] < 4 and r['round'] < 30],
        'queen_food_sprints': [r for r in rows if r['id'] == 1 and r['food_removed'] and r['paid_steps']],
        'initial_unit_totals_first30': {
            i: {'food': sum(len(r['food_removed']) for r in rows if r['id'] == i and r['round'] < 30),
                'paid_steps': sum(r['paid_steps'] for r in rows if r['id'] == i and r['round'] < 30)}
            for i in range(4)
        },
        'limits': 'Recorded trajectory diagnosis; no counterfactual strength claim. Food routes use visible window, but portal mapping is reconstructed from public replay and routes with remote landing outside window are excluded.'
    }
    (OUT / 'opening-diagnosis.json').write_text(json.dumps(report, indent=2))
    # Actual legal observation frames for earliest destructive food sprint.
    q = checks['queens']['1']
    prefix = [f for f in q['frames'] if f['round'] <= 2]
    (OUT / 'queen-first3-input.json').write_text(json.dumps({'input': q['init'] + ''.join(f['input'] for f in prefix) + 'ENDGAME\n',
                                                          'recorded_actions': [f['action'] for f in prefix],
                                                          'scope': 'Official legal observations, continuous initial memory; only first three frames.'}, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ('first30_initial_units', 'queen_food_sprints')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True, parents=True)
    audit(args.candidate)
