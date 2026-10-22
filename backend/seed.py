"""Create the schema and seed Facebook-like demo content.

Seed accounts are pre-verified (no email round-trip) so the feed is populated
the moment a new user completes registration. All avatars / post images are
generated locally as SVG, so the app works fully offline; they can later be
swapped for qianpro-generated images (see qianpro_seed.py).
"""

from __future__ import annotations

import hashlib
import html
import random
from datetime import timedelta

from sqlalchemy import select
from werkzeug.security import generate_password_hash

import clock
from config import SEED_PASSWORD, STATIC_DIR
from db import Base, SessionLocal, engine
from models import Post, User, VerificationToken

SEED_DIR = STATIC_DIR / "seed"

SEED_USERS = [
    ("yating.chen@gmail.com", "陳雅婷", "#1877f2"),
    ("zhihao.lin@gmail.com", "林志豪", "#42b72a"),
    ("xiaomei.wang@gmail.com", "王小美", "#f7b125"),
    ("jiahao.zhang@gmail.com", "張家豪", "#8a56d6"),
    ("xinyi.li@gmail.com", "李欣怡", "#e5534b"),
    ("jianwen.huang@gmail.com", "黃建文", "#17bf63"),
    ("peishan.wu@gmail.com", "吳佩珊", "#f45b69"),
    ("junjie.liu@gmail.com", "劉俊傑", "#3b82f6"),
    ("mingling.tsai@gmail.com", "蔡明玲", "#a855f7"),
    ("wenhao.cheng@gmail.com", "鄭文豪", "#0ea5e9"),
]

SEED_POSTS = [
    ("yating.chen@gmail.com", "今天天氣終於放晴了，決定去淡水老街走一圈。\n沿著河堤吹風的時候突然覺得，手機滑一整天也沒有真的走出門重要。", 1),
    ("zhihao.lin@gmail.com", "這個月的專案終於結案，決定犒賞自己一頓好的。\n加班到很晚是值得的 ✌️", 2),
    ("xiaomei.wang@gmail.com", "週末的早晨，咖啡、書本，還有一隻不肯起床的貓。", 3),
    ("jiahao.zhang@gmail.com", "新的辦公室座位整理好了，終於不用背對著螢幕了。", 4),
    ("xinyi.li@gmail.com", "跑了 5 公里，第一次覺得呼吸是件很奢侈的事。", 5),
    ("jianwen.huang@gmail.com", "剛把家裡那台老電視淘汰掉，換了一台新的。\n開機的瞬間還是有那種國中時代的期待感。", 6),
    ("peishan.wu@gmail.com", "同事今天分享了一包很好吃的鳳梨酥，辦公室瞬間變成下午茶時間。", 7),
    ("mingling.tsai@gmail.com", "整理相簿的時候翻到五年前的照片，時間真的過得比想像中快。", 8),
    ("wenhao.cheng@gmail.com", "看完《臥虎藏龍》，重點依然是那個「慢慢來」的人生哲學。", 9),
    ("yating.chen@gmail.com", "有人推薦我這家店的明太子義大利麵，結果我直接噴飯。真的很好吃。", 10),
]


# --------------------------------------------------------------------------- #
# local SVG assets
# --------------------------------------------------------------------------- #
def _initials(name: str) -> str:
    return name[:2]


def write_avatar_svg(name: str, color: str, index: int) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs><linearGradient id="g{index}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{color}"/><stop offset="100%" stop-color="{shade(color)}"/>
  </linearGradient></defs>
  <rect width="200" height="200" fill="url(#g{index})"/>
  <circle cx="100" cy="78" r="34" fill="rgba(255,255,255,0.92)"/>
  <path d="M32 200c0-38 30-62 68-62s68 24 68 62z" fill="rgba(255,255,255,0.92)"/>
  <text x="100" y="184" font-family="Arial, sans-serif" font-size="26" font-weight="700"
        fill="{color}" text-anchor="middle">{html.escape(_initials(name))}</text>
