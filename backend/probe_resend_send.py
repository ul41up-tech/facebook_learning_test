"""Determine what the resend.dev sandbox is allowed to deliver to.

Uses the key from the secret file (never printed). Sends at most one real
message, and only to Resend's own documented test mailbox plus one
deliberately non-existent gmail-formatted address.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESEND_API_KEY  # noqa: E402

API = "https://api.resend.com"
H = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

TESTS = [
    ("resend official test mailbox", "delivered@resend.dev"),
    ("gmail-formatted (deliberately non-existent)", "zzz.no.such.account.qwerty123@gmail.com"),
]


def main() -> None:
    for label, to_addr in TESTS:
        resp = requests.post(
            f"{API}/emails",
            headers=H,
            json={
                "from": "Facebook <onboarding@resend.dev>",
                "to": [to_addr],
                "subject": "Resend sandbox capability probe",
                "text": "probe",
            },
            timeout=30,
        )
        print(f"\n--- {label} -> {to_addr} ---")
        print(f"HTTP {resp.status_code}: {resp.text[:400]}")


if __name__ == "__main__":
    main()
