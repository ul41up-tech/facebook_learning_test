export interface User {
  id: number | string
  name: string
  email: string
  avatar_url: string | null
}

export interface Post {
  id: number | string
  author: {
    id: number | string
    name: string
    avatar_url: string | null
  }
  content: string
  image_url: string | null
  created_at: string
  likes_count: number
  comments_count: number
}

export interface ApiError {
  ok: false
  error: string
  message?: string
}

export interface ApiOk<T> {
  ok: true
  [key: string]: unknown
  user?: T
  post?: T
  posts?: T[]
  message?: string
  now?: string
}
