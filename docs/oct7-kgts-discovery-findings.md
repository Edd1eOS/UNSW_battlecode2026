# Oct7 KGTS additional discovery

All three independently frozen candidates completed 44 games against the same GPL-isolated public KGTS adaptation: seed `2026100703`, 22 local maps, both sides. The two strict paired comparisons each verify all 44 environment identities, initial bodies, raw replays, formal results, eligibility and gross resource ledgers. There are no missing, duplicate, unscored or failed analyses, recorded runtime faults, or candidate turns at/above the 90M margin. This is additional discovery, **not a holdout or a ladder-strength measurement**. No candidate-versus-candidate games were used.

| Candidate | Formal W–L | Own Queen alive | Peak candidate points | Peak KGTS points |
|---|---:|---:|---:|---:|
| V5 | 42–2 | 21/44 | 20,562,691 | 42,419,853 |
| Egress | 42–2 | 21/44 | 20,801,890 | 42,419,853 |
| Allocation | 43–1 | 19/44 | 26,503,683 | 42,032,205 |

The 22 local maps comprise 17 names observed in the previous online panel and five supplements; their bytes are not certified as the complete online pool. Separating these pre-existing groups is material: V5/Egress each win all 34 games on the 17 observed names; Allocation wins 33 and loses one. The extra overall Allocation win comes from turning **supplemental Stronghold A and B** into wins while losing **observed Trauma A**. Its 43/44 therefore does not establish an improvement on the online-relevant coverage.

## Whole game and common prefix

Each number below is a paired candidate-minus-V5 difference over **44** verified games. Median differences are calculated per game; they are not differences of marginal medians. Common prefix ends at the earlier terminal round for each pair, so it excludes later events rather than replacing the full-game result.

| Metric | Egress whole median / mean | Egress prefix median / mean | Allocation whole median / mean | Allocation prefix median / mean |
|---|---:|---:|---:|---:|
| Food minus paid steps | 0 / +0.11 | 0 / −1.30 | +6 / −17.18 | +6 / −11.77 |
| Retained team length since initial | 0 / −0.16 | 0 / −0.70 | +0.5 / +3.61 | −0.5 / +2.64 |
| Body capital lost on death | 0 / +0.27 | 0 / −0.59 | +3.5 / −20.80 | +3.5 / −14.41 |
| Own longest dragon | 0 / −1.00 | 0 / −0.98 | 0 / −0.48 | −0.5 / −0.95 |
| Own Queen terminal length | 0 / −1.16 | 0 / −1.16 | 0 / −2.00 | 0 / −2.34 |

Split birth is a transfer of existing body capital, not income. The verified accounting is retained growth = food − paid − death capital. Per-game aggregates can disagree with averages: Allocation has positive net income in 26 pairs and negative in 16, yet its large negative cases make the mean negative. Its retained length rises in 22 pairs and falls in 19. There is no uniform resource or retention improvement.

Egress has zero differences in every reported whole-game metric in 40/44 pairs; this does not assert byte-identical actions. The four changing cases are Big Empty A, Default Small B, Devil B and Trophy A. Own longest decreases in all four. Queen survival exchanges Big Empty A (V5 length58, Egress dead) for Default Small B (V5 dead, Egress length7); no observed-map Queen survival changes. Devil B gets net income +78 but loses retained length45 and longest13. Trophy A gets net income +160 over a longer game (497 versus416 rounds); at the common prefix, the overall Egress net income mean is negative. More whole-game food is not sufficient evidence of a better mechanism.

Allocation adds seven Queen deaths and avoids five, producing 21→19 surviving Queens. The seven new deaths are Arena A, Australia B, Autarky A, Big Empty A, Default B, Trauma A and UNSW A. The five avoided deaths are Australia A, Big Empty B, Default Small B and Tower Defense A/B. These are outcome facts; the comparison alone does not attribute them to a particular resource assignment or infer private opponent intent.

## Scoring evidence and acceptance

Both V5 losses are Stronghold: A has both Queens dead and loses longest33 to35; B loses24 to26. Allocation wins those games with longest30 to27 on A and52 to22 on B. The A flip occurs despite its own longest being three shorter than V5: opponent response and retention also change. Allocation's new Trauma A loss replaces a V5 Queen26 win with both Queens dead and longest8 to14; its total length36 exceeds the opponent's19 but cannot override the Longest criterion. Team net income is +13 relative to V5 while retained length is −11 and death capital is +24 there. More resources do not protect the primary score automatically.

