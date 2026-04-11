This example, shows manual instrumentation of the varying llm calls using manual wrapper around the llm calls.
Uses a local otel collector which forwards to Dynatrace as the backend

1. set the .env file with the otel endpoint and Dynatrace API token
2. run, from with this folder - requires the docker-compose.yml file
>>docker compose up 
3. run deep-research.py
4. open Dynatrace and view Distributed Traces app; the traces from the llm calls will be shown
>example: ../dynatrace-trace.png

misc:
https://www.linkedin.com/in/jason-godbold-smith-4788a515b/
Dynatrace trial environment: https://www.dynatrace.com/signup/