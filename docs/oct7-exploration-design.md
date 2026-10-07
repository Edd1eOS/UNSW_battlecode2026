# Oct 7: bounded worker exploration

This experiment isolates one resource-exploration defect in frozen Generalist V5. It changes neither Queen policy nor investment/population scoring. Unknown information remains an opportunity, not expected food or proven safety. No engine match or platform upload was run by the analysis and verification described here.

## Complete causal reconstruction

The independent external SAS Portals B game is `test-results/external-panel-v5-20261006/games/holdout/sas-987/portals-2026100695-B/`, seed 2026100695. Its official terminal score is Queen 3 versus 3, Longest 3 versus 3, Total 9 versus 11: V5 loses Total. Its three original units 1/3/5 all survive, collect zero pearls, pay zero sprint segments, and finish length 3. They visit 183/183/187 distinct head positions, respectively; this is not merely a four-cell loop. SAS is a public independent mechanism baseline, not evidence of competitive rating strength.

The official replay was decoded, then reduced chronologically to each unit's actual current observation: only its 49 toroidal visible tiles, current visible body parts with public segment directions, visible border edges, own length/direction/unit count, and observed countdowns enter the input. Hidden full bodies/terrain are used only to reconstruct those visible protocol fields. Each unit starts at round 0 with empty Memory; no hidden or retrospectively invented Atlas is injected. The unchanged V5 inspector uses the original observe/choose/remember sequence and records legal first-direction alternatives.

Both workers were reproduced continuously through all 500 own turns, with **500/500 chosen moves equal to the recorded actions for each worker**, not just selected examples. Worker 3 sees an unresolved portal at its head on 42 legal first-step opportunities; worker 5 sees 51. All 1,000 selected moves have the full known continuation depth 6. No portal opportunity is selected. The current known-target graph is dry on 372/500 and 330/500 turns, respectively; it reports near-spawn opportunities on the other 128/170 turns. Of the 42/51 unresolved portal opportunities, 41/43 have a dry target graph. Actual pearls eaten are zero throughout. A reconstruction correction applies the official countdown decrement at every roundStart; resets alone emit replay countdown events. The previous claim that every target graph was dry is withdrawn. Exact move equality and portal-opportunity counts are unchanged.

For example, worker 3 at replay round 35, head (19,2), has `W` into an unresolved portal (grade 2) and `S` with a full known depth-6 continuation (grade 3); it chooses `S`. At round 159, head (22,9), the unresolved `E` portal again loses to a depth-6 `N` move. Unknown mouths are genuinely present in legal vision, and past legal observations have not resolved their partners. The current lexicographic continuation ordering therefore suppresses information gathering even after extensive dry travel. It does not imply the unseen exit is safe or rich.

Machine-readable evidence and hashes are in `test-results/exploration-ro/v5-portals-exploration-proof.json`, SHA256 **285a3a8d1849dbd23a2927abc7a1471acdf30f602fd9d3675be2737449a56d36**. It includes the inspector/reconstruction source hashes, complete input/log hashes, action-equality checks and all counts. The decoded replay SHA256 is `1ca58951a2cae7abacdb0951532673580567ea067d2670d8c6dd6703d213a097`.

## Narrow candidate and interface

`opponents/generalist-exploration-v1/` is an independent complete copy of frozen V5. Only a new `exploration.hpp` and planner integration differ. The model exposes `eligible(ct, memory, reserve, last_food, budget)` and unique current-head `PortalOpportunity{direction, portal_id}` records. Their observable path cost is exactly one first step; no exit distance, resource yield or occupancy is guessed. Portal IDs are deduplicated.

The override is available only to a harvest worker with all these conditions:

- At least 24 turns without food, complete remembered own body, and exploration cooldown expired.
- More than one own unit, and neither Queen nor sticky reserve.
- No visible enemy segment, including headless bodies that could produce a split head.
- No reachable known current pearl or observed near-spawn target in the original V5 graph.
- The selected baseline move has neither current food nor a visible next-free-food estimate, and is not a split or sacrifice.

It may select one unresolved portal **free first step**, preserving its uncertain grade 2. Each attempt starts a 24-turn cooldown. It never emits guessed follow-up movement through an unseen exit, never uses the incoming reverse direction at length at least 2, and never labels unknown terrain safe. The existing pending-body reconciliation preserves the off-vision old neck after arrival. Known food, visible opponents, paid movement, split decisions, protected roles and normal no-candidate fallback retain the original V5 pipeline.

