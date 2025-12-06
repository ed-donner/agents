# Ensemble LLMs Rank Gemini-2.0-Flash as Best in Intelligence

Using Ed Donner's _The Complete Agentic AI Engineering Course (2025)_ as a starting point (specifically `1_lab2` in `1_foundations`), we launched an experiment to evaluate large language models (LLMs) through an ensemble-based ranking system.

## 🧠 Method Overview

1. OpenAI (GPT-4o) was prompted to create a challenging, nuanced question to test reasoning and intelligence.
2. Each LLM responded to this question.
3. Each LLM was then asked to judge the quality of all answers — including its own — and provide a ranked list.
4. Ranks were aggregated across judges using both mean and median.

The following table shows the aggregated results:

|  | Judges |  | | | | | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLMs | 03_mini | anthropic | deepseek | gemini | groq | ollama | mean | median |
| gpt-4o-mini | 2 | 2 | 2 | 2 | 1 | 1 | 1.7 | 2 |
| gemini-2.0-flash | 1 | 1 | 1 | 1 | 2 | 5 | 1.8 | 1 |
| deepseek-chat | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 | 3 |
| llama-3.3-70b-versatile | 4 | 4 | 4 | 4 | 4 | 4 | 4.0 | 4 |
| claude-3-7-sonnet-latest | 6 | 5 | 5 | 6 | 6 | 2 | 5.0 | 5 |
| llama3 | 5 | 6 | 6 | 5 | 5 | 6 | 5.5 | 5 |

## 🔍 Interpretation

The mean is sensitive to extremes. In this case, Ollama ranked Gemini-2.0-Flash as 5, while most others gave it rank 1. This skews the mean slightly higher. The median, however, is robust to such outliers (just like in figure skating judging).

Since Ollama is a smaller model, its outlier judgment may carry less reliability. Thus, the median is arguably a more accurate reflection — and by that standard, Gemini-2.0-Flash is the top performer.

## ❓ The Initial Question

The experiment began with this prompt to OpenAI:

> "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence."

OpenAI returned:

> "How would you approach resolving a moral dilemma where the decision to save one person over another would result in a significant societal impact, and how would you justify your choice?"

Each model responded to this question in turn.

## 🧑‍⚖️ Judging Prompt

Each model was then prompted to judge all the answers:

```python
judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""
```

## 🥇 The Winning Answer by Gemini

<details>
<summary>Gemini's Full Answer</summary>

This is a profoundly difficult ethical question, and there's no easy or universally accepted answer. Here's my approach, broken down into steps, along with potential justifications:

This is a profoundly difficult ethical question, and there's no easy or universally accepted answer. Here's my approach, broken down into steps, along with potential justifications:

1. Identify the Core Dilemma & Gather Information:

- Clarify the Stakes: What are the potential outcomes of each decision? What are the potential societal impacts (positive and negative) of saving each person? How significant are these impacts?
- Gather Relevant Facts: Who are the individuals involved? What are their backgrounds, contributions, skills, potential future contributions, vulnerabilities, dependencies, and responsibilities? What is the nature of the societal impact they represent? Are there pre-existing laws, regulations, or ethical guidelines that apply? Are there any experts to consult (e.g., ethicists, economists, social scientists)?
- Consider Alternative Solutions: Is there any way to save both individuals, mitigate the negative consequences of either choice, or find a third option? Exploring alternatives is crucial before committing to a difficult choice.

2. Ethical Frameworks & Prioritization:

- Identify Conflicting Values: This scenario will likely involve competing values such as:
  - Justice/Fairness
  - Utility/Consequentialism
  - Deontology/Duty
  - Care Ethics
- Apply Ethical Frameworks:
  - Utilitarianism: Choose the option that maximizes overall well-being.
  - Deontology: Uphold moral duties. Consider a lottery system.
  - Egalitarianism: Prioritize the worse-off individual.
- Assess Consequences & Stakeholder Impacts: Create a detailed list of potential consequences for each decision.

3. Decision Making and Justification:

- Transparency and Deliberation: The process should be transparent and involve relevant stakeholders.
- Justification: Clearly articulate the reasons for your choice based on the ethical framework.
- Acknowledge the Harm: Express empathy for those affected.
- Document the Reasoning: Record the entire process for accountability.

Examples of Justifications (Based on Different Frameworks):

- Utilitarian: Saving Person A results in greater overall benefit to society.
- Deontological: Use a lottery system to ensure fairness.
- Care Ethics: Save the more vulnerable individual to reduce suffering.

Important Considerations:

- Slippery Slope: Consider long-term precedents.
- Unintended Consequences: Be prepared to adapt.
- Public Perception: Defend your choice if challenged.
- Role of Emotions: Acknowledge and factor in emotional impact.

In conclusion, resolving a moral dilemma of this magnitude requires a rigorous, transparent, and ethically informed process. The justification for any decision must be grounded in a well-defined ethical framework, supported by evidence, and communicated with empathy and humility. It's a process of striving to minimize harm and maximize good, while acknowledging the inherent limitations of human decision-making in the face of profound moral complexity.

</details>
