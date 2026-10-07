# Oct 7 exploration discovery: two Queen deaths

This is a read-only causal audit of the frozen exploration candidate against the independent public SAS mechanism baseline. Both Portals games win on Longest after both Queens die; neither win proves competitive strength. The candidate and its runner were not edited, and this audit starts no matches.

All rounds below are the replay's zero-based `roundStart` index. Sources are `test-results/oct7-exploration-panel/games/discovery/sas-987/portals-2026100701-A/` and the corresponding `-B/`, seed 2026100701. Candidate source bundle remains `32e6bf7f5ece9c8d19b44cbe06dc1813e37d321112ea148c7e2d28f5f8ccc3a4`, WASM `6fb834c127737afcabf29f1e579e17e3c727962da0702b3db6de0631ea1f40cb`.

## A: a later friendly body seals the next exit

Queen 0, length 3, dies by self collision at round 183. This is a forced last-turn fallback, not a normal move simulator accepting an occupied cell.

At round 182 her actual body is `(14,3),(14,2),(14,1)`. North is her neck; east/west are kelp. The only free first step is south to `(14,4)`. The planner assigns it depth 8, risk 0, `direct_contact=0`, and `exploration_opportunity=0`. Its static continuation starts west through `(13,4)` and `(12,4)`. Friendly reserve 11 is already visible at `(13,5)` with visible body at `(14,5),(14,6)`; its complete length-8 body is known to its own process, not supplied to the Queen.

After the Queen moves, unit 11 legally chooses `MOVE NW`: `(13,5) -> (13,4) -> (12,4)`. Its new neck `(13,4)` seals the Queen's only remaining exit. At round 183 the Queen at `(14,4)` sees north occupied by her neck, east kelp, and south/west occupied by unit 11. Length 3 cannot split. `GENERALIST FALLBACK loss_min no_confirmed_escape` emits `MOVE N`, and the engine records `S`. The selected ordinary move at round 182 was legal at execution time; its next-turn continuation was conditional on the friendly body staying fixed.

There is also a legal paid local alternative at round 182: `MOVE SW` ends at `(13,4)`, length 2, with static continuation grade 3. The current capital guard dominates it with the free grade-3 move because neither has enemy risk. This is not proof that spending would win: unit 11's recorded `N` would then hit the Queen unless its decision also changes. A cooperative exit reservation, or a separately verified emergency investment, is required. At unit 11's turn, a split retaining its head/neck can leave `(13,4)` free; this is a proposal to simulate jointly, not a claim that the child or subsequent match survives.

The Queen's earlier round-180 west alternative has a known depth-8 route, but the later friendly head is outside her view then. At round 181 it is still four cells away in y. A policy cannot claim to predict the actual unseen friend; it can only price the known narrow passage or retain a safe loop. The directly observable coordination failure is unit 11 cutting an already-visible Queen's sole movement exit.

## B: exploration feeds a worker into a portal-dependent passage

Queen 1, length 3, dies by a friendly head collision at round 146. The colliding actor is own reserve 30; both die with reason `H`. This is not enemy pressure.

Unit 30 starts round 143 at `(23,4)`, length 6, with a known safe south route of depth 6. Its eligible exploration override chooses unresolved `W`, `exploration_opportunity=1`, and arrives at `(8,9)` on a pearl, length 7. At that decision its legal view also contains the Queen at `(20,5)`; the initial decision has no information about the hidden destination's resources or occupancy.

At round 144 it chooses `NE`, eats two pearls and grows to length 9. At round 145 it chooses `S`, eats one pearl and reaches `(9,9)`, length 10, now a sticky reserve. The observed ordinary chamber is a four-cell path `(8,9) -> (8,8) -> (9,8) -> (9,9)`, whose bottom connection is a portal rather than an ordinary cycle. Old remote tail segments remain correctly tracked; all inspector simulations have a complete body.

At round 146 unit 30's north neighbor is its own neck `(9,8)`, and east/south edges are kelp. West is the now-known portal, with destination `(22,4)` outside its current view. There is **no safe non-portal MOVE** and no resource return on this turn. The inherited pipeline emits the sole unresolved escape `MOVE W`, depth 0/outside 1. This is not the dry-worker override at round 146, and hard-banning the return portal at this point would force a different loss.

The Queen has acted earlier in the round: `(21,4) -> (22,4)` by `MOVE E`. Her depth-8 plan has risk 0. She sees body segments of ally 30 at `(23,4),(24,4),(24,3)` but no head, so the existing head-only risk map adds no warning. Unit 30 sees no current Queen at its remote exit. Its known portal step collides with her head. No hidden current position is injected into either reconstructed input.

A bounded counterfactual is possible from the Queen's legal round-146 packet: `N` to `(21,3)` and `S` to `(21,5)` are also known grade-3 routes. Either first endpoint is disjoint from unit 30's recorded portal arrival `(22,4)`. This establishes a possible one-round avoidance prefix, not a full-match victory. An arrival warning derived from visible friendly body crossing a portal, or a short-lived historical traffic record, could change this tie without forbidding worker escape.

