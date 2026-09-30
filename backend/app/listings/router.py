"""
Listings router — Seller side.

Endpoints:
  POST   /listings/                        create a listing
  GET    /listings/my                      view own listings
  GET    /listings/{listing_id}            get single listing (full)
  PUT    /listings/{listing_id}            edit listing
  PATCH  /listings/{listing_id}/status     activate / deactivate / mark sold
  DELETE /listings/{listing_id}            delete listing
  POST   /listings/{listing_id}/images     upload waste image(s)
  DELETE /listings/{listing_id}/images/{image_id}  remove an image
  GET    /listings/{listing_id}/interested  view buyers who expressed interest
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status

from app.core.schemas import (
    ListingCreate,
    ListingUpdate,
    ListingOut,
    ListingBriefOut,
    ListingImageOut,
    ListingStatus,
    MessageResponse,
)
from app.core import store
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/listings", tags=["Listings — Seller"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrich_listing(listing: dict) -> dict:
    """Attach computed fields needed by ListingOut."""
    cat = store.waste_categories.get(listing["waste_category_id"], {})
    seller = store.users.get(listing["seller_id"], {})
    images = [
        img for img in store.listing_images.values()
        if img["listing_id"] == listing["id"]
    ]
    interested = [
        t for t in store.transactions.values()
        if t["listing_id"] == listing["id"]
    ]
    primary = next((i["url"] for i in images if i["is_primary"]), None)
    return {
        **listing,
        "waste_category_name": cat.get("name", "Unknown"),
        "seller_name": seller.get("name", "Unknown"),
        "images": images,
        "interested_buyers_count": len(interested),
        "primary_image_url": primary,
        "location_address": listing["location"]["address"],
    }


def _get_listing_or_404(listing_id: str) -> dict:
    listing = store.listings.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


def _assert_owner(listing: dict, user_id: str) -> None:
    if listing["seller_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this listing",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    current_user: dict = Depends(require_role("seller")),
):
    """Create a new organic-waste listing."""
    if payload.waste_category_id not in store.waste_categories:
        raise HTTPException(status_code=400, detail="Invalid waste_category_id")

    now = datetime.now(timezone.utc)
    listing_id = str(uuid4())
    listing = {
        "id": listing_id,
        "seller_id": current_user["id"],
        **payload.model_dump(),
        "location": payload.location.model_dump(),
        "status": ListingStatus.active,
        "created_at": now,
        "updated_at": now,
    }
    store.listings[listing_id] = listing
    return _enrich_listing(listing)


@router.get("/my", response_model=List[ListingOut])
def get_my_listings(
    status_filter: Optional[ListingStatus] = Query(None, alias="status"),
    current_user: dict = Depends(require_role("seller")),
):
    """Return all listings owned by the authenticated seller."""
    results = [
        l for l in store.listings.values()
        if l["seller_id"] == current_user["id"]
    ]
    if status_filter:
        results = [l for l in results if l["status"] == status_filter]
    results.sort(key=lambda l: l["created_at"], reverse=True)
    return [_enrich_listing(l) for l in results]


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: str):
    """Fetch full detail of a single listing (public)."""
    listing = _get_listing_or_404(listing_id)
    return _enrich_listing(listing)


@router.put("/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: str,
    payload: ListingUpdate,
    current_user: dict = Depends(require_role("seller")),
):
    """Edit any field of an existing listing."""
    listing = _get_listing_or_404(listing_id)
    _assert_owner(listing, current_user["id"])

    updates = payload.model_dump(exclude_unset=True)
    if "location" in updates and updates["location"]:
        updates["location"] = updates["location"].model_dump() if hasattr(updates["location"], "model_dump") else updates["location"]
    if "waste_category_id" in updates and updates["waste_category_id"] not in store.waste_categories:
        raise HTTPException(status_code=400, detail="Invalid waste_category_id")

    listing.update(updates)
    listing["updated_at"] = datetime.now(timezone.utc)
    store.listings[listing_id] = listing
    return _enrich_listing(listing)


@router.patch("/{listing_id}/status", response_model=ListingOut)
def update_listing_status(
    listing_id: str,
    new_status: ListingStatus = Query(...),
    current_user: dict = Depends(require_role("seller")),
):
    """Quickly flip a listing's status (active / inactive / sold)."""
    listing = _get_listing_or_404(listing_id)
    _assert_owner(listing, current_user["id"])
    listing["status"] = new_status
    listing["updated_at"] = datetime.now(timezone.utc)
    return _enrich_listing(listing)


