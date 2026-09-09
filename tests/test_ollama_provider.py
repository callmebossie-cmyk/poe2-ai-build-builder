from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from poe2_builder.ollama_provider import OllamaProvider, direction_json_schema


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class OllamaProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = {
            "skill": {"id": "SnipePlayer"},
            "candidates": {
                "mechanics": [{"id": "mechanic-1"}],
                "supports": [{"id": "support-1"}],
                "passives": [{"id": "passive-1"}],
                "ascendancies": [{"id": "Ranger1"}],
                "item_bases": [{"id": "bow-1"}],
                "mods": [{"id": "mod-1"}],
                "uniques": [{"id": "unique-1"}],
            },
        }

    def test_schema_constrains_every_entity_reference_to_context_ids(self) -> None:
        schema = direction_json_schema(self.context)
        direction = schema["properties"]["directions"]["items"]
        self.assertEqual(direction["properties"]["skill_id"]["enum"], ["SnipePlayer"])
        self.assertEqual(direction["properties"]["support_ids"]["items"]["enum"], ["support-1"])
        self.assertEqual(direction["properties"]["ascendancy_id"]["enum"], ["Ranger1"])
        self.assertFalse(direction["additionalProperties"])

    @patch("urllib.request.urlopen")
    def test_local_request_uses_schema_non_streaming_and_no_thinking(self, urlopen: object) -> None:
        urlopen.return_value = FakeResponse(
            {
                "model": "qwen3:8b",
                "done_reason": "stop",
                "message": {"content": '{"schema_version":1,"directions":[]}'},
                "prompt_eval_count": 100,
                "eval_count": 20,
            }
        )
        provider = OllamaProvider()
        content = provider.generate({"build_context": self.context, "task": "test"})
        self.assertIn("schema_version", content)
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertFalse(body["stream"])
        self.assertFalse(body["think"])
        self.assertIsInstance(body["format"], dict)
        self.assertEqual(body["options"]["temperature"], 0.15)
        self.assertEqual(provider.last_metadata["prompt_eval_count"], 100)
