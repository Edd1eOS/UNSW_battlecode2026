"""Meter dense resource fields using official legal observation frames, no match."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verify_candidate as verifier


def dense_fixtures():
    spec = importlib.util.spec_from_file_location("foraging_frames", ROOT / "external-benchmarks/smoke_external.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DIM = 64
    body = [(20, 20), (19, 20), (18, 20), (18, 21), (19, 21), (20, 21), (20, 22), (19, 22)]
    pearls = tuple((x, y) for y in range(17, 24) for x in range(17, 24) if (x, y) not in body)
    return [{"name": f"dense-resource-field-id{identity}-L8",
             "init": f"ID {identity}\nTEAM A\nMAP 64 64\nUNIT_LIMIT 64\n",
             "turns": [module.frame(identity, body, round_num=100, units=10, pearls=pearls)],
             "constructed": True} for identity in (0, 2)]


if __name__ == "__main__":
    original = verifier.fixtures
    verifier.fixtures = lambda: original() + dense_fixtures()
    out = ROOT / "test-results/foraging-v1-dense-protocol.json"
    verifier.run(ROOT / "opponents/generalist-foraging-v1", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    report["additional_fixture_driver_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "fixtures": len(report["fixtures"]),
                      "peak": report["max_measured_cpu_points"], "matches_run": 0}))
