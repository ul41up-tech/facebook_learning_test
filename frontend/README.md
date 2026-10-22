# Facebook-lookalike Frontend (test harness)

A Vite + React 18 + TypeScript SPA that looks and behaves like Facebook, used as a
manual test harness for the Flask backend's **email-verification login flow**.

Only three runtime dependencies: `react`, `react-dom`, `react-router-dom`. All styling is
plain CSS in `src/styles.css` (no UI framework, no Tailwind).

## Run

```bash
npm install
npm run dev     # http://localhost:5173, proxies /api -> http://127.0.0.1:5000
npm run build   # type-checks (tsc -b) and emits to ./dist
npm run preview # serve the production build locally
```

Copy `.env.example` to `.env` to change the dev proxy target (`VITE_API_TARGET`).
All frontend requests use relative `/api/...` paths, so the production build works
behind the same-origin Flask server with no configuration.

## API contract

Every request is sent with `credentials: 'include'` (HttpOnly session cookie),
`Accept: application/json`, and `Content-Type: application/json` when it has a body.
Non-2xx responses are parsed as `{ ok: false, error: "<code>" }`.

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | `{ email, name }` | `{ ok: true, message }` — sends verification email. `409 email_taken` |
| POST | `/api/auth/verify` | `{ token, name, password }` | `{ ok: true, user }`. `400 invalid_token` / `expired_token` / `already_used` |
| POST | `/api/auth/login` | `{ email, password }` | `{ ok: true, user }`. `401 invalid_credentials` |
| POST | `/api/auth/logout` | – | `{ ok: true }` |
| GET | `/api/me` | – | `{ user }` or `401 unauthenticated` |
| GET | `/api/feed?limit=50` | – | `{ posts: [...] }` |
| POST | `/api/posts` | `{ content, image_url? }` | `201 { post }` |
| GET | `/api/health` | – | `{ ok: true, time }` |
| GET | `/api/dev/now` | – | `{ now }` (dev only, may 404) |
| POST | `/api/dev/advance-time` | `{ seconds }` | `{ ok: true, now }` (dev only, may 404) |

`user` = `{ id, name, email, avatar_url }`.
`post` = `{ id, author: { id, name, avatar_url }, content, image_url, created_at, likes_count, comments_count }`.

## Routes

- `/` — feed (protected; redirects to `/login` when `/api/me` returns 401)
- `/login` — login + registration card, including the "check your Gmail" confirmation screen
- `/verify?token=…` — complete registration (name + password + confirm)
- `*` — not found

## Notes for testers

- Dev helpers (`/api/dev/now`, `/api/dev/advance-time`) let you move the server clock
  forward to exercise the `expired_token` path; the frontend tolerates their absence.
- The composer modal posts to `/api/posts`; the feed prepends the new post and shows an
  empty state when there are no posts yet.
