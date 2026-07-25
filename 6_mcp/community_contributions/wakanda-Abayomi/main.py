import ast
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

import gradio as gr
from agents import Agent, OpenAIChatCompletionsModel, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)

_PROJECT_ROOT = Path(__file__).resolve().parent
_SUBPROCESS_ENV = {k: v for k, v in os.environ.items() if v is not None}

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-4o-mini"
cache: dict[str, object] = {}

instructions = """
You are a financial research assistant with MCP tools for live FX data and search.

CRITICAL: Your final message MUST be a single JSON object only (no markdown fences, no preamble).
Use this exact shape (strings or numbers are fine for rate fields):
{
  "pair": "BASE/TARGET",
  "rate": "<spot: how many TARGET units per 1 BASE>",
  "inverse": "<how many BASE per 1 TARGET>",
  "insight": "<short markdown overview: tables for spot + inverse, market factors, sources/date>",
  "trade_idea": "<one concise actionable trade thesis, not UNKNOWN>"
}

Populate rate and inverse from MCP tools when possible; never leave them as literal "N/A" if you have numbers.
"""

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

client_model = OpenAIChatCompletionsModel(
    model=MODEL,
    openai_client=client,
)

search_params: dict = {
    "command": "uvx",
    "args": ["serper-mcp-server"],
    "cwd": str(_PROJECT_ROOT),
    "env": _SUBPROCESS_ENV,
}

exchange_rate_params: dict = {
    "command": sys.executable,
    "args": [str(_PROJECT_ROOT / "mcp_exchange_rate.py")],
    "cwd": str(_PROJECT_ROOT),
    "env": _SUBPROCESS_ENV,
}

forex_server: MCPServerStdio | None = None
search_server: MCPServerStdio | None = None
agent: Agent | None = None


# --- Output parsing


