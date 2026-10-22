import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import type { Post } from '../types'
import { PostCard } from '../components/PostCard'
import { ComposerModal } from '../components/ComposerModal'
import { Avatar } from '../components/Avatar'
import { IconCamera, IconSmile, IconVideo } from '../components/icons'

export function FeedPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [composerOpen, setComposerOpen] = useState(false)

  const loadFeed = useCallback(async () => {
    setLoading(true)
    setLoadError('')
    try {
      const res = await apiFetch<{ posts: Post[] }>('/feed?limit=50')
      setPosts(res.posts ?? [])
    } catch (err) {
      setLoadError(errorMessage(err, '無法載入動態，請稍後再試'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadFeed()
  }, [loadFeed])

  const handleCreated = (post: Post) => {
    setPosts((prev) => [post, ...prev])
  }

  return (
    <div className="feed">
      <section className="card composer-card" aria-label="建立貼文">
        <div className="composer-top">
          <Avatar name={user?.name ?? '我'} url={user?.avatar_url ?? null} size={40} />
          <button
            type="button"
            className="composer-pill"
            onClick={() => setComposerOpen(true)}
            aria-label="建立貼文"
          >
            你在想什麼？
          </button>
        </div>
        <div className="composer-divider" />
        <div className="composer-actions">
          <button type="button" className="composer-action" onClick={() => setComposerOpen(true)}>
            <span className="composer-action-icon composer-action-red">
              <IconVideo />
            </span>
            <span>直播影片</span>
          </button>
          <button type="button" className="composer-action" onClick={() => setComposerOpen(true)}>
            <span className="composer-action-icon composer-action-green">
              <IconCamera />
            </span>
            <span>照片/影片</span>
          </button>
          <button type="button" className="composer-action" onClick={() => setComposerOpen(true)}>
            <span className="composer-action-icon composer-action-yellow">
              <IconSmile />
            </span>
            <span>心情/活動</span>
          </button>
        </div>
      </section>

      {loading && (
        <div className="feed-skeletons" aria-live="polite" aria-busy="true">
          {[0, 1, 2].map((i) => (
            <div className="card skeleton-card" key={i}>
              <div className="skeleton-head">
                <span className="skeleton skeleton-circle" />
                <span className="skeleton skeleton-lines" />
              </div>
              <span className="skeleton skeleton-block" />
              <span className="skeleton skeleton-block short" />
            </div>
          ))}
          <span className="sr-only">載入中</span>
        </div>
      )}

      {!loading && loadError && (
        <div className="card feed-state">
          <p className="feed-state-text">{loadError}</p>
          <button type="button" className="btn btn-primary" onClick={() => void loadFeed()}>
            重新載入
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/login')}>
            前往登入
          </button>
        </div>
      )}

      {!loading && !loadError && posts.length === 0 && (
        <div className="card feed-state">
          <h2 className="feed-state-title">還沒有貼文</h2>
          <p className="feed-state-text">還沒有貼文，成為第一個發文的人！</p>
          <button type="button" className="btn btn-primary" onClick={() => setComposerOpen(true)}>
            發佈第一則貼文
          </button>
        </div>
      )}

      {!loading &&
        !loadError &&
        posts.map((post) => <PostCard key={post.id} post={post} />)}

      <ComposerModal
        open={composerOpen}
        onClose={() => setComposerOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  )
}
