# Short swarm behavioral proxy

This deterministic opponent models a test phenotype observed in selected online
replays: many short units, single-step resource collection, and adjacent head
collisions. It does not reconstruct Manny, Shannon, or any other private bot.

Queen uses frozen v66 unchanged. Workers prioritize an ordinary adjacent enemy
head (Queen first; N/E/S/W breaks equal ties). Otherwise they split exactly two
segments whenever `can_split(2)` allows it and their complete remembered body has
a visible tail with a currently empty ordinary exit. There is no expansion cap
beyond the official own-team unit limit. A split consumes the parent's action.

Workers otherwise issue exactly one free movement step. They greedily rank
routes entirely within current vision for present pearls, visible spawn
countdowns at most 12, and reachable unknown frontier, with a visit penalty.
Known visible portal landings can participate; unresolved/out-of-view portals
are tried only when no modeled visible step exists. With no exit, the policy
still emits one movement and can die. It has no worker survival lookahead or
friendly endpoint reservation, so head trades and crowding remain possible.

All information comes from official per-dragon observations, own identity,
length, own-team count/limit, map dimensions, and memory of previously seen
terrain/body/visits. No map files, hidden opponent counts, or sonar protocol are
used. Workers never spend length on extra steps; Queen retains v66's paid-step
policy under the 2026-10-01 `ceil(initial length / 4)` free-step rule.

Dependencies are top-level files copied unchanged from
`opponents/v66-queen-threat-buffer` (baseline source hash
`42162e3c924cb13407aa7810c8f8d1fbe7f9a06ae77514ef47804bda2c4a4f61`).
Run comparisons with fresh seeds and both sides; proxy wins do not establish a
counter to any named online team.
