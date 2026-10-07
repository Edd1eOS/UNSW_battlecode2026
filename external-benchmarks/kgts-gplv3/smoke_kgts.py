"""Check the pinned KGTS source in the official Python judge; no games.

The upstream sources are not imported in the host interpreter. SandboxPool
compiles them to guest bytecode and executes main only inside the WASM guest.
"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import re
import shutil

from unswbc.sandbox import SandboxBot, SandboxPool, WASM_PATH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMMIT = "b72ca9baac0e00071ac8013e238b01fe718d02b5"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scenarios():
    spec = importlib.util.spec_from_file_location("our_local_packet_builder", ROOT / "external-benchmarks/smoke_external.py")
    packets = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packets)
    packets.DIM = 64
    long_body = ([(x, 20) for x in range(20, -1, -1)]
                 + [(0, y) for y in range(19, -1, -1)]
                 + [(x, 0) for x in range(1, 24)])
    assert len(long_body) == 64 and len(set(long_body)) == 64
    cases = []
    def case(name, identity, body, *, protocol, round_num=1, units=2, pearls=(), messages=(), expected=None):
        raw = packets.frame(identity, body, round_num=round_num, units=units, protocol=protocol,
                            pearls=pearls, messages=messages)
        cases.append({"name": name, "init": f"ID {identity}\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                      "turns": [raw], "expected": expected, "protocol": protocol,
                      "scope": "isolated legal local observation; no match"})
    case("official_initial_protocol2", 0, long_body[:2], protocol=2, pearls=((21,20),), expected="MOVE E")
    # Hypothetical already-upgraded parent and inherited child inputs isolate
    # the parser problem. They do not prove that this source can upgrade itself.
    case("already_upgraded_protocol3", 0, long_body[:2], protocol=3, pearls=((21,20),), expected="MOVE E")
    case("fresh_child_inherited_protocol3_uint64", 8, long_body[:2], protocol=3, round_num=100,
         pearls=((21,20),), messages=(18446744073709551615,), expected="MOVE E")
    case("early_phase_queen_split2", 0, long_body[:5], protocol=3, expected="SPLIT 2")
    case("middle_phase_worker_split3", 2, long_body[:10], protocol=3, round_num=300, expected="SPLIT 3")
    case("late_phase_stops_split", 2, long_body[:10], protocol=3, round_num=425, pearls=((21,20),), expected="MOVE E")
    case("64map_long_partial_body_budget", 2, long_body, protocol=3, round_num=200, units=64,
         pearls=((21,20),(20,18),(22,21)))
    case("toroidal_seam_visible_food", 2, [(0,20),(1,20)], protocol=3,
         pearls=((63,20),), expected="MOVE W")
    return cases


def main():
    source = HERE / "source"
    records = {p.name: {"sha256": digest(p.read_bytes()), "bytes": p.stat().st_size}
               for p in sorted(source.iterdir()) if p.suffix in (".py", ".toml")}
    for p in source.glob("*.py"):
        ast.parse(p.read_text(encoding="utf-8"), filename=p.name)  # Syntax only, no host import.
    report = {"commit_sha": COMMIT, "tested_utc": datetime.now(timezone.utc).isoformat(),
              "unswbc_version": importlib.metadata.version("unswbc"), "source_files": records,
              "source_bundle_sha256": digest(json.dumps(records,sort_keys=True,separators=(",",":")).encode()),
              "license": "GPLv3 (upstream LICENSE)", "license_sha256": digest((HERE/"LICENSE").read_bytes()),
              "runtime": "official Python WASM interpreter + guest-compiled bot bytecode; no bot-specific WASM",
              "python_interpreter_wasm_sha256": digest(WASM_PATH.read_bytes()),
              "driver_sha256": digest(Path(__file__).read_bytes()), "upstream_scripts_executed": False,
              "host_import_of_upstream": False, "matches_run": 0, "scenarios": []}
    cases = scenarios()
    (HERE / "smoke-fixtures.json").write_text(json.dumps({"matches_run": 0, "fixtures": cases},indent=2)+"\n")
    pool = SandboxPool(["python", "main.py"], cwd=str(source), key="kgts-pinned-protocol-only")
    try:
        artifacts = HERE / "guest-bytecode"
        artifacts.mkdir(exist_ok=True)
        for p in sorted((pool.root/"bot").glob("*.pyc")):
            shutil.copyfile(p,artifacts/p.name)
        report["guest_bytecode_files"] = {p.name:digest(p.read_bytes()) for p in sorted(artifacts.glob("*.pyc"))}
        for c in cases:
            identity = re.search(r"^ID (\d+)",c["init"]).group(1)
            bot = SandboxBot(pool,init=c["init"].encode(),name=identity)
            rows = []
            try:
                for raw in c["turns"]:
                    output = bot.ask(raw.encode()).decode("utf-8","replace")
                    stderr = bot.take_stderr().decode("utf-8","replace")
                    points,memory = bot.live
                    actions = re.findall(r"^(?:MOVE [NEWS]+|SPLIT \d+)$",output,re.M)
                    passed = (bot.error is None and not stderr and bot._framer.done and len(actions)==1
                              and points < 90_000_000 and (c["expected"] is None or actions==[c["expected"]]))
                    rows.append({"input_sha256":digest(raw.encode()),"output":output,"error":bot.error,
                                 "stderr":stderr,"endturn_received":bot._framer.done,"cpu_points":points,
                                 "memory_bytes":memory,"passed":passed})
            finally:
                bot.stop()
            report["scenarios"].append({"name":c["name"],"protocol":c["protocol"],"turns":rows,
                                        "passed":all(r["passed"] for r in rows)})
            print(c["name"],rows[-1]["passed"],rows[-1]["cpu_points"],rows[-1]["error"],flush=True)
    finally:
        pool.close()
    report["passed"] = all(c["passed"] for c in report["scenarios"])
    report["max_measured_cpu_points"] = max(t["cpu_points"] for c in report["scenarios"] for t in c["turns"])
    report["compatibility_decision"] = "Original source ineligible: initial protocol2 parser fails" if not report["scenarios"][0]["passed"] else "Review remaining checks"
    (HERE/"smoke-results.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("passed","max_measured_cpu_points","compatibility_decision","matches_run")}))


if __name__ == "__main__":
    main()
