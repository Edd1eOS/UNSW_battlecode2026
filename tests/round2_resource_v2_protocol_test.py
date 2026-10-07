"""Official protocol and current-view crowding fixtures; no matches."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_candidate as verifier
from external_panel import source_bundle


def added_fixtures():
    spec = importlib.util.spec_from_file_location('allocation_frames', ROOT / 'external-benchmarks/smoke_external.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DIM = 64
    heads = [(18, 17), (21, 17), (23, 17), (18, 23), (21, 23), (23, 23), (18, 19)]
    result = []
    for length in (3, 32):
        for identity in (0, 2):
            body = [((20 - i) % 64, 20) for i in range(length)]
            peers = [(k + 2 if identity == 0 else (0 if k == 0 else k + 3), [p, (p[0] - 1, p[1])])
                     for k, p in enumerate(heads)]
            occupied = set(body) | {p for _, chain in peers for p in chain}
            pearls = [(x, y) for y in range(17, 24) for x in range(17, 24) if (x, y) not in occupied][:16]
            packet = module.frame(identity, body, round_num=200, units=10, pearls=pearls, enemies=peers)
            packet = '\n'.join('A ' + line[2:] if line.startswith('B ') else line for line in packet.splitlines()) + '\n'
            result.append({'name': f'allocation-L{length}-id{identity}-eight-heads-visible-food',
                           'init': f'ID {identity}\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n',
                           'turns': [packet], 'constructed': True})
    return result


if __name__ == '__main__':
    original = verifier.fixtures
    verifier.fixtures = lambda: original() + added_fixtures()
    candidate = ROOT / 'opponents/generalist-resource-priority-v2'
    out = ROOT / 'test-results/round2-resource-v2-protocol.json'
    verifier.run(candidate, out)
    report = json.loads(out.read_text(encoding='utf-8'))
    report['protocol_source_content_sha256'] = report['source_bundle_sha256']
    report['source_bundle_sha256'] = source_bundle(candidate)[0]
    report['additional_fixture_driver_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['additional_fixture_scope'] = 'Legal current 7x7 eight-head projection; no private Atlas supplied; no match'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
