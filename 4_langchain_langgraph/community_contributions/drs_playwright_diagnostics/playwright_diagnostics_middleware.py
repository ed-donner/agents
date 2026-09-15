from langchain.agents.middleware import wrap_tool_call

@wrap_tool_call
async def diagnose_browser_calls(request, handler):
    call = request.tool_call
    print(f"  [tool] {call['name']}({call['args']})")

    if call["name"] == "browser_evaluate":
        probe = await request.tool.ainvoke({"function": "() => location.href"})
        print(f"  [tool]   current page before evaluate: {getattr(probe, 'content', probe)}")

    result = await handler(request)

    status = getattr(result, "status", None)
    content = getattr(result, "content", result)
    if status == "error":
        print(f"  [tool] {call['name']} FAILED: {content}")
    return result
