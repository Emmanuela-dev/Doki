"""
End-to-end test of the Kopo Kopo M-Pesa STK Push integration.

Runs the real FastAPI application (app.main) over HTTP via TestClient,
intercepts the outbound Kopo Kopo request with an httpx MockTransport,
and verifies the full STK Push payload is sent correctly. Also exercises
the callback/webhook endpoint to confirm payment status updates.
"""
import base64
import hashlib
import hmac
import json
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.payments.service import PAID, PAYMENT_PROCESSING, register_transaction


def _basic_auth(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def _sign(payload: dict[str, object], secret: str) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def client_and_requests(monkeypatch):
    """Start the real app and capture outbound Kopo Kopo requests."""
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/v1/token":
            return httpx.Response(200, json={"access_token": "test-access-token"})
        return httpx.Response(
            201,
            json={
                "id": "provider-payment-e2e",
                "status": "received",
                "data": {
                    "id": "provider-payment-e2e",
                    "attributes": {
                        "status": "Success",
                        "event": {
                            "resource": {
                                "amount": "50.00",
                                "payment_id": "payment-e2e",
                            }
                        },
                    },
                },
            },
        )

    original_client = httpx.AsyncClient

    def patched_client(**kwargs):
        return original_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", patched_client)

    # Import app *after* patching so the service module uses the patched client.
    from app.main import app  # noqa: WPS433

    with TestClient(app) as test_client:
        yield test_client, requests


def test_stk_push_sends_mpesa_request_to_kopokopo(client_and_requests):
    client, requests = client_and_requests

    register_transaction("TX-E2E", Decimal("50.00"))

    response = client.post(
        "/api/payments/kopokopo/stk-push",
        json={
            "transaction_id": "TX-E2E",
            "amount": "50.00",
            "phone_number": "0712345678",
            "description": "E2E test payment",
        },
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["provider"] == "KOPOKOPO"
    assert body["status"] == PAYMENT_PROCESSING
    assert body["phone_number"] == "254712345678"
    assert body["provider_reference"] == "provider-payment-e2e"

    # The STK push must have been sent to Kopo Kopo.
    assert len(requests) == 2
    token_request, stk_request = requests

    # Auth request uses the configured client id/secret.
    assert token_request.url.path == "/oauth/v1/token"
    assert token_request.headers["Authorization"] == _basic_auth(
        settings.kopokopo_client_id, settings.kopokopo_client_secret
    )

    # STK push request
    assert stk_request.url.path == "/api/v2/incoming_payments"
    assert stk_request.headers["Authorization"] == "Bearer test-access-token"
    assert stk_request.headers["Accept"] == "application/vnd.kopokopo.v2+json"
    assert stk_request.headers["Content-Type"] == "application/vnd.kopokopo.v2+json"

    payload = json.loads(stk_request.content)
    assert payload["payment_channel"] == "M-PESA STK Push"
    assert payload["till_number"] == settings.kopokopo_till_number
    assert payload["subscriber"]["phone_number"] == "254712345678"
    assert payload["amount"] == {"currency": "KES", "value": "50.00"}
    assert payload["metadata"]["transaction_id"] == "TX-E2E"
    assert payload["metadata"]["description"] == "E2E test payment"
    assert payload["_links"]["callback_url"] == settings.payment_callback_url


def test_callback_marks_payment_paid(client_and_requests):
    client, _requests = client_and_requests

    register_transaction("TX-CB", Decimal("50.00"))

    # Trigger a payment so the internal _payments registry has the record.
    stk = client.post(
        "/api/payments/kopokopo/stk-push",
        json={
            "transaction_id": "TX-CB",
            "amount": "50.00",
            "phone_number": "0712345678",
        },
    )
    assert stk.status_code == 202
    payment_id = stk.json()["id"]

    # Simulate Kopo Kopo sending a signed successful callback.
    callback_payload = {
        "data": {
            "id": "provider-payment-cb",
            "attributes": {
                "status": "Success",
                "event": {
                    "resource": {
                        "amount": "50.00",
                        "payment_id": payment_id,
                    }
                },
                "metadata": {"payment_id": payment_id},
            },
        }
    }
    headers = {}
    if settings.kopokopo_webhook_secret:
        headers["x-kopokopo-signature"] = _sign(callback_payload, settings.kopokopo_webhook_secret)

    callback = client.post(
        "/api/payments/kopokopo/callback",
        json=callback_payload,
        headers=headers,
    )

    assert callback.status_code == 202, callback.text
    assert callback.json()["status"] == PAID

    status = client.get(f"/api/payments/kopokopo/status/{payment_id}")
    assert status.status_code == 200
    assert status.json()["status"] == PAID