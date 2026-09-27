from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.listings.models import ListingStatus, OrganicWasteCategory


class ListingCreate(BaseModel):


    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    category: OrganicWasteCategory

    quantity_tonnes: float = Field(..., gt=0)
    price_per_unit: float = Field(..., ge=0)

    unit: str = Field(default="tonne", min_length=1, max_length=50)

    moisture_content: str | None = None
    purity_level: str | None = None
    quality_grade: str | None = None

    location: str = Field(..., min_length=1, max_length=255)

    image_url: str | None = None


class ListingUpdate(BaseModel):


    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    category: OrganicWasteCategory | None = None

    quantity_tonnes: float | None = Field(default=None, gt=0)
    price_per_unit: float | None = Field(default=None, ge=0)

    unit: str | None = Field(default=None, min_length=1, max_length=50)

    moisture_content: str | None = None
    purity_level: str | None = None
    quality_grade: str | None = None

    location: str | None = Field(default=None, min_length=1, max_length=255)

    image_url: str | None = None

    status: ListingStatus | None = None


class ListingResponse(BaseModel):


    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None

    category: OrganicWasteCategory

    quantity_tonnes: float
    price_per_unit: float
    unit: str

    moisture_content: str | None
    purity_level: str | None
    quality_grade: str | None

    location: str
    image_url: str | None

    status: ListingStatus

    seller_id: int

    created_at: datetime
    updated_at: datetime
