"""Change only the doomed Queen's round133 action in the official engine."""
import gzip
import json
import re
from pathlib import Path
from unswbc.engine import EngineModule
from audit_online import load_replay

OUT = Path('test-results/oct9-final-sprint')
SOURCE = OUT / 'online-v35-bhole/M1524205.replay'
d = load_replay(SOURCE, node_path='D:/node/node.exe')
ref = json.loads(gzip.decompress((OUT / 'verified-queen-threats/M1524205-observations.json.gz').read_bytes()))
actions = {}
rnd = -1
for e in d['events']:
    if e['type'] == 'roundStart': rnd = e['round']
    elif e['type'] == 'dragonAction': actions[(rnd, e['id'])] = e['action']
name = next(x for x in d['map'].splitlines() if x.startswith('MAP_NAME '))
maps = [p for p in Path('maps/current').glob('*.map') if name in p.read_text().splitlines()]
assert len(maps) == 1
tile_lines = {tuple(s.split()[1:3]): s for s in maps[0].read_text().splitlines() if s.startswith('TILE ')}
map_text = '\n'.join(tile_lines.get(tuple(s.split()[1:3]), s) if s.startswith('TILE ') else s for s in d['map'].splitlines()) + '\n'


class StopProbe(Exception):
    pass


cases = {}
for label in ('recorded_split2', 'only_round133_portal_N'):
    frames = []
    deaths = []
    seen_134 = False

    def reply(who, block):
        global seen_134
        r = int(re.search(rb'^ROUND (\d+)', block, re.M)[1])
        if who == 0:
            frames.append({'round': r, 'input': block.decode()})
        if r >= 134:
            if who == 0: seen_134 = True
            raise StopProbe()
        a = actions[(r, who)]
        cmd = 'MOVE ' + ''.join(a['steps']) if a['kind'] == 'move' else (
            'SPLIT ' + str(a['childSegmentCount']) if a['kind'] == 'split' else '')
        if label != 'recorded_split2' and who == 0 and r == 133:
            cmd = 'MOVE N'
        if who == 0:
            frames[-1]['action'] = cmd
        return (cmd + '\nPROTOCOL 3\nENDTURN\n').encode()

    try:
        EngineModule().run(map_text.encode(), reply, seed=int(d['seed']),
                           on_death=lambda i, r, why: deaths.append({'id': i, 'round': r, 'reason': why}),
                           on_notice=lambda _: None)
    except StopProbe:
        pass
    cases[label] = {'queen_deaths': [e for e in deaths if e['id'] == 0],
                    'enemy32_deaths': [e for e in deaths if e['id'] == 32],
                    'queen_observation_at134': seen_134, 'frames': frames}

assert all(a['input'] == b['input'] for a, b in zip(cases['recorded_split2']['frames'], ref['queens']['0']['frames']))
assert all(a['input'] == b['input'] for a, b in zip(cases['recorded_split2']['frames'], cases['only_round133_portal_N']['frames']))
assert cases['recorded_split2']['queen_deaths'] == [{'id': 0, 'round': 133, 'reason': 'H'}]
assert not cases['only_round133_portal_N']['queen_deaths']
assert cases['only_round133_portal_N']['queen_observation_at134']
report = {'source': str(SOURCE), 'source_sha256': d['input_sha256'],
          'only_changed_action': {'id': 0, 'round': 133, 'before': 'SPLIT 2', 'after': 'MOVE N'},
          'same_map_seed_other_recorded_actions': True, 'observations_identical_through_intervention': True,
          'cases': {k: {**v, 'frames': [f for f in v['frames'] if f['round'] >= 131]} for k, v in cases.items()},
          'scope': 'Official-engine local causal intervention, stopped before any round134 action. Queen now survives and gets a round134 observation; enemy32 hits her remaining body and dies with reasonO. Original replay has no Queen actions after her round133 death, so we do not invent a new continuation to claim round136 or full-match survival.'}
(OUT / 'default-portal-causal.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'frames'} for k, v in cases.items()}, indent=2))
