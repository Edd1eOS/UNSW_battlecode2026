# KGTS paired additional-discovery audit

`tools/oct7_kgts_compare.py` is an independent copy of the frozen
`oct7_compare_external.py`. It never launches an engine or a bot. Each arm is
a separate C++ candidate panel against the same GPL-isolated,
protocol-adapted KGTS source. The two candidate bots never play one another.
This is additional mechanism discovery, with no holdout or online-strength
claim. KGTS strength is unknown.

```powershell
.venv\Scripts\python.exe tools/oct7_kgts_compare.py --baseline test-results/oct7-v5-kgts-panel --candidate <new-KGTS-candidate-panel> --out test-results/oct7-kgts-paired.json --cache test-results/oct7-kgts-compact-cache
```

Both panels pass the new runner's strict `read_plan` and `candidate_record`
before results are analyzed. The candidate's current source, staged source
and WASM must still match its freeze. Each result must match its job,
candidate record, frozen map and initial bodies, full environment record and
full KGTS record. Across paired arms, the full Python opponent record must
match: all source-file hashes and sizes, all guest `.pyc` hashes, the official
interpreter WASM, original/adapted freezes, patch, provenance, commit,
license, literal argv and source path. KGTS has no bot-specific WASM; the
comparator does not invent or request one.

The original strict `panel_trajectory.analyze_result` and raw-replay decoder
remain the accounting implementation. `pair_key`, `coverage_frames`,
`compact_report`, `analyze_compact`, `view` and `summarize` have identical ASTs
to the origin, verified by a test. Whole-match and common-terminal-prefix
metrics stay separate. Food/payment deltas require both complete strict
gross ledgers and runtime eligibility. Missing gross data retains verified
net-body changes. Split transfer and newborn capital are not food income.

All formal results, runtime errors and unscored infrastructure attempts are
retained even when identity or replay validation refuses a mechanism pair.
Unstarted jobs and incomplete attempt directories are listed explicitly.
The report can be partial; missing/duplicate keys cannot count as additional
successes. Cache keys bind result bytes, raw replay bytes and decoder/runner/
comparator dependencies. Dependencies also bind the frozen origin comparator.

Validation: 19 comparator tests plus 8 existing KGTS runner tests pass, without
starting matches. They cover real strict-ledger integration with a Python
record containing no bot WASM, each source/bytecode/interpreter identity
component, formal retention on mismatch, infrastructure attempts, explicit
missing jobs, cache tampering, split capital, paid steps, and different
terminal rounds. An offline invocation against the 0-match packaging smoke
panel passes strict real plan/candidate validation, reports both arms as
44 scheduled/0 completed, and lists all 44 missing jobs. That invocation is
only a packaging contract check. The packaging candidate is never a strength
benchmark. Frozen code/test/dependency hashes and the output binding are in
`test-results/oct7-kgts-compare-freeze.json`.

## Parallel pool isolation

Read-only inspection of the installed official `unswbc/sandbox.py` shows:

- `SandboxPool` constructs a unique temporary root and separate ready queue,
  gate and closed flag (lines 1335 and 1360). `close` stops its own spares and
  removes only its own root (line 1392).
- Every `Sandbox` gets a new `Store` and `SharedMemory` (lines 384–386), with
  separate bot pipes/state. The pool key seeds RNG; it is not a live-pool
  cache key.
- The process cache shares compiled Engine/Module objects under a lock
  (line 273), not a bot Store or memory. Disk compilation cache writes use
  temporary files and replacement (line 292). Python/system code mounts are
  read-only.

Consequently, equal seed/team keys across panels do not share live bot state
or close one another's pools. Keep those keys equal for the paired random
seed control. Use distinct panel directories and a new pool per game, as the
frozen runner already does. Bound process concurrency to avoid host memory
and latency pressure; warm official compilation caches before timing-sensitive
runs. Shared host cache/startup effects do not make the two gameplay paths
identical, and action changes still change opponent responses.

This concurrency conclusion is a source audit of the installed official
module, not a new parallel gameplay experiment. Its exact module hash is
recorded in the comparator freeze proof.
