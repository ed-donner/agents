# CrewAI Trading Strategy Generator

Full project:
https://github.com/sirknigget/crewai-trading-strategy

An AI-powered cryptocurrency trading strategy generator that uses multiple AI agents to research, design, and implement profitable trading strategies. Built with [CrewAI](https://crewai.com), this project leverages a multi-agent system to automatically create, backtest, and iterate on trading strategies for Bitcoin.

## 🎯 Purpose

This project demonstrates a sophisticated AI workflow that:

- **Researches** historical cryptocurrency price data to identify profitable trading patterns
- **Designs** detailed technical specifications for trading strategy implementations
- **Implements** self-contained Python trading strategies following strict API guidelines
- **Backtests** strategies against historical data to validate performance
- **Iterates** automatically to improve strategy profitability across multiple attempts

The system uses three specialized AI agents working in sequence: a Strategy Researcher, an Engineering Lead, and a Senior Developer, each with specific expertise to ensure high-quality trading strategy development.

## 🏗️ Architecture Overview

### Multi-Agent Workflow

The project employs a **CrewAI Flow** architecture with three specialized agents:

1. **Strategy Researcher Agent** (`strategy_researcher`)

   - Role: Senior crypto trading strategy researcher
   - Goal: Analyze daily cryptocurrency data and define profitable trading strategies
   - Tools: Historical price data analysis, custom code execution on datasets
   - Output: Trading strategy outline document
2. **Engineering Lead Agent** (`engineering_lead`)

   - Role: Senior engineering lead
   - Goal: Create detailed technical designs for strategy implementation
   - Input: Strategy outline from researcher
   - Output: Comprehensive design document with pseudocode and API specifications
3. **Developer Agent** (`developer`)

   - Role: Senior Python developer
   - Goal: Implement trading strategies based on engineering designs
   - Input: Design document from engineering lead
   - Output: Production-ready Python code following strict API guidelines

### What Happens During Execution

1. **Iteration Loop**: The flow runs up to 3 attempts (configurable via `MAX_ATTEMPTS`)
2. **Each Iteration**:
   - Strategy Researcher analyzes BTC historical data
   - Engineering Lead creates detailed design
   - Developer implements the strategy
   - Strategy is backtested automatically
   - Results are logged and fed into the next iteration
3. **Output**: All attempts are saved, and the best-performing strategy is selected
4. **Results**: Check the `output/` directory for:
   - Strategy outlines and designs
   - Implementation code
   - Backtest results
   - Full attempts log (JSON)
