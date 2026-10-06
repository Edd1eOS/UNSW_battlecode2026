# Frozen external mechanisms, 2026-10-06

These are public implementations written outside this project. Their original
source bytes and licenses are preserved, with immutable upstream paths and
SHA-256 digests in each `PROVENANCE.json`. They are independent mechanism
baselines, not evidence of a particular current leaderboard rating.

| Baseline | Fixed upstream commit | Coverage | Material gap |
| --- | --- | --- | --- |
| [sas-987](sas-987/README.md) | `1a3f3775353605f0da7142f276085e2764bca997` | Aggressive small splits, visible-food pursuit, dispersal | Splits the fixed Queen at length 4; no Queen preservation |
| [official murder](official-murder/README.md) | `79e22e7950e334711574bcc1166b3973153ccc4f` | Local BFS pursuit of visible enemy heads | Splits and attacks with the Queen; no food objective |

The smoke driver uses the already installed official `unswbc.clangtool` and
metered `WasmPool`/`SandboxBot`. It verifies source digests before and after
compilation, stages the complete frozen bundle under a digest-bearing directory,
and feeds only 7x7 visible-window packets. Repository scripts, hooks and build
systems are not executed. `bot.wasm`, `build.log`, `smoke-fixtures.json` and
`smoke-results.json` are generated artifacts; upstream `main.cpp`, `helper.hpp`,
`bot.toml` and `LICENSE` remain unchanged.

Reproduce the protocol checks with the installed workspace environment:

```
.venv\Scripts\python.exe external-benchmarks\smoke_external.py sas-987 official-murder
```

No matches are part of this preparation. Successful smoke tests establish that
these particular protocol frames compile and produce framed actions within the
judge budget. They do not establish win rate, full-game survival, unknown-portal
safety, or compatibility with every possible observation. The harness is not a
game simulator: the adjacent-head attack case intentionally records an action
that would collide with a visible head.

Official sandbox smoke results (`unswbc==1.2.7`, 2026-10-06):

| Baseline | Scenarios / framed turns | Result | Highest measured turn points |
| --- | --- | --- | --- |
| sas-987 | 7 / 15 | All pass, no stderr or runtime error | 3,582,025 / 100,000,000 |
| official murder | 6 / 13 | All pass, no stderr or runtime error | 6,384,075 / 100,000,000 |

Victories against these weak Queen policies must not be presented as evidence
of beating the current Queen-preserving competitive field. Neither this set nor
the in-house short-swarm / queen-grow proxies covers strong passive Queen
defense, coordinated threats, efficient free sprints or high-quality long-worker
growth. A stronger claim needs a separately selected diverse online panel,
independent holdout seeds and fixed acceptance criteria. Unknown private code is
not recovered by these sources.
