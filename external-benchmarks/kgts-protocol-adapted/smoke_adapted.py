"""Validate only the KGTS optional-ECHOES adaptation in the official judge.

No games, upstream host imports, upstream hooks or project scripts are run.
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
BASE = HERE.parent / "kgts-gplv3"
ROOT = HERE.parents[1]
COMMIT = "b72ca9baac0e00071ac8013e238b01fe718d02b5"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Only our reviewed fixture builders.
    return module


def scenarios():
    original = load_module("original_local_assessment", BASE / "smoke_kgts.py")
    cases = original.scenarios()
    for c in cases:
        c["expected_actions"] = [c.pop("expected")]
        c["compare_original"] = c["protocol"] == 3
    packets = load_module("local_protocol_packet_builder", ROOT / "external-benchmarks/smoke_external.py")
    packets.DIM = 64
    ring = [(20,20),(21,20),(21,21),(20,21)]
    edges = list(zip(ring,ring[1:]+ring[:1]))
    cases.append({"name":"continuous_protocol2_to3_ring", "protocol":2,
                  "init":"ID 0\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                  "turns":[packets.frame(0,[ring[i],ring[(i-1)%4]],round_num=i+1,units=2,
                                          protocol=2 if i==0 else 3,edges=edges,
                                          messages=() if i==0 else (18446744073709551615,)) for i in range(4)],
                  "expected_actions":["MOVE E","MOVE S","MOVE W","MOVE N"],"compare_original":False,
                  "scope":"successive legal body/position observations agree with each prior output"})
    cases.append({"name":"fresh_child_protocol2_before_upgrade", "protocol":2,
                  "init":"ID 8\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                  "turns":[packets.frame(8,[(20,20),(19,20)],round_num=100,units=3,protocol=2,pearls=((21,20),))],
                  "expected_actions":["MOVE E"],"compare_original":False,
                  "scope":"protocol2 child of legacy parent; local view only"})
    messages=tuple((1<<60)|((x%64)<<30)|((x//64+40)%64) for x in range(256))
    cases.append({"name":"256_uint64_sonar_messages_budget", "protocol":3,
                  "init":"ID 2\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
                  "turns":[packets.frame(2,[(20,20),(19,20)],round_num=200,units=64,protocol=3,messages=messages)],
                  "expected_actions":[None],"compare_original":True,
                  "scope":"constructed protocol budget sample; no claim of a recorded real message distribution"})
    return cases


def ask(pool, case):
    bot=SandboxBot(pool,init=case["init"].encode(),name=re.search(r"^ID (\d+)",case["init"]).group(1))
    rows=[]
    try:
        for index,raw in enumerate(case["turns"]):
            output=bot.ask(raw.encode()).decode("utf-8","replace")
            stderr=bot.take_stderr().decode("utf-8","replace")
            points,memory=bot.live
            actions=re.findall(r"^(?:MOVE [NEWS]+|SPLIT \d+)$",output,re.M)
            expected=case["expected_actions"][index]
            rows.append({"input_sha256":digest(raw.encode()),"output":output,"error":bot.error,"stderr":stderr,
                         "endturn_received":bot._framer.done,"cpu_points":points,"memory_bytes":memory,
                         "passed":bot.error is None and not stderr and bot._framer.done and len(actions)==1
                                  and points<90_000_000 and (expected is None or actions==[expected])})
            if not rows[-1]["passed"]:break
    finally:
        bot.stop()
    return rows


def main():
    sources=HERE/"source"
    unchanged=["main.py","main_actual_template.py","bot.toml"]
    assert all((sources/name).read_bytes()==(BASE/"source"/name).read_bytes() for name in unchanged)
    for p in sources.glob("*.py"):ast.parse(p.read_text(encoding="utf-8"),filename=p.name)
    records={p.name:{"sha256":digest(p.read_bytes()),"bytes":p.stat().st_size}
             for p in sorted(sources.iterdir()) if p.suffix in (".py",".toml")}
    report={"commit_sha":COMMIT,"adaptation":"Only optional ECHOES parsing and first tile preservation",
            "tested_utc":datetime.now(timezone.utc).isoformat(),"unswbc_version":importlib.metadata.version("unswbc"),
            "source_files":records,"unchanged_strategy_files":unchanged,
            "source_bundle_sha256":digest(json.dumps(records,sort_keys=True,separators=(",",":")).encode()),
            "license":"GPLv3 (preserved upstream LICENSE)","license_sha256":digest((HERE/"LICENSE").read_bytes()),
            "python_interpreter_wasm_sha256":digest(WASM_PATH.read_bytes()),"bot_specific_wasm":None,
            "driver_sha256":digest(Path(__file__).read_bytes()),"matches_run":0,"upstream_scripts_executed":False,
            "host_import_of_upstream":False,"scenarios":[]}
    cases=scenarios();(HERE/"smoke-fixtures.json").write_text(json.dumps({"matches_run":0,"fixtures":cases},indent=2)+"\n")
    pool=SandboxPool(["python","main.py"],cwd=str(sources),key="kgts-protocol-adaptation")
    baseline=None
    try:
        baseline=SandboxPool(["python","main.py"],cwd=str(BASE/"source"),key="kgts-protocol-adaptation")
        artifacts=HERE/"guest-bytecode";artifacts.mkdir(exist_ok=True)
        for p in sorted((pool.root/"bot").glob("*.pyc")):shutil.copyfile(p,artifacts/p.name)
        report["guest_bytecode_files"]={p.name:digest(p.read_bytes()) for p in sorted(artifacts.glob("*.pyc"))}
        for case in cases:
            rows=ask(pool,case);entry={"name":case["name"],"scope":case["scope"],"turns":rows,
                                      "passed":len(rows)==len(case["turns"]) and all(t["passed"] for t in rows)}
            if case["compare_original"]:
                original=ask(baseline,case)
                entry["original_turns"]=original
                entry["protocol3_outputs_identical"]=len(original)==len(rows) and all(a["output"]==b["output"] and b["passed"] for a,b in zip(rows,original))
                entry["passed"] &= entry["protocol3_outputs_identical"]
            report["scenarios"].append(entry)
            print(case["name"],entry["passed"],max(t["cpu_points"] for t in rows),flush=True)
    finally:
        pool.close()
        if baseline is not None:baseline.close()
    report["passed"]=all(c["passed"] for c in report["scenarios"])
    report["cases"]=len(report["scenarios"]);report["frames"]=sum(len(c["turns"]) for c in report["scenarios"])
    report["protocol3_comparisons"]=sum("protocol3_outputs_identical" in c for c in report["scenarios"])
    report["max_measured_cpu_points"]=max(t["cpu_points"] for c in report["scenarios"] for t in c["turns"])
    (HERE/"smoke-results.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("passed","cases","frames","protocol3_comparisons","max_measured_cpu_points","matches_run")}))
    if not report["passed"]:raise SystemExit(1)


if __name__=="__main__":main()
