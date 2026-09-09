from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .database import connect
from .graph import PassiveGraph


class FullBuildValidationError(ValueError):
    """Raised when a full build violates the deterministic contract."""


class FullBuildProvider(Protocol):
    name: str
    kind: str

    def generate(self, request: dict[str, object]) -> str:
        """Return one JSON object matching the full-build response contract."""


NARRATIVE_FIELDS = (
    "passive_direction",
    "defense",
    "resource_solution",
    "leveling_concept",
    "rotation",
)

LIST_TEXT_FIELDS = ("affix_priorities", "upgrade_order")

UNSUPPORTED_QUANTITATIVE_CLAIM = re.compile(
    r"(?:\d|%|\b(?:dps|damage per second|divine|chaos|exalted)\b)", re.IGNORECASE
)


def full_build_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "build_fields": {
            "build_id": "non-empty string",
            "title": "non-empty string",
            "level": "integer 1..100",
            "class_name": "must match selected direction",
            "ascendancy_id": "must match selected direction and class",
            "main_skill_id": "must match selected direction",
            "attributes": "strength, dexterity, intelligence non-negative integers",
            "passive_ids": "connected allocation including the class start",
            "skill_links": "main skill and source-compatible support IDs",
            "equipment": "unique slots with existing released bases and compatible mods",
            "affix_priorities": "non-empty list of strings",
            "defense": "non-empty string",
            "resource_solution": "non-empty string",
            "leveling_concept": "non-empty string",
            "upgrade_order": "non-empty list of strings",
            "rotation": "non-empty string",
        },
        "claim_boundary": (
            "narrative fields are advisory theorycraft; exact numeric DPS, percentages, "
            "prices, and currency claims are forbidden until backed by a calculator"
        ),
    }


def build_full_context(database_path: Path, direction: dict[str, object]) -> dict[str, object]:
    required = ("direction_id", "class_name", "ascendancy_id", "skill_id")
    for field in required:
        if not isinstance(direction.get(field), str) or not direction[field]:
            raise FullBuildValidationError(f"direction.{field} must be a non-empty string")
    graph = PassiveGraph.from_database(
        database_path, allowed_ascendancy=direction["ascendancy_id"]
    )
    start = graph.class_start(direction["class_name"])
    suggested = {start}
    for target in direction.get("passive_ids", []):
        suggested.update(graph.shortest_path(start, target).nodes)

    db = connect(database_path)
    try:
        character = db.execute(
            "SELECT base_strength,base_dexterity,base_intelligence FROM character_classes WHERE name=?",
            (direction["class_name"],),
        ).fetchone()
        if character is None:
            raise FullBuildValidationError("direction class does not exist")
        ascendancy = db.execute(
            "SELECT base_class,disabled FROM ascendancies WHERE id=?",
            (direction["ascendancy_id"],),
        ).fetchone()
        if ascendancy is None or ascendancy["base_class"] != direction["class_name"] or ascendancy["disabled"]:
            raise FullBuildValidationError("direction ascendancy is unavailable or mismatched")
        skill = db.execute("SELECT id,name FROM skills WHERE id=?", (direction["skill_id"],)).fetchone()
        if skill is None:
            raise FullBuildValidationError("direction skill does not exist")
        base_requirements = []
        for base_id in direction.get("item_base_ids", []):
            base = db.execute(
                "SELECT id,name,drop_level,payload_json FROM item_bases WHERE id=?", (base_id,)
            ).fetchone()
            if base is None:
                raise FullBuildValidationError(f"direction item base does not exist: {base_id}")
            requirements = json.loads(base["payload_json"]).get("requirements", {})
            base_requirements.append(
                {
                    "id": base["id"],
                    "name": base["name"],
                    "required_level": max(base["drop_level"] or 1, requirements.get("level", 1)),
                    "required_strength": requirements.get("strength", 0),
                    "required_dexterity": requirements.get("dexterity", 0),
                    "required_intelligence": requirements.get("intelligence", 0),
                }
            )
        mod_requirements = []
        for mod_id in direction.get("mod_ids", []):
            mod = db.execute("SELECT id,required_level FROM mods WHERE id=?", (mod_id,)).fetchone()
            if mod is None:
                raise FullBuildValidationError(f"direction mod does not exist: {mod_id}")
            mod_requirements.append({"id": mod["id"], "required_level": mod["required_level"] or 1})
    finally:
        db.close()
    return {
        "selected_direction": direction,
        "character": {
            "class_name": direction["class_name"],
            "base_strength": character["base_strength"],
            "base_dexterity": character["base_dexterity"],
            "base_intelligence": character["base_intelligence"],
            "class_start_id": start,
        },
        "skill": dict(skill),
        "suggested_connected_passive_ids": sorted(suggested),
        "equipment_requirements": {
            "item_bases": base_requirements,
            "mods": mod_requirements,
            "minimum_build_level": max(
                [1]
                + [item["required_level"] for item in base_requirements]
                + [mod["required_level"] for mod in mod_requirements]
            ),
            "minimum_attributes": {
                attribute: max(
                    [character[f"base_{attribute}"]]
                    + [item[f"required_{attribute}"] for item in base_requirements]
                )
                for attribute in ("strength", "dexterity", "intelligence")
            },
        },
    }


