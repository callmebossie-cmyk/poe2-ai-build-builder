from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from poe2_builder.fetch import sha256_file
from poe2_builder.validation import CHECKS


class DataCoreTests(unittest.TestCase):
    def test_sha256_file_matches_known_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value"
            path.write_bytes(b"poe2")
            self.assertEqual(
                sha256_file(path),
                "2358aae6868d3e39c5318cdce7c3d0867ac0273487cfb80ef050755b6627bc79",
            )

    def test_checkpoint_queries_are_read_only_selects(self) -> None:
        for query, _minimum in CHECKS.values():
            self.assertTrue(query.lstrip().upper().startswith("SELECT"))
            self.assertNotIn(";", query)

    def test_json1_is_not_required(self) -> None:
        with closing(sqlite3.connect(":memory:")) as db:
            db.execute("CREATE TABLE records(payload_json TEXT NOT NULL)")
            payload = json.dumps({"name": "Snipe"})
            db.execute("INSERT INTO records VALUES(?)", (payload,))
            self.assertEqual(db.execute("SELECT payload_json FROM records").fetchone()[0], payload)


if __name__ == "__main__":
    unittest.main()
