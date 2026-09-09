from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from poe2_builder.full_builds import (
    FullBuildService,
    FullBuildValidationError,
    OfflineFullBuildProvider,
    build_full_context,
    validate_full_build,
)


SELECTED_DIRECTION = {
    "direction_id": "direction_2",
    "title": "Projectile Speed Boost",
    "class_name": "Ranger",
    "ascendancy_id": "Ranger1",
    "skill_id": "SnipePlayer",
    "support_ids": [
        "Metadata/Items/Gem/SupportGemDeadlyResolve",
        "Metadata/Items/Gems/SupportGemLacerateTwo",
    ],
    "passive_ids": ["31055", "19337", "35660"],
    "item_base_ids": ["Metadata/Items/Weapons/TwoHandWeapons/Bows/FourBow2"],
    "mod_ids": [
        "BowAttackSpeedJewel",
        "CorruptionUpgradeAdditionalArrows1",
        "AbyssModBowSpearUlamanSuffixAttackSpeedLocalAndWithCompanion",
    ],
    "unique_ids": [],
}


class FullBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = Path("data/poe2.db")
        if not cls.database.exists():
            raise unittest.SkipTest("Run the importer before full-build tests")
        cls.context = build_full_context(cls.database, SELECTED_DIRECTION)
        raw = OfflineFullBuildProvider().generate({"build_context": cls.context})
        cls.response = json.loads(raw)

    def test_offline_full_build_passes_all_deterministic_checks(self) -> None:
        result = FullBuildService(
            self.database, OfflineFullBuildProvider()
        ).generate(SELECTED_DIRECTION)
        self.assertEqual(result["selected_direction_id"], "direction_2")
        self.assertTrue(all(result["validation"].values()))
        self.assertEqual(result["provider"]["output_status"], "test_only_not_ai_recommendation")

    def test_context_supplies_a_connected_allocation_from_ranger_start(self) -> None:
        allocated = set(self.context["suggested_connected_passive_ids"])
        self.assertIn(self.context["character"]["class_start_id"], allocated)
        self.assertTrue(set(SELECTED_DIRECTION["passive_ids"]) <= allocated)

    def test_wrong_class_and_disconnected_allocation_are_rejected(self) -> None:
        wrong_class = deepcopy(self.response)
        wrong_class["build"]["class_name"] = "Huntress"
        with self.assertRaisesRegex(FullBuildValidationError, "selected direction"):
            validate_full_build(wrong_class, self.context, self.database)

        missing_path = deepcopy(self.response)
        missing_path["build"]["passive_ids"] = SELECTED_DIRECTION["passive_ids"]
        with self.assertRaisesRegex(FullBuildValidationError, "bounded connected allocation"):
            validate_full_build(missing_path, self.context, self.database)

    def test_incompatible_support_and_mod_are_rejected(self) -> None:
        bad_support = deepcopy(self.response)
        bad_support["build"]["skill_links"][0]["support_ids"] = ["InventedSupport"]
        with self.assertRaisesRegex(FullBuildValidationError, "supports"):
            validate_full_build(bad_support, self.context, self.database)

        bad_mod = deepcopy(self.response)
        bad_mod["build"]["equipment"][0]["mod_ids"] = ["InventedMod"]
        with self.assertRaisesRegex(FullBuildValidationError, "mods"):
            validate_full_build(bad_mod, self.context, self.database)

    def test_level_and_attribute_requirements_are_enforced(self) -> None:
        underleveled = deepcopy(self.response)
        underleveled["build"]["level"] = 10
        with self.assertRaisesRegex(FullBuildValidationError, "mod is unavailable"):
            validate_full_build(underleveled, self.context, self.database)

        low_dexterity = deepcopy(self.response)
        low_dexterity["build"]["attributes"]["dexterity"] = 0
        with self.assertRaisesRegex(FullBuildValidationError, "lacks dexterity"):
            validate_full_build(low_dexterity, self.context, self.database)
