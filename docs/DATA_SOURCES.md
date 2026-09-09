# Data Sources and Distribution Boundary

Checked on 2026-09-09.

## Sources pinned for Checkpoint 1

| Data | Repository | Pinned revision | Local file |
| --- | --- | --- | --- |
| Passive tree | `grindinggear/poe2-skilltree-export` | `bd87e6512c92b868542eddfb1ba4ea8b6dc2da36` | `passive_tree.json` |
| Skills, gems, ascendancies, bases, mods | `repoe-fork/poe2` | `5428e93202bedda0af43f79723c7dba586733f41` | five JSON exports |

The RePoE export reports game/export version `4.5.5.1.6` at this revision.

Every downloaded file is recorded in `.cache/sources/manifest.json` with its URL, pinned revision, byte length, SHA-256 digest, and fetch time. The SQLite `data_sources` table copies that provenance into the generated database.

## Licensing findings

- `repoe-fork/repoe` tooling is MIT licensed. Its license separately says generated files under `data` are owned by Grinding Gear Games and must be used or published in accordance with GGG's terms.
- `PathOfBuildingCommunity/PathOfBuilding-PoE2` identifies its main code as MIT and includes third-party notices. We inspected it as an architectural/data reference and copied no PoB code or data in this phase.
- The PoB2 inspection used development revision `fd4c1acb7f9f5ffd13372f5387ae16f8e6278c15`. Its generated skill files and Snipe-specific stat-description files confirm the local generated-data architecture described in the project plan.
- `grindinggear/poe2-skilltree-export` publishes the official tree export but has no repository license file as of the pinned revision.
- GGG's developer policy permits independent executable applications, requires public OAuth clients for API access, prohibits applications that interact with the game or game files, forbids bundled credentials, and requires an unaffiliated-product notice for public applications.

## Project policy

This repository contains importer code and source metadata. It does not commit downloaded game/community JSON or the generated SQLite database. Users or developers fetch the pinned sources locally. Before any public/community release, re-check current GGG terms, source licenses, attribution, and whether generated data may be redistributed. PoE2DB is not scraped or redistributed.
