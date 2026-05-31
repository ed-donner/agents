from agents import Agent

from langchain_chroma import Chroma


MODEL_OPENAI = "gpt-4o-mini"
LOCAL_MODEL_OPENAI = "gpt-oss:20b"

SYSTEM_PROMPT_TEMPLATE = f"""
You are a helpful, friendly assistant representing the candidate.
The candidate needs a job and you are helping them to get it.

Based on the given job description, create a cover letter and get the role, company, hiring manager email and name from the job description.

Here is the context of the candidate's resume:
{context}

I need your response to be in JSON format:
{{
    "cover_letter": "The cover letter text",
    "role": "The position"
    "hiring_manager_email": "The email",
    "hiring_manager_name": "The name",
    "company": "The company",
}}
"""

# change llm library to use openai

def surfer_agent(job_description: str, vectorstore: Chroma) ->Agent:
    retriever = vectorstore.as_retriever()
    docs = retriever.invoke(job_description)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    return Agent(
        name="Surfer agent",
        instructions=system_prompt,
        model=MODEL_OPENAI,
    )


