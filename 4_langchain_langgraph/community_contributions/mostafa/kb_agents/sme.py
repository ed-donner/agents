from tqdm import tqdm
from kb_state import KBState
from utils import get_llm
from models import PlanReview, ResearchPlan, SourceReview


def sme_plan_review(state: KBState) -> dict:
    """SME reviews the research plan. Returns approval decision."""
    llm = get_llm().with_structured_output(PlanReview)

    plan: ResearchPlan = state["research_plan"]

    prompt = f'''
    Review the following research plan for completeness, relevance, and quality. 

    **Topic:** {plan.topic}
    **Rationale:** {plan.rationale}

    **Subtopics:**
    {chr(10).join(
        [
            f'''
        - {sub.name}: {sub.description}
          Queries: {sub.search_queries}
        ''' for sub in plan.subtopics
        ]
    )}

    Evaluate:
    1. Does the plan cover all critical aspects of the domain?
    2. Are the subtopics genuinely important and distinct?
    3. Are the search queries likely to yield high-quality sources?
    4. Is the structure logical and coherent for a research project?
    5. Is the plan actionable and detailed enough for execution?

    Provide specific feedback for improvement if needed.
    '''

    review: PlanReview = llm.invoke(prompt)
    return {
        'plan_feedback': review.feedback,
        'messages': state['messages'] + [{
            'role': 'sme',
            'content': f'Plan review: {review.decision.value} with feedback: {review.reasoning}'
        }]
    }


def sme_source_review(state: KBState) -> dict:
    """SME reviews each raw source for credibility."""
    llm = get_llm().with_structured_output(SourceReview)

    approved_sources = []
    rejected_sources = []

    BATCH_SIZE = 5
    sources = state["raw_sources"]
    with tqdm(total=len(sources), desc="Reviewing sources", unit='source') as pbar:
        for i in range(0, len(sources), BATCH_SIZE):
            batch = sources[i:i + BATCH_SIZE]

            sources_text = '\n\n'.join(
                [f'''
            ## Source {j+1}
            - **URL:** {source.url}
            - **Title:** {source.title}
            - **Subtopic:** {source.subtopic}
            - **Snippet:** {source.snippet}
            - **Content preview:** {source.snippet})
            ''' for j, source in enumerate(batch)]
            )

            prompt = f'''
            Evaluate each source for inclusion in a knowledge base on the topic of {state["topic"]}.

            {sources_text}

            For each source, assess:
            1. Credibility of the source (authoritativeness, trustworthiness)
            2. Accuracy (factual correctness)
            3. Recency (is the information up-to-date?)
            4. Bias (commercial, ideological, etc.)
            5. Relevance to the subtopic
            6. Quality of content (depth, clarity, usefulness)


            Provide a decision for each source, along with reasoning.
            '''

            review: SourceReview = llm.invoke(prompt)
            approved_sources.extend(review.approved_sources)
            rejected_sources.extend(review.rejected_sources)
            pbar.set_postfix(approved=len(approved_sources),
                             rejected=len(rejected_sources))
            pbar.update(len(batch))

    return {
        'approved_sources': approved_sources,
        'rejected_sources': rejected_sources,
        'messages': [{
            'role': 'sme',
            'content': f'Approved {len(approved_sources)} sources, rejected {len(rejected_sources)} sources so far.'
        }]
    }


