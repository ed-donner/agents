This example, shows instrumentation using OpenLMMetry. With this auto instrucmentation you get for 'free' attributes which aling with https://opentelemetry.io/docs/specs/semconv/gen-ai/ Makes it easier when using multi-LLMs as you have a consistent set of attributes to query from. 


Uses a local otel collector which forwards to Dynatrace as the backend

>>pip3 install traceloop-sdk

1. set the .env file with the otel endpoint and Dynatrace API token
2. run deep-research.py
3. open Dynatrace and view Distributed Traces app; the traces from the llm calls will be shown
>example: ../dynatrace-trace.png

misc:
https://www.linkedin.com/in/jason-godbold-smith-4788a515b/

--Dynatrace trial environment: https://www.dynatrace.com/signup/
--Authentication is handled using an API access token and the Authorization HTTP header. For more information on access tokens, see Dynatrace API - Tokens and authentication.
---scope: ingest traces, logs + metrics