# Possible split-tail attacks: Generalist V4

The frozen online Generalist V3 sample is all 17 maps against three external opponents: 51 games, 13 wins and 38 losses, platform v19 / submission 18674. Of 35 Queen deaths, 27 were enemy head collisions. At the Queen's latest own decision, the eventual attacker was an existing visible head in 13 cases, an existing unseen head in 11, and a newly split child created later in that same round in 3. This is a post-match causal classification, not a claim that all deaths were avoidable. Evidence: `test-results/v3-queen-ro/queen-head-deaths.json` and `queen-findings.json`.

## Three observed same-round births

Rounds below show replay's zero-based round, followed by the UI round.

| Official replay | Queen's recorded action | Later opponent action and collision |
| --- | --- | --- |
| [risq-v, Devil, M1249235](https://game.battlecode.au/battles/1249235), raw 185 / UI 186 | Queen 1 at (22,10), `MOVE N` to (22,9); `direct_contact=0` | Enemy parent 173 splits 2. New child 212 has head (22,8), neck (22,7), then `MOVE S` into the Queen. Parent head was unseen, but three parent body segments were visible. |
| [risq-v, Trophy, M1249246](https://game.battlecode.au/battles/1249246), raw 31 / UI 32 | Queen 0 at (14,7), `MOVE SS` to (14,9), collecting one pearl; `direct_contact=0` | Visible enemy parent 8 splits 2. Child 10 starts at old tail (14,10), neck (13,10), then `MOVE N` into the Queen. |
| [STAR, Around UNSW, M1249302](https://game.battlecode.au/battles/1249302), raw 30 / UI 31 | Queen 0 at (28,32), `MOVE E` to (29,32); `direct_contact=0` | Enemy parent 35 splits 2. Child 42 starts at (30,32), neck (31,32), then `MOVE W` into the Queen. Only these two parent body segments were visible; its head (32,33) was outside the legal window. |

Official turns are sequential: an entire `MOVE` completes before another unit acts. New children are appended to that round's turn list. Therefore these are attacks after our endpoint was chosen, not enemies moving between our sprint microsteps.

## Bounded legal-vision model

`opponents/generalist-v4/born_threat.hpp` considers visible enemy non-head segments whose visible predecessor is another non-head segment of the same parent. A visible successor pointing into a segment excludes it as a possible tail. Missing successors do **not** prove a tail, and an observed partial chain does **not** prove the enemy's total length. If following the candidate tail's predecessor chain reaches a visible head in fewer than four segments, that candidate cannot legally split child 2 while leaving parent length 2 and is excluded.

For each remaining possible tail, the model reverses the last two segments and maps the new length-2 child's one free step. Its old neck and other visible segments of that stationary parent remain blockers. Ordinary toroidal edges and already known portal destinations are used; unresolved portals produce uncertainty without fabricated target cells. Other units may move before the new child acts, so their current occupancy is not treated as a reliable shield. This is a possible attack hypothesis, not a safety oracle; it does not cover every split size or larger newborn sprint.

The API returns `same_round_possible` for parent IDs greater than our current ID and separate `next_round_possible` flags for earlier parents. **Next-round flags are currently not used in decisions.** Parent split eligibility, its true tail, and whether it chooses to attack may remain unknown.

## Candidate ranking and limits

V4 retains the existing `imminent` meaning: a visible enemy head can reach a cell in one step. This is a reach observation, not certainty that the enemy will attack. `birth_possible` is a separate flag. Queen, reserve, and last-unit candidates with continuing-route evidence prefer no such contact, then possible birth contact, then existing visible-head contact. Alternatives are ranked rather than forbidden; when all are exposed, a legal escape remains selectable. Ordinary workers receive only an extra 0.35 soft risk for a possible same-round birth. A threatened free move cannot suppress a paid escape through the capital-dominance guard. The existing no-candidate loss-minimizing fallback is unchanged.

**The ordering is a strong tradeoff:** contact tier precedes continuation grade. A no-birth candidate with a fully searched finite route of depth 2 or more (grade 1) can outrank a possible-birth candidate with the full search horizon (grade 3). Grade 0 has no protected contact preference, but that alone does not guarantee selection of a long-lived route. Static finite closure may change when another unit moves; it may also be a real trap. V4 does not distinguish those cases here. In the STAR fixture the original `E` and new `ES` both reach the full horizon, so that particular comparison avoids this shorter-route tradeoff. Source remains frozen; this risk is reported rather than changed after discovery started.

The [Citadel Around UNSW case M1249270](https://game.battlecode.au/battles/1249270), raw 205 / UI 206, has a different limit: Queen (8,29) chooses `WS` to (7,30) with no visible enemy segment. Unseen enemy 249 at (4,30), length 5, uses `EEE`—two free steps and one paid step—to collide. V4's birth model does not solve this unseen-head problem, nor the broader dynamic exit-blocking problem. Unknown terrain is not a guarantee of safety.

## Verification and frozen bytes

The reconstructed STAR observation contains only its actual 49 visible tiles, visible border edges, and 20 visible body segments. In a fresh isolated process V4 outputs `MOVE ES`, ending at (29,33) with `direct_contact=0` and `possible_birth_contact=0`; both microsteps are legal. Historical Memory is not inherited. This is local mechanism evidence, not a counterfactual replay win or a claim about rating strength.

Official judge C++ checks pass for the actual STAR geometry, partial chain versus exact length, known short parents, visible successors, child neck, kelp, known/unresolved portals, parent ID order, friendly exclusion, ranking, and preservation of paid escape. Copied V3 physical assertions also pass. Metered protocol verification passes **40 cases / 47 frames**, including the original 35 / 42, four prior actual/boundary portal cases, and STAR. Peak measured CPU is **8,414,313** points; no matches were run by these tests. Reports are `test-results/generalist-v4-portal-protocol.json`, `generalist-v4-extra-physics-protocol.json`, and `generalist-v4-freeze.json`.

- Canonical source bundle: `41a8c9fdc7d1dd188d1cd7d74a9b4eeac44633c498f043d4d5d7492017848c2f`
- WASM: `f1f125c1be67b8e0bf0e8d9b7240214a62aa62189324c285c7155fc9bd02d4ec`
- Planner: `1177853080210cb06bea7c603c904020079ff0da58f2afa97c99b3ce1c829709`
- Birth header: `2502a92f41f1056eff0145bb8e7cbcc814ace1f1864f6508a578b556d1ac4128`

V4 is a separate local candidate copied from frozen V3. Only its planner and new birth header differ; the root bot and V3 remain unchanged. No source changes are permitted after this freeze. Weak external benchmarks can test mechanisms, but do not establish competitive online strength.

## Independent V5 ordering correction

V4 remains frozen with the strong tier tradeoff described above. A separate V5 changes only ordering: existing visible-head contact tier, then continuation grade, then possible same-round birth contact within that grade, then utility. Thus a finite grade-1 route without a possible birth cannot defeat a full-horizon grade-3 route merely because the latter has a possible birth. The author's permanent-leaf fixture selects the full-horizon route in V5; the original STAR `E` and replacement `ES` have equal full-horizon evidence, so the birth comparison still selects `ES` there. This repairs the identified ordering defect without changing the birth hypotheses, physical simulation, or V4 bytes.

On 2026-10-06 at 14:34 UTC, the same five additional protocol inputs pass for frozen V5: actual portal children 192/398 select `S`/`SE`, known border-portal partial lengths 2/50 both select `W`, and the actual STAR observation selects `ES` to (29,33). Their peak is 5,642,337 points. Together with the root's 35-case / 42-frame portal report, V5 has **40 cases / 47 frames passed**, peak **8,414,441**. These are zero-match protocol checks and still do not prove final-game survival or competitive strength.

- V5 canonical source bundle: `39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`
- V5 WASM, independently matched against the root freeze: `7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`
- Extra protocol report: `test-results/generalist-v5-extra-physics-protocol.json`, SHA256 `80419951897392520f4a7e57eb0702e7a4bfa1300ec0cd7fc3b3a11c4a43b9d0`
- Author's selection/physics checks: `test-results/generalist-v5-functional-checks.json`
