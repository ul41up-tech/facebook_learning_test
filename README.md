# Facebook Clone — Resend Email-Verification Test Harness

一個「外殼是 Facebook、內核是 Resend 驗證流程測試台」的專案。

- **前端**：Vite + React 18 + TypeScript（原生 CSS，仿 Facebook 桌面版三欄介面）
- **後端**：Python 3.14 + Flask + SQLAlchemy + psycopg3
- **資料庫**：PostgreSQL 18（本機）
- **部署**：Cloudflare Tunnel quick tunnel → `https://<隨機>.trycloudflare.com`
- **驗證信**：Resend（依 `resend` skill 的規範：環境變數金鑰、idempotency key、webhook 簽章驗證）

> 這個專案存在的唯一理由：**讓 Resend 的 email 驗證登入流程可以被真實測試**。
> 「像 Facebook」是手段，不是目的——但外觀必須夠真，否則測不出真實的問題。

---

## 快速開始

### 0. 填兩個秘密檔案（不用貼到聊天視窗）

| 檔案 | 填什麼 |
|---|---|
| `backend/secrets/resend_api_key.txt` | Resend API key（`re_...`） |
| `backend/secrets/pg_password.txt` | 本機 PostgreSQL 的 postgres 密碼 |
| `backend/secrets/resend_domain.txt` | 你要驗證的寄件網域（B 案） |
| `backend/secrets/cloudflare_api_token.txt` | 選填，有填就能自動寫 DNS |

解析規則：忽略 `#` 開頭的行與空行；`KEY=value` 取 value；`KEY=` 空值視為「尚未填寫」繼續往下找。
**這些檔案的內容不會被任何腳本印到畫面上。**

### 1. 一鍵 bootstrap

```powershell
.\scripts\setup-all.ps1
```

會依序：建立 PostgreSQL 資料庫 → seed → 驗證 Resend 寄件網域 → 建置前端 → 起 Cloudflare 隧道 + Flask。

### 2. 或逐步執行

```powershell
.\scripts\setup-db.ps1          # 建庫 + seed
.\scripts\start.ps1             # 隧道 + Flask（自動把隧道網域寫進 .env）
```

啟動後會印出：

```
[start] tunnel URL: https://xxxx-yyyy-zzzz.trycloudflare.com
```

**網站本體就走 Cloudflare 臨時網域**（免帳號、免 SLA、每次重啟網址會變）。
只有「寄件人」用你自己驗證過的網域 —— 這是 Resend 的規則，跟網站怎麼部署無關。

---

## B 案：用自己的網域做 Resend 寄件人

為什麼需要：`onboarding@resend.dev` 是沙箱，只能寄到 Resend 帳號自己的信箱；
要寄到**任意外部 Gmail** 必須驗證自有網域。

```powershell
cd backend
.\.venv\Scripts\python.exe setup_resend_domain.py
```

腳本會：建立 Resend 網域 → 把 Resend 要求的 MX / TXT / CNAME 紀錄**自動寫進 Cloudflare**
（需要 `secrets/cloudflare_api_token.txt`；沒填就會把紀錄整理出來讓你手動加）→ 觸發驗證 → 回報狀態。

驗證成功後把寄件人改成自己的網域：

```powershell
# backend\.env
RESEND_FROM=Facebook <no-reply@yourdomain.com>
```

> `trycloudflare.com` **不能**當寄件網域（那是給網站用的，沒有 DNS 控管權）。

---

## 主要流程（測試對象）

```
1. /login → 「以電子郵件建立帳號」→ 填名字 + Gmail 信箱
2. POST /api/auth/register → Resend 寄出驗證信
3. 點信中的連結 → /verify?token=... → 設定密碼 → 完成註冊
4. 立刻進入 / ，看到動態牆
```

### 時間旅行（測 TTL 過期用）

不用真的等 15 分鐘：

```powershell
curl -X POST http://127.0.0.1:5000/api/dev/advance-time -H "Content-Type: application/json" -d '{"seconds":900}'
curl -X POST http://127.0.0.1:5000/api/dev/reset-time -H "Content-Type: application/json" -d '{}'
```

時鐘偏移存在資料庫 `app_state` 表，重啟後仍在。

---

## API

| Method | Path | 說明 |
|---|---|---|
| POST | `/api/auth/register` | `{email, name}` → 寄出驗證信 |
| POST | `/api/auth/resend` | 同上（重新寄送） |
| POST | `/api/auth/verify` | `{token, name, password}` → 完成註冊並登入 |
| POST | `/api/auth/login` | `{email, password}` |
| POST | `/api/auth/logout` | |
| GET | `/api/me` | 目前登入者 |
| GET | `/api/feed?limit=50` | 動態牆（需登入） |
| POST | `/api/posts` | `{content, image_url?}` |
| GET | `/api/health` | 健康檢查 |
| POST | `/api/webhooks/resend` | Resend 事件 webhook（需 `RESEND_WEBHOOK_SECRET`） |
| GET | `/api/dev/now` | 目前（偏移後的）時間 |
| POST | `/api/dev/advance-time` | `{seconds}` 快轉時鐘 |
| POST | `/api/dev/reset-time` | 重設時鐘 |
| GET | `/api/dev/email-events` | 最近 100 筆寄信事件 |

錯誤碼：`invalid_email` / `name_required` / `email_taken` / `invalid_token` / `expired_token` / `already_used` / `weak_password` / `invalid_credentials` / `not_verified` / `unauthenticated` / `email_send_failed`

---

## Resend 注意事項（重要）

1. **`onboarding@resend.dev` 是沙箱**，只能寄到 Resend 帳號「自己註冊的信箱」。
   - 如果你的 Resend 帳號是用 Gmail 註冊的 → 直接用沙箱就能完整測試一輪。
   - 要寄到**任意外部 Gmail** → 必須先驗證自有網域（DNS 放在 Cloudflare），且 `from` 的網域必須與已驗證網域**完全相符**。
2. **不要用假信箱測試**（`test@gmail.com` 之類）：會退信並摧毀寄件者信譽。
   - Resend 官方測試信箱：`delivered@resend.dev`（成功）、`bounced@resend.dev`（退信）、`complained@resend.dev`（檢舉）。
3. **TTL 要長於真實投遞延遲**（Gmail 通常 1–30 秒，有時更久），否則會出現「信還沒到、連結就過期」。
4. **重寄驗證信時 idempotency key 必須換新的**（本專案用 `verification/{token.id}`），
   否则 Resend 會回 409（同 key 不同 payload）。
5. **Webhook 一定要驗簽章**（`svix-id` / `svix-timestamp` / `svix-signature`），本專案用 `resend.Webhooks.verify()`。

---

## 環境需求（已在本機確認）

| 工具 | 版本 | 狀態 |
|---|---|---|
| cloudflared | 2026.10.3 | 已安裝 |
| PostgreSQL | 18.6 | 已安裝，服務執行中 |
| Python | 3.14.7 | 已安裝（uv 建 venv） |
| Node | 24.21.0 | 已安裝 |
| uv | 0.13.4 | 已安裝 |
| Docker | — | **未安裝**（故直接用本機 Postgres） |

---

## 目錄結構

```
backend/          Flask API
  app.py            路由
  models.py         SQLAlchemy 模型
  clock.py          可快轉的時鐘
  mailer.py         Resend 寄信
  seed.py           seed 帳號與貼文（本地 SVG 素材）
  smoke_test.py     端到端自我測試（用 SQLite，不需任何憑證）
frontend/         Vite + React + TS
scripts/          start.ps1 / setup-db.ps1
_bmad-output/     BMAD 腦力激盪產出（memlog、intent doc）
```
