#!/usr/bin/env python3
"""Test script to validate guardrails in deep_research."""

import os
from guardrails import run_guardrails

# Test cases: (query, answers, expected_passed, description)
test_cases = [
    # Should pass
    ("What is quantum computing?", [], True, "Valid research query"),
    ("Impact of AI on healthcare", ["Focus on Europe", "Last 5 years"], True, "Valid with answers"),

    # Should fail - PII
    ("Research about siva@example.com", [], False, "Contains email"),
    ("Call me at +44 1234 567890", [], False, "Contains phone"),
    ("My postcode is SW1A 1AA", [], False, "Contains postcode"),

    # Should fail - intent
    ("", [], False, "Empty query"),
    ("Write a poem about cats", [], False, "Not research"),
    ("Tell me a joke", [], False, "Off-topic"),

    # Should fail - length
    ("A" * 2500, [], False, "Query too long"),
    ("Short", ["A" * 8000], False, "Total input too long"),

    # Edge case - recipient email allowed
    ("Research topic\nRecipient email: test@example.com", [], True, "Recipient email allowed"),
]

def run_tests():
    print("Testing guardrails...\n")
    passed_tests = 0
    total_tests = len(test_cases)

    for query, answers, expected, desc in test_cases:
        result = run_guardrails(
            query,
            answers,
            check_pii=True,
            check_intent=True,
            check_length=True,
            allow_recipient_email=True
        )
        success = (result.passed == expected)
        status = "PASS" if success else "FAIL"
        print(f"{status}: {desc}")
        if not success:
            print(f"  Expected: {'pass' if expected else 'fail'}")
            print(f"  Got: {'pass' if result.passed else 'fail'} - {result.message}")
        else:
            passed_tests += 1
        print()

    print(f"Results: {passed_tests}/{total_tests} tests passed")
    if passed_tests == total_tests:
        print("All guardrails are working correctly!")
    else:
        print("Some guardrails need fixing.")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Intent checks will be skipped.")
    run_tests()