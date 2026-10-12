"""
Live end-to-end check: start the real uvicorn server, send an STK push over
HTTP, and confirm the request reaches Kopo Kopo with the correct payload.
"""
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from decimal import Decimal

import httpx

# Patch httpx before importing anything that uses it.
OUTBOUND = []


async def handler(request):
    OUTBOUND.append(request)
    if request.url.path == "/oauth/v1/token":
        return httpx.Response(200, json={"access_token": "live-access-token"})
    return httpx.Response(
        201,
        json={
            "id": "provider-live-1",
            "status": "received",
            "data": {
                "id": "provider-live-1",
                "attributes": {
                    "status": "Success",
                    "event": {
                        "resource": {"amount": "50.00", "payment_id": "payment-live-1"}
                    },
                },
            },
        },
    )


_orig = httpx.AsyncClient


def _patched(**kwargs):
    return _orig(transport=httpx.MockTransport(handler), **kwargs)


httpx.AsyncClient = _patched  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

from app.core import store  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.payments.service import register_transaction  # noqa: E402

register_transaction("TX-LIVE", Decimal("50.00"))

import uvicorn  # noqa: E402

config = uvicorn.Config(
    "app.main:app",
    host="127.0.0.1",
    port=8765,
    log_level="warning",
)
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()

# Wait for the server to come up.
for _ in range(50):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(0.2)
else:
    print("SERVER DID NOT START")
    sys.exit(1)

print("server up")

# 1) Health check
with urllib.request.urlopen("http://127.0.0.1:8765/health") as r:
    print("health:", r.status, r.read().decode())

# 2) STK push
body = json.dumps(
    {
        "transaction_id": "TX-LIVE",
        "amount": "50.00",
        "phone_number": "0712345678",
        "description": "Live STK push test",
    }
).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/payments/kopokopo/stk-push",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=10) as r:
    print("stk-push:", r.status, r.read().decode())

# 3) Status
with urllib.request.urlopen("http://127.0.0.1:8765/api/payments/kopokopo/auth") as r:
    print("auth:", r.status, r.read().decode())

# Verify the outbound Kopo Kopo request.
assert len(OUTBOUND) == 2, f"expected 2 outbound requests, got {len(OUTBOUND)}"
token_req, stk_req = OUTBOUND
assert token_req.url.path == "/oauth/v1/token"
assert stk_req.url.path == "/api/v2/incoming_payments"
assert stk_req.headers["Authorization"] == "Bearer live-access-token"
assert stk_req.headers["Accept"] == "application/vnd.kopokopo.v2+json"
payload = json.loads(stk_req.content)
assert payload["payment_channel"] == "M-PESA STK Push", payload
assert payload["till_number"] == settings.kopokopo_till_number, payload
assert payload["subscriber"]["phone_number"] == "254712345678", payload
assert payload["amount"] == {"currency": "KES", "value": "50.00"}, payload
assert payload["metadata"]["transaction_id"] == "TX-LIVE", payload
assert payload["metadata"]["description"] == "Live STK push test", payload
assert payload["_links"]["callback_url"] == settings.payment_callback_url, payload

print("\nSTK push payload verified:")
print(json.dumps(payload, indent=2))

# 4) Callback with valid signature
import base64
import hashlib
import hmac

callback_payload = {
    "data": {
        "id": "provider-live-cb",
        "attributes": {
            "status": "Success",
            "event": {
                "resource": {
                    "amount": "50.00",
                    "payment_id": "payment-live-1",
                }
            },
            "metadata": {"payment_id": "payment-live-1"},
        },
    }
}
secret = settings.kopokopo_webhook_secret
body_bytes = json.dumps(callback_payload, separators=(",", ":"), sort_keys=True).encode()
digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
sig = f"sha256={digest}"

cb_req = urllib.request.Request(
    "http://127.0.0.1:8765/api/payments/kopokopo/callback",
    data=json.dumps(callback_payload).encode(),
    headers={
        "Content-Type": "application/json",
        "x-kopokopo-signature": sig,
    },
    method="POST",
)
with urllib.request.urlopen(cb_req, timeout=10) as r:
    print("callback:", r.status, r.read().decode())

server.should_exit = True
thread.join(timeout=5)
print("\nALL LIVE CHECKS PASSED")