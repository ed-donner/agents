import asyncio

from autogen_core import AgentId, SingleThreadedAgentRuntime
from dotenv import load_dotenv

import agents
import messages

load_dotenv(override=True)

MONITOR_INTERVAL_SECONDS = 30  # How often to run a monitoring cycle
MONITOR_CYCLES = 3  # How many monitoring cycles to run, set to None to loop forever

async def main():
    agents.runtime = SingleThreadedAgentRuntime()
    await agents.MonitoringAgent.register(
        agents.runtime, "monitoring_agent",
        lambda: agents.MonitoringAgent("monitoring_agent")
    )
    await agents.TriageAgent.register(
        agents.runtime, "triage_agent",
        lambda: agents.TriageAgent("triage_agent")
    )
    await agents.HumanProxyAgent.register(
        agents.runtime, "human_proxy_agent",
        lambda: agents.HumanProxyAgent("human_proxy_agent")
    )
    await agents.FixerAgent.register(
        agents.runtime, "fixer_agent",
        lambda: agents.FixerAgent("fixer_agent")
    )

    agents.runtime.start()

    cycle = 0
    while MONITOR_CYCLES is None or cycle < MONITOR_CYCLES:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"  Monitoring cycle {cycle}")
        print(f"{'='*60}")

        result = await agents.runtime.send_message(
            messages.MonitorRequest(),
            AgentId("orchestrator", "default"),
        )

        print(f"\n[Result] severity={result.severity} | {result.outcome}")

        if MONITOR_CYCLES is None or cycle < MONITOR_CYCLES:
            print(f"\nNext check in {MONITOR_INTERVAL_SECONDS}s... (Ctrl+C to stop)")
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

    await agents.runtime.stop_when_idle()
    print("\nDone. Check logs/incidents.log for the full incident record.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped.")