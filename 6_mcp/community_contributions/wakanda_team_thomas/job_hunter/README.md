# Job Hunter

Job Hunter lives inside the parent `agents` repository and uses the parent UV project.

## Notes

- Do not create a separate virtualenv or `pyproject.toml` here.
- Dependencies are managed at the repo root (`/home/gasmyr/AI_SPACE/agents/pyproject.toml`).
- Keep local `.env` in this folder for app-specific runtime configuration.

## Run

From repo root:

```bash
uv run --directory 6_mcp/community_contributions/wakanda_team_thomas/job_hunter streamlit run app/main.py
uv run --directory 6_mcp/community_contributions/wakanda_team_thomas/job_hunter python app.py hunt ~/resume.pdf
uv run --directory 6_mcp/community_contributions/wakanda_team_thomas/job_hunter python -m src.mcp_server.server
uv run --directory 6_mcp/community_contributions/wakanda_team_thomas/job_hunter python -m scheduler.job_scheduler
```
