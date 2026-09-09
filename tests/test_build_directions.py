from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from poe2_builder.directions import (
    BuildDirectionService,
    DirectionValidationError,
    OfflineDeterministicProvider,
    QualityMode,
    validate_direction_response,
)
from poe2_builder.retrieval import BuildIntent, CandidateRetriever


class CapturingProvider(OfflineDeterministicProvider):
    def __init__(self) -> None:
        self.request = None

    def generate(self, request: dict[str, object]) -> str:
        self.request = request
        return super().generate(request)


class FailsOnceProvider(OfflineDeterministicProvider):
    def __init__(self) -> None:
        self.calls = 0
        self.feedback = None

    def generate(self, request: dict[str, object]) -> str:
        self.calls += 1
        if self.calls == 1:
            return "not json"
        self.feedback = request.get("validation_feedback")
        return super().generate(request)


class BuildDirectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = Path("data/poe2.db")
        if not cls.database.exists():
            raise unittest.SkipTest("Run the real-data importer before this integration test")
        cls.intent = BuildIntent("Snipe", "Fast", "Mapping", "Cheap")
        cls.context = CandidateRetriever(cls.database).retrieve(cls.intent)

    def test_offline_provider_returns_three_valid_distinct_directions(self) -> None:
        result = BuildDirectionService(
            self.database, OfflineDeterministicProvider()
        ).generate(self.intent, QualityMode.BALANCED)
        self.assertEqual(len(result["directions"]), 3)
        self.assertEqual(len({item["direction_id"] for item in result["directions"]}), 3)
        self.assertTrue(result["validation"]["schema_valid"])
        self.assertTrue(result["validation"]["entity_references_valid"])

    def test_offline_output_is_prominently_labeled_as_test_only(self) -> None:
        result = BuildDirectionService(
            self.database, OfflineDeterministicProvider()
        ).generate(self.intent)
        self.assertFalse(result["provider"]["is_live_ai"])
        self.assertEqual(result["provider"]["output_status"], "test_only_not_ai_recommendation")
        self.assertTrue(
            all("not an AI build recommendation" in item["concept"] for item in result["directions"])
        )

    def test_provider_receives_only_bounded_context_and_contract(self) -> None:
        provider = CapturingProvider()
        result = BuildDirectionService(self.database, provider).generate(self.intent)
        self.assertIsNotNone(provider.request)
        self.assertIn("build_context", provider.request)
        self.assertIn("response_contract", provider.request)
        serialized = json.dumps(provider.request)
        self.assertNotIn("payload_json", serialized)
        self.assertNotIn(str(self.database), serialized)
        self.assertLess(result["request_bytes"], 50_000)

    def test_invented_entity_reference_is_rejected(self) -> None:
        raw = OfflineDeterministicProvider().generate(
            {"build_context": self.context}
        )
        response = json.loads(raw)
        response["directions"][0]["support_ids"].append("InventedSupportGem")
        with self.assertRaisesRegex(DirectionValidationError, "unknown IDs"):
            validate_direction_response(response, self.context)

    def test_mismatched_class_and_ascendancy_are_rejected(self) -> None:
        response = json.loads(
            OfflineDeterministicProvider().generate({"build_context": self.context})
        )
        response["directions"][0]["class_name"] = "Definitely Wrong"
        with self.assertRaisesRegex(DirectionValidationError, "does not match"):
            validate_direction_response(response, self.context)

    def test_cosmetically_renamed_duplicate_direction_is_rejected(self) -> None:
        response = json.loads(
            OfflineDeterministicProvider().generate({"build_context": self.context})
        )
        duplicate = deepcopy(response["directions"][0])
        duplicate["direction_id"] = "renamed-copy"
        duplicate["title"] = "A Different Title"
        response["directions"][2] = duplicate
        with self.assertRaisesRegex(DirectionValidationError, "materially distinct"):
            validate_direction_response(response, self.context)

    def test_malformed_and_incomplete_responses_are_rejected(self) -> None:
        class MalformedProvider:
            name = "malformed"
            kind = "offline_test"

            def generate(self, request: dict[str, object]) -> str:
                return "not json"

        with self.assertRaisesRegex(DirectionValidationError, "invalid JSON"):
            BuildDirectionService(self.database, MalformedProvider()).generate(self.intent)

        response = json.loads(
            OfflineDeterministicProvider().generate({"build_context": self.context})
        )
        incomplete = deepcopy(response)
        del incomplete["directions"][0]["defense_direction"]
        with self.assertRaisesRegex(DirectionValidationError, "defense_direction"):
            validate_direction_response(incomplete, self.context)

    def test_all_quality_modes_cross_the_provider_boundary(self) -> None:
        for mode in QualityMode:
            provider = CapturingProvider()
            result = BuildDirectionService(self.database, provider).generate(self.intent, mode)
            self.assertEqual(provider.request["quality_mode"], mode.value)
            self.assertEqual(result["quality_mode"], mode.value)

    def test_validation_failure_is_retried_with_bounded_feedback(self) -> None:
        provider = FailsOnceProvider()
        result = BuildDirectionService(
            self.database, provider, max_attempts=2
        ).generate(self.intent)
        self.assertEqual(provider.calls, 2)
        self.assertEqual(result["attempts"], 2)
        self.assertIn("invalid JSON", provider.feedback)

    def test_retry_count_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            BuildDirectionService(
                self.database, OfflineDeterministicProvider(), max_attempts=0
            ).generate(self.intent)
