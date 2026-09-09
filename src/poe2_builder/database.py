from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    file_name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL
);
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    gem_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    cast_time_ms INTEGER,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE skill_tags (
    skill_id TEXT NOT NULL REFERENCES skills(id),
    tag TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (skill_id, tag)
);
CREATE TABLE skill_levels (
    skill_id TEXT NOT NULL REFERENCES skills(id),
    level INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (skill_id, level)
);
CREATE TABLE skill_stats (
    skill_id TEXT NOT NULL REFERENCES skills(id),
    stat_set_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (skill_id, stat_set_id, level)
);
CREATE TABLE support_gems (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    granted_skills_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE support_tags (
    support_id TEXT NOT NULL REFERENCES support_gems(id),
    tag TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (support_id, tag)
);
CREATE TABLE support_compatibility (
    skill_id TEXT NOT NULL REFERENCES skills(id),
    support_id TEXT NOT NULL REFERENCES support_gems(id),
    relationship TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (skill_id, support_id)
);
CREATE TABLE passive_nodes (
    id TEXT PRIMARY KEY,
    name TEXT,
    ascendancy_id TEXT,
    group_id INTEGER,
    orbit INTEGER,
    orbit_index INTEGER,
    is_keystone INTEGER NOT NULL,
    is_notable INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE passive_edges (
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (from_node, to_node)
);
CREATE TABLE passive_stats (
    node_id TEXT NOT NULL REFERENCES passive_nodes(id),
    ordinal INTEGER NOT NULL,
    text TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (node_id, ordinal)
);
CREATE TABLE ascendancies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_class TEXT,
    disabled INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE ascendancy_nodes (
    ascendancy_id TEXT NOT NULL,
    node_id TEXT NOT NULL REFERENCES passive_nodes(id),
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (ascendancy_id, node_id)
);
CREATE TABLE item_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    item_class TEXT,
    drop_level INTEGER,
    release_state TEXT,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE item_base_tags (
    item_base_id TEXT NOT NULL REFERENCES item_bases(id),
    tag TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (item_base_id, tag)
);
CREATE TABLE mods (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    generation_type TEXT,
    required_level INTEGER,
    text TEXT,
    payload_json TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id)
);
CREATE TABLE mod_stats (
    mod_id TEXT NOT NULL REFERENCES mods(id),
    ordinal INTEGER NOT NULL,
    stat_id TEXT NOT NULL,
    min_value REAL,
    max_value REAL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (mod_id, ordinal)
);
CREATE TABLE mod_tags (
    mod_id TEXT NOT NULL REFERENCES mods(id),
    tag TEXT NOT NULL,
    kind TEXT NOT NULL,
    weight INTEGER,
    source_id INTEGER NOT NULL REFERENCES data_sources(id),
    PRIMARY KEY (mod_id, tag, kind)
);
CREATE INDEX idx_skill_name ON skills(name);
CREATE INDEX idx_passive_name ON passive_nodes(name);
CREATE INDEX idx_passive_stats_text ON passive_stats(text);
CREATE INDEX idx_item_class ON item_bases(item_class);
CREATE INDEX idx_mod_text ON mods(text);
CREATE INDEX idx_mod_tags_tag ON mod_tags(tag);
"""


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

