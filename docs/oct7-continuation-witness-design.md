# Continuation witness V1

This independent candidate copies frozen V5 and changes only `planner.hpp`. It does not include the separate Certainty, Exploration, Investment, Cooperation or Emergency changes. Root preregistered it as a new discovery arm; no matches or uploads were run by this implementation task.

`Future.unresolved_depth`, initially −1, records the maximum **actually simulated known prefix on a branch that reaches an unresolved boundary**. Outside vision, an unresolved portal, or exhausted search budget records the current recursion depth. The unobserved next step is not executed or counted. Recursion merges this field independently: a longer fully finite branch cannot donate its depth to a different nearer unresolved exit. A confirmed full horizon keeps the old early return, its grade3 and witness −1. Exhaustion records only depth reached, not the horizon.

The old `depth`, same-continuation `next_free_food`, OR flags, grades, candidate pruning, node budgets, physical simulation, payment, body memory, contact/birth tiers, capital dominance and worker utility are preserved. The new field is compared before old utility only for Queen/reserve/last-unit candidates with grade2 after their contact, grade and possible-birth tiers tie. All worker and grade3/1/0 comparisons retain the old ordering. The indicator adds `unresolved_depth` for auditing.

Existing uncertain candidates that skip continuation receive0: no known future step was verified. This includes a directly unresolved action or incomplete starting body. It differs in provenance from a recursion boundary at depth0 but neither proves a move into the unknown. Their existing uncertainty flags and grades are unchanged.

This is candidate-level evidence, not a proof of a global exit, future income or survival. Foreign occupancy is frozen within the inherited search, enemies can respond, and budget exhaustion can mark a branch without demonstrating an actual terrain exit. The bounded maximum is sensitive to the inherited search order. All such uncertainty remains explicit. The change does not reserve a path for teammates or enlarge the observation window.

## Verification

Five scenario suites pass under the official judge clang and Sandbox:

- `witness_continuation_test.cpp`: finite six-step branch plus an immediate unknown exit records witness0; a real three-step known prefix to outside records3; portal records2; one-node search budget records1; known full horizon remains grade3/witness−1; ordinary-worker and confirmed-grade rank exclusions.
- `witness_physics_test.cpp`: copied V3 pending-body, paid affordability, capital dominance, protected-last and fresh-child reverse assertions.
- `witness_birth_test.cpp`: copied V5 possible-birth geometry and the isolated legal STAR observation; its confirmed depth8 action remains ES.
- `witness_capital_test.cpp`: the existing r86 local capital fixture keeps the free action and verifies the eight-step continuation.
- `witness_closed_route_test.cpp`: the finite leaf cannot outrank the known full-horizon candidate because of possible birth risk.

These are model assertions executed as official WASM, not independent actual-engine matches. The unchanged official protocol runner additionally passes35 cases /42 input frames, including portal two-frame body tracking and expected reverse-neck exclusions. Peak sampled candidate cost is8,495,831 points, below the90M margin. This is a sampled protocol cost, not a universal upper bound or strength result.

Source/test/staging/WASM/protocol identities and the seven unchanged V5 source files are recorded in `test-results/continuation-witness-v1-correctness.json`. Its protocol record's source hash uses the existing filename-plus-bytes method; the panel canonical record uses workspace paths with per-file SHA/byte lengths. Both bind the same candidate bytes and their distinct hash methods are labeled.

Reproduction launches no matches:

```powershell
.venv\Scripts\python.exe tools/check_cpp.py tests/witness_continuation_test.cpp tests/witness_physics_test.cpp tests/witness_birth_test.cpp tests/witness_capital_test.cpp tests/witness_closed_route_test.cpp
.venv\Scripts\python.exe tools/verify_portal_tracking.py opponents/generalist-continuation-witness-v1 --out <new-protocol.json>
```

The candidate remains an experiment until root runs its separately declared external discovery and applies the primary-score/resource/retention gates. No local fixture is claimed to rescue the original game after an action diverges.
