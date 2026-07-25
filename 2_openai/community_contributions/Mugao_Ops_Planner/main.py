from agent.agent import Agent
from agent.planner import Planner
from core.client import MCPClient
from core.server import MCPServer


def main():
    server = MCPServer()
    client = MCPClient(server)
    planner = Planner()
    agent = Agent(planner, client)

    print("\n=== Life Ops Agent ===\n")

    while True:
        query = input("Enter your request (or 'exit'): ")

        if query.lower() == "exit":
            break

        result = agent.run(query)

        print("\n--- RESULT ---")
        print(result)
        print("\n")


if __name__ == "__main__":
    main()