"""Central configuration for the Facebook-clone test harness.

Secrets are NEVER read from this file and NEVER printed by it.
Two secret files are supported, both under `backend/secrets/`:

    secrets/resend_api_key.txt   -> the Resend API key (one line)
    secrets/pg_password.txt      -> the local PostgreSQL password (one line)

Lines starting with `#` and blank lines are ignored, so the files can carry
short instructions above the actual value.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"
STATIC_DIR = BASE_DIR / "static"
SECRETS_DIR = BASE_DIR / "secrets"

load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------------------------------- #
# secret helpers - read a value from a file without ever exposing it
# --------------------------------------------------------------------------- #
def read_secret_file(path: Path) -> str:
    """Return the secret stored in a file, without ever logging it.

    Rules:
      * blank lines and lines starting with `#` are ignored
      * a line of the form ``KEY=value`` yields ``value`` (so the template file
        can show the exact syntax to fill in)
      * a line of the form ``KEY=`` (empty value) counts as *not filled in yet*
      * anything else is taken verbatim
    """
    try:
        if not path.is_file():
            return ""
        for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = raw.strip().lstrip("\ufeff")
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                if key.strip().replace("_", "").isalnum() and key.strip().isupper():
                    value = value.strip().strip('"').strip("'")
                    if value:
                        return value
                    continue  # empty placeholder -> keep looking further down
            return line
    except OSError:
        return ""
    return ""


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# --- Flask -----------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# --- Database --------------------------------------------------------------
# Priority: explicit DATABASE_URL > secrets/pg_password.txt > built-in default.
PG_USER = os.getenv("PG_USER", "postgres")
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "facebook_clone")

_pg_password = read_secret_file(SECRETS_DIR / "pg_password.txt")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.environ["DATABASE_URL"]
elif _pg_password:
    DATABASE_URL = (
        f"postgresql+psycopg://{quote_plus(PG_USER)}:{quote_plus(_pg_password)}"
        f"@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )
else:
    DATABASE_URL = f"postgresql+psycopg://{PG_USER}:postgres@{PG_HOST}:{PG_PORT}/{PG_DB}"

# --- Public URL (used to build the verification link inside the email) ------
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:5055").rstrip("/")

# --- Resend ----------------------------------------------------------------
# Priority: env var > secrets/resend_api_key.txt
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip() or read_secret_file(
    SECRETS_DIR / "resend_api_key.txt"
)
RESEND_FROM = os.getenv("RESEND_FROM", "Facebook <onboarding@resend.dev>")
RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET", "").strip() or read_secret_file(
    SECRETS_DIR / "resend_webhook_secret.txt"
)

# --- Verification ----------------------------------------------------------
# How long a verification link stays valid. Must comfortably exceed real Gmail
# delivery latency (1-30s, sometimes more) while still being short enough to
# observe expiry without waiting forever.
VERIFY_TTL_MINUTES = _int("VERIFY_TTL_MINUTES", 15)
MIN_PASSWORD_LENGTH = _int("MIN_PASSWORD_LENGTH", 8)

# --- Test-harness switches -------------------------------------------------
# The time-travel endpoints let you fast-forward the clock so TTL expiry can
# be exercised in seconds instead of minutes.
ENABLE_DEV_ENDPOINTS = _bool("ENABLE_DEV_ENDPOINTS", True)
MAX_ADVANCE_SECONDS = _int("MAX_ADVANCE_SECONDS", 60 * 60 * 24 * 30)

SEED_PASSWORD = os.getenv("SEED_PASSWORD", "password123")
