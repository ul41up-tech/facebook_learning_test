import { Avatar } from './Avatar'
import { IconKebab } from './icons'

const CONTACTS = [
  { name: '王小明', color: '#1877f2' },
  { name: '李大華', color: '#f7b500' },
  { name: '陳美玲', color: '#31a24c' },
  { name: '林志豪', color: '#e5484d' },
  { name: '張曉雯', color: '#8b5cf6' },
  { name: '黃建國', color: '#0ba5ec' },
  { name: '吳怡君', color: '#f7b500' },
  { name: '劉子誠', color: '#31a24c' },
]

const GROUPS = [
  { name: '前端工程師日常', color: '#1877f2', count: '12 個新貼文' },
  { name: '台灣旅遊同好會', color: '#f7b500', count: '5 個新貼文' },
  { name: '咖啡與書', color: '#8b5cf6', count: '3 個新貼文' },
]

export function SidebarRight() {
  return (
    <aside className="sidebar-right" aria-label="右側欄">
      <div className="card right-card sponsored">
        <h2 className="right-heading">贊助商</h2>
        <div className="sponsored-item">
          <div className="sponsored-thumb" aria-hidden="true" />
          <div className="sponsored-meta">
            <p className="sponsored-title">極致行動網路吃到飽</p>
            <p className="sponsored-sub">了解方案詳情</p>
          </div>
        </div>
      </div>

      <div className="card right-card">
        <h2 className="right-heading">聯絡人</h2>
        <ul className="contact-list">
          {CONTACTS.map((c) => (
            <li key={c.name}>
              <a className="contact-row" href="#">
                <Avatar name={c.name} url={null} size={40} online />
                <span className="contact-name">{c.name}</span>
              </a>
            </li>
          ))}
        </ul>
        <button type="button" className="more-link">
          <IconKebab /> 更多
        </button>
      </div>

      <div className="card right-card">
        <h2 className="right-heading">社團</h2>
        <ul className="group-list">
          {GROUPS.map((g) => (
            <li key={g.name}>
              <a className="group-row" href="#">
                <span className="group-dot" style={{ background: g.color }} aria-hidden="true">
                  {g.name.slice(0, 1)}
                </span>
                <span className="group-meta">
                  <span className="group-name">{g.name}</span>
                  <span className="group-count">{g.count}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>

      <footer className="right-footer">
        <span>隱私權</span>
        <span>條款</span>
        <span>廣告</span>
        <span>說明中心</span>
        <span>© 2026 Facebook</span>
      </footer>
    </aside>
  )
}
