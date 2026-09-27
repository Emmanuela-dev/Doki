from pydantic import BaseModel, Field


class ModerationAction(BaseModel):


    action: str = Field(
        ...,
        pattern="^(approve|reject|flag)$",
    )

    reason: str | None = None


class DisputeUpdate(BaseModel):


    status: str = Field(
        ...,
        pattern="^(open|under_review|resolved|dismissed)$",
    )

    resolution_note: str | None = None
