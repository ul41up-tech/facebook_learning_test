import { cx } from '../lib/format'

interface AvatarProps {
  name: string
  url?: string | null
  size?: number
  online?: boolean
  className?: string
}

function initials(name: string): string {
  const trimmed = (name || '?').trim()
  return trimmed.slice(0, 1).toUpperCase()
}

export function Avatar({ name, url, size = 40, online = false, className }: AvatarProps) {
  const style = { width: size, height: size, fontSize: Math.max(11, Math.round(size * 0.42)) }
  return (
    <span className={cx('avatar-wrap', className)} style={{ width: size, height: size }}>
      {url ? (
        <img className="avatar" src={url} alt={name} style={style} />
      ) : (
        <span className="avatar avatar-fallback" style={style} aria-hidden="true">
          {initials(name)}
        </span>
      )}
      {online && <span className="presence-dot" style={{ width: size * 0.3, height: size * 0.3 }} />}
    </span>
  )
}
