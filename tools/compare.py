"""Build once, compare in the official sandbox, record exact source hashes."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
from dataclasses import asdict
from importlib.metadata import version
from unswbc import clangtool
from unswbc.run import execute
from unswbc.engine import DEBUG_ALL, DEBUG_LIMITS
from unswbc.engine import EngineModule
from unswbc.sandbox import SandboxBot

# 记录明确的协作事件，避免把有意交付的自撞和导航错误混为一谈。
cooperation_counts = {}
planned_releases = set()
development_counts = {}
previous_turn = {}
worker_peaks = {}
original_ask = SandboxBot.ask
def measured_ask(self, block):
    reply = original_ask(self, block)
    team = next((line.split()[1] for line in self._init.decode().splitlines()
                 if line.startswith('TEAM ')), '?')
    counts = cooperation_counts.setdefault(team, dict(grants=0, releases=0, pickups=0, received_pearls=0))
    raw = block.decode(errors='replace')
    action = reply.decode(errors='replace')
    length_match = re.search(r'^LENGTH (\d+)', raw, re.M)
    units_match = re.search(r'^UNIT_COUNT (\d+)', raw, re.M)
    round_match = re.search(r'^ROUND (\d+)', raw, re.M)
    dev = development_counts.setdefault(team, dict(turns=0, split_actions=0, move_steps=0,
        observed_growth=0, peak_units=0, queen_last_round=0, queen_peak_length=0, queen_attacks=0, large_worker_attacks=0, queen_split_actions=0,
        queen_growth=0, queen_paid_steps=0, worker_peak_length=0, worker_peak_id=-1))
    dev.setdefault('resource_contest_turns', 0)
    dev.setdefault('contact_action_changes', 0)
    contest = re.search(r'\braces=(\d+)', action)
    dev['resource_contest_turns'] += int(contest is not None and int(contest[1]) > 0)
    dev['contact_action_changes'] += int('contact_change=1' in action)
    dev['turns'] += 1
    if units_match: dev['peak_units'] = max(dev['peak_units'], int(units_match[1]))
    if length_match:
        length = int(length_match[1]); identity = (team, self._name)
        if identity in previous_turn:
            growth = max(0, length - previous_turn[identity])
            dev['observed_growth'] += growth
            if int(self._name) <= 1:
                dev['queen_growth'] += growth
        split = re.search(r'^SPLIT (\d+)', action, re.M)
        move = re.search(r'^MOVE ([NESW]+)', action, re.M)
        cost = int(split[1]) if split else max(0, len(move[1]) - (length+3)//4) if move else 0
        previous_turn[identity] = length-cost
        dev['split_actions'] += int(split is not None)
        dev['move_steps'] += len(move[1]) if move else 0
        dev['queen_attacks'] += int('ATTACK_QUEEN' in action)
        dev['large_worker_attacks'] += int('ATTACK_LARGE_WORKER' in action)
        dev['queen_split_actions'] += int(split is not None and int(self._name)<=1)
        if int(self._name) <= 1:
            dev['queen_last_round'] = int(round_match[1]) if round_match else 0
            dev['queen_peak_length'] = max(dev['queen_peak_length'], length)
            dev['queen_paid_steps'] += cost if move else 0
        else:
            peak = worker_peaks.setdefault(team, {})
            peak[int(self._name)] = max(peak.get(int(self._name), 0), length)
            if length > dev['worker_peak_length']:
                dev['worker_peak_length'] = length
                dev['worker_peak_id'] = int(self._name)
    for event, amount in re.findall(r'FEED_(GRANT|RELEASE|PICKUP|RECEIPT) (\d+)', reply.decode(errors='replace')):
        key = dict(GRANT='grants', RELEASE='releases', PICKUP='pickups', RECEIPT='received_pearls')[event]
        counts[key] += int(amount) if event == 'RECEIPT' else 1
        if event == 'RELEASE': planned_releases.add(int(self._name))
    return reply
SandboxBot.ask = measured_ask

# 新引擎直接提供 Queen 长度，不能继续拿最长普通龙代替主分数。
latest_result = {}
original_run = EngineModule.run
def measured_run(self, *args, **kwargs):
    global latest_result
    result = original_run(self, *args, **kwargs)
    latest_result = asdict(result)
    return result
EngineModule.run = measured_run

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', default='bot')
parser.add_argument('--opponent', default='opponents/v1')
parser.add_argument('--maps', nargs='+', default=['arena', 'default', 'portals', 'big_empty', 'stronghold', 'dilemma'])
parser.add_argument('--seeds', nargs='+', type=int, default=[17, 29])
parser.add_argument('--name', default='v2-v1')
parser.add_argument('--replays', action='store_true')
parser.add_argument('--map-dir', default='maps/current')
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
            cooperation_counts.clear()
            planned_releases.clear()
            development_counts.clear()
            previous_turn.clear()
            worker_peaks.clear()
            bots = [candidate, opponent] if side == 'A' else [opponent, candidate]
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                replay = out / f'{map_name}-{seed}-{side}.replay' if args.replays else None
                code = execute(f'{args.map_dir}/{map_name}.map', bots, False, replay, not args.replays,
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
            row['engine_result'] = latest_result.copy()
            row['cooperation'] = {team: counters.copy() for team, counters in cooperation_counts.items()}
            row['development'] = {team: counters.copy() for team, counters in development_counts.items()}
            row['intentional_self_collisions'] = sum(int(dragon) in planned_releases for dragon in
                re.findall(r'bot (\d+) \(team '+side+r'\) died: hit itself', log))
            row['accidental_self_collisions'] = row['self_collisions'] - row['intentional_self_collisions']
            deaths = {int(identity): dict(round=int(round_num), reason=reason.strip())
                      for round_num, identity, reason in re.findall(
                          r'round (\d+): bot (\d+) \(team '+side+r'\) died: ([^\n]+)', log)}
            # Observed peaks include starting and inherited split lengths;
            # a dragon's final action can grow then die before another input.
            row['observed_peak_workers'] = [dict(id=identity, peak_length=length,
                                             death=deaths.get(identity))
                for identity, length in sorted(worker_peaks.get(side, {}).items(),
                    key=lambda item: (-item[1], item[0]))[:5]]
            print(row, flush=True)
report = dict(candidate=args.candidate, opponent=args.opponent,
              engine_version=version('unswbc'), map_dir=args.map_dir,
              candidate_hash=candidate_hash, opponent_hash=opponent_hash, games=rows)
(out / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print({k:sum(r['result']==k for r in rows) for k in ('win','loss','draw','error')})
if any(r['result']=='error' for r in rows):
    raise SystemExit(1)
