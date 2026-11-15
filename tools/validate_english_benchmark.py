#!/usr/bin/env python3
"""Validate English Exam Coach benchmark packs without third-party dependencies."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

RIGHTS_ORIGINS = {"original", "licensed", "public_domain", "restricted_reference_only", "unknown"}
RIGHTS_STATES = {"cleared", "pending", "blocked"}
REVIEW_STATES = {"draft", "reviewed", "approved", "rejected"}
SKILLS = {"listening", "reading", "writing", "speaking"}
DIFFICULTIES = {"A1", "A2", "B1", "B2", "C1", "C2", "IELTS-unknown"}


def validate_pack(pack: dict, require_release: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(pack, dict):
        return ["pack must be a JSON object"]
    for field in ("pack_schema_version", "pack_id", "exam_adapter", "pack_version", "items"):
        if field not in pack:
            errors.append(f"pack missing required field: {field}")
    if pack.get("exam_adapter") != "ielts-academic":
        errors.append("exam_adapter must be ielts-academic")
    if not isinstance(pack.get("items"), list) or not pack.get("items"):
        errors.append("items must be a non-empty array")
        return errors

    schema_path = Path(__file__).parents[1] / "benchmarks/english-exam-coach/schemas/content-item.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    except Exception as exc:
        return [f"content item schema could not be loaded/validated: {exc}"]

    seen: set[str] = set()
    for index, item in enumerate(pack["items"]):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for schema_error in schema_validator.iter_errors(item):
            location = ".".join(str(part) for part in schema_error.absolute_path)
            location_prefix = "." + location if location else ""
            errors.append(f"{prefix}{location_prefix}: {schema_error.message}")
        for field in ("schema_version", "item_id", "exam_adapter", "skill", "task_type",
                      "difficulty", "prompt", "provenance", "review"):
            if field not in item:
                errors.append(f"{prefix} missing required field: {field}")
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{prefix}.item_id must be a non-empty string")
        elif item_id in seen:
            errors.append(f"duplicate item_id: {item_id}")
        else:
            seen.add(item_id)
        if item.get("exam_adapter") != "ielts-academic":
            errors.append(f"{prefix}.exam_adapter must be ielts-academic")
        if item.get("skill") not in SKILLS:
            errors.append(f"{prefix}.skill is invalid")
        if item.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{prefix}.difficulty is invalid")

        task_type = item.get("task_type")
        if item.get("skill") == "reading":
            if task_type not in {"multiple_choice_single", "true_false_not_given", "short_answer"}:
                errors.append(f"{prefix}.task_type is unsupported for reading")
            prompt_value = item.get("prompt")
            answer_value = item.get("answer_key")
            if isinstance(prompt_value, dict) and isinstance(answer_value, dict):
                expected = answer_value.get("expected")
                if task_type == "multiple_choice_single":
                    options = prompt_value.get("options")
                    option_ids = {option.get("id") for option in options if isinstance(option, dict)} if isinstance(options, list) else set()
                    if len(option_ids) < 2:
                        errors.append(f"{prefix}.prompt.options requires at least two unique option ids")
                    if not isinstance(expected, str) or expected not in option_ids:
                        errors.append(f"{prefix}.answer_key.expected must match a prompt option id")
                elif task_type == "true_false_not_given" and expected not in {"TRUE", "FALSE", "NOT GIVEN"}:
                    errors.append(f"{prefix}.answer_key.expected must be TRUE, FALSE, or NOT GIVEN")
                elif task_type == "short_answer" and (
                    not isinstance(expected, list) or not expected or not all(isinstance(value, str) and value.strip() for value in expected)
                ):
                    errors.append(f"{prefix}.answer_key.expected must be a non-empty list of accepted answer phrases")

        prompt = item.get("prompt")
        if not isinstance(prompt, dict) or not prompt.get("instruction") or not prompt.get("stimulus"):
            errors.append(f"{prefix}.prompt requires non-empty instruction and stimulus")

        if item.get("skill") in {"listening", "reading"}:
            answer = item.get("answer_key")
            if not isinstance(answer, dict) or "expected" not in answer or not answer.get("explanation"):
                errors.append(f"{prefix}.answer_key requires expected and explanation")
        elif item.get("skill") in {"writing", "speaking"} and not item.get("rubric_ref"):
            errors.append(f"{prefix}.rubric_ref is required for writing/speaking")

        provenance = item.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{prefix}.provenance must be an object")
            provenance = {}
        if provenance.get("origin") not in RIGHTS_ORIGINS:
            errors.append(f"{prefix}.provenance.origin is invalid")
        if provenance.get("rights_status") not in RIGHTS_STATES:
            errors.append(f"{prefix}.provenance.rights_status is invalid")
        if not provenance.get("creator") or not provenance.get("created_at"):
            errors.append(f"{prefix}.provenance requires creator and created_at")
        if not isinstance(provenance.get("permitted_uses"), list):
            errors.append(f"{prefix}.provenance.permitted_uses must be an array")

        review = item.get("review")
        if not isinstance(review, dict):
            errors.append(f"{prefix}.review must be an object")
            review = {}
        if review.get("status") not in REVIEW_STATES:
            errors.append(f"{prefix}.review.status is invalid")
        if review.get("ambiguity_status") not in {"unassessed", "clear", "unresolved"}:
            errors.append(f"{prefix}.review.ambiguity_status is invalid")
        if not isinstance(review.get("reviewer_ids"), list):
            errors.append(f"{prefix}.review.reviewer_ids must be an array")

        if require_release:
            if provenance.get("origin") in {"restricted_reference_only", "unknown"}:
                errors.append(f"{prefix} has prohibited provenance for release")
            if provenance.get("rights_status") != "cleared":
                errors.append(f"{prefix} rights are not cleared")
            if "commercial_distribution" not in provenance.get("permitted_uses", []):
                errors.append(f"{prefix} lacks commercial_distribution permission")
            if review.get("status") != "approved":
                errors.append(f"{prefix} is not approved")
            if review.get("ambiguity_status") != "clear":
                errors.append(f"{prefix} ambiguity is not cleared")
            if item.get("skill") in {"listening", "reading"} and review.get("answer_verification") != "independently_verified":
                errors.append(f"{prefix} answer key is not independently verified")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("--require-release", action="store_true",
                        help="enforce rights, review, ambiguity, and answer-verification release gates")
    args = parser.parse_args()
    try:
        pack = json.loads(args.pack.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2
    errors = validate_pack(pack, require_release=args.require_release)
    result = {
        "ok": not errors,
        "pack_id": pack.get("pack_id") if isinstance(pack, dict) else None,
        "item_count": len(pack.get("items", [])) if isinstance(pack, dict) and isinstance(pack.get("items"), list) else 0,
        "mode": "release" if args.require_release else "structural",
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
