"""Meter candidate protocol fixtures without playing another bot.

Recorded inputs check interface compatibility, not counterfactual match wins.
Constructed 64x64 inputs exercise large maps, partial bodies and contact load.
No upstream process or self-match is started.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import re

from unswbc import clangtool
from unswbc.sandbox import SandboxBot, WasmPool

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    spec = importlib.util.spec_from_file_location("local_protocol_frames", ROOT / "external-benchmarks/smoke_external.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DIM = 64
    # Supply a real complete chain to the packet builder; it filters out parts
    # beyond the local window. A truncated three-part declaration in an open
    # window would omit the still-visible fourth segment of a long body.
    long_body = ([(x, 20) for x in range(20, -1, -1)]
                 + [(0, y) for y in range(19, -1, -1)]
                 + [(x, 0) for x in range(1, 24)])
    assert len(long_body) == 64 and len(set(long_body)) == 64
    cases = []
    for identity in (0, 2):
        for length in (3, 16, 64):
            body = long_body[:length]
            turns = [module.frame(identity, body, round_num=100, units=64,
                                  pearls=((21, 20), (20, 18), (22, 21)))]
            cases.append({"name": f"64map-id{identity}-length{length}-single-observation",
                          "init": f"ID {identity}\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n", "turns": turns,
                          "constructed": True})
    # Length two and a wall-bounded four-cell ring force exactly one free step
    # each turn. These successive packets agree with the expected actions.
    ring = [(20, 20), (21, 20), (21, 21), (20, 21)]
    edges = list(zip(ring, ring[1:] + ring[:1]))
    turns = [module.frame(0, [ring[i], ring[(i - 1) % 4]], round_num=100+i,
                          units=64, edges=edges, protocol=2 if i == 0 else 3,
                          messages=() if i == 0 else (18446744073709551615,))
             for i in range(4)]
    cases.append({"name": "64map-forced-ring-protocol2then3",
                  "init": "ID 0\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                  "turns": turns, "constructed": True,
                  "expected_actions": ["MOVE E", "MOVE S", "MOVE W", "MOVE N"]})
    # A newly split worker can start with inherited protocol 3.
    cases.append({"name": "64map-fresh-worker-inherits-protocol3",
                  "init": "ID 8\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                  "turns": [module.frame(8, long_body[:16], round_num=100, units=2,
                                        protocol=3, messages=(18446744073709551615,))],
                  "constructed": True})
    enemy_heads = [(21, 19), (22, 21), (20, 22), (19, 18), (17, 22), (23, 18)]
    enemies = tuple((5 + 2 * i, [p, (p[0], p[1] - 1)]) for i, p in enumerate(enemy_heads))
    for identity in (0, 2):
        cases.append({"name": f"64map-id{identity}-multiple-visible-heads",
                      "init": f"ID {identity}\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                      "turns": [module.frame(identity, long_body[:32], round_num=200, units=64,
                                             enemies=enemies)], "constructed": True})
    # Old recordings are isolated observation regressions. Each starts a fresh
    # process: replaying the next historical packet after a different candidate
    # action would create a counterfactual body/position history.
    for name in ("portal-self-body-round107.json", "portal-scout-round18.json"):
        saved = json.loads((ROOT / "tests/fixtures" / name).read_text(encoding="utf-8"))
        raw = saved["input"]
        split = raw.index("ROUND ")
        starts = [match.start() for match in re.finditer(r"^ROUND ", raw, re.M)] + [len(raw)]
        for index, (a, b) in enumerate(zip(starts, starts[1:])):
            cases.append({"name": f"{name}-isolated-observation-{index + 1}", "init": raw[:split],
                          "turns": [raw[a:b]], "constructed": False,
                          "source": saved.get("source", "recorded observation")})
    return cases


def build(candidate: Path):
    source = {p.relative_to(candidate).as_posix(): p.read_bytes()
              for p in candidate.rglob("*") if p.is_file() and p.suffix in (".cpp", ".hpp", ".h", ".toml")}
    if not source or "main.cpp" not in source:
        raise ValueError("Candidate needs source files and main.cpp")
    digest = hashlib.sha256(b"".join(k.encode() + v for k, v in sorted(source.items()))).hexdigest()
    stage = ROOT / "test-results/candidate-protocol-build" / digest
    for name, data in source.items():
        destination = stage / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return clangtool.build(stage), digest


def run(candidate: Path, out: Path):
    wasm, digest = build(candidate)
    pool = WasmPool([str(wasm)], key=f"candidate-protocol-{digest[:24]}")
    report = {"candidate": str(candidate.resolve()), "source_bundle_sha256": digest,
              "wasm_sha256": hashlib.sha256(Path(wasm).read_bytes()).hexdigest(),
              "unswbc_version": importlib.metadata.version("unswbc"),
              "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "matches_run": 0, "fixtures": [], "cpu_limit_for_margin": 90_000_000,
              "scope": "Protocol and measured fixture runtime only; no strength result or universal worst-case bound"}
    try:
        for case in fixtures():
            name = re.search(r"^ID (\d+)", case["init"]).group(1)
            bot = SandboxBot(pool, init=case["init"].encode(), name=name)
            rows = []
            try:
                for index, raw in enumerate(case["turns"]):
                    output = bot.ask(raw.encode()).decode("utf-8", "replace")
                    actions = re.findall(r"^(?:MOVE [NESW]+|SPLIT \d+)$", output, re.M)
                    stderr = bot.take_stderr().decode("utf-8", "replace")
                    points, memory = bot.live
                    rows.append({"round": int(re.search(r"^ROUND (\d+)", raw, re.M).group(1)),
                                 "input_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                                 "output": output, "error": bot.error, "stderr": stderr,
                                 "cpu_points": points, "memory_bytes": memory,
                                 "passed": bot.error is None and not stderr and bot._framer.done
                                           and len(actions) == 1 and points < 90_000_000
                                           and ("expected_actions" not in case
                                                or actions == [case["expected_actions"][index]])})
                    if bot.error or not rows[-1]["passed"]:
                        break
            finally:
                bot.stop()
            report["fixtures"].append({"name": case["name"], "constructed": case["constructed"],
                                        "turns": rows, "all_turns_received": len(rows) == len(case["turns"])})
    finally:
        pool.close()
    report["passed"] = all(c["all_turns_received"] and all(t["passed"] for t in c["turns"]) for c in report["fixtures"])
    report["max_measured_cpu_points"] = max(t["cpu_points"] for c in report["fixtures"] for t in c["turns"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "fixtures": len(report["fixtures"]),
                      "max_measured_cpu_points": report["max_measured_cpu_points"], "matches_run": 0}), flush=True)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, nargs="?")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fixtures-only", action="store_true", help="Write observations without building or executing a bot")
    args = parser.parse_args()
    if args.fixtures_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"matches_run": 0, "bot_executions": 0, "fixtures": fixtures()}, indent=2), encoding="utf-8")
    elif args.candidate is None:
        parser.error("candidate is required unless --fixtures-only is selected")
    else:
        run(args.candidate, args.out)
