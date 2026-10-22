import { cx } from '../lib/format'
import {
  IconEye,
  IconGroups,
  IconHome,
  IconKebab,
  IconMarket,
  IconVideo,
} from './icons'

const NAV_ITEMS = [
  { label: '動態', icon: IconHome, active: true, count: 3 },
  { label: '觀看影片', icon: IconVideo },
  { label: 'Marketplace', icon: IconMarket },
  { label: '群組', icon: IconGroups, count: 2 },
  { label: '收藏', icon: IconEye },
  { label: '遊戲', icon: IconKebab },
  { label: '貼文', icon: IconKebab },
]

const SHORTCUTS = [
  { label: '台灣旅遊社團', color: '#1877f2' },
  { label: '前端工程師日常', color: '#f7b500' },
  { label: '咖啡愛好者', color: '#8b5cf6' },
  { label: '居家生活', color: '#31a24c' },
]

export function SidebarLeft() {
  return (
    <aside className="sidebar-left" aria-label="側邊選單">
      <div className="card sidebar-card">
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.label}>
                <a
                  className={cx('nav-row', item.active && 'nav-row-active')}
                  href="#"
                  aria-current={item.active ? 'page' : undefined}
                >
                  <span className="nav-icon">
                    <Icon />
                  </span>
                  <span className="nav-label">{item.label}</span>
                  {item.count ? <span className="nav-badge">{item.count}</span> : null}
                </a>
              </li>
            )
          })}
        </ul>
      </div>

      <div className="card sidebar-card">
        <h2 className="sidebar-heading">你的捷徑</h2>
        <ul className="shortcut-list">
          {SHORTCUTS.map((s) => (
            <li key={s.label}>
              <a className="shortcut-row" href="#">
                <span className="shortcut-dot" style={{ background: s.color }} aria-hidden="true">
                  {s.label.slice(0, 1)}
                </span>
                <span className="shortcut-label">{s.label}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}