## General mechanisms to test separately

**Visible protected-unit exit preservation.** For a worker candidate, construct its actual predicted post-action body, using the existing old-body/payment contract. Re-evaluate the currently visible friendly Queen's legal first-step exits. Treat outside terrain, unresolved portals and incomplete search as uncertain; do not call them closed. If the candidate changes a confirmed available exit into zero ordinary movement exits using only kelp, the Queen's visible body and this worker's predicted body, record `seals_protected_exit`. Compare an equally viable move or a jointly verified split first; when all worker moves seal it, use a loss-aware rescue comparison rather than pretending a free escape exists. Do not infer the other dragon's total length from observed segments. A Queen may split to wait, so this is a movement blockage certificate, not a certain-death label. It fits a bounded next-turn candidate check and leaves certified Queen rings unchanged.

**Portal traffic uncertainty within equal continuation grades.** A protected endpoint adjacent to a visible portal mouth can receive a possible-arrival flag when a later friendly body's segment points through that mouth but its head is absent. A recently observed friendly head/Queen can alternatively produce a short-TTL reachable-position envelope over remembered terrain. These are possible traffic, never current occupancy or certain enemy reach. Prefer a same-grade route without this flag; preserve escape when no such route exists. Do not demote all portals or all off-vision cells. The B Queen has such same-grade alternatives; the B worker's final return does not.

**Separate capital budget for information attempts.** A free step risks the worker's whole length, not only its paid-step cost. A low-capital scout limit, or joint move/split investment that creates a real small scout, limits this exposure. The newborn's real location, occupancy and turn order must be simulated; a split cannot place it at the parent's portal mouth. After arrival, distinguish a sustainable ordinary loop from a passage whose only continuation is a remote portal. Growth can remove available turns for a loop, and automatic pearl consumption cannot be wished away. This gate would reject some profitable unknown destinations; it cannot certify an unknown chamber before entry. Keep exploration opportunity and actual income separate, and evaluate the income/survival tradeoff on fresh paired external seeds.

Sonar is not a remote occupancy API: the official `sonar.cc` casts a directional ray through portals, stops at the first body/wall, delivers a value only to a hit dragon, and returns category counts on a later observation. `game.cc` casts it after the movement, so a return-ray sent on the fatal crossing is too late. A prior-round traffic handshake could help if the ray reaches an ally, but has latency, occlusion, direction ambiguity and failure-to-deliver limits. It must not replace collision validation or use absent echoes as proof of safety.

These are separate designs, not changes to Exploration V1. The minimal directly evidenced change is visible Queen exit preservation; portal traffic and scout capital are additional hypotheses with separate acceptance tests.

## Reproduction and proof

`tools/oct7_exploration_death_audit.py` decodes the official replay and exports each selected actor's continuous legal observation stream from its initial spawn or actual split birth. It applies every round's countdown decrement before reset events, and uses only the current toroidal 7x7 tiles, current visible parts/directions, visible edges, and public own fields. Diagnostic global bodies are separate metadata, never input. These games contain no sonar messages.

The inspector `tests/inspect_exploration_death.cpp` runs the unchanged frozen candidate's observe/choose/remember sequence through those packets. Full MOVE steps and SPLIT child sizes reproduce exactly: A Queen **184/184**, A worker 11 **215/215**, B Queen **147/147**, B worker 30 **57/57**. The C++ inspector is compiled and executed with the official judge WASM toolchain; this is model/protocol execution, not a counterfactual engine match. Recorded deaths and terminal scores come from the actual official replay.

```powershell
.venv\Scripts\python.exe tools/oct7_exploration_death_audit.py --replay test-results/oct7-exploration-panel/games/discovery/sas-987/portals-2026100701-A/raw.replay --out-dir test-results/oct7-exploration-causal-ro/A --ids 0 11
.venv\Scripts\python.exe tools/oct7_exploration_death_audit.py --replay test-results/oct7-exploration-panel/games/discovery/sas-987/portals-2026100701-B/raw.replay --out-dir test-results/oct7-exploration-causal-ro/B --ids 1 30
.venv\Scripts\python.exe tools/check_cpp.py tests/inspect_exploration_death.cpp --input-fixture test-results/oct7-exploration-causal-ro/A/causal-unit0-input.json
.venv\Scripts\python.exe tools/check_cpp.py tests/inspect_exploration_death.cpp --input-fixture test-results/oct7-exploration-causal-ro/B/causal-unit30-input.json
```

The exact replay, input, trace, exporter and inspector hashes are recorded in `test-results/oct7-exploration-causal-ro/proof.json`. The optional `queen-predeath-states.json` files are explicitly global diagnostics with copied bodies; their radius-4 `near` list is not legal vision and must not be used as a bot packet. No later historical packet is supplied after any counterfactual decision.
