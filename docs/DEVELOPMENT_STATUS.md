# Development Status

Last updated: 2026-09-09 (Asia/Bangkok)

## Current phase

Checkpoints 1 and 2 are complete. Checkpoint 3 is next.

## Current checkpoint

Checkpoint 3 — Candidate Retrieval (pending)

## Completed work

- Preserved the complete project specification in the repository.
- Created durable resume, task, and user-action documents.
- Established `main` as the initial branch.
- Added pinned fetch, checksum manifest, normalized SQLite import, validation, and query commands using only the Python standard library.
- Imported and validated the real Snipe slice plus the full passive tree, ascendancies, item bases, and mods.
- Documented source provenance, licensing findings, and the no-redistribution boundary in `docs/DATA_SOURCES.md`.
- Added normalized character-class/start mappings derived from source `classStartIndex` metadata.
- Added undirected passive traversal with virtual-root exclusion, opt-in ascendancy islands, connectivity inspection, shortest paths, and allocation point costs.
- Documented traversal rules and verified examples in `docs/PASSIVE_GRAPH.md`.

## Tests

- Passing: ten unit/integration tests on Python 3.10 and Python 3.14 with `ResourceWarning` promoted to an error.
- Passing: all 14 data validation queries, SQLite integrity check, and foreign-key check.
- Passing: class mapping, real projectile route, point cost, virtual-root exclusion, wrong-ascendancy rejection, enabled-ascendancy route, and missing-node rejection.
- Failing: none.

## Known issues

- Support compatibility currently means `recommended_by_source`; rule-level compatibility validation belongs to a later checkpoint.
- The generated database is local and reproducible but is not packaged or redistributed.
- The graph currently optimizes point count only; weighted build value belongs to candidate retrieval and later planning.

## Current blockers

None.

## Data versions

- GGG PoE2 tree revision: `bd87e6512c92b868542eddfb1ba4ea8b6dc2da36`.
- RePoE PoE2 revision: `5428e93202bedda0af43f79723c7dba586733f41`.
- RePoE reported game/export version: `4.5.5.1.6`.
- PoB2 reference inspection revision: `fd4c1acb7f9f5ffd13372f5387ae16f8e6278c15`.

## Architectural decisions

- Local structured data and deterministic code own the database, graph, calculator, and validator.
- AI is used for theorycrafting over a compact retrieved context.
- Implementation proceeds from real data through normalization, database, graph, retrieval, AI, validation, calculation, UI, and Windows distribution.
- PoE2DB remains a human reference/fallback until its permission and redistribution terms are clear.
- No checkpoint may pass using hand-written mock data, hard-coded output, or unvalidated stubs.
- Checkpoint 1 uses Python 3.10+ and the standard-library `sqlite3` module so data inspection and importer iteration stay dependency-free. The final desktop direction remains React, TypeScript, Tauri, and a Rust core unless later evidence warrants a documented change.
- Raw source JSON and generated SQLite remain local artifacts ignored by Git; the repository stores downloader/importer code and pinned metadata.
- Passive allocation treats source edges as undirected, excludes the virtual `root`, and opens only the explicitly selected ascendancy island.
- Repository changes are accumulated locally and are pushed only when the user explicitly asks.

## Next task

Implement bounded, explainable candidate retrieval for `Snipe / Fast / Mapping / Cheap` without passing the full database to the AI layer.
