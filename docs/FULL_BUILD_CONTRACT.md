# Full Build Contract

Checkpoint 5A defines the first bounded full-build contract and deterministic validator.

## Selected direction

The first slice expands the validated live direction `direction_2`, Projectile Speed Boost, using Ranger, Ranger1, and Snipe. It was selected because its real bow base, bow-spawnable mods, source-recommended supports, and passive targets can all be checked against the existing local database and graph.

## Provider boundary

The provider receives the selected direction, base character attributes, the selected skill, and a deterministic connected passive allocation. It does not receive the database path or raw source exports.

The response must include class, ascendancy, level, attributes, a connected passive allocation, the main skill and supports, equipment bases and mods, affix priorities, defense, resource solution, leveling concept, upgrade order, and rotation.

## Deterministic checks

- Class, ascendancy, and main skill must match the selected direction.
- The allocation must exactly match the bounded graph-generated allocation, include the class start, and be connected under the selected ascendancy rules.
- Supports must be selected by the direction and have `recommended_by_source` compatibility with Snipe.
- Equipment must use a released Bow base selected by the direction.
- Mods must be selected by the direction, meet the build level, and have a positive spawn tag shared with the base.
- Build level and stated attributes must satisfy the recorded base requirements.
- Duplicate equipment slots, invented IDs, missing narrative fields, and malformed structures are rejected.

## Boundary of Checkpoint 5A

The offline provider is a contract fixture, not an AI recommendation. Checkpoint 5 remains open until a live provider expands the selected direction and the returned full build passes this validator. Exact DPS, complete gem-rule compatibility, computed passive attributes, and deeper conflict detection remain outside this first slice and must not be claimed as validated.
