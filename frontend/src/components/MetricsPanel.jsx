import { useEffect, useState } from 'react'
import { getFeedbackStats } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, RefreshCw } from 'lucide-react'

const COLORS = { openai: '#10b981', anthropic: '#8b5cf6', gemini: '#f59e0b', ollama: '#64748b' }

export default function MetricsPanel() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await getFeedbackStats()
      setStats(res.data)
    } catch {
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const byProvider = stats.reduce((acc, s) => {
    if (!acc[s.provider]) acc[s.provider] = { provider: s.provider, queries: 0, rating: 0, latency: 0, weight: 0, n: 0 }
    acc[s.provider].queries += s.total_queries
    acc[s.provider].rating += s.avg_rating
    acc[s.provider].latency += s.avg_latency_ms
    acc[s.provider].weight += s.routing_weight
    acc[s.provider].n += 1
    return acc
  }, {})

  const chartData = Object.values(byProvider).map((p) => ({
    name: p.provider,
    Rating: parseFloat((p.rating / p.n).toFixed(2)),
    Weight: parseFloat((p.weight / p.n * 100).toFixed(1)),
    Queries: p.queries,
    'Latency (s)': parseFloat((p.latency / p.n / 1000).toFixed(2)),
  }))

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-300">
          <TrendingUp size={15} /> Performance Metrics
        </div>
        <button onClick={load} className="text-gray-500 hover:text-gray-300">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {chartData.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-4">No data yet — start chatting!</p>
      ) : (
        <>
          <div>
            <p className="text-xs text-gray-500 mb-2">Avg Rating by Provider</p>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <YAxis domain={[0, 5]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 11 }}
                />
                <Bar dataKey="Rating" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name] || '#60a5fa'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <p className="text-xs text-gray-500 mb-2">Routing Weight (%)</p>
            <ResponsiveContainer width="100%" height={100}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 11 }}
                />
                <Bar dataKey="Weight" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name] || '#60a5fa'} opacity={0.7} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detail table */}
          <table className="w-full text-xs text-gray-400">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-1">Provider</th>
                <th className="text-right py-1">Queries</th>
                <th className="text-right py-1">Rating</th>
                <th className="text-right py-1">Latency</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((row) => (
                <tr key={row.name} className="border-b border-gray-800">
                  <td className="py-1 capitalize">{row.name}</td>
                  <td className="text-right">{row.Queries}</td>
                  <td className="text-right">{row.Rating}/5</td>
                  <td className="text-right">{row['Latency (s)']}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
