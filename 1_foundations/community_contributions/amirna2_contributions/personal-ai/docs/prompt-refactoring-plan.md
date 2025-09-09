# Prompt Management Refactoring Plan

## Overview
This document outlines the plan to refactor the prompt management system in the career_chatbot.py application. The goal is to improve maintainability, organization, and reusability by extracting prompts into separate files and creating a simple prompt loading system.

## Current State Analysis

### Existing Prompts
The application currently has several prompts embedded as f-strings within Python methods:

1. **Main Chat System Prompt** (`_create_system_prompt()` - line 889)
   - Instructions for AI assistant behavior
   - Critical instructions for contact handling
   - Job matching thresholds
   - Tool descriptions
   - Context injection (resume, LinkedIn, summary)

2. **Base System Prompt** (`_create_base_system_prompt()` - line 403)
   - Simplified version without evaluation context
   - Used for initial chat responses

3. **Evaluator System Prompt** (`_create_evaluator_prompt()` - line 293)
   - Instructions for response evaluation
   - Validation logic for tool usage
   - Behavioral rules verification
   - Context provided to evaluator

4. **Evaluator with GitHub Context** (`_create_evaluator_prompt_with_github()` - line 561)
   - Enhanced evaluator prompt
   - Includes GitHub tool results as valid context

5. **Chat Rerun Prompt** (inline in `rerun()` method - line 386)
   - Template for regenerating responses after evaluation failure
   - Includes feedback from failed evaluation

6. **Job Matching Prompt** (inline in `evaluate_job_match()` - line 742)
   - Detailed job analysis instructions
   - Skill assessment levels
   - Match level definitions
   - Contact facilitation thresholds

### Current Issues
- Prompts are scattered throughout the codebase
- Difficult to edit prompts without modifying Python code
- Variable substitution using f-strings is tightly coupled
- No clear separation between prompt logic and application logic
- Hard to track prompt changes in version control

## Proposed Solution

### 1. Directory Structure
```
personal-ai/
├── prompts/
│   ├── chat_init.md          # Main AI assistant system prompt
│   ├── chat_base.md          # Base system prompt without evaluation
│   ├── evaluator.md          # Evaluator system prompt
│   ├── evaluator_github.md   # Evaluator prompt with GitHub context
│   ├── chat_rerun.md         # Rerun prompt for failed evaluations
│   └── job_match.md          # Job matching analysis prompt
├── promptkit.py              # Prompt loading and rendering module
└── career_chatbot.py         # Updated to use promptkit
```

### 2. PromptKit Module Implementation

```python
from pathlib import Path
import re

_pat = re.compile(r"\{([a-zA-Z0-9_\.]+)\}")

def _get(ctx, path):
    """Navigate nested objects/dicts to retrieve values"""
    cur = ctx
    for p in path.split("."):
        cur = cur[p] if isinstance(cur, dict) else getattr(cur, p)
    return cur

def render(path, vars):
    """Load and render a prompt template with variable substitution"""
    txt = Path(path).read_text(encoding="utf-8")
    return _pat.sub(lambda m: str(_get(vars, m.group(1))), txt)
```

### 3. Prompt File Format

Each prompt will be a markdown file with variable placeholders using `{variable_name}` syntax.

Example: `prompts/chat_init.md`
```markdown
You are an AI assistant designed by {config.name} and representing them, helping visitors learn about their professional background.
Your knowledge comes from {config.name}'s resume, LinkedIn profile, and professional summary provided below.
Your knowledge can also be augmented with real-time data from GitHub if needed and/or when appropriate.

CRITICAL INSTRUCTIONS:
1. ALWAYS search through ALL the provided context (Summary, LinkedIn, Resume) before claiming you don't have information. Be precise and thorough.
2. CONTACT IS A TWO-STEP PROCESS:
   a. First, OFFER to facilitate contact for i) professional questions you can't fully answer, or ii) job matches rated '{config.job_match_threshold}' or better. Your response should just be text making the offer.
   b. Second, WAIT for the user to provide their email. ONLY THEN should you use the `record_user_details` tool. Never invent an email.
...

## CONTEXT:

### Summary:
{context.summary}

### LinkedIn Profile:
{context.linkedin}

### Resume:
{context.resume}
```

### 4. Integration Changes

Update methods in `career_chatbot.py`:

```python
from promptkit import render

class ChatAgent:
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI assistant"""
        vars = {
            'config': self.config,
            'context': self.context
        }
        base_prompt = render('prompts/chat_init.md', vars)

        # Add conditional tools section if web_search_service exists
        if self.web_search_service:
            tools_section = render('prompts/tools_github.md', vars)
            base_prompt += "\n" + tools_section

        return base_prompt
```

### 5. Variable Mapping

Variables to be passed to prompt templates:

- **config**: ChatbotConfig object
  - `config.name`
  - `config.job_match_threshold`
  - `config.evaluator_model`
  - etc.

- **context**: Dictionary with document content
  - `context.summary`
  - `context.linkedin`
  - `context.resume`

- **Dynamic variables**: For specific prompts
  - `role_title` (job matching)
  - `job_description` (job matching)
  - `feedback` (rerun prompt)
  - `github_context` (evaluator with GitHub)
  - `evaluation_criteria` (evaluator prompts)

### 6. Migration Steps

1. **Phase 1: Setup**
   - Create `prompts/` directory
   - Implement `promptkit.py` module
   - Add unit tests for promptkit

2. **Phase 2: Extract Prompts**
   - Extract each prompt to its corresponding .md file
   - Preserve all existing formatting and variables
   - Test each extraction individually

3. **Phase 3: Update Code**
   - Modify each `_create_*_prompt()` method to use promptkit
   - Update inline prompts to use promptkit
   - Ensure backward compatibility

4. **Phase 4: Testing**
   - Run existing tests
   - Manual testing of all chat flows
   - Verify prompt rendering with various inputs

5. **Phase 5: Documentation**
   - Update README with prompt management section
   - Document variable naming conventions
   - Add examples of prompt customization

## Benefits

1. **Separation of Concerns**: Prompts are separate from code logic
2. **Easier Maintenance**: Edit prompts without touching Python code
3. **Better Version Control**: Clear diffs for prompt changes
4. **Reusability**: Promptkit can be used for future prompt needs
5. **Consistency**: Unified approach to variable substitution
6. **Flexibility**: Easy to add new prompts or modify existing ones
7. **Testing**: Prompts can be tested independently

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Comprehensive testing, gradual migration |
| Variable naming conflicts | Clear documentation, naming conventions |
| Performance impact | Minimal - file reads are cached, regex is efficient |
| Complex nested variables | Enhanced _get() function handles nested access |

## Future Enhancements

1. **Prompt Versioning**: Support for multiple prompt versions
2. **Prompt Validation**: Schema validation for required variables
3. **Prompt Inheritance**: Base prompts that others can extend
4. **Dynamic Loading**: Hot-reload prompts without restart
5. **Prompt Library**: Shared prompts across multiple agents
6. **Localization**: Support for multi-language prompts

## Implementation Timeline

- **Step 1**: Create promptkit module and tests
- **Step 2**: Extract and migrate prompts
- **Step 3**: Update career_chatbot.py integration
- **Step 4**: Testing and documentation
- **Step 5**: Review and refinements

## Success Criteria

- [ ] All existing functionality preserved
- [ ] All tests pass
- [ ] Prompts are in separate .md files
- [ ] Promptkit successfully renders all prompts
- [ ] Documentation is complete
- [ ] Code is cleaner and more maintainable
