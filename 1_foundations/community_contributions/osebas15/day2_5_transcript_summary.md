# Day 2 Part 5: Workflow Design Patterns Summary

## 5 Anthropic Workflow Design Patterns

### 1. **Prompt Chaining**
- **Pattern**: Sequential LLM calls with optional code between steps
- **Architecture**: `LLM → [Code] → LLM → [Code] → LLM`
- **Use Case**: Decompose complex tasks into fixed subtasks
- **Example**: Sector → Pain Point → Solution
- **Key**: Each LLM call precisely framed for optimal response

### 2. **Routing**
- **Pattern**: LLM router decides which specialist model handles task
- **Architecture**: `Input → Router LLM → Specialist LLM (1/2/3)`
- **Use Case**: Separation of concerns with expert models
- **Key**: Router classifies tasks and routes to appropriate specialists

### 3. **Parallelization**
- **Pattern**: Code breaks task into parallel pieces, sends to multiple LLMs
- **Architecture**: `Code → [LLM1, LLM2, LLM3] → Code (aggregator)`
- **Use Case**: Concurrent subtasks or multiple attempts at same task
- **Key**: Code orchestrates, not LLM; can aggregate results

### 4. **Orchestrator-Worker**
- **Pattern**: LLM breaks down complex task, other LLMs execute, LLM recombines
- **Architecture**: `Orchestrator LLM → [Worker LLMs] → Orchestrator LLM`
- **Use Case**: Dynamic task decomposition and synthesis
- **Key**: LLM (not code) does orchestration; more flexible than parallelization

### 5. **Evaluator-Optimizer**
- **Pattern**: Generator LLM creates solution, Evaluator LLM validates/rejects
- **Architecture**: `Generator LLM → Evaluator LLM → [Accept/Reject Loop]`
- **Use Case**: Quality assurance and accuracy improvement
- **Key**: Feedback loop for validation; most commonly used pattern

## Key Architectural Insights

- **Blurred Lines**: Distinction between workflows and agents is artificial
- **Autonomy Elements**: Even workflows can have discretion and autonomy
- **Guardrails**: Workflows provide constraints while maintaining flexibility
- **Production Focus**: Evaluator pattern crucial for accuracy and robustness

## Pattern Comparison

| Pattern | Orchestrator | Flexibility | Use Case |
|---------|-------------|-------------|----------|
| Prompt Chaining | Code | Low | Sequential tasks |
| Routing | LLM | Medium | Expert selection |
| Parallelization | Code | Medium | Concurrent tasks |
| Orchestrator-Worker | LLM | High | Dynamic decomposition |
| Evaluator-Optimizer | LLM | High | Quality assurance | 