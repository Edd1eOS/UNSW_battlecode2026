"""Run reproducible sandbox matches against the unchanged official starter."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "test-results"
OUTPUT.mkdir(exist_ok=True)
cli = Path(sys.executable).with_name("unswbc.exe" if sys.platform == "win32" else "unswbc")
results = []
for map_name in ("arena", "default", "portals", "big_empty", "stronghold", "dilemma"):
    for side in ("A", "B"):
        bots = ["bot", "opponents/starter"]
        if side == "B":
            bots.reverse()
        command = [str(cli), "run", f"maps/{map_name}.map", *bots,
                   "--sandbox", "--seed", "17", "--no-replay"]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        log = run.stdout + run.stderr
        (OUTPUT / f"{map_name}-{side}.log").write_text(log, encoding="utf-8")
        winner = re.search(r"team ([AB]) wins after (\d+) rounds", log)
        outcome = ("win" if winner[1] == side else "loss") if winner else (
            "draw" if re.search(r"draw after \d+ rounds", log) else "error")
        if run.returncode or "sandbox error" in log or "no valid action" in log:
            outcome = "error"
        result = {"map": map_name, "side": side, "seed": 17, "outcome": outcome}
        results.append(result)
        print(result, flush=True)
(OUTPUT / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print({key: sum(r["outcome"] == key for r in results) for key in ("win", "loss", "draw", "error")})
if any(r["outcome"] == "error" for r in results):
    sys.exit(1)
