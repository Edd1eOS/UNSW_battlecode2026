# Bounded expansion and length retention proxy

This deterministic behavioral proxy keeps frozen v66's Queen and movement
policy. It tests a colony that stops ordinary expansion early and retains
worker length; it does not reconstruct any named online opponent and does not
implement feeding or promise greater Queen growth.

The only policy change is the ordinary worker split gate. An ordinary split
requires round <60, own-team units <8, no previous split by this worker, and
the worker never having reached length6. Reaching length6 permanently disables
its ordinary splitting even if it later shrinks. All existing v66 split checks
also remain. Descendants can each expand once subject to the same round/count
gate. Emergency rescue splits remain possible, as do baseline worker attacks,
collector roles, multi-step movement, and Queen rescue behavior.

All information is official per-dragon input and legal memory. There is no
hidden full-board access, opponent unit count, map hardcoding, resource transfer
protocol, or sonar communication. Queen still competes for food through v66's
existing policy; reduced splitting alone may help a longest worker without
feeding Queen. Costs follow the 2026-10-01 `ceil(initial length / 4)` free-step
rule; v66's existing paid Queen escape and attack behavior remain.

Top-level source dependencies come from `opponents/v66-queen-threat-buffer`
(baseline hash `42162e3c924cb13407aa7810c8f8d1fbe7f9a06ae77514ef47804bda2c4a4f61`).
`forage.hpp` adds one sticky worker flag and the ordinary split restrictions;
`main.cpp` adds a provenance comment. Other copied files are unchanged. Treat
this as a phenotype stress test, not evidence of a counter to a named team.
