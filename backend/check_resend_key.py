"""Safe health check for the Resend API key.

Never sends an email - it only asks Resend to describe the key, so it can be
run repeatedly without any risk to sender reputation.

    .venv\\Scripts\\python.exe check_resend_key.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESEND_API_KEY, RESEND_FROM  # noqa: E402

API = "https://api.resend.com"
H = {"Authorization": f"Bearer {RESEND_API_KEY}"}


def main() -> int:
    if not RESEND_API_KEY:
        print("FAIL  no key in backend/secrets/resend_api_key.txt")
        return 2

    resp = requests.get(f"{API}/domains", headers=H, timeout=30)
    print(f"key length : {len(RESEND_API_KEY)}")
    print(f"from       : {RESEND_FROM}")

    if resp.status_code == 200:
        domains = resp.json().get("data") or []
        print("STATUS: OK (full-access key)")
        for d in domains:
            print(f"  - {d.get('name')}  [{d.get('status')}]")
        if not domains:
            print("  (no sending domains yet - the resend.dev sandbox is still usable)")
        return 0

    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    name = payload.get("name", "")
    message = payload.get("message", "")

    if name == "restricted_api_key":
        print("STATUS: OK (send-only key - can send, cannot manage domains)")
        return 0
    if name == "suspended_api_key":
        print("STATUS: SUSPENDED")
        print(f"  {message}")
        print("  -> create a new key in the Resend dashboard and put it in")
        print("     backend/secrets/resend_api_key.txt")
        return 1
    if name in {"invalid_api_key", "not_found"} or resp.status_code == 401:
        print("STATUS: INVALID")
        print(f"  {message}")
        return 1

    print(f"STATUS: UNKNOWN ({resp.status_code})")
    print(f"  {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
