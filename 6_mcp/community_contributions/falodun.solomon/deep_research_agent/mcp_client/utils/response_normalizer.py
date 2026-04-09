class ResponseNormalizer:

    @staticmethod
    def extract_data(response):
        if not response:
            return []

        # Case 1: MCP structured response
        if hasattr(response, "content"):
            return response.content

        # Case 2: dict
        if isinstance(response, dict):
            return (
                response.get("content")
                or response.get("data")
                or response.get("results")
                or []
            )

        # Case 3: already list
        if isinstance(response, list):
            return response

        return []