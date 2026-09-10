from __future__ import annotations

import json
import unittest

from poe2_builder.build_chat import (
    BuildChatService,
    BuildChatValidationError,
    OfflineBuildChatProvider,
)


DIRECTION = {
    "ascendancy_id": "Ranger1",
    "skill_id": "SnipePlayer",
    "mechanic_ids": ["skill-tag:Bow"],
    "support_ids": ["SupportOne"],
    "passive_ids": ["123"],
    "item_base_ids": ["BowOne"],
    "mod_ids": ["ModOne"],
    "unique_ids": [],
}
BUILD = {
    "ascendancy_id": "Ranger1",
    "main_skill_id": "SnipePlayer",
    "passive_ids": ["123", "456"],
    "skill_links": [{"skill_id": "SnipePlayer", "support_ids": ["SupportOne"]}],
    "equipment": [{"item_base_id": "BowOne", "mod_ids": ["ModOne"]}],
}


class InventingProvider(OfflineBuildChatProvider):
    def generate(self, request: dict[str, object]) -> str:
        return json.dumps({"schema_version": 1, "answer": "Invented", "grounded_entity_ids": ["Fake"], "advisory": False})


class UnsupportedClaimProvider(OfflineBuildChatProvider):
    def generate(self, request: dict[str, object]) -> str:
        return json.dumps({"schema_version": 1, "answer": "This grants 10% more damage.", "grounded_entity_ids": [], "advisory": False})


class BuildChatTests(unittest.TestCase):
    def test_grounded_answer_passes(self) -> None:
        result = BuildChatService(OfflineBuildChatProvider()).answer(DIRECTION, BUILD, "Why Snipe?", [])
        self.assertEqual(result["grounded_entity_ids"], ["SnipePlayer"])
        self.assertTrue(result["advisory"])

    def test_unknown_entity_is_rejected(self) -> None:
        with self.assertRaisesRegex(BuildChatValidationError, "unknown entity"):
            BuildChatService(InventingProvider()).answer(DIRECTION, BUILD, "Why?", [])

    def test_unsupported_quantitative_claim_is_rejected(self) -> None:
        with self.assertRaisesRegex(BuildChatValidationError, "unsupported"):
            BuildChatService(UnsupportedClaimProvider()).answer(DIRECTION, BUILD, "How much?", [])

    def test_history_and_question_are_bounded(self) -> None:
        with self.assertRaisesRegex(BuildChatValidationError, "at most 12"):
            BuildChatService(OfflineBuildChatProvider()).answer(
                DIRECTION, BUILD, "Why?", [{"role": "user", "content": "x"}] * 13
            )
        with self.assertRaisesRegex(BuildChatValidationError, "1 to 2000"):
            BuildChatService(OfflineBuildChatProvider()).answer(DIRECTION, BUILD, "", [])