The separate scoring-context reports retain all 44 games. In the nine Allocation pairs that reach Longest in both arms, own longest paired median is +12 and own-minus-rival margin median +19. That subset is selected after the outcomes; it cannot replace the main denominator or the Queen regression. Egress's corresponding 13-game subset has median0 and mean−1 for both own longest and margin.

The compatibility/identity/budget gate passes. This panel does **not** pass a general adoption gate: Egress supplies no new formal wins and no net Queen improvement; Allocation's one extra win masks a newly observed-map loss, lower Queen survival and mixed resource effects. Neither result establishes 1700-level strength, an Elo gain, opponent-private strategy recovery, or a successful unseen-seed holdout. Further acceptance must preserve the separate primary-score and resource/retention checks across independently declared external opponents and genuinely untouched seeds; it must not select an easier opponent or a favorable score-axis subset after observing results. Root maintains the central final acceptance ledger; this report does not alter the earlier gates or exposure records.

## External identity and evidence

The public source is [Sumitforces/unsw-battlecode-kgts at b72ca9b](https://github.com/Sumitforces/unsw-battlecode-kgts/tree/b72ca9baac0e00071ac8013e238b01fe718d02b5), licensed GPLv3. Original first-protocol2-frame failure remains frozen. The isolated adaptation only changes optional ECHOES parsing and first tile reuse plus its modification notice; `main.py`, template and project bytes match upstream. It uses legal local observations and sonar-memory claims, treats Queen and workers alike, splits early, takes one step despite larger free allowances, and normally avoids portals. Those source-level coverage limits remain; a high win rate against it is not evidence of a mature ladder benchmark. No GPL code was copied into any candidate or production source.

Pinned identities:

- Commit: `b72ca9baac0e00071ac8013e238b01fe718d02b5`.
- Adapted source bundle: `256184b8b291638a9137dfc18465c392bb80dad0f4177c165c1eec488f6dc0fe`; adaptation patch: `4fe39e8c24dfdd8f449f9989e727957d7bd95403410590dfd3a858b26424b368`.
- Official engine WASM: `26e68680e45eb0f221db702aead9eefde776c2ad2ba066f4ddf8c12500c6a546`.
- Official Python interpreter WASM: `48342178e7ca73775b90aacd0899efed906d79bff79b961360aefe76b5f78125`; it is not a bot-specific WASM.
- Frozen KGTS comparator: `b1260292584508405186fde82a65258ccbbc6fdd8ca29a8e8e463a8e07f4c800`; separate runner: `7b591916f76b1e2cb3fcabb1fb9dd752fa7faf3149684fddbac9ad3bb9f73662`.

The three plan records, candidate source/WASM freezes, all132 result/raw bindings, full Python source/bytecode identity, runtime bundle/module hashes, strict comparisons, scoring contexts, original/adapted GPL records and protocol evidence are bound in `docs/oct7-kgts-evidence-manifest.json`. The shared collector's bytes are explicitly included along with the wrapper. The collector binds evidence; the independently frozen comparator performs the full scoring/ledger checks.

Reproduction commands run only offline analysis; they launch no matches:

```powershell
.venv\Scripts\python.exe tools/oct7_kgts_compare.py --baseline test-results/oct7-v5-kgts-panel --candidate test-results/oct7-egress-kgts-panel --out <new-egress-report.json> --cache <new-cache>
.venv\Scripts\python.exe tools/oct7_kgts_compare.py --baseline test-results/oct7-v5-kgts-panel --candidate test-results/oct7-allocation-kgts-panel --out <new-allocation-report.json> --cache <new-cache>
.venv\Scripts\python.exe tools/oct7_scoring_context.py --comparison <report.json> --out <new-context.json>
```

The frozen reports are `test-results/oct7-kgts-egress-vs-v5.json`, `test-results/oct7-kgts-allocation-vs-v5.json` and their `*-scoring-context.json` files. All formal outcomes are reported, including all five loss records (three distinct map/side cases). Map/side repeats and shared opponent seeds are correlated; geometric coverage is not useful food discovery or guaranteed reachable space. Same seed does not force identical opponent responses after a candidate changes its action.
