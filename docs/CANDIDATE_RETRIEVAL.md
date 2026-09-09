# Candidate Retrieval

Checkpoint 3 converts a structured `BuildIntent` into a compact `BuildContext` using deterministic SQLite queries and passive-graph distances. No LLM call occurs in this phase.

## Input

The verified vertical slice uses:

```text
Main Skill: Snipe
Playstyle: Fast
Goal: Mapping
Budget: Cheap
```

## Candidate sets

The result contains mechanics, supports, passive nodes, ascendancies, item bases, modifiers, and unique-item metadata. Every candidate has:

- source record ID and name;
- integer score;
- one or more human-readable selection reasons;
- source dataset and pinned revision;
- a compact category-specific metadata object.

The retriever records the terms, scanned-row counts, returned-row counts, limits, assumptions, and serialized byte count for debugging.

## Scoring boundaries

- Mechanics come directly from the skill's real tags.
- Supports must be listed as recommended for the selected skill by the source export. Intent/tag matches refine their score.
- Passive candidates must have matching real stat text and be reachable from the recorded start without a virtual-root or ascendancy shortcut. Point distance reduces the score.
- Ascendancies use their real node text and base class. Dexterity-side classes receive a transparent fit bonus for the dexterity-tagged Snipe gem.
- Bases must match the skill's weapon tag and release state. Low drop level and source attack time influence Cheap/Fast ranking.
- Modifiers must have a positive source spawn weight for the weapon tag and matching modifier text.
- The current unique export contains identity metadata but no effects. Bow uniques are exposed with a low neutral score and `effect_data_available: false`; the retriever does not invent a mechanical or budget fit.

## Size limits

The current limits return at most 65 candidates across all seven categories. The verified Snipe context is about 26 KB, while the generated SQLite database is over 40 MB. The AI layer will receive the compact result rather than raw tables or stored JSON payloads.

## Current assumption

Passive distances use the Ranger start because Snipe is a dexterity-tagged Bow skill. Ranger and Huntress share the same source start node. A later build-direction phase may evaluate paths for several classes before choosing one.
