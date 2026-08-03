from kb_state import KBState
from utils import get_llm
from models import ResearchPlan



def research_planner(state: KBState) -> dict:
    """Creates or revises the research plan."""
    llm = get_llm().with_structured_output(ResearchPlan)

    feedback_context = ''
    if state["plan_feedback"]:
        feedback_context = f'''
        Previous feedback (you MUST address every point):
        {'\n'.join(state['plan_feedback'])}
        '''

    prompt = f'''
    Create a comprehensive search plan for the following topic:

    **Topic:** {state["topic"]}

    {feedback_context}

    Break the domain into logical subtopics, each with specific search queries.
    Prioritize by importance and relevance to the field.
    Ensure queries are detailed enough to retrieve high-quality sources.
    The plan should be actionable and detailed enough for a search engine to execute.
    '''

    plan: ResearchPlan = llm.invoke(prompt)

    return {
        'research_plan': plan,
        'plan_revision_count': state.get('plan_revision_count', 0) + 1,
        # 'messages': state['messages'] + [{'role': 'planner', 'content': plan}]
        'messages': [{
            'role': 'planner',
            'content': f'Proposed plan with {len(plan.subtopics)} subtopics'
        }]
    }


