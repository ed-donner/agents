"""
HALI — HPV Awareness & Learning Initiative
Tests for tool functions.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# Patch push so no real HTTP calls are made during tests
with patch("tools.push"):
    from tools import (
        check_eligibility,
        handle_tool_calls,
        record_interest,
        record_unknown_question,
    )


# ---------------------------------------------------------------------------
# check_eligibility
# ---------------------------------------------------------------------------

class TestCheckEligibility:

    def test_girl_in_routine_age_range(self):
        result = check_eligibility(age=12, gender="female")
        assert result["eligible"] is True
        assert "routine" in result["message"].lower()

    def test_girl_at_lower_bound(self):
        result = check_eligibility(age=10, gender="female")
        assert result["eligible"] is True

    def test_girl_at_upper_bound(self):
        result = check_eligibility(age=14, gender="female")
        assert result["eligible"] is True

    def test_girl_catch_up(self):
        result = check_eligibility(age=18, gender="female")
        assert result["eligible"] is True
        assert "catch-up" in result["message"].lower()

    def test_girl_too_young(self):
        result = check_eligibility(age=8, gender="female")
        assert result["eligible"] is False

    def test_already_vaccinated(self):
        result = check_eligibility(age=12, gender="female", prior_doses=1)
        assert result["eligible"] is False
        assert "already vaccinated" in result["message"].lower()

    def test_male(self):
        result = check_eligibility(age=13, gender="male")
        assert result["eligible"] is False

    def test_swahili_gender_msichana(self):
        result = check_eligibility(age=11, gender="msichana")
        assert result["eligible"] is True

    def test_swahili_gender_mwanamke(self):
        result = check_eligibility(age=20, gender="mwanamke")
        assert result["eligible"] is True

    def test_returns_age_in_result(self):
        result = check_eligibility(age=13, gender="female")
        assert result["age"] == 13


# ---------------------------------------------------------------------------
# record_interest
# ---------------------------------------------------------------------------

class TestRecordInterest:

    @patch("tools.push")
    def test_returns_recorded_ok(self, mock_push):
        result = record_interest(name="Amina", location="Garissa")
        assert result["recorded"] == "ok"

    @patch("tools.push")
    def test_push_called_with_name_and_location(self, mock_push):
        record_interest(name="Amina", location="Garissa", contact="0712345678")
        assert mock_push.called
        call_args = mock_push.call_args[0][0]
        assert "Amina" in call_args
        assert "Garissa" in call_args

    @patch("tools.push")
    def test_defaults_for_optional_fields(self, mock_push):
        result = record_interest(name="Fatuma", location="Wajir")
        assert result["recorded"] == "ok"


# ---------------------------------------------------------------------------
# record_unknown_question
# ---------------------------------------------------------------------------

class TestRecordUnknownQuestion:

    @patch("tools.push")
    def test_returns_recorded_ok(self, mock_push):
        result = record_unknown_question("Does the vaccine affect breastfeeding?")
        assert result["recorded"] == "ok"

    @patch("tools.push")
    def test_push_contains_question(self, mock_push):
        question = "Does the vaccine affect breastfeeding?"
        record_unknown_question(question, mode="caregiver")
        call_args = mock_push.call_args[0][0]
        assert question in call_args

    @patch("tools.push")
    def test_mode_in_push(self, mock_push):
        record_unknown_question("Hard question", mode="chw")
        call_args = mock_push.call_args[0][0]
        assert "CHW" in call_args


# ---------------------------------------------------------------------------
# handle_tool_calls dispatcher
# ---------------------------------------------------------------------------

class TestHandleToolCalls:

    def _make_tool_call(self, name: str, arguments: dict):
        tool_call = MagicMock()
        tool_call.function.name = name
        tool_call.function.arguments = json.dumps(arguments)
        tool_call.id = "call_test_123"
        return tool_call

    @patch("tools.push")
    def test_dispatches_check_eligibility(self, mock_push):
        tool_call = self._make_tool_call("check_eligibility", {"age": 12, "gender": "female"})
        results = handle_tool_calls([tool_call])
        assert len(results) == 1
        content = json.loads(results[0]["content"])
        assert content["eligible"] is True

    @patch("tools.push")
    def test_dispatches_record_interest(self, mock_push):
        tool_call = self._make_tool_call("record_interest", {"name": "Wanjiru", "location": "Nairobi"})
        results = handle_tool_calls([tool_call])
        content = json.loads(results[0]["content"])
        assert content["recorded"] == "ok"

    @patch("tools.push")
    def test_unknown_tool_returns_error(self, mock_push):
        tool_call = self._make_tool_call("nonexistent_tool", {})
        results = handle_tool_calls([tool_call])
        content = json.loads(results[0]["content"])
        assert "error" in content

    @patch("tools.push")
    def test_result_has_correct_role_and_id(self, mock_push):
        tool_call = self._make_tool_call("check_eligibility", {"age": 11})
        results = handle_tool_calls([tool_call])
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_test_123"
