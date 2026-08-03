# Architecture Documentation

## Overview

The Autonomous Decision Engine (ADE) is a Human-in-the-Loop AI system built on LangGraph. It provides a structured framework for AI decision-making that prioritizes safety, transparency, and human oversight.

## Core Design Principles

### 1. Safety First
- No automatic irreversible actions
- No credential storage
- Human confirmation for high-risk tasks
- Clear refusal paths for dangerous requests

### 2. Transparency
- Complete audit trail of all decisions
- Clear reasoning for each routing choice
- Visible risk assessments

### 3. Separation of Concerns
- State management isolated from business logic
- Pure function nodes (state in → state out)
- Clear separation between routing and execution

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (app/ui/cli.py, app/main.py)                               │
├─────────────────────────────────────────────────────────────┤
│                      Graph Layer                             │
│  (app/graphs/decision_graph.py, routers.py)                 │
├─────────────────────────────────────────────────────────────┤
│                      Node Layer                              │
│  task_analyzer │ risk_evaluator │ worker │ evaluator │ ...  │
├─────────────────────────────────────────────────────────────┤
│                     State Layer                              │
│  (app/state/schema.py, enums.py)                            │
├─────────────────────────────────────────────────────────────┤
│                    Tools Layer                               │
│  (app/tools/browser.py, search.py, document.py)             │
├─────────────────────────────────────────────────────────────┤
│                   Memory Layer                               │
│  (app/memory/checkpoint.py - SQLite)                        │
└─────────────────────────────────────────────────────────────┘
```

## State Schema

The `ADEState` TypedDict flows through all nodes:

| Field | Type | Purpose |
|-------|------|---------|
| `task_input` | str | Original user request |
| `task_analysis` | TaskAnalysis | Structured classification |
| `risk_assessment` | RiskAssessment | Risk scores and flags |
| `decision` | DecisionType | Current routing decision |
| `messages` | list | Conversation history |
| `work_output` | str | Output from worker |
| `evaluation` | EvaluationOutput | Quality assessment |
| `decision_path` | list[DecisionRecord] | Audit trail |
| `thread_id` | str | Session identifier |

## Decision Flow

### 1. Task Analysis
The `task_analyzer` node classifies incoming tasks:
- Domain detection (Campus France, visa, general, etc.)
- Complexity assessment (simple, moderate, complex)
- Ambiguity detection
- Authentication requirements
- External action detection

### 2. Risk Evaluation
The `risk_evaluator` node assesses risk across categories:
- **Legal**: Contracts, official documents
- **Financial**: Payments, scholarships
- **Ethical**: Privacy, consent
- **Hallucination**: Factual accuracy risk
- **Authentication**: Login requirements
- **Irreversible**: Permanent consequences

### 3. Decision Routing
Based on overall risk score:
- **AUTONOMOUS** (risk < 0.3): Full autonomy
- **TOOLS** (0.3 ≤ risk < 0.5): Tool-assisted
- **HUMAN** (0.5 ≤ risk < 0.7): Human confirmation
- **STOP** (risk ≥ 0.7): Refusal

### 4. Quality Gate
The `evaluator` node assesses work output:
- **PASS**: Complete, proceed to output
- **RETRY**: Needs improvement
- **ESCALATE**: Human review required

## Node Contracts

All nodes follow a pure function pattern:

```python
def node_name(state: ADEState) -> dict:
    """
    Process state and return updates.
    
    Args:
        state: Current graph state
    
    Returns:
        Dictionary of state updates (only changed fields)
    """
    # Read from state
    input_data = state["some_field"]
    
    # Process
    result = do_something(input_data)
    
    # Return updates only
    return {
        "output_field": result,
        "decision_path": [new_record],
    }
```

## Routing Logic

Conditional edges are defined in `app/graphs/routers.py`:

```python
def route_after_risk_evaluation(state: ADEState) -> str:
    decision = state.get("decision")
    if decision == DecisionType.AUTONOMOUS:
        return "worker"
    elif decision == DecisionType.TOOLS:
        return "tool_worker"
    elif decision == DecisionType.HUMAN:
        return "human_input"
    else:  # STOP
        return "refusal"
```

## Checkpointing

SQLite-based checkpointing enables:
- Session persistence across restarts
- Thread-based conversation continuity
- Audit log storage

Configuration:
```python
config = {"configurable": {"thread_id": "unique-session-id"}}
result = await graph.ainvoke(state, config=config)
```

## Domain Workflows

### Campus France Workflow

Special handling for scholarship applications:
- Automatic detection of Campus France tasks
- Step-specific guidance
- Enforced human login for portal access
- Submission requires explicit human action

Detected via keywords:
- "campus france", "études en france", "eiffel", "bourse france", etc.

## Tool Integration

### Read-Only Browser (Playwright)
- Navigate public pages
- Extract text content
- No form submissions
- No credential handling

### Web Search (Serper)
- Current information lookup
- Fact verification
- Optional (graceful fallback)

### Document Tools
- CV guidance (French format)
- Motivation letter templates
- Study project structure

## Security Considerations

### Never Stored
- User credentials
- API keys in state
- Personal identification documents

### Always Required
- Human confirmation for submissions
- Explicit approval for irreversible actions
- Clear consent for sensitive operations

### Logged
- All decisions and routing
- Risk assessments
- Human interactions

## Extension Points

### Adding New Domains
1. Create workflow in `app/workflows/`
2. Add detection keywords
3. Define step-specific constraints
4. Update `HIGH_RISK_DOMAINS` if needed

### Adding New Tools
1. Create tool in `app/tools/`
2. Return list of LangChain `Tool` objects
3. Import in `decision_graph.py`

### Custom Risk Categories
1. Add to `RiskCategory` enum
2. Update risk evaluation prompt
3. Adjust threshold logic if needed

