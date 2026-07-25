class QueryRefiner:

    def __init__(self, llm):
        self.llm = llm

    async def refine(self, query, state):
        prompt = f"""
        Original query: {query}

        Findings so far:
        {state.sources}

        Suggest a better search query to fill gaps.
        """

        result = self.llm(prompt)

        if isinstance(result, dict):
            return result.get("query", query)

        return result