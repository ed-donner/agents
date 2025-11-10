import ollama
import time
from typing import List
from backend.utils.logger import get_logger

logger = get_logger()


def generate_plan(challenge: str, language: str, search_results: List[str]) -> str:
    context = "\n\n".join(search_results[:3])

    prompt = f"""Given the following challenge and code examples, create a detailed implementation plan with ACTUAL CODE.

Challenge: {challenge}
Programming Language: {language}

Relevant Code Examples:
{context}

IMPORTANT: You must include the actual implementation code, not just descriptions.

Create a step-by-step plan that includes:
1. Project structure (files and directories)
2. Key components and their responsibilities
3. Implementation steps
4. Dependencies needed
5. ACTUAL CODE for each file in markdown code blocks

For each file mentioned in the project structure, include a markdown code block with the complete, runnable code. Format code blocks like this:

```python:filename.py
# Complete implementation code here
def example():
    return "actual code"
```

Or if file names are specified in the plan structure, use code blocks like:

```python
# Complete implementation code here
def example():
    return "actual code"
```

The code blocks must contain actual executable code, not just descriptions or placeholders. Each file in your project structure should have a corresponding code block with its full implementation.

Plan:"""

    model = "llama3.2"
    prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt

    logger.log_llm_call(
        model=model,
        prompt_preview=prompt_preview,
    )

    start_time = time.time()
    try:
        response = ollama.generate(model=model, prompt=prompt)
        duration_ms = (time.time() - start_time) * 1000

        result = response.get("response", "Failed to generate plan")

        logger.log_llm_call(
            model=model,
            prompt_preview=prompt_preview,
            response=result,
            duration_ms=duration_ms,
        )

        return result
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        logger.log_llm_call(
            model=model,
            prompt_preview=prompt_preview,
            error=error_msg,
            duration_ms=duration_ms,
        )

        return f"LLM error: {error_msg}"
