from pydantic import BaseModel
from typing import List
from datetime import datetime


class ClassificationResponse(BaseModel):
    id: int
    image_url: str
    waste_type: str
    confidence: str
    description: str
    possible_uses: List[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConfirmClassification(BaseModel):
    waste_type: str | None = None
    description: str | None = None