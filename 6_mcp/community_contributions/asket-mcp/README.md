# Asket MCP — Personal Study Brain (v3.1)

MCP server + optional **Streamlit** UI for a **local-first study workflow**: an allow-listed **Brain folder** (Markdown), **semantic memory** (ChromaDB on disk + OpenAI embeddings), **public web fetch**, **SQLite scratch notes**, optional **Pushover**, and **time** in any IANA timezone. Built with **FastMCP** (aligned with the `6_mcp` course—**not** a trading stack).

**Privacy framing:** Brain files and Chroma indices stay **on your machine**. **`semantic_memory_*`**, **`ask_the_brain`**, **`greet_and_assess`**, and embeddings use the **OpenAI API** when `OPENAI_API_KEY` is set — content you embed or send in those calls is transmitted to OpenAI per their policies.

## Fits this mental model

- **Brain = your library** — `brain_*` tools for Markdown under the configured folder only.
- **Semantic memory** — ingest passages with `semantic_memory_ingest_*`; search by meaning with `semantic_memory_search`; **`ask_the_brain`** for RAG (retrieve + GPT).
- **Learner profile** — **`study_profile_get` / `study_profile_update`** and **`greet_and_assess`** (coach blurb from profile).
- **Overwrite / delete are gated** — `brain_write_markdown(..., overwrite=true)` and `brain_delete_file(..., user_confirmed_deletion=true)` only after approval; same for `note_delete`.
- **Web** — `fetch_public_page` for public http(s) text (size capped; not a full browser).
- **Scratch** — `note_*` tools use SQLite under `ASKET_MCP_DATA_DIR`.

## Tools (summary)

| Area | Tools |
|------|--------|
| Brain | `brain_read_file`, `brain_write_markdown`, `brain_list_files`, `brain_find_markdown_files`, `brain_search_notes`, `brain_delete_file` |
| Semantic | `semantic_memory_ingest_text`, `semantic_memory_ingest_brain_file`, `semantic_memory_ingest_url`, `semantic_memory_search`, `ask_the_brain` |
| Profile / coach | `study_profile_get`, `study_profile_update`, `greet_and_assess` |
| Web | `fetch_public_page` |
| Time | `current_time` |
| Notify | `send_push` (Pushover) |
| Scratch DB | `note_create`, `note_list`, `note_read`, `note_delete` |
| Meta | `asket_info` |

## Quick start (stdio — Cursor, Claude Desktop, etc.)

From the **agents** repository root (this course layout):

```bash
cd 6_mcp/community_contributions/asket-mcp
```

If you are **already inside** the `6_mcp` folder:

```bash
cd community_contributions/asket-mcp
```

Then:

```bash
uv sync --extra semantic
uv run asket-mcp
```

Set variables in a `.env` file in this directory and/or in your shell (`Settings` in `asket_mcp/config.py` lists names). Typical entries include `PERSONAL_STUDY_BRAIN_DIR`, `ASKET_MCP_DATA_DIR`, and `OPENAI_API_KEY` for semantic tools.

`uv run asket-mcp` uses **stdio** and waits for an MCP client (Cursor, etc.). **Ctrl+C** ends the process; stack traces from `CancelledError` on shutdown are normal.

- **MCP only + semantic:** `uv sync --extra semantic`
- **Streamlit UI:** include **`streamlit`** — `uv sync --extra ui --extra semantic` (or one-shot **`uv sync --extra all`** for UI + semantic together).

Minimal install **without** OpenAI/Chroma: `uv sync` — semantic tools return a clear install/config error until you add `--extra semantic` and `OPENAI_API_KEY`.

Example **Cursor** `mcp.json` snippet (adjust absolute paths):

```json
{
  "mcpServers": {
    "personal-study-brain": {
      "command": "uv",
      "args": ["run", "asket-mcp"],
      "cwd": "/absolute/path/to/community_contributions/asket-mcp",
      "env": {
        "ASKET_MCP_DATA_DIR": "/absolute/path/to/community_contributions/asket-mcp/data",
        "PERSONAL_STUDY_BRAIN_DIR": "/absolute/path/to/your/PersonalStudyBrain"
      }
    }
  }
}
```

