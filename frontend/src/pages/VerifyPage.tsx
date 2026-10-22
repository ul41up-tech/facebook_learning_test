import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiFetch, errorMessage, isHttpError } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import type { User } from '../types'

/**
 * Best-effort local check: if the token looks like a JWT we can read its `exp`
 * claim without verifying the signature and warn early. The backend remains
 * the source of truth.
 */
function tokenExpiry(token: string): number | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))) as {
      exp?: number
    }
    if (typeof payload.exp === 'number') return payload.exp * 1000
  } catch {
    return null
  }
  return null
}

export function VerifyPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const navigate = useNavigate()
  const { setUser } = useAuth()

  const [checking, setChecking] = useState(true)
  const [expired, setExpired] = useState(false)
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      if (!token) {
        if (!cancelled) {
          setExpired(true)
          setChecking(false)
        }
        return
      }
      try {
        // Optional dev helper; gracefully ignore when disabled.
        await apiFetch('/dev/now')
      } catch {
        /* ignore */
      }
      const exp = tokenExpiry(token)
      if (!cancelled) {
        if (exp !== null && Date.now() > exp) setExpired(true)
        setChecking(false)
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [token])

  const passwordError = useMemo(() => {
    if (password.length === 0) return ''
    if (password.length < 6) return '密碼至少需要 6 個字元'
    return ''
  }, [password])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 6) {
      setError('密碼至少需要 6 個字元')
      return
    }
    if (password !== confirm) {
      setError('兩次輸入的密碼不一致')
      return
    }
    setBusy(true)
    try {
      const res = await apiFetch<{ user: User }>('/auth/verify', {
        method: 'POST',
        body: { token, name: name.trim(), password },
      })
      setUser(res.user)
      navigate('/', { replace: true })
    } catch (err) {
      if (isHttpError(err)) {
        if (err.code === 'expired_token' || err.code === 'invalid_token') {
          setExpired(true)
          setBusy(false)
          return
        }
        if (err.code === 'already_used') {
          setError('此驗證連結已被使用')
          setBusy(false)
          return
        }
      }
      setError(errorMessage(err, '驗證失敗，請稍後再試'))
      setBusy(false)
    }
  }

  if (checking) {
    return (
      <div className="auth-page">
        <div className="auth-card auth-card-loading">
          <span className="spinner" aria-hidden="true" />
          <p className="auth-text">正在檢查驗證連結…</p>
        </div>
      </div>
    )
  }

  if (expired) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1 className="auth-title">此驗證連結已過期</h1>
          <p className="auth-text">驗證連結無效或已過期，請回到登入頁重新寄送驗證信。</p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <Link className="btn btn-primary btn-block" to="/login">
            返回登入頁
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">完成註冊</h1>
        <p className="auth-text">設定你的姓名與密碼即可完成註冊。</p>
        <form className="auth-form" onSubmit={submit}>
          <div className="field">
            <label className="sr-only" htmlFor="verify-name">
              姓名
            </label>
            <input
              id="verify-name"
              className="field-input"
              type="text"
              placeholder="姓名"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoComplete="name"
            />
          </div>
          <div className="field">
            <label className="sr-only" htmlFor="verify-password">
              密碼
            </label>
            <input
              id="verify-password"
              className="field-input"
              type="password"
              placeholder="密碼"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="field">
            <label className="sr-only" htmlFor="verify-confirm">
              確認密碼
            </label>
            <input
              id="verify-confirm"
              className="field-input"
              type="password"
              placeholder="確認密碼"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          {passwordError && <p className="form-hint">{passwordError}</p>}
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
            {busy ? '驗證中…' : '完成註冊'}
          </button>
        </form>
      </div>
    </div>
  )
}
