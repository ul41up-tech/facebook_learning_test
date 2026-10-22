import { Link } from 'react-router-dom'
import { FLogo } from '../components/icons'

export function NotFoundPage() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <FLogo />
        </div>
        <h1 className="auth-title">找不到這個頁面</h1>
        <p className="auth-text">你瀏覽的頁面可能已移動或不存在。</p>
        <Link className="btn btn-primary btn-block" to="/">
          回到動態
        </Link>
      </div>
    </div>
  )
}
