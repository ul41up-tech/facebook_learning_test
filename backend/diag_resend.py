"""Diagnose why the Resend SDK rejects the key while raw HTTP works.

Never prints the key - only its length, a boolean, and the SDK's base URL.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests
import resend

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESEND_API_KEY  # noqa: E402

API = "https://api.resend.com"
H = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

print(f"key present      : {bool(RESEND_API_KEY)}")
print(f"key length       : {len(RESEND_API_KEY)}")
print(f"starts with 're_': {RESEND_API_KEY.startswith('re_')}")
print(f"has whitespace   : {RESEND_API_KEY != RESEND_API_KEY.strip()}")
print(f"has quotes       : {'\"' in RESEND_API_KEY or chr(39) in RESEND_API_KEY}")
print(f"sdk api_url      : {resend.api_url}")

print("\n[1] raw HTTP, no idempotency key")
r = requests.post(
    f"{API}/emails",
    headers=H,
    json={
        "from": "Facebook <onboarding@resend.dev>",
        "to": ["delivered@resend.dev"],
        "subject": "diag 1",
        "text": "diag",
    },
    timeout=30,
)
print(f"    HTTP {r.status_code}: {r.text[:200]}")

print("\n[2] raw HTTP, with idempotency key")
r = requests.post(
    f"{API}/emails",
    headers={**H, "Idempotency-Key": "verification/diag-2"},
    json={
        "from": "Facebook <onboarding@resend.dev>",
        "to": ["delivered@resend.dev"],
        "subject": "diag 2",
        "text": "diag",
    },
    timeout=30,
)
print(f"    HTTP {r.status_code}: {r.text[:200]}")

print("\n[3] SDK without options")
resend.api_key = RESEND_API_KEY
try:
    resp = resend.Emails.send(
        {
            "from": "Facebook <onboarding@resend.dev>",
            "to": ["delivered@resend.dev"],
            "subject": "diag 3",
            "text": "diag",
        }
    )
    print(f"    OK -> {getattr(resp, 'id', resp)}")
except Exception as exc:  # noqa: BLE001
    print(f"    ERROR {type(exc).__name__}: {exc}")

print("\n[4] SDK with idempotency key")
try:
    resp = resend.Emails.send(
        {
            "from": "Facebook <onboarding@resend.dev>",
            "to": ["delivered@resend.dev"],
            "subject": "diag 4",
            "text": "diag",
        },
        options={"idempotency_key": "verification/diag-4"},
    )
    print(f"    OK -> {getattr(resp, 'id', resp)}")
except Exception as exc:  # noqa: BLE001
    print(f"    ERROR {type(exc).__name__}: {exc}")
