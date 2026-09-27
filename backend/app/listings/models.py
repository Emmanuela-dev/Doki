from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrganicWasteCategory(str, Enum):


    FOOD_PROCESSING = "food_processing"
    BREWERY_SPENT_GRAIN = "brewery_spent_grain"
    COFFEE_HULLS_PULP = "coffee_hulls_pulp"
    MARKET_ORGANIC_WASTE = "market_organic_waste"
    DAIRY_SUGAR_BYPRODUCTS = "dairy_sugar_byproducts"
    ANIMAL_MANURE = "animal_manure"
    OTHER_ORGANIC = "other_organic"


class ListingStatus(str, Enum):


    PENDING = "pending"
    ACTIVE = "active"
    FLAGGED = "flagged"
    SOLD = "sold"
    REJECTED = "rejected"


def utc_now() -> datetime:

    return datetime.now(timezone.utc)


class WasteListing(Base):


    __tablename__ = "waste_listings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[OrganicWasteCategory] = mapped_column(
        SQLEnum(
            OrganicWasteCategory,
            name="organic_waste_category",
            native_enum=False,
        ),
        nullable=False,
    )

    quantity_tonnes: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    price_per_unit: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="tonne",
    )

    moisture_content: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    purity_level: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    quality_grade: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(
            ListingStatus,
            name="listing_status",
            native_enum=False,
        ),
        nullable=False,
        default=ListingStatus.ACTIVE,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
