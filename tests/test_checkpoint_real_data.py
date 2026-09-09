from __future__ import annotations

import unittest
from pathlib import Path

from poe2_builder.validation import snipe_summary, validate_database
from poe2_builder.database import connect
from poe2_builder.graph import NodeNotFoundError, PassiveGraph, PathNotFoundError


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
        self.assertEqual(len(summary["sources"]), 7)

    def test_real_tree_maps_all_character_classes_to_start_nodes(self) -> None:
        graph = PassiveGraph.from_database(self.database)
        self.assertEqual(len(graph.class_starts), 12)
        self.assertEqual(graph.class_start("Ranger"), graph.class_start("Huntress"))
        self.assertNotEqual(graph.class_start("Ranger"), graph.class_start("Witch"))

    def test_real_tree_calculates_a_valid_projectile_path_and_cost(self) -> None:
        graph = PassiveGraph.from_database(self.database)
        start = graph.class_start("Ranger")
        db = connect(self.database)
        try:
            targets = [
                row[0]
                for row in db.execute(
                    "SELECT DISTINCT node_id FROM passive_stats WHERE lower(text) LIKE '%projectile%'"
                )
            ]
        finally:
            db.close()
        paths = []
        for target in targets:
            try:
                paths.append(graph.shortest_path(start, target))
            except PathNotFoundError:
                continue
        nearest = min(paths, key=lambda path: path.point_cost)
        self.assertEqual(nearest.nodes[0], start)
        self.assertIn(nearest.nodes[-1], targets)
        self.assertEqual(nearest.point_cost, len(nearest.nodes) - 1)
        self.assertGreater(nearest.point_cost, 0)
        self.assertGreater(graph.component_size(start), 1000)

    def test_virtual_root_cannot_shortcut_between_classes(self) -> None:
        graph = PassiveGraph.from_database(self.database)
        path = graph.shortest_path(graph.class_start("Ranger"), graph.class_start("Witch"))
        self.assertGreater(path.point_cost, 2)
        self.assertNotIn("root", path.nodes)

    def test_wrong_ascendancy_path_is_rejected(self) -> None:
        graph = PassiveGraph.from_database(self.database)
        ranger_start = graph.class_start("Ranger")
        db = connect(self.database)
        try:
            infernalist_node = db.execute(
                "SELECT node_id FROM ascendancy_nodes WHERE ascendancy_id='Witch1' LIMIT 1"
            ).fetchone()[0]
        finally:
            db.close()
        with self.assertRaises(PathNotFoundError):
            graph.shortest_path(ranger_start, infernalist_node)

        infernalist_graph = PassiveGraph.from_database(
            self.database, allowed_ascendancy="Witch1"
        )
        valid_path = infernalist_graph.shortest_path(
            infernalist_graph.class_start("Witch"), infernalist_node
        )
        self.assertEqual(valid_path.nodes[-1], infernalist_node)
        self.assertGreater(valid_path.point_cost, 0)

    def test_missing_node_is_rejected(self) -> None:
        graph = PassiveGraph.from_database(self.database)
        with self.assertRaises(NodeNotFoundError):
            graph.shortest_path(graph.class_start("Ranger"), "not-a-real-node")
