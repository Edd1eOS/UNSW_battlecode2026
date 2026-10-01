"""Build once, compare in the official sandbox, record exact source hashes."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
from unswbc import clangtool
from unswbc.run import execute
from unswbc.engine import DEBUG_ALL, DEBUG_LIMITS

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', default='bot')
parser.add_argument('--opponent', default='opponents/v1')
parser.add_argument('--maps', nargs='+', default=['arena', 'default', 'portals', 'big_empty', 'stronghold', 'dilemma'])
parser.add_argument('--seeds', nargs='+', type=int, default=[17, 29])
parser.add_argument('--name', default='v2-v1')
parser.add_argument('--replays', action='store_true')
args = parser.parse_args()
out = ROOT / 'test-results' / args.name
out.mkdir(parents=True, exist_ok=True)

def build(project):
    directory = ROOT / project
    files = sorted(p for p in directory.iterdir() if p.suffix in ('.cpp', '.hpp', '.toml'))
    digest = hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in files)).hexdigest()
    # Include header changes in the cache key; toolkit 1.2.2 hashes .cpp only.
    stage = ROOT / 'test-results' / 'build' / digest[:16]
    stage.mkdir(parents=True, exist_ok=True)
    for p in files:
        (stage / p.name).write_bytes(p.read_bytes())
    return str(clangtool.build(stage)), digest

candidate, candidate_hash = build(args.candidate)
opponent, opponent_hash = build(args.opponent)
rows = []
for map_name in args.maps:
    for seed in args.seeds:
        for side in ('A', 'B'):
            bots = [candidate, opponent] if side == 'A' else [opponent, candidate]
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                replay = out / f'{map_name}-{seed}-{side}.replay' if args.replays else None
                code = execute(f'maps/{map_name}.map', bots, False, replay, not args.replays,
                               True, DEBUG_ALL | DEBUG_LIMITS, seed)
            log = buffer.getvalue()
            (out / f'{map_name}-{seed}-{side}.log').write_text(log, encoding='utf-8')
            winner = re.search(r'team ([AB]) wins after (\d+) rounds', log)
            result = ('win' if winner[1] == side else 'loss') if winner else (
                'draw' if re.search(r'draw after \d+ rounds', log) else 'error')
            if code or re.search(r'no valid action|sandbox error|exhaust|timed out', log):
                result = 'error'
            peak = re.search(r'team '+side+r' points per turn:.*?max ([\d.]+)([KM]?)', log)
            points = float(peak[1]) * {'':1,'K':1000,'M':1000000}[peak[2]] if peak else None
            row = dict(map=map_name, seed=seed, side=side, result=result, peak_points=points,
                       self_collisions=len(re.findall(r'team '+side+r'\) died: hit itself', log)))
            rows.append(row)
            print(row, flush=True)
report = dict(candidate=args.candidate, opponent=args.opponent,
              candidate_hash=candidate_hash, opponent_hash=opponent_hash, games=rows)
(out / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print({k:sum(r['result']==k for r in rows) for k in ('win','loss','draw','error')})
if any(r['result']=='error' for r in rows):
    raise SystemExit(1)
