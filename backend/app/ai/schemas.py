from pydantic import BaseModel
from typing import List


class ClassificationResponse(BaseModel):
    waste_type: str
    confidence: str
    description: str
    possible_uses: List[str]