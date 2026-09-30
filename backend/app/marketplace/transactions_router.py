"""
Transactions router.

Endpoints:
  GET    /transactions/                     list my transactions (buyer or seller view)
  GET    /transactions/{txn_id}             get single transaction detail
  PATCH  /transactions/{txn_id}/agree       seller agrees + sets final price/quantity/date
  PATCH  /transactions/{txn_id}/reject      seller rejects interest
  PATCH  /transactions/{txn_id}/payment     buyer proceeds to payment (sets payment_pending)
  PATCH  /transactions/{txn_id}/confirm-delivery  buyer confirms delivery → completed
  PATCH  /transactions/{txn_id}/dispute     buyer raises a dispute
  PATCH  /transactions/{txn_id}/cancel      buyer or seller cancels
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.schemas import TransactionOut, TransactionStatus, MessageResponse
from app.core import store
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ---------------------------------------------------------------------------
# Request bodies for targeted PATCH actions
# ---------------------------------------------------------------------------

class AgreePayload(BaseModel):
    agreed_price_per_unit: float = Field(..., ge=0)
    agreed_quantity: float = Field(..., gt=0)
    delivery_date: datetime
    seller_notes: Optional[str] = Field(None, max_length=500)


class RejectPayload(BaseModel):
    seller_notes: Optional[str] = Field(None, max_length=500)


class PaymentPayload(BaseModel):
    payment_method: str = Field(default="mpesa", description="mpesa | card | bank")
    buyer_notes: Optional[str] = Field(None, max_length=500)


class DisputePayload(BaseModel):
    reason: str = Field(..., min_length=10, max_length=1000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_txn_or_404(txn_id: str) -> dict:
    txn = store.transactions.get(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


def _assert_party(txn: dict, user_id: str):
    """Ensure caller is buyer or seller in this transaction."""
    if txn["buyer_id"] != user_id and txn["seller_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied — not a party to this transaction")


def _assert_status(txn: dict, *allowed: TransactionStatus):
    if txn["status"] not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Action not allowed in status '{txn['status']}'. "
                   f"Required: {[s.value for s in allowed]}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[TransactionOut])
def list_my_transactions(
    role_view: str = Query("buyer", description="'buyer' or 'seller' — which side to show"),
    txn_status: Optional[TransactionStatus] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
):
    """
    Return all transactions for the current user.
    Pass role_view=seller to see transactions on your listings.
    """
    uid = current_user["id"]
    if role_view == "seller":
        results = [t for t in store.transactions.values() if t["seller_id"] == uid]
    else:
        results = [t for t in store.transactions.values() if t["buyer_id"] == uid]

    if txn_status:
        results = [t for t in results if t["status"] == txn_status]

    results.sort(key=lambda t: t["created_at"], reverse=True)
    return results


@router.get("/{txn_id}", response_model=TransactionOut)
def get_transaction(
    txn_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get full detail of a single transaction."""
    txn = _get_txn_or_404(txn_id)
    _assert_party(txn, current_user["id"])
    return txn


@router.patch("/{txn_id}/agree", response_model=TransactionOut)
def seller_agree(
    txn_id: str,
    payload: AgreePayload,
    current_user: dict = Depends(get_current_user),
):
    """
    Seller agrees to the transaction, locks in price, quantity and delivery date.
    Status moves to 'agreed'.
    """
    txn = _get_txn_or_404(txn_id)
    if txn["seller_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can agree to a transaction")
    _assert_status(txn, TransactionStatus.initiated)

    txn["agreed_price_per_unit"] = payload.agreed_price_per_unit
    txn["agreed_quantity"] = payload.agreed_quantity
    txn["delivery_date"] = payload.delivery_date
    txn["seller_notes"] = payload.seller_notes
    txn["total_amount"] = round(payload.agreed_price_per_unit * payload.agreed_quantity, 2)
    txn["status"] = TransactionStatus.agreed
    txn["updated_at"] = datetime.now(timezone.utc)
    return txn


@router.patch("/{txn_id}/reject", response_model=TransactionOut)
def seller_reject(
    txn_id: str,
    payload: RejectPayload,
    current_user: dict = Depends(get_current_user),
):
    """Seller rejects the buyer's interest. Status moves to 'cancelled'."""
    txn = _get_txn_or_404(txn_id)
    if txn["seller_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the seller can reject a transaction")
    _assert_status(txn, TransactionStatus.initiated)

    txn["seller_notes"] = payload.seller_notes
    txn["status"] = TransactionStatus.cancelled
    txn["updated_at"] = datetime.now(timezone.utc)

    # Re-activate listing if no other open transactions remain
    _maybe_reactivate_listing(txn["listing_id"])
    return txn


