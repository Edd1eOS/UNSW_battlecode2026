"""Bounded collector for the second Oct7 round; no matches or promotion.

The original two-opponent and KGTS collectors remain unchanged. References from
the preceding round are identified separately and excluded from new-match counts.
"""
import datetime
import hashlib
import json
from pathlib import Path
import oct7_build_manifest as collector
import oct7_external_panel as primary
import oct7_kgts_panel as kgts

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('evidence', 'topology', 'topology-v2', 'resource', 'resource-v2')


def collect():
    collector.panel_driver = primary
    references = [collector.collect_panel(Path('test-results/oct7-v5-panel'))]
    panels = [collector.collect_panel(Path(f'test-results/round2-{n}-panel')) for n in NAMES]
    collector.panel_driver = kgts
    references.append(collector.collect_panel(Path('test-results/oct7-v5-kgts-panel')))
    panels += [collector.collect_panel(Path(f'test-results/round2-{n}-kgts-panel')) for n in NAMES if n != 'evidence']
    collector.panel_driver = primary
    reports = []
    for name in NAMES:
        for suffix in ('compare', 'kgts-compare'):
            p = Path(f'test-results/round2-{name}-{suffix}.json')
            if not p.exists():
                if name == 'evidence' and suffix == 'kgts-compare':
                    continue
                raise ValueError(f'Missing expected completed report: {p}')
            r = json.loads(p.read_text(encoding='utf-8'))
            if r['actual_scope'] != 'complete' or any(r['denominators'][k] for k in ('unmatched', 'duplicate_key_conflicts')):
                raise ValueError(f'Incomplete paired report: {p}')
            reports.append({'binding': collector.binding(p), 'denominators': r['denominators'],
                            'summary': r['summary']['all'], 'dependencies': r['analyzer_dependencies_sha256']})
    evidence = {Path('.gitattributes'), Path('README.md'), Path(__file__).relative_to(ROOT)}
    for pattern in ('docs/oct7-round2-*', 'tools/round2_*.py', 'tests/round2_*',
                    'test-results/round2-*.json', 'test-results/round2-*.log',
                    'test-results/round2-topology-preflight-initial/*',
                    'test-results/round2-topology-maze-*-reader/proof.json',
                    'test-results/round2-topology-maze-*-reader/input.txt',
                    'test-results/round2-topology-maze-*-reader/output.log',
                    'test-results/round2-topology-maze-*-reader/diagnostic/*.hpp',
                    'test-results/round2-topology-maze-*-reader/diagnostic/*.cpp'):
        evidence.update(p.relative_to(ROOT) for p in ROOT.glob(pattern) if p.is_file())
    out = Path('docs/oct7-round2-evidence-manifest.json')
    evidence.discard(out)
    checks = json.loads((ROOT / 'test-results/round2-final-cpp-checks.json').read_text(encoding='utf-8'))
    if not checks['passed']:
        raise ValueError('Final C++ contracts did not pass')
    retained = json.loads((ROOT / 'test-results/round2-retained-cpp-checks.json').read_text(encoding='utf-8'))
    if (not retained['passed'] or len(retained['checks']) != len(checks['checks'])
            or retained['source_record_sha256'] != collector.binding('test-results/round2-final-cpp-checks.json')['sha256']):
        raise ValueError('Retained C++ executions do not match the final artifact record')
    for check, execution in zip(checks['checks'], retained['checks']):
        wasm = ROOT / check['stage'] / 'executed.wasm'
        if (execution['test'] != check['test'] or execution['exit_code'] != 0
                or hashlib.sha256(wasm.read_bytes()).hexdigest() != execution['wasm_sha256']
                or execution['wasm_sha256'] != check['wasm_files']['executed.wasm']):
            raise ValueError('Retained C++ artifact identity or execution failed')
    for panel in panels:
        if not panel['actual_status']['phases']['discovery']['complete']:
            raise ValueError('Incomplete new discovery panel')
        for raw in panel['candidate']['source_files'].values():
            # candidate_record() already verified every frozen source file.
            if not raw['sha256']:
                raise ValueError('Missing source digest')
    protocols = []
    for name in NAMES:
        p = Path(f'test-results/round2-{name}-protocol.json')
        r = json.loads(p.read_text(encoding='utf-8'))
        frozen = json.loads(Path(f'test-results/round2-{name}-panel/candidate/freeze.json').read_text(encoding='utf-8'))
        if not r['passed'] or r['wasm_sha256'] != frozen['wasm_sha256']:
            raise ValueError('Protocol output is not the frozen production WASM')
        protocols.append({'name': name, 'binding': collector.binding(p), 'production_wasm_sha256': r['wasm_sha256'],
                          'canonical_source_sha256': frozen['source_bundle_sha256'], 'peak_sampled_points': r['max_measured_cpu_points']})
    record = {'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'base_commit': '556a0551bb07a1a398b038b7d03610c4842669c2',
              'scope': __doc__, 'new_completed_matches': sum(len(p['result_bindings']) for p in panels),
              'old_reference_matches_not_new': sum(len(p['result_bindings']) for p in references),
              'new_panels': panels, 'old_references': references, 'reports': reports, 'protocol_bindings': protocols,
              'other_evidence': [collector.binding(p) for p in sorted(evidence)],
              'limits': ['Repeated maps/opponents and candidate arms are correlated; do not pool win rates.',
                         'Frozen local external references do not establish mature ladder strength.',
                         'Protocol and synthetic correctness executions are not games.',
                         'This manifest verifies local bytes and schedule identities, not GitHub publication or platform activation.']}
    (ROOT / out).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'new_matches': record['new_completed_matches'], 'old_reference_matches': record['old_reference_matches_not_new'],
                      'panels': len(panels), 'evidence_files': len(evidence), 'manifest': collector.binding(out)}))


if __name__ == '__main__':
    collect()
