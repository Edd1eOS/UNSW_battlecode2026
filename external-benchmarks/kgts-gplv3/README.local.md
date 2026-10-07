# Frozen KGTS source: incompatible original

This isolated external mechanism is from [Sumitforces/unsw-battlecode-kgts](https://github.com/Sumitforces/unsw-battlecode-kgts/tree/b72ca9baac0e00071ac8013e238b01fe718d02b5), commit `b72ca9baac0e00071ac8013e238b01fe718d02b5` (2026-09-25). The full upstream GPLv3 [LICENSE](LICENSE) is preserved. No source is copied into our candidates or production bot. `source/` retains every Python file selected by upstream `bot.toml`, including its unused template. Upstream README files are retained separately from this local assessment.

The repository was cloned bare with hooks disabled; fixed-commit blobs were exported without checkout filters. All three bot Python files were read before execution. They import only local helper and Python standard modules. Host I/O is protocol stdin/stdout plus `sys.exit`; no network, file-opening, external process, dynamic import, eval or exec operation was found. No upstream installation, build script or hook was run. Bot code was not imported or run in the host Python interpreter.

## Compatibility result

**Do not register the original in a match panel.** Official initial protocol2 input causes `helper.py:599` to raise `TypeError: SonarEchoes.__init__() missing 2 required positional arguments: 'enemy' and 'enemy_head'`, with no action or ENDTURN. The parser unconditionally reads an ECHOES line and instead consumes the first tile. Official [wire protocol](https://game.battlecode.au/docs/protocol) supplies ECHOES only after a prior PROTOCOL3 reply; initial dragons default to legacy protocol, and split children inherit their parent's protocol. This is also confirmed by the installed official engine's `types.h`, `protocol.cc` and `actions.cc`.

Official SandboxPool successfully compiled the unchanged sources to guest bytecode. Seven isolated hypothetical protocol3 inputs passed: upgraded parent, inherited child with uint64 inbox, early Queen SPLIT2, middle-phase worker SPLIT3, late-phase no split, 64-map long partial body at unit limit, and toroidal food. Peak measured live CPU was 31,126,298 points, below the 90M check margin. The initial failing process has unavailable live CPU/memory after exit; recorded zeros are not a measured zero-cost turn. There is no valid protocol2-to3 transition for the original, so these diagnostics do not establish match compatibility or strength.

This Python program has **no bot-specific WASM binary**. Identity consists of exact source, guest bytecode, and the official metered Python interpreter WASM. `PROVENANCE.json`, `smoke-results.json` and `FREEZE.json` bind those separately. No match was run.

## Mechanism coverage and limits

The source supplies a distinct collection mechanism: visible-food BFS, one ordinary step per action, flood-fill with an unobserved-boundary bonus, 40-round sonar pearl memory, and phase-based splitting. It uses legal local observations and received messages; it has no omniscient board. An unobserved boundary is treated as attractive space by its heuristic, not established physical safety. Portals are avoided during normal planning but may be chosen by its trapped fallback.

Queen and workers share the phase split rule: before round300, length5+ may split2; until425, length10+ may split3. There is no dedicated Queen capital or enemy head contact model, and no use of larger dragons' free sprint quota. These are benchmark coverage limits, not claims about a private competitor or a measured rating. Repeatedly splitting the Queen can limit retained Queen length. Runtime bounds were sampled, not proven for all messages or maps.

A future pure protocol adaptation could retain this algorithm in a **new GPL-isolated directory**, support the optional initial ECHOES line, and receive a distinct source/bytecode freeze and compatibility report. Only after that could a newly declared external panel register it with unused discovery/holdout seeds. Existing frozen runners and panels remain unchanged. The original is stopped at this compatibility failure; it is not counted as an additional independent valid strength opponent.

Reproduce the eight protocol diagnostics without playing matches:

```powershell
.venv\Scripts\python.exe external-benchmarks\kgts-gplv3\smoke_kgts.py
```

The driver is local assessment code; it runs upstream code only inside the official Python WASM sandbox. It intentionally records the first failure and the separate hypothetical protocol3 diagnostics.
