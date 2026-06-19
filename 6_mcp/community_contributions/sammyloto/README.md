# Agronomy Advisor (MCP)

A small [Model Context Protocol](https://modelcontextprotocol.io/) server for **agronomy scenario planning**: growing degree days (GDD), planting-window hints, soil–water snapshots, crop rotation scores, synthetic pest-pressure bands, and a combined field brief.

All numeric outputs are **illustrative** (synthetic climate curves, toy rotation matrix). They are meant for coursework and agent demos—not farm prescriptions.

## Layout

| File | Role |
|------|------|
| `agronomy_core.py` | Domain logic and reference catalogs (zones, crops, soils). |
| `mcp_server.py` | FastMCP stdio server exposing tools + JSON resources. |
| `app.py` | CLI chat agent that connects to `mcp_server.py` via stdio. |
| `simple_client.py` | Smoke-test client (no LLM). |
| `mcp_params.py` | Ready-made stdio params for agent frameworks. |

## Run the chat app

Set `OPENAI_API_KEY`, then from this directory:

```bash
python app.py
```

Optional: `OPENAI_MODEL` (default `gpt-4o-mini`).

## Run the MCP server alone

```bash
python mcp_server.py
```

## Smoke test (no LLM)

```bash
python simple_client.py
```

## Tools (summary)

- **compute_gdd_sum** — Sum GDD over a date range for a zone + crop.
- **planting_window_hint** — Heuristic starting month vs rainy seasons.
- **soil_water_snapshot** — Rough stress band from rain, ET₀, soil texture, and rooting depth.
- **crop_rotation_score** — Toy compatibility score between two crops.
- **pest_risk_band** — Seasonal synthetic index for planning conversations.
- **nutrient_placeholder** — Placeholder NPK commentary (always validate with soil tests).
- **integrated_field_brief** — One-shot summary for a notional field.

Resources: `agronomy://catalog/crops`, `agronomy://catalog/zones`.

## Requirements

See `requirements.txt` (`mcp`).
