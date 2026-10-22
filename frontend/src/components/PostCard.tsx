import { useState } from 'react'
import type { Post } from '../types'
import { relativeTime } from '../lib/format'
import { Avatar } from './Avatar'
import { IconComment, IconKebab, IconLike, IconShare } from './icons'

const REACTIONS = ['👍', '❤️', '😆']

interface PostCardProps {
  post: Post
}

export function PostCard({ post }: PostCardProps) {
  const [liked, setLiked] = useState(false)
  const likeCount = post.likes_count + (liked ? 1 : 0)

  return (
    <article className="card post-card">
      <header className="post-header">
        <Avatar name={post.author.name} url={post.author.avatar_url} size={40} />
        <div className="post-header-text">
          <a className="post-author" href="#">
            {post.author.name}
          </a>
          <p className="post-meta">
            {relativeTime(post.created_at)} · 公開
          </p>
        </div>
        <button type="button" className="post-kebab" aria-label="貼文選項">
          <IconKebab />
        </button>
      </header>

      {post.content && <p className="post-content">{post.content}</p>}

      {post.image_url && (
        <img className="post-image" src={post.image_url} alt="" loading="lazy" />
      )}

      <div className="post-stats">
        <span className="reaction-stack" aria-hidden="true">
          {REACTIONS.map((r) => (
            <span key={r} className="reaction-chip">
              {r}
            </span>
          ))}
        </span>
        <span className="post-stat-text">{likeCount} 人</span>
        <span className="post-stat-spacer" />
        <span className="post-stat-text">{post.comments_count} 則留言</span>
        <span className="post-stat-text">{post.likes_count} 次讚</span>
      </div>

      <div className="post-divider" />

      <div className="post-actions">
        <button
          type="button"
          className={`post-action ${liked ? 'post-action-liked' : ''}`}
          onClick={() => setLiked((v) => !v)}
          aria-pressed={liked}
        >
          <IconLike />
          <span>讚好</span>
        </button>
        <button type="button" className="post-action">
          <IconComment />
          <span>留言</span>
        </button>
        <button type="button" className="post-action">
          <IconShare />
          <span>分享</span>
        </button>
      </div>
    </article>
  )
}
