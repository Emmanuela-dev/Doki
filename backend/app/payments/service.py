from typing import Any
from uuid import uuid4

import httpx

from app.core.config import Settings, settings
from app.payments.schemas import PaymentInitiation, PaymentInitiated, PaymentStatus


class PaymentProviderError(RuntimeError):
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

    async def initiate(self, payment: PaymentInitiation) -> PaymentInitiated:
        self._validate_configuration()
        payment_id = str(uuid4())
        api_version = self.configuration.kopokopo_api_version
        headers = {
            "Accept": f"application/vnd.kopokopo.{api_version}+json",
            "Content-Type": f"application/vnd.kopokopo.{api_version}+json",
        }
        payload = {
            "payment_method": "mpesa_stk_push",
            "till_number": self.configuration.kopokopo_till_number,
            "subscriber": {"phone_number": payment.phone_number},
            "amount": {"currency": "KES", "value": str(payment.amount)},
            "metadata": {"payment_id": payment_id, "reference": payment.reference},
            "_links": {"callback_url": self.configuration.payment_callback_url},
        }
        if payment.description:
            payload["metadata"]["description"] = payment.description

        async with httpx.AsyncClient(base_url=self.configuration.kopokopo_base_url) as client:
            token = await self._access_token(client)
            headers["Authorization"] = f"Bearer {token}"
            response = await client.post("/api/v1/incoming_payments", json=payload, headers=headers)

        if response.is_error:
            raise PaymentProviderError(f"Kopo Kopo payment initiation failed ({response.status_code})")
        provider_response = response.json()
        return PaymentInitiated(
            id=payment_id,
            status="pending",
            reference=payment.reference,
            amount=payment.amount,
            phone_number=payment.phone_number,
            provider_response=provider_response,
        )


_payments: dict[str, PaymentStatus] = {}


async def initiate_payment(payment: PaymentInitiation) -> PaymentInitiated:
    result = await KopoKopoClient().initiate(payment)
    _payments[result.id] = PaymentStatus(
        id=result.id,
        reference=result.reference,
        status=result.status,
        amount=result.amount,
        phone_number=result.phone_number,
    )
    return result


def process_callback(payload: dict[str, Any]) -> PaymentStatus | None:
    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}
    metadata = payload.get("metadata") or data.get("metadata") or attributes.get("metadata") or {}
    payment_id = metadata.get("payment_id")
    if not payment_id or payment_id not in _payments:
        return None
    status = str(payload.get("status") or data.get("status") or attributes.get("status") or "completed").lower()
    current = _payments[payment_id]
    updated = current.model_copy(update={"status": status, "callback": payload})
    _payments[payment_id] = updated
    return updated


def get_payment(payment_id: str) -> PaymentStatus | None:
    return _payments.get(payment_id)