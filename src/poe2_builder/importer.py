from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .database import SCHEMA, connect, json_text
from .fetch import verify_manifest

SNIPE_GEM_ID = "Metadata/Items/Gem/SkillGemSnipe"
SNIPE_SKILL_ID = "SnipePlayer"


def load_json(cache_dir: Path, name: str) -> dict:
    with (cache_dir / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_database(cache_dir: Path, database_path: Path) -> dict[str, int]:
    manifest = verify_manifest(cache_dir)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = database_path.with_suffix(database_path.suffix + ".building")
    if temporary.exists():
        temporary.unlink()

    skill_gems = load_json(cache_dir, "skill_gems.json")
    skills = load_json(cache_dir, "skills.json")
    passive_tree = load_json(cache_dir, "passive_tree.json")
    ascendancies = load_json(cache_dir, "ascendancies.json")
    item_bases = load_json(cache_dir, "base_items.json")
    mods = load_json(cache_dir, "mods.json")

    if SNIPE_GEM_ID not in skill_gems or SNIPE_SKILL_ID not in skills:
        raise ValueError("Pinned real-data sources do not contain the expected Snipe records")

    imported_at = datetime.now(timezone.utc).isoformat()
    with connect(temporary) as db:
        db.executescript(SCHEMA)
        source_ids: dict[str, int] = {}
        for record in manifest["files"]:
            cursor = db.execute(
                "INSERT INTO data_sources(name,version,file_name,url,sha256,imported_at) VALUES(?,?,?,?,?,?)",
                (record["source"], record["version"], record["file"], record["url"], record["sha256"], imported_at),
            )
            source_ids[record["file"]] = cursor.lastrowid

        gem_source = source_ids["skill_gems.json"]
        skill_source = source_ids["skills.json"]
        tree_source = source_ids["passive_tree.json"]
        ascendancy_source = source_ids["ascendancies.json"]
        item_source = source_ids["base_items.json"]
        mod_source = source_ids["mods.json"]

        gem = skill_gems[SNIPE_GEM_ID]
        skill = skills[SNIPE_SKILL_ID]
        active = skill["active_skill"]
        db.execute(
            "INSERT INTO skills VALUES(?,?,?,?,?,?,?)",
            (SNIPE_SKILL_ID, SNIPE_GEM_ID, active["display_name"], active.get("description", ""), skill.get("cast_time"), json_text(skill), skill_source),
        )
        tags = list(dict.fromkeys([*gem.get("tags", []), *active.get("types", [])]))
        db.executemany("INSERT INTO skill_tags VALUES(?,?,?)", ((SNIPE_SKILL_ID, tag, gem_source) for tag in tags))
        db.executemany(
            "INSERT INTO skill_levels VALUES(?,?,?,?)",
            ((SNIPE_SKILL_ID, int(level), json_text(data), skill_source) for level, data in skill.get("per_level", {}).items()),
        )
        for stat_set in skill.get("stat_sets", []):
            for level, data in stat_set.get("per_level", {}).items():
                db.execute(
                    "INSERT INTO skill_stats VALUES(?,?,?,?,?)",
                    (SNIPE_SKILL_ID, stat_set["id"], int(level), json_text(data), skill_source),
                )

        for support_id in gem.get("recommended_supports", []):
            support = skill_gems.get(support_id)
            if support is None:
                raise ValueError(f"Recommended support is missing from source: {support_id}")
            name = support.get("base_item", {}).get("display_name") or support.get("support_name") or support_id
            db.execute(
                "INSERT INTO support_gems VALUES(?,?,?,?,?)",
                (support_id, name, json_text(support.get("grants_skills", [])), json_text(support), gem_source),
            )
            db.executemany(
                "INSERT INTO support_tags VALUES(?,?,?)",
                ((support_id, tag, gem_source) for tag in dict.fromkeys(support.get("tags", []))),
            )
            db.execute(
                "INSERT INTO support_compatibility VALUES(?,?,?,?)",
                (SNIPE_SKILL_ID, support_id, "recommended_by_source", gem_source),
            )

        for node_id, node in passive_tree["nodes"].items():
            db.execute(
                "INSERT INTO passive_nodes VALUES(?,?,?,?,?,?,?,?,?,?)",
                (str(node_id), node.get("name"), node.get("ascendancyId"), node.get("group"), node.get("orbit"), node.get("orbitIndex"), int(bool(node.get("isKeystone"))), int(bool(node.get("isNotable"))), json_text(node), tree_source),
            )
            db.executemany(
                "INSERT INTO passive_stats VALUES(?,?,?,?)",
                ((str(node_id), ordinal, text, tree_source) for ordinal, text in enumerate(node.get("stats", []))),
            )
            if node.get("ascendancyId"):
                db.execute(
                    "INSERT INTO ascendancy_nodes VALUES(?,?,?)",
                    (node["ascendancyId"], str(node_id), tree_source),
                )
        for class_index, character_class in enumerate(passive_tree.get("classes", [])):
            db.execute(
                "INSERT INTO character_classes VALUES(?,?,?,?,?,?,?)",
                (
                    class_index,
                    character_class["name"],
                    character_class.get("base_str", 0),
                    character_class.get("base_dex", 0),
                    character_class.get("base_int", 0),
                    json_text(character_class),
                    tree_source,
                ),
            )
        for node_id, node in passive_tree["nodes"].items():
            for class_index in node.get("classStartIndex", []):
                character_class = passive_tree["classes"][class_index]
                db.execute(
                    "INSERT INTO class_starts VALUES(?,?,?)",
                    (character_class["name"], str(node_id), tree_source),
                )
        db.executemany(
            "INSERT OR IGNORE INTO passive_edges VALUES(?,?,?)",
            ((str(edge["from"]), str(edge["to"]), tree_source) for edge in passive_tree["edges"]),
        )

        base_class_by_ascendancy = {
            asc["id"]: base["name"]
            for base in passive_tree.get("classes", [])
            for asc in base.get("ascendancies", [])
        }
        for ascendancy_id, record in ascendancies.items():
            db.execute(
                "INSERT INTO ascendancies VALUES(?,?,?,?,?,?)",
                (ascendancy_id, record.get("name", ascendancy_id), base_class_by_ascendancy.get(ascendancy_id), int(bool(record.get("disabled"))), json_text(record), ascendancy_source),
            )

        for item_id, item in item_bases.items():
            db.execute(
                "INSERT INTO item_bases VALUES(?,?,?,?,?,?,?)",
                (item_id, item.get("name", item_id), item.get("item_class"), item.get("drop_level"), item.get("release_state"), json_text(item), item_source),
            )
            db.executemany(
                "INSERT INTO item_base_tags VALUES(?,?,?)",
                ((item_id, tag, item_source) for tag in dict.fromkeys(item.get("tags", []))),
            )

        for mod_id, mod in mods.items():
            db.execute(
                "INSERT INTO mods VALUES(?,?,?,?,?,?,?,?)",
                (mod_id, mod.get("name", mod_id), mod.get("domain"), mod.get("generation_type"), mod.get("required_level"), mod.get("text"), json_text(mod), mod_source),
            )
            db.executemany(
                "INSERT INTO mod_stats VALUES(?,?,?,?,?,?)",
                ((mod_id, ordinal, stat.get("id", ""), stat.get("min"), stat.get("max"), mod_source) for ordinal, stat in enumerate(mod.get("stats", []))),
            )
            tag_rows = []
            for tag in mod.get("implicit_tags", []):
                tag_rows.append((mod_id, tag, "implicit", None, mod_source))
            for spawn in mod.get("spawn_weights", []):
                tag_rows.append((mod_id, spawn["tag"], "spawn", spawn.get("weight"), mod_source))
            for generation in mod.get("generation_weights", []):
                tag_rows.append((mod_id, generation["tag"], "generation", generation.get("weight"), mod_source))
            db.executemany("INSERT OR IGNORE INTO mod_tags VALUES(?,?,?,?,?)", tag_rows)

        db.execute("PRAGMA optimize")

    db.close()
    if database_path.exists():
        database_path.unlink()
    temporary.replace(database_path)
    with connect(database_path) as db:
        return {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "skills", "skill_tags", "skill_levels", "skill_stats", "support_gems",
                "passive_nodes", "passive_edges", "character_classes", "class_starts", "ascendancies", "ascendancy_nodes",
                "item_bases", "mods", "data_sources",
            )
        }
