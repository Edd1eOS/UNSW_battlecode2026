# sas-987 public expansion / food baseline

Source: [sas-987/unsw_battlecode at the fixed commit](https://github.com/sas-987/unsw_battlecode/tree/1a3f3775353605f0da7142f276085e2764bca997),
committed 2026-10-03 17:24:09 UTC. `LICENSE` is the original MIT license,
copyright 2026 Sai Amrit. `PROVENANCE.json` records the original path, URL,
byte count and SHA-256 of every file. No upstream code was changed.

Full review covered `main.cpp`, all of `helper.hpp`, `bot.toml` and `LICENSE`.
The code contains ordinary in-memory containers and protocol stdin/stdout
operations. No file access, network access, process spawning, environment reads
or repository-script execution was found in the bot. This is a source review,
not a formal proof about all libraries or the sandbox implementation.

The policy splits two segments whenever legal, then prefers an adjacent pearl,
then a step that minimizes toroidal Manhattan distance to any visible pearl.
With no food it continues an ID-based exploration direction when possible.
Its normal step filter rejects kelp, portals and currently occupied adjacent
tiles. The trapped fallback merely selects a passable edge, so it can select a
portal with an unknown exit or an occupied destination.

The controller uses only legal current local vision and spawn metadata; it
does not obtain a hidden map. Its helper tolerates the initial protocol-2 frame,
requests protocol 3 at `ENDTURN`, then parses the next frame's `ECHOES` and
64-bit messages. The policy issues one-step moves; these are free under current
`ceil(L/4)` rules, but it does not use the additional free quota of longer units.

The fixed Queen receives no special protection. At length 4 with room in the
unit limit, the first branch outputs `SPLIT 2`, leaving her length 2 instead of
building the primary scoring unit. It also lacks predictive enemy-head safety,
obstacle-aware food routing and resource-spawn scheduling. This makes it useful
for independent expansion pressure, not a strong contemporary Queen strategy.
There is no verified association between this exact public commit and a rated
online submission or rating.

The metered smoke package covers early Queen splitting, adjacent visible food,
worker food pursuit, protocol 2 to 3 negotiation with a full-width message,
toroidal movement, a partly visible long body at the unit limit, and eight
consecutive forced corridor turns. See `smoke-results.json` for measured points
and raw outputs. No matches were run while freezing this baseline.
