"""Official metered interface checks, including complete joint-body fixtures.

No match is played. Existing observations remain isolated exactly as in the
frozen common verifier; the additional frame generator is independently hashed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_candidate as verifier


def added_fixtures():
    spec = importlib.util.spec_from_file_location('investment_frames', ROOT / 'external-benchmarks/smoke_external.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DIM = 64
    body6 = [(20, 20), (19, 20), (18, 20), (18, 21), (19, 21), (20, 21)]
    body8 = body6 + [(20, 22), (19, 22)]
    cases = []
    for length, body in ((6, body6), (8, body8)):
        packet = module.frame(2, body, round_num=100, units=10,
                              pearls=((21, 21), (22, 21), (23, 21)))
        # Symmetric ordinary head-E edge becomes kelp in the protocol matrix.
        lines = packet.splitlines()
        vertical = lines[-4].split()
        vertical[4] = 'w'
        lines[-4] = ' '.join(vertical)
        case = {'name': f'complete-L{length}-tail-resource-joint-investment',
                'init': 'ID 2\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n',
                'turns': ['\n'.join(lines) + '\n'], 'constructed': True}
        if length == 6:
            case['expected_actions'] = ['SPLIT 2']
        cases.append(case)
    pearls = tuple((x, y) for y in range(17, 24) for x in range(17, 24) if (x, y) not in body8)
    cases.append({'name': 'complete-L8-dense-visible-food-joint-budget',
                  'init': 'ID 2\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n',
                  'turns': [module.frame(2, body8, round_num=100, units=10, pearls=pearls)],
                  'constructed': True})
    return cases


if __name__ == '__main__':
    original = verifier.fixtures
    verifier.fixtures = lambda: original() + added_fixtures()
    out = ROOT / 'test-results/investment-v1-final-protocol.json'
    verifier.run(ROOT / 'opponents/generalist-investment-v1', out)
    report = json.loads(out.read_text(encoding='utf-8'))
    report['additional_fixture_driver_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['additional_fixture_scope'] = 'Complete parent/child investment and dense-food budget; no match or strength result'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
