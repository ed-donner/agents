from typing import Dict, Any

class DiagnosisTemplates:
    @staticmethod
    def current_state_header(unittest_count: int, target_unittest: int) -> str:
        return f"""=== CURRENT STATE ===
test.py: {unittest_count} test methods (MINIMUM REQUIRED: {target_unittest})

NOTE: This is a MINIMUM count. You can have more than {target_unittest} tests if needed.
"""

    @staticmethod
    def action_items_header() -> str:
        return """=== ACTION ITEMS (DO THESE IN ORDER) ==="""

    @staticmethod
    def failing_tests_warning(action_num: int) -> str:
        return f"""
{'=' * 60}
⚠️  CRITICAL: TESTS ARE FAILING - LOGIC ERRORS IN main.py!
{'=' * 60}

{action_num}. THE MAIN PROBLEM: Your logic in main.py is WRONG!
   Tests are FAILING because the code doesn't work correctly.

   WHAT YOU MUST DO:
   1. READ the validation report above carefully
   2. UNDERSTAND why tests are failing (logic errors, wrong algorithm, etc.)
   3. FIX the logic in main.py to make tests pass
   4. Update test.py if needed to add more comprehensive tests

   DO NOT just add more tests! Fix the broken logic first!
"""

    @staticmethod
    def remember_checklist() -> str:
        return """
REMEMBER: After writing files, verify:
- main.py has CORRECT logic that makes all tests pass
- test.py has MINIMUM 2 test methods
- test.py MUST import from main.py: 'from main import <function_or_class>'
- main.py MUST define the function/class that test.py imports
- All tests in test.py should pass when run with pytest or unittest

CRITICAL: You MUST use the write_file TOOL to create/update files.
   DO NOT just describe files in text - you MUST make tool calls.
   Text-only responses will cause the system to fail.
"""


class BuilderTemplates:
    @staticmethod
    def force_fix_message(iteration: int, test_count: int, target_unittest: int = 2) -> str:
        return f"""
{'=' * 80}
CRITICAL: VALIDATION FAILED - YOU MUST FIX FILES WITH TOOLS
{'=' * 80}

CURRENT STATE (WHAT YOU WROTE BEFORE - THIS IS WRONG):
  - test.py: {test_count} test methods (MUST BE AT LEAST {target_unittest})

YOU KEEP WRITING THE SAME THING! IT'S STILL WRONG AFTER {iteration} ITERATIONS!

WHAT YOU MUST DO NOW (DO NOT REPEAT THE SAME MISTAKE):
1. IF test.py has less than {target_unittest} test methods → ADD MORE TEST METHODS until it has AT LEAST {target_unittest}
2. IF tests are failing → FIX the logic in main.py to make tests pass

YOU CANNOT just describe fixes in text. YOU MUST:
1. Call the write_file tool for EACH file that needs fixing
2. Actually write the CORRECTED content
3. Fix ALL issues identified in the diagnosis above

TEXT-ONLY RESPONSES ARE COMPLETELY UNACCEPTABLE. YOU MUST CALL write_file TOOLS.

Example: If test.py currently has 10 test methods but needs {target_unittest}, you must write a NEW test.py with {target_unittest} test methods!

You MUST make tool calls to fix the broken files. No exceptions.
"""


class StatusTemplates:
    @staticmethod
    def max_steps_reached(validation_passed: bool, reviewer_passed: bool) -> str:
        return f"Maximum steps reached - Validation: {'PASSED' if validation_passed else 'FAILED'}, Reviewer: {'APPROVED' if reviewer_passed else 'REJECTED'}"

    @staticmethod
    def success() -> str:
        return "🎉 SUCCESS! All files generated, validated, and approved!"

    @staticmethod
    def iteration_limit_reached(max_iterations: int, validation_passed: bool, reviewer_passed: bool) -> str:
        return f"Iteration limit reached ({max_iterations}) - Validation: {'PASSED' if validation_passed else 'FAILED'}, Reviewer: {'APPROVED' if reviewer_passed else 'REJECTED'}"


