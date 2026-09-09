# Project Checkpoint

Last updated: 2026-09-09 (Asia/Bangkok)

## Current state

- Checkpoints 1 through 5 are complete; the deterministic/AI Core MVP exists.
- A dependency-free Python data core downloads seven pinned real-data exports, verifies SHA-256 checksums, and builds `data/poe2.db` locally.
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
- The local Ollama adapter constrains structured output to candidate IDs and retries validator failures with bounded feedback.
- A live `qwen3:8b` run returned three materially distinct, schema-valid directions with valid entity references on its first attempt.
- Live evidence is preserved locally at `.cache/live-directions.json` and excluded from Git; the bounded request was 27,293 bytes.
- The first full-build slice expands the validated Ranger direction into an exact graph-connected allocation and checks supports, Bow base, affix spawn tags, levels, and base attributes against SQLite.
- The local Ollama full-build route uses a task-specific JSON schema bounded to the selected direction and deterministic equipment requirements.
- A live `qwen3:8b` run produced a level-65 full build on its first attempt after requirement-aware context was added; all five deterministic validation groups passed.
- Live full-build evidence is preserved locally at `.cache/live-full-build.json` and excluded from Git; the bounded request was 3,563 bytes.
- Basic conflict validation rejects duplicate supports/mods, case-insensitive duplicate slots, shared exclusive mod groups, and more than three prefixes or suffixes per item.
- Gem rule validation checks support `allowed_types` and `excluded_types` against the pinned active-skill types, beyond source recommendation alone.
- Character validation rejects stated attributes below the selected class base values; provider minimums combine class and equipment requirements.
- The preserved live Full Build passes the new gem-rule and character-base checks without revision.
- Narrative fields are explicitly advisory, resource/DPS/price calculation is labeled unavailable, and unsupported quantitative narrative claims are rejected.
- The preserved live Full Build passes the final Checkpoint 5 validator without revision.
- Forty-two tests pass on Python 3.10 with resource warnings treated as errors; the pre-Ollama suite also passed on Python 3.14.
- Checkpoint 6A adds a runnable React 19, TypeScript 7, Vite 8, and Tauri 2 desktop shell with provider-neutral first-run configuration.
- Users can continue with no AI, choose local Ollama, or prepare a cloud endpoint/model; ordinary configuration stores no credential.
- Five provider-state tests, the frontend production build, Rust `cargo check`, and native release compilation pass.
- Checkpoint 6B adds one fixed, read-only Tauri `core_status` command that invokes Python validation and returns typed aggregate counts.
- The no-AI dashboard renders real local counts: 15/15 checks, 1 Snipe skill, 5,153 passive nodes, 35 released bow bases, and 7 provenance files.
- Two Rust bridge tests pass, including a real Python/SQLite invocation and failed-validation rejection.

## Current phase

Checkpoint 6B — read-only deterministic core status bridge is complete. Checkpoint 6C — deterministic build-intent and retrieval UI is next.

## Next exact action

Add the first Snipe build-intent form and expose bounded candidate retrieval through another narrow typed bridge command, without invoking AI.

## Completion rule for the next phase

Validate inputs in both Rust and Python-facing boundaries, keep retrieval bounded, and do not add AI calls or the complete workflow in the same phase.
