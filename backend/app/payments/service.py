from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import Settings, settings
from app.payments.schemas import PaymentInitiation, PaymentInitiated, PaymentStatus


PAYMENT_PENDING = "PAYMENT_PENDING"
PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
PAID = "PAID"
PAYMENT_FAILED = "PAYMENT_FAILED"


class PaymentProviderError(RuntimeError):
    pass


class PaymentValidationError(ValueError):
    pass


class KopoKopoClient:
    def __init__(self, configuration: Settings = settings) -> None:
        self.configuration = configuration

    def _validate_configuration(self) -> None:
        missing = [
            name
            for name, value in (
                ("KOPOKOPO_CLIENT_ID", self.configuration.kopokopo_client_id),
                ("KOPOKOPO_CLIENT_SECRET", self.configuration.kopokopo_client_secret),
                ("KOPOKOPO_TILL_NUMBER", self.configuration.kopokopo_till_number),
                ("PAYMENT_CALLBACK_URL", self.configuration.payment_callback_url),
            )
            if not value
        ]
        if missing:
            raise PaymentProviderError("Missing payment configuration: " + ", ".join(missing))

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            "/oauth/v1/token",
            auth=(self.configuration.kopokopo_client_id, self.configuration.kopokopo_client_secret),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
        )
        if response.is_error:
            raise PaymentProviderError(f"Kopo Kopo authentication failed ({response.status_code})")
        token = response.json().get("access_token")
        if not token:
            raise PaymentProviderError("Kopo Kopo authentication returned no access token")
        return token

    async def initiate(self, payment: PaymentInitiation, payment_id: str) -> PaymentInitiated:
        self._validate_configuration()
        api_version = self.configuration.kopokopo_api_version
        headers = {
            "Accept": f"application/vnd.kopokopo.{api_version}+json",
            "Content-Type": f"application/vnd.kopokopo.{api_version}+json",
        }
        payload: dict[str, Any] = {
            "payment_channel": "M-PESA STK Push",
            "till_number": self.configuration.kopokopo_till_number,
            "subscriber": {"phone_number": payment.phone_number},
            "amount": {"currency": "KES", "value": str(payment.amount)},
            "metadata": {"payment_id": payment_id, "transaction_id": payment.transaction_id},
            "_links": {"callback_url": self.configuration.payment_callback_url},
        }
        if payment.description:
            payload["metadata"]["description"] = payment.description

        async with httpx.AsyncClient(base_url=self.configuration.kopokopo_base_url) as client:
            token = await self._access_token(client)

            headers["Authorization"] = "Bearer " + token
            response = await client.post(
                f"/api/{api_version}/incoming_payments",
                json=payload,
                headers=headers,
            )

        if response.is_error:
            raise PaymentProviderError(f"Kopo Kopo STK Push failed ({response.status_code})")
        provider_response = response.json()
        return PaymentInitiated(
            id=payment_id,
            status=PAYMENT_PROCESSING,
            transaction_id=payment.transaction_id,
            amount=payment.amount,
            phone_number=payment.phone_number,
            provider="KOPOKOPO",
            provider_reference=_provider_reference(provider_response),
            provider_response=provider_response,
        )


def _provider_reference(payload: dict[str, Any]) -> str | None:
    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}
    reference = (
        payload.get("id")
        or data.get("id")
        or attributes.get("id")
        or payload.get("reference")
    )
    return str(reference) if reference else None


def _callback_value(payload: dict[str, Any], name: str) -> Any:
    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}
    metadata = payload.get("metadata") or data.get("metadata") or attributes.get("metadata") or {}
    event = attributes.get("event") or {}
    resource = event.get("resource") or {}
    return (
        payload.get(name)
        or data.get(name)
        or attributes.get(name)
        or metadata.get(name)
        or resource.get(name)
    )


def _callback_status(payload: dict[str, Any]) -> str:
    value = str(_callback_value(payload, "status") or "").lower()
    if value in {"success", "successful", "completed", "complete", "paid"}:
        return PAID
    if value in {"pending", "processing", "received", "initiated"}:
        return PAYMENT_PROCESSING
    return PAYMENT_FAILED


def _verify_callback(payload: dict[str, Any], signature: str | None, configuration: Settings) -> bool:
    if not configuration.kopokopo_webhook_secret:
        return True
    if not signature:
        return False
    digest = hmac.new(
        configuration.kopokopo_webhook_secret.encode(),
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), digest)


_payments: dict[str, PaymentStatus] = {}
_transactions: dict[str, Decimal] = {}


def register_transaction(transaction_id: str, amount: Decimal) -> None:
    _transactions[transaction_id] = amount


async def initiate_payment(payment: PaymentInitiation) -> PaymentInitiated:
    expected_amount = _transactions.get(payment.transaction_id)
    if expected_amount is None:
        raise PaymentValidationError("Transaction was not found")
    if expected_amount != payment.amount:
        raise PaymentValidationError("Payment amount does not match the transaction amount")

    payment_id = str(uuid4())
    _payments[payment_id] = PaymentStatus(
        id=payment_id,
        transaction_id=payment.transaction_id,
        status=PAYMENT_PENDING,
        amount=payment.amount,
        phone_number=payment.phone_number,
        provider="KOPOKOPO",
    )
    try:
        result = await KopoKopoClient().initiate(payment, payment_id)
    except Exception:
        _payments.pop(payment_id, None)
        raise
    _payments[payment_id] = PaymentStatus(**result.model_dump(exclude={"provider_response"}))
    return result


def process_callback(
    payload: dict[str, Any],
    signature: str | None = None,
    configuration: Settings = settings,
) -> PaymentStatus | None:
    if not _verify_callback(payload, signature, configuration):
        raise PaymentProviderError("Invalid Kopo Kopo callback signature")
    payment_id = _callback_value(payload, "payment_id")
    current = _payments.get(str(payment_id))
    if current is None:
        return None
    callback_amount = _callback_value(payload, "amount")
    if isinstance(callback_amount, dict):
        callback_amount = callback_amount.get("value")
    if callback_amount is not None and Decimal(str(callback_amount)) != current.amount:
        raise PaymentProviderError("Callback amount does not match the payment amount")
    updated = current.model_copy(update={"status": _callback_status(payload), "callback": payload})
    _payments[current.id] = updated
    return updated


def get_payment(payment_id: str) -> PaymentStatus | None:
    return _payments.get(payment_id)
