"""Probe the Resend account using the key from the secret file (never printed).

Only non-secret metadata is shown: domains, sandbox status and the mailbox the
sandbox is allowed to deliver to.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESEND_API_KEY, RESEND_FROM  # noqa: E402

API = "https://api.resend.com"
H = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}


def show(label: str, resp) -> None:
    print(f"\n--- {label} [{resp.status_code}] ---")
    try:
        print(resp.text[:1200])
    except Exception:
        print("<no body>")


def main() -> None:
    print(f"key present: {bool(RESEND_API_KEY)}  (length {len(RESEND_API_KEY)})")
    print(f"configured from: {RESEND_FROM}")

    show("GET /domains", requests.get(f"{API}/domains", headers=H, timeout=30))

    for path in ("/domains/resend.dev", "/account", "/emails?limit=5"):
        show(f"GET {path}", requests.get(f"{API}{path}", headers=H, timeout=30))

    # Which address does the sandbox allow? Probe it with a harmless validation
    # call (no email is sent - the API rejects an unverified `from` first).
    probe = requests.post(
        f"{API}/emails",
        headers=H,
        json={"from": "Facebook <onboarding@resend.dev>", "to": ["probe@example.com"], "subject": "probe", "text": "probe"},
        timeout=30,
    )
    show("POST /emails (probe, no deliver)", probe)


if __name__ == "__main__":
    main()
