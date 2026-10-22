import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch, errorMessage, isHttpError } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import type { User } from '../types'
import { FLogo } from '../components/icons'

type Mode = 'login' | 'register' | 'sent'

export function LoginPage() {
  const { setUser } = useAuth()
  const [mode, setMode] = useState<Mode>('login')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')

  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sentTo, setSentTo] = useState('')

  const switchMode = (next: Mode) => {
    setMode(next)
    setError('')
  }

  const doLogin = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await apiFetch<{ user: User }>('/auth/login', {
        method: 'POST',
        body: { email: email.trim(), password },
      })
      setUser(res.user)
    } catch (err) {
      setError(
        isHttpError(err) && err.code === 'invalid_credentials'
          ? '電子郵件或密碼錯誤，請再試一次'
          : errorMessage(err, '登入失敗，請稍後再試'),
      )
      setBusy(false)
    }
  }

  const sendVerification = async (e?: FormEvent) => {
    if (e) e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await apiFetch('/auth/register', {
        method: 'POST',
        body: { email: email.trim(), name: name.trim() },
      })
      setSentTo(email.trim())
      setMode('sent')
    } catch (err) {
      setError(
        isHttpError(err) && err.code === 'email_taken'
          ? '此電子郵件已被註冊，請改用登入'
          : errorMessage(err, '無法寄送驗證信，請稍後再試'),
      )
      setBusy(false)
    }
  }

  if (mode === 'sent') {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-brand">
            <FLogo />
          </div>
          <h1 className="auth-title">請查收你的驗證信</h1>
          <p className="auth-text">
            我們已將驗證連結寄到 <strong>{sentTo}</strong>。請打開電子郵件並點擊連結以完成註冊。
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button
            type="button"
            className="btn btn-primary btn-block"
            onClick={() => void sendVerification()}
            disabled={busy}
          >
            {busy ? '寄送中…' : '重新寄送'}
          </button>
          <div className="auth-divider">
            <span>或</span>
          </div>
          <button type="button" className="btn btn-secondary btn-block" onClick={() => switchMode('login')}>
            返回登入
          </button>
          <p className="auth-footnote">
            已經有帳號了嗎？<Link to="/login">登入</Link>
          </p>
        </div>
      </div>
    )
  }

  if (mode === 'register') {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-brand">
            <FLogo />
          </div>
          <h1 className="auth-title">建立帳號</h1>
          <p className="auth-text">只需名字和電子郵件，我們會寄送驗證信給你。</p>
          <form className="auth-form" onSubmit={sendVerification}>
            <div className="field">
              <label className="sr-only" htmlFor="reg-name">
                姓名
              </label>
              <input
                id="reg-name"
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
              <label className="sr-only" htmlFor="reg-email">
                電子郵件
              </label>
              <input
                id="reg-email"
                className="field-input"
                type="email"
                placeholder="電子郵件"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
              {busy ? '寄送中…' : '繼續'}
            </button>
          </form>
          <div className="auth-divider">
            <span>或</span>
          </div>
          <button type="button" className="btn btn-secondary btn-block" onClick={() => switchMode('login')}>
            返回登入
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <FLogo />
        </div>
        <h1 className="auth-title">登入 Facebook</h1>
        <p className="auth-text">使用電子郵件和密碼登入。</p>
        <form className="auth-form" onSubmit={doLogin}>
          <div className="field">
            <label className="sr-only" htmlFor="login-email">
              電子郵件
            </label>
            <input
              id="login-email"
              className="field-input"
              type="email"
              placeholder="電子郵件"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="field">
            <label className="sr-only" htmlFor="login-password">
              密碼
            </label>
            <input
              id="login-password"
              className="field-input"
              type="password"
              placeholder="密碼"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
            {busy ? '登入中…' : '登入'}
          </button>
        </form>
        <div className="auth-divider">
          <span>或</span>
        </div>
        <button
          type="button"
          className="btn btn-green btn-block"
          onClick={() => switchMode('register')}
        >
          以電子郵件建立帳號
        </button>
        <p className="auth-footnote">
          已經有驗證連結了嗎？<Link to="/verify">前往驗證</Link>
        </p>
      </div>
    </div>
  )
}
