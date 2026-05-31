from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import ResearchState
from dotenv import load_dotenv

load_dotenv(override=True)

llm = ChatOpenAI(model="gpt-4o-mini")

class GeneratedTopics(BaseModel):
    topics: list[str] = Field(description="Three relevant research topics.")

def topic_generator_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: TOPIC GENERATOR NODE")
    structured_llm = llm.with_structured_output(GeneratedTopics)
    qa_pairs = "\n".join(
        f"Q: {q}\nA: {a}" for q, a in zip(state.clarifying_questions or [], state.clarifying_answers or [])
    )

    full_context = f"""
    Original User Query:
    {state.user_query}

    Clarification Transcript:
    {qa_pairs}
    """

    prompt = f"""
    You are a helpful research assistant. You are provided with the following input: {full_context}. It contains the following:
    1. Original user query: It is the high level user query.
    2. Clarification transcript: It is the transcript of the clarifying questions the user was asked and their answers.
    Your job is to analyze this entire information and generate 3 concise, relevant research topics.
    """
    
    if state.feedback and not state.is_acceptable:
        print(f"RETRYING Topic Generation (Attempt {state.retry_count + 1})")
        prompt += f"""
        The previous attempt FAILED.
        The evaluator rejected the previous topics for the following reason: {state.feedback}
        You must address this feedback and generate an improved, more relevant set of topics.
        """
        state.retry_count += 1

    result = structured_llm.invoke(prompt)
    print("Topics have been generated.")
    state.topics = result.topics
    state.full_context = full_context.strip()
    return state