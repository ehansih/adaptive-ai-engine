import { useState } from 'react'
import { submitFeedback } from '../services/api'
import { ThumbsUp, ThumbsDown, Star, RotateCcw, CheckCircle } from 'lucide-react'
import clsx from 'clsx'

const TAGS = ['helpful', 'accurate', 'too_long', 'too_short', 'wrong', 'off_topic', 'needs_retry']

export default function FeedbackPanel({ messageId, provider, onRetry }) {
  const [rating, setRating] = useState(0)
  const [selected, setSelected] = useState([])
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  const toggleTag = (tag) =>
    setSelected((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag])

  const handleSubmit = async () => {
    if (!rating) return
    setLoading(true)
    try {
      const res = await submitFeedback({ message_id: messageId, rating, tags: selected, comment })
      setSubmitted(true)
      if (res.data.triggered_retry && onRetry) onRetry()
    } catch {
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="flex items-center gap-2 text-xs text-green-400 mt-2">
        <CheckCircle size={13} /> Feedback recorded. Model weights updated.
      </div>
    )
  }

  return (
    <div className="mt-2">
      {/* Quick thumbs */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">Rate this response:</span>
        {[1,2,3,4,5].map((n) => (
          <button
            key={n}
            onClick={() => { setRating(n); setOpen(true) }}
            className={clsx(
              'transition-colors',
              rating >= n ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'
            )}
          >
            <Star size={14} fill={rating >= n ? 'currentColor' : 'none'} />
          </button>
        ))}
        {rating > 0 && (
          <button onClick={() => setOpen(!open)} className="text-xs text-gray-500 hover:text-gray-300 ml-1">
            {open ? 'hide' : 'details'}
          </button>
        )}
      </div>

      {open && (
        <div className="mt-2 p-3 bg-gray-800 rounded-xl border border-gray-700 space-y-3 text-xs">
          {/* Tags */}
          <div className="flex flex-wrap gap-1.5">
            {TAGS.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={clsx(
                  'px-2 py-0.5 rounded-full border text-xs transition-colors',
                  selected.includes(tag)
                    ? 'bg-brand-600 border-brand-500 text-white'
                    : 'border-gray-600 text-gray-400 hover:border-gray-400'
                )}
              >
                {tag.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Comment */}
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional comment..."
            rows={2}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-100 resize-none focus:outline-none focus:ring-1 focus:ring-brand-500"
          />

          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={!rating || loading}
              className="px-3 py-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-lg text-xs transition-colors"
            >
              {loading ? 'Saving...' : 'Submit Feedback'}
            </button>
            {rating <= 2 && onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-1 px-3 py-1 border border-gray-600 hover:border-gray-400 text-gray-300 rounded-lg text-xs transition-colors"
              >
                <RotateCcw size={11} /> Retry with different model
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
