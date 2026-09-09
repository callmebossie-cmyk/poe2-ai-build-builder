# Project Checkpoint

Last updated: 2026-09-09 (Asia/Bangkok)

## Current state

- Checkpoints 1 through 3 and Checkpoint 4A are complete. Checkpoint 4B is waiting for a live-provider choice.
- A dependency-free Python data core downloads seven pinned real-data exports, verifies SHA-256 checksums, and builds `data/poe2.db` locally.
- The generated database contains Snipe, its real tags/levels/stat sets, 15 source-recommended supports, the complete passive tree, ascendancies, item bases, mods, and per-file provenance.
- Downloaded JSON and the generated database are excluded from Git.
- User action is required only for the live-provider route recorded in `USER_ACTION_REQUIRED.md`.
- Changes after commit `d62d287` are local only and have not been pushed, following the user's instruction.

## Completed acceptance evidence

- Snipe: 1 skill, 21 tags, 40 levels, 120 stat-set rows.
- Related supports: 15 queryable source recommendations.
- Passive tree: 5,153 nodes, 6,076 edges, 116 nodes with projectile-related stat text.
- Ascendancies: 37 records and 669 linked passive nodes.
- Equipment: 5,496 item bases including 35 released bows; 16,784 mods including 90 bow-spawnable mods.
- Provenance: seven source files with pinned revisions and SHA-256 digests.
- SQLite integrity and foreign-key checks pass.
- Class starts: 12 classes mapped to six shared real-data start nodes.
- Default passive graph: 4,461 nodes reachable from Ranger without virtual-root or ascendancy shortcuts.
- Verified route: Ranger start `50459` to Projectile Damage `56651`, one allocated point.
- Impossible-path handling: missing nodes and closed/wrong ascendancy paths are rejected explicitly.
- Candidate retrieval scans real tables and returns at most 65 records across mechanics, supports, passives, ascendancies, bases, mods, and uniques.
- Verified `Snipe / Fast / Mapping / Cheap` context: about 25.7 KB versus a generated database over 40 MB.
- Every candidate includes an integer score, human-readable reasons, source record ID, dataset, pinned revision, and compact metadata.
- Unique source rows: 449 preserved; 11 Bow uniques queryable. Missing effect data is labeled and receives no invented mechanical/budget score.
- Provider-neutral direction contract requires at least three complete, materially distinct directions and four configurable quality modes.
- Requests contain the bounded BuildContext and contract, with no database path, raw payload, or secret; verified below 50 KB.
- Response validation rejects malformed/incomplete JSON, wrong skill, class/ascendancy mismatch, invented candidate IDs, duplicate identities/titles, and cosmetically renamed duplicate selections.
- Offline output is labeled `test_only_not_ai_recommendation` and cannot be mistaken for a live recommendation.
- Twenty-five tests pass on Python 3.10 and Python 3.14 with resource warnings treated as errors.

## Current phase

Checkpoint 4A — provider contract and validation is complete. Checkpoint 4B — live provider execution is blocked on provider/model choice.

## Next exact action

Read this file, `docs/DEVELOPMENT_STATUS.md`, and `USER_ACTION_REQUIRED.md`. After the user chooses a provider/model and acceptable cost/resource route, implement that adapter, run the bounded request, validate at least three live build directions, and preserve the validated response as local test evidence without committing secrets.

## Completion rule for the next phase

Do not mark Checkpoint 4 complete until a live provider receives only the bounded BuildContext, returns at least three schema-valid and materially distinct directions with every referenced entity present in the candidate context, and the live output passes the existing validator.
