"""Offline tests for the deep_research extensions - no API calls, no network.

Run from this folder:  python test_offline.py
"""
from clarifier_agent import ClarifyingQuestions, clarifier_agent, HOW_MANY_QUESTIONS
from evaluator_agent import EvaluationResult, evaluator_agent
from planner_agent import WebSearchItem
from research_manager import ResearchManager
from research_agent import research_manager_agent, build_manager_input

CLAR = ResearchManager.format_clarifications(["Scope?"], ["EU only"])


def test_clarifying_questions_model():
    cq = ClarifyingQuestions.model_validate({"questions": ["Scope?", "Time frame?", "Audience?"]})
    assert cq.questions == ["Scope?", "Time frame?", "Audience?"]


def test_clarifier_is_structured():
    assert clarifier_agent.output_type is ClarifyingQuestions
    assert HOW_MANY_QUESTIONS == 3


def test_format_clarifications_combines_qa():
    text = ResearchManager.format_clarifications(
        ["Scope?", "Depth?"], ["EU only", "Detailed"]
    )
    assert "Scope?" in text and "EU only" in text
    assert "Depth?" in text and "Detailed" in text


def test_format_clarifications_empty_when_none():
    assert ResearchManager.format_clarifications([], []) == ""


def test_format_clarifications_skips_blank_questions():
    # The Gradio layer pads to 3 questions; blank ones should be ignored.
    text = ResearchManager.format_clarifications(["Scope?", ""], ["EU only", ""])
    assert "Scope?" in text and "EU only" in text
    assert text.count("- Q:") == 1


# --- Challenge #2: evaluator + clarification propagation ---

def test_evaluation_result_model():
    ev = EvaluationResult.model_validate({"aligned": False, "feedback": "Missing the EU angle"})
    assert ev.aligned is False and "EU" in ev.feedback


def test_evaluator_is_structured():
    assert evaluator_agent.output_type is EvaluationResult


def test_clarifications_propagate_to_planner():
    out = ResearchManager.build_planner_input("AI agents", CLAR, feedback="cover EU regulation")
    assert "AI agents" in out and "EU only" in out and "EU regulation" in out


def test_clarifications_propagate_to_search():
    item = WebSearchItem(reason="why", query="AI agents EU")
    out = ResearchManager.build_search_input(item, CLAR)
    assert "AI agents EU" in out and "EU only" in out


def test_clarifications_propagate_to_writer():
    out = ResearchManager.build_writer_input("AI agents", ["summary1"], CLAR)
    assert "AI agents" in out and "EU only" in out and "summary1" in out


def test_clarifications_propagate_to_evaluator():
    out = ResearchManager.build_evaluator_input("AI agents", CLAR, ["summary1"])
    assert "AI agents" in out and "EU only" in out and "summary1" in out


def test_builders_omit_clarifications_when_absent():
    # With no clarifications the blocks should simply be left out, not add empty noise.
    assert "Clarifications" not in ResearchManager.build_planner_input("AI agents", "")
    item = WebSearchItem(reason="why", query="AI agents")
    assert "Focus your summary" not in ResearchManager.build_search_input(item, "")


# --- Challenge #3: autonomous manager agent (agents-as-tools, no handoffs) ---

def test_manager_uses_agents_as_tools_not_handoffs():
    assert research_manager_agent.handoffs == []
    names = {t.name for t in research_manager_agent.tools}
    assert {"plan_searches", "web_search", "evaluate_alignment", "write_report", "send_report_email"} <= names


def test_manager_input_includes_query_and_clarifications():
    out = build_manager_input("AI agents", CLAR)
    assert "AI agents" in out and "EU only" in out


def test_manager_input_without_clarifications():
    out = build_manager_input("AI agents")
    assert "AI agents" in out and "Clarifications" not in out


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS  {name}")
    print("\nAll offline tests passed")
