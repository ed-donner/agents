import json
import re


def safe_json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def extract_tool_call(text):
    """
    Parses:
    [TOOL:record_user_details email=test@test.com name=John]
    """
    match = re.search(r"\[TOOL:(\w+)(.*?)\]", text)
    if not match:
        return None

    tool_name = match.group(1)
    args_str = match.group(2).strip()

    args = {}
    for part in args_str.split():
        if "=" in part:
            k, v = part.split("=", 1)
            args[k] = v.strip('"')

    return tool_name, args
