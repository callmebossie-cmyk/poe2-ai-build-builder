from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .database import connect
from .graph import PassiveGraph, PathNotFoundError


@dataclass(frozen=True)
class BuildIntent:
    main_skill: str
    playstyle: str
    goal: str
    budget: str


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    score: int
    reasons: tuple[str, ...]
    source: str
    source_version: str
    metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        return value


CORE_TERMS = {
    "attack": 10,
    "bow": 14,
    "cold": 10,
    "freeze": 12,
    "projectile": 14,
    "area": 8,
    "channel": 8,
    "perfect timing": 10,
}

INTENT_TERMS = {
    "fast": {"speed": 14, "tempo": 12, "fast": 12, "perfect": 8, "repeat": 6},
    "mapping": {"area": 12, "projectile": 10, "chain": 12, "pierce": 10, "clear": 12, "multiple": 8},
    "cheap": {"common": 6, "basic": 5, "simple": 4},
}

LIMITS = {
    "mechanics": 10,
    "supports": 10,
    "passives": 12,
    "ascendancies": 5,
    "item_bases": 8,
    "mods": 12,
    "uniques": 8,
}


def matching_terms(text: str, weighted_terms: dict[str, int]) -> list[tuple[str, int]]:
    folded = text.casefold()
    return [
        (term, weight)
        for term, weight in weighted_terms.items()
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", folded)
    ]


def humanize_tag(tag: str) -> str:
    with_spaces = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", tag.replace("_", " "))
    return " ".join(with_spaces.split())


def source_fields(row: object) -> tuple[str, str]:
    return row["source_name"], row["source_version"]


