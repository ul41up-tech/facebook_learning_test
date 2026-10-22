"""Unit checks for the secret-file parser (no real secrets involved)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, r"C:\Users\user\Desktop\facebook\backend")

import config  # noqa: E402

CASES = {
    "comment only": "# hello\n\n",
    "key=value": "RESEND_API_KEY=re_abc123\n",
    "empty placeholder then value": "RESEND_API_KEY=\nre_later\n",
    "bare value": "re_bare_value\n",
    "quoted": 'RESEND_API_KEY="re_quoted"\n',
    "leading spaces": "   RESEND_API_KEY=re_spaced   \n",
    "bom": "\ufeffRESEND_API_KEY=re_bom\n",
    "not a key=value pair": "https://example.com/?a=b\n",
}

failures = 0
for name, content in CASES.items():
    path = pathlib.Path(__file__).with_name("_tmp_secret_case.txt")
    path.write_text(content, encoding="utf-8")
    got = config.read_secret_file(path)
    print(f"  {name:28} -> {got!r}")
    path.unlink(missing_ok=True)

expected = {
    "comment only": "",
    "key=value": "re_abc123",
    "empty placeholder then value": "re_later",
    "bare value": "re_bare_value",
    "quoted": "re_quoted",
    "leading spaces": "re_spaced",
    "bom": "re_bom",
    "not a key=value pair": "https://example.com/?a=b",
}

print()
for name, content in CASES.items():
    path = pathlib.Path(__file__).with_name("_tmp_secret_case.txt")
    path.write_text(content, encoding="utf-8")
    got = config.read_secret_file(path)
    path.unlink(missing_ok=True)
    want = expected[name]
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r} want {want!r}")
    if not ok:
        failures += 1

print("\nALL PASSED" if not failures else f"\n{failures} FAILURE(S)")
raise SystemExit(1 if failures else 0)
