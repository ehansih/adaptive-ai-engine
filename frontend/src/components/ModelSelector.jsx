import { useEffect, useState } from 'react'
import { getProviders } from '../services/api'
import { useSettingsStore } from '../hooks/useStore'
import { Cpu, ChevronDown } from 'lucide-react'

export default function ModelSelector() {
  const [providers, setProviders] = useState([])
  const { provider, model, strategy, temperature, maxTokens,
          setProvider, setModel, setStrategy, setTemperature, setMaxTokens } = useSettingsStore()

  useEffect(() => {
    getProviders()
      .then((r) => setProviders(r.data))
      .catch(() => {})
  }, [])

  const currentProvider = providers.find((p) => p.id === provider)

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-300">
        <Cpu size={15} /> Model Settings
      </div>

      {/* Provider */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Provider</label>
        <select
          value={provider}
          onChange={(e) => { setProvider(e.target.value); setModel('') }}
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">Auto (Adaptive)</option>
          {providers.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      {/* Model */}
      {currentProvider && (
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Model</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">Default ({currentProvider.default})</option>
            {currentProvider.models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      )}

      {/* Strategy */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Routing Strategy</label>
        <select
          value={strategy}
          onChange={(e) => setStrategy(e.target.value)}
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="adaptive">Adaptive (Feedback-Driven)</option>
          <option value="round-robin">Round Robin</option>
          <option value="cost-optimized">Cost Optimized</option>
        </select>
      </div>

      {/* Temperature */}
      <div>
        <label className="text-xs text-gray-500 mb-1 flex justify-between">
          <span>Temperature</span>
          <span className="text-gray-300">{temperature}</span>
        </label>
        <input
          type="range" min="0" max="1" step="0.05"
          value={temperature}
          onChange={(e) => setTemperature(parseFloat(e.target.value))}
          className="w-full accent-brand-500"
        />
      </div>

      {/* Max Tokens */}
      <div>
        <label className="text-xs text-gray-500 mb-1 flex justify-between">
          <span>Max Tokens</span>
          <span className="text-gray-300">{maxTokens}</span>
        </label>
        <input
          type="range" min="256" max="8192" step="256"
          value={maxTokens}
          onChange={(e) => setMaxTokens(parseInt(e.target.value))}
          className="w-full accent-brand-500"
        />
      </div>
    </div>
  )
}
