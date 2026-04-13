import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../services/api'
import { useAuthStore } from '../hooks/useStore'
import { Bot, LogIn, UserPlus } from 'lucide-react'

export default function LoginPage() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const fn = mode === 'login' ? login : register
      const payload = mode === 'login' ? { username, password } : { username, email, password }
      const res = await fn(payload)
      setAuth(res.data.access_token, { id: res.data.user_id, username: res.data.username, role: res.data.role })
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-600 rounded-2xl mb-4">
            <Bot size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Adaptive AI Engine</h1>
          <p className="text-gray-500 text-sm mt-1">Multi-model AI Orchestration</p>
        </div>

        <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 space-y-4">
          <div className="flex rounded-xl bg-gray-800 p-1">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-1.5 text-sm rounded-lg transition-colors capitalize ${
                  mode === m ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              required
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            {mode === 'register' && (
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                className="w-full bg-gray-800 border border-gray-600 rounded-xl px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            )}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors"
            >
              {mode === 'login' ? <LogIn size={15} /> : <UserPlus size={15} />}
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-xs text-gray-600">
            Or{' '}
            <button onClick={() => navigate('/')} className="text-brand-400 hover:underline">
              continue as guest
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
