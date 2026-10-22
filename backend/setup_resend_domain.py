"""Set up a real sending domain in Resend (option B) and wire its DNS to Cloudflare.

Why this exists
---------------
`onboarding@resend.dev` is a sandbox: it can only deliver to the mailbox that
owns the Resend account. To email *arbitrary* Gmail addresses you need a
sending domain you control, verified through DNS. The website itself still runs
on the Cloudflare quick tunnel (trycloudflare.com) - only the *sender* uses
your own domain.

Flow
----
    1. Read the domain from `secrets/resend_domain.txt`.
    2. Create the domain in Resend (POST https://api.resend.com/domains).
    3. If `secrets/cloudflare_api_token.txt` holds a token, push the returned
       DNS records into Cloudflare automatically. Otherwise print them so you
       can add them by hand.
    4. Ask Resend to re-check the verification status.

Secrets are read straight from the files and never printed.

    .venv\\Scripts\\python.exe setup_resend_domain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from config import RESEND_API_KEY, SECRETS_DIR, read_secret_file  # noqa: E402

RESEND_API = "https://api.resend.com"
CF_API = "https://api.cloudflare.com/client/v4"

CF_API_TOKEN = read_secret_file(SECRETS_DIR / "cloudflare_api_token.txt")
DOMAIN = read_secret_file(SECRETS_DIR / "resend_domain.txt")


def die(msg: str) -> None:
    print(f"\n[ERROR] {msg}\n", file=sys.stderr)
    raise SystemExit(1)


def resend_headers() -> dict:
    return {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}


def cf_headers() -> dict:
    return {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}


def create_domain(domain: str) -> dict:
    existing = requests.get(f"{RESEND_API}/domains", headers=resend_headers(), timeout=30)
    if existing.status_code == 200:
        for item in existing.json().get("data", []):
            if item.get("name") == domain:
                print(f"[ok  ] domain '{domain}' already exists in Resend (id={item.get('id')})")
                return item

    resp = requests.post(
        f"{RESEND_API}/domains",
        headers=resend_headers(),
        json={"name": domain},
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        die(f"Resend domain creation failed: {resp.status_code} {resp.text[:400]}")
    data = resp.json()
    print(f"[ok  ] created domain '{domain}' in Resend (id={data.get('id')})")
    return data


def get_domain(domain_id: str) -> dict:
    resp = requests.get(f"{RESEND_API}/domains/{domain_id}", headers=resend_headers(), timeout=30)
    if resp.status_code != 200:
        die(f"Resend domain lookup failed: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def trigger_verify(domain_id: str) -> dict:
    resp = requests.post(
        f"{RESEND_API}/domains/{domain_id}/verify", headers=resend_headers(), timeout=30
    )
    if resp.status_code not in (200, 201, 202):
        return {"error": f"{resp.status_code} {resp.text[:200]}"}
    return resp.json()


def cloudflare_zone(domain: str) -> dict | None:
    resp = requests.get(
        f"{CF_API}/zones", headers=cf_headers(), params={"name": domain}, timeout=30
    )
    if resp.status_code != 200:
        return None
    zones = resp.json().get("result") or []
    return zones[0] if zones else None


def to_cloudflare_record(record: dict) -> dict | None:
    """Translate a Resend DNS record into a Cloudflare DNS record payload."""
    rtype = (record.get("type") or "").upper()
    name = (record.get("name") or "").strip()
    value = (record.get("value") or "").strip()
    if not rtype or not name or not value:
        return None

    cf_type = rtype
    content = value
    priority = record.get("priority")

    if rtype == "MX":
        cf_type = "MX"
    elif rtype == "TXT":
        content = value  # Resend already includes the surrounding quotes
    elif rtype == "CNAME":
        cf_type = "CNAME"

    payload: dict = {
        "type": cf_type,
        "name": name,
        "content": content,
        "ttl": 3600,
        "proxied": False,
    }
    if cf_type == "MX" and priority is not None:
        payload["priority"] = int(priority)
    return payload


def upsert_cf_record(zone_id: str, payload: dict) -> tuple[bool, str]:
    name = payload["name"]
    existing = requests.get(
        f"{CF_API}/zones/{zone_id}/dns_records",
        headers=cf_headers(),
        params={"type": payload["type"], "name": name},
        timeout=30,
    )
    if existing.status_code == 200 and existing.json().get("result"):
        rec_id = existing.json()["result"][0]["id"]
        resp = requests.put(
            f"{CF_API}/zones/{zone_id}/dns_records/{rec_id}",
            headers=cf_headers(),
            json=payload,
            timeout=30,
        )
        return resp.status_code in (200, 201), f"updated {payload['type']} {name}"
    resp = requests.post(
        f"{CF_API}/zones/{zone_id}/dns_records", headers=cf_headers(), json=payload, timeout=30
    )
    return resp.status_code in (200, 201), f"created {payload['type']} {name}"


def print_manual_records(records: list[dict]) -> None:
    print("\n--- add these DNS records in Cloudflare -----------------------------------")
    print(f"{'TYPE':<8} {'NAME':<40} {'VALUE':<60} PRI")
    for r in records:
        print(f"{r.get('type',''):<8} {r.get('name',''):<40} {r.get('value',''):<60} {r.get('priority','')}")
    print("---------------------------------------------------------------------------\n")


def main() -> int:
    if not RESEND_API_KEY:
        die("RESEND_API_KEY is empty - fill in secrets/resend_api_key.txt first.")
    if not DOMAIN:
        die("No sending domain - fill in secrets/resend_domain.txt first.")

    print(f"[*] target sending domain: {DOMAIN}")

    domain = create_domain(DOMAIN)
    domain_id = domain.get("id")
    if not domain_id:
        die(f"Resend did not return a domain id: {domain}")

    records = get_domain(domain_id).get("records") or []

    if CF_API_TOKEN:
        zone = cloudflare_zone(DOMAIN)
        if not zone:
            print(
                f"[warn] domain '{DOMAIN}' is not a zone in this Cloudflare account.\n"
                f"       Add it to Cloudflare first (nameservers), then re-run."
            )
        else:
            zone_id = zone["id"]
            print(f"[ok  ] Cloudflare zone found (id={zone_id})")
            for record in records:
                payload = to_cloudflare_record(record)
                if payload is None:
                    continue
                ok, msg = upsert_cf_record(zone_id, payload)
                print(f"[{'ok  ' if ok else 'fail'}] Cloudflare DNS: {msg}")
                if not ok:
                    print_manual_records([record])
    else:
        print("[info] no Cloudflare API token found - here are the records to add by hand.")
        print_manual_records(records)

    result = trigger_verify(domain_id)
    print(f"[*] verification check: {result}")

    status = get_domain(domain_id).get("status")
    print(f"\n[*] Resend domain status: {status}")
    if status == "verified":
        print(f"""
    GREAT - you can now send from any address on {DOMAIN}.
    Update backend/.env:
        RESEND_FROM=Facebook <no-reply@{DOMAIN}>
""")
    else:
        print(f"""
    The domain still needs to be verified. If you added the records by hand,
    DNS propagation can take a few minutes. Re-run this script to check again.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