class CandidateRetriever:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def retrieve(self, intent: BuildIntent) -> dict[str, object]:
        db = connect(self.database_path)
        try:
            skill = db.execute(
                """
                SELECT k.*,d.name AS source_name,d.version AS source_version
                FROM skills k JOIN data_sources d ON d.id=k.source_id
                WHERE lower(k.name)=lower(?)
                """,
                (intent.main_skill,),
            ).fetchone()
            if skill is None:
                raise ValueError(f"Skill is not available in the local database: {intent.main_skill}")
            skill_tags = [
                row[0]
                for row in db.execute("SELECT tag FROM skill_tags WHERE skill_id=?", (skill["id"],))
            ]
            terms = self._terms(intent, skill_tags)
            mechanics = self._mechanics(skill, skill_tags, terms)
            supports, supports_scanned = self._supports(db, skill["id"], terms)
            passives, passives_scanned = self._passives(db, terms)
            ascendancies, ascendancies_scanned = self._ascendancies(db, terms)
            item_bases, bases_scanned = self._item_bases(db, skill_tags, intent)
            mods, mods_scanned = self._mods(db, skill_tags, terms)
            uniques, uniques_scanned = self._uniques(db, skill_tags, intent)
            source = {"name": skill["source_name"], "version": skill["source_version"]}
        finally:
            db.close()

        candidate_sets = {
            "mechanics": mechanics,
            "supports": supports,
            "passives": passives,
            "ascendancies": ascendancies,
            "item_bases": item_bases,
            "mods": mods,
            "uniques": uniques,
        }
        result = {
            "intent": asdict(intent),
            "skill": {
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "tags": sorted(skill_tags, key=str.casefold),
                "source": source,
            },
            "candidates": {
                name: [candidate.to_dict() for candidate in candidates]
                for name, candidates in candidate_sets.items()
            },
            "debug": {
                "terms": terms,
                "scanned": {
                    "supports": supports_scanned,
                    "passives": passives_scanned,
                    "ascendancies": ascendancies_scanned,
                    "item_bases": bases_scanned,
                    "mods": mods_scanned,
                    "uniques": uniques_scanned,
                },
                "returned": {name: len(values) for name, values in candidate_sets.items()},
                "limits": LIMITS,
                "assumptions": {
                    "passive_start_class": "Ranger",
                    "reason": "Snipe is a dexterity-tagged Bow skill and Ranger shares the dexterity-side start with Huntress",
                },
            },
        }
        result["debug"]["serialized_bytes"] = len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        return result

    def _terms(self, intent: BuildIntent, skill_tags: Iterable[str]) -> dict[str, int]:
        terms = dict(CORE_TERMS)
        for tag in skill_tags:
            normalized = humanize_tag(tag).casefold()
            if len(normalized) >= 4:
                terms.setdefault(normalized, 6)
        for value in (intent.playstyle, intent.goal, intent.budget):
            terms.update(INTENT_TERMS.get(value.casefold(), {}))
        return terms

    def _mechanics(self, skill: object, tags: list[str], terms: dict[str, int]) -> list[Candidate]:
        source, version = source_fields(skill)
        candidates = []
        seen = set()
        for tag in dict.fromkeys(tags):
            normalized = humanize_tag(tag)
            identity = normalized.casefold()
            if identity in seen:
                continue
            seen.add(identity)
            matches = matching_terms(normalized, terms)
            if not matches:
                continue
            candidates.append(
                Candidate(
                    id=f"skill-tag:{tag}",
                    name=normalized,
                    score=30 + sum(weight for _term, weight in matches),
                    reasons=("present on the real skill record",) + tuple(f"matches {term}" for term, _weight in matches),
                    source=source,
                    source_version=version,
                    metadata={"skill_id": skill["id"]},
                )
            )
        return self._top(candidates, "mechanics")

    def _supports(self, db: object, skill_id: str, terms: dict[str, int]) -> tuple[list[Candidate], int]:
        rows = db.execute(
            """
            SELECT s.*,d.name AS source_name,d.version AS source_version,c.relationship
            FROM support_compatibility c
            JOIN support_gems s ON s.id=c.support_id
            JOIN data_sources d ON d.id=s.source_id
            WHERE c.skill_id=?
            """,
            (skill_id,),
        ).fetchall()
        candidates = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            gem = payload["gem"]
            searchable = " ".join([row["name"], *gem.get("tags", []), json.dumps(payload["granted_skills"])])
            matches = matching_terms(searchable, terms)
            score = 50 + sum(weight for _term, weight in matches)
            reasons = ["recommended for this skill by the source export"]
            reasons.extend(f"matches {term}" for term, _weight in matches[:4])
            candidates.append(
                Candidate(row["id"], row["name"], score, tuple(reasons), *source_fields(row), {"tags": gem.get("tags", []), "relationship": row["relationship"]})
            )
        return self._top(candidates, "supports"), len(rows)

    def _passives(self, db: object, terms: dict[str, int]) -> tuple[list[Candidate], int]:
        rows = db.execute(
            """
            SELECT n.id,n.name,n.source_id,d.name AS source_name,d.version AS source_version,
                   group_concat(s.text,' | ') AS stat_text
            FROM passive_nodes n JOIN passive_stats s ON s.node_id=n.id
            JOIN data_sources d ON d.id=n.source_id
            WHERE n.ascendancy_id IS NULL AND n.name IS NOT NULL
            GROUP BY n.id,n.name,n.source_id,d.name,d.version
            """
        ).fetchall()
        graph = PassiveGraph.from_database(self.database_path)
        start = graph.class_start("Ranger")
        candidates = []
        for row in rows:
            matches = matching_terms(f"{row['name']} {row['stat_text']}", terms)
            if not matches:
                continue
            try:
                path = graph.shortest_path(start, row["id"])
            except PathNotFoundError:
                continue
            score = 25 + sum(weight for _term, weight in matches) - min(path.point_cost, 20)
            reasons = [f"reachable from Ranger start in {path.point_cost} points"]
            reasons.extend(f"stat text matches {term}" for term, _weight in matches[:4])
            candidates.append(
                Candidate(row["id"], row["name"], score, tuple(reasons), *source_fields(row), {"point_cost": path.point_cost, "stats": row["stat_text"].split(" | ")})
            )
        return self._top(candidates, "passives"), len(rows)

    def _ascendancies(self, db: object, terms: dict[str, int]) -> tuple[list[Candidate], int]:
        rows = db.execute(
            """
            SELECT a.id,a.name,a.base_class,a.source_id,d.name AS source_name,d.version AS source_version,
                   group_concat(ps.text,' | ') AS stat_text
            FROM ascendancies a
            JOIN data_sources d ON d.id=a.source_id
            LEFT JOIN ascendancy_nodes an ON an.ascendancy_id=a.id
            LEFT JOIN passive_stats ps ON ps.node_id=an.node_id
            WHERE a.disabled=0
            GROUP BY a.id,a.name,a.base_class,a.source_id,d.name,d.version
            """
        ).fetchall()
        candidates = []
        for row in rows:
            stat_text = row["stat_text"] or ""
            matches = matching_terms(f"{row['name']} {stat_text}", terms)
            dex_bonus = 12 if row["base_class"] in {"Ranger", "Huntress"} else 0
            if not matches and not dex_bonus:
                continue
            reasons = [f"base class: {row['base_class'] or 'unknown'}"]
            if dex_bonus:
                reasons.append("dexterity-side class fits the Snipe gem requirement")
            reasons.extend(f"node text matches {term}" for term, _weight in matches[:4])
            candidates.append(
                Candidate(row["id"], row["name"], 20 + dex_bonus + sum(weight for _term, weight in matches), tuple(reasons), *source_fields(row), {"base_class": row["base_class"], "matched_terms": [term for term, _weight in matches]})
            )
        return self._top(candidates, "ascendancies"), len(rows)

    def _item_bases(self, db: object, tags: list[str], intent: BuildIntent) -> tuple[list[Candidate], int]:
        item_class = "Bow" if any(tag.casefold() == "bow" for tag in tags) else None
        if item_class is None:
            return [], 0
        rows = db.execute(
            """
            SELECT i.*,d.name AS source_name,d.version AS source_version
            FROM item_bases i JOIN data_sources d ON d.id=i.source_id
            WHERE i.item_class=? AND i.release_state='released'
            """,
            (item_class,),
        ).fetchall()
        candidates = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            properties = payload.get("properties", {})
            drop_level = row["drop_level"] or 0
            cheap_bonus = max(0, 20 - drop_level // 4) if intent.budget.casefold() == "cheap" else 0
            attack_time = properties.get("attack_time")
            speed_bonus = max(0, 10 - int(attack_time or 1000) // 150) if intent.playstyle.casefold() == "fast" else 0
            reasons = ["released Bow base required by Snipe"]
            if cheap_bonus:
                reasons.append(f"low drop level {drop_level} supports a cheap progression path")
            if attack_time:
                reasons.append(f"source attack time: {attack_time} ms")
            candidates.append(
                Candidate(row["id"], row["name"], 30 + cheap_bonus + speed_bonus, tuple(reasons), *source_fields(row), {"drop_level": drop_level, "attack_time_ms": attack_time, "physical_damage": [properties.get("physical_damage_min"), properties.get("physical_damage_max")]})
            )
        return self._top(candidates, "item_bases"), len(rows)

    def _mods(self, db: object, tags: list[str], terms: dict[str, int]) -> tuple[list[Candidate], int]:
        required_tag = "bow" if any(tag.casefold() == "bow" for tag in tags) else None
        if required_tag is None:
            return [], 0
        rows = db.execute(
            """
            SELECT DISTINCT m.*,d.name AS source_name,d.version AS source_version
            FROM mods m JOIN mod_tags t ON t.mod_id=m.id
            JOIN data_sources d ON d.id=m.source_id
            WHERE t.tag=? AND t.kind='spawn' AND t.weight>0
            """,
            (required_tag,),
        ).fetchall()
        candidates = []
        for row in rows:
            searchable = f"{row['name']} {row['text'] or ''}"
            matches = matching_terms(searchable, terms)
            if not matches:
                continue
            reasons = ["can spawn on bows according to source weights"]
            reasons.extend(f"modifier text matches {term}" for term, _weight in matches[:4])
            candidates.append(
                Candidate(row["id"], row["name"], 25 + sum(weight for _term, weight in matches), tuple(reasons), *source_fields(row), {"required_level": row["required_level"], "text": row["text"]})
            )
        return self._top(candidates, "mods"), len(rows)

    def _uniques(self, db: object, tags: list[str], intent: BuildIntent) -> tuple[list[Candidate], int]:
        item_class = "Bow" if any(tag.casefold() == "bow" for tag in tags) else None
        if item_class is None:
            return [], 0
        rows = db.execute(
            """
            SELECT u.*,d.name AS source_name,d.version AS source_version
            FROM unique_items u JOIN data_sources d ON d.id=u.source_id
            WHERE u.item_class=?
            """,
            (item_class,),
        ).fetchall()
        candidates = [
            Candidate(
                row["id"],
                row["name"],
                10,
                ("source identifies this item as a Bow unique", "effect data is unavailable, so no mechanical score was invented"),
                *source_fields(row),
                {"canonical_id": row["canonical_id"], "item_class": row["item_class"], "effect_data_available": False, "budget_fit": "unverified" if intent.budget.casefold() == "cheap" else "not_scored"},
            )
            for row in rows
        ]
        return self._top(candidates, "uniques"), len(rows)

    @staticmethod
    def _top(candidates: list[Candidate], category: str) -> list[Candidate]:
        return sorted(candidates, key=lambda candidate: (-candidate.score, candidate.name.casefold(), candidate.id))[: LIMITS[category]]
