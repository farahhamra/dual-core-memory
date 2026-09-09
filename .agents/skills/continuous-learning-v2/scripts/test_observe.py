import os
import tempfile
import unittest
from pathlib import Path
import json

from observe import (
    validate_and_parse_transcript,
    SchemaMismatchError,
    is_negative_stop_phrase,
    extract_direct_imperatives,
    calculate_confidence,
    detect_project,
    write_instinct_file,
    mine_transcript,
)

class TestObservePipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.homunculus_dir = Path(self.temp_dir.name) / "ecc-homunculus"

    def tearDown(self):
        self.temp_dir.cleanup()

    # 1. Schema Validation Tests
    def test_schema_validation_valid_antigravity(self):
        transcript_file = Path(self.temp_dir.name) / "transcript.jsonl"
        valid_lines = [
            json.dumps({"step_index": 1, "type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Always run unit tests."}),
            json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "source": "MODEL", "content": "Running tests..."}),
        ]
        transcript_file.write_text("\n".join(valid_lines), encoding="utf-8")

        entries = validate_and_parse_transcript(transcript_file)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["step_index"], 1)

    def test_schema_validation_malformed_json(self):
        bad_file = Path(self.temp_dir.name) / "bad.jsonl"
        bad_file.write_text("NOT_JSON_AT_ALL\n", encoding="utf-8")

        with self.assertRaises(SchemaMismatchError) as ctx:
            validate_and_parse_transcript(bad_file)
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_schema_validation_missing_fields(self):
        invalid_schema = Path(self.temp_dir.name) / "invalid.jsonl"
        invalid_schema.write_text(json.dumps({"random_key": "some_value"}) + "\n", encoding="utf-8")

        with self.assertRaises(SchemaMismatchError) as ctx:
            validate_and_parse_transcript(invalid_schema)
        self.assertIn("Unsupported transcript schema", str(ctx.exception))

    # 2. Negative Stop-Phrase Filtering (0% False Positives)
    def test_negative_stop_phrase_rejection(self):
        negative_samples = [
            "never mind, I found it myself.",
            "Nevermind, let's keep going.",
            "I always wanted to try implementing a compiler in Rust.",
            "This is not always the best approach.",
            "As always, your help is appreciated.",
            "It almost always works on my machine.",
            "I hardly ever use global state.",
            "Is it always necessary to run migrations?",
            "Should we never touch legacy tables?",
            "Can you check the log files?",
            "Could you please review this code?",
            "Why do we always get timeouts here?",
        ]
        for phrase in negative_samples:
            self.assertTrue(
                is_negative_stop_phrase(phrase),
                f"Expected negative stop-phrase detection for: '{phrase}'"
            )
            extracted = extract_direct_imperatives(phrase)
            self.assertEqual(
                len(extracted), 0,
                f"Negative phrase should yield 0 instincts: '{phrase}', but got {extracted}"
            )

    # 3. Positive Directive Extraction
    def test_positive_directive_extraction(self):
        directives = [
            ("Always validate user input because unescaped strings cause SQL injection.", True, "workflow"),
            ("Never commit .env files because credentials will leak.", True, "workflow"),
            ("Use httpx instead of requests because it supports modern async.", True, "coding-style"),
            ("Do not use var, use const.", False, "workflow"),
        ]

        for text, expect_reason, expect_domain in directives:
            extracted = extract_direct_imperatives(text)
            self.assertGreaterEqual(
                len(extracted), 1,
                f"Failed to extract directive from: '{text}'"
            )
            inst = extracted[0]
            self.assertEqual(inst["has_rationale"], expect_reason)
            self.assertEqual(inst["domain"], expect_domain)

    # 4. Symmetric Two-Sighting Confidence Scoring Rubric
    def test_two_sighting_confidence_rubric(self):
        # 1st sighting of explained directive -> 0.65 (held)
        cand_explained = {"has_rationale": True, "is_error_recovery": False}
        conf_1, count_1 = calculate_confidence(cand_explained, existing_meta=None)
        self.assertEqual(conf_1, 0.65)
        self.assertEqual(count_1, 1)

        # 2nd sighting of explained directive -> 0.85 (promoted)
        conf_2, count_2 = calculate_confidence(cand_explained, existing_meta={"reinforcement_count": 1})
        self.assertEqual(conf_2, 0.85)
        self.assertEqual(count_2, 2)

        # 1st sighting of terse directive -> 0.55 (held)
        cand_terse = {"has_rationale": False, "is_error_recovery": False}
        conf_t1, count_t1 = calculate_confidence(cand_terse, existing_meta=None)
        self.assertEqual(conf_t1, 0.55)
        self.assertEqual(count_t1, 1)

        # 2nd sighting of terse directive -> 0.70 (promoted)
        conf_t2, count_t2 = calculate_confidence(cand_terse, existing_meta={"reinforcement_count": 1})
        self.assertEqual(conf_t2, 0.70)
        self.assertEqual(count_t2, 2)

    # 5. Sanitized Project Detection
    def test_sanitized_project_detection(self):
        test_dir = Path(self.temp_dir.name) / "MySensitiveClientProject"
        test_dir.mkdir(parents=True)

        pid, name = detect_project(test_dir)
        self.assertEqual(len(pid), 12)
        # Verify pid is a clean hex hash
        int(pid, 16)
        self.assertNotIn("c:", pid.lower())
        self.assertNotIn("\\", pid)

    # 6. Homunculus Persistence & End-to-End Mining
    def test_end_to_end_mining_and_persistence(self):
        transcript_entries = [
            {
                "step_index": 1,
                "type": "USER_INPUT",
                "source": "USER_EXPLICIT",
                "content": "Always use kebab-case for plugin names because Antigravity registry enforces it."
            }
        ]

        pid = "a1b2c3d4e5f6"
        instincts = mine_transcript(transcript_entries, pid, "test-project", self.homunculus_dir)
        self.assertEqual(len(instincts), 1)
        inst = instincts[0]

        # 1st pass: should be staged at 0.65
        self.assertEqual(inst["confidence"], 0.65)
        self.assertEqual(inst["reinforcement_count"], 1)
        self.assertEqual(inst["status"], "staged")

        # Write to disk
        out_file = write_instinct_file(inst, self.homunculus_dir, scope="project")
        self.assertTrue(out_file.exists())

        # 2nd pass: mine same transcript again with file now existing
        instincts_2 = mine_transcript(transcript_entries, pid, "test-project", self.homunculus_dir)
        self.assertEqual(len(instincts_2), 1)
        inst_2 = instincts_2[0]

        # 2nd pass: should be promoted at 0.85
        self.assertEqual(inst_2["confidence"], 0.85)
        self.assertEqual(inst_2["reinforcement_count"], 2)
        self.assertEqual(inst_2["status"], "promotable")

if __name__ == "__main__":
    unittest.main()