@dataclass
class FullBuildService:
    database_path: Path
    provider: FullBuildProvider
    max_attempts: int = 1

    def generate(self, direction: dict[str, object]) -> dict[str, object]:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        context = build_full_context(self.database_path, direction)
        request = {
            "schema_version": 1,
            "task": "generate_full_build",
            "build_context": context,
            "response_contract": full_build_contract(),
            "instructions": [
                "Return JSON only.",
                "Expand only the selected direction and use only its referenced entity IDs.",
                "Use suggested_connected_passive_ids as the complete passive allocation.",
                "Do not invent effects, requirements, prices, or exact DPS.",
            ],
        }
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            raw = self.provider.generate(request)
            try:
                response = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as error:
                last_error = FullBuildValidationError(f"Provider returned invalid JSON: {error}")
            else:
                try:
                    build = validate_full_build(response, context, self.database_path)
                    break
                except FullBuildValidationError as error:
                    last_error = error
            if attempt < self.max_attempts:
                request["validation_feedback"] = str(last_error)
        else:
            raise last_error
        result = {
            "schema_version": 1,
            "provider": {
                "name": self.provider.name,
                "kind": self.provider.kind,
                "is_live_ai": self.provider.kind == "live_ai",
                "output_status": "ai_generated" if self.provider.kind == "live_ai" else "test_only_not_ai_recommendation",
            },
            "selected_direction_id": direction["direction_id"],
            "build": build,
            "validation": {
                "schema_valid": True,
                "entity_references_valid": True,
                "passive_path_valid": True,
                "support_compatibility_valid": True,
                "equipment_requirements_valid": True,
                "character_requirements_valid": True,
                "basic_conflicts_valid": True,
                "unsupported_quantitative_claims_absent": True,
            },
            "claim_boundaries": {
                "deterministically_validated": [
                    "entity references",
                    "passive connectivity",
                    "support type compatibility",
                    "equipment spawn, level, attribute, affix-count, and mod-group rules",
                    "class base attributes",
                ],
                "advisory_only": list(NARRATIVE_FIELDS) + list(LIST_TEXT_FIELDS),
                "resource_status": "advisory_not_calculated",
                "exact_dps_status": "not_calculated",
                "price_status": "not_calculated",
            },
            "request_bytes": len(json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
            "attempts": attempt,
        }
        runtime_metadata = getattr(self.provider, "last_metadata", None)
        if runtime_metadata:
            result["provider"]["runtime"] = runtime_metadata
        return result


def _non_empty_text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FullBuildValidationError(f"{location} must be a non-empty string")
    return value


def _support_accepts_skill(support_payload: dict[str, object], skill_types: set[str]) -> bool:
    granted_skills = support_payload.get("granted_skills", {})
    if not isinstance(granted_skills, dict):
        return False
    rules = [
        granted.get("support_gem")
        for granted in granted_skills.values()
        if isinstance(granted, dict) and granted.get("is_support") is True
    ]
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        allowed = set(rule.get("allowed_types") or [])
        excluded = set(rule.get("excluded_types") or [])
        if (not allowed or allowed & skill_types) and not excluded & skill_types:
            return True
    return False


def validate_full_build(
    response: object, context: dict[str, object], database_path: Path
) -> dict[str, object]:
    if not isinstance(response, dict) or response.get("schema_version") != 1:
        raise FullBuildValidationError("Response must be an object with schema_version 1")
    build = response.get("build")
    if not isinstance(build, dict):
        raise FullBuildValidationError("build must be an object")
    for field in ("build_id", "title", *NARRATIVE_FIELDS):
        _non_empty_text(build.get(field), f"build.{field}")
    for field in NARRATIVE_FIELDS:
        if UNSUPPORTED_QUANTITATIVE_CLAIM.search(build[field]):
            raise FullBuildValidationError(
                f"build.{field} contains an unsupported quantitative DPS, percentage, or price claim"
            )
    for field in LIST_TEXT_FIELDS:
        values = build.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(x, str) and x.strip() for x in values):
            raise FullBuildValidationError(f"build.{field} must be a non-empty list of strings")
    if type(build.get("level")) is not int or not 1 <= build["level"] <= 100:
        raise FullBuildValidationError("build.level must be an integer from 1 to 100")

    direction = context["selected_direction"]
    expected = {
        "class_name": direction["class_name"],
        "ascendancy_id": direction["ascendancy_id"],
        "main_skill_id": direction["skill_id"],
    }
    for field, value in expected.items():
        if build.get(field) != value:
            raise FullBuildValidationError(f"build.{field} does not match the selected direction")
    attributes = build.get("attributes")
    if not isinstance(attributes, dict):
        raise FullBuildValidationError("build.attributes must be an object")
    for attribute in ("strength", "dexterity", "intelligence"):
        if type(attributes.get(attribute)) is not int or attributes[attribute] < 0:
            raise FullBuildValidationError(f"build.attributes.{attribute} must be a non-negative integer")
        base_attribute = context["character"][f"base_{attribute}"]
        if attributes[attribute] < base_attribute:
            raise FullBuildValidationError(
                f"build.attributes.{attribute} cannot be below the class base value"
            )

    passive_ids = build.get("passive_ids")
    if not isinstance(passive_ids, list) or not passive_ids or len(passive_ids) != len(set(passive_ids)):
        raise FullBuildValidationError("build.passive_ids must be a non-empty unique list")
    if set(passive_ids) != set(context["suggested_connected_passive_ids"]):
        raise FullBuildValidationError("build.passive_ids must equal the bounded connected allocation")
    graph = PassiveGraph.from_database(database_path, allowed_ascendancy=build["ascendancy_id"])
    start = graph.class_start(build["class_name"])
    if start not in passive_ids:
        raise FullBuildValidationError("passive allocation must include the class start")
    allocated = set(passive_ids)
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbour in graph.adjacency[current] & allocated:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    if visited != allocated:
        raise FullBuildValidationError("passive allocation is not connected")

    allowed = {
        "support_ids": set(direction["support_ids"]),
        "item_base_ids": set(direction["item_base_ids"]),
        "mod_ids": set(direction["mod_ids"]),
        "unique_ids": set(direction["unique_ids"]),
    }
    skill_links = build.get("skill_links")
    if not isinstance(skill_links, list) or len(skill_links) != 1 or not isinstance(skill_links[0], dict):
        raise FullBuildValidationError("build.skill_links must contain exactly the main skill link")
    link = skill_links[0]
    if link.get("skill_id") != build["main_skill_id"]:
        raise FullBuildValidationError("skill link must use the main skill")
    support_ids = link.get("support_ids")
    if not isinstance(support_ids, list) or not support_ids or not set(support_ids) <= allowed["support_ids"]:
        raise FullBuildValidationError("skill link contains unsupported or out-of-direction supports")
    if len(support_ids) != len(set(support_ids)):
        raise FullBuildValidationError("skill link contains duplicate supports")

    equipment = build.get("equipment")
    if not isinstance(equipment, list) or not equipment:
        raise FullBuildValidationError("build.equipment must be a non-empty list")
    slots: set[str] = set()
    db = connect(database_path)
    try:
        skill_row = db.execute("SELECT payload_json FROM skills WHERE id=?", (build["main_skill_id"],)).fetchone()
        if skill_row is None:
            raise FullBuildValidationError("main skill is missing during rule validation")
        skill_types = set(json.loads(skill_row["payload_json"]).get("active_skill", {}).get("types", []))
        for support_id in support_ids:
            row = db.execute(
                """SELECT c.relationship,s.payload_json
                   FROM support_compatibility c
                   JOIN support_gems s ON s.id=c.support_id
                   WHERE c.skill_id=? AND c.support_id=?""",
                (build["main_skill_id"], support_id),
            ).fetchone()
            if row is None or row["relationship"] != "recommended_by_source":
                raise FullBuildValidationError(f"support is not source-compatible: {support_id}")
            if not _support_accepts_skill(json.loads(row["payload_json"]), skill_types):
                raise FullBuildValidationError(f"support type rules reject the main skill: {support_id}")
        for index, item in enumerate(equipment):
            if not isinstance(item, dict):
                raise FullBuildValidationError(f"build.equipment[{index}] must be an object")
            slot = _non_empty_text(item.get("slot"), f"build.equipment[{index}].slot")
            normalized_slot = slot.casefold()
            if normalized_slot in slots:
                raise FullBuildValidationError(f"duplicate equipment slot: {slot}")
            slots.add(normalized_slot)
            base_id = item.get("item_base_id")
            mod_ids = item.get("mod_ids")
            if base_id not in allowed["item_base_ids"]:
                raise FullBuildValidationError(f"equipment base is outside the selected direction: {base_id}")
            if not isinstance(mod_ids, list) or not mod_ids or not set(mod_ids) <= allowed["mod_ids"]:
                raise FullBuildValidationError("equipment contains unknown or out-of-direction mods")
            if len(mod_ids) != len(set(mod_ids)):
                raise FullBuildValidationError("equipment contains duplicate mods")
            base = db.execute(
                "SELECT item_class,drop_level,release_state,payload_json FROM item_bases WHERE id=?",
                (base_id,),
            ).fetchone()
            if base is None or base["release_state"] != "released" or base["item_class"] != "Bow":
                raise FullBuildValidationError("Snipe primary equipment must be a released Bow base")
            payload = json.loads(base["payload_json"])
            requirements = payload.get("requirements", {})
            if build["level"] < max(base["drop_level"] or 1, requirements.get("level", 1)):
                raise FullBuildValidationError("build level is below equipment requirement")
            for attribute in ("strength", "dexterity", "intelligence"):
                if attributes[attribute] < requirements.get(attribute, 0):
                    raise FullBuildValidationError(f"build lacks {attribute} for equipment")
            base_tags = set(payload.get("tags", []))
            occupied_groups: set[str] = set()
            affix_counts = {"prefix": 0, "suffix": 0}
            for mod_id in mod_ids:
                mod = db.execute(
                    "SELECT generation_type,required_level,payload_json FROM mods WHERE id=?", (mod_id,)
                ).fetchone()
                if mod is None or build["level"] < (mod["required_level"] or 1):
                    raise FullBuildValidationError(f"mod is unavailable at build level: {mod_id}")
                spawn_tags = {
                    row["tag"]
                    for row in db.execute(
                        "SELECT tag FROM mod_tags WHERE mod_id=? AND kind='spawn' AND weight>0",
                        (mod_id,),
                    )
                }
                if not base_tags & spawn_tags:
                    raise FullBuildValidationError(f"mod cannot spawn on selected base: {mod_id}")
                mod_payload = json.loads(mod["payload_json"])
                groups = set(mod_payload.get("groups", []))
                conflict = occupied_groups & groups
                if conflict:
                    raise FullBuildValidationError(
                        f"equipment mods share an exclusive group: {sorted(conflict)[0]}"
                    )
                occupied_groups.update(groups)
                if mod["generation_type"] in affix_counts:
                    affix_counts[mod["generation_type"]] += 1
                    if affix_counts[mod["generation_type"]] > 3:
                        raise FullBuildValidationError(
                            f"equipment exceeds three {mod['generation_type']} modifiers"
                        )
    finally:
        db.close()
    return build


