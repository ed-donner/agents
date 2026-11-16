import unittest

from debate_crew.validator import validate_verdict


VALID_VERDICT = """\
**Motion:** Artificial intelligence will improve education.

**Winning Side: Pro**

| Criterion | Pro Score | Pro Justification | Counter Score | Counter Justification |
|---|---:|---|---:|---|
| Logical consistency | 4 | The argument is consistent. | 3 | One point is unclear. |
| Relevance | 5 | Directly addresses the motion. | 4 | Addresses the motion. |
| Reasoning | 4 | Explains the causal links. | 3 | Reasoning needs development. |
| Evidence quality | 3 | Some examples, limited evidence. | 2 | Little verifiable evidence. |
| Counterargument handling | 4 | Addresses major objections. | 3 | Misses one objection. |

**Pro Total Score: 20 out of 25**
**Counter Total Score: 15 out of 25**

### Final Decision
Pro wins based on the higher total.
"""


class TestValidateVerdict(unittest.TestCase):
    def test_valid_verdict_passes(self):
        self.assertEqual(validate_verdict(VALID_VERDICT), [])

    def test_incorrect_total_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "Pro Total Score: 20 out of 25",
            "Pro Total Score: 19 out of 25",
        )
        self.assertTrue(
            any("total mismatch" in error.lower()
                for error in validate_verdict(verdict))
        )

    def test_missing_criterion_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "| Evidence quality | 3 | Some examples, limited evidence. | 2 | Little verifiable evidence. |",
            "",
        )
        errors = validate_verdict(verdict)
        self.assertTrue(any("Evidence quality" in error for error in errors))

    def test_contradictory_final_decision_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "Pro wins based on the higher total.",
            "Counter wins based on the higher total.",
        )

        errors = validate_verdict(verdict)

        self.assertTrue(
            any("final decision" in error.lower() for error in errors),
            "Validator should reject a final decision that contradicts the winner.",
        )

    def test_wrong_winner_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "**Winning Side: Pro**",
            "**Winning Side: Counter**",
        )
        self.assertTrue(
            any("winner conflicts" in error.lower()
                for error in validate_verdict(verdict))
        )

    def test_invalid_score_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "| Relevance | 5 | Directly addresses the motion. | 4 | Addresses the motion. |",
            "| Relevance | 6 | Directly addresses the motion. | 4 | Addresses the motion. |",
        )
        self.assertTrue(
            any("outside 1–5" in error
                for error in validate_verdict(verdict))
        )

    def test_wrong_criterion_order_is_rejected(self):
        lines = VALID_VERDICT.splitlines()
        first = next(i for i, line in enumerate(lines)
                     if line.startswith("| Logical consistency |"))
        second = next(i for i, line in enumerate(lines)
                      if line.startswith("| Relevance |"))
        lines[first], lines[second] = lines[second], lines[first]
        errors = validate_verdict("\n".join(lines))
        self.assertTrue(
            any("order" in error.lower() for error in errors),
            "Validator should reject criteria in the wrong order",
        )


if __name__ == "__main__":
    unittest.main()


class TestCorrectVerdictConsistency(unittest.TestCase):
    def test_corrects_total_mismatch(self):
        from debate_crew.validator import correct_verdict_consistency

        text = VALID_VERDICT.replace(
            "Pro Total Score: 20 out of 25",
            "Pro Total Score: 19 out of 25",
        )
        corrected = correct_verdict_consistency(text)
        self.assertIn("**Pro Total Score: 20 out of 25**", corrected)

    def test_corrects_winner_to_tie(self):
        from debate_crew.validator import correct_verdict_consistency

        text = VALID_VERDICT.replace(
            "| Logical consistency | 4 | The argument is consistent. | 3 | One point is unclear. |",
            "| Logical consistency | 4 | The argument is consistent. | 4 | One point is unclear. |",
        ).replace(
            "| Relevance | 5 | Directly addresses the motion. | 4 | Addresses the motion. |",
            "| Relevance | 5 | Directly addresses the motion. | 5 | Addresses the motion. |",
        ).replace(
            "| Reasoning | 4 | Explains the causal links. | 3 | Reasoning needs development. |",
            "| Reasoning | 4 | Explains the causal links. | 4 | Reasoning needs development. |",
        ).replace(
            "| Evidence quality | 3 | Some examples, limited evidence. | 2 | Little verifiable evidence. |",
            "| Evidence quality | 3 | Some examples, limited evidence. | 3 | Little verifiable evidence. |",
        ).replace(
            "| Counterargument handling | 4 | Addresses major objections. | 3 | Misses one objection. |",
            "| Counterargument handling | 4 | Addresses major objections. | 4 | Misses one objection. |",
        ).replace(
            "Counter Total Score: 15 out of 25",
            "Counter Total Score: 20 out of 25",
        ).replace(
            "**Winning Side: Pro**",
            "**Winning Side: Counter**",
        )

        corrected = correct_verdict_consistency(text)
        self.assertIn("**Pro Total Score: 20 out of 25**", corrected)
        self.assertIn("**Counter Total Score: 20 out of 25**", corrected)
        self.assertIn("**Winning Side: Tie**", corrected)

    def test_rejects_malformed_table(self):
        from debate_crew.validator import correct_verdict_consistency

        text = VALID_VERDICT.replace(
            "| Logical consistency | 4 | The argument is consistent. | 3 | One point is unclear. |",
            "",
        )
        with self.assertRaises(ValueError):
            correct_verdict_consistency(text)


class TestAdditionalVerdictRules(unittest.TestCase):
    def test_high_evidence_score_without_verifiable_reference_is_flagged(self):
        verdict = VALID_VERDICT.replace(
            "| Evidence quality | 3 | Some examples, limited evidence. | 2 | Little verifiable evidence. |",
            "| Evidence quality | 4 | Some examples, limited evidence. | 2 | Little verifiable evidence. |",
        ).replace(
            "Pro Total Score: 20 out of 25",
            "Pro Total Score: 21 out of 25",
        )
        errors = validate_verdict(verdict)
        self.assertTrue(
            any("evidence" in error.lower() for error in errors),
            "Unsupported high evidence score should be flagged.",
        )

    def test_invalid_scoring_table_header_is_rejected(self):
        verdict = VALID_VERDICT.replace(
            "| Criterion | Pro Score | Pro Justification | Counter Score | Counter Justification |",
            "| Category | Pro Score | Pro Justification | Counter Score | Counter Justification |",
        )
        errors = validate_verdict(verdict)
        self.assertTrue(
            any("header" in error.lower() or "table" in error.lower()
                for error in errors),
            "Wrong table header should be rejected.",
        )
