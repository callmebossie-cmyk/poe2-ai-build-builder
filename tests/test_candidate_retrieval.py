from __future__ import annotations

import unittest
from pathlib import Path

from poe2_builder.retrieval import (
    LIMITS,
    BuildIntent,
    CandidateRetriever,
    matching_terms,
)


class CandidateRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = Path("data/poe2.db")
        if not cls.database.exists():
            raise unittest.SkipTest("Run the real-data importer before this integration test")
        cls.retriever = CandidateRetriever(cls.database)
        cls.intent = BuildIntent("Snipe", "Fast", "Mapping", "Cheap")
        cls.context = cls.retriever.retrieve(cls.intent)

    def test_context_is_bounded_and_smaller_than_full_database(self) -> None:
        debug = self.context["debug"]
        self.assertLess(debug["serialized_bytes"], 40_000)
        self.assertLess(debug["serialized_bytes"], self.database.stat().st_size // 100)
        for category, maximum in LIMITS.items():
            self.assertLessEqual(debug["returned"][category], maximum)
        self.assertGreater(debug["scanned"]["passives"], debug["returned"]["passives"])
        self.assertGreater(debug["scanned"]["mods"], debug["returned"]["mods"])

    def test_every_candidate_has_score_reason_and_provenance(self) -> None:
        for candidates in self.context["candidates"].values():
            self.assertTrue(candidates)
            for candidate in candidates:
                self.assertIsInstance(candidate["score"], int)
                self.assertTrue(candidate["reasons"])
                self.assertTrue(candidate["source"])
                self.assertEqual(len(candidate["source_version"]), 40)
                self.assertNotIn("payload_json", candidate)

    def test_expected_real_snipe_candidates_are_present(self) -> None:
        supports = {item["name"] for item in self.context["candidates"]["supports"]}
        mechanics = {item["name"] for item in self.context["candidates"]["mechanics"]}
        self.assertIn("Window of Opportunity I", supports)
        self.assertIn("Perfect Timing", mechanics)
        self.assertIn("Skill Consumes Freeze", mechanics)
        self.assertTrue(
            all("point_cost" in item["metadata"] for item in self.context["candidates"]["passives"])
        )

    def test_unique_effects_are_not_invented(self) -> None:
        uniques = self.context["candidates"]["uniques"]
        self.assertTrue(uniques)
        self.assertTrue(
            all(item["metadata"]["effect_data_available"] is False for item in uniques)
        )
        self.assertTrue(
            all("unavailable" in " ".join(item["reasons"]) for item in uniques)
        )

    def test_retrieval_is_deterministic(self) -> None:
        self.assertEqual(self.context, self.retriever.retrieve(self.intent))

    def test_unknown_skill_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not available"):
            self.retriever.retrieve(BuildIntent("Imaginary Skill", "Fast", "Mapping", "Cheap"))


class MatchingTests(unittest.TestCase):
    def test_matching_uses_word_boundaries(self) -> None:
        self.assertEqual(matching_terms("nearby enemies", {"area": 10}), [])
        self.assertEqual(matching_terms("increased Area damage", {"area": 10}), [("area", 10)])
