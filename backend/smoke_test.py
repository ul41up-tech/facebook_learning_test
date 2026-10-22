"""End-to-end smoke test for the API (no real email is sent).

Runs against SQLite by default so it can be executed before any Postgres /
Resend credentials exist:

    .venv\\Scripts\\python.exe smoke_test.py

Set DATABASE_URL to point it at the real Postgres database instead.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{(BACKEND / 'smoke.db').as_posix()}")
os.environ.setdefault("ENABLE_DEV_ENDPOINTS", "1")
os.environ.setdefault("SECRET_KEY", "smoke-secret")
os.environ.setdefault("PUBLIC_BASE_URL", "http://127.0.0.1:5000")

import app as app_module  # noqa: E402
from db import Base, engine  # noqa: E402

SENT: list[dict] = []


def fake_send(**kwargs):
    SENT.append(kwargs)
    return "fake-email-id"


app_module.send_verification_email = fake_send

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" - {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    with app_module.app.app_context():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    client = app_module.app.test_client()

    print("\n== registration & verification ==")
    r = client.post("/api/auth/register", json={"email": "test.user@gmail.com", "name": "測試者"})
    check("register returns 200", r.status_code == 200, r.get_data(as_text=True))
    check("verification mail dispatched", len(SENT) == 1, str(SENT))

    link = SENT[-1]["link"]
    token = link.split("token=")[-1]
    check("link points at PUBLIC_BASE_URL", link.startswith("http://127.0.0.1:5000/verify"), link)

    r = client.post("/api/auth/verify", json={"token": "not-a-real-token", "password": "password123"})
    check("bad token rejected", r.status_code == 400 and r.get_json()["error"] == "invalid_token")

    r = client.post("/api/auth/verify", json={"token": token, "password": "short"})
    check("weak password rejected", r.get_json()["error"] == "weak_password")

    r = client.post("/api/auth/verify", json={"token": token, "password": "password123", "name": "測試者"})
    check("verification succeeds", r.status_code == 200 and r.get_json()["user"]["email"] == "test.user@gmail.com",
          r.get_data(as_text=True))

    r = client.post("/api/auth/verify", json={"token": token, "password": "password123"})
    check("token cannot be reused", r.get_json()["error"] == "already_used")

    print("\n== session & feed ==")
    r = client.get("/api/me")
    check("session established", r.status_code == 200 and r.get_json()["user"]["name"] == "測試者")

    r = client.get("/api/feed")
    check("feed reachable", r.status_code == 200 and "posts" in r.get_json())

    r = client.post("/api/posts", json={"content": "第一則測試貼文", "image_url": None})
    check("post created", r.status_code == 201, r.get_data(as_text=True))
    post_id = r.get_json()["post"]["id"]

    r = client.get("/api/feed")
    posts = r.get_json()["posts"]
    check("post visible on feed", any(p["id"] == post_id for p in posts))

    r = client.post("/api/auth/logout")
    check("logout ok", r.status_code == 200)
    r = client.get("/api/me")
    check("session cleared", r.status_code == 401)

    r = client.post("/api/auth/login", json={"email": "test.user@gmail.com", "password": "wrong"})
    check("bad password rejected", r.status_code == 401)
    r = client.post("/api/auth/login", json={"email": "test.user@gmail.com", "password": "password123"})
    check("login ok", r.status_code == 200, r.get_data(as_text=True))

    print("\n== TTL expiry (time travel) ==")
    client.post("/api/auth/logout")
    r = client.post("/api/auth/register", json={"email": "ttl.user@gmail.com", "name": "TTL"})
    check("second mail dispatched", len(SENT) == 2)
    ttl_token = SENT[-1]["link"].split("token=")[-1]

    r = client.post("/api/dev/advance-time", json={"seconds": 60 * 60})
    check("clock advanced", r.status_code == 200, r.get_data(as_text=True))

    r = client.post("/api/auth/verify", json={"token": ttl_token, "password": "password123"})
    check("expired token rejected", r.get_json().get("error") == "expired_token", r.get_data(as_text=True))

    r = client.post("/api/dev/reset-time", json={})
    check("clock reset", r.status_code == 200)

    print("\n== static frontend ==")
    r = client.get("/")
    check("root serves something", r.status_code == 200)

    print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILURE(S): {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
