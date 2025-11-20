#!/usr/bin/env python3
"""
Assertion MCP Server - Python Implementation
Provides assertion and validation tools for BDD testing
"""

import asyncio
import json
import re
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Create MCP server instance
app = Server("assertion-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available assertion tools"""
    return [
        Tool(
            name="assert_equals",
            description="Assert that two values are equal. Returns success or failure with details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actual": {
                        "type": "string",
                        "description": "The actual value to compare"
                    },
                    "expected": {
                        "type": "string",
                        "description": "The expected value"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["actual", "expected"]
            }
        ),
        Tool(
            name="assert_contains",
            description="Assert that text contains a substring. Case-sensitive by default.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to search in"
                    },
                    "substring": {
                        "type": "string",
                        "description": "The substring to find"
                    },
                    "caseSensitive": {
                        "type": "boolean",
                        "description": "Whether the search is case-sensitive (default: true)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["text", "substring"]
            }
        ),
        Tool(
            name="assert_not_contains",
            description="Assert that text does NOT contain a substring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to search in"
                    },
                    "substring": {
                        "type": "string",
                        "description": "The substring that should not be present"
                    },
                    "caseSensitive": {
                        "type": "boolean",
                        "description": "Whether the search is case-sensitive (default: true)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["text", "substring"]
            }
        ),
        Tool(
            name="assert_count",
            description="Assert that a count matches the expected value.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actual": {
                        "type": "number",
                        "description": "The actual count"
                    },
                    "expected": {
                        "type": "number",
                        "description": "The expected count"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["actual", "expected"]
            }
        ),
        Tool(
            name="assert_greater_than",
            description="Assert that actual value is greater than expected value.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actual": {
                        "type": "number",
                        "description": "The actual value"
                    },
                    "expected": {
                        "type": "number",
                        "description": "The value that actual should be greater than"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["actual", "expected"]
            }
        ),
        Tool(
            name="assert_less_than",
            description="Assert that actual value is less than expected value.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actual": {
                        "type": "number",
                        "description": "The actual value"
                    },
                    "expected": {
                        "type": "number",
                        "description": "The value that actual should be less than"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["actual", "expected"]
            }
        ),
        Tool(
            name="assert_true",
            description="Assert that a condition is true.",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "boolean",
                        "description": "The condition to check"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["condition"]
            }
        ),
        Tool(
            name="assert_false",
            description="Assert that a condition is false.",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "boolean",
                        "description": "The condition to check"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["condition"]
            }
        ),
        Tool(
            name="assert_matches_regex",
            description="Assert that text matches a regular expression pattern.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to match against"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "The regex pattern to match"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional custom failure message"
                    }
                },
                "required": ["text", "pattern"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool execution"""
    
    try:
        if name == "assert_equals":
            actual = arguments.get("actual", "")
            expected = arguments.get("expected", "")
            message = arguments.get("message")
            
            passed = actual == expected
            result = {
                "passed": passed,
                "assertion": "assert_equals",
                "actual": actual,
                "expected": expected,
                "message": "Assertion passed: Values are equal" if passed else 
                          (message or f'Expected "{expected}" but got "{actual}"')
            }
            
        elif name == "assert_contains":
            text = arguments.get("text", "")
            substring = arguments.get("substring", "")
            case_sensitive = arguments.get("caseSensitive", True)
            message = arguments.get("message")
            
            search_text = text if case_sensitive else text.lower()
            search_substring = substring if case_sensitive else substring.lower()
            passed = search_substring in search_text
            
            result = {
                "passed": passed,
                "assertion": "assert_contains",
                "text": text,
                "substring": substring,
                "caseSensitive": case_sensitive,
                "message": f'Assertion passed: Text contains "{substring}"' if passed else
                          (message or f'Expected text to contain "{substring}" but it was not found')
            }
            
        elif name == "assert_not_contains":
            text = arguments.get("text", "")
            substring = arguments.get("substring", "")
            case_sensitive = arguments.get("caseSensitive", True)
            message = arguments.get("message")
            
            search_text = text if case_sensitive else text.lower()
            search_substring = substring if case_sensitive else substring.lower()
            passed = search_substring not in search_text
            
            result = {
                "passed": passed,
                "assertion": "assert_not_contains",
                "text": text,
                "substring": substring,
                "caseSensitive": case_sensitive,
                "message": f'Assertion passed: Text does not contain "{substring}"' if passed else
                          (message or f'Expected text NOT to contain "{substring}" but it was found')
            }
            
        elif name == "assert_count":
            actual = arguments.get("actual", 0)
            expected = arguments.get("expected", 0)
            message = arguments.get("message")
            
            passed = actual == expected
            result = {
                "passed": passed,
                "assertion": "assert_count",
                "actual": actual,
                "expected": expected,
                "message": f"Assertion passed: Count is {expected}" if passed else
                          (message or f"Expected count {expected} but got {actual}")
            }
            
        elif name == "assert_greater_than":
            actual = arguments.get("actual", 0)
            expected = arguments.get("expected", 0)
            message = arguments.get("message")
            
            passed = actual > expected
            result = {
                "passed": passed,
                "assertion": "assert_greater_than",
                "actual": actual,
                "expected": expected,
                "message": f"Assertion passed: {actual} > {expected}" if passed else
                          (message or f"Expected {actual} to be greater than {expected}")
            }
            
        elif name == "assert_less_than":
            actual = arguments.get("actual", 0)
            expected = arguments.get("expected", 0)
            message = arguments.get("message")
            
            passed = actual < expected
            result = {
                "passed": passed,
                "assertion": "assert_less_than",
                "actual": actual,
                "expected": expected,
                "message": f"Assertion passed: {actual} < {expected}" if passed else
                          (message or f"Expected {actual} to be less than {expected}")
            }
            
        elif name == "assert_true":
            condition = arguments.get("condition", False)
            message = arguments.get("message")
            
            passed = condition is True
            result = {
                "passed": passed,
                "assertion": "assert_true",
                "condition": condition,
                "message": "Assertion passed: Condition is true" if passed else
                          (message or "Expected condition to be true but it was false")
            }
            
        elif name == "assert_false":
            condition = arguments.get("condition", True)
            message = arguments.get("message")
            
            passed = condition is False
            result = {
                "passed": passed,
                "assertion": "assert_false",
                "condition": condition,
                "message": "Assertion passed: Condition is false" if passed else
                          (message or "Expected condition to be false but it was true")
            }
            
        elif name == "assert_matches_regex":
            text = arguments.get("text", "")
            pattern = arguments.get("pattern", "")
            message = arguments.get("message")
            
            try:
                regex = re.compile(pattern)
                passed = bool(regex.search(text))
            except re.error as e:
                passed = False
                result = {
                    "passed": False,
                    "assertion": "assert_matches_regex",
                    "text": text,
                    "pattern": pattern,
                    "message": f"Invalid regex pattern: {e}"
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            result = {
                "passed": passed,
                "assertion": "assert_matches_regex",
                "text": text,
                "pattern": pattern,
                "message": f'Assertion passed: Text matches pattern "{pattern}"' if passed else
                          (message or f'Expected text to match pattern "{pattern}"')
            }
            
        else:
            result = {
                "passed": False,
                "error": f"Unknown tool: {name}"
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        error_result = {
            "passed": False,
            "error": str(e)
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def main():
    """Main entry point - start the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