</svg>"""
    path = SEED_DIR / f"avatar-{index}.svg"
    path.write_text(svg, encoding="utf-8")
    return f"/static/seed/{path.name}"


def write_post_svg(index: int, title: str) -> str:
    palettes = [
        ("#4a90d9", "#7b5ea7"),
        ("#f2994a", "#eb5757"),
        ("#27ae60", "#2f80ed"),
        ("#9b51e0", "#2d9cdb"),
        ("#eb5757", "#f2994a"),
        ("#56ccf2", "#2f80ed"),
        ("#6fcf97", "#27ae60"),
        ("#bb6bd9", "#8a56d6"),
        ("#f2c94c", "#f2994a"),
        ("#219653", "#56ccf2"),
    ]
    c1, c2 = palettes[index % len(palettes)]
    rng = random.Random(index * 7919)
    shapes = []
    for i in range(6):
        x = rng.randint(0, 800)
        y = rng.randint(0, 500)
        r = rng.randint(40, 160)
        op = round(rng.uniform(0.08, 0.28), 3)
        shapes.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" opacity="{op}"/>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
  <defs><linearGradient id="p{index}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
  </linearGradient></defs>
  <rect width="800" height="500" fill="url(#p{index})"/>
  {''.join(shapes)}
  <text x="40" y="452" font-family="'PingFang TC','Microsoft JhengHei',Arial,sans-serif"
        font-size="30" fill="rgba(255,255,255,0.9)" font-weight="600">{html.escape(title)}</text>
</svg>"""
    path = SEED_DIR / f"post-{index}.svg"
    path.write_text(svg, encoding="utf-8")
    return f"/static/seed/{path.name}"


def avatar_url(name: str, color: str, index: int) -> str:
    """Prefer a qianpro-generated photo; fall back to the local SVG placeholder."""
    photo = SEED_DIR / f"avatar-{index}.jpg"
    if photo.is_file() and photo.stat().st_size > 1024:
        return f"/static/seed/{photo.name}"
    return write_avatar_svg(name, color, index)


def post_image_url(index: int, title: str) -> str:
    photo = SEED_DIR / f"post-{index}.jpg"
    if photo.is_file() and photo.stat().st_size > 1024:
        return f"/static/seed/{photo.name}"
    return write_post_svg(index, title)


def shade(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * 0.6), int(g * 0.6), int(b * 0.6))


# --------------------------------------------------------------------------- #
# seeding
# --------------------------------------------------------------------------- #
def seed(reset: bool = False) -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if reset:
            db.query(VerificationToken).delete()
            db.query(Post).delete()
            db.query(User).delete()
            db.commit()

        avatars: dict[str, str] = {}
        for idx, (email, name, color) in enumerate(SEED_USERS, start=1):
            avatars[email] = avatar_url(name, color, idx)

        now = clock.now(db)
        for email, name, _color in SEED_USERS:
            exists = db.scalar(select(User).where(User.email == email))
            if exists:
                continue
            db.add(
                User(
                    email=email,
                    name=name,
                    password_hash=generate_password_hash(SEED_PASSWORD),
                    avatar_url=avatars[email],
                    is_verified=True,
                    is_seed=True,
                )
            )
        db.commit()

        post_images = {
            i: post_image_url(
                i,
                title,
            )
            for i, title in enumerate(
                [
                    "淡水老街的河堤",
                    "值得的一頓",
                    "週末早晨",
                    "新座位",
                    "5 公里",
                    "新電視",
                    "下午茶時間",
                    "五年前的照片",
                    "慢慢來",
                    "明太子義大利麵",
                ],
                start=1,
            )
        }

        for offset, (email, content, image_index) in enumerate(SEED_POSTS):
            author = db.scalar(select(User).where(User.email == email))
            if author is None:
                continue
            already = db.scalar(
                select(Post).where(Post.author_id == author.id, Post.content == content)
            )
            if already:
                continue
            post = Post(
                author_id=author.id,
                content=content,
                image_url=post_images.get(image_index),
                likes_count=12 + (offset * 37) % 260,
                comments_count=(offset * 11) % 44,
                created_at=now - timedelta(hours=offset * 3 + 1),
            )
            db.add(post)
        db.commit()

        users = db.query(User).count()
        posts = db.query(Post).count()
        print(f"[seed] users={users} posts={posts} assets={SEED_DIR}")


if __name__ == "__main__":
    import sys

    seed(reset="--reset" in sys.argv)
