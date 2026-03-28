from resources.scheduler import create_weekly_schedule
from resources.budget import calculate_budget
from resources.priority import prioritize_tasks
from resources.summary_resource import generate_summary
from resources.format import format_output


class MCPServer:

    def handle_request(self, request_type: str, payload: dict):

        if request_type == "schedule_week":
            return create_weekly_schedule(payload["goal"])

        elif request_type == "calculate_budget":
            return calculate_budget(payload["expenses"])

        elif request_type == "prioritize_tasks":
            return prioritize_tasks(payload["tasks"])

        elif request_type == "summarize":
            return generate_summary(payload["data"])

        elif request_type == "format_output":
            return format_output(payload["goal"], payload["data"])

        else:
            raise ValueError(f"Unknown request type: {request_type}")