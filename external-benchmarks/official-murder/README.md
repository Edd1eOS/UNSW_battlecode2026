# Official murder head-pursuit mechanism

Source: [UNSW CPMSoc's murder example at the fixed commit](https://github.com/unswcpmsoc/unswbc/tree/79e22e7950e334711574bcc1166b3973153ccc4f/examples/murder),
committed 2026-10-02 04:39:14 UTC. `LICENSE` is the original repository MIT
license, copyright 2026 UNSW CPMSoc. `PROVENANCE.json` maps the copied filenames
to their original repository paths and records their byte counts and SHA-256
digests. No upstream source was changed.

Full review covered `main.cpp`, all of the actual example's `helper.hpp`,
`bot.toml` and the root license. No file access, network access, process spawning
or environment reads were found in the bot. The timing experiment is commented
out. Its observable I/O consists of protocol input and action/log/indicator
output. Repository scripts and build hooks were not used.

It first splits four segments whenever legal. Otherwise it performs BFS inside
the current 7x7 window across ordinary non-kelp edges, treating bodies as
obstacles but allowing head cells. It orders visible enemy heads by unwrapped
Manhattan distance and takes the first step toward a reachable head. With no
reachable target it shuffles ordinary directions with a fixed PRNG seed and
takes an immediately unoccupied passable step. That fallback may cross a portal
without validating its exit. A trapped unit tries a legal split or emits no
movement action.

Its older helper stays on protocol 2, which the current judge supports. It
does not request protocol 3 or consume `ECHOES`. One-step movement remains legal
and free under current `ceil(L/4)` rules; the policy does not exploit larger
free movement allowances. It uses local observations, not hidden terrain or
full-board opponent state.

This is an official illustrative mechanism, not a strong current competitor.
It does not protect the fixed Queen: she may split at length 6 to leave length
2, and the head-pursuit policy can deliberately ram a visible enemy head with
her. It has no pearl objective and emits extra BFS logs. Victories over it
primarily exercise pursuit, body obstacles and collision response; they do not
establish superiority over Queen-preserving teams.

The metered smoke package covers early Queen splitting, adjacent enemy-head
pursuit, a forced kelp corridor to a visible head, a sole legal unoccupied step,
a partly visible long body at the unit limit, and eight consecutive protocol-2
corridor turns. Raw outputs and measured points are in `smoke-results.json`.
The head-pursuit frame demonstrates the selected command, not safe execution
of that collision. No matches were run while freezing this baseline.