class OfflineFullBuildProvider:
    """Deterministic fixture that exercises validation without claiming AI quality."""

    name = "offline-full-build-contract-test"
    kind = "offline_test"

    def generate(self, request: dict[str, object]) -> str:
        context = request["build_context"]
        direction = context["selected_direction"]
        build = {
            "build_id": "offline-full-build-1",
            "title": f"{direction['title']} Contract Fixture",
            "level": 70,
            "class_name": direction["class_name"],
            "ascendancy_id": direction["ascendancy_id"],
            "main_skill_id": direction["skill_id"],
            "attributes": {"strength": 20, "dexterity": 100, "intelligence": 20},
            "passive_ids": context["suggested_connected_passive_ids"],
            "skill_links": [{"skill_id": direction["skill_id"], "support_ids": direction["support_ids"]}],
            "equipment": [{"slot": "primary_weapon", "item_base_id": direction["item_base_ids"][0], "mod_ids": direction["mod_ids"]}],
            "passive_direction": "Connected contract fixture using the bounded path supplied by deterministic graph code.",
            "affix_priorities": ["Use only the selected direction mod IDs"],
            "defense": "Narrative placeholder for contract testing, not a recommendation.",
            "resource_solution": "Narrative placeholder for contract testing, not a recommendation.",
            "leveling_concept": "Respect recorded item and mod level requirements.",
            "upgrade_order": ["Equip the selected released bow base", "Add compatible selected mods"],
            "rotation": "Narrative placeholder for contract testing, not a recommendation.",
        }
        return json.dumps({"schema_version": 1, "build": build}, ensure_ascii=False)