def _strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _try_parse_json_object(blob: str) -> dict | None:
    blob = blob.strip()
    if not blob:
        return None
    try:
        data = json.loads(blob)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
    # Last JSON object in text
    start = blob.rfind("{")
    end = blob.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(blob[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
    return None


def _extract_rates_from_text(text: str, base: str, target: str) -> tuple[str | None, str | None]:
    """Parse markdown/plain tables like | USD | EUR | 0.8638 | or USD | EUR | 0.8638."""
    if not text:
        return None, None
    b, t = base.strip().upper(), target.strip().upper()
    rate: str | None = None
    inv: str | None = None

    patterns_fwd = [
        rf"\|\s*{re.escape(b)}\s*\|\s*{re.escape(t)}\s*\|\s*([0-9][0-9.,]*)\s*\|",
        rf"\b{re.escape(b)}\s*\|\s*{re.escape(t)}\s*\|\s*([0-9][0-9.,]*)",
        rf"{re.escape(b)}\s+{re.escape(t)}\s+([0-9][0-9.,]*)",
    ]
    for p in patterns_fwd:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            rate = m.group(1).replace(",", "")
            break

    patterns_inv = [
        rf"\|\s*{re.escape(t)}\s*\|\s*{re.escape(b)}\s*\|\s*([0-9][0-9.,]*)\s*\|",
        rf"\b{re.escape(t)}\s*\|\s*{re.escape(b)}\s*\|\s*([0-9][0-9.,]*)",
        rf"{re.escape(t)}\s+{re.escape(b)}\s+([0-9][0-9.,]*)",
    ]
    for p in patterns_inv:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            inv = m.group(1).replace(",", "")
            break

    def _inv_from_r(x: str) -> str:
        v = float(x)
        if v == 0:
            raise ValueError
        return f"{1.0 / v:.6g}"

    try:
        if rate and not inv:
            inv = _inv_from_r(rate)
        elif inv and not rate:
            rate = _inv_from_r(inv)
    except (ValueError, ZeroDivisionError, OverflowError):
        pass

    return rate, inv


def _extract_trade_section(text: str) -> str | None:
    if not text:
        return None
    m = re.search(
        r"(?:^|\n)\s*(?:#{1,3}\s*)?(?:Trade\s+(?:Recommendations?|Idea|Idea[s])|Recommendation)\b[^\n]*\n+([\s\S]{10,4000}?)"
        r"(?=(?:\n#{1,3}\s)|(?:\n\*\*[A-Z])|\n\n-{3,}|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if m:
        return m.group(1).strip()
    m2 = re.search(
        r"(?:Short-term|Long-term)\s*[:\-].{20,1500}",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m2:
        return m2.group(0).strip()[:2000]
    return None


def parse_agent_fx_result(final_output: str, base: str, target: str) -> dict:
    """Normalize agent output into pair, rate, inverse, insight, trade_idea."""
    raw = final_output or ""
    stripped = _strip_json_fence(raw)
    parsed = _try_parse_json_object(stripped) or _try_parse_json_object(raw)

    pair = f"{base.upper()}/{target.upper()}"
    rate_s: str | None = None
    inv_s: str | None = None
    insight = raw
    trade: str | None = None

    if parsed:
        rate_s = parsed.get("rate")
        inv_s = parsed.get("inverse")
        insight = str(parsed.get("insight") or raw)
        trade = parsed.get("trade_idea") or parsed.get("trade_recommendation")
        pair = str(parsed.get("pair") or pair)
        if rate_s is not None:
            rate_s = str(rate_s).strip()
        if inv_s is not None:
            inv_s = str(inv_s).strip()
        if trade is not None:
            trade = str(trade).strip()

    if rate_s in (None, "", "N/A", "n/a") or inv_s in (None, "", "N/A", "n/a"):
        hr, hi = _extract_rates_from_text(raw, base, target)
        if rate_s in (None, "", "N/A", "n/a") and hr:
            rate_s = hr
        if inv_s in (None, "", "N/A", "n/a") and hi:
            inv_s = hi

    if trade in (None, "", "UNKNOWN", "unknown"):
        trade = _extract_trade_section(raw) or _extract_trade_section(insight)

    if not rate_s:
        rate_s = "N/A"
    if not inv_s:
        inv_s = "N/A"
    if not trade:
        trade = "See **Trade Recommendations** in the market insight below."

    return {
        "pair": pair,
        "rate": rate_s,
        "inverse": inv_s,
        "insight": insight,
        "trade_idea": trade,
    }


async def init_forex_server() -> None:
    global forex_server
    if forex_server is not None:
        return
    fs = MCPServerStdio(params=exchange_rate_params, client_session_timeout_seconds=60)
    await fs.__aenter__()
    forex_server = fs


async def init_search_server() -> None:
    global search_server
    if search_server is not None:
        return
    ss = MCPServerStdio(params=search_params, client_session_timeout_seconds=60)
    await ss.__aenter__()
    search_server = ss


async def init_agent() -> None:
    global agent
    await init_forex_server()
    await init_search_server()
    if agent is None:
        agent = Agent(
            name="fx_pro_agent",
            instructions=instructions,
            model=client_model,
            mcp_servers=[search_server, forex_server],
        )


@lru_cache(maxsize=1)
def get_fallback_currencies() -> list[str]:
    return ["USD", "EUR", "GBP", "AUD", "JPY", "CAD", "NGN", "CHF", "NZD"]


async def fetch_supported_currencies() -> list[str]:
    try:
        await init_forex_server()
        res = await forex_server.call_tool("list_supported_currencies", {})  # type: ignore[union-attr]
        for block in getattr(res, "content", None) or []:
            text = getattr(block, "text", None)
            if not text:
                continue
            data = None
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    continue
            if isinstance(data, list):
                return sorted(str(x) for x in data)
    except Exception as e:
        print(f"Currency list from MCP failed: {e}")
    return list(get_fallback_currencies())


async def run_agent(base_currency: str, target_currency: str) -> dict:
    key = f"{base_currency}/{target_currency}"
    if key in cache:
        return cache[key]  # type: ignore[return-value]

    await init_agent()
    assert agent is not None

    request = f"""
Using MCP tools, produce the JSON object specified in your instructions for {base_currency}/{target_currency}.
Use lookup_exchange_rate / search as needed. Rates must be numeric in rate and inverse fields when available.
"""

    result = await Runner.run(agent, request, max_turns=20)
    final = result.final_output or ""
    parsed = parse_agent_fx_result(final, base_currency, target_currency)

    cache[key] = parsed
    return parsed


def format_output(raw_output: dict | str, selected_currency: str) -> str:
    if isinstance(raw_output, dict):
        pair = raw_output.get("pair", selected_currency)
        rate = raw_output.get("rate", "N/A")
        inv = raw_output.get("inverse", "N/A")
        trade = raw_output.get("trade_idea", "")
        insight = raw_output.get("insight", "")
        if not isinstance(insight, str):
            insight = json.dumps(insight, indent=2)
        raw_json = json.dumps(raw_output, indent=2, ensure_ascii=False)
    else:
        pair = selected_currency
        rate = inv = "N/A"
        trade = ""
        insight = str(raw_output)
        raw_json = insight

    summary = f"""# FX Intelligence Dashboard

## Pair: {pair}

| | |
|:--|:--|
| **Forward rate** | **{rate}** ({pair.split("/")[0] if "/" in str(pair) else ""} → {selected_currency}) |
| **Inverse** | **{inv}** |

## Trade idea

{trade}

## Market insight

{insight}
"""

    pattern = rf"{re.escape(selected_currency)}.*?(?=\n## |\n### |\Z)"
    match = re.search(pattern, insight, re.IGNORECASE | re.DOTALL)
    focused = f"\n### Focus: {selected_currency}\n\n{match.group(0).strip()}\n" if match else ""

    return f"""{summary}{focused}
---
<details>
<summary>Full structured data (JSON)</summary>

```json
{raw_json}
```
</details>
"""


async def run_dashboard(base_currency: str, target_currency: str) -> str:
    parsed = await run_agent(base_currency, target_currency)
    return format_output(parsed, target_currency)


async def populate_dropdowns():
    try:
        sorted_codes = await fetch_supported_currencies()
        return (
            gr.update(choices=sorted_codes, value="USD"),
            gr.update(choices=sorted_codes, value="EUR"),
        )
    except Exception as e:
        print(f"Failed to load UI currencies: {e}")
        fallback = list(get_fallback_currencies())
        return (
            gr.update(choices=fallback, value="USD"),
            gr.update(choices=fallback, value="EUR"),
        )


with gr.Blocks() as app:
    gr.Markdown("""
    # AI-Powered FX Intelligence Dashboard
    ### Direct Pair Analysis via MCP + Agent
    """)

    with gr.Row():
        base_currency = gr.Dropdown(
            choices=["USD"],
            value="USD",
            label="Base (From)",
            interactive=True,
        )
        target_currency = gr.Dropdown(
            choices=["EUR"],
            value="EUR",
            label="Target (To)",
            interactive=True,
        )

    output = gr.Markdown()
    run_btn = gr.Button("Run Analysis", variant="primary")

    app.load(fn=populate_dropdowns, inputs=None, outputs=[base_currency, target_currency])

    run_btn.click(
        fn=run_dashboard,
        inputs=[base_currency, target_currency],
        outputs=output,
    )


if __name__ == "__main__":
    app.launch(inbrowser=True, theme=gr.themes.Soft())
