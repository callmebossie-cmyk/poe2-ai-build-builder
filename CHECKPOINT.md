# Project Checkpoint

Last updated: 2026-09-09 (Asia/Bangkok)

## Current state

- Checkpoint 1 — Real Data Import is complete.
- A dependency-free Python data core downloads six pinned real-data exports, verifies SHA-256 checksums, and builds `data/poe2.db` locally.
- The generated database contains Snipe, its real tags/levels/stat sets, 15 source-recommended supports, the complete passive tree, ascendancies, item bases, mods, and per-file provenance.
- Downloaded JSON and the generated database are excluded from Git.
- No user action is currently required.

## Completed acceptance evidence

- Snipe: 1 skill, 21 tags, 40 levels, 120 stat-set rows.
- Related supports: 15 queryable source recommendations.
- Passive tree: 5,153 nodes, 6,076 edges, 116 nodes with projectile-related stat text.
- Ascendancies: 37 records and 669 linked passive nodes.
- Equipment: 5,496 item bases including 35 released bows; 16,784 mods including 90 bow-spawnable mods.
- Provenance: six source files with pinned revisions and SHA-256 digests.
- SQLite integrity and foreign-key checks pass.
- Five tests pass on Python 3.10 and Python 3.14.

## Current phase

Checkpoint 1 complete. Ready to begin Checkpoint 2 — Passive Graph.

## Next exact action

Read this file and `docs/DEVELOPMENT_STATUS.md`, then implement graph loading and traversal over `passive_nodes` and `passive_edges`. Identify class starts from real source metadata, calculate one valid shortest path and point cost, and reject an impossible path.

## Completion rule for the next phase

Do not mark Checkpoint 2 complete until the graph can load real nodes/edges, identify a class start, prove connectivity, calculate a valid path and point cost, and reject an impossible path with meaningful tests.
