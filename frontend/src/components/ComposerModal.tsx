import { useState } from 'react'
import type { FormEvent } from 'react'
import { Modal } from './Modal'
import { apiFetch, errorMessage } from '../lib/api'
import type { Post } from '../types'

interface ComposerModalProps {
  open: boolean
  onClose: () => void
  onCreated: (post: Post) => void
}

export function ComposerModal({ open, onClose, onCreated }: ComposerModalProps) {
  const [content, setContent] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const reset = () => {
    setContent('')
    setImageUrl('')
    setError('')
    setBusy(false)
  }

  const close = () => {
    if (busy) return
    reset()
    onClose()
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!content.trim()) {
      setError('請輸入貼文內容')
      return
    }
    setBusy(true)
    setError('')
    try {
      const res = await apiFetch<{ post: Post }>('/posts', {
        method: 'POST',
        body: {
          content: content.trim(),
          image_url: imageUrl.trim() ? imageUrl.trim() : null,
        },
      })
      onCreated(res.post)
      reset()
      onClose()
    } catch (err) {
      setError(errorMessage(err, '發佈失敗，請稍後再試'))
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title="建立貼文" onClose={close}>
      <form className="composer-form" onSubmit={submit}>
        <label className="sr-only" htmlFor="composer-content">
          貼文內容
        </label>
        <textarea
          id="composer-content"
          className="composer-textarea"
          placeholder="你在想什麼？"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={5}
          autoFocus
        />
        <label className="sr-only" htmlFor="composer-image">
          圖片網址（選填）
        </label>
        <input
          id="composer-image"
          type="url"
          className="composer-input"
          placeholder="圖片網址（選填）"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
        />
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary composer-submit" disabled={busy}>
          {busy ? '發佈中…' : '發佈'}
        </button>
      </form>
    </Modal>
  )
}
