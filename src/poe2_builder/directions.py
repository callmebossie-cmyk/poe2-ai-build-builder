from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from .retrieval import BuildIntent, CandidateRetriever


class QualityMode(str, Enum):
    ECONOMY = "economy"
    BALANCED = "balanced"
    DEEP_ANALYSIS = "deep_analysis"
    MAXIMUM = "maximum"


class DirectionValidationError(ValueError):
    """Raised when a provider returns structurally or referentially invalid data."""


class DirectionProvider(Protocol):
    name: str
    kind: str

    def generate(self, request: dict[str, object]) -> str:
        """Return one JSON object matching the build-direction response contract."""


REQUIRED_TEXT_FIELDS = (
    "direction_id",
    "title",
    "concept",
    "class_name",
    "ascendancy_id",
    "skill_id",
    "damage_direction",
    "defense_direction",
    "budget",
)

REQUIRED_LIST_FIELDS = (
    "mechanic_ids",
    "support_ids",
    "passive_ids",
    "item_base_ids",
    "mod_ids",
    "unique_ids",
    "strengths",
    "weaknesses",
    "critical_dependencies",
)


def response_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "minimum_directions": 3,
        "direction_fields": {
            "direction_id": "non-empty string unique in response",
            "title": "non-empty string",
            "concept": "non-empty string",
            "class_name": "base class matching ascendancy_id",
            "ascendancy_id": "ID from candidates.ascendancies",
            "skill_id": "selected skill ID",
            "mechanic_ids": "non-empty IDs from candidates.mechanics",
            "support_ids": "non-empty IDs from candidates.supports",
            "passive_ids": "non-empty IDs from candidates.passives",
            "item_base_ids": "non-empty IDs from candidates.item_bases",
            "mod_ids": "non-empty IDs from candidates.mods",
            "unique_ids": "zero or more IDs from candidates.uniques",
            "damage_direction": "non-empty string",
            "defense_direction": "non-empty string",
            "mapping_viability": {"rating": "integer 1..5", "rationale": "non-empty string"},
            "boss_viability": {"rating": "integer 1..5", "rationale": "non-empty string"},
            "budget": "non-empty string",
            "league_start": {"viable": "boolean", "rationale": "non-empty string"},
            "strengths": "non-empty list of strings",
            "weaknesses": "non-empty list of strings",
            "critical_dependencies": "non-empty list of strings",
        },
    }


@dataclass
class BuildDirectionService:
    database_path: Path
    provider: DirectionProvider
    max_attempts: int = 1

    def generate(
        self,
        intent: BuildIntent,
        quality_mode: QualityMode = QualityMode.BALANCED,
    ) -> dict[str, object]:
        context = CandidateRetriever(self.database_path).retrieve(intent)
        request = {
            "schema_version": 1,
            "task": "generate_build_directions",
            "quality_mode": quality_mode.value,
            "build_context": context,
            "response_contract": response_contract(),
            "instructions": [
                "Return JSON only.",
                "Use only entity IDs present in build_context.",
                "Return at least three materially distinct directions.",
                "Do not claim exact DPS or effects absent from candidate metadata.",
            ],
        }
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        last_error = None
        for attempt in range(1, self.max_attempts + 1):
            raw = self.provider.generate(request)
            try:
                response = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as error:
                last_error = DirectionValidationError(f"Provider returned invalid JSON: {error}")
            else:
                try:
                    directions = validate_direction_response(response, context)
                    break
                except DirectionValidationError as error:
                    last_error = error
            if attempt < self.max_attempts:
                request["validation_feedback"] = str(last_error)
                request["instructions"].append(
                    "The previous attempt failed validation. Regenerate the complete response and fix validation_feedback."
                )
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
            "quality_mode": quality_mode.value,
            "intent": context["intent"],
            "directions": directions,
            "validation": {"schema_valid": True, "entity_references_valid": True},
            "request_bytes": len(json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
            "attempts": attempt,
        }
        runtime_metadata = getattr(self.provider, "last_metadata", None)
        if runtime_metadata:
            result["provider"]["runtime"] = runtime_metadata
        return result


