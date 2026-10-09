"""Probe actual cooperation failure states with honest fresh-memory isolation."""
import argparse
import json
import re
from pathlib import Path

from unswbc.sandbox import SandboxBot, WasmPool
from verify_candidate import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/oct9-aggressive'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--fixtures', type=Path, default=OUT / 'cooperation-actual-fixtures.json')
    a = p.parse_args()
    fixture = json.loads(a.fixtures.read_text())
    wasm, digest = build(a.candidate)
    pool = WasmPool([str(wasm)], key='cooperation-probe-' + digest[:20])
    result = {'candidate': str(a.candidate), 'source_sha256': digest, 'source_replay': fixture['source'],
              'source_physical_events_verified': fixture['physical_events_equal'],
              'scope': 'Fresh-process isolated actual observations. No invented continuous memory and no counterfactual match result.',
              'rows': []}
    try:
        for who, unit in fixture['units'].items():
            for frame in unit['frames']:
                bot = SandboxBot(pool, init=unit['init'].encode(), name=who)
                try:
                    output = bot.ask(frame['input'].encode()).decode()
                    actions = re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$', output, re.M)
                    result['rows'].append({'id': int(who), 'round': frame['round'],
                                           'recorded_action': frame['action'], 'output': output, 'actions': actions,
                                           'cpu_points': bot.live[0], 'error': bot.error})
                finally:
                    bot.stop()
    finally:
        pool.close()
    a.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
