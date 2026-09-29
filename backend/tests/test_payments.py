import json

import httpx
import pytest

from app.core.config import Settings
from app.payments.schemas import PaymentInitiation
from app.payments.service import KopoKopoClient


def test_phone_number_is_normalized_to_kenyan_format() -> None:
    payment = PaymentInitiation(amount="1250.00", phone_number="0712345678", reference="TX-1")

    assert payment.phone_number == "254712345678"


@pytest.mark.asyncio
async def test_initiation_requests_stk_push() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/v1/token":
            return httpx.Response(200, json={"access_token": "test-token"})
        return httpx.Response(201, json={"status": "received"})

    configuration = Settings(
        kopokopo_client_id="client-id",
        kopokopo_client_secret="client-secret",
        kopokopo_till_number="123456",
        payment_callback_url="https://doki.example/callback",
    )
    client = KopoKopoClient(configuration)
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs)  # type: ignore[assignment]
    try:
        result = await client.initiate(
            PaymentInitiation(amount="50", phone_number="0712345678", reference="TX-1")
        )
    finally:
        httpx.AsyncClient = original_client

    assert result.status == "pending"
    assert requests[1].headers["Authorization"] == "Bearer test-token"
    request_body = json.loads(requests[1].content)
    assert request_body["payment_method"] == "mpesa_stk_push"
    assert request_body["subscriber"]["phone_number"] == "254712345678"