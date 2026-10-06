# Frozen external mechanism panel, 2026-10-06

`tools/external_panel.py` is separate from `compare.py`. Importing it, planning,
checking status and running its unit tests do not start games. Only `run` starts
matches, using the installed official `EngineModule` and metered `WasmPool`.
Repository scripts, hooks, native binaries and other opponent directories are
not accepted. The only opponents are the two source-and-WASM-pinned entries in
`external-benchmarks/FREEZE.json`: sas-987 and official-murder.

The map scope is **22 local files**, comprising 17 names observed in the current
100-game discovery sample and five supplemental maps: `arena`, `big_empty`,
`default_small`, `Colosseum`, `stronghold`. This does not establish the complete
current online pool, or byte identity between a local file and an online map
with the same name. The panel hashes and copies the actual local input files,
records all initial bodies and teams, and separates observed-name and
supplemental results.

Before any match, the fixed schedule is:

| Phase | Maps | Seed | Games |
| --- | --- | --- | --- |
| Discovery | Devil, Trophy, Islands, Maze | `2026100601` | 4 × 2 external opponents × both sides = 16 |
| Holdout | All 22 local files | `2026100691` | 68 observed-name + 20 supplemental = 88 |

The discovery selection follows the 100-game report's high-frequency
elimination failures on Devil/Trophy, Longest failures on Islands, and
Longest/Queen failures on Maze. It was made before executing panel games.
Each phase has a different seed. Fixed map/opponent/A,B order prevents selecting
only favorable completed matches. `--limit` takes the next unfinished jobs;
the remainder stays pending, and an incomplete phase is reported as partial.
Interrupted attempts are retained and not silently replayed or scored.

Prepare without any bot matches:

```
.venv\Scripts\python.exe -m unittest tests.external_panel_test -v
.venv\Scripts\python.exe tools\external_panel.py plan --out test-results/external-panel-20261006
.venv\Scripts\python.exe tools\external_panel.py protocol --panel test-results/external-panel-20261006
```

The `protocol` step adds fresh split-child process checks. The sas child starts
directly with inherited protocol 3, ECHOES and a 64-bit message; the murder child
starts with inherited protocol 2. These are standalone observation fixtures,
not matches. Existing frozen smoke packages already cover initial and successive
turns. The panel checks require a framed action, no runtime diagnostic and
points below 90M.

After the root agent has supplied a candidate and its functional checks pass:

```
.venv\Scripts\python.exe tools\external_panel.py freeze --panel test-results/external-panel-20261006 --candidate opponents/generalist-v1 --label generalist-v1
.venv\Scripts\python.exe tools\external_panel.py run --panel test-results/external-panel-20261006 --phase discovery --limit 8
.venv\Scripts\python.exe tools\external_panel.py status --panel test-results/external-panel-20261006
.venv\Scripts\python.exe tools\external_panel.py run --panel test-results/external-panel-20261006 --phase discovery
.venv\Scripts\python.exe tools\external_panel.py run --panel test-results/external-panel-20261006 --phase holdout --limit 8
```

Run one executor per panel. Each game runs to the official terminal; `--limit`
limits the number of complete games, not their rounds. Holdout requires completed
discovery with no candidate runtime/infrastructure errors and peak candidate
points below 90M. Candidate sources, quoted dependencies, the binary, maps,
official engine and driver fingerprints are checked again before every game.
Edited candidate sources require a new discovery panel. Once holdout starts,
an exposure ledger prevents the same sealed seeds being reused for a redesigned
candidate under a new independent-holdout claim.

Each game directory contains `result.json`, `raw.log` and the unmodified official
`raw.replay`. Results include the formal dataclass, normalized terminal scores,
decisive score axis, candidate side, seed, initial body positions, source/WASM/map
digests, runtime events and per-team CPU/memory peaks. The official winner is
retained even when an opponent fails; those games are excluded from eligible
mechanism wins. Engine stderr notices are conservatively marked for review and
also excluded. Normal bot LOG/INDICATOR output is recorded in the official
replay, not sent through this stderr callback. Two fixed-protocol, one-turn
engine interface checks confirm that distinction and that an unpaired portal
is rejected before any bot reply. They execute no candidate or external bot.

`raw.log` contains runner diagnostics and callback events, without console
colour formatting; it is not a full viewer event export. Use `raw.replay` for
trajectory analysis. The text-log loader does not generally remove ANSI escapes
and cannot reconstruct movement from the panel's diagnostic JSON lines.

Whole-match analysis can consume the raw replay directly, for example:

```
.venv\Scripts\python.exe tools\trajectory_metrics.py test-results/external-panel-20261006/games/discovery/sas-987/devil-2026100601-A/raw.replay --team A --out test-results/external-panel-20261006/games/discovery/sas-987/devil-2026100601-A/trajectory.json
```

Use the candidate side recorded in each result when interpreting curves. Verify
the replay's formal terminal and reconstruction quality; mean lead duration or
historical peak length does not override the terminal result. Raw replays allow
actual body updates and deaths to be audited. Requested movement costs and
visible-body counts are not substituted for executed resource accounting.

These weak policies do not establish 1700-level play. Their Queen splitting and
pursuit weaknesses make high win rates possible without countering mature Queen
defense or long-worker growth. The panel is a correctness and mechanism screen;
online confirmation against diverse independent opponents remains necessary.
No match had been run when this schedule and script were prepared.
