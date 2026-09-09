from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field


class OllamaProviderError(RuntimeError):
    """Raised when the local Ollama endpoint cannot provide a usable response."""


def direction_json_schema(context: dict[str, object]) -> dict[str, object]:
    candidate_ids = {
        category: [candidate["id"] for candidate in candidates]
        for category, candidates in context["candidates"].items()
    }
    string = {"type": "string", "minLength": 1}

    def id_list(category: str, *, minimum: int = 1) -> dict[str, object]:
        return {
            "type": "array",
            "items": {"type": "string", "enum": candidate_ids[category]},
            "minItems": minimum,
            "uniqueItems": True,
        }

    rating = {
        "type": "object",
        "properties": {
            "rating": {"type": "integer", "minimum": 1, "maximum": 5},
            "rationale": string,
        },
        "required": ["rating", "rationale"],
        "additionalProperties": False,
    }
    league_start = {
        "type": "object",
        "properties": {"viable": {"type": "boolean"}, "rationale": string},
        "required": ["viable", "rationale"],
        "additionalProperties": False,
    }
    properties = {
        "direction_id": string,
        "title": string,
        "concept": string,
        "class_name": string,
        "ascendancy_id": {"type": "string", "enum": candidate_ids["ascendancies"]},
        "skill_id": {"type": "string", "enum": [context["skill"]["id"]]},
        "mechanic_ids": id_list("mechanics"),
        "support_ids": id_list("supports"),
        "passive_ids": id_list("passives"),
        "item_base_ids": id_list("item_bases"),
        "mod_ids": id_list("mods"),
        "unique_ids": id_list("uniques", minimum=0),
        "damage_direction": string,
        "defense_direction": string,
        "mapping_viability": rating,
        "boss_viability": rating,
        "budget": string,
        "league_start": league_start,
        "strengths": {"type": "array", "items": string, "minItems": 1},
        "weaknesses": {"type": "array", "items": string, "minItems": 1},
        "critical_dependencies": {"type": "array", "items": string, "minItems": 1},
    }
    direction = {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "directions": {"type": "array", "items": direction, "minItems": 3},
        },
        "required": ["schema_version", "directions"],
        "additionalProperties": False,
    }


def full_build_json_schema(context: dict[str, object]) -> dict[str, object]:
    direction = context["selected_direction"]
    passive_ids = context["suggested_connected_passive_ids"]
    requirements = context.get("equipment_requirements", {})
    minimum_attributes = requirements.get("minimum_attributes", {})
    string = {"type": "string", "minLength": 1}
    attributes = {
        "type": "object",
        "properties": {
            name: {"type": "integer", "minimum": minimum_attributes.get(name, 0)}
            for name in ("strength", "dexterity", "intelligence")
        },
        "required": ["strength", "dexterity", "intelligence"],
        "additionalProperties": False,
    }
    skill_link = {
        "type": "object",
        "properties": {
            "skill_id": {"type": "string", "enum": [direction["skill_id"]]},
            "support_ids": {
                "type": "array",
                "items": {"type": "string", "enum": direction["support_ids"]},
                "minItems": 1,
                "uniqueItems": True,
            },
        },
        "required": ["skill_id", "support_ids"],
        "additionalProperties": False,
    }
    equipment = {
        "type": "object",
        "properties": {
            "slot": string,
            "item_base_id": {"type": "string", "enum": direction["item_base_ids"]},
            "mod_ids": {
                "type": "array",
                "items": {"type": "string", "enum": direction["mod_ids"]},
                "minItems": 1,
                "uniqueItems": True,
            },
        },
        "required": ["slot", "item_base_id", "mod_ids"],
        "additionalProperties": False,
    }
    properties = {
        "build_id": string,
        "title": string,
        "level": {
            "type": "integer",
            "minimum": requirements.get("minimum_build_level", 1),
            "maximum": 100,
        },
        "class_name": {"type": "string", "enum": [direction["class_name"]]},
        "ascendancy_id": {"type": "string", "enum": [direction["ascendancy_id"]]},
        "main_skill_id": {"type": "string", "enum": [direction["skill_id"]]},
        "attributes": attributes,
        "passive_ids": {
            "type": "array",
            "items": {"type": "string", "enum": passive_ids},
            "minItems": len(passive_ids),
            "maxItems": len(passive_ids),
            "uniqueItems": True,
        },
        "skill_links": {
            "type": "array",
            "items": skill_link,
            "minItems": 1,
            "maxItems": 1,
        },
        "equipment": {"type": "array", "items": equipment, "minItems": 1},
        "passive_direction": string,
        "affix_priorities": {"type": "array", "items": string, "minItems": 1},
        "defense": string,
        "resource_solution": string,
        "leveling_concept": string,
        "upgrade_order": {"type": "array", "items": string, "minItems": 1},
        "rotation": string,
    }
    build = {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "build": build,
        },
        "required": ["schema_version", "build"],
        "additionalProperties": False,
    }


@dataclass
class OllamaProvider:
    model: str = "qwen3:8b"
    endpoint: str = "http://127.0.0.1:11434/api/chat"
    timeout_seconds: int = 900
    name: str = field(init=False)
    kind: str = field(init=False, default="live_ai")
    last_metadata: dict[str, object] | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.name = f"ollama:{self.model}"

    def generate(self, request: dict[str, object]) -> str:
        context = request["build_context"]
        if request.get("task") == "generate_full_build":
            schema = full_build_json_schema(context)
            task_instruction = (
                "Expand the one selected direction into one full build. Copy the complete supplied "
                "passive allocation and choose only entity IDs present in that direction."
            )
        else:
            schema = direction_json_schema(context)
            task_instruction = "Make the three build directions materially distinct."
        system = (
            "You are the theorycrafting component of a Path of Exile 2 build planner. "
            "Treat the supplied context as the complete allowed entity set. Return only the "
            "requested JSON. Do not invent IDs, exact DPS, prices, item effects, or game rules "
            f"absent from the context. {task_instruction}"
        )
        prompt = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0.15,
                "seed": 42,
                "num_ctx": 32768,
                "num_predict": 6000,
            },
            "keep_alive": "10m",
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        http_request = urllib.request.Request(
            self.endpoint,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise OllamaProviderError(f"Ollama request failed: {error}") from error
        try:
            content = result["message"]["content"]
        except (KeyError, TypeError) as error:
            raise OllamaProviderError("Ollama response did not contain message.content") from error
        if not isinstance(content, str) or not content.strip():
            raise OllamaProviderError("Ollama returned empty message content")
        self.last_metadata = {
            "model": result.get("model", self.model),
            "done_reason": result.get("done_reason"),
            "total_duration_ns": result.get("total_duration"),
            "load_duration_ns": result.get("load_duration"),
            "prompt_eval_count": result.get("prompt_eval_count"),
            "eval_count": result.get("eval_count"),
        }
        return content
