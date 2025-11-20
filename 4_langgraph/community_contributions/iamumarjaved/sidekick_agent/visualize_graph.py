"""
Visualize the Sidekick Agent LangGraph Structure
This file generates a visual representation of the graph nodes and edges.
"""

import asyncio
from pathlib import Path
from sidekick import Sidekick


async def visualize_graph():
    """Print the LangGraph structure showing all nodes, edges, and routing logic."""

    print("=" * 80)
    print("SIDEKICK AGENT - LANGGRAPH STRUCTURE")
    print("=" * 80)
    print()

    sidekick = Sidekick()
    await sidekick.setup()

    print("GENERATING VISUAL GRAPH...")
    try:
        graph = sidekick.graph
        if graph:
            graph_image = graph.get_graph().draw_mermaid_png()
            
            output_dir = Path(__file__).parent
            graph_file = output_dir / "sidekick_graph.png"
            
            with open(graph_file, "wb") as f:
                f.write(graph_image)
            
            print(f"Visual graph saved to: {graph_file}")
            print(f"   You can open this file to see the visual flow diagram!")
            print(f"   Tip: Use 'open {graph_file}' to view it now")
        else:
            print("WARNING: Graph not available - showing text visualization only")
    except Exception as e:
        print(f"WARNING: Could not generate visual graph: {e}")
        print("   Showing text visualization only")
    
    print()

    print("GRAPH STRUCTURE:")
    print()

    # Define the graph structure manually since we know it from the code
    nodes = {
        "START": "Entry point",
        "plan": "Create task plan from user prompt",
        "build": "Generate code files (main.py, test.py, JSON files)",
        "tools": "Execute tool calls (write_file, read_file)",
        "format_tests": "Normalize JSON test files",
        "validate": "Run validator.py (JSON + unittest validation)",
        "diagnose": "Analyze validation errors and create fix instructions",
        "review": "Review code quality and provide feedback",
        "END": "Exit point"
    }

    print("NODES:")
    for node, description in nodes.items():
        print(f"  - {node:15} -> {description}")

    print()
    print("=" * 80)
    print()

    print("EDGES & ROUTING LOGIC:")
    print()

    edges = [
        {
            "from": "START",
            "to": "plan",
            "type": "unconditional",
            "description": "Always starts with planning"
        },
        {
            "from": "plan",
            "to": "build",
            "type": "unconditional",
            "description": "Plan feeds into build phase"
        },
        {
            "from": "build",
            "to": ["tools", "build", "format_tests"],
            "type": "conditional",
            "router": "_builder_router",
            "logic": """
            if has_tool_calls:
                return "tools"  # LLM called write_file/read_file
            elif all_files_exist:
                return "format_tests"  # Files created, validate them
            else:
                return "build"  # Keep building
            """
        },
        {
            "from": "tools",
            "to": ["build", "format_tests"],
            "type": "conditional",
            "router": "_tools_router",
            "logic": """
            if validation_passed is None and all_files_exist:
                return "format_tests"  # Initial creation complete
            elif validation_passed is False:
                return "format_tests"  # Re-validate after fixes
            elif reviewer_passed is False:
                return "format_tests"  # Re-validate after review fixes
            else:
                return "build"  # Continue building
            """
        },
        {
            "from": "format_tests",
            "to": ["build", "validate"],
            "type": "conditional",
            "router": "_format_router",
            "logic": """
            if formatting_errors:
                print("STRICT QUALITY MODE")
                return "build"  # Must fix formatting errors
            else:
                return "validate"  # Formatting OK, proceed to validation
            """
        },
        {
            "from": "validate",
            "to": ["diagnose", "review"],
            "type": "conditional",
            "router": "_validator_router",
            "logic": """
            if validation_passed:
                return "review"  # All tests passed
            else:
                return "diagnose"  # Tests failed, diagnose issues
            """
        },
        {
            "from": "diagnose",
            "to": "build",
            "type": "unconditional",
            "description": "Diagnosis feeds back into build to fix issues"
        },
        {
            "from": "review",
            "to": ["END", "build"],
            "type": "conditional",
            "router": "_review_router",
            "logic": """
            if reviewer_passed and validation_passed:
                return "END"  # Quality approved, complete!
            elif iteration >= MAX_ITERATIONS:
                return "END"  # Hit iteration limit, force stop
            else:
                return "build"  # Address reviewer feedback
            """
        }
    ]

    for edge in edges:
        from_node = edge["from"]
        to_nodes = edge["to"] if isinstance(edge["to"], list) else [edge["to"]]
        edge_type = edge["type"]

        print(f"  {from_node}")
        print(f"    |")

        if edge_type == "unconditional":
            print(f"    -> {to_nodes[0]}")
            print(f"       ({edge['description']})")
        else:
            print(f"    [Router: {edge['router']}]")
            print(f"    Decision logic:")
            for line in edge["logic"].strip().split('\n'):
                print(f"      {line}")
            print(f"    Possible routes:")
            for to_node in to_nodes:
                print(f"      -> {to_node}")

        print()

    print("=" * 80)
    print()

    print("TYPICAL FLOW PATHS:")
    print()

    flows = [
        {
            "name": "Perfect Path (2-3 iterations)",
            "path": "START -> plan -> build -> tools -> format_tests -> validate -> review -> END",
            "description": "Everything works first try"
        },
        {
            "name": "With Validation Errors (3-5 iterations)",
            "path": "START -> plan -> build -> tools -> format_tests -> validate -> diagnose -> build -> tools -> format_tests -> validate -> review -> END",
            "description": "Initial validation fails, fixes applied, re-validates, passes"
        },
        {
            "name": "With Formatting Errors",
            "path": "START -> plan -> build -> tools -> format_tests -> build -> tools -> format_tests -> validate -> review -> END",
            "description": "Format errors detected, fixes applied, re-formats, validates, completes"
        },
        {
            "name": "With Review Feedback",
            "path": "START -> plan -> build -> tools -> format_tests -> validate -> review -> build -> tools -> format_tests -> validate -> review -> END",
            "description": "Review suggests improvements, changes made, re-validates, re-reviews, approved"
        },
        {
            "name": "Maximum Iterations Hit",
            "path": "START -> plan -> build -> ... (repeats) -> END (forced at iteration 100)",
            "description": "Quality issues persist, system stops at MAX_ITERATIONS"
        }
    ]

    for flow in flows:
        print(f"  {flow['name']}")
        print(f"     {flow['path']}")
        print(f"     {flow['description']}")
        print()

    print("=" * 80)
    print()

    print("KEY STATE VARIABLES:")
    print()

    state_vars = {
        "validation_passed": "None (not run) | False (failed) | True (passed)",
        "reviewer_passed": "None (not run) | False (rejected) | True (approved)",
        "iteration": "Current iteration count (0-100)",
        "step_count": "Total graph steps taken (0-200)",
        "formatting_errors": "List of formatting errors from format_tests node",
        "validation_report": "Full output from validator.py",
        "diagnosis": "Analysis and fix instructions from diagnose node",
        "reviewer_feedback": "Feedback and suggestions from review node",
        "messages": "LangChain message history",
        "workspace_dir": "Path to task workspace"
    }

    for var, description in state_vars.items():
        print(f"  - {var:20} -> {description}")

    print()
    print("=" * 80)
    print()

    print("QUALITY ENFORCEMENT POINTS:")
    print()

    quality_checks = [
        "1. format_tests: Validates JSON structure, test count, and REJECTS manual string escaping",
        "2. format_tests: Ensures minimum test counts (public >=5, private >=10)",
        "3. validate: Runs validator.py which checks:",
        "   - JSON compatibility (no tuples, proper types)",
        "   - Test alignment (test.py count must match JSON count)",
        "   - Unittest execution (all tests must pass)",
        "   - JSON test execution (all JSON tests must pass)",
        "4. review: Checks code quality, best practices, and completeness",
        "5. STRICT MODE: NO auto-fixes, NO skipping errors, quality over speed"
    ]

    for check in quality_checks:
        print(f"  {check}")

    print()
    print("=" * 80)
    print()

    print("CONFIGURATION:")
    print(f"  MAX_ITERATIONS: {sidekick.MAX_ITERATIONS}")
    print(f"  MAX_STEPS: {sidekick.MAX_STEPS}")
    print(f"  READY_TOKEN: {sidekick.READY_TOKEN}")
    print()

    print("=" * 80)
    print("Graph visualization complete!")
    print()
    print("OUTPUT FILES:")
    output_dir = Path(__file__).parent
    graph_file = output_dir / "sidekick_graph.png"
    if graph_file.exists():
        print(f"  Visual Graph: {graph_file}")
        print(f"      Open this PNG file to see the visual flow diagram")
    print(f"  Text Output: Displayed above")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(visualize_graph())
