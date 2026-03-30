from pydantic import BaseModel, Field


class EmailDraft(BaseModel):
    subject: str = Field(description="Short subject line")
    greeting: str = Field(description="Greeting line")
    body: str = Field(description="Email body, 3-6 sentences")
    cta: str = Field(description="Clear call-to-action")
    signature: str = Field(description="Signature line")
