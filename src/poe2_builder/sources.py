from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceFile:
    name: str
    source: str
    version: str
    url: str


GGG_TREE_COMMIT = "bd87e6512c92b868542eddfb1ba4ea8b6dc2da36"
REPOE_COMMIT = "5428e93202bedda0af43f79723c7dba586733f41"
REPOE_GAME_VERSION = "4.5.5.1.6"

SOURCE_FILES = (
    SourceFile(
        "passive_tree.json",
        "GGG PoE2 Passive Skill Tree Export",
        GGG_TREE_COMMIT,
        f"https://raw.githubusercontent.com/grindinggear/poe2-skilltree-export/{GGG_TREE_COMMIT}/data.json",
    ),
    *(
        SourceFile(
            filename,
            "RePoE Fork PoE2 Export",
            REPOE_COMMIT,
            f"https://raw.githubusercontent.com/repoe-fork/poe2/{REPOE_COMMIT}/data/{filename}",
        )
        for filename in (
            "skill_gems.json",
            "skills.json",
            "ascendancies.json",
            "base_items.json",
            "mods.json",
            "uniques.json",
        )
    ),
)
