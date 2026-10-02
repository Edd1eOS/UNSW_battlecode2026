"""Capture the exact observations and actions in a reproducible local match."""
import argparse
import json
from pathlib import Path
from unswbc.run import execute
from unswbc.sandbox import SandboxBot

p = argparse.ArgumentParser()
p.add_argument('--map', default='arena')
p.add_argument('--a', default='opponents/starter')
p.add_argument('--b', default='opponents/v2')
p.add_argument('--seed', type=int, default=17)
p.add_argument('--out', default='test-results/v2-trace.json')
p.add_argument('--dragon', type=int, help='Record only this dragon (for example 0 or 1 for a queen)')
a = p.parse_args()
turns = []
original = SandboxBot.ask
def traced(self, block):
    output = original(self, block)
    if a.dragon is None or int(self._name) == a.dragon:
        turns.append(dict(dragon=self._name, init=self._init.decode(),
                          input=block.decode(), output=output.decode()))
    return output
SandboxBot.ask = traced
try:
    execute(f'maps/{a.map}.map', [a.a, a.b], False, None, True, True, seed=a.seed)
finally:
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(turns, indent=2), encoding='utf-8')
