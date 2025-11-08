from datetime import datetime
from agents import Agent, Tool
from config import client, MODEL, CLARIFIER_MAX_TOKENS
import re

#limiting the numbe rof times it can seek clarity. kept small for the sake of tokens
MAX_ROUNDS = 2

def _safe_get_original_query(history, user_message):
    if history:
        first = history[0]
        if isinstance(first, dict):
            return first.get("user") or first.get("content") or user_message
    return user_message

def clarifier_step(state, user_message=None):
    if state is None:
        state = {"round": 1, "history": [], "final_query": None}

    round_num = state.get("round", 1)
    history = state.get("history", [])

    if user_message is not None:
        history.append({"user": user_message})
    if state.get("final_query"):
        return "Got it — final query already produced. Please wait for your report.", state
    if round_num > MAX_ROUNDS:
        final_query = finalize_query(history)
        state["final_query"] = final_query
        state["history"] = history
        return f"Final Clarified Query: {final_query}", state


    conversation_context = "\n".join(
        [f"Q: {turn.get('clarifier', '')}\nA: {turn.get('user', '')}" for turn in history]
    )

    original_query = _safe_get_original_query(history, user_message)

    prompt = f"""
You are a Clarifier Agent whose goal is to produce a clear single final research question.
Rules:- Ask only ONE missing clarification question per turn if necessary.- Do not repeat previous questions. - If clarity is achieved, respond exactly in this format:
Final Clarified Query: <concise final query>
Conversation so far:{conversation_context}
Original user request:{original_query}
"""

    #call model
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a concise, highly structured clarifier."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=CLARIFIER_MAX_TOKENS,
            temperature=0.0,
        )
        response = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[clarifier] API call failed: {e}")
        fallback = "Could you specify the geographic scope (e.g., country, region) for this request?"
        history.append({"clarifier": fallback})
        state["round"] = round_num + 1
        state["history"] = history
        return f"**Clarification Round {round_num}/{MAX_ROUNDS}**\n\n{fallback}", state

    if response.startswith("Final Clarified Query:"):
        final_text = response.replace("Final Clarified Query:", "").strip()
        final_text = re.sub(r"\s+", " ", final_text).strip()
        state["final_query"] = final_text
        state["history"] = history
        return f"Please wait... Final Query: {final_text}", state

    history.append({"clarifier": response})
    state["round"] = round_num + 1
    state["history"] = history

    return f"**Clarification Round {round_num}/{MAX_ROUNDS}**\n\n{response}", state


def finalize_query(history):
    answers = [h.get("user") for h in history if h.get("user")]
    combined = ", ".join(answers)
    return combined if combined else "User intent unclear; request a broad feasibility analysis."

async def get_clarifier_tool(mcp_servers) -> Tool:
    agent = Agent(
        name="ClarifierAgent",
        instructions=f"Iteratively refines user queries. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="ClarifierAgent",
        tool_description="Refines user input into a clear, structured final query.",
        func=clarifier_step
    )
