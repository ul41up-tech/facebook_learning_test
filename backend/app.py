"""Flask application: the API for the Facebook-clone Resend test harness."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

import clock
from config import (
    CORS_ORIGINS,
    ENABLE_DEV_ENDPOINTS,
    FRONTEND_DIST,
    MAX_ADVANCE_SECONDS,
    MIN_PASSWORD_LENGTH,
    PUBLIC_BASE_URL,
    RESEND_WEBHOOK_SECRET,
    SECRET_KEY,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    STATIC_DIR,
    VERIFY_TTL_MINUTES,
)
from db import Base, SessionLocal, engine, get_db
from mailer import MailerError, resend_configured, send_verification_email
from models import EmailEvent, Post, User, VerificationToken

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("fbclone")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def err(code: str, status: int = 400, **extra):
    payload = {"ok": False, "error": code}
    payload.update(extra)
    return jsonify(payload), status


def user_json(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }


def post_json(post: Post) -> dict:
    return {
        "id": post.id,
        "author": user_json(post.author),
        "content": post.content,
        "image_url": post.image_url,
        "created_at": clock.as_iso(post.created_at),
        "likes_count": post.likes_count,
        "comments_count": post.comments_count,
    }


def current_user(db) -> User | None:
    uid = session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)


def fake_engagement(post_id: int) -> tuple[int, int]:
    """Deterministic, plausible-looking counters (no real reactions in the MVP)."""
    seed = (post_id * 2654435761) % 997
    return 3 + seed % 288, seed % 47


# Human-readable hints for the Resend failures a tester will actually hit.
MAILER_HINTS = {
    "email_key_suspended": (
        "Resend 已暫停這把 API key（通常是先前有測試信件造成硬退信）。"
        "請到 Resend Dashboard 解除停用或建立新 key，並檢查 Suppressions 清單。"
    ),
    "email_key_invalid": (
        "Resend API key 無效（可能已被暫停或刪除）。"
        "請到 Resend Dashboard 檢查 API key 狀態，必要時建立新 key，"
        "並確認 backend\\secrets\\resend_api_key.txt 的內容。"
    ),
    "email_key_restricted": "這把 API key 權限不足（只能寄信）。寄信本身不受影響。",
    "email_rejected": (
        "Resend 拒絕了這封信。resend.dev 沙箱只能寄到 Resend 帳號自己的信箱；"
        "要寄給其他信箱請先驗證自己的網域。"
    ),
    "email_rate_limited": "寄信速度過快，請稍候再試。",
    "email_send_failed": "無法寄出驗證信，請稍後再試。",
}


# --------------------------------------------------------------------------- #
# app factory
# --------------------------------------------------------------------------- #
def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=SECRET_KEY,
        SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
        SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        JSON_AS_ASCII=False,
    )
    CORS(
        app,
        resources={r"/api/*": {"origins": [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]}},
        supports_credentials=True,
    )

    with app.app_context():
        Base.metadata.create_all(engine)

    # ------------------------------------------------------------------ #
    # health
    # ------------------------------------------------------------------ #
    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "ok": True,
                "time": clock.as_iso(clock.now(SessionLocal())),
                "resend_configured": resend_configured(),
                "public_base_url": PUBLIC_BASE_URL,
            }
        )

    # ------------------------------------------------------------------ #
    # auth
    # ------------------------------------------------------------------ #
    @app.post("/api/auth/register")
    def register():
        """Create (or re-send) a verification email. No password yet."""
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        name = (data.get("name") or "").strip()

        if not email or "@" not in email or "." not in email.split("@")[-1]:
            return err("invalid_email", 400)
        if not name:
            return err("name_required", 400)

        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None and user.is_verified:
                return err("email_taken", 409)
            if user is None:
                user = User(email=email, name=name, is_verified=False)
                db.add(user)
                db.flush()
            else:
                user.name = name or user.name

            now = clock.now(db)
            for old in user.tokens:
                if old.used_at is None:
                    old.used_at = now  # burn previous links

            raw = secrets.token_urlsafe(32)
            token = VerificationToken(
                user_id=user.id,
                token_hash=hash_token(raw),
                expires_at=now + timedelta(minutes=VERIFY_TTL_MINUTES),
                send_count=1,
            )
            db.add(token)
            db.commit()

            link = f"{PUBLIC_BASE_URL}/verify?token={raw}"
            try:
                email_id = send_verification_email(
                    to_email=email,
                    name=user.name,
                    link=link,
                    code=raw[:6].upper(),
                    ttl_minutes=VERIFY_TTL_MINUTES,
                    idempotency_key=f"verification/{token.id}",
                )
            except MailerError as exc:
                logger.error("verification email failed: %s", exc)
                token.used_at = clock.now(db)  # burn the undelivered link
                db.commit()
                # Deliberately a 4xx: Cloudflare's edge replaces the body of a
                # 5xx response with its own error page, which would hide the
                # actionable message we want the tester to see.
                return err(
                    exc.code,
                    422,
                    detail=str(exc),
                    message=MAILER_HINTS.get(exc.code, "無法寄出驗證信，請稍後再試。"),
                )

            db.add(
                EmailEvent(
                    event_type="email.sent",
                    email_id=email_id,
                    recipient=email,
                )
            )
            db.commit()

        return jsonify(
            {
                "ok": True,
                "message": f"驗證信已寄出，請查收 {email}",
                "email": email,
                "ttl_minutes": VERIFY_TTL_MINUTES,
            }
        )

    @app.post("/api/auth/resend")
    def resend_verification():
        """Alias of /api/auth/register kept for the 'resend the mail' button."""
        return register()

    @app.post("/api/auth/verify")
    def verify():
        """Consume a verification link and complete registration."""
        data = request.get_json(silent=True) or {}
        raw = (data.get("token") or "").strip()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()

        if not raw:
            return err("invalid_token", 400)

        with SessionLocal() as db:
            token = db.scalar(
                select(VerificationToken).where(VerificationToken.token_hash == hash_token(raw))
            )
            if token is None:
                return err("invalid_token", 400)
            if token.used_at is not None:
                return err("already_used", 400)

            now = clock.now(db)
            expires_at = token.expires_at
            if expires_at is not None and clock.as_aware(expires_at) <= now:
                return err("expired_token", 400)

            user = db.get(User, token.user_id)
            if user is None:
                return err("invalid_token", 400)

            if password and len(password) < MIN_PASSWORD_LENGTH:
                return err("weak_password", 400, min_length=MIN_PASSWORD_LENGTH)

            token.used_at = now
            user.is_verified = True
            if name:
                user.name = name
            if password:
                user.password_hash = generate_password_hash(password)
            db.commit()

            session.clear()
            session["user_id"] = user.id
            session.permanent = True

            return jsonify({"ok": True, "user": user_json(user)})

    @app.post("/api/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return err("invalid_credentials", 401)

        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is None or not user.password_hash:
                return err("invalid_credentials", 401)
            if not check_password_hash(user.password_hash, password):
                return err("invalid_credentials", 401)
            if not user.is_verified:
                return err("not_verified", 401)

            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            return jsonify({"ok": True, "user": user_json(user)})

    @app.post("/api/auth/logout")
    def logout():
        session.clear()
        return jsonify({"ok": True})

    @app.get("/api/me")
    def me():
        with SessionLocal() as db:
            user = current_user(db)
            if user is None:
                return err("unauthenticated", 401)
            return jsonify({"ok": True, "user": user_json(user)})

    # ------------------------------------------------------------------ #
    # feed & posts
    # ------------------------------------------------------------------ #
    @app.get("/api/feed")
    def feed():
        with SessionLocal() as db:
            user = current_user(db)
            if user is None:
                return err("unauthenticated", 401)
            try:
                limit = max(1, min(int(request.args.get("limit", 50)), 200))
            except (TypeError, ValueError):
                limit = 50
            posts = db.scalars(
                select(Post)
                .options(joinedload(Post.author))
                .order_by(Post.created_at.desc(), Post.id.desc())
                .limit(limit)
            ).all()
            return jsonify({"ok": True, "posts": [post_json(p) for p in posts]})

    @app.post("/api/posts")
    def create_post():
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        image_url = (data.get("image_url") or "").strip() or None

        with SessionLocal() as db:
            user = current_user(db)
            if user is None:
                return err("unauthenticated", 401)
            if not user.is_verified:
                return err("not_verified", 403)
            if not content and not image_url:
                return err("empty_post", 400)

            post = Post(author_id=user.id, content=content, image_url=image_url)
            db.add(post)
            db.commit()
            db.refresh(post)
            post.likes_count, post.comments_count = fake_engagement(post.id)
            db.commit()
            db.refresh(post)
            return jsonify({"ok": True, "post": post_json(post)}), 201

    # ------------------------------------------------------------------ #
    # resend webhooks
    # ------------------------------------------------------------------ #
    @app.post("/api/webhooks/resend")
    def resend_webhook():
        """Receive delivery events (delivered / opened / clicked / bounced)."""
        if not RESEND_WEBHOOK_SECRET:
            return err("webhook_not_configured", 400)
        try:
            import resend as resend_sdk
            from resend.webhooks._webhook import VerifyWebhookOptions

            raw = request.get_data(as_text=True)
            headers = {
                "svix-id": request.headers.get("svix-id", ""),
                "svix-timestamp": request.headers.get("svix-timestamp", ""),
                "svix-signature": request.headers.get("svix-signature", ""),
            }
            event = resend_sdk.Webhooks.verify(
                options=VerifyWebhookOptions(
                    payload=raw,
                    headers=headers,
                    webhook_secret=RESEND_WEBHOOK_SECRET,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("webhook verification failed: %s", exc)
            return err("invalid_signature", 400)

        event_type = getattr(event, "type", "unknown")
        data = getattr(event, "data", None)
        email_id = getattr(data, "email_id", None)
        recipients = getattr(data, "to", None) or []
        recipient = recipients[0] if recipients else None

        with SessionLocal() as db:
            db.add(
                EmailEvent(
                    event_type=event_type,
                    email_id=email_id,
                    recipient=recipient,
                    payload=raw[:8000],
                )
            )
            db.commit()

        return jsonify({"ok": True})

    # ------------------------------------------------------------------ #
    # harness-only endpoints
    # ------------------------------------------------------------------ #
    if ENABLE_DEV_ENDPOINTS:

        @app.get("/api/dev/now")
        def dev_now():
            with SessionLocal() as db:
                return jsonify(
                    {
                        "ok": True,
                        "now": clock.as_iso(clock.now(db)),
                        "offset_seconds": clock.get_offset_seconds(db),
                    }
                )

        @app.post("/api/dev/advance-time")
        def dev_advance_time():
            data = request.get_json(silent=True) or {}
            try:
                seconds = int(data.get("seconds", 0))
            except (TypeError, ValueError):
                return err("invalid_seconds", 400)
            seconds = max(-MAX_ADVANCE_SECONDS, min(seconds, MAX_ADVANCE_SECONDS))
            with SessionLocal() as db:
                clock.advance(db, seconds)
                return jsonify(
                    {
                        "ok": True,
                        "now": clock.as_iso(clock.now(db)),
                        "offset_seconds": clock.get_offset_seconds(db),
                    }
                )

        @app.post("/api/dev/reset-time")
        def dev_reset_time():
            with SessionLocal() as db:
                clock.reset(db)
                return jsonify(
                    {
                        "ok": True,
                        "now": clock.as_iso(clock.now(db)),
                        "offset_seconds": 0,
                    }
                )

        @app.get("/api/dev/email-events")
        def dev_email_events():
            with SessionLocal() as db:
                events = db.scalars(
                    select(EmailEvent).order_by(EmailEvent.id.desc()).limit(100)
                ).all()
                return jsonify(
                    {
                        "ok": True,
                        "events": [
                            {
                                "id": e.id,
                                "type": e.event_type,
                                "email_id": e.email_id,
                                "recipient": e.recipient,
                                "created_at": clock.as_iso(e.created_at),
                            }
                            for e in events
                        ],
                    }
                )

    # ------------------------------------------------------------------ #
    # static frontend (SPA)
    # ------------------------------------------------------------------ #
    @app.get("/static/<path:filename>")
    def static_files(filename: str):
        return send_from_directory(STATIC_DIR, filename)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def frontend(path: str):
        if path.startswith("api/"):
            return err("not_found", 404)
        if path:
            candidate = FRONTEND_DIST / path
            if candidate.is_file():
                return send_from_directory(FRONTEND_DIST, path)
        index = FRONTEND_DIST / "index.html"
        if index.is_file():
            return send_from_directory(FRONTEND_DIST, "index.html")
        return (
            "<h1>Facebook clone - API is running</h1>"
            "<p>前端尚未建置。請在 <code>frontend/</code> 執行 <code>npm run build</code>。</p>",
            200,
        )

    return app


app = create_app()


if __name__ == "__main__":
    from config import SECRET_KEY as _  # noqa: F401

    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
