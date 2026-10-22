type IconProps = { className?: string }

export function FLogo({ className }: IconProps) {
  return (
    <span className={`flogo ${className ?? ''}`} aria-hidden="true">
      f
    </span>
  )
}

export function IconHome({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 3 2 12h3v8h5v-6h4v6h5v-8h3z" />
    </svg>
  )
}

export function IconVideo({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M4 5h11a2 2 0 0 1 2 2v2.2l4-2.9v11.4l-4-2.9V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
    </svg>
  )
}

export function IconMarket({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M4 4h16l-1.2 4H5.2zM5.5 10h13l-1 10h-11z" />
    </svg>
  )
}

export function IconGroups({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 10c4 0 8 2 8 5v1H4v-1c0-3 4-5 8-5z" />
    </svg>
  )
}

export function IconBell({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 22a2.5 2.5 0 0 0 2.5-2.5h-5A2.5 2.5 0 0 0 12 22zm7-6-2-2v-4a5 5 0 0 0-4.2-4.9V4a.8.8 0 0 0-1.6 0v1.1A5 5 0 0 0 7 10v4l-2 2v1h14z" />
    </svg>
  )
}

export function IconMessenger({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 3C6.5 3 2 6.8 2 11.5c0 2.6 1.4 5 3.6 6.5-.2 1.3-.8 2.6-1.6 3.6 1.7-.2 3.3-.9 4.6-1.9 1 .2 2.2.4 3.4.4 5.5 0 10-3.8 10-8.5S17.5 3 12 3z" />
    </svg>
  )
}

export function IconKebab({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <circle cx="5" cy="12" r="1.7" />
      <circle cx="12" cy="12" r="1.7" />
      <circle cx="19" cy="12" r="1.7" />
    </svg>
  )
}

export function IconLike({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M2 10h4v11H2zm20 1a3 3 0 0 0-3-3h-5.5l1-4.6v-.3l-1.2-1.2-5.6 5.5V21h10.6a3 3 0 0 0 2.9-2.3l1.8-6a3 3 0 0 0 0-1.7z" />
    </svg>
  )
}

export function IconComment({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 3C6.5 3 2 6.9 2 11.8c0 2.4 1.2 4.5 3.1 6V22l3.6-2.2c1 .2 2.1.4 3.3.4 5.5 0 10-3.9 10-8.8S17.5 3 12 3z" />
    </svg>
  )
}

export function IconShare({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="m13 3 7 7-7 7-1.4-1.4 4.1-4.1H4v-3h11.7L11.6 4.4z" />
    </svg>
  )
}

export function IconCamera({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M3 7h4l1.5-2h7L17 7h4v13H3zm9 2.5A4.5 4.5 0 1 0 16.5 14 4.5 4.5 0 0 0 12 9.5z" />
    </svg>
  )
}

export function IconSmile({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-4 7.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm7 0a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm-7 4a6 6 0 0 0 6 6 6 6 0 0 0 6-6z" />
    </svg>
  )
}

export function IconEye({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 5C6.5 5 2.7 9 1 12c1.7 3 5.5 7 11 7s9.3-4 11-7c-1.7-3-5.5-7-11-7zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" />
    </svg>
  )
}

export function IconSearch({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
      <path d="M10 3a7 7 0 1 1-4.4 12.4l-3 3-1.4-1.4 3-3A7 7 0 0 1 10 3zm0 2a5 5 0 1 0 0 10 5 5 0 0 0 0-10z" />
    </svg>
  )
}
