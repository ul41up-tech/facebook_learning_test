import { Avatar } from './Avatar'
import {
  FLogo,
  IconBell,
  IconHome,
  IconMarket,
  IconMessenger,
  IconSearch,
  IconVideo,
} from './icons'
import { useAuth } from '../context/AuthContext'

export function TopBar() {
  const { user } = useAuth()
  return (
    <header className="topbar">
      <div className="topbar-left">
        <a className="topbar-logo" href="/" aria-label="Facebook 首頁">
          <FLogo />
        </a>
        <div className="topbar-search">
          <IconSearch />
          <input type="search" placeholder="搜尋 Facebook" aria-label="搜尋 Facebook" />
        </div>
      </div>
      <nav className="topbar-right" aria-label="功能選單">
        <button type="button" className="icon-btn" aria-label="首頁">
          <IconHome />
        </button>
        <button type="button" className="icon-btn" aria-label="觀看影片">
          <IconVideo />
        </button>
        <button type="button" className="icon-btn" aria-label="Marketplace">
          <IconMarket />
        </button>
        <button type="button" className="icon-btn" aria-label="群組">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path d="M12 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 10c4 0 8 2 8 5v1H4v-1c0-3 4-5 8-5z" />
          </svg>
        </button>
        <button type="button" className="icon-btn" aria-label="通知">
          <IconBell />
          <span className="notif-dot" />
        </button>
        <button type="button" className="icon-btn" aria-label="Messenger">
          <IconMessenger />
        </button>
        {user && (
          <a className="topbar-avatar" href="/" aria-label={`${user.name} 的個人檔案`}>
            <Avatar name={user.name} url={user.avatar_url} size={40} />
          </a>
        )}
      </nav>
    </header>
  )
}
