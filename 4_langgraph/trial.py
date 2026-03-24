# pip install langgraph langchain-openai langchain-core

from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator

# ── 1. Shared State ────────────────────────────────────────────────────────────
class DebateState(TypedDict):
    topic: str
    proposer_argument: str
    opposer_argument: str
    verdict: dict          # { winner, score_proposer, score_opposer, reasoning }

# ── 2. LLM ────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# ── 3. Agent Nodes ─────────────────────────────────────────────────────────────
def proposer_node(state: DebateState) -> dict:
    """Argues FOR the motion."""
    messages = [
        SystemMessage(content="""You are a skilled debater arguing IN FAVOUR of the motion.
        Craft a compelling, structured argument. Be persuasive and use logical reasoning."""),
        HumanMessage(content=f"""Motion: "{state['topic']}"
        Present your opening argument FOR this motion.""")
    ]
    response = llm.invoke(messages)
    return {"proposer_argument": response.content}


def opposer_node(state: DebateState) -> dict:
    """Argues AGAINST the motion, rebutting the proposer."""
    messages = [
        SystemMessage(content="""You are a skilled debater arguing AGAINST the motion.
        Directly counter the proposer's points. Be persuasive and logical."""),
        HumanMessage(content=f"""Motion: "{state['topic']}"

The Proposer argued:
\"\"\"{state['proposer_argument']}\"\"\"

Now argue AGAINST the motion and rebut their points.""")
    ]
    response = llm.invoke(messages)
    return {"opposer_argument": response.content}


def judge_node(state: DebateState) -> dict:
    """Evaluates both sides and delivers a verdict."""
    messages = [
        SystemMessage(content="""You are an impartial debate judge.
        Evaluate on: logical strength, evidence, persuasiveness, and rebuttal quality.
        Respond ONLY in JSON:
        { "winner": "Proposer|Opposer|Draw",
          "score_proposer": <0-10>,
          "score_opposer": <0-10>,
          "reasoning": "<2-3 sentences>" }"""),
        HumanMessage(content=f"""Motion: "{state['topic']}"

--- PROPOSER ---
{state['proposer_argument']}

--- OPPOSER ---
{state['opposer_argument']}

Deliver your verdict.""")
    ]
    response = llm.invoke(messages)

    import json, re
    raw = response.content
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    verdict = json.loads(match.group()) if match else {"winner": "Draw", "reasoning": raw}
    return {"verdict": verdict}

def should_continue(state: DebateState) -> str:
    scores = state["verdict"]
    # too close to call — debate another round
    if abs(scores["score_proposer"] - scores["score_opposer"]) < 2:
        return "proposer"   # loops back
    return END


# ── 4. Build the Graph ─────────────────────────────────────────────────────────
builder = StateGraph(DebateState)

builder.add_node("proposer", proposer_node)
builder.add_node("opposer",  opposer_node)
builder.add_node("judge",    judge_node)
builder.add_conditional_edges("judge", should_continue, {
    "proposer": "proposer",
    END: END
})

builder.set_entry_point("proposer")      # START → proposer
builder.add_edge("proposer", "opposer")  # proposer → opposer
builder.add_edge("opposer",  "judge")    # opposer  → judge
builder.add_edge("judge",    END)        # judge    → END

graph = builder.compile()

# ── 5. Run ─────────────────────────────────────────────────────────────────────
result = graph.invoke({
    "topic": "AI will do more harm than good to society",
    "proposer_argument": "",
    "opposer_argument": "",
    "verdict": {}
})

print("=== PROPOSER ===")
print(result["proposer_argument"])

print("\n=== OPPOSER ===")
print(result["opposer_argument"])

print("\n=== VERDICT ===")
v = result["verdict"]
print(f"Winner:   {v['winner']}")
print(f"Scores:   PRO {v['score_proposer']}/10  vs  CON {v['score_opposer']}/10")
print(f"Reasoning: {v['reasoning']}")