# KGTS external mechanism panel

`tools/oct7_kgts_panel.py` is a separate copy of the frozen Oct7 panel implementation. It does not monkey-patch, modify or extend the original registry, external FREEZE, runner or exposure ledger. It allows exactly one opponent: the GPL-isolated `external-benchmarks/kgts-protocol-adapted` derived from commit `b72ca9baac0e00071ac8013e238b01fe718d02b5`.

The original KGTS parser fails the official first protocol2 frame and remains frozen, ineligible, with its failure evidence. The adaptation changes only optional ECHOES parsing and reuse of the first tile line; strategy and project bytes remain identical. Original/modified source, GPL license, reviewable patch, compiled guest bytecode and official Python interpreter have separate hashes. See each isolated directory's `README.local.md`, `PROVENANCE.json`, `FREEZE.json` and protocol reports.

The new panel is **discovery only**: seed `2026100703`, all 22 frozen local maps, both candidate sides = 44 jobs. These are 17 names observed in the online100 series and five supplemental local maps; they are not a verified complete online map pool. There is no holdout, online strength claim or conversion to Elo. The external algorithm's competitive strength is unknown; the panel broadens collection, sonar-memory and phase-split mechanisms only.

## Runtime and strict identity

The C++ candidate is packaged and compiled with the official judge clang, frozen with all quoted-include dependencies and its WASM digest. Candidate packaging rejects dependencies from isolated external directories. The opponent uses official `SandboxPool`, aliased as `PythonPool`, with literal `['python', 'main.py']` and the registered source directory. It accepts no alternate executable, path, argument or opponent. Every source file is pinned; extra files, subdirectories and symlinks are rejected. After official guest compilation, every Python bytecode digest must match the external freeze.

`read_plan` verifies the plan checksum, exact registered original/adapted manifests, source and patch, Python interpreter WASM, entire bundled Python runtime root digest, official engine WASM, engine/Sandbox/turn/metering/project/clang modules, original runner identity, new runner identity, maps, fixed seed and full schedule. A rewritten checksum does not permit changing jobs or seed.

Rows retain the existing core schema: candidate/opponent identities, map hash and initial bodies, official engine and terminal result, raw replay/hash, runtime diagnostics, deaths including reason A, team points/memory peaks and eligibility. A Python interpreter digest is never mislabeled as an opponent-specific compiled WASM. Normal engine events are in the replay; `map_notices` contains the official notice stream. All formal outcomes survive runtime ineligibility. An infrastructure failure, candidate runtime event or candidate peak at/above 90M stops subsequent jobs; resuming the same failed panel is also rejected. External errors remain recorded and ineligible without erasing a formal outcome.

Existing `panel_trajectory.analyze_result` accepts the core row/replay schema. A separate KGTS comparison tool should call this runner's strict `read_plan` and compare Python source/interpreter/bytecode identity, rather than assuming the two-C++-opponent registry or a bot-specific WASM field. No existing comparator was changed.

## Functional verification

Eleven external protocol cases / fourteen frames pass, with eight valid protocol3 diagnostic outputs byte-identical to original KGTS. Peak sampled CPU is 60,362,814 points, including a 256-message budget input; this is not a universal bound. An independent short official EngineModule contract adds four frames confirming legacy parent input, PROTOCOL3 upgrade, immediate child inheritance and the next round.

The **new runner's own** `protocol` command repeats a single two-round EngineModule contract using its strict Python-pool factory and the engine's real spawn/init callbacks. Fixed other-dragon replies and intentional round2 termination make this a protocol contract, not a strength game. All four frames and exact compiled-bytecode checks pass. Eight tool unit tests cover fixed 44-job coverage, seed/holdout refusal, extra-source refusal, strict schedule verification, GPL packaging isolation, persistent candidate budget stop and formal Queen-first scoring. Official compilation/packaging of a minimal `int main(){return 0;}` fixture also passes; that fixture has never been played.

`test-results/oct7-kgts-runner-smoke-final` contains those functional artifacts and zero completed games. Their hashes and runner identity are summarized in `test-results/oct7-kgts-runner-functional-proof.json`. The functional fixture candidate is not a strength candidate; production experiments must create a fresh panel and freeze the intended C++ source there.

## Root-controlled execution

Only `run` starts matches; this work did not invoke it. Root can prepare a new candidate-specific panel:

```powershell
.venv\Scripts\python.exe tools\oct7_kgts_panel.py plan --out test-results\<new-kgts-panel>
.venv\Scripts\python.exe tools\oct7_kgts_panel.py protocol --panel test-results\<new-kgts-panel>
.venv\Scripts\python.exe tools\oct7_kgts_panel.py freeze --panel test-results\<new-kgts-panel> --candidate opponents\<frozen-cpp-candidate> --label <candidate-label>
.venv\Scripts\python.exe tools\oct7_kgts_panel.py status --panel test-results\<new-kgts-panel>
```

After root decides to start the predeclared discovery, the explicit command is `run --panel test-results\<new-kgts-panel> --phase discovery`. It runs jobs in fixed map/A/B order. Independent candidate-versus-KGTS panels may share this discovery seed for mechanism pairing; they are not independent holdout or candidate-versus-candidate games.

KGTS still treats Queen and workers alike, can split the Queen early, takes one step regardless of a larger free quota, normally avoids portals and gives a large heuristic bonus to unseen space. Its sonar food claims expire after 40 rounds. These intentional upstream behaviors remain available for mechanism testing; local compatibility and any future high win rate do not establish a mature external strength baseline.
