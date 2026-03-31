from utils.logger import log


class MCPClient:

    def __init__(self, server):
        self.server = server

    def call(self, request_type: str, payload: dict):
        log(f"→ Calling: {request_type}")
        response = self.server.handle_request(request_type, payload)
        log(f"← Completed: {request_type}")
        return response