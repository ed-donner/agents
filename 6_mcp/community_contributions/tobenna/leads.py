import json
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from database import list_leads as db_list_leads, read_lead, upsert_lead


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: f"lead_{uuid4().hex[:10]}")
    name: str = ""
    email: str = ""
    company: str = ""
    role_title: str = ""
    interest: str = ""
    status: str = "new"
    summary: str = ""
    next_action: str = ""
    source_brief: str = ""
    priority: str = "normal"
    qualification_status: str = "pending"
    qualification_reason: str = ""
    routing_owner: str = ""
    routing_queue: str = ""
    routing_reason: str = ""
    notification_status: str = "not_sent"
    notification_detail: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def get(cls, lead_id: str) -> "Lead":
        data = read_lead(lead_id)
        if not data:
            raise ValueError(f"Lead {lead_id} was not found")
        return cls(**data)

    @classmethod
    def list(cls, status: str = "all") -> list["Lead"]:
        return [cls(**lead) for lead in db_list_leads(status)]

    def save(self) -> None:
        self.updated_at = datetime.now().isoformat()
        upsert_lead(self.model_dump())

    def to_context(self) -> str:
        return json.dumps(self.model_dump(), indent=2)

    def apply_qualification(
        self,
        qualification_status: str,
        priority: str,
        qualification_reason: str,
        next_action: str,
    ) -> None:
        self.qualification_status = qualification_status
        self.priority = priority
        self.qualification_reason = qualification_reason
        self.next_action = next_action
        if qualification_status == "qualified":
            self.status = "qualified"
        elif qualification_status == "nurture":
            self.status = "nurture"
        else:
            self.status = "disqualified"
        self.save()

    def apply_routing(self, owner: str, queue: str, routing_reason: str) -> None:
        self.routing_owner = owner
        self.routing_queue = queue
        self.routing_reason = routing_reason
        if self.qualification_status == "qualified":
            self.status = "routed"
        self.save()

    def apply_notification(self, notification_status: str, notification_detail: str) -> None:
        self.notification_status = notification_status
        self.notification_detail = notification_detail
        self.save()