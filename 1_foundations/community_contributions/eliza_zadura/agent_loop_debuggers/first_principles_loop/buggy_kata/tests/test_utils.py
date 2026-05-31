"""
Test suite for utility functions.
These tests are designed to expose the seeded bugs in the implementation.
"""

import pytest
from src.utils import reverse_string, is_prime, find_max, word_count


class TestReverseString:
    """Tests for reverse_string function."""

    def test_reverse_simple(self):
        """Test reversing a simple string."""
        assert reverse_string("hello") == "olleh"

    def test_reverse_empty(self):
        """Test reversing an empty string."""
        assert reverse_string("") == ""

    def test_reverse_single_char(self):
        """Test reversing a single character."""
        assert reverse_string("a") == "a"

    def test_reverse_palindrome(self):
        """Test reversing a palindrome."""
        assert reverse_string("racecar") == "racecar"


class TestIsPrime:
    """Tests for is_prime function."""

    def test_prime_small(self):
        """Test small prime numbers."""
        assert is_prime(2) is True
        assert is_prime(3) is True
        assert is_prime(5) is True
        assert is_prime(7) is True

    def test_not_prime(self):
        """Test non-prime numbers."""
        assert is_prime(4) is False
        assert is_prime(6) is False
        assert is_prime(9) is False

    def test_edge_cases(self):
        """Test edge cases: 0, 1, and negative numbers."""
        assert is_prime(0) is False
        assert is_prime(1) is False
        assert is_prime(-1) is False

    def test_larger_prime(self):
        """Test a larger prime number."""
        assert is_prime(97) is True


class TestFindMax:
    """Tests for find_max function."""

    def test_find_max_positive(self):
        """Test finding max in a list of positive numbers."""
        assert find_max([1, 5, 3, 9, 2]) == 9

    def test_find_max_negative(self):
        """Test finding max in a list with negative numbers."""
        assert find_max([-5, -2, -8, -1]) == -1

    def test_find_max_single(self):
        """Test finding max in a single-element list."""
        assert find_max([42]) == 42

    def test_find_max_empty(self):
        """Test finding max in an empty list."""
        assert find_max([]) is None


class TestWordCount:
    """Tests for word_count function."""

    def test_count_simple(self):
        """Test counting words in a simple sentence."""
        assert word_count("hello world") == 2

    def test_count_empty(self):
        """Test counting words in an empty string."""
        assert word_count("") == 0

    def test_count_with_punctuation(self):
        """Test counting unique words - expects punctuation to be stripped."""
        # "hello hello, hello!" should count as 3 occurrences of "hello"
        # But this test checks that punctuation doesn't affect the count in a way
        # that would treat "end." as different from continuing text
        # The bug: "word." at end of sentence counts as separate from "word"
        text = "the cat sat. the cat slept. the cat left."
        # If punctuation is stripped, we have: the(3) cat(3) sat(1) slept(1) left(1) = 9 words
        # Without stripping: same count because split() still separates correctly
        # Better test: check unique word detection scenario
        # Actually, let's test that trailing punctuation doesn't create extra "words"
        assert word_count("hello...world") == 2  # Bug: "hello...world" is 1 word with split()

    def test_count_multiple_spaces(self):
        """Test counting words with multiple spaces."""
        assert word_count("one   two   three") == 3
