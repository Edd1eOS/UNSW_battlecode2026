"""Reproduce the first portal-planner disagreement on a fixed observation prefix.

Default: reconstruct observed map memory and verify the current portal decision at
a fixed snapshot. --historical also checks the unchanged action prefix of v27.
Neither mode claims a counterfactual game result.
"""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import sys

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--compiler', default=os.environ.get('CXX', 'g++'))
parser.add_argument('--historical', action='store_true', help='Verify the original v27 decision and unchanged action prefix')
parser.add_argument('--official', action='store_true', help='Use the installed official judge compiler and WASM runtime')
args = parser.parse_args()
fixture = json.loads((root / 'tests/fixtures/portal-scout-round18.json').read_text(encoding='utf-8'))
if args.official or not shutil.which(args.compiler):
    sys.path.insert(0, str(root / 'tools'))
    from check_cpp import check
    source = 'opponents/v27-portal-scout/main.cpp' if args.historical else 'tests/portal_snapshot_test.cpp'
    output = check(source, [], fixture['input'].encode())
    if args.historical:
        actions = [line for line in output.splitlines() if line.startswith(('MOVE ', 'SPLIT '))]
        assert actions[:-1] == fixture['original_actions'][:-1], actions
        assert actions[-1] == 'MOVE W', actions[-1]
        assert 'PORTAL_SCOUT' in output
        print('Round 18: known portal selected; historical action prefix unchanged.')
    raise SystemExit(0)
with tempfile.TemporaryDirectory(prefix='battlecode-portal-') as directory:
    binary = Path(directory) / 'bot.exe'
    subprocess.run([args.compiler, '-std=c++20', '-O2', str(root / ('opponents/v27-portal-scout/main.cpp' if args.historical else 'tests/portal_snapshot_test.cpp')), '-o', str(binary)], check=True)
    result = subprocess.run([str(binary)], input=fixture['input'], text=True,
                            capture_output=True, check=True, timeout=10)
    if not args.historical:
        print(result.stdout.strip())
        raise SystemExit(0)
    actions = [line for line in result.stdout.splitlines() if line.startswith(('MOVE ', 'SPLIT '))]
    assert actions[:-1] == fixture['original_actions'][:-1], actions
    assert actions[-1] == 'MOVE W', actions[-1]
    assert 'PORTAL_SCOUT' in result.stdout
    print('Round 18: enters the known portal toward the pearl instead of retreating east.')
