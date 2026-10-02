"""Exercise the real Queen -> sonar -> donor death -> pickup sequence in the official engine."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
from unswbc import clangtool
from unswbc.run import execute
from unswbc.sandbox import SandboxBot

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'test-results' / 'cooperation-engine'
out.mkdir(parents=True, exist_ok=True)
files = sorted(p for p in (ROOT / 'bot').iterdir() if p.suffix in ('.cpp', '.hpp', '.toml'))
digest = hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in files)).hexdigest()
stage = ROOT / 'test-results' / 'build' / digest[:16]
stage.mkdir(parents=True, exist_ok=True)
for p in files:
    (stage / p.name).write_bytes(p.read_bytes())
binary = str(clangtool.build(stage))
queens = [(5,5),(4,5),(4,4),(4,3),(5,3),(6,3),(7,3),(7,4),(7,5)]
donor = [(6,4),(6,5),(6,6),(7,6)]
bodies = [queens, [(26,26),(25,26)], donor, [(26,22),(25,22)],
          [(20,20),(19,20)], [(22,26),(21,26)], [(24,20),(23,20)], [(22,22),(21,22)]]
lines = ['MAP 32 32', 'MAP_NAME Feeding integration', 'TILE_COUNT 0', 'EDGE_COUNT 0', 'DRAGON_COUNT 8']
for i, body in enumerate(bodies):
    lines.append(f'DRAGON {i%2} {len(body)} ' + ' '.join(f'{x} {y}' for x,y in body))
lines.append('END')
map_path = out / 'feeding.map'
map_path.write_text('\n'.join(lines)+'\n')
turns = []
original = SandboxBot.ask
def capture(self, block):
    reply = original(self, block)
    text = block.decode()
    round_num = int(re.search(r'^ROUND (\d+)', text)[1])
    if self._name in ('0','2') and round_num <= 2:
        turns.append(dict(dragon=int(self._name), round=round_num,
                          length=int(re.search(r'^LENGTH (\d+)', text, re.M)[1]),
                          input=text, output=reply.decode()))
    return reply
SandboxBot.ask = capture
log = io.StringIO()
try:
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        code = execute(str(map_path), [binary, binary], False, out/'feeding.replay', False, True, seed=71)
finally:
    SandboxBot.ask = original
(out/'engine.log').write_text(log.getvalue(), encoding='utf-8')
(out/'turns.json').write_text(json.dumps(turns, indent=2), encoding='utf-8')
assert code == 0, log.getvalue()[-2000:]
q0 = next(t for t in turns if t['dragon']==0 and t['round']==0)
d0 = next(t for t in turns if t['dragon']==2 and t['round']==0)
q1 = next(t for t in turns if t['dragon']==0 and t['round']==1)
q2 = next(t for t in turns if t['dragon']==0 and t['round']==2)
assert 'FEED_GRANT 2' in q0['output'], turns
assert 'FEED_RELEASE 2' in d0['output'], turns
assert 'FEED_PICKUP 2' in q1['output'], turns
assert q2['length']==11 and 'FEED_RECEIPT 2' in q2['output'], turns
assert re.search(r'round 0: bot 2 \(team A\) died: hit itself', log.getvalue()), log.getvalue()[:2000]
assert not re.search(r'no valid action|sandbox error|exhaust|timed out', log.getvalue())
report = dict(source_hash=digest, seed=71, queen_start=9, queen_after=11, donor_length=4,
              turns=[{key:value for key,value in turn.items() if key!='input'} for turn in turns])
(out/'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('Official sandbox verified: Queen grants -> donor releases 2 pearls -> Queen grows 9 to 11.')
print(json.dumps(report, indent=2))
