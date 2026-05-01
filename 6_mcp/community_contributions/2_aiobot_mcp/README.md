# AIObot Community Edition

AI activity assistant that suggests activities based on real-time weather (via MCP) and local events (via Ticketmaster API).

**Live Demo:** [http://aiobot.lisekarimi.com](http://aiobot.lisekarimi.com)

## What It Does

- Fetches weather via **MCP (Model Context Protocol)** using [@swonixs/weatherapi-mcp](https://github.com/swonixs/weatherapi-mcp)
- Searches events via **Ticketmaster API** (US, CA, GB, AU, AE, NO, NZ)
- Generates activity suggestions using **OpenAI Agents SDK**
- **Gradio** web interface

## Prerequisites

- Python 3.11.x
- [uv](https://github.com/astral-sh/uv) package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- make (optional)

## Quick Start

### 1. Setup API Keys

Get keys from:
- [OpenAI](https://platform.openai.com/api-keys)
- [Ticketmaster](https://developer.ticketmaster.com/)
- [WeatherAPI](https://www.weatherapi.com/)

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run in Docker

```bash
uv lock
cd 6_mcp/03_aiobot_mcp
make dev
```

Access at http://localhost:7860


## Usage

Try: "What can I do in Paris this weekend?" or "Suggest activities in London tomorrow"