## Streamlit web UI (same Brain / fetch / notes / Push)

Browser dashboard over the **same Python APIs** as MCP (does not speak MCP wire protocol). Layout is implemented in **`asket_mcp/ui/streamlit_app.py`**; shared handlers in **`asket_mcp/ui/handlers.py`**.

```bash
uv sync --extra ui --extra semantic
uv run asket-mcp-ui
```

The launcher runs **`streamlit run`** on **port `ASKET_UI_PORT`** (default **7860**) and **`ASKET_UI_HOST`** (default **127.0.0.1**). Open the URL Streamlit prints. Set **`ASKET_UI_HOST=0.0.0.0`** only if you expose it on a LAN and understand the risk. **`PERSONAL_STUDY_BRAIN_DIR`** and **`ASKET_MCP_DATA_DIR`** apply here too.

You get **Study partner** (chat + optional uploads), **Learning roadmap / Knowledge map / Scratch notes** in a second column, and a **More tools** expander for full notes, fetch, Brain, batch semantic ingest, alerts, and help. Chat supports **.txt, .md, .csv, .pdf, .docx** (PDF/Word via **`pypdf`**, **`python-docx`** in the `ui` extra). Semantic / coach flows need **`OPENAI_API_KEY`** and `uv sync --extra semantic` where noted.

**Launch / proxy:** The launcher still merges **loopback** into **`NO_PROXY` / `no_proxy`** so local tooling and fetches behave behind corporate proxies. **TLS:** terminate HTTPS at a reverse proxy (recommended) or use Streamlit’s own SSL flags in a custom `streamlit run` invocation; `ASKET_UI_SSL_*` env vars are validated but full TLS pass-through in the launcher is not implemented—use a proxy in production.

**Manual run:** `uv run streamlit run asket_mcp/ui/streamlit_app.py --server.port=7860`

## Production checklist

- **Secrets**: never commit real `.env` files; protect the Streamlit port (firewall / reverse-proxy auth) when the UI is reachable beyond localhost.
- **Network**: prefer **TLS** at a reverse proxy (Caddy, nginx, Traefik) in front of Streamlit. The MCP HTTP transports (`sse`, `streamable-http`) should sit behind the same kind of protection if exposed on the internet.
- **Binding**: `ASKET_UI_HOST=0.0.0.0` and `ASKET_MCP_HOST=0.0.0.0` log warnings when there is no matching UI auth or when MCP is wide-open — treat that as a reminder to add a firewall or proxy auth.
- **Paths**: use **absolute** `PERSONAL_STUDY_BRAIN_DIR` and `ASKET_MCP_DATA_DIR` on servers so the process does not depend on the current working directory.
- **Docker**: the image runs as **UID 10001**. Named volumes work as-is; for **bind mounts**, ensure `/data` (and any Brain path) are writable by that UID or adjust ownership (`chown -R 10001:10001 …` on the host paths you mount).
- **Operational**: set `ASKET_MCP_LOG_LEVEL=INFO` (or `WARNING`) on shared systems.

Additional environment variables are defined on **`Settings`** in `asket_mcp/config.py` (optional UI/TLS keys, aliases for older installs).

## Docker (SSE / streamable-http + optional UI)

```bash
docker compose up --build
```

Compose runs two services:

- **`asket-mcp`** — MCP on **8765** (default `ASKET_MCP_TRANSPORT=sse`), volume **`/data`**.
- **`asket-mcp-ui`** — Streamlit on **7860**, same volume so notes and Brain data align.

Override `PERSONAL_STUDY_BRAIN_DIR` (default inside the stack: `/data/brain`). For auth in front of Streamlit, use your reverse proxy or a Streamlit auth extension; `ASKET_UI_AUTH_*` env vars are not wired into the Streamlit app.

The image installs **`.[ui,semantic]`** (Streamlit + Chroma + OpenAI client). Exposes **8765** and **7860**, and defines a **HEALTHCHECK** on the MCP port. Pass **`OPENAI_API_KEY`** via environment or secrets at runtime for semantic features. The process user is **non-root** (see production checklist for bind mounts).

## License

MIT (community contribution).
