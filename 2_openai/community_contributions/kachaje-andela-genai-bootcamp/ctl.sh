#!/usr/bin/env bash

if [[ "$1" == "clean" ]]; then

  rm -rf logs/

elif [[ "$1" == "run" ]]; then

  uv run deep_research.py

elif [[ "$1" == "logs" ]]; then

  tail -f logs/traces.jsonl | hl -P

elif [[ "$1" == "test" ]]; then

  uv run pytest tests/ "${@:2}"

else

  echo "Usage: $0 [clean|run|logs|test]"
  echo ""
  echo "Examples:"
  echo "  $0 run        # Run deep research agent"
  echo "  $0 logs       # View logs"
  echo "  $0 clean      # Clean logs"
  echo "  $0 test       # Run all tests"
  exit 1

fi