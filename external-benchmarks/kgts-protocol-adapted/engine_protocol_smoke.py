"""A two-round official protocol contract, not a benchmark match.

Only parent2 and its newborn use audited KGTS in the official Python sandbox.
Other dragons use fixed replies. After the two tested rounds, intentionally
missing actions end the synthetic fixture; these are not bot policy failures.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from unswbc.engine import DEBUG_ALL, DEBUG_LIMITS, EngineModule
from unswbc.sandbox import SandboxBot, SandboxPool, WASM_PATH

HERE=Path(__file__).resolve().parent


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    map_bytes=("MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT 1\nTILE 5 6 1 1\nEDGE_COUNT 0\n"
               "DRAGON_COUNT 3\nDRAGON 0 2 1 1 1 2\nDRAGON 1 2 18 18 19 18\n"
               "DRAGON 0 5 5 5 4 5 3 5 3 6 4 6\n").encode()
    engine=EngineModule();bots={};observed=[];notices=[]
    pool=SandboxPool(["python","main.py"],cwd=str(HERE/"source"),key="kgts-actual-protocol-fixture")
    def reply(identity,block):
        raw=block.decode();round_no=int(re.search(r"^ROUND (\d+)",raw,re.M)[1])
        if round_no>=2:return b"LOG intentional protocol fixture stop\nENDTURN\n"
        if identity not in (2,3):return b"MOVE N\nENDTURN\n"
        if identity not in bots:
            init=f"ID {identity}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n"
            bots[identity]=SandboxBot(pool,init=init.encode(),name=str(identity))
        bot=bots[identity];output=bot.ask(block);stderr=bot.take_stderr().decode();points,memory=bot.live
        actions=re.findall(rb"^(?:MOVE [NEWS]+|SPLIT \d+)$",output,re.M)
        row={"round":round_no,"id":identity,"input":raw,"input_sha256":digest(block),
             "output":output.decode(),"error":bot.error,"stderr":stderr,"cpu_points":points,
             "memory_bytes":memory,"endturn_received":bot._framer.done}
        row["passed"]=bot.error is None and not stderr and len(actions)==1 and bot._framer.done and points<90_000_000
        observed.append(row)
        return output+b"ENDTURN\n"
    try:
        engine.run(map_bytes,reply,on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100780)
        replay=engine.replay("fixed-protocol-fixture-A","fixed-protocol-fixture-B")
        (HERE/"engine-protocol-smoke.replay").write_bytes(replay)
    finally:
        for bot in bots.values():bot.stop()
        pool.close()
    assert [(r["round"],r["id"]) for r in observed]==[(0,2),(0,3),(1,2),(1,3)]
    assert "ECHOES " not in observed[0]["input"]
    assert "SPLIT 2\n" in observed[0]["output"] and "PROTOCOL 3\n" in observed[0]["output"]
    assert all("ECHOES " in r["input"] for r in observed[1:])
    assert all(r["passed"] for r in observed)
    (HERE/"engine-protocol-smoke.raw.log").write_text("".join(notices),encoding="utf-8")
    report={"tested_utc":datetime.now(timezone.utc).isoformat(),"passed":True,"cases":1,"frames":len(observed),
            "matches_run":0,"fixture_kind":"two-round synthetic protocol contract with fixed other replies",
            "intentional_end":"Round2 onwards sends no action to stop fixture; no final result is a strength sample",
            "map_sha256":digest(map_bytes),"driver_sha256":digest(Path(__file__).read_bytes()),
            "python_interpreter_wasm_sha256":digest(WASM_PATH.read_bytes()),"source_files":{
                p.name:digest(p.read_bytes()) for p in (HERE/"source").iterdir() if p.suffix in (".py",".toml")},
            "replay_sha256":digest(replay),"turns":observed,"max_measured_cpu_points":max(r["cpu_points"] for r in observed),
            "confirmed":["Initial parent protocol2 without ECHOES parses","Parent replies SPLIT2 and PROTOCOL3",
                         "Same-round newborn inherits protocol3 and acts","Next round parent and child receive ECHOES"]}
    (HERE/"engine-protocol-smoke.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("passed","cases","frames","max_measured_cpu_points","matches_run")}))


if __name__=="__main__":main()
