"""Reproduce the first portal-planner disagreement on a fixed observation prefix.

This verifies a decision, not a counterfactual game result. All earlier actions
must match the recording; observations stop at the first changed action.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--compiler', default=os.environ.get('CXX', 'g++'))
args = parser.parse_args()
fixture = json.loads((root / 'tests/fixtures/portal-scout-round18.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='battlecode-portal-') as directory:
    binary = Path(directory) / 'bot.exe'
    subprocess.run([args.compiler, '-std=c++20', '-O2', str(root / 'bot/main.cpp'), '-o', str(binary)], check=True)
    result = subprocess.run([str(binary)], input=fixture['input'], text=True,
                            capture_output=True, check=True, timeout=10)
    actions = [line for line in result.stdout.splitlines() if line.startswith(('MOVE ', 'SPLIT '))]
    assert actions[:-1] == fixture['original_actions'][:-1], actions
    assert actions[-1] == 'MOVE W', actions[-1]
    assert 'PORTAL_SCOUT' in result.stdout
    print('Round 18: enters the known portal toward the pearl instead of retreating east.')
