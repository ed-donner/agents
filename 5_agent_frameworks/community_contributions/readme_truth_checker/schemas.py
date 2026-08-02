from typing import Literal

from pydantic import BaseModel, Field


class DocClaim(BaseModel):
    id: str = Field(description="Short id, e.g. C1, C2")
    text: str = Field(description="One atomic, checkable statement implied by the README")
    category: Literal["file_path", "command", "env_var", "dependency", "other"] = Field(
        description="What kind of fact is being asserted"
    )


class ClaimBundle(BaseModel):
    claims: list[DocClaim] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Checkable claims extracted from the README (aim for 5–15)",
    )
