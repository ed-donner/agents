from database import write_log

class LogTracer:
    def __init__(self, name: str = "github_agent"):
        self.name = name

    def info(self, message: str):
        write_log(self.name, "info", message)

    def error(self, message: str):
        write_log(self.name, "error", message)

    def tool(self, tool_name: str, arguments: dict, result: str):
        message = f"Executed {tool_name} with args {arguments}: {result[:100]}..."
        write_log(self.name, "tool", message)

    def resource(self, uri: str, content: str):
        message = f"Read resource {uri}: {content[:100]}..."
        write_log(self.name, "resource", message)
