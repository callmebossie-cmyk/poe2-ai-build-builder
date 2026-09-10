from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .full_builds import UNSUPPORTED_QUANTITATIVE_CLAIM


class BuildChatValidationError(ValueError):
    """Raised when a build-chat request or response violates its bounded contract."""


class BuildChatProvider(Protocol):
    name: str
    kind: str

    def generate(self, request: dict[str, object]) -> str: ...


def chat_response_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "fields": {
            "answer": "non-empty plain text",
            "grounded_entity_ids": "IDs present in the supplied validated build or direction",
            "advisory": "true when the answer includes qualitative or uncalculated guidance",
        },
    }


def allowed_entity_ids(direction: dict[str, object], build: dict[str, object]) -> set[str]:
    allowed: set[str] = set()
    for field in ("ascendancy_id", "skill_id"):
        value = direction.get(field)
        if isinstance(value, str):
            allowed.add(value)
    for field in ("mechanic_ids", "support_ids", "passive_ids", "item_base_ids", "mod_ids", "unique_ids"):
        values = direction.get(field, [])
        if isinstance(values, list):
            allowed.update(value for value in values if isinstance(value, str))
    for field in ("ascendancy_id", "main_skill_id"):
        value = build.get(field)
        if isinstance(value, str):
            allowed.add(value)
    allowed.update(value for value in build.get("passive_ids", []) if isinstance(value, str))
    for link in build.get("skill_links", []):
        if isinstance(link, dict):
            values = [link.get("skill_id"), *link.get("support_ids", [])]
            allowed.update(value for value in values if isinstance(value, str))
    for item in build.get("equipment", []):
        if isinstance(item, dict):
            values = [item.get("item_base_id"), *item.get("mod_ids", [])]
            allowed.update(value for value in values if isinstance(value, str))
    return allowed


def validate_chat_input(question: object, history: object) -> list[dict[str, str]]:
    if not isinstance(question, str) or not question.strip() or len(question) > 2_000:
        raise BuildChatValidationError("question must contain 1 to 2000 characters")
    if not isinstance(history, list) or len(history) > 12:
        raise BuildChatValidationError("history must contain at most 12 messages")
    validated = []
    for index, message in enumerate(history):
        if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
            raise BuildChatValidationError(f"history[{index}] has an invalid role")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 4_000:
            raise BuildChatValidationError(f"history[{index}].content is invalid")
        validated.append({"role": message["role"], "content": content})
    return validated


@dataclass
class BuildChatService:
    provider: BuildChatProvider

    def answer(self, direction: dict[str, object], build: dict[str, object], question: str,
               history: list[dict[str, str]], evidence: dict[str, object] | None = None) -> dict[str, object]:
        validated_history = validate_chat_input(question, history)
        allowed_ids = allowed_entity_ids(direction, build)
        request = {
            "schema_version": 1,
            "task": "answer_build_question",
            "validated_build": build,
            "selected_direction": direction,
            "build_evidence": evidence or {},
            "allowed_entity_ids": sorted(allowed_ids),
            "conversation": [*validated_history, {"role": "user", "content": question.strip()}],
            "response_contract": chat_response_contract(),
            "claim_boundaries": [
                "Do not invent game rules, entity IDs, exact DPS, prices, or percentages.",
                "Say when the supplied build does not contain enough evidence.",
                "Treat qualitative defense, resource, rotation, and performance guidance as advisory.",
                "Do not claim that a suggested build change has been validated.",
            ],
        }
        last_error: BuildChatValidationError | None = None
        for attempt in range(1, 4):
            try:
                response = json.loads(self.provider.generate(request))
                answer, entity_ids, advisory = _validate_chat_response(response, allowed_ids)
            except (json.JSONDecodeError, TypeError, BuildChatValidationError) as error:
                last_error = error if isinstance(error, BuildChatValidationError) else BuildChatValidationError(
                    f"Provider returned invalid JSON: {error}"
                )
                if attempt < 3:
                    request["validation_feedback"] = str(last_error)
                    continue
                raise last_error
            return {
                "schema_version": 1,
                "provider": {"name": self.provider.name, "kind": self.provider.kind},
                "answer": answer,
                "grounded_entity_ids": entity_ids,
                "advisory": advisory,
                "attempts": attempt,
            }
        raise last_error  # pragma: no cover


def _validate_chat_response(response: object, allowed_ids: set[str]) -> tuple[str, list[str], bool]:
    if not isinstance(response, dict) or response.get("schema_version") != 1:
        raise BuildChatValidationError("response must have schema_version 1")
    answer = response.get("answer")
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 8_000:
        raise BuildChatValidationError("answer must contain 1 to 8000 characters")
    if UNSUPPORTED_QUANTITATIVE_CLAIM.search(answer):
        raise BuildChatValidationError("answer contains an unsupported DPS, percentage, or price claim")
    entity_ids = response.get("grounded_entity_ids")
    if not isinstance(entity_ids, list) or not all(isinstance(value, str) for value in entity_ids):
        raise BuildChatValidationError("grounded_entity_ids must be a list of strings")
    unknown = set(entity_ids) - allowed_ids
    if unknown:
        raise BuildChatValidationError(f"answer references unknown entity IDs: {sorted(unknown)}")
    advisory = response.get("advisory")
    if type(advisory) is not bool:
        raise BuildChatValidationError("advisory must be a boolean")
    return answer.strip(), entity_ids, advisory


class OfflineBuildChatProvider:
    name = "offline-build-chat-contract-test"
    kind = "offline_test"

    def generate(self, request: dict[str, object]) -> str:
        build = request["validated_build"]
        return json.dumps({
            "schema_version": 1,
            "answer": "This contract-test answer is grounded in the selected main skill.",
            "grounded_entity_ids": [build["main_skill_id"]],
            "advisory": True,
        })
