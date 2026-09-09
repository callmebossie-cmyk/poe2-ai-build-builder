from __future__ import annotations

import unittest
from pathlib import Path

from poe2_builder.validation import snipe_summary, validate_database


class RealDataCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = Path("data/poe2.db")
        if not cls.database.exists():
            raise unittest.SkipTest("Run the real-data importer before this integration test")

    def test_checkpoint_one_acceptance_queries_pass(self) -> None:
        results = validate_database(self.database)
        self.assertTrue(results)
        self.assertTrue(all(result["passed"] for result in results))

    def test_snipe_vertical_slice_is_from_queryable_records(self) -> None:
        summary = snipe_summary(self.database)
        self.assertEqual(summary["id"], "SnipePlayer")
        self.assertEqual(summary["levels"], 40)
        self.assertGreaterEqual(len(summary["supports"]), 10)
        self.assertGreater(len(summary["projectile_passives"]), 0)
        self.assertGreater(len(summary["bow_bases"]), 0)
        self.assertGreater(len(summary["bow_mods"]), 0)
        self.assertEqual(len(summary["sources"]), 6)

