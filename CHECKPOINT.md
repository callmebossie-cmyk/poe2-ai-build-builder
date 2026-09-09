# Project Checkpoint

Last updated: 2026-09-09 (Asia/Bangkok)

## Current state

- Checkpoints 1 and 2 are complete.
- A dependency-free Python data core downloads six pinned real-data exports, verifies SHA-256 checksums, and builds `data/poe2.db` locally.
- The generated database contains Snipe, its real tags/levels/stat sets, 15 source-recommended supports, the complete passive tree, ascendancies, item bases, mods, and per-file provenance.
- Downloaded JSON and the generated database are excluded from Git.
- No user action is currently required.
- Changes after commit `d62d287` are local only and have not been pushed, following the user's instruction.

## Completed acceptance evidence

- Snipe: 1 skill, 21 tags, 40 levels, 120 stat-set rows.
- Related supports: 15 queryable source recommendations.
- Passive tree: 5,153 nodes, 6,076 edges, 116 nodes with projectile-related stat text.
- Ascendancies: 37 records and 669 linked passive nodes.
- Equipment: 5,496 item bases including 35 released bows; 16,784 mods including 90 bow-spawnable mods.
- Provenance: six source files with pinned revisions and SHA-256 digests.
- SQLite integrity and foreign-key checks pass.
- Class starts: 12 classes mapped to six shared real-data start nodes.
- Default passive graph: 4,461 nodes reachable from Ranger without virtual-root or ascendancy shortcuts.
- Verified route: Ranger start `50459` to Projectile Damage `56651`, one allocated point.
- Impossible-path handling: missing nodes and closed/wrong ascendancy paths are rejected explicitly.
- Ten tests pass on Python 3.10 and Python 3.14 with resource warnings treated as errors.

## Current phase

Checkpoint 2 complete. Ready to begin Checkpoint 3 — Candidate Retrieval.

## Next exact action

Read this file and `docs/DEVELOPMENT_STATUS.md`, then implement deterministic candidate retrieval for `Snipe / Fast / Mapping / Cheap`. Return mechanics, supports, passives, ascendancies, item bases, mods, and available uniques with scores/reasons that explain every selection.

## Completion rule for the next phase

Do not mark Checkpoint 3 complete until compact candidate sets come from database queries, include debug-friendly scores/reasons, avoid sending the full database onward, and pass meaningful tests over the real imported data.