@router.patch("/{txn_id}/payment", response_model=TransactionOut)
def proceed_to_payment(
    txn_id: str,
    payload: PaymentPayload,
    current_user: dict = Depends(get_current_user),
):
    """
    Buyer confirms they want to proceed and initiates payment.
    Status moves to 'payment_pending'.

    The actual M-Pesa / payment gateway call is handled by the payments module.
    This endpoint records the intent and returns payment instructions.
    """
    txn = _get_txn_or_404(txn_id)
    if txn["buyer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the buyer can proceed to payment")
    _assert_status(txn, TransactionStatus.agreed)

    txn["buyer_notes"] = payload.buyer_notes
    txn["status"] = TransactionStatus.payment_pending
    txn["payment_method"] = payload.payment_method
    txn["updated_at"] = datetime.now(timezone.utc)

    # Stub: real implementation forwards to payments module
    txn["payment_instructions"] = _build_payment_instructions(txn, payload.payment_method)
    return txn


@router.patch("/{txn_id}/confirm-delivery", response_model=TransactionOut)
def confirm_delivery(
    txn_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Buyer confirms the waste has been delivered as agreed.
    Status moves to 'completed'.
    """
    txn = _get_txn_or_404(txn_id)
    if txn["buyer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the buyer can confirm delivery")
    _assert_status(txn, TransactionStatus.paid, TransactionStatus.in_transit)

    txn["status"] = TransactionStatus.completed
    txn["updated_at"] = datetime.now(timezone.utc)

    # Mark listing as sold
    listing = store.listings.get(txn["listing_id"])
    if listing:
        from app.core.schemas import ListingStatus
        listing["status"] = ListingStatus.sold
        listing["updated_at"] = datetime.now(timezone.utc)

    return txn


@router.patch("/{txn_id}/dispute", response_model=TransactionOut)
def raise_dispute(
    txn_id: str,
    payload: DisputePayload,
    current_user: dict = Depends(get_current_user),
):
    """
    Buyer raises a dispute (e.g. wrong quantity, quality issues).
    Status moves to 'disputed'. Admin will review.
    """
    txn = _get_txn_or_404(txn_id)
    if txn["buyer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the buyer can raise a dispute")
    _assert_status(
        txn,
        TransactionStatus.paid,
        TransactionStatus.in_transit,
        TransactionStatus.completed,
    )

    txn["status"] = TransactionStatus.disputed
    txn["dispute_reason"] = payload.reason
    txn["dispute_raised_at"] = datetime.now(timezone.utc)
    txn["updated_at"] = datetime.now(timezone.utc)
    return txn


@router.patch("/{txn_id}/cancel", response_model=TransactionOut)
def cancel_transaction(
    txn_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Either party can cancel before payment is made.
    After payment, only admin can cancel.
    """
    txn = _get_txn_or_404(txn_id)
    _assert_party(txn, current_user["id"])
    _assert_status(
        txn,
        TransactionStatus.initiated,
        TransactionStatus.agreed,
    )

    txn["status"] = TransactionStatus.cancelled
    txn["updated_at"] = datetime.now(timezone.utc)
    _maybe_reactivate_listing(txn["listing_id"])
    return txn


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _maybe_reactivate_listing(listing_id: str):
    """Re-activate a listing if it has no remaining open transactions."""
    from app.core.schemas import ListingStatus
    open_statuses = {
        TransactionStatus.initiated,
        TransactionStatus.agreed,
        TransactionStatus.payment_pending,
        TransactionStatus.paid,
        TransactionStatus.in_transit,
    }
    has_open = any(
        t for t in store.transactions.values()
        if t["listing_id"] == listing_id and t["status"] in open_statuses
    )
    if not has_open:
        listing = store.listings.get(listing_id)
        if listing and listing["status"] == ListingStatus.pending:
            listing["status"] = ListingStatus.active
            listing["updated_at"] = datetime.now(timezone.utc)


def _build_payment_instructions(txn: dict, method: str) -> dict:
    """Stub — returns instructions the frontend uses to trigger payment."""
    base = {
        "transaction_id": txn["id"],
        "amount": txn.get("total_amount"),
        "currency": txn.get("currency", "KES"),
    }
    if method == "mpesa":
        return {
            **base,
            "method": "mpesa",
            "instructions": "An M-Pesa STK push will be sent to your registered number.",
            "paybill": "DOKI_PAYBILL_STUB",
            "account_number": txn["id"][:8].upper(),
        }
    return {**base, "method": method, "instructions": "Proceed via the payment gateway."}
