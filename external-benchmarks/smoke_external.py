"""Compile audited, pinned external bots with the installed official judge.

This driver feeds local-vision protocol fixtures; it does not start a game,
import our bot, execute upstream scripts, or change any upstream source.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil

from unswbc import clangtool
from unswbc.sandbox import MAX_TURN_POINTS, SandboxBot, WasmPool

ROOT = Path(__file__).resolve().parent
DIM = 20


def frame(unit_id, body, *, round_num=1, units=2, length=None, pearls=(),
          enemies=(), protocol=2, edges=None, messages=()):
    """Only the 7x7 toroidal window and its visible edges enter the packet."""
    hx, hy = body[0]
    def facing(a, b):
        dx = (a[0] - b[0] + DIM // 2) % DIM - DIM // 2
        dy = (a[1] - b[1] + DIM // 2) % DIM - DIM // 2
        return {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}[(dx, dy)]
    window = [((hx + dx) % DIM, (hy + dy) % DIM)
              for dy in range(-3, 4) for dx in range(-3, 4)]
    visible = set(window)
    horizontal = [["."] * 7 for _ in range(8)]
    vertical = [["."] * 8 for _ in range(7)]
    if edges is not None:
        horizontal = [["w"] * 7 for _ in range(8)]
        vertical = [["w"] * 8 for _ in range(7)]
        # Existing ordinary body chains must agree with the supplied terrain.
        body_links = [link for chain in [body, *(b for _, b in enemies)]
                      for link in zip(chain, chain[1:])
                      if link[0] in visible and link[1] in visible]
        for a, b in [*edges, *body_links]:
            ax = ((a[0] - hx + 3) % DIM)
            ay = ((a[1] - hy + 3) % DIM)
            bx = ((b[0] - hx + 3) % DIM)
            by = ((b[1] - hy + 3) % DIM)
            if abs(ax - bx) + abs(ay - by) != 1:
                raise ValueError("fixture edge must be an ordinary visible step")
            if ax == bx:
                horizontal[max(ay, by)][ax] = "."
            else:
                vertical[ay][max(ax, bx)] = "."
    lines = [f"ROUND {round_num}", f"DIR {facing(body[0], body[1])}",
             f"LENGTH {length or len(body)}", f"UNIT_COUNT {units}",
             f"NUM_MSGS {len(messages)}", *map(str, messages)]
    if protocol == 3:
        lines.append("ECHOES 0 0 0 0 0")
    lines.extend(f"{x} {y} {int((x, y) in pearls)} -1" for x, y in window)
    parts = [("A", unit_id, p, int(i == 0), facing(body[0], body[1]) if i == 0 else facing(body[i-1], p))
             for i, p in enumerate(body) if p in visible]
    parts += [("B", enemy_id, p, int(i == 0), facing(enemy_body[0], enemy_body[1]) if i == 0 else facing(enemy_body[i-1], p))
              for enemy_id, enemy_body in enemies
              for i, p in enumerate(enemy_body) if p in visible]
    if len({p for _, _, p, _, _ in parts}) != len(parts):
        raise ValueError("overlapping fixture parts")
    lines.append(f"DRAGON_BODIES {len(parts)}")
    lines.extend(f"{team} {dragon_id} {x} {y} {direction} {head}"
                 for team, dragon_id, (x, y), head, direction in parts)
    lines.extend(" ".join(row) for row in horizontal)
    lines.extend(" ".join(row) for row in vertical)
    return "\n".join(lines) + "\n"


def scenario(name, unit_id, turns, expected):
    return {"name": name, "init": f"ID {unit_id}\nTEAM A\nMAP {DIM} {DIM}\nUNIT_LIMIT 64\n",
            "turns": turns, "expected_actions": expected}


def fixtures(name):
    head = (5, 5)
    short = [head, (4, 5)]
    long_body = [head, (4, 5), (3, 5), (2, 5), (2, 6), (2, 7)]
    if name == "sas-987":
        cases = [
            scenario("queen_length4_splits_to2", 0,
                     [frame(0, long_body[:4], units=1)], ["SPLIT 2"]),
            scenario("adjacent_visible_pearl", 0,
                     [frame(0, short, pearls=((6, 5),))], ["MOVE E"]),
            scenario("worker_adjacent_pearl", 2,
                     [frame(2, short, pearls=((6, 5),))], ["MOVE E"]),
            scenario("protocol2_then3_with_uint64_message", 0,
                     [frame(0, short, pearls=((6, 5),)),
                      frame(0, [(6, 5), head, (4, 5)], round_num=2,
                            pearls=((6, 4),), protocol=3,
                            messages=(18446744073709551615,))],
                     ["MOVE E", "MOVE N"]),
            scenario("toroidal_seam_pearl", 0,
                     [frame(0, [(0, 5), (1, 5)], pearls=((19, 5),))], ["MOVE W"]),
            scenario("large_length_partial_body_unit_limit", 0,
                     [frame(0, long_body[:4], length=8, units=64,
                            pearls=((6, 5),))], ["MOVE E"]),
        ]
    else:
        corridor = [((5, 5), (5, 4)), ((5, 4), (6, 4)), ((6, 4), (7, 4))]
        cases = [
            scenario("queen_length6_splits_to2", 0,
                     [frame(0, long_body, units=1)], ["SPLIT 4"]),
            scenario("queen_chases_adjacent_enemy_head", 0,
                     [frame(0, long_body[:3], enemies=((1, [(6, 5), (7, 5)]),))],
                     ["MOVE E"]),
            scenario("worker_head_pursuit_through_kelp_corridor", 2,
                     [frame(2, long_body[:3], edges=corridor,
                            enemies=((5, [(6, 4), (7, 4)]),))], ["MOVE N"]),
            scenario("sole_safe_step", 2,
                     [frame(2, long_body[:3], edges=[(head, (6, 5))])], ["MOVE E"]),
            scenario("large_length_partial_body_unit_limit", 0,
                     [frame(0, long_body[:4], length=8, units=64,
                            edges=[(head, (6, 5))])], ["MOVE E"]),
        ]
    ring = [(5, 5), (6, 5), (6, 6), (5, 6)]
    ring_edges = list(zip(ring, ring[1:] + ring[:1]))
    directions = ["MOVE E", "MOVE S", "MOVE W", "MOVE N"] * 2
    turns = [frame(0, [ring[i % 4], ring[(i - 1) % 4]], round_num=i + 1,
                   edges=ring_edges,
                   protocol=3 if name == "sas-987" and i else 2)
             for i in range(8)]
    cases.append(scenario("eight_consecutive_local_corridor_turns", 0, turns, directions))
    return cases


def verify_sources(directory):
    provenance = json.loads((directory / "PROVENANCE.json").read_text(encoding="utf-8"))
    for entry in provenance["files"]:
        data = (directory / entry["local_path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Frozen upstream source changed: {entry['local_path']}")
    return provenance


def run(name):
    directory = ROOT / name
    provenance = verify_sources(directory)
    digest = provenance["source_bundle_sha256"]
    stage = ROOT / "build-stages" / f"{name}-{digest[:24]}"
    stage.mkdir(parents=True, exist_ok=True)
    for entry in provenance["files"]:
        shutil.copyfile(directory / entry["local_path"], stage / entry["local_path"])
    cases = fixtures(name)
    (directory / "smoke-fixtures.json").write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    result = {"source_bundle_sha256": digest, "commit_sha": provenance["commit_sha"],
              "tested_utc": datetime.now(timezone.utc).isoformat(),
              "toolchain": "installed official unswbc.clangtool + metered WasmPool/SandboxBot",
              "unswbc_version": importlib.metadata.version("unswbc"),
              "upstream_scripts_executed": False, "matches_run": 0,
              "scenario_results": []}
    with (directory / "build.log").open("w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            wasm = clangtool.build(stage)
    artifact = directory / "bot.wasm"
    shutil.copyfile(wasm, artifact)
    result["wasm_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    pool = WasmPool([str(artifact)], key=f"external-smoke-{digest}")
    try:
        for case in cases:
            bot = SandboxBot(pool, init=case["init"].encode(), name=case["name"])
            replies = []
            try:
                for index, (turn, expected) in enumerate(zip(case["turns"], case["expected_actions"])):
                    output = bot.ask(turn.encode()).decode("utf-8", "replace")
                    actions = re.findall(r"^(?:MOVE [NESW]+|SPLIT \d+)$", output, re.M)
                    points, memory = bot.live
                    passed = (bot.error is None and bot._framer.done
                              and actions == [expected] and points <= MAX_TURN_POINTS
                              and (name != "sas-987" or "PROTOCOL 3\n" in output)
                              and (name != "official-murder" or "PROTOCOL " not in output))
                    replies.append({"turn": index + 1, "expected_action": expected,
                                    "output": output, "error": bot.error,
                                    "stderr": bot.take_stderr().decode("utf-8", "replace"),
                                    "endturn_received": bot._framer.done,
                                    "cpu_points": points, "memory_bytes": memory, "passed": passed})
            finally:
                bot.stop()
            result["scenario_results"].append({"name": case["name"], "turns": replies,
                                               "passed": all(t["passed"] for t in replies)})
    finally:
        pool.close()
    verify_sources(directory)
    result["passed"] = all(case["passed"] for case in result["scenario_results"])
    result["turns_tested"] = sum(len(case["turns"]) for case in result["scenario_results"])
    result["max_cpu_points"] = max(turn["cpu_points"] for case in result["scenario_results"] for turn in case["turns"])
    (directory / "smoke-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {'PASS' if result['passed'] else 'FAIL'}, {len(cases)} scenarios, "
          f"{result['turns_tested']} turns, max {result['max_cpu_points']} points", flush=True)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bots", nargs="+", choices=["sas-987", "official-murder"])
    args = parser.parse_args()
    os.environ["UNSWBC_WARM"] = "1"
    for bot_name in args.bots:
        run(bot_name)
