from __future__ import annotations

from contextlib import closing
from pathlib import Path

from .database import connect


CHECKS = {
    "Snipe exists": ("SELECT COUNT(*) FROM skills WHERE id='SnipePlayer' AND name='Snipe'", 1),
    "Skill tags available": ("SELECT COUNT(*) FROM skill_tags WHERE skill_id='SnipePlayer'", 1),
    "Level data available": ("SELECT COUNT(*) FROM skill_levels WHERE skill_id='SnipePlayer'", 1),
    "Stat-set data available": ("SELECT COUNT(*) FROM skill_stats WHERE skill_id='SnipePlayer'", 1),
    "Related supports queryable": ("SELECT COUNT(*) FROM support_compatibility WHERE skill_id='SnipePlayer'", 1),
    "Passive data available": ("SELECT COUNT(*) FROM passive_nodes", 1000),
    "Passive edges available": ("SELECT COUNT(*) FROM passive_edges", 1000),
    "Class starts available": ("SELECT COUNT(*) FROM class_starts", 12),
    "Projectile passives queryable": ("SELECT COUNT(DISTINCT node_id) FROM passive_stats WHERE lower(text) LIKE '%projectile%'", 1),
    "Ascendancy data available": ("SELECT COUNT(*) FROM ascendancies WHERE disabled=0", 1),
    "Ascendancy nodes available": ("SELECT COUNT(*) FROM ascendancy_nodes", 1),
    "Bow bases queryable": ("SELECT COUNT(*) FROM item_bases WHERE item_class='Bow' AND release_state='released'", 1),
    "Bow mods queryable": ("SELECT COUNT(DISTINCT mod_id) FROM mod_tags WHERE tag='bow' AND kind='spawn' AND weight>0", 1),
    "Bow uniques queryable": ("SELECT COUNT(*) FROM unique_items WHERE item_class='Bow'", 1),
    "Data provenance recorded": ("SELECT COUNT(*) FROM data_sources WHERE length(sha256)=64 AND length(version)>0", 7),
}


def validate_database(path: Path) -> list[dict[str, object]]:
    results = []
    with closing(connect(path)) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"SQLite integrity check failed: {integrity}")
        foreign_keys = db.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise ValueError(f"SQLite foreign key check failed: {foreign_keys[:3]}")
        for name, (query, minimum) in CHECKS.items():
            actual = db.execute(query).fetchone()[0]
            results.append({"check": name, "actual": actual, "minimum": minimum, "passed": actual >= minimum})
    failures = [row for row in results if not row["passed"]]
    if failures:
        raise ValueError(f"Checkpoint 1 validation failed: {failures}")
    return results


def snipe_summary(path: Path) -> dict[str, object]:
    with closing(connect(path)) as db:
        skill = dict(db.execute("SELECT id,name,description,cast_time_ms FROM skills WHERE id='SnipePlayer'").fetchone())
        skill["tags"] = [row[0] for row in db.execute("SELECT tag FROM skill_tags WHERE skill_id=? ORDER BY tag", (skill["id"],))]
        skill["levels"] = db.execute("SELECT COUNT(*) FROM skill_levels WHERE skill_id=?", (skill["id"],)).fetchone()[0]
        skill["stat_rows"] = db.execute("SELECT COUNT(*) FROM skill_stats WHERE skill_id=?", (skill["id"],)).fetchone()[0]
        skill["supports"] = [dict(row) for row in db.execute("SELECT s.id,s.name,c.relationship FROM support_compatibility c JOIN support_gems s ON s.id=c.support_id WHERE c.skill_id=? ORDER BY s.name", (skill["id"],))]
        skill["projectile_passives"] = [dict(row) for row in db.execute("SELECT DISTINCT n.id,n.name FROM passive_nodes n JOIN passive_stats s ON s.node_id=n.id WHERE lower(s.text) LIKE '%projectile%' AND n.name IS NOT NULL ORDER BY n.name LIMIT 10")]
        skill["class_starts"] = [dict(row) for row in db.execute("SELECT class_name,node_id FROM class_starts ORDER BY class_name")]
        skill["bow_bases"] = [dict(row) for row in db.execute("SELECT id,name,drop_level FROM item_bases WHERE item_class='Bow' AND release_state='released' ORDER BY drop_level,name LIMIT 10")]
        skill["bow_mods"] = [dict(row) for row in db.execute("SELECT DISTINCT m.id,m.name,m.text FROM mods m JOIN mod_tags t ON t.mod_id=m.id WHERE t.tag='bow' AND t.kind='spawn' AND t.weight>0 ORDER BY m.required_level,m.name LIMIT 10")]
        skill["bow_uniques"] = [dict(row) for row in db.execute("SELECT id,name FROM unique_items WHERE item_class='Bow' ORDER BY name")]
        skill["sources"] = [dict(row) for row in db.execute("SELECT name,version,file_name,sha256 FROM data_sources ORDER BY file_name")]
        return skill
