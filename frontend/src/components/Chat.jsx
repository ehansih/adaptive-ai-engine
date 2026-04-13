import { useEffect, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { sendMessage, getMessages, getSessions, deleteSession } from '../services/api'
import { useChatStore, useSettingsStore } from '../hooks/useStore'
import FeedbackPanel from './FeedbackPanel'
import { Send, Bot, User, Plus, Trash2, MessageSquare, Loader2, Zap, DollarSign } from 'lucide-react'
import clsx from 'clsx'

function Message({ msg, onRetry }) {
  const isUser = msg.role === 'user'
  return (
    <div className={clsx('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div className={clsx(
        'w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5',
        isUser ? 'bg-brand-600' : 'bg-gray-700'
      )}>
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>
      <div className={clsx('flex flex-col max-w-[85%]', isUser ? 'items-end' : 'items-start')}>
        <div className={clsx(
          'rounded-2xl px-4 py-2.5 text-sm',
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-gray-800 text-gray-100 rounded-tl-sm'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div" {...props}>
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className="bg-gray-900 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                      {children}
                    </code>
                  )
                },
              }}
            >
              {msg.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Message metadata */}
        {!isUser && msg.provider && (
          <div className="flex items-center gap-3 mt-1 px-1">
            <span className="text-[10px] text-gray-500 capitalize">{msg.provider}/{msg.model_used?.split('/').pop()}</span>
            {msg.latency_ms > 0 && (
              <span className="flex items-center gap-0.5 text-[10px] text-gray-600">
                <Zap size={8} />{(msg.latency_ms / 1000).toFixed(1)}s
              </span>
            )}
            {msg.cost_usd > 0 && (
              <span className="flex items-center gap-0.5 text-[10px] text-gray-600">
                <DollarSign size={8} />{msg.cost_usd.toFixed(5)}
              </span>
            )}
            {msg.attempt > 1 && (
              <span className="text-[10px] text-yellow-600">retry #{msg.attempt}</span>
            )}
          </div>
        )}

        {!isUser && msg.id && (
          <FeedbackPanel messageId={msg.id} provider={msg.provider} onRetry={onRetry} />
        )}
      </div>
    </div>
  )
}

export default function Chat() {
  const { sessions, currentSessionId, messages, loading,
          setSessions, setCurrentSession, setMessages, addMessage, setLoading, addSession, removeSession } = useChatStore()
  const { provider, model, strategy, temperature, maxTokens } = useSettingsStore()
  const [input, setInput] = useState('')
  const [retryMsg, setRetryMsg] = useState(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    getSessions().then((r) => setSessions(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const loadSession = async (id) => {
    setCurrentSession(id)
    try {
      const res = await getMessages(id)
      setMessages(res.data)
    } catch {}
  }

  const handleSend = useCallback(async (overrideProvider, overrideModel) => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    const userMsg = { role: 'user', content: text, id: null }
    addMessage(userMsg)

    try {
      const res = await sendMessage({
        message: text,
        session_id: currentSessionId,
        provider: overrideProvider || provider || undefined,
        model: overrideModel || model || undefined,
        strategy,
        temperature,
        max_tokens: maxTokens,
      })
      const data = res.data

      if (!currentSessionId) {
        setCurrentSession(data.session_id)
        addSession({ id: data.session_id, title: text.slice(0, 60), created_at: new Date().toISOString() })
        setSessions((prev) => [{ id: data.session_id, title: text.slice(0, 60) }, ...prev])
      }

      addMessage({
        id: data.message_id,
        role: 'assistant',
        content: data.content,
        provider: data.provider,
        model_used: data.model,
        tokens_in: data.tokens_in,
        tokens_out: data.tokens_out,
        latency_ms: data.latency_ms,
        cost_usd: data.cost_usd,
        attempt: data.attempt,
      })
    } catch (err) {
      addMessage({
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || err.message}`,
        id: null,
      })
    } finally {
      setLoading(false)
    }
  }, [input, loading, currentSessionId, provider, model, strategy, temperature, maxTokens])

  const handleRetry = () => {
    // Pick a different provider from current
    const others = ['openai', 'anthropic', 'gemini'].filter((p) => p !== provider)
    handleSend(others[0] || undefined, undefined)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    setCurrentSession(null)
    setMessages([])
  }

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation()
    await deleteSession(id)
    removeSession(id)
    if (currentSessionId === id) handleNewChat()
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-56 bg-gray-900 border-r border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-700">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm transition-colors"
          >
            <Plus size={15} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => loadSession(s.id)}
              className={clsx(
                'w-full flex items-center gap-2 px-2 py-2 rounded-lg text-left text-xs group transition-colors',
                currentSessionId === s.id
                  ? 'bg-gray-700 text-gray-100'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              )}
            >
              <MessageSquare size={12} className="shrink-0" />
              <span className="flex-1 truncate">{s.title || 'Chat'}</span>
              <button
                onClick={(e) => handleDeleteSession(e, s.id)}
                className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400"
              >
                <Trash2 size={11} />
              </button>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot size={48} className="text-gray-700 mb-4" />
              <h2 className="text-xl font-semibold text-gray-400">Adaptive AI Engine</h2>
              <p className="text-sm text-gray-600 mt-2 max-w-sm">
                Multi-model AI with adaptive routing. Responses improve with your feedback.
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} onRetry={handleRetry} />
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center">
                <Bot size={14} />
              </div>
              <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 size={16} className="animate-spin text-gray-400" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex gap-2 items-end bg-gray-800 border border-gray-600 rounded-2xl px-4 py-2 focus-within:border-brand-500 transition-colors">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
              rows={1}
              style={{ maxHeight: 200 }}
              className="flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none py-1"
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="p-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-xl text-white transition-colors shrink-0"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
