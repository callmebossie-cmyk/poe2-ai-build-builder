"""Source-backed inspection data. This module never invents build selections."""
from __future__ import annotations

import json
import re
from collections import deque


def clean(text):
    return re.sub(r"\[([^\]]+)\]", lambda m: m.group(1).split("|")[-1], text or "")


def inspection_data(db, build, direction):
    allocated = set(build["passive_ids"])
    start = db.execute("SELECT node_id FROM class_starts WHERE class_name=?", (build["class_name"],)).fetchone()[0]
    stats = {}
    for row in db.execute("SELECT node_id,text FROM passive_stats ORDER BY node_id,ordinal"):
        stats.setdefault(row["node_id"], []).append(clean(row["text"]))
    nodes = []
    for row in db.execute("SELECT * FROM passive_nodes ORDER BY id"):
        payload = json.loads(row["payload_json"])
        if not isinstance(payload.get("x"), (int, float)) or not isinstance(payload.get("y"), (int, float)):
            continue
        nodes.append(dict(id=row["id"], name=row["name"] or "Travel node", x=payload["x"], y=payload["y"],
                          stats=stats.get(row["id"], []), icon=payload.get("icon", ""),
                          is_start=row["id"] == start, is_allocated=row["id"] in allocated,
                          is_target=row["id"] in direction.get("passive_ids", []),
                          is_notable=bool(row["is_notable"]), is_keystone=bool(row["is_keystone"]),
                          ascendancy_id=row["ascendancy_id"], depth=-1))
    ids = {node["id"] for node in nodes}
    pairs = sorted({tuple(sorted((r[0], r[1]))) for r in db.execute("SELECT from_node,to_node FROM passive_edges")
                    if r[0] in ids and r[1] in ids and r[0] != r[1]})
    adjacency = {node: [] for node in allocated}
    for a, b in pairs:
        if a in allocated and b in allocated:
            adjacency[a].append(b)
            adjacency[b].append(a)
    parents = {start: None}
    queue = deque([start])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(adjacency.get(node, [])):
            if neighbor not in parents:
                parents[neighbor] = node
                queue.append(neighbor)
    ascendancy = db.execute("SELECT name FROM ascendancies WHERE id=?", (build["ascendancy_id"],)).fetchone()
    sources = [dict(r) for r in db.execute("SELECT name,version,file_name,url FROM data_sources ORDER BY file_name")]
    skill = json.loads(db.execute("SELECT payload_json FROM skills WHERE id=?", (build["main_skill_id"],)).fetchone()[0])
    effects = []
    for effect in skill.get("stat_sets", []):
        label = effect.get("label")
        effects.append({"name": label[0] if isinstance(label, list) and label else effect["id"],
                        "text": [clean(t) for t in effect.get("static", {}).get("stat_text", {}).values() if t],
                        "levels": effect.get("per_level", {})})
    warnings = [
        "This is a partial build plan. DPS, effective life, resistances and resource sustain have not been calculated.",
        "Character attributes and level are AI proposals; gear, passive attribute choices and quest rewards are not reconciled.",
        "Only the selected main skill and weapon are generated. Other gear slots, utility skills and ascendancy allocation need planning.",
    ]
    for item in build["equipment"]:
        for mod_id in item["mod_ids"]:
            mod = db.execute("SELECT name,generation_type FROM mods WHERE id=?", (mod_id,)).fetchone()
            if mod["generation_type"] not in ("prefix", "suffix"):
                warnings.append(f"{mod['name'] or mod_id}: {mod['generation_type']} modifier is a special-source candidate, not a confirmed craftable affix on this item.")
    return {"nodes": nodes, "edges": [{"from": a, "to": b} for a, b in pairs],
            "allocation_order": order, "parents": parents, "ascendancy_name": ascendancy[0] if ascendancy else build["ascendancy_id"],
            "sources": sources, "warnings": warnings, "skill_effects": effects,
            "skill_levels": skill.get("per_level", {})}
