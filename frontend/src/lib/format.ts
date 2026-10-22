export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const diff = Math.max(0, Date.now() - then)
  const min = Math.floor(diff / 60000)
  if (min < 1) return '剛剛'
  if (min < 60) return `${min} 分鐘`
  const hours = Math.floor(min / 60)
  if (hours < 24) return `${hours} 小時`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} 天`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks} 週`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months} 個月`
  return `${Math.floor(days / 365)} 年`
}

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}