class NotificationTemplates:
    @staticmethod
    def success(iteration: int) -> str:
        return f"""🎉 Sidekick Agent: SUCCESS!

Task completed in {iteration} iterations
✅ Validation: PASSED
✅ Reviewer: APPROVED

All files generated, validated, and approved!"""

    @staticmethod
    def max_steps_reached(iteration: int, validation_passed: bool, reviewer_passed: bool) -> str:
        val_status = '✅ PASSED' if validation_passed else '❌ FAILED'
        rev_status = '✅ APPROVED' if reviewer_passed else '❌ REJECTED'
        return f"""⚠️ Sidekick Agent: Maximum steps reached

Iterations: {iteration}
Validation: {val_status}
Reviewer: {rev_status}

Stopped to prevent infinite loop."""

    @staticmethod
    def iteration_limit_reached(max_iterations: int, validation_passed: bool, reviewer_passed: bool) -> str:
        val_status = '✅ PASSED' if validation_passed else '❌ FAILED'
        rev_status = '✅ APPROVED' if reviewer_passed else '❌ REJECTED'
        return f"""⚠️ Sidekick Agent: Iteration limit reached

Completed {max_iterations} iterations
Validation: {val_status}
Reviewer: {rev_status}

Force stopped to prevent infinite loop."""


class RouterTemplates:
    @staticmethod
    def tools_router_decision(iteration: int, validation_passed: bool, reviewer_passed: bool,
                             all_files_exist: bool, decision: str, reason: str) -> str:
        return f"""
{'=' * 80}
TOOLS_ROUTER [Iteration {iteration}]
   validation_passed={validation_passed}, reviewer_passed={reviewer_passed}
   all_files_exist={all_files_exist}
   DECISION: {decision}
   {reason}
{'=' * 80}
"""

    @staticmethod
    def validator_router_decision(iteration: int, validation_passed: bool, decision: str) -> str:
        status = "✅" if validation_passed else "❌"
        action = "PASSED → routing to REVIEW" if validation_passed else "FAILED → routing to DIAGNOSE"
        return f"""
{'=' * 80}
🔀 VALIDATOR_ROUTER [Iteration {iteration}]
   validation_passed={validation_passed}
   {status} DECISION: Validation {action}
{'=' * 80}
"""

    @staticmethod
    def review_router_decision(iteration: int, validation_passed: bool, reviewer_passed: bool,
                              decision: str, reason: str = "") -> str:
        message = f"""
{'=' * 80}
🔀 REVIEW_ROUTER [Iteration {iteration}]
   validation_passed={validation_passed}, reviewer_passed={reviewer_passed}
   DECISION: {decision}
"""
        if reason:
            message += f"   REASON: {reason}\n"
        message += f"{'=' * 80}\n"
        return message


class NodeHeaderTemplates:
    @staticmethod
    def builder(iteration: int) -> str:
        return f"""
{'=' * 60}
BUILDER: Starting build phase (iteration {iteration})...
{'=' * 60}"""

    @staticmethod
    def validator() -> str:
        return f"""
{'=' * 60}
✅ VALIDATOR: Starting validation phase...
{'=' * 60}"""

    @staticmethod
    def diagnose(iteration: int) -> str:
        return f"""
{'=' * 80}
DIAGNOSE NODE [Iteration {iteration}]
   Validation failed - analyzing errors and preparing fix instructions...
{'=' * 80}"""

    @staticmethod
    def reviewer(iteration: int) -> str:
        return f"""
{'=' * 60}
REVIEWER: Starting review phase (iteration {iteration})...
{'=' * 60}"""