This first candidate does not introduce a multi-target resource field or new competitive allocation rule. Existing V5 resource goals remain unchanged; the exploration/known-income distinction is explicit. A later field could expose unique observed resource-cell records with known route cost and a separate uncertain frontier/portal opportunity list, then apply visible-rival/friendly allocation discounts without turning unknown opportunities into income. That is a separate mechanism requiring separate tests and seeds, not part of this freeze.

## Verification and reproduction

The universal causal fixture has a verified length-2 four-cell ordinary ring and one visible unresolved portal with an unobserved partner. V5 chooses the ring for both Queen and worker. Exploration V1 still keeps the Queen in the ring, but permits the eligible dry worker's one-step portal attempt. Additional scenarios preserve reserve/last units, cooldown, recent food, reachable pearls/near spawns, enemy headless-body risk, partial-body caution, and the proven old-neck reverse veto. All copied V5 physical model assertions pass when compiled and executed with the official judge WASM toolchain. These are assertions of the C++ simulation, not an actual engine execution against replies; the root's separate four installed-engine contracts check execution order/payment/collision independently.

The actual worker-3 round-0-through-35 protocol prefix also passes. Its first 35 actions still equal V5; at round 35 it selects `MOVE W` into the visible portal, with `food=0`, `paid=0`, and `exploration_opportunity=1`. **No later historical packet is fed after this divergent decision.** This proves the local decision change without inventing a counterfactual subsequent body or game outcome. The corrected countdown prefix was rechecked separately in `test-results/generalist-exploration-v1-corrected-prefix-protocol.json`; all 36 frames pass against the same frozen WASM.

Official metered verification passes **41 cases / 83 frames**, peak **8,518,933 CPU points**: original 35/42, four prior actual/boundary portal cases, STAR birth case, and the actual 36-frame prefix. Reports are `test-results/generalist-exploration-v1-portal-protocol.json`, `generalist-exploration-v1-extra-physics-protocol.json`, and `generalist-exploration-v1-freeze.json`.

From the repository root, use the installed official toolchain; do not run external repository scripts:

```powershell
.venv\Scripts\python.exe tools/oct7_reconstruct_portals.py
.venv\Scripts\python.exe tools/check_cpp.py tests/inspect_exploration_v5.cpp --input-fixture test-results/exploration-ro/v5-portals-unit3-input.json > test-results/exploration-ro/v5-portals-unit3-trace.log
.venv\Scripts\python.exe tools/check_cpp.py tests/inspect_exploration_v5.cpp --input-fixture test-results/exploration-ro/v5-portals-unit5-input.json > test-results/exploration-ro/v5-portals-unit5-trace.log
.venv\Scripts\python.exe tools/check_cpp.py tests/exploration_causal_test.cpp tests/exploration_test.cpp tests/exploration_physics_test.cpp
.venv\Scripts\python.exe tools/verify_portal_tracking.py opponents/generalist-exploration-v1 --out test-results/generalist-exploration-v1-portal-protocol.json
```

The cold reconstruction tool reads the raw official replay through the existing trusted decoder; it does not require ignored decoded caches or other analysis scripts. Two independent cold exports were checked byte-for-byte against all three corrected 500-frame input fixtures. The standalone tool SHA is recorded in the proof JSON. Importing it performs no export. It uses official maxGap>0 for beds and rejects any sonar-containing replay instead of inventing an empty inbox. Input fixtures terminate with `ENDGAME`; this is required by the helper's complete-stream parser. The proof JSON provides expected action equality and hashes. Inspector checks are not strength measurements or per-turn CPU benchmarks; the metered protocol reports supply the latter sample measurements.

## Frozen bytes and limits

- Canonical source bundle: `32e6bf7f5ece9c8d19b44cbe06dc1813e37d321112ea148c7e2d28f5f8ccc3a4`
- WASM: `6fb834c127737afcabf29f1e579e17e3c727962da0702b3db6de0631ea1f40cb`
- Planner: `6d398f13f701049ac8aa708330a977a44935aab3d2a8e95bcf6a0d15cb35ca62`
- Exploration header: `7f0bcc190b13fed236c9cc87c3cf3737be08ee6cc3da704ee918119176b9c410`

Unknown exits can still contain an unseen dragon or an unsuitable chamber. A small free information step limits immediate capital spending, not mortality. The no-visible-enemy guard does not eliminate off-vision attacks. This candidate does not solve multi-unit resource assignment, spawn camping, general dynamic corridor control, or hostile swarms. Queen's already certified safe four-cell ring remains a valid scoring strategy; the experiment does not globally lower Queen threat avoidance or continuation grades. No map names, opponent names, private opponent code, hidden terrain, or hidden resource state participate in decisions.
