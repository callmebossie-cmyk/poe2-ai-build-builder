# TODO

## Completed — Checkpoint 1: Real Data Import

- [x] Re-read the project plan and current development status.
- [x] Inspect authoritative/current source schemas and licenses.
- [x] Record chosen source versions and provenance.
- [x] Select Python standard library and SQLite for the bounded data-core phase.
- [x] Design the initial normalized SQLite schema.
- [x] Implement the real-data import pipeline for the Snipe slice.
- [x] Add unit and real-data integration tests.
- [x] Verify every Checkpoint 1 acceptance criterion.
- [x] Update checkpoint and development documents.

## Completed — Checkpoint 2: Passive Graph

- [x] Load passive nodes and edges from SQLite.
- [x] Identify class start nodes from real metadata.
- [x] Check graph connectivity without the virtual-root shortcut.
- [x] Calculate a valid shortest path and point cost.
- [x] Reject missing and impossible paths with explicit errors.
- [x] Add meaningful graph tests over the real imported tree.
- [x] Update status documents and create a local checkpoint commit.

## Completed — Checkpoint 3: Candidate Retrieval

- [x] Define the structured build-intent input.
- [x] Retrieve compact Snipe mechanics and related support candidates.
- [x] Rank relevant passives and ascendancies with reasons.
- [x] Rank relevant bow bases, mods, and available uniques with reasons.
- [x] Include source record IDs and scoring metadata for debugging.
- [x] Prove the result is bounded and does not contain the full database.
- [x] Add real-data retrieval tests.
- [x] Update status documents and create a local checkpoint commit without pushing.

## Next — Checkpoint 4: AI Build Directions

- [x] Define a provider-neutral request/response contract and quality mode.
- [x] Serialize only the compact BuildContext across the provider boundary.
- [x] Require at least three schema-valid and materially distinct build directions.
- [x] Require concept, class, ascendancy, mechanics, damage, defense, mapping, bossing, budget, league-start, strengths, weaknesses, and dependencies.
- [x] Reject referenced skills, supports, passives, bases, mods, and uniques that do not exist in the candidate context.
- [x] Add an explicitly labeled offline deterministic provider for tests.
- [x] Add structured-output, duplicate-direction, and invented-entity tests.
- [x] Complete Checkpoint 4A documentation and local commit without pushing.
- [ ] User chooses live cloud provider/model and test budget, or local Ollama model/resource route.
- [ ] Implement the selected live provider adapter without storing credentials.
- [ ] Run and validate at least three live directions.
- [ ] Complete Checkpoint 4B and mark Checkpoint 4 complete.

## Later checkpoints

- [x] Checkpoint 2 — Passive Graph
- [x] Checkpoint 3 — Candidate Retrieval
- [ ] Checkpoint 4 — AI Build Directions
- [ ] Checkpoint 5 — Full Build and Validator
- [ ] Checkpoint 6 — Desktop Application
- [ ] Checkpoint 7 — Windows Distribution
