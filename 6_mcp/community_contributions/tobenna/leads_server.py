import json

from mcp.server.fastmcp import FastMCP

from leads import Lead

mcp = FastMCP("lead_intake_server")


@mcp.tool()
async def intake_lead(
    name: str = "",
    email: str = "",
    company: str = "",
    role_title: str = "",
    interest: str = "",
    source_brief: str = "",
    summary: str = "",
    next_action: str = "Review the lead and send a first response",
    status: str = "new",
) -> str:
    lead = Lead(
        name=name,
        email=email,
        company=company,
        role_title=role_title,
        interest=interest,
        source_brief=source_brief,
        summary=summary,
        next_action=next_action,
        status=status,
    )
    lead.save()
    return json.dumps({"lead_id": lead.id, "status": lead.status, "next_action": lead.next_action})


@mcp.tool()
async def list_leads(status: str = "all") -> str:
    leads = [lead.model_dump() for lead in Lead.list(status)]
    return json.dumps(leads, indent=2)


@mcp.tool()
async def get_lead_context(lead_id: str) -> str:
    return Lead.get(lead_id).to_context()


@mcp.tool()
async def qualify_lead(
    lead_id: str,
    qualification_status: str,
    priority: str,
    qualification_reason: str,
    next_action: str,
) -> str:
    lead = Lead.get(lead_id)
    lead.apply_qualification(
        qualification_status=qualification_status,
        priority=priority,
        qualification_reason=qualification_reason,
        next_action=next_action,
    )
    return json.dumps(
        {
            "lead_id": lead.id,
            "status": lead.status,
            "qualification_status": lead.qualification_status,
            "priority": lead.priority,
            "next_action": lead.next_action,
        }
    )


@mcp.tool()
async def route_lead(lead_id: str, owner: str, queue: str, routing_reason: str) -> str:
    lead = Lead.get(lead_id)
    lead.apply_routing(owner=owner, queue=queue, routing_reason=routing_reason)
    return json.dumps(
        {
            "lead_id": lead.id,
            "status": lead.status,
            "routing_owner": lead.routing_owner,
            "routing_queue": lead.routing_queue,
        }
    )


@mcp.tool()
async def log_notification(lead_id: str, notification_status: str, notification_detail: str) -> str:
    lead = Lead.get(lead_id)
    lead.apply_notification(
        notification_status=notification_status,
        notification_detail=notification_detail,
    )
    return json.dumps(
        {
            "lead_id": lead.id,
            "notification_status": lead.notification_status,
            "notification_detail": lead.notification_detail,
        }
    )


@mcp.resource("leads://lead/{lead_id}")
async def read_lead_resource(lead_id: str) -> str:
    return Lead.get(lead_id).to_context()


if __name__ == "__main__":
    mcp.run(transport="stdio")