# KGTS: isolated protocol adaptation

This GPLv3 external mechanism derives from [KGTS commit b72ca9baac0e00071ac8013e238b01fe718d02b5](https://github.com/Sumitforces/unsw-battlecode-kgts/tree/b72ca9baac0e00071ac8013e238b01fe718d02b5). The full upstream LICENSE and original source are preserved separately in `../kgts-gplv3`. The original fails official initial protocol2 parsing and is not a valid match baseline.

This directory changes only `source/helper.py`: accept an optional ECHOES line; when it is absent, preserve that line as the first of the 49 tiles. The helper also carries a dated modification notice. `source/main.py`, `main_actual_template.py` and `bot.toml` are byte-identical to the pinned upstream files. `helper-protocol.patch` shows every changed line. No strategy is transferred into our candidates or production bot; this is a separately licensed external executable.

Official Python SandboxPool compiled the sources to guest bytecode. Eleven protocol cases / fourteen frames pass, including a continuous protocol2-to3 sequence, both initial and inherited child protocols, uint64 messages, phase splits and a 256-message budget sample. Eight valid protocol3 diagnostics produce exactly the same outputs as the original. Maximum sampled CPU is 60,362,814 points, below the 90M margin; this is not a worst-case bound.

An additional actual official EngineModule contract executes two rounds with fixed replies for the other dragons: initial worker2 reads protocol2, returns SPLIT2 and PROTOCOL3, child3 immediately receives ECHOES and acts, then both receive protocol3 next round. This adds one case / four frames, with measured peak 28,564,584. The synthetic fixture intentionally stops after those rounds; its terminal result is not a benchmark game or strength observation. Source/fixture/replay hashes are in the reports and FREEZE.json. No matches or uploads were run.

Python has no bot-specific WASM. Execution identity binds source, guest bytecode and the official metered Python interpreter WASM (`48342178e7ca73775b90aacd0899efed906d79bff79b961360aefe76b5f78125`). Source-specific identity is separately recorded in PROVENANCE.json/FREEZE.json. Engine and Sandbox module bytes must also be frozen when a new panel starts.

Its strategy remains limited: no separate Queen role, early Queen splitting, one-step movement despite larger free sprint quota, normal avoidance of portals, optimistic space bonus at the view boundary, 40-round sonar food memory and no dedicated enemy-head model. Its strength is unknown. It expands collection/messaging/split mechanisms, not proof of a 1700-level opponent. A new panel must register only this adapted identity with unused discovery seeds; the original and already frozen two-opponent panels are unchanged.

The minimal official Python interface is:

```python
from unswbc.sandbox import SandboxPool, SandboxBot

pool = SandboxPool(["python", "main.py"],
                   cwd="external-benchmarks/kgts-protocol-adapted/source",
                   key="<16-hex-digit-seed>-b")
bot = SandboxBot(pool, init=b"ID 1\nTEAM B\nMAP 20 20\nUNIT_LIMIT 64\n", name="1")
try:
    reply = bot.ask(round_block)  # Actual engine-produced legal local bytes.
    points, memory = bot.live
    error, stderr = bot.error, bot.take_stderr()
finally:
    bot.stop()
    pool.close()
```

Use one pool per team and a distinct SandboxBot per engine spawn, retaining it across turns. SandboxPool performs official guest compilation; do not launch upstream Python in the host. It is the official Python pool (called `PythonPool` by the new panel's alias), whereas the C++ candidate uses WasmPool. Strictly freeze every file under the source directory and fixed `python/main.py` arguments, so no new file can silently enter the SandboxPool copy.

Reproduce protocol-only checks with `smoke_adapted.py` and `engine_protocol_smoke.py` in this directory. The latter is a short contract fixture, not a match. Existing frozen runners, external manifests and exposure ledgers must not be altered to add this mechanism.
