"""
Shared Pydantic schemas used across marketplace, listings, and transactions.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ListingStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    sold = "sold"
    pending = "pending"


class QuantityUnit(str, Enum):
    kg = "kg"
    tonnes = "tonnes"
    litres = "litres"
    bags = "bags"
    truckloads = "truckloads"


class TransactionStatus(str, Enum):
    initiated = "initiated"
    agreed = "agreed"
    payment_pending = "payment_pending"
    paid = "paid"
    in_transit = "in_transit"
    delivered = "delivered"
    completed = "completed"
    disputed = "disputed"
    cancelled = "cancelled"


class UserRole(str, Enum):
    seller = "seller"
    buyer = "buyer"
    admin = "admin"


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

class LocationIn(BaseModel):
    place_id: str = Field(..., description="Google Maps place_id")
    address: str = Field(..., description="Human-readable address from Google Maps")
    lat: float
    lng: float
    county: Optional[str] = None
    city: Optional[str] = None


class LocationOut(LocationIn):
    pass


# ---------------------------------------------------------------------------
# Listing Image
# ---------------------------------------------------------------------------

class ListingImageOut(BaseModel):
    id: str
    listing_id: str
    url: str
    is_primary: bool
    uploaded_at: datetime


# ---------------------------------------------------------------------------
# Listing schemas
# ---------------------------------------------------------------------------

class ListingCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    waste_category_id: str
    quantity: float = Field(..., gt=0)
    quantity_unit: QuantityUnit
    price_per_unit: float = Field(..., ge=0)
    currency: str = Field(default="KES", max_length=3)
    availability_date: Optional[datetime] = None
    location: LocationIn
    is_recurring: bool = False
    recurring_frequency_days: Optional[int] = Field(None, ge=1)
    tags: List[str] = Field(default_factory=list)


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    waste_category_id: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    quantity_unit: Optional[QuantityUnit] = None
    price_per_unit: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    availability_date: Optional[datetime] = None
    location: Optional[LocationIn] = None
    status: Optional[ListingStatus] = None
    is_recurring: Optional[bool] = None
    recurring_frequency_days: Optional[int] = Field(None, ge=1)
    tags: Optional[List[str]] = None


class ListingOut(BaseModel):
    id: str
    seller_id: str
    seller_name: str
    title: str
    description: str
    waste_category_id: str
    waste_category_name: str
    quantity: float
    quantity_unit: QuantityUnit
    price_per_unit: float
    currency: str
    availability_date: Optional[datetime]
    location: LocationOut
    status: ListingStatus
    is_recurring: bool
    recurring_frequency_days: Optional[int]
    tags: List[str]
    images: List[ListingImageOut]
    interested_buyers_count: int
    created_at: datetime
    updated_at: datetime


class ListingBriefOut(BaseModel):
    """Lightweight card used in browse/search results."""
    id: str
    seller_id: str
    seller_name: str
    title: str
    waste_category_name: str
    quantity: float
    quantity_unit: QuantityUnit
    price_per_unit: float
    currency: str
    location_address: str
    status: ListingStatus
    primary_image_url: Optional[str]
    interested_buyers_count: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------

class TransactionCreate(BaseModel):
    listing_id: str
    quantity_requested: float = Field(..., gt=0)
    message_to_seller: Optional[str] = Field(None, max_length=500)
    proposed_price_per_unit: Optional[float] = Field(None, ge=0)
    delivery_address: Optional[LocationIn] = None


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    agreed_price_per_unit: Optional[float] = Field(None, ge=0)
    agreed_quantity: Optional[float] = Field(None, gt=0)
    delivery_date: Optional[datetime] = None
    seller_notes: Optional[str] = Field(None, max_length=500)
    buyer_notes: Optional[str] = Field(None, max_length=500)


class TransactionOut(BaseModel):
    id: str
    listing_id: str
    listing_title: str
    seller_id: str
    seller_name: str
    buyer_id: str
    buyer_name: str
    quantity_requested: float
    quantity_unit: QuantityUnit
    proposed_price_per_unit: Optional[float]
    agreed_price_per_unit: Optional[float]
    agreed_quantity: Optional[float]
    total_amount: Optional[float]
    currency: str
    status: TransactionStatus
    message_to_seller: Optional[str]
    seller_notes: Optional[str]
    buyer_notes: Optional[str]
    delivery_address: Optional[LocationOut]
    delivery_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str


class PaginatedListings(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[ListingBriefOut]
