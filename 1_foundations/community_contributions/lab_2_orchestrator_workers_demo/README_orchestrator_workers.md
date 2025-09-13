# Orchestrator-Workers Workflow Demo

## Overview

This implementation demonstrates the **orchestrator-workers workflow** pattern from Anthropic's ["Building Effective Agents"](https://www.anthropic.com/engineering/building-effective-agents) blog post. This pattern is fundamentally different from the **evaluator-optimizer workflow** used in lab 2.

## Pattern Comparison

### Lab 2: Evaluator-Optimizer Workflow
- **What it does**: Sends the same task to multiple LLMs and uses a judge to rank/compare their responses
- **Use case**: Quality improvement, model comparison, finding the best response
- **Structure**: Task → Multiple Models → Judge → Ranking
- **Trade-offs**: Higher cost, more complex evaluation, but better quality assurance

### This Demo: Orchestrator-Workers Workflow
- **What it does**: A central LLM breaks down a complex task into subtasks, delegates them to specialized workers, and synthesizes results
- **Use case**: Complex tasks requiring diverse expertise, scalable problem-solving
- **Structure**: Complex Task → Orchestrator → Subtasks → Specialized Workers → Synthesis
- **Trade-offs**: More complex orchestration, potential coordination issues, but better for complex, multi-faceted problems

## How It Works

1. **Task Breakdown**: The orchestrator (GPT-4) analyzes a complex task and breaks it into 3-4 focused subtasks
2. **Worker Assignment**: Each subtask is assigned to a specialized worker LLM with different expertise
3. **Parallel Execution**: Workers execute their subtasks independently using different models
4. **Result Synthesis**: The orchestrator combines all worker results into a comprehensive final report

## Key Features

- **Dynamic Task Decomposition**: Unlike predefined workflows, the orchestrator determines subtasks based on the specific input
- **Model Specialization**: Different LLMs handle different types of analysis (safety, economic, legal, etc.)
- **Flexible Architecture**: Can handle tasks where you can't predict the required subtasks in advance
- **Comprehensive Synthesis**: Integrates diverse perspectives into a coherent final report

## Usage

### Prerequisites
- OpenAI API key (required)
- Anthropic API key (required)
- Google API key (optional, for Gemini)
- DeepSeek API key (optional)
- Groq API key (optional)

### Running the Demo

#### Option 1: Direct execution with uv
```bash
cd 1_foundations/community_contributions/lab_2_orchestrator_workers_demo
uv run orchestrator_workers_demo.py
```

#### Option 2: Install dependencies and run
```bash
cd 1_foundations/community_contributions/lab_2_orchestrator_workers_demo
uv sync  # Install dependencies
uv run python orchestrator_workers_demo.py
```

#### Option 3: From project root
```bash
# From the agents project root
uv run python 1_foundations/community_contributions/lab_2_orchestrator_workers_demo/orchestrator_workers_demo.py
```

#### Option 4: With specific Python version
```bash
uv run --python 3.11 python orchestrator_workers_demo.py
```

### Customizing the Task

Modify the `complex_task` variable in the `main()` function to analyze different topics:

```python
complex_task = """
Analyze the impact of renewable energy adoption on:
1. Economic development
2. Environmental sustainability  
3. Social equity and access
4. Technological innovation

Provide comprehensive analysis with recommendations.
"""
```

## Architecture

```
Complex Task
     ↓
Orchestrator (GPT-4)
     ↓
Task Breakdown → Subtask 1 → Worker 1 (Claude - Safety)
     ↓                    → Subtask 2 → Worker 2 (GPT-4 - Economic)  
     ↓                    → Subtask 3 → Worker 3 (Gemini - Legal)
     ↓
Result Synthesis (GPT-4)
     ↓
Final Comprehensive Report
```

## When to Use Each Pattern

### Use Evaluator-Optimizer When:
- You need to compare multiple approaches to the same problem
- Quality and accuracy are the primary concerns
- You want to identify the best response from multiple candidates
- Cost is less important than quality assurance

### Use Orchestrator-Workers When:
- You have a complex, multi-faceted problem
- Different aspects require specialized expertise
- You can't predict the required subtasks in advance
- You need scalable, systematic problem decomposition
- You want to leverage different LLM strengths for different tasks

## Business Applications

- **Research Projects**: Breaking down complex research questions into specialized analyses
- **Product Development**: Coordinating different aspects of product design and analysis
- **Policy Analysis**: Evaluating complex policy implications across multiple domains
- **Strategic Planning**: Decomposing strategic initiatives into actionable components
- **Content Creation**: Coordinating specialized content creation across different topics

## Future Enhancements

This implementation could be extended with:
- **Parallel Execution**: Run worker tasks simultaneously for better performance
- **Dynamic Worker Selection**: Choose workers based on task requirements
- **Quality Gates**: Add validation steps between orchestration phases
- **Error Handling**: Implement robust error handling and retry mechanisms
- **Memory Integration**: Add context memory for multi-turn conversations

## References

- [Building Effective Agents - Anthropic Engineering](https://www.anthropic.com/engineering/building-effective-agents)
- Lab 2: Evaluator-Optimizer Workflow Implementation
- Anthropic's Model Context Protocol for tool integration
