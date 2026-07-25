from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import ResearchState

llm = ChatOpenAI(model="gpt-4o-mini")

class EvaluationResult(BaseModel):
    feedback: str = Field(description="Feedback on topic quality.")
    score: float = Field(description="Numeric relevance score between 1 and 10.")
    is_acceptable: bool = Field(description="True if topics are relevant enough to continue.")

def topic_evaluator_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: TOPIC EVALUATOR NODE")
    
    structured_llm = llm.with_structured_output(EvaluationResult)

    topics_text = "\n".join(f"- {t}" for t in state.topics or [])

    prompt = f"""
    You are a senior research analyst. You are provided with the the following inputs:
    1. Full research context including the original query and clarifications: {state.full_context}
    2. List of proposed topics based on the user's query: {topics_text}
    Your job is to evaluate how relevant and well-aligned these topics are to the clarified user intent.
    Be strict with your judgement.
    Respond with:
    - feedback (a short paragraph)
    - score (1 - 10) based on how relevant the topics are.
    - is_acceptable = True if topics meet the clarified intent, else False
    """
    
    result = structured_llm.invoke(prompt)
    state.feedback = result.feedback
    state.score = result.score
    state.is_acceptable = result.is_acceptable

    # Track best topics
    if state.best_score is None or result.score > state.best_score:
        state.best_score = result.score
        state.best_topics = state.topics

    print(f"Evaluation result: score={result.score:.2f}, acceptable={result.is_acceptable}")
    print(f"Feedback: {result.feedback}\n")

    return state
