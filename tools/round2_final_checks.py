"""Capture final new C++ contracts and verify their executed dependencies.

Synthetic history-budget entrypoints use their separate metered drivers, not
this argument-free correctness runner. No matches are started.
"""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import sys
import shutil
import check_cpp

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-log',action='store_true',help='Reindex an already successful, hash-verified execution log')
    args=parser.parse_args()
    tests = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'tests').glob('round2_*test.cpp')
                   if 'history_budget' not in p.name)
    command = [sys.executable, 'tools/check_cpp.py', *tests]
    log = ROOT / 'test-results/round2-final-cpp-checks.log'
    if args.reuse_log:
        prior=json.loads((ROOT/'test-results/round2-final-cpp-checks.json').read_text(encoding='utf-8'))
        assert prior['command']==command and prior['exit_code']==0 and prior['log_sha256']==digest(log)
        assert all(digest(ROOT/r['test'])==r['source_sha256'] for r in prior['checks'])
        code=prior['exit_code']
    else:
        with log.open('wb') as stream:
            result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        code=result.returncode
    text = log.read_text(encoding='utf-8')
    rows = []
    for test in tests:
        found = {}
        check_cpp.dependencies(ROOT / test, found)
        sha = hashlib.sha256(b''.join(p.relative_to(ROOT).as_posix().encode() + d for p, d in sorted(found.items()))).hexdigest()
        stage = ROOT / 'test-results/cpp-checks' / sha[:24]
        # Official clang returns its cache path, not a WASM inside the stage.
        # Re-resolve that content-bound cache and retain the executed artifact.
        wasm=Path(check_cpp.clangtool.build(stage))
        retained=stage/'executed.wasm'
        shutil.copyfile(wasm,retained)
        rows.append({'test': test, 'source_sha256': digest(ROOT / test), 'dependency_sha256': sha,
                     'stage': stage.relative_to(ROOT).as_posix(),
                     'pass_line_found': f'PASS {test} ({sha[:12]})' in text,
                     'wasm_files': {'executed.wasm': digest(retained)}})
    passed = code == 0 and all(r['pass_line_found'] and r['wasm_files'] for r in rows)
    report = {'matches_run': 0, 'command': command, 'exit_code': code, 'passed': passed,
              'reindexed_existing_successful_log': args.reuse_log,
              'driver_sha256': digest(Path(__file__)), 'compiler_driver_sha256': digest(Path(check_cpp.__file__)),
              'log_sha256': digest(log), 'checks': rows}
    (ROOT / 'test-results/round2-final-cpp-checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(rows), 'passed': passed, 'log': str(log)}))
    if not passed:
        print(text[-4000:])
        raise SystemExit(1)
