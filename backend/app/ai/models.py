from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=False)
    waste_type = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    possible_uses = Column(JSON, nullable=False)
    status = Column(String, default="pending_review")
    created_at = Column(DateTime(timezone=True), server_default=func.now())