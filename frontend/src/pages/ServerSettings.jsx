import { useState, useEffect } from 'react'
import { getBackendUrl, setBackendUrl } from '../services/storage'
import { Server, CheckCircle, AlertTriangle } from 'lucide-react'

export default function ServerSettings({ onClose }) {
  const [url, setUrl] = useState('')
  const [saved, setSaved] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  useEffect(() => {
    getBackendUrl().then(setUrl)
  }, [])

  const testConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch(`${url.replace(/\/$/, '')}/health`, { signal: AbortSignal.timeout(5000) })
      const data = await res.json()
      setTestResult({ ok: true, msg: `Connected — ${data.providers_configured} provider(s) configured` })
    } catch (e) {
      setTestResult({ ok: false, msg: e.message || 'Connection failed' })
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    await setBackendUrl(url)
    setSaved(true)
    setTimeout(() => { setSaved(false); onClose?.() }, 1200)
    // Reload axios base URL
    window.location.reload()
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4">
        <div className="flex items-center gap-2 font-semibold text-white">
          <Server size={18} /> Server Configuration
        </div>

        <div className="space-y-2">
          <label className="text-xs text-gray-500">Backend URL</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-server.com or http://192.168.1.x:8000"
            className="w-full bg-gray-800 border border-gray-600 rounded-xl px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <p className="text-xs text-gray-600">
            Use HTTPS in production. HTTP only for local testing.
          </p>
        </div>

        {testResult && (
          <div className={`flex items-center gap-2 text-xs p-2.5 rounded-lg ${
            testResult.ok ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'
          }`}>
            {testResult.ok ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
            {testResult.msg}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={testConnection}
            disabled={testing || !url}
            className="flex-1 py-2 border border-gray-600 hover:border-gray-400 text-gray-300 rounded-xl text-sm disabled:opacity-40 transition-colors"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={handleSave}
            disabled={!url || saved}
            className="flex-1 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-xl text-sm transition-colors"
          >
            {saved ? '✓ Saved' : 'Save & Reload'}
          </button>
        </div>

        <button onClick={onClose} className="w-full text-xs text-gray-600 hover:text-gray-400">
          Cancel
        </button>
      </div>
    </div>
  )
}
