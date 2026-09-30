from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.admin.models import Dispute, ListingModerationLog
from app.admin.schemas import ModerationAction
from app.db.database import get_db
from app.listings.models import ListingStatus, WasteListing


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/listings/pending")
def get_pending_listings(
    db: Session = Depends(get_db),
):


    query = select(WasteListing).where(
        or_(
            WasteListing.status == ListingStatus.PENDING,
            WasteListing.status == ListingStatus.FLAGGED,
        )
    )

    result = db.execute(query)

    return result.scalars().all()


@router.patch(
    "/listings/{listing_id}/moderate",
)
def moderate_listing(
    listing_id: int,
    moderation: ModerationAction,
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

    status_mapping = {
        "approve": ListingStatus.ACTIVE,
        "reject": ListingStatus.REJECTED,
        "flag": ListingStatus.FLAGGED,
    }

    new_status = status_mapping[moderation.action]

    listing.status = new_status

    # Temporary admin ID until authentication is integrated.
    admin_id = 1

    moderation_log = ListingModerationLog(
        listing_id=listing.id,
        admin_id=admin_id,
        action=moderation.action,
        reason=moderation.reason,
    )

    db.add(moderation_log)
    db.commit()
    db.refresh(listing)

    return {
        "message": "Listing moderated successfully.",
        "listing_id": listing.id,
        "status": listing.status,
    }


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
):


    total_listings = db.scalar(
        select(func.count(WasteListing.id))
    )

    active_listings = db.scalar(
        select(func.count(WasteListing.id)).where(
            WasteListing.status == ListingStatus.ACTIVE
        )
    )

    total_disputes = db.scalar(
        select(func.count(Dispute.id))
    )

    return {
        "total_listings": total_listings or 0,
        "active_listings": active_listings or 0,
        "total_disputes": total_disputes or 0,
    }
