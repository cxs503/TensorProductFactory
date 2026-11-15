import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from validate_english_benchmark import validate_pack


FIXTURE = Path(__file__).parents[1] / "benchmarks/english-exam-coach/fixtures/reading-original-v0.1.json"


class EnglishBenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.pack = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_original_fixture_is_structurally_valid(self):
        self.assertEqual(validate_pack(self.pack), [])

    def test_duplicate_ids_are_rejected(self):
        self.pack["items"][1]["item_id"] = self.pack["items"][0]["item_id"]
        self.assertTrue(any("duplicate item_id" in e for e in validate_pack(self.pack)))

    def test_missing_answer_key_is_rejected(self):
        del self.pack["items"][0]["answer_key"]
        self.assertTrue(any("answer_key" in e for e in validate_pack(self.pack)))

    def test_draft_content_is_blocked_from_release(self):
        errors = validate_pack(self.pack, require_release=True)
        self.assertTrue(any("is not approved" in e for e in errors))
        self.assertTrue(any("ambiguity is not cleared" in e for e in errors))
        self.assertTrue(any("not independently verified" in e for e in errors))

    def test_uncleared_rights_are_blocked_from_release(self):
        self.pack["items"][0]["provenance"]["rights_status"] = "pending"
        errors = validate_pack(self.pack, require_release=True)
        self.assertTrue(any("rights are not cleared" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
