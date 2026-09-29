from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.payments.schemas import PaymentInitiation, PaymentInitiated, PaymentStatus
from app.payments.service import PaymentProviderError, get_payment, initiate_payment, process_callback


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/mpesa", response_model=PaymentInitiated, status_code=status.HTTP_202_ACCEPTED)
async def create_mpesa_payment(payment: PaymentInitiation) -> PaymentInitiated:
    try:
        return await initiate_payment(payment)
    except PaymentProviderError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.post("/callbacks/kopokopo", response_model=PaymentStatus, status_code=status.HTTP_202_ACCEPTED)
async def kopokopo_callback(payload: dict[str, Any]) -> PaymentStatus:
    payment = process_callback(payload)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment was not found")
    return payment


@router.get("/{payment_id}", response_model=PaymentStatus)
async def payment_status(payment_id: str) -> PaymentStatus:
    payment = get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment was not found")
    return payment