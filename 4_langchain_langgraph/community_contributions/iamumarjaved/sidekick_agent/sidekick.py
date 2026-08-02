import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
try:
    from langsmith.callbacks import LangSmithTracer
except ImportError:
    LangSmithTracer = None
try:
    from .core.retriever import GuidelineRetriever
    from .core.state import (
        BuildState,
        MAX_ITERATIONS as DEFAULT_MAX_ITERATIONS,
        MAX_STEPS as DEFAULT_MAX_STEPS,
        READY_TOKEN as DEFAULT_READY_TOKEN,
        ReviewDecision,
    )
    from .core.templates import (
        DiagnosisTemplates,
        BuilderTemplates,
        StatusTemplates,
        NotificationTemplates,
        RouterTemplates,
        NodeHeaderTemplates,
        SystemPromptTemplates,
    )
    from .sidekick_tools import other_tools, playwright_tools
except ImportError:
    current_file = Path(__file__).resolve()
    langgraph_dir = current_file.parent.parent.parent.parent
    if str(langgraph_dir) not in sys.path:
        sys.path.insert(0, str(langgraph_dir))
    from community_contributions.iamumarjaved.sidekick_agent.core.retriever import GuidelineRetriever
    from community_contributions.iamumarjaved.sidekick_agent.core.state import (
        BuildState,
        MAX_ITERATIONS as DEFAULT_MAX_ITERATIONS,
        MAX_STEPS as DEFAULT_MAX_STEPS,
        READY_TOKEN as DEFAULT_READY_TOKEN,
        ReviewDecision,
    )
    from community_contributions.iamumarjaved.sidekick_agent.core.templates import (
        DiagnosisTemplates,
        BuilderTemplates,
        StatusTemplates,
        NotificationTemplates,
        RouterTemplates,
        NodeHeaderTemplates,
        SystemPromptTemplates,
    )
    from community_contributions.iamumarjaved.sidekick_agent.sidekick_tools import other_tools, playwright_tools


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR.parent / "data"
GUIDELINE_DOC = DATA_DIR / "Trainer Guidelines.docx"
IDEAL_CODE_INSTRUCTIONS = DATA_DIR / "ideal_code_instructions.txt"
TEST_INSTRUCTIONS = DATA_DIR / "test_instructions.txt"
TASKS_ROOT = PROJECT_DIR / "tasks"
FIXED_WORKSPACE = TASKS_ROOT


load_dotenv(override=True)




