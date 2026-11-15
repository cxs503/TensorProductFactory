import json
import sys
import unittest
from jsonschema import Draft202012Validator, FormatChecker
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from validate_english_benchmark import validate_pack


FIXTURE = Path(__file__).parents[1] / "benchmarks/english-exam-coach/fixtures/reading-original-v0.1.json"


class EnglishBenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.pack = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_original_fixture_is_structurally_valid(self):
        self.assertEqual(validate_pack(self.pack), [])

    def test_fixture_items_conform_to_published_json_schema(self):
        schema_path = Path(__file__).parents[1] / "benchmarks/english-exam-coach/schemas/content-item.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for item in self.pack["items"]:
            self.assertEqual(list(validator.iter_errors(item)), [])

    def test_duplicate_ids_are_rejected(self):
        self.pack["items"][1]["item_id"] = self.pack["items"][0]["item_id"]
        self.assertTrue(any("duplicate item_id" in e for e in validate_pack(self.pack)))

    def test_missing_answer_key_is_rejected(self):
        del self.pack["items"][0]["answer_key"]
        self.assertTrue(any("answer_key" in e for e in validate_pack(self.pack)))

    def test_multiple_choice_answer_must_match_an_option_id(self):
        self.pack["items"][0]["answer_key"]["expected"] = "Z"
        self.assertTrue(any("must match a prompt option id" in e for e in validate_pack(self.pack)))

    def test_true_false_not_given_uses_supported_answer(self):
        self.pack["items"][1]["answer_key"]["expected"] = "MAYBE"
        self.assertTrue(any("must be TRUE, FALSE, or NOT GIVEN" in e for e in validate_pack(self.pack)))

    def test_short_answer_requires_accepted_phrase_list(self):
        self.pack["items"][2]["answer_key"]["expected"] = "long-term support"
        self.assertTrue(any("non-empty list of accepted answer phrases" in e for e in validate_pack(self.pack)))

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
