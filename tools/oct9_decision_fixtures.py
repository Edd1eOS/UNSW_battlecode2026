"""Small decision sanity checks, not local strength selection."""
import argparse
import importlib.util
import json
import re
from pathlib import Path

from unswbc.sandbox import SandboxBot, WasmPool
from verify_candidate import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/oct9-aggressive'


def fixtures():
    spec = importlib.util.spec_from_file_location('frame_maker', ROOT / 'external-benchmarks/smoke_external.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    body = [(5, 5), (4, 5), (3, 5)]
    cases = []

    def add(name, who, chain, expected, reason, **kwargs):
        cases.append({'name': name, 'init': f'ID {who}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',
                      'turns': [mod.frame(who, chain, **kwargs)], 'expected_actions': expected,
                      'reason': reason})

    for who in (0, 2):
        add(f'front_pearl_id{who}', who, body, ['MOVE E'],
            'Uncontested adjacent food in open terrain: take it with one free step and grow from3to4.', pearls=((6, 5),))
        add(f'two_steps_food_preserve_growth_id{who}', who, body, ['MOVE E'],
            'One pearl two cells away, length3: paid EE consumes the entire food gain; free E keeps growth possible.', pearls=((7, 5),))

    add('queen_trade_two_steps', 2, body, ['MOVE EE'],
        'Worker can directly trade for visible enemy Queen. The paid step has decisive tactical value.', units=3,
        enemies=((1, [(7, 5), (8, 5)]),))
    corridor = [((5, 5), (6, 5)), ((6, 5), (7, 5)), ((7, 5), (8, 5))]
    add('tail_sealed_parent_safe_no_breeding', 0, body + [(2, 5)], ['MOVE E'],
        'Parent can leave forward; any split creates a child whose head is trapped at old tail by kelp and own neck.',
        edges=corridor, units=2)
    add('both_ends_sealed_diagnostic', 0, body + [(2, 5)], [],
        'All free exits at both heads blocked; diagnosis only. A last-resort split may be legitimate, so no prescriptive pass/fail.',
        edges=[], units=2)
    return cases


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=Path)
    p.add_argument('--out', type=Path, default=OUT / 'decision-fixtures-results.json')
    a = p.parse_args()
    cases = fixtures()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'decision-fixtures.json').write_text(json.dumps(cases, indent=2))
    if a.candidate is None:
        print(f'Wrote {len(cases)} decision fixtures')
        return
    wasm, digest = build(a.candidate)
    pool = WasmPool([str(wasm)], key='oct9-decision-' + digest[:20])
    result = {'candidate': str(a.candidate), 'source_sha256': digest, 'matches_run': 0,
              'scope': 'Decision checks only, not a local strength gate.', 'cases': []}
    try:
        for case in cases:
            who = re.search(r'^ID (\d+)', case['init'])[1]
            bot = SandboxBot(pool, init=case['init'].encode(), name=who)
            try:
                output = bot.ask(case['turns'][0].encode()).decode()
                actions = re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$', output, re.M)
                result['cases'].append({**case, 'output': output, 'actions': actions,
                                        'expected_matched': actions == case['expected_actions'] if case['expected_actions'] else None,
                                        'cpu_points': bot.live[0], 'error': bot.error})
            finally:
                bot.stop()
    finally:
        pool.close()
    a.out.write_text(json.dumps(result, indent=2))
    print(json.dumps([{k: c[k] for k in ('name', 'actions', 'expected_matched', 'error')} for c in result['cases']], indent=2))


if __name__ == '__main__':
    main()
