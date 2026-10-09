"""Freeze Oct7 paired discovery and independent holdout against audited external mechanisms.

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
REGISTRY = {
    "sas-987": {
        "commit_sha": "1a3f3775353605f0da7142f276085e2764bca997",
        "source_bundle_sha256": "80741062ddc9441d087b541c2311c69cfdd7abe2538577b857667aca8dee7529",
        "wasm_sha256": "2ad3e55d4bc727449fa842e8bbf720f6ce4df690409889fb795faf69c0185ddb",
    },
    "official-murder": {
        "commit_sha": "79e22e7950e334711574bcc1166b3973153ccc4f",
        "source_bundle_sha256": "49ab706103223f8b0399e102072133de70cb63c78caf9bce29e4e892986e1eeb",
        "wasm_sha256": "831b3c06360bf5f961af8c63c151c1c6e7247d0f0e3b4c64f4584b8a268ccd55",
    },
}
# Both phases cover every frozen map; paired discovery does not play candidates together.
OBSERVED_MAP_NAMES = {"unsw", "australia", "autarky", "default", "devil", "islands", "maze", "portals",
                      "dilemma", "queen_of_spades", "schooltime", "slithery_fight", "stripes",
                      "tower_defense", "trauma", "trophy", "weakhold"}
SEEDS = {"discovery": (2026100701,), "holdout": (2026100791, 2026100792)}
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
    """Commit, original-byte and binary digests are pinned in this driver."""
    freeze = json.loads((base / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["files"].items():
        if digest(within(base / relative, base).read_bytes()) != expected:
            raise ValueError(f"External freeze changed: {relative}")
    records = {}
    for name, expected in REGISTRY.items():
        directory = within(base / name, base)
        provenance = json.loads((directory / "PROVENANCE.json").read_text(encoding="utf-8"))
        if {f["local_path"] for f in provenance["files"]} != {"main.cpp", "helper.hpp", "bot.toml", "LICENSE"}:
            raise ValueError(f"Unexpected upstream source set: {name}")
        for entry in provenance["files"]:
            if digest((directory / entry["local_path"]).read_bytes()) != entry["sha256"]:
                raise ValueError(f"Upstream bytes changed: {name}/{entry['local_path']}")
        bundle = digest(b"".join(entry["local_path"].encode() + b"\0" + (directory / entry["local_path"]).read_bytes()
                                  for entry in sorted(provenance["files"], key=lambda item: item["local_path"])))
        if (provenance["commit_sha"] != expected["commit_sha"] or bundle != expected["source_bundle_sha256"]
                or digest((directory / "bot.wasm").read_bytes()) != expected["wasm_sha256"]):
            raise ValueError(f"Unregistered external implementation: {name}")
        smoke = json.loads((directory / "smoke-results.json").read_text(encoding="utf-8"))
        if not smoke["passed"] or smoke["wasm_sha256"] != expected["wasm_sha256"]:
            raise ValueError(f"Missing passing external protocol smoke: {name}")
        records[name] = {**expected, "path": str(directory), "license": "MIT",
                         "provenance_sha256": digest((directory / "PROVENANCE.json").read_bytes())}
    return records


def environment():
    from unswbc import clangtool, engine, sandbox
    return {"unswbc_version": importlib.metadata.version("unswbc"),
            "engine_wasm_sha256": digest(engine.WASM_PATH.read_bytes()),
            "driver_files": {Path(module.__file__).name: digest(Path(module.__file__).read_bytes())
                             for module in (clangtool, engine, sandbox)},
            "runner_sha256": digest(Path(__file__).read_bytes())}


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
    if set(seeds) != set(SEEDS):
        raise ValueError("Both discovery and holdout seed lists are required")
    for values in seeds.values():
        if not values or len(set(values)) != len(values) or any(
                type(value) is not int or not 0 <= value < 2**64 for value in values):
            raise ValueError("Seeds must be distinct unsigned 64-bit integers")
    if set(seeds["discovery"]) & set(seeds["holdout"]):
        raise ValueError("Discovery and holdout seeds overlap")


def jobs_for(maps, seeds=None):
    seeds = SEEDS if seeds is None else seeds
    validate_seeds(seeds)
    jobs = []
    for phase, names in (("discovery", tuple(sorted(maps))), ("holdout", tuple(sorted(maps)))):
        for map_name in names:
            if map_name not in maps:
                raise ValueError(f"Missing preregistered map: {map_name}")
            for seed in seeds[phase]:
                for opponent in REGISTRY:
                    for side in ("A", "B"):
                        jobs.append({"id": f"{phase}/{opponent}/{map_name}-{seed}-{side}",
                                     "phase": phase, "opponent": opponent, "map": map_name,
                                     "map_evidence": maps[map_name]["map_evidence"],
                                     "seed": seed, "candidate_team": side,
                                     "opponent_team": "B" if side == "A" else "A"})
    return jobs


def plan_panel(out, map_dir, seeds=None):
    seeds = SEEDS if seeds is None else seeds
    validate_seeds(seeds)
    maps = {path.stem: map_record(path) for path in sorted(map_dir.glob("*.map"))}
    if not maps:
        raise ValueError("No current map pool")
    plan = {"created_utc": now(), "claim": "paired external discovery; unopened holdout for one final frozen candidate; no rating conversion",
            "opponents": external_records(), "external_freeze_sha256": digest((EXTERNAL / "FREEZE.json").read_bytes()),
            "environment": environment(), "maps": maps, "seeds": seeds,
            "map_scope": "22 local map files: 17 names observed in online100 plus 5 supplements; not a verified complete online pool or byte-identical online maps",
            "discovery_selection": "All 22 frozen local maps in both phases; shared discovery seed controls initial conditions across independent candidate-versus-external matches",
            "online100_findings_sha256": digest((ROOT / "test-results" / "online100-findings.md").read_bytes()),
            "jobs": jobs_for(maps, seeds), "candidate_budget_margin_points": 90_000_000,
            "order": "fixed phase/map/seed/opponent/A,B; partial runs resume first pending job",
            "holdout_policy": "one frozen candidate; no source or environment changes; discovery complete first"}
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
        raise ValueError("Panel only permits the two pinned external opponents")
    if plan["environment"] != environment():
        raise ValueError("Official engine, toolchain or runner changed after preregistration")
    if plan["external_freeze_sha256"] != digest((EXTERNAL / "FREEZE.json").read_bytes()):
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
    class AuditedBot(SandboxBot):
        def _fresh(self):
            if self._box is not None:
                team = teams[int(self._name)]
                points, memory = self.live
                event = {"team": team, "id": int(self._name), "error": self._reason(),
                         "kind": "implicit_restart", "cpu_points": points, "memory_bytes": memory}
                errors.append(event)
                peak[team]["points"] = max(peak[team]["points"], points)
                log.write(json.dumps({"bot_diagnostic": event}) + "\n")
            super()._fresh()
    row["implicit_restart_audit"] = True
    def spawn(identity, init):
        team = next(line.split()[1] for line in init.decode().splitlines() if line.startswith("TEAM "))
        teams[identity] = team
        live[identity] = AuditedBot(pools[team], init=init, name=str(identity))
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
        paths = {job["candidate_team"]: panel / "candidate" / "bot.wasm",
                 job["opponent_team"]: Path(row["opponent"]["path"]) / "bot.wasm"}
        for team in "AB":
            pools[team] = WasmPool([str(paths[team])], key=f"{job['seed']:016x}-{team.lower()}")
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


def reserve_holdout(panel, frozen, ledger, seeds=None):
    """Opening these seeds for one candidate makes later redesigns discovery."""
    claim = {"panel": str(panel.resolve()), "plan_file_sha256": digest((panel / "plan.json").read_bytes()),
             "candidate_source_sha256": frozen["source_bundle_sha256"], "candidate_wasm_sha256": frozen["wasm_sha256"]}
    if seeds is not None:
        claim["holdout_seeds"] = list(seeds)
        for prior in ledger.parent.glob("external-panel-holdout-exposure-*.json"):
            previous = json.loads(prior.read_text(encoding="utf-8"))["claim"]
            previous_seeds = previous.get("holdout_seeds")
            if previous_seeds is None:
                previous_plan = Path(previous["panel"]) / "plan.json"
                previous_seeds = json.loads(previous_plan.read_text(encoding="utf-8"))["plan"]["seeds"]["holdout"]
            if set(seeds) & set(previous_seeds) and previous != claim:
                raise ValueError("Holdout seed was already opened for another panel/candidate")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ledger.open("x", encoding="utf-8") as stream:
            json.dump({"opened_utc": now(), "claim": claim}, stream, indent=2)
    except FileExistsError:
        previous = json.loads(ledger.read_text(encoding="utf-8"))["claim"]
        if previous != claim:
            raise ValueError("This holdout was already opened for another panel/candidate; its seeds are no longer independent for redesigns")


def run_panel(panel, phase, limit):
    plan, frozen = read_plan(panel), candidate_record(panel)
    previous = status(panel, plan)["phases"]["discovery"]
    if phase == "holdout" and (not previous["complete"] or previous["candidate_runtime_events"] or previous["infrastructure_errors"] or previous["candidate_budget_margin_failures"]):
        raise ValueError("Holdout needs completed discovery with candidate correctness and budget checks passing")
    incomplete = status(panel, plan)["phases"][phase]["incomplete_attempts"]
    if incomplete:
        raise ValueError("Interrupted attempts are retained and not silently retried: " + ", ".join(incomplete))
    pending = [job for job in plan["jobs"] if job["phase"] == phase
               and not (panel / "games" / job["id"]).exists()]
    if limit is not None:
        pending = pending[:limit]
    if phase == "holdout" and pending:
        seeds = plan["seeds"]["holdout"]
        stamp = digest(canonical(seeds))[:16]
        reserve_holdout(panel, frozen, ROOT / "test-results" / f"external-panel-holdout-exposure-{stamp}.json", seeds)
    for job in pending:
        read_plan(panel)
        candidate_record(panel)
        row = run_game(panel, plan, frozen, job)
        write_json(panel / "summary.json", status(panel, plan))
        print(json.dumps({"job": job["id"], "official_outcome": row.get("official_outcome"),
                          "eligible": row["eligible_mechanism_result"], "decisive_axis": (row["formal_result"] or {}).get("decisive_axis")}), flush=True)
        if "infrastructure_error" in row or row["invalid_runtime_events"][job["candidate_team"]] or not row["candidate_budget_margin_passed"]:
            break
    report = status(panel, plan)
    write_json(panel / "summary.json", report)
    return report


def child_protocol_fixtures():
    cases = {}
    for name in REGISTRY:
        fixtures = json.loads((EXTERNAL / name / "smoke-fixtures.json").read_text(encoding="utf-8"))
        if name == "sas-987":
            case = next(item for item in fixtures if item["name"] == "worker_adjacent_pearl")
            init = case["init"].replace("ID 2\n", "ID 8\n")
            turn = case["turns"][0].replace("A 2 ", "A 8 ")
            turn = turn.replace("NUM_MSGS 0\n", "NUM_MSGS 1\n18446744073709551615\nECHOES 0 0 0 0 0\n")
            turn = turn.replace("DRAGON_BODIES 2\n", "DRAGON_BODIES 4\n")
            lines = turn.splitlines()
            index = next(i for i, line in enumerate(lines) if line == "DRAGON_BODIES 4")
            lines[index + 3:index + 3] = ["A 0 2 5 W 1", "A 0 3 5 W 0"]
            turn = "\n".join(lines) + "\n"
            protocol = 3
        else:
            case = next(item for item in fixtures if item["name"] == "large_length_partial_body_unit_limit")
            init = case["init"].replace("ID 0\n", "ID 8\n")
            turn = case["turns"][0].replace("A 0 ", "A 8 ").replace("LENGTH 8\n", "LENGTH 4\n").replace("UNIT_COUNT 64\n", "UNIT_COUNT 2\n")
            protocol = 2
        cases[name] = {"name": "fresh_split_child_inherits_parent_protocol", "init": init,
                       "turn": turn, "protocol": protocol, "expected_action": "MOVE E"}
    return cases


def protocol_check(panel):
    plan = read_plan(panel)
    from unswbc.sandbox import SandboxBot, WasmPool
    cases, rows = child_protocol_fixtures(), {}
    for name, case in cases.items():
        pool = WasmPool([str(Path(plan["opponents"][name]["path"]) / "bot.wasm")], key=f"external-child-smoke-{name}")
        bot = SandboxBot(pool, init=case["init"].encode(), name="8")
        try:
            output = bot.ask(case["turn"].encode()).decode()
            actions = re.findall(r"^(?:MOVE [NESW]+|SPLIT \d+)$", output, re.M)
            stderr = bot.take_stderr().decode()
            rows[name] = {"output": output, "error": bot.error, "stderr": stderr,
                          "cpu_points": bot.live[0], "endturn_received": bot._framer.done,
                          "passed": bot.error is None and not stderr and bot._framer.done
                                    and bot.live[0] < plan["candidate_budget_margin_points"]
                                    and actions == [case["expected_action"]]
                                    and (("PROTOCOL 3\n" in output) if name == "sas-987" else "PROTOCOL " not in output)}
        finally:
            bot.stop()
            pool.close()
    result = {"tested_utc": now(), "matches_run": 0, "fixtures": cases, "results": rows,
              "passed": all(row["passed"] for row in rows.values())}
    write_json(panel / "child-protocol-smoke.json", result)
    if not result["passed"]:
        raise ValueError("Split child protocol smoke failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--out", required=True)
    plan.add_argument("--discovery-seed", action="append", type=int)
    plan.add_argument("--holdout-seed", action="append", type=int)
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
        seeds = {"discovery": args.discovery_seed or SEEDS["discovery"],
                 "holdout": args.holdout_seed or SEEDS["holdout"]}
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
