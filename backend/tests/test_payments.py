import json
from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.payments.schemas import PaymentInitiation, PaymentStatus
from app.payments.service import (
    PAID,
    PAYMENT_PROCESSING,
    KopoKopoClient,
    _payments,
    process_callback,
    register_transaction,
)


def test_phone_number_is_normalized_to_kenyan_format() -> None:
    payment = PaymentInitiation(
        transaction_id="TX-1",
        amount="1250.00",
        phone_number="0712345678",
    )

    assert payment.phone_number == "254712345678"


@pytest.mark.asyncio
async def test_initiation_requests_k2_v2_stk_push_to_configured_till() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/v1/token":
            return httpx.Response(200, json={"access_token": "test-token"})
        return httpx.Response(201, json={"id": "provider-payment-1", "status": "received"})

    configuration = Settings(
        kopokopo_client_id="client-id",
        kopokopo_client_secret="client-secret",
        kopokopo_till_number="123456",
        payment_callback_url="https://doki.example/api/payments/kopokopo/callback",
        kopokopo_api_version="v2",
    )
    client = KopoKopoClient(configuration)
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs)  # type: ignore[assignment]
    try:
        result = await client.initiate(
            PaymentInitiation(transaction_id="TX-1", amount="50", phone_number="0712345678"),
            "payment-1",
        )
    finally:
        httpx.AsyncClient = original_client

    assert result.status == PAYMENT_PROCESSING
    assert requests[1].headers["Authorization"] == "Bearer test-token"
    assert requests[1].headers["Accept"] == "application/vnd.kopokopo.v2+json"
    assert requests[1].url.path == "/api/v2/incoming_payments"
    request_body = json.loads(requests[1].content)
    assert request_body["payment_channel"] == "M-PESA STK Push"
    assert request_body["till_number"] == "123456"
    assert request_body["subscriber"]["phone_number"] == "254712345678"
    assert request_body["metadata"]["transaction_id"] == "TX-1"


def test_callback_reads_kopokopo_event_amount() -> None:
    payment_id = "payment-kopokopo-callback"
    _payments[payment_id] = PaymentStatus(
        id=payment_id,
        transaction_id="TX-kopokopo-callback",
        status=PAYMENT_PROCESSING,
        amount=Decimal("50.00"),
        phone_number="254712345678",
        provider="KOPOKOPO",
    )

    result = process_callback(
        {
            "data": {
                "id": "provider-payment-1",
                "attributes": {
                    "status": "Success",
                    "event": {
                        "resource": {
                            "amount": "50.00",
                        }
                    },
                    "metadata": {
                        "payment_id": payment_id,
                    },
                },
            }
        }
    )

    assert result is not None
    assert result.status == PAID


def test_callback_marks_payment_paid_only_after_provider_success() -> None:
    register_transaction("TX-callback", Decimal("50.00"))

    payment = PaymentInitiation(
        transaction_id="TX-callback",
        amount="50.00",
        phone_number="0712345678",
    )
    payment_id = "payment-callback"

    _payments[payment_id] = PaymentStatus(
        id=payment_id,
        transaction_id=payment.transaction_id,
        status=PAYMENT_PROCESSING,
        amount=payment.amount,
        phone_number=payment.phone_number,
        provider="KOPOKOPO",
    )

    result = process_callback(
        {
            "status": "success",
            "metadata": {"payment_id": payment_id, "transaction_id": "TX-callback"},
            "amount": {"value": "50.00"},
        }
    )

    assert result is not None
    assert result.status == PAID
