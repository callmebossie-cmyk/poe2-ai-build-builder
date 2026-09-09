# Full Build Contract

Checkpoint 5A defines the first bounded full-build contract and deterministic validator. Checkpoint 5B adds and validates the live local-Ollama route.

## Selected direction

The first slice expands the validated live direction `direction_2`, Projectile Speed Boost, using Ranger, Ranger1, and Snipe. It was selected because its real bow base, bow-spawnable mods, source-recommended supports, and passive targets can all be checked against the existing local database and graph.

## Provider boundary

The provider receives the selected direction, base character attributes, the selected skill, and a deterministic connected passive allocation. It does not receive the database path or raw source exports.

The response must include class, ascendancy, level, attributes, a connected passive allocation, the main skill and supports, equipment bases and mods, affix priorities, defense, resource solution, leveling concept, upgrade order, and rotation.

## Deterministic checks

- Class, ascendancy, and main skill must match the selected direction.
- The allocation must exactly match the bounded graph-generated allocation, include the class start, and be connected under the selected ascendancy rules.
- Supports must be selected by the direction, have `recommended_by_source` compatibility with Snipe, and pass pinned allowed/excluded active-skill type rules.
- Equipment must use a released Bow base selected by the direction.
- Mods must be selected by the direction, meet the build level, and have a positive spawn tag shared with the base.
- Build level and stated attributes must satisfy recorded equipment requirements, and attributes cannot be below the selected class base values.
- Duplicate equipment slots, invented IDs, missing narrative fields, and malformed structures are rejected.
- Duplicate support/mod IDs, equipment slots that differ only by case, shared exclusive mod groups, and more than three prefixes or suffixes are rejected.

## Live Checkpoint 5B evidence

The provider receives explicit, deterministic minimum level and base-attribute requirements for the selected equipment and mods. Its JSON schema restricts every entity reference to the selected direction and requires the complete graph-generated passive allocation.

On 2026-09-09, local `qwen3:8b` generated a level-65 Ranger/Ranger1 Snipe full build in one requirement-aware attempt. The 3,563-byte request used no database path or raw exports, and the result passed schema, entity-reference, passive-path, source-support, and equipment-requirement validation. Evidence is stored locally at ignored path `.cache/live-full-build.json`.

## Remaining Checkpoint 5 boundary

The offline provider remains a contract fixture, not an AI recommendation. Narrative fields are labeled advisory and resource, exact DPS, and price calculations are explicitly `not_calculated`. Numeric DPS, percentage, and currency/price claims in narrative fields are rejected until a deterministic calculator can support them.

The preserved live Full Build passes the complete bounded validator, so Checkpoint 5 and the Core MVP are complete. Full PoB-grade DPS, reservation/resource simulation, computed passive attributes, and deeper mechanics remain later expansion work and must not be presented as validated.
