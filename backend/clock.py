"""A clock that can be fast-forwarded.

Real TTL expiry would mean waiting out the whole verification window on every
test run. The harness therefore keeps a persisted offset in `app_state` and
adds it to the wall clock whenever a timestamp is produced or compared.

The offset lives in the database (not in process memory) so it survives
restarts and is shared by every worker.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models import AppState, utcnow

OFFSET_KEY = "time_offset_seconds"


def get_offset_seconds(db: Session) -> int:
    row = db.get(AppState, OFFSET_KEY)
    if row is None:
        return 0
    try:
        return int(row.value)
    except (TypeError, ValueError):
        return 0


def set_offset_seconds(db: Session, seconds: int) -> int:
    row = db.get(AppState, OFFSET_KEY)
    if row is None:
        row = AppState(key=OFFSET_KEY, value=str(seconds))
        db.add(row)
    else:
        row.value = str(seconds)
    db.commit()
    return seconds


def advance(db: Session, seconds: int) -> int:
    return set_offset_seconds(db, get_offset_seconds(db) + int(seconds))


def reset(db: Session) -> int:
    return set_offset_seconds(db, 0)


def now(db: Session) -> datetime:
    """Current time including the persisted fast-forward offset."""
    return utcnow() + timedelta(seconds=get_offset_seconds(db))


def as_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def as_aware(value: datetime) -> datetime:
    """Normalise a datetime to timezone-aware UTC (SQLite hands back naive values)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