def validate_direction_response(
    response: object,
    context: dict[str, object],
) -> list[dict[str, object]]:
    if not isinstance(response, dict) or response.get("schema_version") != 1:
        raise DirectionValidationError("Response must be an object with schema_version 1")
    directions = response.get("directions")
    if not isinstance(directions, list) or len(directions) < 3:
        raise DirectionValidationError("Response must contain at least three directions")

    candidate_ids = {
        category: {candidate["id"] for candidate in candidates}
        for category, candidates in context["candidates"].items()
    }
    ascendancy_classes = {
        candidate["id"]: candidate["metadata"]["base_class"]
        for candidate in context["candidates"]["ascendancies"]
    }
    reference_fields = {
        "mechanic_ids": "mechanics",
        "support_ids": "supports",
        "passive_ids": "passives",
        "item_base_ids": "item_bases",
        "mod_ids": "mods",
        "unique_ids": "uniques",
    }
    seen_ids = set()
    seen_titles = set()
    seen_reference_signatures = set()
    for index, direction in enumerate(directions):
        location = f"directions[{index}]"
        if not isinstance(direction, dict):
            raise DirectionValidationError(f"{location} must be an object")
        for field in REQUIRED_TEXT_FIELDS:
            if not isinstance(direction.get(field), str) or not direction[field].strip():
                raise DirectionValidationError(f"{location}.{field} must be a non-empty string")
        for field in REQUIRED_LIST_FIELDS:
            value = direction.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                raise DirectionValidationError(f"{location}.{field} must be a list of non-empty strings")
            if field != "unique_ids" and not value:
                raise DirectionValidationError(f"{location}.{field} must not be empty")
        for field in ("mapping_viability", "boss_viability"):
            rating = direction.get(field)
            if not isinstance(rating, dict):
                raise DirectionValidationError(f"{location}.{field} must be an object")
            if type(rating.get("rating")) is not int or not 1 <= rating["rating"] <= 5:
                raise DirectionValidationError(f"{location}.{field}.rating must be an integer from 1 to 5")
            if not isinstance(rating.get("rationale"), str) or not rating["rationale"].strip():
                raise DirectionValidationError(f"{location}.{field}.rationale must be a non-empty string")
        league_start = direction.get("league_start")
        if not isinstance(league_start, dict) or type(league_start.get("viable")) is not bool:
            raise DirectionValidationError(f"{location}.league_start.viable must be a boolean")
        if not isinstance(league_start.get("rationale"), str) or not league_start["rationale"].strip():
            raise DirectionValidationError(f"{location}.league_start.rationale must be a non-empty string")
        if direction["skill_id"] != context["skill"]["id"]:
            raise DirectionValidationError(f"{location}.skill_id is not the selected skill")
        if direction["ascendancy_id"] not in candidate_ids["ascendancies"]:
            raise DirectionValidationError(f"{location}.ascendancy_id is not in the candidate context")
        if direction["class_name"] != ascendancy_classes[direction["ascendancy_id"]]:
            raise DirectionValidationError(f"{location}.class_name does not match its ascendancy")
        for field, category in reference_fields.items():
            invented = set(direction[field]) - candidate_ids[category]
            if invented:
                raise DirectionValidationError(f"{location}.{field} contains unknown IDs: {sorted(invented)}")
        if direction["direction_id"] in seen_ids:
            raise DirectionValidationError("direction_id values must be unique")
        if direction["title"].casefold() in seen_titles:
            raise DirectionValidationError("direction titles must be unique")
        reference_signature = (
            direction["ascendancy_id"],
            tuple(sorted(direction["mechanic_ids"])),
            tuple(sorted(direction["support_ids"])),
            tuple(sorted(direction["passive_ids"])),
            tuple(sorted(direction["item_base_ids"])),
            tuple(sorted(direction["mod_ids"])),
            tuple(sorted(direction["unique_ids"])),
        )
        if reference_signature in seen_reference_signatures:
            raise DirectionValidationError("directions must use materially distinct entity selections")
        seen_ids.add(direction["direction_id"])
        seen_titles.add(direction["title"].casefold())
        seen_reference_signatures.add(reference_signature)
    return directions


class OfflineDeterministicProvider:
    """Contract-test provider. Its output is never represented as an AI recommendation."""

    name = "offline-deterministic-contract-test"
    kind = "offline_test"

    def generate(self, request: dict[str, object]) -> str:
        context = request["build_context"]
        candidates = context["candidates"]
        directions = []
        themes = (
            ("Fast Mapping", 5, 3),
            ("Freeze Control", 4, 4),
            ("Budget Progression", 4, 3),
        )
        for index, (theme, mapping_rating, boss_rating) in enumerate(themes):
            ascendancy = candidates["ascendancies"][index]
            offset = index * 2
            select = lambda category, count: [
                item["id"] for item in candidates[category][offset : offset + count]
            ] or [candidates[category][0]["id"]]
            directions.append(
                {
                    "direction_id": f"offline-contract-{index + 1}",
                    "title": f"{theme} Snipe Contract Example",
                    "concept": "Contract-test composition of retrieved candidates; not an AI build recommendation.",
                    "class_name": ascendancy["metadata"]["base_class"],
                    "ascendancy_id": ascendancy["id"],
                    "skill_id": context["skill"]["id"],
                    "mechanic_ids": select("mechanics", 3),
                    "support_ids": select("supports", 3),
                    "passive_ids": select("passives", 4),
                    "item_base_ids": select("item_bases", 2),
                    "mod_ids": select("mods", 3),
                    "unique_ids": [],
                    "damage_direction": "Use the selected attack, projectile, and bow candidates as a structured direction hypothesis.",
                    "defense_direction": "Defense remains a required narrative field; exact layers need a later validated build stage.",
                    "mapping_viability": {"rating": mapping_rating, "rationale": "Mapping-oriented contract value used to test the schema."},
                    "boss_viability": {"rating": boss_rating, "rationale": "Boss-oriented contract value used to test the schema."},
                    "budget": context["intent"]["budget"],
                    "league_start": {"viable": index != 1, "rationale": "Deterministic contract value, not a market claim."},
                    "strengths": ["Uses only retrieved entity IDs", "Produces a complete structured response"],
                    "weaknesses": ["Generated by an offline contract-test provider"],
                    "critical_dependencies": ["Requires live-provider reasoning before use as a build recommendation"],
                }
            )
        return json.dumps({"schema_version": 1, "directions": directions}, ensure_ascii=False)
