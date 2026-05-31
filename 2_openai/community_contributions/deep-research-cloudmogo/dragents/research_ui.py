import gradio as gr

from models.models import AppState, Clarification, ResearchState, ResearchUIState


def empty_clarification() -> Clarification:
    """Create an empty clarification state for the UI."""
    return Clarification(clarification_questions=[], clarification_answers=[])


def empty_ui_state() -> ResearchUIState:
    """Create the default UI state."""
    return ResearchUIState(
        clarification=empty_clarification(),
        show_submit=False,
        show_output=False,
    )


def empty_app_state(query: str = "") -> AppState:
    """Create the default top-level app state."""
    return AppState(query=query, ui=empty_ui_state(), research=None)


def build_ui_state_from_clarification(clarification: Clarification) -> ResearchUIState:
    """Build the UI state after clarification questions are available."""
    return ResearchUIState(
        clarification=clarification,
        show_submit=len(clarification.clarification_questions) > 0,
        show_output=False,
    )


def build_app_state_from_clarification(
    query: str,
    clarification: Clarification,
) -> AppState:
    """Build the app state after clarification questions are available."""
    return AppState(
        query=query,
        ui=build_ui_state_from_clarification(clarification),
        research=ResearchState(
            original_query=query,
            clarification=clarification,
            needs_clarification=False,
            next_action="plan_searches",
        ),
    )


def build_question_updates(
    clarification: Clarification,
    max_questions: int,
) -> list[dict]:
    """Convert clarification questions into textbox visibility updates."""
    questions = (clarification.clarification_questions or [])[:max_questions]
    updates = []

    for index in range(max_questions):
        if index < len(questions):
            updates.append(
                gr.update(
                    label=questions[index],
                    value="",
                    visible=True,
                    interactive=True,
                )
            )
        else:
            updates.append(
                gr.update(
                    label="",
                    value="",
                    visible=False,
                )
            )

    return updates


def render_question_screen(
    app_state: AppState,
    max_questions: int,
) -> list:
    """Render clarification question inputs plus button visibility from UI state."""
    updates = build_question_updates(app_state.ui.clarification, max_questions)
    submit_update = gr.update(visible=app_state.ui.show_submit)
    return [*updates, submit_update, app_state]


def fill_clarification_answers(
    clarification: Clarification,
    answer_values: list[str],
) -> Clarification:
    """Attach UI answer values to the clarification questions."""
    questions = (clarification.clarification_questions or [])[: len(answer_values)]
    answers = []

    for answer in answer_values[: len(questions)]:
        answers.append((answer or "").strip())

    return Clarification(
        clarification_questions=questions,
        clarification_answers=answers,
    )


def apply_answers_to_app_state(
    app_state: AppState,
    answer_values: list[str],
) -> AppState:
    """Build the answered clarification payload into the top-level app state."""
    clarification = fill_clarification_answers(app_state.ui.clarification, answer_values)
    research = (
        app_state.research.model_copy(update={"clarification": clarification})
        if app_state.research is not None
        else ResearchState(
            original_query=app_state.query,
            clarification=clarification,
            needs_clarification=False,
            next_action="plan_searches",
        )
    )
    next_ui_state = app_state.ui.model_copy(update={"clarification": clarification})
    return app_state.model_copy(update={"ui": next_ui_state, "research": research})


def show_output_update(app_state: AppState):
    """Reveal the output panel while preserving app state."""
    next_ui_state = app_state.ui.model_copy(update={"show_output": True})
    next_state = app_state.model_copy(update={"ui": next_ui_state})
    return gr.update(visible=next_ui_state.show_output, value=""), next_state
