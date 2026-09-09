# Development Status

Last updated: 2026-09-09 (Asia/Bangkok)

## Current phase

Checkpoints 1 through 4 and Checkpoints 5A through 5B are complete. Checkpoint 5C remains open.

## Current checkpoint

Checkpoint 5B — schema-constrained live Full Build run (complete); Checkpoint 5C — remaining basic conflict validation (next)

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
- Added a provider-neutral build-direction service with Economy, Balanced, Deep Analysis, and Maximum quality modes.
- Added a strict JSON response contract and validation for required content, types, ratings, entity references, class/ascendancy consistency, and material distinction.
- Added an offline deterministic contract provider that is explicitly labeled as test-only output.
- Documented the provider boundary and remaining live-provider work in `docs/BUILD_DIRECTION_CONTRACT.md`.
- Added a local Ollama adapter with JSON-schema constrained output, runtime metadata, and bounded validation retries.
- Ran `qwen3:8b` against the bounded Snipe context and validated three materially distinct live directions on the first attempt.
- Preserved the live result at ignored local path `.cache/live-directions.json`; no credentials or generated recommendations are committed.
- Selected the validated Ranger/Ranger1 Projectile Speed Boost direction for the first bounded full-build slice.
- Added a provider-neutral full-build contract, graph-derived passive allocation, deterministic validator, and explicitly labeled offline fixture.
- Added validation for selected entity IDs, passive connectivity, source support relationships, released Bow bases, positive mod spawn tags, item/mod levels, base attributes, and duplicate slots.
- Added a task-specific Ollama Full Build JSON schema, a CLI route that expands a selected validated direction, and bounded item/mod requirement context.
- Ran `qwen3:8b` live and validated a level-65 Ranger/Ranger1 Snipe build on the first requirement-aware attempt; evidence remains local at `.cache/live-full-build.json`.

## Tests

- Passing: thirty-six unit/integration tests on Python 3.10 with `ResourceWarning` promoted to an error; the pre-Ollama suite also passed on Python 3.14.
- Passing: all 15 data validation queries, SQLite integrity check, and foreign-key check.
- Passing: class mapping, real projectile route, point cost, virtual-root exclusion, wrong-ascendancy rejection, enabled-ascendancy route, and missing-node rejection.
- Passing: retrieval bounds, provenance/reasons, expected Snipe mechanics/supports, unique-data honesty, deterministic output, word-boundary matching, and unknown-skill rejection.
- Passing: all quality modes, bounded provider request, three-direction schema, test-only labeling, malformed/incomplete response rejection, invented IDs, class mismatch, and duplicate-selection rejection.
- Failing: none.

## Known issues

- Support compatibility currently means `recommended_by_source`; rule-level compatibility validation belongs to a later checkpoint.
- The generated database is local and reproducible but is not packaged or redistributed.
- The graph currently optimizes point count only; weighted build value belongs to candidate retrieval and later planning.
- Candidate scores are deterministic heuristics for context selection, not claims of final build strength or exact DPS.
- Unique effect data is absent from the selected RePoE export and remains unscored until a permitted, versioned source is integrated.
- Qualitative theorycrafting claims, exact DPS, and deeper equipment/gem conflicts are not calculation-engine validated.

## Current blockers

None for the next bounded implementation phase.

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
- Provider responses remain untrusted until schema and candidate-reference validation pass. Offline provider output is always labeled test-only.

## Next task

Extend deterministic validation for the remaining basic conflicts required by Checkpoint 5, one bounded rule group at a time.
