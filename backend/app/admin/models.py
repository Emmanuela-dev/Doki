from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerificationStatus(str, Enum):


    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DisputeStatus(str, Enum):


    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class ListingModerationLog(Base):


    __tablename__ = "listing_moderation_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("waste_listings.id"),
        nullable=False,
        index=True,
    )

    admin_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class BusinessVerificationRequest(Base):


    __tablename__ = "business_verification_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    registration_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    document_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[VerificationStatus] = mapped_column(
        String(50),
        nullable=False,
        default=VerificationStatus.PENDING,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Dispute(Base):


    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("waste_listings.id"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[DisputeStatus] = mapped_column(
        String(50),
        nullable=False,
        default=DisputeStatus.OPEN,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