class SystemPromptTemplates:
    @staticmethod
    def reviewer_rejected_section(reviewer_feedback: str) -> str:
        return f"""
{'=' * 80}
REVIEWER REJECTED - MUST FIX ALL ISSUES BELOW
{'=' * 80}
The reviewer has REJECTED the current implementation. You MUST address ALL issues listed below:

{reviewer_feedback}
{'=' * 80}
"""

    @staticmethod
    def validation_failed_section(diagnosis: str) -> str:
        return f"""
{'=' * 80}
CRITICAL DIAGNOSIS - READ THIS FIRST AND FIX ALL ISSUES
{'=' * 80}
Validation FAILED. The diagnosis below identifies specific issues that MUST be fixed:

{diagnosis}
{'=' * 80}
"""

    @staticmethod
    def critical_requirements() -> str:
        return """CRITICAL REQUIREMENTS (MUST FOLLOW):
1. test.py: MUST have MINIMUM 2 test methods
2. test.py: MUST import from main.py (e.g., "from main import <function_or_class>")
3. main.py: MUST define the function/class that test.py imports
4. All tests must pass when run with unittest/pytest
5. Code must satisfy ALL requirements from the user prompt"""

    @staticmethod
    def main_py_guidelines() -> str:
        return """=== FILE 1: main.py (IMPLEMENTATION) ===
- Implement the full, correct solution for the prompt's entry function
- Use ONLY Python standard library imports
- Implement exactly the function signature defined in the prompt
- No global mutable state; keep logic inside functions/classes
- Deterministic behavior only: no randomness, time-based logic, or I/O
- Match the specified input/output formats and edge-case rules
- Keep names, structure, and constraints aligned with the prompt text
- Pass ALL tests in test.py deterministically
- Put hard variables/constraints (ranges, max values, default id, etc.) at top level in CAPITAL CASE"""

    @staticmethod
    def test_py_guidelines() -> str:
        return """=== FILE 2: test.py (TESTS) ===
CRITICAL: MUST have MINIMUM 2 test methods (test_1 through test_2 at minimum)
- MUST import from main.py: "from main import <function_or_class_name>"
- Test ONLY the main entry function from the prompt
- Use Python's unittest module (class inheriting from unittest.TestCase)
- Each test method must be named test_XXX and call the entry function
- MINIMUM: 2 test methods covering various scenarios
- Use assertEqual (or similar exact checks) on the returned value
- Cover normal cases, edge cases, and error/guard behavior described in prompt
- Do NOT test behavior that is not mentioned in the prompt
- Keep tests deterministic: no random, no network, no time-based checks
- DO NOT put any processing or pre-processing logic in the test file
- Example: Write test_1 through test_15 (minimum) covering different input scenarios"""

    @staticmethod
    def file_writing_rules(absolute_workspace: str, ready_token: str) -> str:
        return f"""CRITICAL FILE WRITING RULES - READ CAREFULLY
- FIXED WORKSPACE PATH: {absolute_workspace}
- ALL files MUST be written to this EXACT path (no subdirectories, no variations)
- You MUST use the write_file tool (available in your toolset) to create files
- You CANNOT just describe files in text - you MUST make tool calls
- If you respond with only text and no tool calls, the system will FAIL
- File names must be EXACTLY: main.py, test.py
- Write BOTH files using write_file tool calls directly to: {absolute_workspace}
- The write_file tool is scoped to {absolute_workspace}, so use file_path="main.py" (not full path)
- After writing both files and verifying they exist, end your response with the token {ready_token} on its own line
- DO NOT just describe files - you MUST actually call write_file tool for each file
- Example: Call write_file with file_path="test.py" and content="[actual file content]"
- If files are missing, you MUST call write_file tool. Text-only responses are INVALID.
- DO NOT call any validator tools - validation is done automatically by the system after you write files
- Your job is ONLY to write/update files using write_file tool"""

    @staticmethod
    def build_full_system_prompt(absolute_workspace: str, workspace_path: str, existing_files_str: str,
                                 previous_messages_summary: str, prominent_feedback: str,
                                 user_prompt: str, task_plan: str, validation_feedback: str,
                                 reviewer_feedback: str, context: str, ready_token: str) -> str:
        return f"""You are an autonomous coding agent working in a FIXED directory.

FIXED WORKSPACE PATH (USE THIS EXACT PATH)
{absolute_workspace}

All files MUST be created in this exact directory. This is the ONLY location where files should be written.

Current files in workspace: {existing_files_str}
{previous_messages_summary}

{prominent_feedback}

{'=' * 80}
ORIGINAL USER PROMPT (COMPLETE - READ EVERY DETAIL CAREFULLY)
{'=' * 80}
{user_prompt}
{'=' * 80}

CRITICAL: The prompt above contains ALL requirements and specifications.
Every single detail, constraint, edge case, and behavior mentioned is MANDATORY.
You MUST implement EXACTLY what the prompt specifies - nothing more, nothing less.
If the prompt mentions specific:
- Function names -> use those EXACT names
- Parameter types -> use those EXACT types
- Return formats -> return in that EXACT format
- Edge cases -> handle those EXACT cases
- Constraints (ranges, limits, validations) -> apply them EXACTLY
- Error handling -> implement as specified EXACTLY

{SystemPromptTemplates.critical_requirements()}

CRITICAL: You MUST use the file management tools to write files. The workspace directory is: {workspace_path}

Using the file tools (write_file), create or update ONLY these files in the workspace root ({workspace_path}):

{SystemPromptTemplates.main_py_guidelines()}

{SystemPromptTemplates.test_py_guidelines()}

{SystemPromptTemplates.file_writing_rules(absolute_workspace, ready_token)}

Task plan:
{task_plan}

{'=' * 80}
VALIDATION REPORT (for reference - see diagnosis above if validation failed or have warnings):
{'=' * 80}
{validation_feedback}
{'=' * 80}

Reviewer feedback (for reference - see prominent section above if reviewer rejected):
{reviewer_feedback}

RAG CONTEXT (CRITICAL - Follow these instructions exactly):
{context}
"""
