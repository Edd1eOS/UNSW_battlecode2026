"""Meter synthetic possible full-Atlas state; no match or hidden live input.

The test includes setup, an explicit emergency assessment, and actual choose (which
assesses the emergency again). It is deliberately more work than one production
choose and is not a universal worst-case bound or observed historical route.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_cpp import dependencies
from external_panel import source_bundle
from unswbc import clangtool
from unswbc import metering
from unswbc.sandbox import Sandbox


if __name__ == '__main__':
    source = ROOT / 'tests/emergency_v2_history_budget_test.cpp'
    found = {}
    dependencies(source, found)
    digest = hashlib.sha256(b''.join(p.relative_to(ROOT).as_posix().encode() + d for p, d in sorted(found.items()))).hexdigest()
    stage = ROOT / 'test-results/emergency-v2-history-budget-build' / digest[:24]
    for path, data in found.items():
        target = stage / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    wasm = clangtool.build(stage)
    metered = stage / 'history-budget-metered.wasm'
    metered.write_bytes(metering.instrument(Path(wasm).read_bytes()))
    records = []
    for length in (8, 32):
        for portals in (0, 1):
            for identity in (0, 2):
                box = Sandbox(wasm_path=metered, argv=['history-budget', str(length), str(portals), str(identity)],
                              needs_zygote=False, needs_meter=True)
                box.instantiate()
                box.refill(100_000_000)
                code = box.main()
                text = bytes(box.stdout).decode('utf-8', 'replace').strip()
                row = {'length': length, 'portals': portals, 'identity': identity,
                       'exit_code': code, 'cpu_points': box.spent(), 'memory_bytes': box.memory.data_len(),
                       'stdout': text, 'stderr': bytes(box.stderr).decode('utf-8', 'replace'), 'failure': box.failure}
                row['passed'] = code == 0 and not row['stderr'] and row['cpu_points'] < 90_000_000
                if code == 0:
                    row.update(json.loads(text))
                records.append(row)
                print(json.dumps(row), flush=True)
                if not row['passed']:
                    print('Budget gate failure: stop and review', flush=True)
                    break
    report = {'scope': __doc__, 'matches_run': 0, 'bot_executions': 0,
              'synthetic_unit_executions': len(records), 'dependency_sha256': digest,
              'current_candidate_source_sha256': source_bundle(ROOT / 'opponents/generalist-emergency-v2')[0],
              'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'wasm_sha256': hashlib.sha256(Path(wasm).read_bytes()).hexdigest(),
              'metered_wasm_sha256': hashlib.sha256(metered.read_bytes()).hexdigest(),
              'records': records, 'passed': len(records) == 8 and all(r['passed'] for r in records),
              'peak_cpu_points': max(r['cpu_points'] for r in records)}
    out = ROOT / 'test-results/emergency-v2-history-budget.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'peak_cpu_points': report['peak_cpu_points'], 'matches_run': 0}), flush=True)
    if not report['passed']:
        raise SystemExit(1)