@router.delete("/{listing_id}", response_model=MessageResponse)
def delete_listing(
    listing_id: str,
    current_user: dict = Depends(require_role("seller")),
):
    """Permanently delete a listing and its images."""
    listing = _get_listing_or_404(listing_id)
    _assert_owner(listing, current_user["id"])

    # Remove associated images
    image_ids = [
        img_id for img_id, img in store.listing_images.items()
        if img["listing_id"] == listing_id
    ]
    for img_id in image_ids:
        del store.listing_images[img_id]

    del store.listings[listing_id]
    return {"message": f"Listing {listing_id} deleted successfully"}


# ---------------------------------------------------------------------------
# Image management
# ---------------------------------------------------------------------------

@router.post(
    "/{listing_id}/images",
    response_model=List[ListingImageOut],
    status_code=status.HTTP_201_CREATED,
)
async def upload_images(
    listing_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(require_role("seller")),
):
    """
    Upload one or more waste images for a listing.
    Files are stored locally under /uploads/<listing_id>/.
    The first image uploaded becomes the primary image if none exists yet.
    """
    import os, aiofiles

    listing = _get_listing_or_404(listing_id)
    _assert_owner(listing, current_user["id"])

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    max_size_bytes = 10 * 1024 * 1024  # 10 MB

    upload_dir = os.path.join("uploads", listing_id)
    os.makedirs(upload_dir, exist_ok=True)

    existing_images = [
        img for img in store.listing_images.values()
        if img["listing_id"] == listing_id
    ]
    has_primary = any(img["is_primary"] for img in existing_images)

    saved: List[ListingImageOut] = []
    for idx, file in enumerate(files):
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' has unsupported type {file.content_type}. "
                       f"Allowed: jpeg, png, webp",
            )
        content = await file.read()
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds 10 MB limit",
            )

        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        image_id = str(uuid4())
        filename = f"{image_id}.{ext}"
        filepath = os.path.join(upload_dir, filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        is_primary = (not has_primary) and (idx == 0)
        img_record = {
            "id": image_id,
            "listing_id": listing_id,
            "url": f"/uploads/{listing_id}/{filename}",
            "is_primary": is_primary,
            "uploaded_at": datetime.now(timezone.utc),
        }
        store.listing_images[image_id] = img_record
        saved.append(ListingImageOut(**img_record))

        if is_primary:
            has_primary = True

    listing["updated_at"] = datetime.now(timezone.utc)
    return saved


@router.delete("/{listing_id}/images/{image_id}", response_model=MessageResponse)
def delete_image(
    listing_id: str,
    image_id: str,
    current_user: dict = Depends(require_role("seller")),
):
    """Remove a single image from a listing."""
    import os

    listing = _get_listing_or_404(listing_id)
    _assert_owner(listing, current_user["id"])

    image = store.listing_images.get(image_id)
    if not image or image["listing_id"] != listing_id:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete file from disk
    disk_path = image["url"].lstrip("/")
    if os.path.exists(disk_path):
        os.remove(disk_path)

    del store.listing_images[image_id]

    # If deleted image was primary, promote the next available image
    remaining = [
        img for img in store.listing_images.values()
        if img["listing_id"] == listing_id
    ]
    if remaining and image.get("is_primary"):
        remaining[0]["is_primary"] = True

    return {"message": f"Image {image_id} removed"}


# ---------------------------------------------------------------------------
# Interested buyers
# ---------------------------------------------------------------------------

@router.get("/{listing_id}/interested", response_model=List[dict])
def get_interested_buyers(
    listing_id: str,
    current_user: dict = Depends(require_role("seller")),
):
    """
    Return all buyers who have expressed interest (initiated a transaction)
    on this listing, with their transaction summary.
    """
    _get_listing_or_404(listing_id)

    interested = []
    for txn in store.transactions.values():
        if txn["listing_id"] != listing_id:
            continue
        buyer = store.users.get(txn["buyer_id"], {})
        interested.append({
            "transaction_id": txn["id"],
            "buyer_id": txn["buyer_id"],
            "buyer_name": buyer.get("name", "Unknown"),
            "buyer_email": buyer.get("email", ""),
            "quantity_requested": txn["quantity_requested"],
            "proposed_price_per_unit": txn.get("proposed_price_per_unit"),
            "status": txn["status"],
            "message": txn.get("message_to_seller"),
            "created_at": txn["created_at"],
        })

    interested.sort(key=lambda x: x["created_at"], reverse=True)
    return interested
