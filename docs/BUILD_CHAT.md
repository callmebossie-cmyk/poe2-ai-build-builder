# Validated Build Chat

The desktop conversation opens only after a selected AI direction has produced a Full Build that passes every deterministic validation flag.

Each question crosses the native boundary with the selected direction, validated build, current intent, and at most twelve prior messages. The Python core validates the build again, retrieves the bounded candidate context, filters evidence to selected entity IDs, and then calls local Ollama. Questions are limited to two thousand characters.

Responses use structured JSON. The core rejects malformed answers, unknown entity IDs, and unsupported numeric DPS, percentage, price, or currency claims. Qualitative guidance is labeled advisory. A response that fails validation receives bounded feedback and may be regenerated up to three times.

The current chat explains the active build. Suggested changes are advisory and are not applied automatically; a future edit workflow must turn changes into structured build revisions and run the Full Build validator before applying them.

The workspace expands equipment, the passive tree, skills and advisory notes on one page. The tree renders the full pinned GGG context and locally bundled icon atlas, with pan, zoom, search, inspection and a parent-connected allocation-order preview. The free class start is excluded from the point count. This sequence is not a character-level guide.

Equipment is a selectable slot diagram with base properties, requirements and modifier candidates. Unknown slots stay unplanned. Gem effects and inspectable per-level source values are separate from AI narrative. Source revisions and bounded validation checks are visible.

This remains a partial build generator, not a PoB calculator. Full gear generation, utility skills, ascendancy allocation, gem level/quality choices, passive budget/quest reconciliation and calculated character totals remain unfinished. Special-source modifiers are highlighted for review.

Workspace verification: Python 46 tests, frontend 5 tests and production TypeScript/Vite build pass. Browser and Windows automation could not initialize (kernel asset path failure), so interactive and responsive visual checks require manual verification.
