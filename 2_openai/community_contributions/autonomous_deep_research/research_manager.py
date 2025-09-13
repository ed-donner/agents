from agents import Runner, trace
from manager_agent import manager_agent


class ResearchManager:

    async def run(self, query: str):
        with trace("Autonomous manager") as t:
            notifications = []
            final_output = ""    
            result = Runner.run_streamed(manager_agent, query)
            async for event in result.stream_events():
                if event.type == "raw_response_event": #and isinstance(event.data, ResponseTextDeltaEvent):
                    continue            
                # When the agent updates, print that
                elif event.type == "agent_updated_stream_event":
                    msg = f"Agent updated: {event.new_agent.name}"
                    notifications.append(msg)
                    yield "\n".join(notifications), None
                # When items are generated, print them
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        msg = f"-- Tool was called: {event.item.raw_item.name}"
                        notifications.append(msg)
                        yield "\n".join(notifications), None
                    elif event.item.type == "tool_call_output_item":
                        msg = f"-- Tool output generated"
                        notifications.append(msg)
                        ## TODO:: need a better way to extract output from tools
                        final_output = event.item.output
                        yield "\n".join(notifications), None
            yield "\n".join(notifications), f"{final_output}"
