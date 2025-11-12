#!/bin/bash
echo "Starting MCP mini servers..."
uvicorn accounts_server:app --port 8001 --reload &
uvicorn quotes_server:app --port 8002 --reload &
sleep 2
echo "Starting Trader Agent..."
python trader_agent.py

