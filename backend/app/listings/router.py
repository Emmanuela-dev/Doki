from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.listings.models import WasteListing, ListingStatus, OrganicWasteCategory
from app.listings.schemas import ListingCreate, ListingResponse, ListingUpdate


router = APIRouter(
    prefix="/listings",
    tags=["Listings"],
)


@router.post(
    "/",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing(
    listing_data: ListingCreate,
    db: Session = Depends(get_db),
):


    # Temporary seller ID until authentication is integrated.
    seller_id = 1

    listing = WasteListing(
        title=listing_data.title,
        description=listing_data.description,
        category=listing_data.category,
        quantity_tonnes=listing_data.quantity_tonnes,
        price_per_unit=listing_data.price_per_unit,
        unit=listing_data.unit,
        moisture_content=listing_data.moisture_content,
        purity_level=listing_data.purity_level,
        quality_grade=listing_data.quality_grade,
        location=listing_data.location,
        image_url=listing_data.image_url,
        status=ListingStatus.ACTIVE,
        seller_id=seller_id,
    )

    db.add(listing)
    db.commit()
    db.refresh(listing)

    return listing


@router.get(
    "/",
    response_model=list[ListingResponse],
)
def get_listings(
    category: OrganicWasteCategory | None = Query(default=None),
    min_quantity: float | None = Query(default=None, gt=0),
    max_price: float | None = Query(default=None, ge=0),
    location: str | None = Query(default=None),
    db: Session = Depends(get_db),
):


    query = select(WasteListing).where(
        WasteListing.status == ListingStatus.ACTIVE
    )

    if category is not None:
        query = query.where(
            WasteListing.category == category
        )

    if min_quantity is not None:
        query = query.where(
            WasteListing.quantity_tonnes >= min_quantity
        )

    if max_price is not None:
        query = query.where(
            WasteListing.price_per_unit <= max_price
        )

    if location is not None:
        query = query.where(
            WasteListing.location.ilike(f"%{location}%")
        )

    query = query.order_by(WasteListing.created_at.desc())

    result = db.execute(query)

    return result.scalars().all()


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
):


    query = select(WasteListing).where(
        WasteListing.id == listing_id
    )

    result = db.execute(query)
    listing = result.scalar_one_or_none()

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste listing not found.",
        )

    return listing


@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
)
def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    db: Session = Depends(get_db),
):


    query = select(WasteListing).where(
        WasteListing.id == listing_id
    )

    result = db.execute(query)
    listing = result.scalar_one_or_none()

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste listing not found.",
        )

    update_data = listing_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)

    return listing
