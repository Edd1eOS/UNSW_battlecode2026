"""Check the decision at a real v2 losing position, using recorded observations.

The prefix reconstructs memory. It is a fixed input regression, not a live match:
earlier actions emitted by the candidate do not alter the recorded observations.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='battlecode-regression-') as temp:
    binary = Path(temp) / 'bot.exe'
    subprocess.run(['g++', '-std=c++20', '-O2', str(ROOT / 'bot/main.cpp'), '-o', str(binary)], check=True)
    for fixture, expected in [('arena-round31.in', 'MOVE E'),
                              # v2.2 preserves 23 cells in the reversing child, rather than halving 25.
                              ('stronghold-trapped.in', 'SPLIT 23')]:
        data = (ROOT / 'tests/fixtures' / fixture).read_text(encoding='utf-8')
        result = subprocess.run([str(binary)], input=data,
            text=True, capture_output=True, check=True, timeout=10)
        actions = [line for line in result.stdout.splitlines() if line.startswith(('MOVE ', 'SPLIT '))]
        assert len(actions) == sum(line.startswith('ROUND ') for line in data.splitlines())
        assert actions[-1] == expected, (fixture, actions[-1])
        print(f'{fixture}: {expected}')
