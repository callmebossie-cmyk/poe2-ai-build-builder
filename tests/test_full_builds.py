from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from poe2_builder.full_builds import (
    FullBuildService,
    FullBuildValidationError,
    OfflineFullBuildProvider,
    _support_accepts_skill,
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
        presentation = result["presentation"]
        self.assertEqual(
            {node["id"] for node in presentation["passive_tree"]["nodes"]},
            set(result["build"]["passive_ids"]),
        )
        self.assertTrue(presentation["passive_tree"]["edges"])
        inspection = presentation["inspection"]
        self.assertGreater(len(inspection["nodes"]), 4000)
        self.assertEqual(
            {node["id"] for node in inspection["nodes"] if node["is_allocated"]},
            set(result["build"]["passive_ids"]),
        )
        order = inspection["allocation_order"]
        self.assertEqual(set(order), set(result["build"]["passive_ids"]))
        self.assertEqual(len(order), len(set(order)))
        edges = {frozenset((edge["from"], edge["to"])) for edge in inspection["edges"]}
        for index, node_id in enumerate(order[1:], 1):
            parent = inspection["parents"][node_id]
            self.assertIn(parent, order[:index])
            self.assertIn(frozenset((parent, node_id)), edges)
        self.assertTrue(inspection["warnings"])
        self.assertTrue(inspection["skill_effects"])
        self.assertTrue(any(source["file_name"] == "passive_tree.json" for source in inspection["sources"]))
        self.assertEqual(presentation["skills"][0]["id"], "SnipePlayer")
        self.assertEqual(
            len(presentation["skills"][0]["supports"]),
            len(result["build"]["skill_links"][0]["support_ids"]),
        )
        self.assertEqual(
            presentation["equipment"][0]["base_id"],
            result["build"]["equipment"][0]["item_base_id"],
        )

    def test_context_supplies_a_connected_allocation_from_ranger_start(self) -> None:
        allocated = set(self.context["suggested_connected_passive_ids"])
        self.assertIn(self.context["character"]["class_start_id"], allocated)
        self.assertTrue(set(SELECTED_DIRECTION["passive_ids"]) <= allocated)
        self.assertEqual(self.context["equipment_requirements"]["minimum_build_level"], 65)
        self.assertEqual(self.context["equipment_requirements"]["minimum_attributes"]["dexterity"], 15)

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

    def test_duplicate_supports_mods_and_casefolded_slots_are_rejected(self) -> None:
        duplicate_support = deepcopy(self.response)
        support = duplicate_support["build"]["skill_links"][0]["support_ids"][0]
        duplicate_support["build"]["skill_links"][0]["support_ids"].append(support)
        with self.assertRaisesRegex(FullBuildValidationError, "duplicate supports"):
            validate_full_build(duplicate_support, self.context, self.database)

        duplicate_mod = deepcopy(self.response)
        mod = duplicate_mod["build"]["equipment"][0]["mod_ids"][0]
        duplicate_mod["build"]["equipment"][0]["mod_ids"].append(mod)
        with self.assertRaisesRegex(FullBuildValidationError, "duplicate mods"):
            validate_full_build(duplicate_mod, self.context, self.database)

        duplicate_slot = deepcopy(self.response)
        second_item = deepcopy(duplicate_slot["build"]["equipment"][0])
        second_item["slot"] = duplicate_slot["build"]["equipment"][0]["slot"].upper()
        duplicate_slot["build"]["equipment"].append(second_item)
        with self.assertRaisesRegex(FullBuildValidationError, "duplicate equipment slot"):
            validate_full_build(duplicate_slot, self.context, self.database)

    def test_mods_in_the_same_exclusive_group_are_rejected(self) -> None:
        conflicting_mod = "AbyssModBowSpearAmanamuSuffixCompanionAndLocalAttackSpeed"
        context = deepcopy(self.context)
        context["selected_direction"]["mod_ids"].append(conflicting_mod)
        response = deepcopy(self.response)
        response["build"]["equipment"][0]["mod_ids"].append(conflicting_mod)
        with self.assertRaisesRegex(FullBuildValidationError, "exclusive group"):
            validate_full_build(response, context, self.database)

    def test_more_than_three_prefixes_are_rejected(self) -> None:
        prefixes = [
            "LocalAddedPhysicalDamage1",
            "LocalAddedFireDamage1",
            "LocalAddedColdDamage1",
            "LocalAddedLightningDamage1",
        ]
        context = deepcopy(self.context)
        context["selected_direction"]["mod_ids"] = prefixes
        response = deepcopy(self.response)
        response["build"]["equipment"][0]["mod_ids"] = prefixes
        with self.assertRaisesRegex(FullBuildValidationError, "exceeds three prefix"):
            validate_full_build(response, context, self.database)

    def test_level_and_attribute_requirements_are_enforced(self) -> None:
        underleveled = deepcopy(self.response)
        underleveled["build"]["level"] = 10
        with self.assertRaisesRegex(FullBuildValidationError, "mod is unavailable"):
            validate_full_build(underleveled, self.context, self.database)

        low_dexterity = deepcopy(self.response)
        low_dexterity["build"]["attributes"]["dexterity"] = 0
        equipment_only_context = deepcopy(self.context)
        equipment_only_context["character"]["base_dexterity"] = 0
        with self.assertRaisesRegex(FullBuildValidationError, "lacks dexterity"):
            validate_full_build(low_dexterity, equipment_only_context, self.database)

        below_class_base = deepcopy(self.response)
        below_class_base["build"]["attributes"]["strength"] = 6
        with self.assertRaisesRegex(FullBuildValidationError, "class base value"):
            validate_full_build(below_class_base, self.context, self.database)

    def test_support_allowed_and_excluded_type_rules_are_enforced(self) -> None:
        payload = {
            "granted_skills": {
                "support": {
                    "is_support": True,
                    "support_gem": {
                        "allowed_types": ["Attack"],
                        "excluded_types": ["Triggered"],
                    },
                }
            }
        }
        self.assertTrue(_support_accepts_skill(payload, {"Attack", "Bow"}))
        self.assertFalse(_support_accepts_skill(payload, {"Spell"}))
        self.assertFalse(_support_accepts_skill(payload, {"Attack", "Triggered"}))

    def test_unsupported_quantitative_narrative_claims_are_rejected(self) -> None:
        resistance = deepcopy(self.response)
        resistance["build"]["defense"] = "This setup has exactly 75% resistance."
        with self.assertRaisesRegex(FullBuildValidationError, "unsupported quantitative"):
            validate_full_build(resistance, self.context, self.database)

        dps = deepcopy(self.response)
        dps["build"]["rotation"] = "This rotation guarantees top DPS."
        with self.assertRaisesRegex(FullBuildValidationError, "unsupported quantitative"):
            validate_full_build(dps, self.context, self.database)

        price = deepcopy(self.response)
        price["build"]["resource_solution"] = "Buy the solution for one Divine."
        with self.assertRaisesRegex(FullBuildValidationError, "unsupported quantitative"):
            validate_full_build(price, self.context, self.database)

    def test_service_labels_narrative_and_resource_claims_as_advisory(self) -> None:
        result = FullBuildService(self.database, OfflineFullBuildProvider()).generate(SELECTED_DIRECTION)
        self.assertEqual(result["claim_boundaries"]["resource_status"], "advisory_not_calculated")
        self.assertEqual(result["claim_boundaries"]["exact_dps_status"], "not_calculated")
        self.assertIn("defense", result["claim_boundaries"]["advisory_only"])
