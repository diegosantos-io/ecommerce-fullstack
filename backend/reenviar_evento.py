import hashlib
import hmac
import json
import time

import requests
import stripe

from app.database.database import settings

EVENT_ID = "evt_1USN87Bm8KmEojn85HfICwUV"

stripe.api_key = settings.STRIPE_SECRET_KEY

event = stripe.Event.retrieve(EVENT_ID)
payload = json.dumps(
    event._to_dict_recursive(),
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")

timestamp = int(time.time())
signed_payload = str(timestamp).encode() + b"." + payload

signature = hmac.new(
    settings.STRIPE_WEBHOOK_SECRET.encode(),
    signed_payload,
    hashlib.sha256,
).hexdigest()

response = requests.post(
    "http://localhost:8000/pagamentos/webhook",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Stripe-Signature": f"t={timestamp},v1={signature}",
    },
    timeout=30,
)

print("HTTP:", response.status_code)
print("RESPOSTA:", response.text)
