# Development Status

Last updated: 2026-09-09 (Asia/Bangkok)

## Current phase

Checkpoints 1 through 3 are complete. Checkpoint 4 is next.

## Current checkpoint

Checkpoint 4 — AI Build Directions (pending)

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
- Added a structured `BuildIntent` and deterministic candidate retriever for mechanics, supports, passives, ascendancies, bases, mods, and uniques.
- Added explainable scores, real graph-distance costs, provenance, bounded result counts, and serialized-size diagnostics.
- Imported all 449 unique source rows without collapsing repeated canonical IDs; unique effect gaps are explicit.
- Documented retrieval rules and current assumptions in `docs/CANDIDATE_RETRIEVAL.md`.

## Tests

- Passing: seventeen unit/integration tests on Python 3.10 and Python 3.14 with `ResourceWarning` promoted to an error.
- Passing: all 15 data validation queries, SQLite integrity check, and foreign-key check.
- Passing: class mapping, real projectile route, point cost, virtual-root exclusion, wrong-ascendancy rejection, enabled-ascendancy route, and missing-node rejection.
- Passing: retrieval bounds, provenance/reasons, expected Snipe mechanics/supports, unique-data honesty, deterministic output, word-boundary matching, and unknown-skill rejection.
- Failing: none.

## Known issues

- Support compatibility currently means `recommended_by_source`; rule-level compatibility validation belongs to a later checkpoint.
- The generated database is local and reproducible but is not packaged or redistributed.
- The graph currently optimizes point count only; weighted build value belongs to candidate retrieval and later planning.
- Candidate scores are deterministic heuristics for context selection, not claims of final build strength or exact DPS.
- Unique effect data is absent from the selected RePoE export and remains unscored until a permitted, versioned source is integrated.

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
- Candidate retrieval uses whole-word/phrase matches, source compatibility/release/spawn rules, passive point distance, and explicit bounded limits. The provider layer receives no raw database payloads.

## Next task

Implement Checkpoint 4's provider-neutral structured build-direction contract, offline test provider, schema validation, and invented-entity rejection over the compact BuildContext.
