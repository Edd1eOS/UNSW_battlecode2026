"""Prepare independent feature ablations without editing the main bot."""
import hashlib
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {
    'full': (1, 1, 1),
    'targets': (1, 0, 0),
    'races': (0, 1, 0),
    'endpoints': (0, 0, 1),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', default='opponents/counterplay-prototype')
    args = parser.parse_args()
    files = sorted(p for p in (ROOT / args.candidate).iterdir() if p.suffix in ('.cpp', '.hpp', '.toml'))
    for name, values in CONFIGS.items():
        data = {p.name: p.read_bytes() for p in files}
        if name != 'full':
            switches = ('COUNTER_TARGETS', 'COUNTER_FOOD_RACE', 'COUNTER_ENDPOINTS')
            data['main.cpp'] = ''.join(f'#define {key} {value}\n' for key, value in zip(switches, values)).encode() + data['main.cpp']
        digest = hashlib.sha256(b''.join(key.encode() + value for key, value in sorted(data.items()))).hexdigest()
        stage = ROOT / 'test-results' / 'counter-variants' / f'{name}-{digest[:12]}'
        stage.mkdir(parents=True, exist_ok=True)
        for key, value in data.items():
            (stage / key).write_bytes(value)
        print(f'{name}: {stage.relative_to(ROOT).as_posix()} {digest}', flush=True)
