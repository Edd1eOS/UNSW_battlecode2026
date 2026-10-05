"""Run C++ scenario checks with the already installed official judge toolchain.

The compiler's default cache hashes .cpp files only. Stage names below also
hash local headers and defines, so an edited bot cannot reuse a stale test.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re

from unswbc import clangtool
from unswbc.sandbox import Sandbox

clangtool.DRIVER_FLAGS += ['-Wall', '-Wextra', '-pedantic']

ROOT = Path(__file__).resolve().parents[1]


def dependencies(path, found):
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"include outside workspace: {path}")
    if path in found:
        return
    found[path] = path.read_bytes()
    for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', found[path].decode('utf-8'), re.M):
        dependencies(path.parent / include, found)


def check(test, defines, input_data=None):
    source = (ROOT / test).resolve()
    found = {}
    dependencies(source, found)
    prefix = ''.join(f'#define {item.replace("=", " ", 1)}\n' for item in defines).encode()
    found[source] = prefix + found[source]
    digest = hashlib.sha256(b''.join(
        path.relative_to(ROOT).as_posix().encode() + data
        for path, data in sorted(found.items()))).hexdigest()
    stage = ROOT / 'test-results' / 'cpp-checks' / digest[:24]
    for path, data in found.items():
        target = stage / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    wasm = clangtool.build(stage)
    box = Sandbox(wasm_path=wasm, argv=['check'],
                  stdin=io.BytesIO(input_data) if input_data is not None else None,
                  needs_zygote=False, needs_meter=False)
    code = box.run()
    output = (bytes(box.stdout) + bytes(box.stderr)).decode('utf-8', 'replace')
    print(output.strip(), flush=True)
    if code:
        raise SystemExit(f'{test}: exit {code}')
    print(f'PASS {test} ({digest[:12]})', flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tests', nargs='+')
    parser.add_argument('-D', '--define', action='append', default=[])
    parser.add_argument('--input-fixture', help='Workspace JSON fixture with an input protocol string')
    args = parser.parse_args()
    input_data = json.loads((ROOT / args.input_fixture).read_text(encoding='utf-8'))['input'].encode() if args.input_fixture else None
    for test in args.tests:
        check(test, args.define, input_data)
