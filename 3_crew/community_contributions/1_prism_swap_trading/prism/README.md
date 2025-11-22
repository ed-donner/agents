# 💹 PRISM - Position Risk Intelligence & Swap Monitor

AI-powered swap trading monitoring system using CrewAI multi-agent framework.

**🌐 Live Demo:** [prism.lisekarimi.com](https://prism.lisekarimi.com)

![PRISM Dashboard](https://github.com/lisekarimi/prism/blob/main/assets/screenshot.png?raw=true)

## 📊 What It Does

PRISM monitors USD SOFR swap trading positions in real-time and automatically generates trading signals when profit/loss thresholds are hit.

**Note:** This demo is specifically configured for USD SOFR (Secured Overnight Financing Rate) swaps only.

## 🏗️ Architecture

![PRISM Workflow](https://github.com/lisekarimi/prism/blob/main/assets/workflow.png?raw=true)

**5 AI Agents working together:**

1. **Market Data Agent** - Fetches current USD SOFR swap rates (2Y, 5Y, 10Y, 30Y)
2. **Position Manager Agent** - Loads trader's swap positions from database
3. **Risk Manager Agent** - Analyzes market conditions and sets dynamic profit/loss thresholds
4. **Risk Calculator Agent** - Calculates P&L for each position
5. **Trading Decision Agent** - Generates CLOSE/HOLD signals based on thresholds

**Thresholds:**
- Close position when profit ≥ $50K
- Close position when loss ≤ -$25K
- Otherwise HOLD

## 🛠️ Tech Stack

- **CrewAI** - Multi-agent orchestration
- **PostgreSQL** - Position & rate storage (Neon)
- **Python 3.11** - Runtime



## 📋 Pre-requisites

- PostgreSQL database (you can use https://neon.com/ which is free)
- OpenAI API key for LLM
- Serper API key from https://serper.dev/ for Google Search API

## 📥 Installation Instructions

1. **Install CrewAI**
   ```bash
   uv tool install crewai
   ```

2. **Set Up Environment**:
   - Copy the `.env.example` to `.env` and fill in the required environment variables for The crew prism project

If you want to access the full codebase with Gradio web dashboard and Docker support, clone the original repository:
   ```bash
   git clone https://github.com/lisekarimi/prism.git
   cd prism
   ```

## 🚀 Quick Start

Run the crew directly:
   ```bash
   uv sync
   cd .cd .\3_crew\community_contributions\1_prism_swap_trading\prism\
   crewai run
   ```

## 🗄️ Database Schema

- `swap_positions` - Trader's swap portfolio
- `market_rates` - Historical rate data
- `trade_signals` - AI-generated trading decisions