class Sidekick:
    
    READY_TOKEN = DEFAULT_READY_TOKEN
    MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
    MAX_STEPS = DEFAULT_MAX_STEPS
    
    def __init__(self):
        self.generator_llm_with_tools = None
        self.planner_llm = None
        self.reviewer_llm = None
        self.review_llm_structured = None
        self.tools: List[Any] = []
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None
        self.retriever = None
        self._rag_init_task = None
        self.langsmith_tracer = self._build_langsmith_tracer()
        self.last_workspace = None
        self.last_thread_id = None
    async def setup(self):
        print("Setting up tools...")
        try:
            self.tools, self.browser, self.playwright = await playwright_tools()
            self.tools += await other_tools()
            print("Tools initialized")
        except Exception as e:
            print(f"WARNING: Tool setup had issues: {e}")
            self.tools = []
            self.tools += await other_tools()
        print("Setting up LLMs...")
        
        try:
            builder_model = os.getenv("SIDEKICK_BUILDER_MODEL", "gpt-5")
            planner_model = os.getenv("SIDEKICK_PLANNER_MODEL", "gpt-5")
            reviewer_model = os.getenv("SIDEKICK_REVIEWER_MODEL", "gpt-5")
            generator_llm = ChatOpenAI(model=builder_model, temperature=0)
            self.generator_llm_with_tools = generator_llm.bind_tools(self.tools)
            self.planner_llm = ChatOpenAI(model=planner_model, temperature=0)
            reviewer_llm = ChatOpenAI(model=reviewer_model, temperature=0)
            self.reviewer_llm = reviewer_llm
            self.review_llm_structured = reviewer_llm.with_structured_output(ReviewDecision)
            print("LLMs initialized")
        except Exception as e:
            print(f"ERROR: Error setting up LLMs: {e}")
            raise
        print("Building graph...")
        await self._build_graph()
        print("Graph built")

        print("Starting RAG retriever initialization in background...")
        import asyncio
        self._rag_init_task = asyncio.create_task(self._initialize_rag_background())

        print("Setup completed! (RAG initializing in background...)")
    async def _initialize_rag_background(self):
        """Initialize RAG retriever in background without blocking."""
        try:
            print("Background: Starting RAG retriever initialization...")
            import asyncio
            loop = asyncio.get_event_loop()
            
            self.retriever = await asyncio.wait_for(
                loop.run_in_executor(None, self._build_retriever),
                timeout=120.0
            )
            print("Background: RAG retriever initialized successfully!")
        except asyncio.TimeoutError:
            print("WARNING: Background: RAG retriever initialization timed out (taking too long)")
            print("   The system will continue with fallback context loading.")
            self.retriever = None
        except Exception as e:
            print(f"WARNING: Background: Failed to initialize RAG retriever: {e}")
            print("   The system will continue with fallback context loading.")
            import traceback
            print(traceback.format_exc())
            self.retriever = None

    async def _update_tools_for_workspace(self, workspace_dir: str):
        """Update file tools to use the current workspace directory."""
        playwright_tools_list, _, _ = await playwright_tools()

        workspace_tools = await other_tools(workspace_dir)

        self.tools = playwright_tools_list + workspace_tools
        
        generator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.generator_llm_with_tools = generator_llm.bind_tools(self.tools)
        
        await self._build_graph()

    def _build_langsmith_tracer(self) -> Optional[Any]:
        if LangSmithTracer is None:
            return None
        project = os.getenv("LANGCHAIN_PROJECT", "IAMUmar-Sidekick")
        try:
            return LangSmithTracer(project_name=project)
        except Exception:
            return None

    def _read_docx(self, path: Path) -> str:
        if not path.exists():
            return ""
        try:
            with zipfile.ZipFile(path) as archive:
                xml_bytes = archive.read("word/document.xml")
            tree = ET.fromstring(xml_bytes)
            namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texts = [node.text or "" for node in tree.iterfind(".//w:t", namespace)]
            return "".join(texts)
        except Exception as exc:
            return f"Document could not be read: {exc}"

    def _build_retriever(self) -> GuidelineRetriever:
        sources: Dict[str, str] = {}
        
        if GUIDELINE_DOC.exists():
            sources["Trainer Guidelines (DOCX)"] = self._read_docx(GUIDELINE_DOC)
        
        guideline_txt = DATA_DIR / "Trainer Guidelines.txt"
        if guideline_txt.exists():
            sources["Trainer Guidelines (TXT)"] = guideline_txt.read_text(encoding="utf-8")

        if IDEAL_CODE_INSTRUCTIONS.exists():
            sources["Ideal Code Instructions (main.py)"] = IDEAL_CODE_INSTRUCTIONS.read_text(encoding="utf-8")

        if TEST_INSTRUCTIONS.exists():
            sources["Test Instructions (test.py)"] = TEST_INSTRUCTIONS.read_text(encoding="utf-8")

        os.environ.setdefault("SIDEKICK_CHROMA_DB", str(DATA_DIR / "chroma_db"))

        return GuidelineRetriever(sources)

    async def _gather_context(self, prompt: str, supplemental: Iterable[str] = (), file_types: Optional[List[str]] = None) -> str:
        """
        Gather RAG context with optional file type filtering.
        
        Args:
            prompt: The user prompt
            supplemental: Additional context (validation feedback, reviewer feedback, etc.)
            file_types: List of file types to focus on (e.g., ['main.py', 'test.py'])
        """
        if self.retriever is None and hasattr(self, '_rag_init_task') and self._rag_init_task is not None:
            try:
                import asyncio
                if not self._rag_init_task.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(self._rag_init_task), timeout=1.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                else:
                    try:
                        await self._rag_init_task
                    except Exception:
                        pass
            except (asyncio.CancelledError, AttributeError, RuntimeError):
                pass
        
        if self.retriever is None:
            print("WARNING: RAG not available, using fallback (direct file loading)")
            fallback_context = []
            try:
                if IDEAL_CODE_INSTRUCTIONS.exists():
                    fallback_context.append(f"=== Ideal Code Instructions ===\n{IDEAL_CODE_INSTRUCTIONS.read_text(encoding='utf-8')}")
                if TEST_INSTRUCTIONS.exists():
                    fallback_context.append(f"=== Test Instructions ===\n{TEST_INSTRUCTIONS.read_text(encoding='utf-8')}")
                
                if fallback_context:
                    print(f"Loaded {len(fallback_context)} instruction files as fallback")
                    return "\n\n".join(fallback_context)
            except Exception as e:
                print(f"WARNING: Could not load instruction files as fallback: {e}")
            
            return "Warning: RAG retriever not available. Using basic instruction context."
        
        query_parts = [prompt]
        query_parts.extend(supplemental)
        
        if file_types:
            file_type_hint = f"Focus on instructions for: {', '.join(file_types)}"
            query_parts.append(file_type_hint)
        
        query = "\n".join(query_parts)
        try:
            print("Querying RAG retriever (semantic search + reranking)...")
            retrieved = self.retriever.query(query, k=20, rerank_k=10)
            print(f"Retrieved {len(retrieved)} relevant chunks from RAG")
        except Exception as e:
            print(f"ERROR: Error querying retriever: {e}")
            return f"Error retrieving context: {e}"
        
        sections = []
        for idx, snippet in enumerate(retrieved):
            source_label = f"Relevant instruction {idx + 1}"
            sections.append(f"{source_label}:\n{snippet}")
        
        if not sections:
            print("WARNING: No relevant context retrieved from RAG")
            return "No relevant context retrieved. Please ensure instruction files are loaded correctly."
        
        return "\n\n".join(sections)

    async def _planner(self, state: BuildState) -> Dict[str, Any]:
        try:
            from .shared_state import update_status
            update_status("Starting planning phase", state.get("iteration", 0), "plan")
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                update_status("Starting planning phase", state.get("iteration", 0), "plan")
            except ImportError:
                pass

        print("\n" + "="*60)
        print("PLANNER: Starting planning phase...")
        print("="*60)
        file_types = ["main.py", "test.py"]
        print(f"Gathering RAG context for file types: {', '.join(file_types)}")
        context = await self._gather_context(state["user_prompt"], file_types=file_types)
        print(f"Context gathered ({len(context)} chars)")
        system_message = """You are a senior prompt architect planning a code generation task.

Your goal: Extract and organize EVERY SINGLE DETAIL from the user prompt into a comprehensive plan.
Missing even one detail will cause validation failures and require costly iterations.

Create a detailed plan covering:

1. EXACT FUNCTION SIGNATURE
   - Function name (EXACT spelling)
   - Parameter names (EXACT spelling)
   - Parameter types (EXACT types: str, dict, int, List, etc.)
   - Return type (EXACT type)
   - All parameters (required + optional with defaults)

2. INPUT/OUTPUT SPECIFICATIONS
   - Input format (dict structure, JSON format, etc.)
   - Output format (dict structure, success/error responses)
   - Error codes and error messages (EXACT strings)
   - Field names in input/output (EXACT spelling)

3. FUNCTIONAL REQUIREMENTS
   - Core algorithm or logic required
   - Data structures needed (Union-Find, graph, tree, etc.)
   - Processing steps in order
   - Any state management needed

4. CONSTRAINTS & VALIDATIONS
   - Size limits (min/max values, array lengths)
   - Type validations (what must be checked)
   - Range constraints (0-100, 1-1000000, etc.)
   - Required fields in input
   - Format validations

5. EDGE CASES & ERROR HANDLING
   - Invalid input scenarios
   - Boundary conditions
   - Empty/null cases
   - Error response format for each error type
   - Error codes for each validation failure

6. TESTING STRATEGY
   - Test coverage: What scenarios to cover (at least 2 test methods)
   - Normal cases, edge cases, error cases
   - Test data examples

7. FILE-SPECIFIC NOTES
   - main.py: Full implementation with all logic
   - test.py: MUST have at least 2 test methods (test_1 through test_2 minimum)

Output: Comprehensive bullet-point plan that captures EVERY detail so the builder can implement it correctly in ONE iteration."""

        human_message = f"""COMPLETE USER PROMPT (Extract ALL details):
{state['user_prompt']}

Retrieved guidelines and instructions:
{context}

TASK: Create a detailed plan that extracts EVERY requirement, constraint, edge case, and specification from the prompt above.
"""

        print("Calling planner LLM...")
        plan_response = self.planner_llm.invoke(
            [SystemMessage(content=system_message), HumanMessage(content=human_message)]
        )
        print(f"Plan generated ({len(plan_response.content)} chars)")

        try:
            from .shared_state import update_plan_output
            update_plan_output(plan_response.content)
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_plan_output
                update_plan_output(plan_response.content)
            except ImportError:
                pass

        print("="*60 + "\n")

        return {
            "messages": [AIMessage(content=f"Planning summary:\n{plan_response.content}")],
            "task_plan": plan_response.content,
            "rag_context": context,
            "iteration": state.get("iteration", 0),
            "step_count": state.get("step_count", 0) + 1,
        }


    async def _build_generation_system_prompt(self, state: BuildState) -> str:
        supplemental_queries = [
            state.get("validation_report") or "",
            state.get("reviewer_feedback") or "",
            state.get("task_plan") or "",
        ]
        file_types = ["main.py", "test.py"]
        context = await self._gather_context(
            state["user_prompt"],
            supplemental_queries,
            file_types=file_types
        )
        
        validation_feedback = state.get("validation_report") or "(no validator feedback yet)"
        reviewer_feedback = state.get("reviewer_feedback") or "(no reviewer feedback yet)"
        workspace_path = Path(state['workspace_dir']).resolve()
        
        existing_files = []
        if workspace_path.exists():
            for f in workspace_path.iterdir():
                if f.is_file():
                    existing_files.append(f.name)
        existing_files_str = ", ".join(existing_files) if existing_files else "none"
        
        previous_messages_summary = ""
        if state.get("messages"):
            message_count = len(state["messages"])
            previous_messages_summary = f"\nPrevious conversation: {message_count} messages in history. Review all previous feedback and corrections."
        
        diagnosis = state.get('diagnosis') or 'No diagnosis available yet.'
        reviewer_passed = state.get("reviewer_passed", None)
        validation_passed = state.get("validation_passed", None)
        formatting_errors = state.get("formatting_errors") or []
        formatting_warnings = state.get("formatting_warnings") or []
        
        absolute_workspace = str(workspace_path.resolve())
        
        feedback_sections = []
        
        if reviewer_passed is False and reviewer_feedback and reviewer_feedback != "(no reviewer feedback yet)":
            feedback_sections.append(SystemPromptTemplates.reviewer_rejected_section(reviewer_feedback))

        if validation_passed is False and diagnosis and diagnosis != 'No diagnosis available yet.':
            feedback_sections.append(SystemPromptTemplates.validation_failed_section(diagnosis))

        prominent_feedback = "\n".join(feedback_sections) if feedback_sections else ""

        return SystemPromptTemplates.build_full_system_prompt(
            absolute_workspace=absolute_workspace,
            workspace_path=workspace_path,
            existing_files_str=existing_files_str,
            previous_messages_summary=previous_messages_summary,
            prominent_feedback=prominent_feedback,
            user_prompt=state['user_prompt'],
            task_plan=state.get('task_plan') or '(plan missing)',
            validation_feedback=validation_feedback,
            reviewer_feedback=reviewer_feedback,
            context=context,
            ready_token=self.READY_TOKEN
        )

    def _parse_pytest_failures(self, validation_report: str) -> Dict[str, Any]:
        """Parse unittest output to extract structured failure information."""
        import re

        failed_tests = []
        assertion_errors = []

        # Extract failed test names from unittest: "test_something (__main__.TestClass) ... FAIL"
        # or "FAIL: test_something"
        failed_pattern_1 = r'(test_\w+)\s+\([^)]+\)\s+\.\.\.\s+FAIL'
        failed_pattern_2 = r'FAIL:\s+(test_\w+)'
        failed_pattern_3 = r'ERROR:\s+(test_\w+)'

        failed_matches = re.findall(failed_pattern_1, validation_report)
        failed_tests.extend(failed_matches)
        failed_matches = re.findall(failed_pattern_2, validation_report)
        failed_tests.extend(failed_matches)
        failed_matches = re.findall(failed_pattern_3, validation_report)
        failed_tests.extend(failed_matches)

        # Remove duplicates while preserving order
        seen = set()
        failed_tests = [x for x in failed_tests if not (x in seen or seen.add(x))]

        # Extract assertion errors
        assertion_pattern = r'AssertionError:([^\n]+)'
        assertion_matches = re.findall(assertion_pattern, validation_report)
        assertion_errors.extend([err.strip() for err in assertion_matches])

        # Extract error messages (common pattern: "self.assertEqual(X, Y) failed")
        error_pattern = r'self\.assert\w+\([^)]+\)[^\n]*'
        error_matches = re.findall(error_pattern, validation_report)
        if error_matches:
            assertion_errors.extend([err.strip() for err in error_matches[:5]])

        # Extract failure section (usually after dashed lines in unittest)
        failures_section = ""
        if "FAIL:" in validation_report or "ERROR:" in validation_report:
            # Get first 2000 chars after first FAIL/ERROR
            fail_idx = validation_report.find("FAIL:")
            error_idx = validation_report.find("ERROR:")
            start_idx = min(x for x in [fail_idx, error_idx] if x != -1) if (fail_idx != -1 or error_idx != -1) else -1
            if start_idx != -1:
                failures_section = validation_report[start_idx:start_idx + 2000]

        summary = f"Found {len(failed_tests)} failed/error tests"
        if assertion_errors:
            summary += f" with {len(assertion_errors)} assertion errors"

        return {
            "failed_test_names": failed_tests[:10],  # First 10
            "assertion_errors": assertion_errors[:10],  # First 10
            "failures_section": failures_section,
            "summary": summary
        }

    async def _diagnose_issues(self, state: BuildState) -> Dict[str, Any]:
        """Diagnose validation errors by analyzing test.py and main.py."""
        try:
            from .shared_state import update_status
            update_status("Diagnosing validation errors", state.get("iteration", 0), "diagnose")
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                update_status("Diagnosing validation errors", state.get("iteration", 0), "diagnose")
            except ImportError:
                pass

        print(f"\n{NodeHeaderTemplates.diagnose(state.get('iteration', 0))}")

        validation_report = state.get("validation_report", "")
        workspace = Path(state["workspace_dir"]).resolve()
        
        # Read files
        file_contents = {}
        for filename in ["main.py", "test.py"]:
            file_path = workspace / filename
            if file_path.exists():
                try:
                    file_contents[filename] = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    print(f"ERROR: Could not read {filename}: {e}")
        
        # Count test methods
        unittest_count = 0
        if "test.py" in file_contents:
            import re
            unittest_count = len(re.findall(r'def\s+test_\w+', file_contents["test.py"]))
        
        target_unittest = 2

        # Initialize error counters (persistent across iterations)
        count_fix_attempts = state.get("count_fix_attempts", 0)

        # Build diagnosis
        diagnosis_parts = []
        error_type = None
        
        # Check if files exist
        files_exist = {"main.py": (workspace / "main.py").exists(), "test.py": (workspace / "test.py").exists()}
        
        if not files_exist["main.py"] or not files_exist["test.py"]:
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("🔴 MISSING FILES")
            diagnosis_parts.append("=" * 80)
            missing = [f for f, exists in files_exist.items() if not exists]
            diagnosis_parts.append(f"Missing files: {', '.join(missing)}")
            diagnosis_parts.append("ACTION: Create ALL required files (main.py and test.py)")
            error_type = "missing_files"
        
        # Check test count
        elif unittest_count < target_unittest:
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("📊 INSUFFICIENT TEST COUNT")
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append(f"Current: {unittest_count} test methods")
            diagnosis_parts.append(f"Required: MINIMUM {target_unittest} test methods")
            diagnosis_parts.append(f"Missing: {target_unittest - unittest_count} more test methods needed")
            diagnosis_parts.append("")
            diagnosis_parts.append("ACTION: Add more test methods to test.py until you have at least 15")
            error_type = "test_count_error"

            # Track count fix attempts for circuit breaker
            count_fix_attempts += 1  # Increment the existing variable (don't shadow it!)
            print(f"  📊 Test count fix attempt #{count_fix_attempts}")

        # Check for test.py errors (import/syntax/runtime errors)
        elif ("importerror" in validation_report.lower() or
              "modulenotfounderror" in validation_report.lower() or
              "syntaxerror" in validation_report.lower() or
              "indentationerror" in validation_report.lower() or
              "nameerror" in validation_report.lower() or
              "attributeerror" in validation_report.lower() or
              "typeerror" in validation_report.lower()):
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("🔴 TEST.PY HAS ERRORS")
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("test.py has syntax, import, or runtime errors that prevent tests from running.")
            diagnosis_parts.append("")
            diagnosis_parts.append("VALIDATION OUTPUT (first 8000 chars for detailed error analysis):")
            diagnosis_parts.append(validation_report[:8000])
            diagnosis_parts.append("")
            diagnosis_parts.append("ACTION: Fix test.py errors FIRST.")
            diagnosis_parts.append("Common issues:")
            diagnosis_parts.append("  - NameError: Using JavaScript 'null' instead of Python 'None'")
            diagnosis_parts.append("  - NameError: Using 'true/false' instead of 'True/False'")
            diagnosis_parts.append("  - Missing 'from main import <function>' statement")
            diagnosis_parts.append("  - Syntax errors (check indentation, parentheses, quotes)")
            diagnosis_parts.append("  - Importing something that doesn't exist in main.py")
            error_type = "test_py_error"
        
        # Check for failing tests (logic errors in main.py)
        elif "tests failed" in validation_report.lower() or "failed)" in validation_report.lower():
            # Parse pytest output for structured error info
            parsed_failures = self._parse_pytest_failures(validation_report)

            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("⚠️  TESTS ARE FAILING - FIX LOGIC IN main.py")
            diagnosis_parts.append("=" * 80)
            diagnosis_parts.append("Tests ARE running, but assertions are failing.")
            diagnosis_parts.append("This means the logic in main.py is INCORRECT.")
            diagnosis_parts.append("")
            diagnosis_parts.append(f"📊 FAILURE SUMMARY: {parsed_failures['summary']}")
            diagnosis_parts.append("")

            if parsed_failures['failed_test_names']:
                diagnosis_parts.append("❌ FAILED TESTS:")
                for test_name in parsed_failures['failed_test_names']:
                    diagnosis_parts.append(f"  - {test_name}")
                diagnosis_parts.append("")

            if parsed_failures['assertion_errors']:
                diagnosis_parts.append("💥 ASSERTION ERRORS:")
                for idx, error in enumerate(parsed_failures['assertion_errors'][:5], 1):
                    diagnosis_parts.append(f"  {idx}. {error}")
                diagnosis_parts.append("")

            if parsed_failures['failures_section']:
                diagnosis_parts.append("📋 UNITTEST FAILURES DETAIL (first 2000 chars):")
                diagnosis_parts.append(parsed_failures['failures_section'])
                diagnosis_parts.append("")

            diagnosis_parts.append("FULL VALIDATION OUTPUT (first 8000 chars):")
            diagnosis_parts.append(validation_report[:8000])
            diagnosis_parts.append("")
            diagnosis_parts.append("ACTION: Fix the logic in main.py to make ALL tests pass.")
            diagnosis_parts.append("Focus on the failed tests and assertion errors listed above.")
            error_type = "main_py_logic_error"
        
        else:
            # All tests passed!
            diagnosis_parts.append("✅ All validations passed!")
            error_type = None
        
        diagnosis = "\n".join(diagnosis_parts)
        
        # Track logic fix attempts (persistent counter - only increments, never resets during failures)
        logic_fix_attempts = state.get("logic_fix_attempts", 0)
        if error_type == "main_py_logic_error":
            logic_fix_attempts += 1
            print(f"  📊 Logic fix attempt #{logic_fix_attempts}")
            if logic_fix_attempts >= 5:
                print(f"  ⚠️  After {logic_fix_attempts} attempts, routing to REVIEWER for guidance")
        # Don't reset counter - keep it persistent to enable circuit breaker
        
        return {
            "messages": [AIMessage(content=f"CRITICAL DIAGNOSIS - MUST FIX ALL:\n{diagnosis}")],
            "diagnosis": diagnosis,
            "error_type": error_type,
            "logic_fix_attempts": logic_fix_attempts,
            "count_fix_attempts": count_fix_attempts,
            "total_validation_failures": state.get("total_validation_failures", 0),  # Preserve validator's counter!
            "iteration": state.get("iteration", 0),
            "step_count": state.get("step_count", 0) + 1,
        }

    async def _builder(self, state: BuildState) -> Dict[str, Any]:
        iteration = state.get("iteration", 0)
        validation_passed = state.get("validation_passed", None)
        reviewer_passed = state.get("reviewer_passed", None)
        formatting_errors = state.get("formatting_errors") or []
        formatting_warnings = state.get("formatting_warnings") or []

        try:
            from .shared_state import update_status
            update_status(f"Building iteration {iteration}", iteration, "build")
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                update_status(f"Building iteration {iteration}", iteration, "build")
            except ImportError:
                pass

        print(NodeHeaderTemplates.builder(iteration))

        # CIRCUIT BREAKER: Check for repeated errors
        error_history = state.get("error_history") or {}
        repeated_errors = {k: v for k, v in error_history.items() if v["count"] >= 2}

        if repeated_errors and formatting_errors:
            print("\n" + "=" * 80)
            print("🚨 CIRCUIT BREAKER ACTIVATED - REPEATED ERROR DETECTED!")
            print("=" * 80)
            for error_key, error_info in repeated_errors.items():
                print(f"\nError location: {error_key}")
                print(f"Seen {error_info['count']} times in iterations: {error_info['iterations']}")
                print(f"Error message: {error_info['error_msg']}")
            print("\n" + "=" * 80)

        if iteration > 0:
            if validation_passed is False:
                print("WARNING: Previous validation FAILED - MUST fix all validation errors!")
            if reviewer_passed is False:
                print("WARNING: Previous reviewer REJECTED - MUST address all reviewer feedback!")
            if validation_passed is False or reviewer_passed is False:
                print("Reviewing validation report and reviewer feedback to fix issues...")
        
        messages = state["messages"]
        print("Building generation system prompt...")
        system_prompt = await self._build_generation_system_prompt(state)
        print(f"System prompt built ({len(system_prompt)} chars)")

        # CIRCUIT BREAKER: When repeated errors detected, use ultra-simplified message history
        circuit_breaker_active = bool(repeated_errors and formatting_errors)

        important_messages = []

        if messages:
            important_messages.append(messages[0])
        
        diagnosis_msg = None
        validation_msg = None
        reviewer_msg = None
        
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = getattr(msg, 'content', '') or ''
                if 'DIAGNOSIS' in content or 'diagnosis' in content.lower():
                    if diagnosis_msg is None:
                        diagnosis_msg = msg
                elif 'Validator output' in content or 'VALIDATION' in content:
                    if validation_msg is None:
                        validation_msg = msg
                elif 'Reviewer verdict' in content or 'REVIEWER' in content:
                    if reviewer_msg is None:
                        reviewer_msg = msg
        
        if diagnosis_msg:
            important_messages.append(diagnosis_msg)
        if validation_msg:
            important_messages.append(validation_msg)
        if reviewer_msg:
            important_messages.append(reviewer_msg)
        
        tool_interactions = []
        i = 0
        while i < len(messages) and len(tool_interactions) < 50:
            msg = messages[i]
            if isinstance(msg, AIMessage) and getattr(msg, 'tool_calls', None):
                interaction = [msg]
                j = i + 1
                while j < len(messages) and isinstance(messages[j], ToolMessage):
                    interaction.append(messages[j])
                    j += 1
                tool_interactions.append(interaction)
                i = j
            else:
                i += 1

        tool_interactions = tool_interactions[-50:] if len(tool_interactions) > 50 else tool_interactions
        
        for interaction in tool_interactions:
            important_messages.extend(interaction)
        
        messages = important_messages
        print(f"Using {len(messages)} relevant messages (truncated from full history)")
        
        cleaned_messages = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            
            if isinstance(msg, AIMessage):
                tool_calls = getattr(msg, 'tool_calls', None)
                if tool_calls:
                    tool_call_ids = set()
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            tc_id = tc.get('id') or tc.get('tool_call_id')
                            if tc_id:
                                tool_call_ids.add(tc_id)
                        elif hasattr(tc, 'id'):
                            tool_call_ids.add(tc.id)
                        elif hasattr(tc, 'tool_call_id'):
                            tool_call_ids.add(tc.tool_call_id)
                    
                    if tool_call_ids:
                        found_responses = set()
                        j = i + 1
                        while j < len(messages) and len(found_responses) < len(tool_call_ids):
                            next_msg = messages[j]
                            if isinstance(next_msg, ToolMessage):
                                tool_id = getattr(next_msg, 'tool_call_id', None)
                                if tool_id and tool_id in tool_call_ids:
                                    found_responses.add(tool_id)
                            j += 1
                        
                        if found_responses == tool_call_ids:
                            cleaned_messages.append(msg)
                            for k in range(i + 1, j):
                                cleaned_messages.append(messages[k])
                            i = j
                            continue
                        else:
                            print(f"Warning: Skipping AIMessage with incomplete tool calls. Expected {len(tool_call_ids)} responses, found {len(found_responses)}")
                            print(f"  Tool call IDs: {tool_call_ids}")
                            print(f"  Found responses: {found_responses}")
                            i += 1
                            continue
            
            cleaned_messages.append(msg)
            i += 1
        
        workspace = Path(state["workspace_dir"]).resolve()
        required_files = ["main.py", "test.py"]
        missing_files = [f for f in required_files if not (workspace / f).exists()]

        existing_files = [f for f in required_files if (workspace / f).exists()]
        if existing_files:
            print(f"Reading {len(existing_files)} existing files to show LLM what it wrote...")
            file_contents_parts = ["=" * 80]
            file_contents_parts.append("CURRENT FILE CONTENTS (what you previously wrote):")
            file_contents_parts.append("=" * 80)
            file_contents_parts.append("")
            file_contents_parts.append("IMPORTANT: These are the ACTUAL files that exist right now.")
            file_contents_parts.append("Review them carefully before making changes.")
            file_contents_parts.append("If diagnosis shows errors, find the EXACT error in the content below and fix it.")
            file_contents_parts.append("")

            for filename in existing_files:
                try:
                    file_path = workspace / filename
                    content = file_path.read_text()
                    file_contents_parts.append(f"{'=' * 80}")
                    file_contents_parts.append(f"FILE: {filename}")
                    file_contents_parts.append(f"{'=' * 80}")

                    # Check if this file has a JSON formatting error
                    json_error = None
                    error_line = None
                    error_col = None
                    if filename.endswith('.json') and formatting_errors:
                        for err in formatting_errors:
                            if filename in err:
                                json_error = err
                                # Extract line and column from error message
                                import re as regex_module
                                line_match = regex_module.search(r'line (\d+)', err)
                                col_match = regex_module.search(r'column (\d+)', err)
                                if line_match:
                                    error_line = int(line_match.group(1))
                                if col_match:
                                    error_col = int(col_match.group(1))
                                break

                    # Show content with line numbers and error highlighting
                    lines = content.split('\n')

                    # If there's an error, show full file with highlighting
                    # If no error, show abbreviated version to save tokens
                    if json_error:
                        file_contents_parts.append("⚠️ THIS FILE HAS ERRORS - SHOWING FULL CONTENT WITH LINE NUMBERS:")
                        file_contents_parts.append("")

                        for i, line in enumerate(lines, 1):
                            line_prefix = f"{i:4d} | "

                            if error_line and i == error_line:
                                # Highlight the error line
                                file_contents_parts.append(f"{line_prefix}{line}  ← 🔴 ERROR ON THIS LINE")

                                # Show pointer to exact column if available
                                if error_col:
                                    pointer_line = " " * (len(line_prefix) + error_col - 1) + "^" * 10 + f" ← ERROR AT COLUMN {error_col}"
                                    file_contents_parts.append(pointer_line)
                            else:
                                file_contents_parts.append(f"{line_prefix}{line}")

                        file_contents_parts.append("")
                        file_contents_parts.append(f"{'🔴' * 40}")
                        file_contents_parts.append(f"ERROR: {json_error}")
                        file_contents_parts.append(f"FIX REQUIRED: Line {error_line}, Column {error_col}")
                        file_contents_parts.append(f"ACTION: Rewrite this entire file with correct JSON syntax!")
                        file_contents_parts.append(f"{'🔴' * 40}")
                    else:
                        # No error - show first 10 and last 5 lines only
                        file_contents_parts.append("✅ THIS FILE HAS NO ERRORS - Showing abbreviated content:")
                        file_contents_parts.append("")

                        if len(lines) <= 20:
                            # Short file, show everything
                            for i, line in enumerate(lines, 1):
                                file_contents_parts.append(f"{i:4d} | {line}")
                        else:
                            # Long file, show first 10 and last 5
                            for i in range(min(10, len(lines))):
                                file_contents_parts.append(f"{i+1:4d} | {lines[i]}")

                            file_contents_parts.append(f"     ... ({len(lines) - 15} lines omitted) ...")

                            for i in range(max(10, len(lines) - 5), len(lines)):
                                file_contents_parts.append(f"{i+1:4d} | {lines[i]}")

                        file_contents_parts.append("")
                        file_contents_parts.append(f"✅ File looks correct - {len(lines)} lines total")

                    file_contents_parts.append("")
                    print(f"  Read {filename} ({len(content)} characters)")
                except Exception as e:
                    print(f"  ERROR: Failed to read {filename}: {e}")
                    file_contents_parts.append(f"FILE: {filename} - ERROR READING: {e}")
                    file_contents_parts.append("")

            file_contents_parts.append("=" * 80)
            file_contents_message = HumanMessage(content="\n".join(file_contents_parts))
            cleaned_messages.append(file_contents_message)
            print(f"Added current file contents to message history ({len(file_contents_parts)} lines)")

            def _count_unittest_methods(path: Path) -> int | None:
                try:
                    text = path.read_text()
                except Exception:
                    return None
                pattern = re.compile(r"^\s*def\s+test_[\w]+\s*\(", re.MULTILINE)
                return len(pattern.findall(text))

            # Check test.py has sufficient tests
            test_methods = _count_unittest_methods(workspace / "test.py")
            if test_methods is not None and test_methods < 2:
                deficit = 15 - test_methods
                test_count_warning = [
                    f"WARNING: `test.py` currently has only {test_methods} test methods.",
                    f"You MUST add at least {deficit} more test methods so the total is >= 2.",
                    "",
                    "ACTION: Regenerate `test.py` with at least 2 test methods total.",
                ]
                cleaned_messages.append(HumanMessage(content="\n".join(test_count_warning)))

        validation_passed = state.get("validation_passed", None)
        files_need_fixing = validation_passed is False

        # CIRCUIT BREAKER: Override normal error message with ultra-focused fix message
        if circuit_breaker_active:
            print("🚨 CIRCUIT BREAKER: Clearing message history and sending ultra-focused fix message!")

            # Keep ONLY essential messages
            cleaned_messages = [messages[0]] if messages else []  # Keep initial user prompt

            # Build ultra-focused error message
            for error_key, error_info in repeated_errors.items():
                # Extract file, line, column from error_key
                parts = error_key.split(':')
                filename = parts[0]
                line_num = parts[1].replace('line_', '')
                col_num = parts[2].replace('col_', '')

                # Read the problematic file and show exact content at error location
                workspace = Path(state["workspace_dir"]).resolve()
                file_path = workspace / filename

                # Read file and extract lines around the error
                file_content_snippet = ""
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        error_line_idx = int(line_num) - 1  # Convert to 0-indexed
                        col_idx = int(col_num) - 1

                        # Show 3 lines before, the error line, and 3 lines after
                        start_idx = max(0, error_line_idx - 3)
                        end_idx = min(len(lines), error_line_idx + 4)

                        file_content_snippet = "FILE CONTENT AROUND ERROR:\n"
                        for i in range(start_idx, end_idx):
                            line_number = i + 1
                            line_content = lines[i].rstrip()

                            if i == error_line_idx:
                                # This is the error line - mark it
                                file_content_snippet += f">>> {line_number:4d} | {line_content}\n"
                                # Add pointer to exact column
                                pointer = " " * (col_idx + 10) + "^" + " " * 3 + f"<-- ERROR at column {col_num}"
                                file_content_snippet += pointer + "\n"
                            else:
                                file_content_snippet += f"    {line_number:4d} | {line_content}\n"
                except Exception as e:
                    file_content_snippet = f"(Could not read file: {e})\n"

                # Specific fix for "Invalid control character"
                specific_fix = ""
                if "Invalid control character" in error_info['error_msg']:
                    specific_fix = """
⚠️  "Invalid control character" means you have raw newlines or special chars in a JSON string!

WRONG (raw newline in string):
  "description": "This test checks
                  multiple lines"

CORRECT (single line):
  "description": "This test checks multiple lines"

OR (escaped newline):
  "description": "This test checks\\nmultiple lines"
"""

                # Debug: Show what we're sending
                print(f"\n📄 SHOWING FILE CONTENT FROM {filename} AT ERROR LOCATION:")
                print(file_content_snippet)
                print()

                circuit_breaker_message = HumanMessage(content=f"""
{'=' * 80}
🚨 CIRCUIT BREAKER ACTIVATED - REPEATED ERROR
{'=' * 80}

You've made the SAME error {error_info['count']} times at the SAME location!

File: {filename}
Error location: Line {line_num}, Column {col_num}
Iterations where this error appeared: {error_info['iterations']}

Error message: {error_info['error_msg']}

{'=' * 80}
{file_content_snippet}
{'=' * 80}
STOP TRYING THE SAME APPROACH!
{'=' * 80}

This error keeps repeating because you're making the same mistake.
{specific_fix}
WHAT TO DO:
1. Look at the >>> marked line above (line {line_num})
2. The ^ pointer shows EXACTLY where the error is (column {col_num})
3. If "Invalid control character": Remove raw newlines from strings
4. If "Expecting ','": Add comma after the previous object/array
5. REWRITE the broken JSON object correctly - write it fresh!

🛑 CRITICAL RULES:
1. ONLY fix {filename} - this is the ONLY file with errors
2. DO NOT touch the other file ({"test.py" if filename == "main.py" else "main.py"})
3. Use write_file tool EXACTLY ONCE for {filename} only
4. If you write the other file, you will BREAK working code

⚠️  FILE TO LEAVE ALONE:
- {"test.py" if filename == "main.py" else "main.py"} (WORKING - DO NOT EDIT)

After you fix this ONE error in {filename}, we'll validate the rest.
{'=' * 80}
""")
                cleaned_messages.append(circuit_breaker_message)
                break  # Only show first repeated error

        # Simplified file checking - only main.py and test.py
        if (
            existing_files
            and not missing_files
            and validation_passed is None
        ):
            print(f"Both files exist and validation hasn't run yet")
            print("   Instructing LLM to emit READY_TOKEN instead of rewriting files")
            ready_message = HumanMessage(content=f"""
EXCELLENT! Both required files have been successfully created:
- main.py
- test.py

YOUR NEXT STEP:
DO NOT rewrite any files. DO NOT call write_file tool.
Simply respond with the ready token to proceed to validation:

{self.READY_TOKEN}

Just output that token on its own line and nothing else. Validation will run automatically after you emit the token.
""")
            cleaned_messages.append(ready_message)

        # Simple message based on what's missing or broken
        if missing_files:
            print(f"WARNING: Missing files detected: {', '.join(missing_files)}")
            print("   Adding explicit instruction to CREATE these files using write_file tool")
            force_tool_message = HumanMessage(content=f"""
CRITICAL: You MUST use the write_file tool RIGHT NOW to create these missing files: {', '.join(missing_files)}

DO NOT just describe what to do - you MUST actually call the write_file tool for each missing file.

Example tool call format:
- Tool: write_file
- Arguments: file_path="test.py", content="[file content here]"

You MUST make tool calls. Text-only responses are NOT acceptable when files are missing.
""")
            cleaned_messages.append(force_tool_message)
        elif files_need_fixing:
            print(f"WARNING: Validation FAILED - files exist but tests are failing")
            print("   Adding explicit instruction to FIX files using write_file tool")

            test_count = _count_unittest_methods(workspace / "test.py") or 0

            force_fix_message = HumanMessage(content=BuilderTemplates.force_fix_message(
                state.get('iteration', 0), test_count
            ))
            cleaned_messages.append(force_fix_message)

        with_system = [SystemMessage(content=system_prompt)] + cleaned_messages
        print(f"Sending {len(cleaned_messages)} messages to generator LLM...")

        try:
            print("Calling generator LLM with tools...")
            response = self.generator_llm_with_tools.invoke(with_system)
            tool_calls = getattr(response, 'tool_calls', None)
            if tool_calls:
                print(f"LLM response received with {len(tool_calls)} tool call(s)")
                for tc in tool_calls:
                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown')
                    print(f"  Tool: {tool_name}")
            else:
                print(f"WARNING: LLM response received (no tool calls, content: {len(response.content) if hasattr(response, 'content') else 0} chars)")
                if missing_files or files_need_fixing:
                    if missing_files:
                        issue_desc = f"Files still missing ({', '.join(missing_files)})"
                        action = f"create these files: {', '.join(missing_files)}"
                    else:
                        issue_desc = "Validation FAILED or formatting errors remain"
                        action = "fix the broken files using write_file tool (rewrite JSON if required)"
                    
                    print(f"ERROR: CRITICAL: {issue_desc} but LLM didn't call tools!")
                    print("   Adding retry message forcing tool usage...")
                    retry_message = HumanMessage(content=f"""
You responded with text but did NOT call any tools. This is WRONG.

{issue_desc}

You MUST call the write_file tool to {action}

I will call the LLM again. This time you MUST use tools. No exceptions.
TEXT-ONLY RESPONSES ARE NOT ACCEPTABLE. YOU MUST CALL write_file TOOLS.
""")
                    retry_system = SystemMessage(content=system_prompt + "\n\nCRITICAL: The previous response was text-only. You MUST use write_file tool calls. Text responses are NOT acceptable.")
                    retry_messages = cleaned_messages + [retry_message]
                    try:
                        response = self.generator_llm_with_tools.invoke([retry_system] + retry_messages)
                        tool_calls = getattr(response, 'tool_calls', None)
                        if tool_calls:
                            print(f"Retry successful: {len(tool_calls)} tool call(s)")
                        else:
                            print(f"ERROR: Retry failed: Still no tool calls. Response: {response.content[:200] if hasattr(response, 'content') else 'N/A'}")
                    except Exception as retry_e:
                        print(f"WARNING: Retry attempt failed: {retry_e}")
        except Exception as e:
            error_msg = str(e)
            if "tool_call" in error_msg.lower():
                print(f"Tool call error: {e}")
                print(f"Message count: {len(cleaned_messages)}")
                for idx, msg in enumerate(cleaned_messages[:5]):
                    msg_type = type(msg).__name__
                    has_tool_calls = isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls
                    print(f"  Message {idx}: {msg_type}, has_tool_calls: {has_tool_calls}")
                raise
            else:
                raise

        iteration = state["iteration"] + 1
        step_count = state.get("step_count", 0) + 1
        update: Dict[str, Any] = {
            "messages": [response],
            "iteration": iteration,
            "step_count": step_count,
        }
        if not formatting_errors:
            update["formatting_errors"] = None
        if not formatting_warnings:
            update["formatting_warnings"] = None
        return update

    def _builder_router(self, state: BuildState) -> str:
        last_message = state["messages"][-1]
        step_count = state.get("step_count", 0)

        if step_count >= self.MAX_STEPS:
            print("WARNING: Step count limit reached, routing to validator pipeline")
            return "validate"

        workspace = Path(state["workspace_dir"]).resolve()
        required_files = ["main.py", "test.py"]
        all_files_exist = all((workspace / name).exists() for name in required_files)
        missing_files = [f for f in required_files if not (workspace / f).exists()]

        has_tool_calls = getattr(last_message, "tool_calls", None)
        content = getattr(last_message, "content", "") or ""
        has_ready_token = self.READY_TOKEN in content

        if missing_files and not has_tool_calls:
            print(f"ERROR: Files missing ({', '.join(missing_files)}) but no tool calls detected")
            print("   LLM must use tools to create files - routing back to build")
            return "build"

        if has_tool_calls:
            tool_calls = getattr(last_message, "tool_calls", None)
            if tool_calls:
                tool_names = []
                for tc in tool_calls:
                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown')
                    tool_names.append(tool_name)

                print(f"Tool calls detected: {tool_names}")

            print(f"   Routing to TOOLS node")
            return "tools"

        if all_files_exist:
            print("All required files exist, routing to validation")
            return "validate"

        if has_ready_token:
            if missing_files:
                print(f"WARNING: READY_TOKEN found but files missing ({', '.join(missing_files)})")
                print("   Routing back to build - LLM must create files first")
                return "build"
            print("READY_TOKEN found, routing to validation")
            return "validate"

        print("Continuing build phase")
        return "build"

    def _tools_router(self, state: BuildState) -> str:
        """
        Route after tools execute:
        - If all files exist and validation hasn't run, route to validate
        - If fixing validation errors (validation_passed is False), route to validate for re-validation
        - If fixing review issues (reviewer_passed is False, validation passed), route to validate for re-validation
        - Otherwise route to build to continue generating
        """
        validation_passed = state.get("validation_passed", None)
        reviewer_passed = state.get("reviewer_passed", None)
        iteration = state.get("iteration", 0)
        workspace = Path(state["workspace_dir"]).resolve()
        required_files = ["main.py", "test.py"]
        all_files_exist = all((workspace / name).exists() for name in required_files)

        print("\n" + "="*80)
        print(f"TOOLS_ROUTER [Iteration {iteration}]")
        print(f"   validation_passed={validation_passed}, reviewer_passed={reviewer_passed}")
        print(f"   all_files_exist={all_files_exist}")

        if validation_passed is None and all_files_exist:
            print("   DECISION: validation_passed=None + all files exist -> routing to VALIDATE")
            print("   This prevents infinite loop: build -> tools -> build -> tools")
            print("="*80 + "\n")
            return "validate"

        if validation_passed is False and all_files_exist:
            print("   DECISION: validation_passed=False -> routing to VALIDATE for re-validation")
            print("="*80 + "\n")
            return "validate"

        if validation_passed is True and reviewer_passed is False and all_files_exist:
            print("   DECISION: reviewer_passed=False -> routing to VALIDATE for re-validation")
            print("="*80 + "\n")
            return "validate"

        print("   DECISION: Files not all created yet -> routing to BUILD")
        print("="*80 + "\n")
        return "build"

    # _format_router removed - no longer using JSON formatting

    def _run_validator(self, workspace: Path) -> subprocess.CompletedProcess:
        """Run unittest tests in test.py to validate the implementation."""
        command = [sys.executable, "test.py"]
        return subprocess.run(
            command,
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )

    def _validator(self, state: BuildState) -> Dict[str, Any]:
        """
        Automatic validation node - runs unittest tests in test.py BEFORE review.
        This is called automatically by the graph after files are written.
        The LLM cannot call this manually - it's system-controlled.
        """
        try:
            from .shared_state import update_status
            update_status("Running validation", state.get("iteration", 0), "validate")
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                update_status("Running validation", state.get("iteration", 0), "validate")
            except ImportError:
                pass

        print(NodeHeaderTemplates.validator())
        workspace = Path(state["workspace_dir"]).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        
        if workspace.exists():
            all_files = [f.name for f in workspace.iterdir() if f.is_file()]
            print(f"📁 Workspace {workspace} contains files: {all_files}")

        required_files = ["main.py", "test.py"]
        missing = [name for name in required_files if not (workspace / name).exists()]

        if missing:
            report = (
                "Validator invoked but files are missing: "
                + ", ".join(missing)
                + "\nEnsure all files exist before marking readiness."
            )
            print(f"❌ Missing files: {', '.join(missing)}")
            print("="*60 + "\n")
            return {
                "validation_report": report,
                "validation_passed": False,
                "messages": [AIMessage(content=f"Validation failed:\n{report}")],
                "iteration": state["iteration"],
            }

        print("🔍 Running unittest tests (python test.py)...")
        process = self._run_validator(workspace)
        output = (process.stdout or "").strip()
        stderr = (process.stderr or "").strip()
        combined = output + ("\n" + stderr if stderr else "")
        passed = process.returncode == 0

        verdict_header = "VALIDATION PASSED" if passed else "VALIDATION FAILED"
        report = f"{verdict_header}\n{combined}".strip()
        print(f"{'✅' if passed else '❌'} Validation {'PASSED' if passed else 'FAILED'}")
        if output:
            print("="*60)
            print("FULL VALIDATOR OUTPUT:")
            print("="*60)
            print(output)
            if stderr:
                print("\n" + "="*60)
                print("VALIDATOR STDERR:")
                print("="*60)
                print(stderr)
            print("="*60)
        print("="*60 + "\n")
        
        try:
            from .shared_state import update_validator_output
            update_validator_output(report)
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_validator_output
                update_validator_output(report)
            except ImportError:
                pass

        # Reset circuit breaker counters when validation passes
        updates = {
            "validation_report": report,
            "validation_passed": passed,
            "messages": [AIMessage(content=f"Validator output:\n{report}")],
            "iteration": state["iteration"],
            "step_count": state.get("step_count", 0) + 1,
        }

        # Reset all error counters when validation succeeds
        if passed:
            updates["logic_fix_attempts"] = 0
            updates["count_fix_attempts"] = 0
            updates["total_validation_failures"] = 0
            print("✅ Validation passed - resetting all error counters")
        else:
            # Increment total failures counter for universal circuit breaker
            updates["total_validation_failures"] = state.get("total_validation_failures", 0) + 1

        return updates

    def _validator_router(self, state: BuildState) -> str:
        validation_passed = state.get("validation_passed", False)
        iteration = state.get("iteration", 0)

        print("\n" + "="*80)
        print(f"🔀 VALIDATOR_ROUTER [Iteration {iteration}]")
        print(f"   validation_passed={validation_passed}")

        if validation_passed:
            print("   ✅ DECISION: Validation PASSED → routing to REVIEW")
            print("="*80 + "\n")
            return "review"
        else:
            print("   ❌ DECISION: Validation FAILED → routing to DIAGNOSE")
            print("="*80 + "\n")
            return "diagnose"

    def _diagnose_router(self, state: BuildState) -> str:
        """Route after DIAGNOSE: If logic fixes or count fixes failing repeatedly, go to REVIEWER for guidance"""
        logic_fix_attempts = state.get("logic_fix_attempts", 0)
        count_fix_attempts = state.get("count_fix_attempts", 0)
        total_validation_failures = state.get("total_validation_failures", 0)
        error_type = state.get("error_type")
        iteration = state.get("iteration", 0)

        print("\n" + "="*80)
        print(f"🔀 DIAGNOSE_ROUTER [Iteration {iteration}]")
        print(f"   logic_fix_attempts={logic_fix_attempts}")
        print(f"   count_fix_attempts={count_fix_attempts}")
        print(f"   total_validation_failures={total_validation_failures}")

        # UNIVERSAL CIRCUIT BREAKER: Prevent infinite loops regardless of error type
        if total_validation_failures >= 3:
            print(f"   🚨 UNIVERSAL CIRCUIT BREAKER ACTIVATED!")
            print(f"   ⚠️  DECISION: {total_validation_failures} consecutive validation failures → routing to REVIEWER")
            print("   Too many validation failures across all error types - need human review")
            print("="*80 + "\n")
            return "review"

        if logic_fix_attempts >= 5:
            print(f"   ⚠️  DECISION: {logic_fix_attempts} logic fix attempts failed → routing to REVIEWER for guidance")
            print("="*80 + "\n")
            return "review"
        elif count_fix_attempts >= 3 or error_type == "stuck_count_error":
            print(f"   ⚠️  DECISION: Counts stuck for {count_fix_attempts} iterations → routing to REVIEWER for guidance")
            print("="*80 + "\n")
            return "review"
        else:
            print(f"   ✅ DECISION: Continue fixing → routing to BUILD")
            print("="*80 + "\n")
            return "build"

    def _collect_artifacts(self, workspace: Path) -> Dict[str, str]:
        artifacts: Dict[str, str] = {}
        if workspace.exists():
            existing_files = list(workspace.iterdir())
            print(f"DEBUG: Workspace {workspace} contains: {[f.name for f in existing_files if f.is_file()]}")
        
        for name in ["main.py", "test.py"]:
            file_path = workspace / name
            if file_path.exists():
                try:
                    artifacts[name] = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
                    artifacts[name] = f"Error reading file: {e}"
            else:
                print(f"DEBUG: File not found: {file_path}")
        return artifacts

    async def _reviewer(self, state: BuildState) -> Dict[str, Any]:
        try:
            from .shared_state import update_status
            update_status("Reviewing code quality", state.get("iteration", 0), "review")
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                update_status("Reviewing code quality", state.get("iteration", 0), "review")
            except ImportError:
                pass

        print(NodeHeaderTemplates.reviewer(state.get("iteration", 0)))
        workspace = Path(state["workspace_dir"])
        print("📦 Collecting artifacts from workspace...")
        artifacts = self._collect_artifacts(workspace)
        print(f"✓ Collected {len(artifacts)} artifacts: {', '.join(artifacts.keys())}")

        artifact_summaries = []
        for name, content in artifacts.items():
            snippet = content if len(content) <= 4000 else content[:4000] + "\n... [truncated]"
            artifact_summaries.append(f"### {name}\n{snippet}")

        supplemental = [
            state.get("validation_report") or "",
            state.get("task_plan") or "",
        ]
        file_types = ["main.py", "test.py"]
        print(f"📚 Gathering RAG context for review...")
        review_context = await self._gather_context(
            state["user_prompt"],
            supplemental,
            file_types=file_types
        )
        print(f"✓ Review context gathered ({len(review_context)} chars)")

        system_prompt = """You are the decisive reviewer for this coding task. Be uncompromising about alignment with the prompt, retrieved context (including all instruction files), and validator expectations.
Approve ONLY when ALL of the following are true:
1. The implementation (main.py) follows ideal code instructions exactly
2. The tests (test.py) have at least 2 test methods and follow unittest instructions exactly
3. All tests pass validation (unittest tests run successfully)
4. All requirements from the prompt are met

If ANY file does not follow its specific instructions or anything is missing, set approved to False and list the issues succinctly with references to the instruction files."""

        human_prompt = f"""Prompt to satisfy:
{state['user_prompt']}

Task plan:
{state.get('task_plan') or ''}

Validator report:
{state.get('validation_report') or ''}

RAG context:
{review_context}

Artifacts:
{'\n'.join(artifact_summaries)}
"""

        print("🤖 Calling reviewer LLM...")
        decision = self.review_llm_structured.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
        )

        feedback_text = decision.feedback
        if decision.notes:
            feedback_text += f"\nNotes: {decision.notes}"

        print(f"{'✅' if decision.approved else '❌'} Reviewer verdict: {decision.verdict}")
        print(f"   Approved: {decision.approved}")
        print(f"   Feedback: {feedback_text[:200]}...")
        print("="*60 + "\n")

        message = AIMessage(
            content=(
                f"Reviewer verdict: {decision.verdict}\n"
                f"Approved: {decision.approved}\n"
                f"Feedback:\n{feedback_text}"
            )
        )

        return {
            "messages": [message],
            "reviewer_feedback": feedback_text,
            "reviewer_passed": bool(decision.approved),
            "iteration": state["iteration"],
            "step_count": state.get("step_count", 0) + 1,
        }

    def _review_router(self, state: BuildState) -> str:
        validation_passed = state.get("validation_passed", False)
        reviewer_passed = state.get("reviewer_passed", False)
        step_count = state.get("step_count", 0)
        iteration = state.get("iteration", 0)

        if step_count >= self.MAX_STEPS:
            print(f"⚠️ Maximum steps ({self.MAX_STEPS}) reached. Stopping to prevent infinite loop.")
            print(f"   Final status: Validation={'PASSED' if validation_passed else 'FAILED'}, Reviewer={'APPROVED' if reviewer_passed else 'REJECTED'}")

            try:
                from .shared_state import update_status
                update_status(StatusTemplates.max_steps_reached(validation_passed, reviewer_passed), iteration, "complete")
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                    update_status(StatusTemplates.max_steps_reached(validation_passed, reviewer_passed), iteration, "complete")
                except ImportError:
                    pass

            try:
                from .sidekick_tools import push
                push(NotificationTemplates.max_steps_reached(iteration, validation_passed, reviewer_passed))
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.sidekick_tools import push
                    push(NotificationTemplates.max_steps_reached(iteration, validation_passed, reviewer_passed))
                except:
                    pass

            return "END"

        if validation_passed and reviewer_passed:
            print("✅ Both validation and reviewer passed! Task complete.")

            try:
                from .shared_state import update_status
                update_status(StatusTemplates.success(), iteration, "complete")
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                    update_status(StatusTemplates.success(), iteration, "complete")
                except ImportError:
                    pass

            try:
                from .sidekick_tools import push
                push(NotificationTemplates.success(iteration))
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.sidekick_tools import push
                    push(NotificationTemplates.success(iteration))
                except:
                    pass

            return "END"

        if not validation_passed:
            print(f"❌ Validation failed (iteration {iteration}). Continuing to fix issues...")
        if not reviewer_passed:
            print(f"❌ Reviewer rejected (iteration {iteration}). Continuing to address feedback...")

        if iteration >= self.MAX_ITERATIONS:
            print(f"⚠️ Reached iteration limit ({self.MAX_ITERATIONS})")
            print(f"   FORCE STOPPING to prevent infinite loop")
            print(f"   Final status: Validation={'PASSED' if validation_passed else 'FAILED'}, Reviewer={'APPROVED' if reviewer_passed else 'REJECTED'}")

            try:
                from .shared_state import update_status
                update_status(StatusTemplates.iteration_limit_reached(self.MAX_ITERATIONS, validation_passed, reviewer_passed), iteration, "complete")
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                    update_status(StatusTemplates.iteration_limit_reached(self.MAX_ITERATIONS, validation_passed, reviewer_passed), iteration, "complete")
                except ImportError:
                    pass

            try:
                from .sidekick_tools import push
                push(NotificationTemplates.iteration_limit_reached(self.MAX_ITERATIONS, validation_passed, reviewer_passed))
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.sidekick_tools import push
                    push(NotificationTemplates.iteration_limit_reached(self.MAX_ITERATIONS, validation_passed, reviewer_passed))
                except:
                    pass

            return "END"

        return "build"

    async def _build_graph(self):
        graph_builder = StateGraph(BuildState)

        self.tool_node = ToolNode(tools=self.tools)

        def tools_with_status(state: BuildState) -> Dict[str, Any]:
            """Wrap ToolNode to add status updates."""
            try:
                from .shared_state import update_status
                update_status("Executing file writes", state.get("iteration", 0), "tools")
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                    update_status("Executing file writes", state.get("iteration", 0), "tools")
                except ImportError:
                    pass

            return self.tool_node.invoke(state)

        graph_builder.add_node("plan", self._planner)
        graph_builder.add_node("build", self._builder)
        graph_builder.add_node("tools", tools_with_status)
        graph_builder.add_node("validate", self._validator)
        graph_builder.add_node("diagnose", self._diagnose_issues)
        graph_builder.add_node("review", self._reviewer)

        graph_builder.add_edge(START, "plan")
        graph_builder.add_edge("plan", "build")
        graph_builder.add_conditional_edges(
            "build",
            self._builder_router,
            {"tools": "tools", "build": "build", "validate": "validate"},
        )
        graph_builder.add_conditional_edges(
            "tools",
            self._tools_router,
            {"build": "build", "validate": "validate"},
        )
        graph_builder.add_conditional_edges(
            "validate",
            self._validator_router,
            {"diagnose": "diagnose", "review": "review"},
        )
        graph_builder.add_conditional_edges(
            "diagnose",
            self._diagnose_router,
            {"build": "build", "review": "review"},
        )
        graph_builder.add_conditional_edges(
            "review",
            self._review_router,
            {"END": END, "build": "build"},
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, prompt: str, continue_conversation: bool = False) -> Dict[str, Any]:
        continuation_keywords = ["fix", "update", "change", "modify", "but", "however", "still", "again", "retry", "continue"]
        is_continuation = continue_conversation or any(keyword in prompt.lower() for keyword in continuation_keywords)
        
        workspace = FIXED_WORKSPACE.resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        
        if is_continuation and self.last_workspace and Path(self.last_workspace).exists():
            print("\n" + "="*80)
            print("🔄 CONTINUING PREVIOUS TASK")
            print("="*80)
            print(f"📝 Continuation prompt: {prompt[:100]}..." if len(prompt) > 100 else f"📝 Continuation prompt: {prompt}")
            print("="*80)
            print(f"📁 Using fixed workspace: {workspace}")
            thread_id = self.last_thread_id or f"{self.sidekick_id}-{uuid.uuid4().hex}"
        else:
            print("\n" + "="*80)
            print("🚀 STARTING NEW TASK (Fresh workspace)")
            print("="*80)
            print(f"📝 Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"📝 Prompt: {prompt}")
            print("="*80)

            print("🧹 Cleaning workspace for new task...")
            files_before = []
            if workspace.exists():
                files_before = list(workspace.iterdir())

            if files_before:
                print(f"   Found {len(files_before)} items from previous task")
                files_cleared = []
                for item in files_before:
                    try:
                        if item.is_file():
                            item.unlink()
                            files_cleared.append(item.name)
                        elif item.is_dir():
                            shutil.rmtree(item)
                            files_cleared.append(f"{item.name}/ (directory)")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not remove {item}: {e}")

                if files_cleared:
                    print(f"✓ Cleared {len(files_cleared)} items: {', '.join(files_cleared[:5])}{'...' if len(files_cleared) > 5 else ''}")
            else:
                print("   Workspace already clean (no previous files)")

            remaining_files = list(workspace.iterdir()) if workspace.exists() else []
            if remaining_files:
                print(f"⚠️ Warning: {len(remaining_files)} items remain after cleanup")
                print(f"   Files: {[f.name for f in remaining_files]}")
            else:
                print("✓ Workspace ready: empty and clean")

            print(f"📁 Using fixed workspace: {workspace}")
            print(f"   All new files will be created here")

            self.last_workspace = None
            self.last_thread_id = None
            thread_id = f"{self.sidekick_id}-{uuid.uuid4().hex}"
        
        self.last_workspace = str(workspace.resolve())
        self.last_thread_id = thread_id
        
        print("🔧 Updating tools for workspace...")
        await self._update_tools_for_workspace(str(workspace.resolve()))
        print("✓ Tools updated")

        initial_messages: List[Any] = [
            HumanMessage(content=f"Primary task prompt:\n{prompt}"),
        ]

        initial_state: BuildState = {
            "messages": initial_messages,
            "user_prompt": prompt,
            "rag_context": "",
            "task_plan": None,
            "workspace_dir": str(workspace.resolve()),
            "validation_report": None,
            "validation_passed": None,
            "reviewer_feedback": None,
            "reviewer_passed": None,
            "diagnosis": None,
            "iteration": 0,
            "step_count": 0,
        }

        recursion_limit = 100
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "recursion_limit": recursion_limit,
        }
        print("\n🔄 Starting graph execution...")
        print(f"   Recursion limit: {recursion_limit}")
        print(f"   Thread ID: {config['configurable']['thread_id']}")

        final_state = None
        accumulated_state = dict(initial_state)
        try:
            if self.langsmith_tracer:
                stream = self.graph.astream(
                    initial_state,
                    config=config,
                    callbacks=[self.langsmith_tracer]
                )
            else:
                stream = self.graph.astream(initial_state, config=config)

            async for state_update in stream:
                # Each state_update is a dict with node_name: node_output
                # Extract the state from the node output and merge it
                if isinstance(state_update, dict):
                    for node_name, node_state in state_update.items():
                        if isinstance(node_state, dict):
                            # Merge node_state into accumulated_state
                            for key, value in node_state.items():
                                if key == "messages":
                                    # Append messages, don't replace
                                    if key in accumulated_state:
                                        accumulated_state[key].extend(value if isinstance(value, list) else [value])
                                    else:
                                        accumulated_state[key] = value if isinstance(value, list) else [value]
                                else:
                                    # For all other keys, just update
                                    accumulated_state[key] = value

            final_state = accumulated_state

            # Debug: Print key state values
            print(f"\n📊 Final State Summary:")
            print(f"   - validation_passed: {final_state.get('validation_passed')}")
            print(f"   - reviewer_passed: {final_state.get('reviewer_passed')}")
            print(f"   - validation_report exists: {bool(final_state.get('validation_report'))}")
            print(f"   - reviewer_feedback exists: {bool(final_state.get('reviewer_feedback'))}")
        except Exception as e:
            error_msg = str(e)
            if "recursion limit" in error_msg.lower() or "recursion_limit" in error_msg.lower():
                print("\n⚠️  RECURSION LIMIT REACHED - Please review results")
                error_message = AIMessage(
                    content=f"⚠️ Recursion limit reached after {recursion_limit} iterations.\n"
                    f"The agent has completed {recursion_limit} iterations but hasn't fully solved the task yet.\n"
                    f"Please review the generated files and validation results below.\n\n"
                    f"This typically means:\n"
                    f"- The task may be too complex for automatic completion\n"
                    f"- The tests or requirements may need adjustment\n"
                    f"- The agent needs human guidance to proceed\n\n"
                    f"Generated files are available in the workspace for review."
                )
                
                try:
                    from langgraph.checkpoint.base import BaseCheckpointSaver
                    checkpoints = list(self.memory.list(config, limit=1))
                    if checkpoints:
                        last_checkpoint = checkpoints[0]
                        last_state = self.memory.get(config, last_checkpoint["checkpoint_id"])
                        if last_state and "channel_values" in last_state:
                            final_state = last_state["channel_values"]
                            final_state["messages"] = final_state.get("messages", []) + [error_message]
                            final_state["reviewer_feedback"] = f"Error: Recursion limit reached. {error_msg}"
                            if not final_state.get("validation_report"):
                                final_state["validation_report"] = "Could not complete validation due to recursion limit."
                        else:
                            raise ValueError("No valid state in checkpoint")
                    else:
                        raise ValueError("No checkpoints found")
                except Exception:
                    final_state = {
                        **initial_state,
                        "messages": initial_state["messages"] + [error_message],
                        "reviewer_feedback": f"Error: Recursion limit reached. {error_msg}",
                        "validation_report": "Could not complete validation due to recursion limit.",
                    }
            else:
                raise

        print("\n✓ Graph execution completed!")
        print(f"   Final iteration: {final_state.get('iteration', 0)}")
        print(f"   Final step count: {final_state.get('step_count', 0)}")
        print(f"   Validation passed: {final_state.get('validation_passed', False)}")
        print(f"   Reviewer passed: {final_state.get('reviewer_passed', False)}")

        print("\n📦 Collecting final artifacts...")
        artifacts = self._collect_artifacts(workspace)
        print(f"✓ Collected {len(artifacts)} artifacts")

        # Get validation and review status
        validation_passed = final_state.get("validation_passed")
        reviewer_passed = final_state.get("reviewer_passed")

        # Build proper status messages
        if validation_passed:
            validation_report = final_state.get("validation_report") or "✅ All tests passed successfully!"
        else:
            validation_report = final_state.get("validation_report") or "Validator did not run."

        if reviewer_passed:
            review_summary = final_state.get("reviewer_feedback") or "✅ Code review passed - implementation meets requirements!"
        else:
            review_summary = final_state.get("reviewer_feedback") or "Review not completed."
        
        # Check if recursion limit was reached
        recursion_limit_reached = final_state and "Recursion limit reached" in str(final_state.get("reviewer_feedback", ""))

        if recursion_limit_reached:
            print("\n" + "="*80)
            print("⚠️  RECURSION LIMIT REACHED - PLEASE REVIEW RESULTS")
            print("="*80 + "\n")
            status_message = f"⚠️ Recursion limit reached after {final_state.get('iteration', 0)} iterations - Please review results"
        else:
            print("\n" + "="*80)
            print("✅ TASK COMPLETED")
            print("="*80 + "\n")
            status_message = "✅ Task completed successfully!"

        try:
            from .shared_state import update_status
            final_iteration = final_state.get("iteration", 0)
            status_state = "complete" if not recursion_limit_reached else "partial"
            update_status(status_message, final_iteration, status_state)
        except ImportError:
            try:
                from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_status
                final_iteration = final_state.get("iteration", 0)
                status_state = "complete" if not recursion_limit_reached else "partial"
                update_status(status_message, final_iteration, status_state)
            except ImportError:

                pass

        chat_history = []
        for message in final_state.get("messages", []):
            if isinstance(message, HumanMessage):
                chat_history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                chat_history.append({"role": "assistant", "content": message.content})

        return {
            "workspace": str(workspace.resolve()),
            "plan": final_state.get("task_plan") or "",
            "validation_report": validation_report,
            "review_summary": review_summary,
            "artifacts": artifacts,
            "chat_history": chat_history,
        }

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())

