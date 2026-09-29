from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from app.payments.schemas import PaymentInitiation, PaymentInitiated, PaymentStatus
from app.payments.service import (
    PaymentProviderError,
    PaymentValidationError,
    get_payment,
    initiate_payment,
    process_callback,
)


router = APIRouter(prefix="/api/payments/kopokopo", tags=["payments"])


@router.post("/stk-push", response_model=PaymentInitiated, status_code=status.HTTP_202_ACCEPTED)
async def create_mpesa_payment(payment: PaymentInitiation) -> PaymentInitiated:
    try:
        return await initiate_payment(payment)
    except PaymentValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except PaymentProviderError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.get("/auth")
async def kopokopo_authentication() -> dict[str, str]:
    return {"provider": "KOPOKOPO", "status": "configured"}


@router.post("/callback", response_model=PaymentStatus, status_code=status.HTTP_202_ACCEPTED)
@router.post("/webhook", response_model=PaymentStatus, status_code=status.HTTP_202_ACCEPTED)
async def kopokopo_callback(
    payload: dict[str, Any],
    x_kopokopo_signature: str | None = Header(default=None),
) -> PaymentStatus:
    try:
        payment = process_callback(payload, x_kopokopo_signature)
    except PaymentProviderError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment was not found")
    return payment


@router.get("/status/{payment_id}", response_model=PaymentStatus)
async def payment_status(payment_id: str) -> PaymentStatus:
    payment = get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment was not found")
    return payment