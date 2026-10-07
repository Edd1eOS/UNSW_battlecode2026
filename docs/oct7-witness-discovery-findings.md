# Continuation witness V1 discovery

The independent frozen Witness candidate completed the preregistered main external discovery: two fixed external programs,22 local maps, seed2026100701 and both sides,88 games. V5 and Witness each played the external programs separately; there were no candidate-versus-candidate games. All88 paired environments, initial bodies, replays and formal results verify;47 pairs are runtime-eligible and have complete gross food/payment ledgers. The other41 pairs remain in the formal account and are excluded from mechanism deltas. There are no unmatched/duplicate keys or analysis failures. No candidate runtime fault, infrastructure failure, or90M margin failure was recorded. The holdout remains unopened.

| Scope | V5 | Witness |
|---|---:|---:|
| All88 formal outcomes | 87W1L | 85W3L |
| Same47 eligible pairs | 46W1L | 45W2L |
| Queen alive in those47 | 25 | 27 |
| Peak candidate points across88 | 27,476,943 | 21,834,069 |

The effective47 consist of44 SAS games and only3 official-murder games. Recorded opponent errors make the remaining41 unsuitable for reliable strength/mechanism comparison; those are not erased or converted into candidate achievements. The22 local map files include17 previously observed online names and5 supplements, not a certified complete online map pool. This is discovery at an exposed seed, not a holdout, ladder benchmark or Elo estimate.

## Full game versus common prefix

Each delta is Witness minus V5, calculated per verified pair. Whole-game totals retain both actual terminal times. Common prefix stops at the earlier terminal round and never feeds a divergent candidate the original replay's later observations.

| Metric across47 pairs | Whole median / mean | Common-prefix median / mean |
|---|---:|---:|
| Food minus paid steps | −1 / −46.04 | 0 / −19.17 |
| Net retained body growth since initial | 0 / −4.28 | +1 / +2.62 |
| Body capital lost on death | −8 / −41.77 | 0 / −21.79 |
| Own Queen length | 0 / +1.98 | 0 / +0.36 |
| Own longest dragon | −1 / −6.06 | −2 / −6.11 |
| Splits | −1 / −17.32 | 0 / −8.06 |

Split birth is transferred capital, not income. Whole-game net income rises in16 pairs, is unchanged in7, and falls in24. Retained growth rises in23, is unchanged in8, and falls in16; lower death losses do not compensate for the average income reduction. At the common prefix, net income has20 positive/7 zero/20 negative pairs. The seven pairs with all reported whole-game metric deltas zero do not imply byte-identical actions.

SAS alone has whole/prefix net-income means−49.11/−20.68 over44 pairs. The three eligible murder pairs have−1/+3. The overall result cannot be attributed to a broad second-opponent improvement.

Witness adds Queen deaths on SAS Arena A, Default A and Stronghold A, and avoids them on Arena B, Devil A, Islands A, Trophy B and UNSW A: net25→27. This survival improvement coexists with lower income and Longest, so neither an absolute Longest decline nor an extra Queen survival alone decides adoption. In the12 pairs where both arms have equal Queens and reach the Longest rule, own longest and own-minus-rival margin each have paired median−3.5 and mean−13. In the13 pairs decided by Queen in both arms, Queen margin has median0 and mean+4. These are descriptive subsets selected by terminal scoring; they do not replace the47-pair main denominator.

## Defeats and one recorded decision chain

- **SAS Portals B is unchanged:** both sides finish with Queen3 and Longest3; V5 and Witness each lose on Total9 versus11 after500 rounds. It is a Total-axis defeat, not Queen/Longest defeat.
- **SAS Colosseum B is a new eligible defeat:** V5 finishes with both Queens dead and wins Longest45 versus3; Witness is eliminated at round index82, with the opponent31 units/total77. It has no candidate or opponent runtime error. Its whole-game net-income delta is−481 and retained delta−91; the common prefix still has net income−6, retained−38 and Queen length−9, so duration alone does not explain the early capital loss.
- **Official-murder Arena B is a new formal but ineligible defeat:** Witness is eliminated at round index176. The candidate has0 recorded runtime events; the opponent has119. This loss remains in85W3L but supplies no eligible mechanism delta.

In Colosseum B, the first recorded action difference across **both teams'** action sequence is action index659, round index69, Queen1: V5 chooses`ENNN` (indicator depth0/outside1), while Witness chooses`E` (depth7/outside1/unresolved_depth7). Before that recorded action, the action sequence agrees. The new candidate then has depth8 actions at70–72. At73 it chooses`E` with depth0/outside1/unresolved_depth0 and dies on another dragon's body (`O`). Its last unit16 later chooses fallback`S` at82 and dies head-to-head (`H`), ending the game. V5 instead transfers Queen capital through successive splits after70 and continues to the Longest win.

These are actual actions/indicators/deaths, not reconstructed private intent or proof of a safe alternative at73. The trace does not enumerate the candidate's alternate action certificates. It illustrates the limitation: a longer known prefix in a frozen local occupancy model is not a timed escape commitment, future growth, or protection against later occupation. The local witness fixtures passed their stated checks; this complete game does not validate the heuristic's global benefit. Source-bound extracted events are in `test-results/oct7-witness-defeat-trace.json`.

## Acceptance and frozen evidence

Identity, protocol/model checks and sampled budget gates pass. The efficacy gate does not: both whole-game and common-prefix net income fall on average, both-arm Longest context regresses, and a new eligible elimination defeat appears. Queen survival improves, but this experiment does not establish an acceptable tradeoff for adoption. Keep it as a documented hypothesis rather than promoting it on fixture success or weak-opponent win count. No new experiment or holdout was opened by this analysis.

Frozen source bundle: `9e83a504d762694da0609ee861670fabbf1a0eb31d005081f0879c79d3380f5a`; WASM: `ef215add2c07f053301497a814cc60e1dd127d940195e9d7a655e20459b64242`. Only planner.hpp differs from V5. The original scope,5 official-WASM model suites,35 protocol cases/42 frames and8,495,831-point sampled protocol peak remain in `docs/oct7-continuation-witness-design.md` and `test-results/continuation-witness-v1-correctness.json`; they are not actual strength matches.

The frozen strict report is `test-results/oct7-witness-discovery-compare.json`; scoring context is `test-results/oct7-witness-scoring-context.json`. Both bind their sources and dependencies; the collector records each frozen plan/candidate/result/raw hash. All88 formal outcomes and all41 ineligible cases remain available. Same map/seed/side is correlated, and changed candidate actions change opponent responses. These new reports do not alter earlier discovery snapshots, candidate sources or the central acceptance/exposure ledger.

```powershell
.venv\Scripts\python.exe tools/oct7_compare_external.py --baseline test-results/oct7-v5-panel --candidate test-results/oct7-witness-panel --out <new-report.json> --cache <new-cache>
.venv\Scripts\python.exe tools/oct7_scoring_context.py --comparison <new-report.json> --out <new-context.json>
```

These reproduction commands only analyze recorded games; they start no matches.
