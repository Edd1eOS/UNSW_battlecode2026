# Counterplay prototype — experimental, not active

Frozen on 2026-10-05. Source hash (sorted `.cpp/.hpp/.toml` names and raw bytes):
`3ee383dc21247fd9a79ff0a6e116d0e32ac4f3e4ef98c6e26ec856cb9d03e445`.

Based on v66. Adds reachable attack-target selection, a visible free-move resource
competition preference, later-head endpoint ranking, and the known portal scout
exit veto for remembered own body. It does not recover private opponent code,
implement a complete opponent classifier, or coordinate Queen feeding.

The earlier package (`65943291e96b...`, before the portal scout veto) lost 14–18
against v66 across 32 held-out games. This exact package went 8–8 across 16 games
on Maze, Portals, Trophy and Default, seeds 10053/10054, both sides. These are
different map sets and source hashes. Neither establishes a stronger mainline.

Online remains v66. Main `bot/` retains only the narrow portal scout veto.
Design, limits, conditional counters and reproducible commands are in
[COUNTERPLAY.md](../../tests/COUNTERPLAY.md); all completed games and hashes are in
[the evidence record](../../tests/fixtures/counterplay-2026-10-05.json).
