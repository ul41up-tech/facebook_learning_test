"""Generate realistic avatars / post images with the QianPro (千鉑) AI Studio API.

Replaces the local SVG placeholders with photo-real images so the fake Facebook
looks convincing - which matters, because the whole point of this harness is to
test the email journey against a believable product.

Requires `QIANPRO_STUDIO_TOKEN` in the environment (see the qianpro-studio skill).

    .venv\\Scripts\\python.exe qianpro_seed.py --avatars --posts
    .venv\\Scripts\\python.exe qianpro_seed.py --posts --limit 3

Flow (per the qianpro-studio skill):
    POST /api/image/gen   -> {"job": "..."}
    GET  /api/image/status/{job} (poll every ~2.5s) -> {"state": "done", "ids": [...]}
    GET  /api/image/view/{img_id} -> image bytes
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests

BASE = "https://studio.qianpro.shop"
OUT_DIR = Path(__file__).resolve().parent / "static" / "seed"

AVATAR_PROMPTS = [
    "photorealistic portrait photo of a friendly Taiwanese woman in her late twenties, natural smile, soft daylight, plain light grey studio background, headshot, sharp focus, 85mm",
    "photorealistic portrait photo of a Taiwanese man in his early thirties, short hair, light blue shirt, natural window light, plain office background, headshot, 85mm",
    "photorealistic portrait photo of a cheerful Taiwanese woman with shoulder-length hair, white blouse, blurred cafe background, headshot, natural light",
    "photorealistic portrait photo of a Taiwanese man in his late twenties wearing glasses, dark t-shirt, plain beige background, headshot, studio light",
    "photorealistic portrait photo of an elegant Taiwanese woman in her thirties, subtle makeup, knit sweater, soft grey background, headshot",
    "photorealistic portrait photo of a Taiwanese man with a beard, olive jacket, outdoor blurred greenery background, headshot",
    "photorealistic portrait photo of a cheerful Taiwanese woman with long straight hair, denim jacket, plain background, headshot",
    "photorealistic portrait photo of a Taiwanese man with styled hair, black hoodie, moody grey background, headshot",
    "photorealistic portrait photo of a Taiwanese woman with bangs, light cardigan, soft pink background, headshot",
    "photorealistic portrait photo of a Taiwanese man in a grey button-up shirt, plain white background, headshot",
]

POST_PROMPTS = [
    "photorealistic travel photo, Tamsui riverside street in Taiwan at golden hour, old street market stalls, warm sunlight, candid",
    "photorealistic food photo, a bowl of Japanese-style spicy tuna spaghetti on a wooden table, restaurant interior, appetising",
    "photorealistic lifestyle photo, a cat sleeping next to a coffee cup and an open book on a sunny windowsill, cosy apartment",
    "photorealistic office photo, a tidy modern desk with a monitor, plant and coffee mug, daylight from a window",
    "photorealistic sports photo, a runner jogging on a riverside path at dawn, motion, morning mist",
    "photorealistic living room photo, a brand new flat screen television on a white console in a bright apartment",
    "photorealistic office snack photo, pineapple cakes on a plate next to a cup of tea on a desk, soft daylight",
    "photorealistic photo, a hand holding an old printed photo album open on a wooden table, nostalgic, warm tones",
    "photorealistic cinema-adjacent photo, a moody desk with a notebook and a cup of tea, film still lighting",
    "photorealistic food photo, a bowl of creamy tomato sauce pasta with basil, close up, shallow depth of field",
]


class QianProError(RuntimeError):
    pass


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def generate_image(token: str, prompt: str, width: int, height: int, timeout: int = 300) -> bytes:
    resp = requests.post(
        f"{BASE}/api/image/gen",
        headers=_headers(token),
        files={
            "prompt": (None, prompt),
            "model": (None, "qwen21"),
            "steps": (None, "25"),
            "cfg": (None, "1"),
            "width": (None, str(width)),
            "height": (None, str(height)),
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise QianProError(f"gen failed: {resp.status_code} {resp.text[:300]}")
    data = resp.json()
    job = data.get("job")
    if not job:
        raise QianProError(f"no job id in response: {data}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2.5)
        status = requests.get(f"{BASE}/api/image/status/{job}", headers=_headers(token), timeout=60)
        if status.status_code != 200:
            continue
        sdata = status.json()
        if sdata.get("state") == "done":
            ids = sdata.get("ids") or []
            if not ids:
                raise QianProError(f"job done but no ids: {sdata}")
            img = requests.get(
                f"{BASE}/api/image/view/{ids[0]}", headers=_headers(token), timeout=120
            )
            if img.status_code != 200:
                raise QianProError(f"view failed: {img.status_code} {img.text[:200]}")
            return img.content
        if sdata.get("state") in {"error", "failed", "canceled"}:
            raise QianProError(f"job failed: {sdata}")

    raise QianProError("timed out waiting for image generation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--avatars", action="store_true", help="generate profile pictures")
    parser.add_argument("--posts", action="store_true", help="generate post photos")
    parser.add_argument("--limit", type=int, default=0, help="max images per kind (0 = all)")
    args = parser.parse_args()

    if not args.avatars and not args.posts:
        args.avatars = args.posts = True

    token = os.getenv("QIANPRO_STUDIO_TOKEN", "").strip()
    if not token:
        print("QIANPRO_STUDIO_TOKEN is not set", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, int, int]] = []
    if args.avatars:
        jobs += [(f"avatar-{i + 1}.jpg", p, 512, 512) for i, p in enumerate(AVATAR_PROMPTS)]
    if args.posts:
        jobs += [(f"post-{i + 1}.jpg", p, 1024, 640) for i, p in enumerate(POST_PROMPTS)]

    if args.limit:
        keep = args.limit * (1 if args.avatars else 0) + args.limit * (1 if args.posts else 0)
        jobs = jobs[:keep]

    failures = 0
    for name, prompt, w, h in jobs:
        target = OUT_DIR / name
        if target.exists() and target.stat().st_size > 1024:
            print(f"[skip] {name} already exists")
            continue
        print(f"[gen ] {name} ...")
        try:
            data = generate_image(token, prompt, w, h)
            target.write_bytes(data)
            print(f"[ok  ] {name} ({len(data) // 1024} KB)")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[fail] {name}: {exc}", file=sys.stderr)
        time.sleep(1.0)

    print(f"\ndone. failures={failures} output={OUT_DIR}")
    print("Next: re-run seed.py so the new images are attached to seed users and posts.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
