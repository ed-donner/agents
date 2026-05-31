class Planner:

    def __init__(self, llm, tools, refiner=None):
        self.llm = llm
        self.tools = tools
        self.refiner = refiner

    def decide(self, query, state):
        prompt = f"""
        You are a research agent.

        Query: {query}
        Notes so far: {state.notes}

        Decide next action:
        - search_web
        - fetch_page
        - extract_structured_data
        - finish

        Respond in JSON.
        """
        return self.llm(prompt)