import type { ApiError, ApiOk } from '../types'

export class HttpError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message?: string) {
    super(message || code)
    this.name = 'HttpError'
    this.status = status
    this.code = code
  }
}

export async function apiFetch<T>(
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const { method = 'GET', body } = options
  const init: RequestInit = {
    method,
    credentials: 'include',
    headers: { Accept: 'application/json' },
  }
  if (body !== undefined) {
    init.headers = { ...init.headers, 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
  }

  let res: Response
  try {
    res = await fetch(`/api${path}`, init)
  } catch {
    throw new HttpError(0, 'network_error', '無法連線到伺服器')
  }

  let data: unknown = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }

  if (!res.ok) {
    const err = data as ApiError | null
    throw new HttpError(res.status, err?.error || 'http_error', err?.message)
  }
  return (data ?? {}) as T
}

export function isHttpError(e: unknown): e is HttpError {
  return e instanceof HttpError
}

export function errorMessage(e: unknown, fallback = '發生錯誤，請稍後再試'): string {
  if (isHttpError(e)) return e.message || fallback
  if (e instanceof Error) return e.message
  return fallback
}

export type ApiResult<T> = ApiOk<T>
