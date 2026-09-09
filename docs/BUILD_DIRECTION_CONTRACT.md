# Build Direction Provider Contract

Checkpoint 4A defines and validates the boundary between deterministic retrieval and an AI provider. It does not claim that a live model has evaluated or recommended a build.

## Request

The provider receives JSON containing:

- schema version and task name;
- configurable quality mode: `economy`, `balanced`, `deep_analysis`, or `maximum`;
- the bounded BuildContext from candidate retrieval;
- a machine-readable response contract;
- instructions to return JSON, use only supplied entity IDs, produce at least three distinct directions, and avoid unsupported numeric/effect claims.

The request contains no database path, raw table dump, stored `payload_json`, provider secret, or API credential. The verified request remains below 50 KB.

## Response

Each direction must include concept, class, ascendancy, main skill, selected mechanics/supports/passives/bases/mods/uniques, damage and defense direction, mapping and boss ratings with rationales, budget, league-start viability, strengths, weaknesses, and critical dependencies.

The validator rejects malformed JSON, fewer than three directions, missing or incorrectly typed fields, duplicate identities/titles, ratings outside 1–5, mismatched class/ascendancy pairs, the wrong main skill, and any entity ID absent from the candidate context.

## Offline provider

`OfflineDeterministicProvider` exists only to prove serialization and validation without credentials or API cost. Its service result is labeled:

```text
kind: offline_test
is_live_ai: false
output_status: test_only_not_ai_recommendation
```

Its direction text repeats that it is a contract example. It must never be shown to users as an AI-generated or viable build recommendation.

## Remaining work for Checkpoint 4

The local Ollama adapter passes the same contract. On 2026-09-09, `qwen3:8b` returned three validated, materially distinct directions on its first attempt using only the bounded BuildContext. The generated evidence remains local at `.cache/live-directions.json`; Checkpoint 4 is complete.
