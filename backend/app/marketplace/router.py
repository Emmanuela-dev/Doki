"""
Marketplace router — Buyer side.

Endpoints:
  GET  /marketplace/                    browse & search listings (paginated)
  GET  /marketplace/categories          list waste categories
  GET  /marketplace/{listing_id}        view full listing detail
  POST /marketplace/{listing_id}/interest  express interest / initiate purchase
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.schemas import (
    ListingBriefOut,
    ListingOut,
    ListingStatus,
    PaginatedListings,
    TransactionCreate,
    TransactionOut,
    TransactionStatus,
    QuantityUnit,
)
from app.core import store
from app.auth.dependencies import get_current_user, require_role
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/marketplace", tags=["Marketplace — Buyer"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _listing_to_brief(listing: dict) -> dict:
    cat = store.waste_categories.get(listing["waste_category_id"], {})
    seller = store.users.get(listing["seller_id"], {})
    images = [img for img in store.listing_images.values() if img["listing_id"] == listing["id"]]
    primary = next((i["url"] for i in images if i["is_primary"]), None)
    interested_count = sum(
        1 for t in store.transactions.values() if t["listing_id"] == listing["id"]
    )
    return {
        **listing,
        "waste_category_name": cat.get("name", "Unknown"),
        "seller_name": seller.get("name", "Unknown"),
        "primary_image_url": primary,
        "location_address": listing["location"]["address"],
        "interested_buyers_count": interested_count,
    }


def _listing_to_full(listing: dict) -> dict:
    cat = store.waste_categories.get(listing["waste_category_id"], {})
    seller = store.users.get(listing["seller_id"], {})
    images = [img for img in store.listing_images.values() if img["listing_id"] == listing["id"]]
    interested_count = sum(
        1 for t in store.transactions.values() if t["listing_id"] == listing["id"]
    )
    return {
        **listing,
        "waste_category_name": cat.get("name", "Unknown"),
        "seller_name": seller.get("name", "Unknown"),
        "images": images,
        "interested_buyers_count": interested_count,
        "location_address": listing["location"]["address"],
    }


# ---------------------------------------------------------------------------
# Browse & Search
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedListings)
def browse_listings(
    # Search
    q: Optional[str] = Query(None, description="Full-text search across title and description"),
    # Filters
    category_id: Optional[str] = Query(None, description="Filter by waste_category_id"),
    county: Optional[str] = Query(None, description="Filter by county name"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price per unit"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price per unit"),
    min_quantity: Optional[float] = Query(None, gt=0, description="Minimum available quantity"),
    quantity_unit: Optional[QuantityUnit] = Query(None, description="Filter by quantity unit"),
    is_recurring: Optional[bool] = Query(None, description="Show only recurring listings"),
    # Sort
    sort_by: str = Query("created_at", description="Field to sort by: created_at | price_per_unit | quantity"),
    order: str = Query("desc", description="asc or desc"),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Browse active listings with optional full-text search, filters, sort and pagination.
    Only ACTIVE listings are returned to buyers.
    """
    results = [
        l for l in store.listings.values()
        if l["status"] == ListingStatus.active
    ]

    # Full-text search
    if q:
        q_lower = q.lower()
        results = [
            l for l in results
            if q_lower in l["title"].lower() or q_lower in l["description"].lower()
        ]

    # Filters
    if category_id:
        results = [l for l in results if l["waste_category_id"] == category_id]
    if county:
        results = [l for l in results if (l["location"].get("county") or "").lower() == county.lower()]
    if city:
        results = [l for l in results if (l["location"].get("city") or "").lower() == city.lower()]
    if min_price is not None:
        results = [l for l in results if l["price_per_unit"] >= min_price]
    if max_price is not None:
        results = [l for l in results if l["price_per_unit"] <= max_price]
    if min_quantity is not None:
        results = [l for l in results if l["quantity"] >= min_quantity]
    if quantity_unit:
        results = [l for l in results if l["quantity_unit"] == quantity_unit]
    if is_recurring is not None:
        results = [l for l in results if l["is_recurring"] == is_recurring]

    # Sort
    reverse = order.lower() != "asc"
    valid_sort_fields = {"created_at", "price_per_unit", "quantity"}
    sort_field = sort_by if sort_by in valid_sort_fields else "created_at"
    results.sort(key=lambda l: l.get(sort_field, 0), reverse=reverse)

    # Paginate
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [_listing_to_brief(l) for l in page_results],
    }


@router.get("/categories", response_model=List[dict])
def list_categories():
    """Return all available waste categories."""
    return list(store.waste_categories.values())


# ---------------------------------------------------------------------------
# Listing Detail
# ---------------------------------------------------------------------------

@router.get("/{listing_id}", response_model=ListingOut)
def get_listing_detail(listing_id: str):
    """
    View the full detail of a listing.
    Accessible to any authenticated user (buyer or seller).
    """
    listing = store.listings.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["status"] not in (ListingStatus.active, ListingStatus.pending):
        raise HTTPException(status_code=404, detail="Listing is not available")
    return _listing_to_full(listing)


# ---------------------------------------------------------------------------
# Express Interest / Initiate Purchase
# ---------------------------------------------------------------------------

@router.post(
    "/{listing_id}/interest",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
)
def express_interest(
    listing_id: str,
    payload: TransactionCreate,
    current_user: dict = Depends(require_role("buyer")),
):
    """
    Buyer expresses interest in a listing — creates a Transaction in
    'initiated' status. Seller is notified (stub) and can agree/reject.
    """
    listing = store.listings.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["status"] != ListingStatus.active:
        raise HTTPException(status_code=400, detail="Listing is not currently active")
    if listing["seller_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot express interest in your own listing")

    # Prevent duplicate open interest from the same buyer
    duplicate = next(
        (
            t for t in store.transactions.values()
            if t["listing_id"] == listing_id
            and t["buyer_id"] == current_user["id"]
            and t["status"] in (
                TransactionStatus.initiated,
                TransactionStatus.agreed,
                TransactionStatus.payment_pending,
            )
        ),
        None,
    )
    if duplicate:
        raise HTTPException(
            status_code=400,
            detail=f"You already have an open transaction ({duplicate['id']}) for this listing",
        )

    cat = store.waste_categories.get(listing["waste_category_id"], {})
    seller = store.users.get(listing["seller_id"], {})
    buyer = store.users.get(current_user["id"], current_user)

    now = datetime.now(timezone.utc)
    txn_id = str(uuid4())

    txn = {
        "id": txn_id,
        "listing_id": listing_id,
        "listing_title": listing["title"],
        "seller_id": listing["seller_id"],
        "seller_name": seller.get("name", "Unknown"),
        "buyer_id": current_user["id"],
        "buyer_name": buyer.get("name", current_user.get("name", "Unknown")),
        "quantity_requested": payload.quantity_requested,
        "quantity_unit": listing["quantity_unit"],
        "proposed_price_per_unit": payload.proposed_price_per_unit,
        "agreed_price_per_unit": None,
        "agreed_quantity": None,
        "total_amount": None,
        "currency": listing["currency"],
        "status": TransactionStatus.initiated,
        "message_to_seller": payload.message_to_seller,
        "seller_notes": None,
        "buyer_notes": None,
        "delivery_address": payload.delivery_address.model_dump() if payload.delivery_address else None,
        "delivery_date": None,
        "created_at": now,
        "updated_at": now,
    }
    store.transactions[txn_id] = txn

    # Update listing status to pending when first interest is expressed
    if listing["status"] == ListingStatus.active:
        listing["status"] = ListingStatus.pending
        listing["updated_at"] = now

    return txn
