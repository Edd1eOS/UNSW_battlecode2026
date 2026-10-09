"""Local official-engine intervention proving the friendly trap was avoidable."""
import gzip
import argparse
import json
import re
from pathlib import Path
from unswbc.engine import EngineModule
from unswbc.sandbox import SandboxBot, WasmPool
from verify_candidate import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/oct9-aggressive'
data = json.loads((OUT / 'trophyB-v258-decoded.json').read_text())
reference = json.loads(gzip.decompress((OUT / 'trophyB-observations/raw-observations.json.gz').read_bytes()))
actions = {}
rnd = -1
for e in data['events']:
    if e['type'] == 'roundStart': rnd = e['round']
    elif e['type'] == 'dragonAction': actions[(rnd, e['id'])] = e['action']
name = next(x for x in data['map'].splitlines() if x.startswith('MAP_NAME '))
maps = [p for p in (ROOT / 'maps/current').glob('*.map') if name in p.read_text().splitlines()]
assert len(maps) == 1
tile_lines = {tuple(s.split()[1:3]): s for s in maps[0].read_text().splitlines() if s.startswith('TILE ')}
map_text = '\n'.join(tile_lines.get(tuple(s.split()[1:3]), s) if s.startswith('TILE ') else s for s in data['map'].splitlines()) + '\n'


class StopProbe(Exception):
    pass


results = {}
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path)
args = parser.parse_args()
candidate_pool = None
digest = None
if args.candidate is not None:
    wasm, digest = build(args.candidate)
    candidate_pool = WasmPool([str(wasm)], key='causal-cooperation-' + digest[:20])
cases = ['recorded', 'queen_escapes_E_S_E'] + (['candidate_fresh_at56'] if candidate_pool else [])
for case in cases:
    frames = []
    deaths = []
    candidate_bot = None
    if case == 'candidate_fresh_at56':
        candidate_bot = SandboxBot(candidate_pool, init=reference['queens']['1']['init'].encode(), name='1')

    def reply(who, block):
        r = int(re.search(rb'^ROUND (\d+)', block, re.M)[1])
        if r >= 60:
            raise StopProbe()
        action = actions.get((r, who))
        assert action is not None, (r, who)
        cmd = 'MOVE ' + ''.join(action['steps']) if action['kind'] == 'move' else (
            'SPLIT ' + str(action['childSegmentCount']) if action['kind'] == 'split' else '')
        if case == 'queen_escapes_E_S_E' and who == 1 and r in (56, 57, 58):
            cmd = 'MOVE ' + {56: 'E', 57: 'S', 58: 'E'}[r]
        if case == 'candidate_fresh_at56' and who == 1 and r >= 56:
            cmd = candidate_bot.ask(block).decode()
        if who == 1:
            frames.append({'round': r, 'input': block.decode(), 'action': cmd})
        return (cmd + '\nPROTOCOL 3\nENDTURN\n').encode()

    try:
        EngineModule().run(map_text.encode(), reply, seed=int(data['seed']),
                           on_death=lambda i, r, why: deaths.append({'id': i, 'round': r, 'reason': why}),
                           on_notice=lambda _: None)
    except StopProbe:
        pass
    finally:
        if candidate_bot is not None:
            candidate_bot.stop()
    results[case] = {'queen_deaths': [d for d in deaths if d['id'] == 1], 'frames': frames}
if candidate_pool is not None:
    candidate_pool.close()

original = reference['queens']['1']['frames']
assert all(a['input'] == b['input'] for a, b in zip(results['recorded']['frames'], original))
assert all(a['input'] == b['input'] for a, b in zip(results['recorded']['frames'][:57], results['queen_escapes_E_S_E']['frames'][:57]))
assert results['recorded']['queen_deaths'] == [{'id': 1, 'round': 59, 'reason': 'O'}]
assert not results['queen_escapes_E_S_E']['queen_deaths']
report = {'same_map_seed_other_actions': True,
          'only_changed_actions': {'round56': 'N -> E', 'round57': 'N -> S', 'round58': 'N -> E'},
          'original_observations_equal': True, 'intervention_observations_equal_through_round56': True,
          'original_queen_death': results['recorded']['queen_deaths'],
          'changed_queen_death_before_round60': results['queen_escapes_E_S_E']['queen_deaths'],
          'candidate': str(args.candidate), 'candidate_source_sha256': digest,
          'candidate_fresh_at56_queen_deaths': results.get('candidate_fresh_at56', {}).get('queen_deaths'),
          'cases': {k: {**v, 'frames': [f for f in v['frames'] if f['round'] >= 54]} for k, v in results.items()},
          'scope': 'Official engine causal local escape check, stopped at start of round60. E/S/E suffix hand selected. Optional candidate intervention is a fresh-memory bot controlling Queen from round56 forward on true resulting observations; not full-game, win-rate, or rating proof.'}
(OUT / 'queen-friendly-trap-causal.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
