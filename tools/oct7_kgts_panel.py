"""Freeze a KGTS-only Python external discovery panel; no holdout or rating claim.

Planning, status and unit tests do not run matches. Only the explicit `run`
subcommand starts games. No upstream scripts or native executables are used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "external-benchmarks"
REGISTRY = {"kgts-protocol-adapted": {
    "commit_sha": "b72ca9baac0e00071ac8013e238b01fe718d02b5",
    "source_bundle_sha256": "256184b8b291638a9137dfc18465c392bb80dad0f4177c165c1eec488f6dc0fe",
    "adapted_freeze_sha256": "7657ec9948a366319f0c97cce61fb53602a0a0ddf07ead6bb82ac4380b0b8750",
    "original_freeze_sha256": "09fa99af996c22ef93a420159c1695d6e0d83bc1fbc72e3944bc20cfc82ce356",
    "adaptation_patch_sha256": "4fe39e8c24dfdd8f449f9989e727957d7bd95403410590dfd3a858b26424b368",
    "python_interpreter_wasm_sha256": "48342178e7ca73775b90aacd0899efed906d79bff79b961360aefe76b5f78125",
}}
# Fixed discovery only: every local map, one external mechanism, both sides.
OBSERVED_MAP_NAMES = {"unsw", "australia", "autarky", "default", "devil", "islands", "maze", "portals",
                      "dilemma", "queen_of_spades", "schooltime", "slithery_fight", "stripes",
                      "tower_defense", "trauma", "trophy", "weakhold"}
SEEDS = {"discovery": (2026100703,)}
SOURCE_SUFFIXES = {".cpp", ".cc", ".cxx", ".c++", ".c", ".h", ".hh", ".hpp", ".hxx", ".inc", ".toml"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def within(path, base):
    path, base = Path(path).resolve(), Path(base).resolve()
    if not path.is_relative_to(base):
        raise ValueError(f"Path outside permitted directory: {path}")
    return path


def external_records(base=EXTERNAL):
    name="kgts-protocol-adapted"; expected=REGISTRY[name]
    directory=within(base/name,base); original=within(base/"kgts-gplv3",base)
    for root,key in ((directory,"adapted_freeze_sha256"),(original,"original_freeze_sha256")):
        frozen=root/"FREEZE.json"
        if digest(frozen.read_bytes())!=expected[key]:raise ValueError("External manifest differs from pinned identity")
        records=json.loads(frozen.read_text(encoding="utf-8"))["files"]
        for relative,h in records.items():
            path=within(root/relative,root)
            if path.is_symlink() or digest(path.read_bytes())!=h:raise ValueError("External frozen bytes changed: "+relative)
    source=directory/"source"
    paths=list(source.rglob("*"))
    if any(p.is_symlink() or not p.is_file() for p in paths):raise ValueError("Unexpected source directory or symlink")
    if {p.name for p in paths}!={"main.py","helper.py","main_actual_template.py","bot.toml"}:raise ValueError("Unexpected Python source files")
    records={p.name:{"sha256":digest(p.read_bytes()),"bytes":p.stat().st_size} for p in sorted(paths)}
    if digest(canonical(records))!=expected["source_bundle_sha256"]:raise ValueError("Python source bundle changed")
    for name_ in ("main.py","main_actual_template.py","bot.toml"):
        if (source/name_).read_bytes()!=(original/"source"/name_).read_bytes():raise ValueError("Upstream strategy bytes changed")
    provenance=json.loads((directory/"PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance["commit_sha"]!=expected["commit_sha"] or digest((directory/"helper-protocol.patch").read_bytes())!=expected["adaptation_patch_sha256"]:
        raise ValueError("GPL provenance or adaptation changed")
    smoke=json.loads((directory/"smoke-results.json").read_text(encoding="utf-8"))
    engine_smoke=json.loads((directory/"engine-protocol-smoke.json").read_text(encoding="utf-8"))
    if not smoke["passed"] or not engine_smoke["passed"]:raise ValueError("Required protocol contracts failed")
    return {name:{**expected,"path":str(directory),"source_path":str(source),"kind":"python",
                 "argv":["python","main.py"],"license":"GPLv3","bot_specific_wasm":None,
                 "source_files":records,"guest_bytecode_files":smoke["guest_bytecode_files"],
                 "provenance_sha256":digest((directory/"PROVENANCE.json").read_bytes())}}

def environment():
    from unswbc import clangtool,engine,sandbox,turn,metering,project
    return {"unswbc_version":importlib.metadata.version("unswbc"),
            "engine_wasm_sha256":digest(engine.WASM_PATH.read_bytes()),
            "python_interpreter_wasm_sha256":digest(sandbox.WASM_PATH.read_bytes()),
            "driver_files":{Path(m.__file__).name:digest(Path(m.__file__).read_bytes()) for m in (clangtool,engine,sandbox,turn,metering,project)},
            "python_runtime_root_bundle_sha256":digest(canonical({p.relative_to(sandbox.ROOT_PATH).as_posix():digest(p.read_bytes()) for p in sorted(sandbox.ROOT_PATH.rglob("*")) if p.is_file()})),
            "runner_sha256":digest(Path(__file__).read_bytes()),
            "runner_origin_sha256":digest((ROOT/"tools/oct7_external_panel.py").read_bytes())}

def map_record(path):
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    dimensions = re.search(r"^MAP[ \t]+(\d+)[ \t]+(\d+)[ \t]*\r?$", text, re.M)
    if not dimensions:
        raise ValueError(f"Missing map dimensions: {path}")
    dragons = []
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0] not in ("DRAGON", "SNAKE"):
            continue
        values = list(map(int, fields[1:]))
        if len(values) != 2 + values[1] * 2 or values[0] not in (0, 1):
            raise ValueError(f"Malformed initial body: {path}")
        dragons.append({"id": len(dragons), "team": "AB"[values[0]],
                        "body": [[values[i], values[i + 1]] for i in range(2, len(values), 2)]})
    if len(dragons) < 2 or {d["team"] for d in dragons[:2]} != {"A", "B"}:
        raise ValueError(f"Map needs fixed Queens on the first two declarations: {path}")
    return {"name": path.stem, "source_path": str(path.resolve()), "sha256": digest(data),
            "width": int(dimensions[1]), "height": int(dimensions[2]), "initial_dragons": dragons,
            "map_evidence": "online100_name_observed" if path.stem in OBSERVED_MAP_NAMES else "supplemental_local_not_observed"}


def validate_seeds(seeds):
    if set(seeds)!={"discovery"} or list(seeds["discovery"])!=[2026100703]:
        raise ValueError("KGTS panel permits only discovery seed2026100703; no holdout")

def jobs_for(maps,seeds=None):
    seeds=SEEDS if seeds is None else seeds;validate_seeds(seeds)
    if len(maps)!=22:raise ValueError("Exactly22 frozen local maps are required")
    return [{"id":f"discovery/kgts-protocol-adapted/{name}-2026100703-{side}","phase":"discovery",
             "opponent":"kgts-protocol-adapted","map":name,"map_evidence":maps[name]["map_evidence"],
             "seed":2026100703,"candidate_team":side,"opponent_team":"B" if side=="A" else "A"}
            for name in sorted(maps) for side in "AB"]

def plan_panel(out, map_dir, seeds=None):
    seeds = SEEDS if seeds is None else seeds
    validate_seeds(seeds)
    maps = {path.stem: map_record(path) for path in sorted(map_dir.glob("*.map"))}
    if not maps:
        raise ValueError("No current map pool")
    plan = {"created_utc": now(), "claim": "KGTS-only discovery mechanism panel; no holdout, online strength or rating claim",
            "opponents": external_records(), "external_freeze_sha256": digest((EXTERNAL / "kgts-protocol-adapted" / "FREEZE.json").read_bytes()),
            "environment": environment(), "maps": maps, "seeds": seeds,
            "map_scope": "22 local map files: 17 names observed in online100 plus 5 supplements; not a verified complete online pool or byte-identical online maps",
            "discovery_selection": "22 frozen local maps x A/B; seed2026100703; one GPL-isolated external mechanism",
            "online100_findings_sha256": digest((ROOT / "test-results" / "online100-findings.md").read_bytes()),
            "jobs": jobs_for(maps, seeds), "candidate_budget_margin_points": 90_000_000,
            "order": "fixed phase/map/seed/opponent/A,B; partial runs resume first pending job",
            "holdout_policy": "No holdout phase; never reads or writes other panels exposure ledgers"}
    out.mkdir(parents=True, exist_ok=False)
    for record in maps.values():
        target = out / "maps" / f"{record['name']}.map"
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(record["source_path"], target)
    write_json(out / "plan.json", {"plan_sha256": digest(canonical(plan)), "plan": plan})
    return plan


def read_plan(panel):
    wrapper = json.loads((panel / "plan.json").read_text(encoding="utf-8"))
    plan = wrapper["plan"]
    if digest(canonical(plan)) != wrapper["plan_sha256"]:
        raise ValueError("Panel plan digest mismatch")
    if plan["opponents"] != external_records() or set(plan["opponents"]) != set(REGISTRY):
        raise ValueError("Panel only permits the pinned GPL-isolated KGTS adaptation")
    if plan["environment"]["python_interpreter_wasm_sha256"] != REGISTRY["kgts-protocol-adapted"]["python_interpreter_wasm_sha256"]:
        raise ValueError("Official Python interpreter differs from audited identity")
    if plan["environment"] != environment():
        raise ValueError("Official engine, toolchain or runner changed after preregistration")
    if plan["external_freeze_sha256"] != digest((EXTERNAL / "kgts-protocol-adapted" / "FREEZE.json").read_bytes()):
        raise ValueError("External freeze manifest changed")
    for name, record in plan["maps"].items():
        if digest((panel / "maps" / f"{name}.map").read_bytes()) != record["sha256"]:
            raise ValueError(f"Frozen map changed: {name}")
    if plan["jobs"] != jobs_for(plan["maps"], plan["seeds"]):
        raise ValueError("Panel schedule differs from preregistered phases")
    return plan


def source_bundle(project, workspace=ROOT):
    workspace = workspace.resolve()
    project = within(project, workspace)
    if project.is_relative_to((workspace / "external-benchmarks").resolve()):
        raise ValueError("Candidate cannot be one of the external baselines")
    found = {}
    def collect(path):
        if path.is_symlink():
            raise ValueError(f"Symlinked candidate dependency: {path}")
        path = within(path, workspace)
        if path.is_relative_to(EXTERNAL.resolve()):
            raise ValueError("Candidate may not incorporate isolated external source")
        if path in found:
            return
        found[path] = path.read_bytes()
        if path.suffix != ".toml":
            for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', found[path].decode("utf-8"), re.M):
                collect(path.parent / include)
    for path in sorted(project.rglob("*")):
        relative = path.relative_to(project)
        if path.is_file() and path.suffix in SOURCE_SUFFIXES and not any(p.startswith(".") for p in relative.parts):
            collect(path)
    if not any(path.suffix in {".c", ".cc", ".cpp", ".cxx", ".c++"} for path in found):
        raise ValueError("Candidate has no C/C++ source")
    records = {path.relative_to(workspace).as_posix(): {"sha256": digest(data), "bytes": len(data)}
               for path, data in sorted(found.items())}
    return digest(canonical(records)), found, records


def freeze_candidate(panel, project, label):
    read_plan(panel)
    protocol = panel / "child-protocol-smoke.json"
    if not protocol.exists() or not json.loads(protocol.read_text(encoding="utf-8"))["passed"]:
        raise ValueError("Run the split-child protocol check before candidate preparation")
    if (panel / "candidate").exists():
        raise ValueError("Candidate preparation already exists; preserve it and use a new panel")
    source_hash, found, records = source_bundle(project)
    stage = panel / "candidate" / "source"
    for path, data in found.items():
        target = stage / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    from unswbc import clangtool
    import contextlib
    # Header and source bytes determine this stage's cache identity.
    named_stage = panel / "candidate" / f"build-{source_hash[:24]}"
    shutil.copytree(stage, named_stage)
    with (panel / "candidate" / "build.log").open("w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            wasm = clangtool.build(named_stage)
    artifact = panel / "candidate" / "bot.wasm"
    shutil.copyfile(wasm, artifact)
    if source_bundle(project)[0] != source_hash:
        raise ValueError("Candidate source changed during compilation")
    frozen = {"frozen_utc": now(), "label": label, "source_path": str(project.resolve()),
              "source_bundle_sha256": source_hash, "source_files": records,
              "wasm_sha256": digest(artifact.read_bytes())}
    write_json(panel / "candidate" / "freeze.json", frozen)
    return frozen


def candidate_record(panel):
    frozen = json.loads((panel / "candidate" / "freeze.json").read_text(encoding="utf-8"))
    if digest((panel / "candidate" / "bot.wasm").read_bytes()) != frozen["wasm_sha256"]:
        raise ValueError("Frozen candidate binary changed")
    current_hash, _, records = source_bundle(Path(frozen["source_path"]))
    if current_hash != frozen["source_bundle_sha256"] or records != frozen["source_files"]:
        raise ValueError("Candidate source changed; create a new discovery panel")
    for relative, record in records.items():
        if digest((panel / "candidate" / "source" / relative).read_bytes()) != record["sha256"]:
            raise ValueError("Candidate source snapshot changed")
    return frozen


def terminal_result(raw):
    teams = {team: {"dragonCount": raw[f"{prefix}_dragons"], "queenLength": raw[f"{prefix}_queen"],
                    "longestDragon": raw[f"{prefix}_longest"], "totalLength": raw[f"{prefix}_length"]}
             for team, prefix in (("A", "a"), ("B", "b"))}
    for stats in teams.values():
        if not (0 <= stats["queenLength"] <= stats["longestDragon"] <= stats["totalLength"]
                and stats["dragonCount"] >= 0
                and (stats["dragonCount"] == 0) == (stats["totalLength"] == 0)):
            raise ValueError("Inconsistent official terminal length hierarchy")
    if raw["end_reason"] == 0:
        counts = [teams[t]["dragonCount"] for t in "AB"]
        if all(counts):
            raise ValueError("Elimination terminal still has both teams")
        winner = "A" if counts[0] else "B" if counts[1] else None
        axis = "elimination" if winner else "tie"
    elif raw["end_reason"] == 1:
        keys = ("queenLength", "longestDragon", "totalLength")
        a, b = (tuple(teams[t][k] for k in keys) for t in "AB")
        winner = "A" if a > b else "B" if b > a else None
        axis = next((name for name, x, y in zip(("queen", "longest", "total_length"), a, b) if x != y), "tie")
    else:
        raise ValueError("Unknown official terminal reason")
    if winner != raw["winner"]:
        raise ValueError("Official winner disagrees with terminal scores")
    return {"terminated": True, "winner": raw["winner"], "endReason": "teamEliminated" if raw["end_reason"] == 0 else "roundLimit",
            "teamA": teams["A"], "teamB": teams["B"], "decisive_axis": axis,
            "engine_last_round_index": raw["rounds"], "round_count": raw["rounds"] + 1}


def make_python_pool(record,key):
    from unswbc.sandbox import SandboxPool as PythonPool
    frozen=external_records()["kgts-protocol-adapted"]
    if record!=frozen:raise ValueError("Unregistered Python opponent")
    pool=PythonPool(["python","main.py"],cwd=record["source_path"],key=key)
    compiled={p.name:digest(p.read_bytes()) for p in sorted((pool.root/"bot").glob("*.pyc"))}
    if compiled!=record["guest_bytecode_files"]:
        pool.close();raise ValueError("Guest-compiled Python bytecode differs from freeze")
    return pool


def run_game(panel, plan, frozen, job):
    from unswbc.engine import DEBUG_ALL, DEBUG_LIMITS, EngineModule
    from unswbc.sandbox import SandboxBot, WasmPool
    directory = panel / "games" / job["id"]
    directory.mkdir(parents=True, exist_ok=False)
    log = (directory / "raw.log").open("w", encoding="utf-8")
    pools, live, teams = {}, {}, {}
    errors, deaths, notices = [], [], []
    peak = {team: {"points": 0, "memory_bytes": 0, "turns": 0} for team in "AB"}
    row = {**job, "started_utc": now(), "candidate": frozen,
           "opponent": plan["opponents"][job["opponent"]], "map_sha256": plan["maps"][job["map"]]["sha256"],
           "initial_dragons": plan["maps"][job["map"]]["initial_dragons"],
           "environment": plan["environment"], "formal_result": None, "engine_result": None,
           "runtime_errors": errors, "deaths": deaths, "map_notices": notices, "peak": peak}
    def spawn(identity, init):
        team = next(line.split()[1] for line in init.decode().splitlines() if line.startswith("TEAM "))
        teams[identity] = team
        live[identity] = SandboxBot(pools[team], init=init, name=str(identity))
    def reply(identity, block):
        bot = live[identity]
        output = bot.ask(block)
        points, memory = bot.live
        team = teams[identity]
        peak[team]["points"] = max(peak[team]["points"], points)
        peak[team]["memory_bytes"] = max(peak[team]["memory_bytes"], memory)
        peak[team]["turns"] += 1
        stderr = bot.take_stderr().decode("utf-8", "replace")
        if bot.error or stderr:
            event = {"team": team, "id": identity, "round_header": block.splitlines()[0].decode(),
                     "error": bot.error, "stderr": stderr}
            if bot.error:
                errors.append(event)
            log.write(json.dumps({"bot_diagnostic": event}) + "\n")
        return output
    def death(identity, round_num, reason):
        event = {"team": teams[identity], "id": identity, "round": round_num, "reason": reason}
        deaths.append(event)
        log.write(json.dumps({"death": event}) + "\n")
        live.pop(identity).stop()
    def notice(text):
        notices.append(text)
        log.write(text + "\n")
    try:
        for team in "AB":
            key=f"{job['seed']:016x}-{team.lower()}"
            pools[team]=(WasmPool([str(panel/"candidate/bot.wasm")],key=key) if team==job["candidate_team"]
                         else make_python_pool(row["opponent"],key))
        engine = EngineModule()
        map_bytes = (panel / "maps" / f"{job['map']}.map").read_bytes()
        if digest(map_bytes) != row["map_sha256"]:
            raise ValueError("Frozen map changed before execution")
        result = engine.run(map_bytes, reply, death, spawn, notice, DEBUG_ALL | DEBUG_LIMITS, job["seed"])
        row["engine_result"] = asdict(result)
        names = {job["candidate_team"]: frozen["label"], job["opponent_team"]: job["opponent"]}
        blob = engine.replay(names["A"], names["B"])
        (directory / "raw.replay").write_bytes(blob)
        row["replay"] = {"path": str((directory / "raw.replay").resolve()), "sha256": digest(blob), "bytes": len(blob)}
        row["formal_result"] = terminal_result(row["engine_result"])
        winner = row["formal_result"]["winner"]
        row["official_outcome"] = "draw" if winner is None else "win" if winner == job["candidate_team"] else "loss"
    except Exception as error:
        row["infrastructure_error"] = f"{type(error).__name__}: {error}"
        log.write(row["infrastructure_error"] + "\n")
    finally:
        for bot in live.values():
            bot.stop()
        for pool in pools.values():
            pool.close()
        log.close()
    invalid = {team: sum(event["team"] == team for event in errors)
                    + sum(event["team"] == team and event["reason"] == "A" for event in deaths) for team in "AB"}
    row["invalid_runtime_events"] = invalid
    row["eligible_mechanism_result"] = (row["formal_result"] is not None and not any(invalid.values()) and not notices)
    row["candidate_budget_margin_passed"] = peak[job["candidate_team"]]["points"] < plan["candidate_budget_margin_points"]
    row["ended_utc"] = now()
    row["raw_log_sha256"] = digest((directory / "raw.log").read_bytes())
    write_json(directory / "result.json", row)
    return row


def status(panel, plan):
    report = {"claim": plan["claim"], "phases": {}}
    for phase in SEEDS:
        jobs = [job for job in plan["jobs"] if job["phase"] == phase]
        rows = [json.loads(path.read_text(encoding="utf-8")) for job in jobs
                if (path := panel / "games" / job["id"] / "result.json").exists()]
        report["phases"][phase] = {"scheduled": len(jobs), "completed": len(rows), "complete": len(rows) == len(jobs),
            "incomplete_attempts": [job["id"] for job in jobs if (panel / "games" / job["id"]).exists()
                                    and not (panel / "games" / job["id"] / "result.json").exists()],
            "official_outcomes": {outcome: sum(row.get("official_outcome") == outcome for row in rows) for outcome in ("win", "loss", "draw")},
            "eligible_outcomes": {outcome: sum(row.get("official_outcome") == outcome and row["eligible_mechanism_result"] for row in rows) for outcome in ("win", "loss", "draw")},
            "ineligible_games": sum(not row["eligible_mechanism_result"] for row in rows),
            "candidate_runtime_events": sum(row["invalid_runtime_events"][row["candidate_team"]] for row in rows),
            "opponent_runtime_events": sum(row["invalid_runtime_events"][row["opponent_team"]] for row in rows),
            "infrastructure_errors": sum("infrastructure_error" in row for row in rows),
            "candidate_budget_margin_failures": sum(not row["candidate_budget_margin_passed"] for row in rows)}
        report["phases"][phase]["by_map_evidence"] = {
            group: {"scheduled": sum(job["map_evidence"] == group for job in jobs),
                    "completed": sum(row["map_evidence"] == group for row in rows),
                    "eligible_outcomes": {outcome: sum(row["map_evidence"] == group and row["eligible_mechanism_result"]
                                                   and row.get("official_outcome") == outcome for row in rows)
                                          for outcome in ("win", "loss", "draw")}}
            for group in ("online100_name_observed", "supplemental_local_not_observed")}
    return report


def run_panel(panel,phase,limit):
    if phase!="discovery":raise ValueError("No holdout phase")
    plan,frozen=read_plan(panel),candidate_record(panel)
    previous=status(panel,plan)["phases"][phase]
    if previous["candidate_runtime_events"] or previous["infrastructure_errors"] or previous["candidate_budget_margin_failures"]:
        raise ValueError("Panel stopped by recorded candidate correctness/budget or infrastructure failure")
    incomplete=previous["incomplete_attempts"]
    if incomplete:raise ValueError("Interrupted attempts retained; not retried: "+", ".join(incomplete))
    pending=[j for j in plan["jobs"] if not (panel/"games"/j["id"]).exists()]
    if limit is not None:pending=pending[:limit]
    for job in pending:
        read_plan(panel);candidate_record(panel)
        row=run_game(panel,plan,frozen,job);write_json(panel/"summary.json",status(panel,plan))
        print(json.dumps({"job":job["id"],"official_outcome":row.get("official_outcome"),"eligible":row["eligible_mechanism_result"]}),flush=True)
        if "infrastructure_error" in row or row["invalid_runtime_events"][job["candidate_team"]] or not row["candidate_budget_margin_passed"]:break
    report=status(panel,plan);write_json(panel/"summary.json",report);return report

def protocol_check(panel):
    plan=read_plan(panel)
    from unswbc.engine import DEBUG_ALL,DEBUG_LIMITS,EngineModule
    from unswbc.sandbox import SandboxBot
    raw=("MAP 20 20\nUNIT_LIMIT 64\nTILE_COUNT 1\nTILE 5 6 1 1\nEDGE_COUNT 0\nDRAGON_COUNT 3\n"
         "DRAGON 0 2 1 1 1 2\nDRAGON 1 2 18 18 19 18\nDRAGON 0 5 5 5 4 5 3 5 3 6 4 6\n").encode()
    pool=make_python_pool(plan["opponents"]["kgts-protocol-adapted"],"kgts-panel-contract")
    bots={};frames=[];births=[];notices=[];engine=EngineModule()
    def spawn(identity,init):
        births.append({"id":identity,"init_sha256":digest(init)})
        if identity>=2:bots[identity]=SandboxBot(pool,init=init,name=str(identity))
    def reply(identity,block):
        round_no=int(re.search(rb"^ROUND (\d+)",block,re.M)[1])
        if round_no>=2:return b"LOG intentional contract stop\nENDTURN\n"
        if identity<2:return b"MOVE N\nENDTURN\n"
        bot=bots[identity];out=bot.ask(block);stderr=bot.take_stderr().decode();points,memory=bot.live
        frames.append({"id":identity,"round":round_no,"input":block.decode(),"input_sha256":digest(block),"output":out.decode(),
                       "error":bot.error,"stderr":stderr,"cpu_points":points,"memory_bytes":memory,
                       "passed":bot.error is None and not stderr and bot._framer.done and points<90_000_000
                                 and len(re.findall(rb"^(?:MOVE [NEWS]+|SPLIT \d+)$",out,re.M))==1})
        return out+b"ENDTURN\n"
    try:
        engine.run(raw,reply,bot_spawn=spawn,on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100780)
        replay=engine.replay("fixed-contract-A","fixed-contract-B");(panel/"child-protocol-smoke.replay").write_bytes(replay)
    finally:
        for bot in bots.values():bot.stop()
        pool.close()
    passed=([(f["round"],f["id"]) for f in frames]==[(0,2),(0,3),(1,2),(1,3)] and all(f["passed"] for f in frames)
            and "ECHOES " not in frames[0]["input"] and all("ECHOES " in f["input"] for f in frames[1:])
            and "SPLIT 2\n" in frames[0]["output"] and "PROTOCOL 3\n" in frames[0]["output"] and not notices)
    result={"tested_utc":now(),"matches_run":0,"kind":"two-round actual protocol contract; fixed other replies; intentionally stopped",
            "passed":passed,"births":births,"frames":frames,"map_sha256":digest(raw),"replay_sha256":digest(replay),
            "opponent":plan["opponents"]["kgts-protocol-adapted"],"environment":plan["environment"]}
    write_json(panel/"child-protocol-smoke.json",result)
    if not passed:raise ValueError("Actual Python spawn/child protocol contract failed")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--out", required=True)
    for command in ("protocol", "status", "freeze", "run"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("--panel", required=True)
        if command == "freeze":
            command_parser.add_argument("--candidate", required=True)
            command_parser.add_argument("--label", required=True)
        if command == "run":
            command_parser.add_argument("--phase", choices=tuple(SEEDS), required=True)
            command_parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    os.environ["UNSWBC_WARM"] = "1"
    if args.command == "plan":
        out = within(ROOT / args.out, ROOT / "test-results")
        seeds = SEEDS
        plan = plan_panel(out, ROOT / "maps" / "current", seeds)
        print(json.dumps({"panel": str(out), "scheduled": {phase: sum(j["phase"] == phase for j in plan["jobs"]) for phase in SEEDS}}))
        return
    panel = within(ROOT / args.panel, ROOT / "test-results")
    if args.command == "protocol":
        result = protocol_check(panel)
    elif args.command == "freeze":
        result = freeze_candidate(panel, within(ROOT / args.candidate, ROOT), args.label)
    elif args.command == "status":
        result = status(panel, read_plan(panel))
    else:
        if args.limit is not None and args.limit < 1:
            parser.error("--limit must be positive")
        result = run_panel(panel, args.phase, args.limit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
