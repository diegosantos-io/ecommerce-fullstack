import json
import time
import hmac
import hashlib

from fastapi.testclient import TestClient
from app.main import app
from app.database.database import settings

client = TestClient(app)

def test_webhook_accepts_valid_signature_for_unrelated_event():
    payload = json.dumps({
        "id": "evt_local_signature_test",
        "type": "payment_intent.succeeded",
        "data": {"object": {}},
    }, separators=(",", ":")).encode()

    timestamp = int(time.time())
    signed_payload = str(timestamp).encode() + b"." + payload
    signature = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "stripe-signature": f"t={timestamp},v1={signature}"
    }

    response = client.post(
        "/pagamentos/webhook",
        content=payload,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}
