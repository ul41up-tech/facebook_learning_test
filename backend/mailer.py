"""Resend integration.

Follows the conventions documented by the `resend` skill:
  * API key always comes from the environment, never hard-coded.
  * Every send carries an idempotency key (`<event-type>/<entity-id>`) so a
    retry after a timeout cannot deliver a duplicate verification mail.
  * Failures are surfaced as exceptions instead of being swallowed.
"""

from __future__ import annotations

import html
import logging

import resend

from config import RESEND_API_KEY, RESEND_FROM

logger = logging.getLogger(__name__)

EMAIL_SUBJECT = "Facebook 帳號驗證 - 確認你的電子郵件地址"


class MailerError(RuntimeError):
    """Raised when Resend refuses or fails to deliver a message."""

    def __init__(self, message: str, code: str = "email_send_failed"):
        super().__init__(message)
        self.code = code


# Friendly, actionable codes for the errors Resend actually returns.
ERROR_CODES = {
    "suspended_api_key": "email_key_suspended",
    "suspended": "email_key_suspended",
    "restricted_api_key": "email_key_restricted",
    "invalid_api_key": "email_key_invalid",
    "api key is invalid": "email_key_invalid",
    "not_found": "email_key_invalid",
    "validation_error": "email_rejected",
    "rate_limit_exceeded": "email_rate_limited",
}


def classify(exc: Exception) -> str:
    """Map a Resend exception onto a stable error code."""
    text = str(exc).lower()
    for needle, code in ERROR_CODES.items():
        if needle in text:
            return code
    if "api key" in text and ("invalid" in text or "not found" in text):
        return "email_key_invalid"
    return "email_send_failed"


def configure_resend() -> None:
    if RESEND_API_KEY:
        resend.api_key = RESEND_API_KEY


def resend_configured() -> bool:
    return bool(RESEND_API_KEY)


def _verification_html(name: str, link: str, code: str, ttl_minutes: int) -> str:
    safe_name = html.escape(name or "朋友")
    safe_link = html.escape(link, quote=True)
    safe_code = html.escape(code)
    return f"""<!doctype html>
<html lang="zh-Hant">
  <body style="margin:0;padding:0;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'PingFang TC','Microsoft JhengHei',sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0f2f5;padding:32px 16px;">
      <tr><td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.15);">
          <tr><td align="center" style="background:#1877f2;padding:20px;">
            <span style="display:inline-block;width:44px;height:44px;line-height:44px;border-radius:50%;background:#ffffff;color:#1877f2;font-size:32px;font-weight:700;font-family:Arial,sans-serif;">f</span>
            <div style="color:#ffffff;font-size:20px;font-weight:600;margin-top:8px;">Facebook</div>
          </td></tr>
          <tr><td style="padding:32px 36px;color:#1c1e21;font-size:15px;line-height:1.5;">
            <p style="margin:0 0 16px;">你好，{safe_name}：</p>
            <p style="margin:0 0 16px;">有人要求使用這個電子郵件地址註冊 Facebook 帳號。請按下方的按鈕完成驗證。</p>
            <p style="margin:0 0 24px;">
              <a href="{safe_link}" style="display:inline-block;background:#1877f2;color:#ffffff;text-decoration:none;font-weight:600;font-size:17px;padding:14px 28px;border-radius:8px;">繼續前往 Facebook</a>
            </p>
            <p style="margin:0 0 8px;color:#65676b;font-size:13px;">如果按鈕無法點擊，請複製以下網址到瀏覽器：</p>
            <p style="margin:0 0 24px;word-break:break-all;font-size:12px;color:#1877f2;">{safe_link}</p>
            <p style="margin:0 0 8px;color:#65676b;font-size:13px;">驗證碼：<strong style="color:#1c1e21;letter-spacing:2px;">{safe_code}</strong></p>
            <p style="margin:0 0 24px;color:#65676b;font-size:13px;">此驗證連結將於 <strong>{ttl_minutes} 分鐘</strong>後失效，過期後請重新申請。</p>
            <p style="margin:0;color:#8a8d91;font-size:12px;">如果這不是你的操作，請忽略這封信，你的帳號不會被建立。</p>
          </td></tr>
          <tr><td style="background:#f0f2f5;padding:16px 36px;color:#8a8d91;font-size:11px;line-height:1.5;">
            這是一封系統寄出的驗證信。<br />
            測試環境寄件人：{html.escape(RESEND_FROM)}
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


def send_verification_email(
    *,
    to_email: str,
    name: str,
    link: str,
    code: str,
    ttl_minutes: int,
    idempotency_key: str,
) -> str:
    """Send the verification mail. Returns the Resend email id."""
    configure_resend()
    if not RESEND_API_KEY:
        raise MailerError("RESEND_API_KEY is not configured")

    params = {
        "from": RESEND_FROM,
        "to": [to_email],
        "subject": EMAIL_SUBJECT,
        "html": _verification_html(name, link, code, ttl_minutes),
    }
    options = {"idempotency_key": idempotency_key}

    try:
        response = resend.Emails.send(params, options=options)
    except Exception as exc:  # noqa: BLE001 - surface any Resend failure
        logger.exception("Resend send failed for %s", to_email)
        raise MailerError(str(exc), classify(exc)) from exc

    email_id = getattr(response, "id", None)
    if email_id is None and isinstance(response, dict):
        email_id = response.get("id")
    if not email_id:
        raise MailerError(f"Resend returned no email id: {response!r}")
    return str(email_id)
