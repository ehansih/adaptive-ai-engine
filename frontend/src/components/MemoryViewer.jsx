import { useEffect, useState } from 'react'
import { listMemory, searchMemory, storeMemory, deleteMemory, exportMemory } from '../services/api'
import { Brain, Search, Plus, Trash2, Download, X } from 'lucide-react'
import clsx from 'clsx'

export default function MemoryViewer() {
  const [entries, setEntries] = useState([])
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [addOpen, setAddOpen] = useState(false)
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [newTags, setNewTags] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    try {
      const res = await listMemory()
      setEntries(res.data)
    } catch {}
  }

  useEffect(() => { load() }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await searchMemory({ query, n_results: 5 })
      setResults(res.data)
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!newKey.trim() || !newValue.trim()) return
    await storeMemory({
      key: newKey,
      value: newValue,
      tags: newTags.split(',').map((t) => t.trim()).filter(Boolean),
    })
    setNewKey(''); setNewValue(''); setNewTags(''); setAddOpen(false)
    load()
  }

  const handleDelete = async (id) => {
    await deleteMemory(id)
    setEntries((prev) => prev.filter((e) => e.id !== id))
  }

  const handleExport = async () => {
    const res = await exportMemory()
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url; a.download = 'memory_export.json'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-300">
          <Brain size={15} /> Memory ({entries.length})
        </div>
        <div className="flex gap-1">
          <button onClick={() => setAddOpen(!addOpen)} className="p-1 text-gray-500 hover:text-gray-300">
            <Plus size={15} />
          </button>
          <button onClick={handleExport} className="p-1 text-gray-500 hover:text-gray-300" title="Export">
            <Download size={15} />
          </button>
        </div>
      </div>

      {/* Semantic search */}
      <div className="flex gap-1">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Semantic search..."
          className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-2.5 py-1.5 text-xs text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
        <button onClick={handleSearch} className="p-1.5 bg-brand-600 hover:bg-brand-700 rounded-lg">
          <Search size={13} className="text-white" />
        </button>
      </div>

      {/* Semantic results */}
      {results.length > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-500">Search results</p>
            <button onClick={() => setResults([])} className="text-gray-600 hover:text-gray-400"><X size={12} /></button>
          </div>
          {results.map((r, i) => (
            <div key={i} className="p-2 bg-gray-800 rounded-lg text-xs text-gray-300 border border-gray-700">
              <p className="font-mono text-gray-500 text-[10px]">{r.metadata?.key}</p>
              <p className="mt-0.5 line-clamp-2">{r.document}</p>
              {r.distance !== null && (
                <p className="text-[10px] text-gray-600 mt-0.5">similarity: {(1 - r.distance).toFixed(3)}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add form */}
      {addOpen && (
        <div className="space-y-2 p-3 bg-gray-800 rounded-xl border border-gray-700">
          <input value={newKey} onChange={(e) => setNewKey(e.target.value)} placeholder="Key"
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500" />
          <textarea value={newValue} onChange={(e) => setNewValue(e.target.value)} placeholder="Value" rows={3}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-100 resize-none focus:outline-none focus:ring-1 focus:ring-brand-500" />
          <input value={newTags} onChange={(e) => setNewTags(e.target.value)} placeholder="Tags (comma separated)"
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500" />
          <button onClick={handleAdd} className="px-3 py-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs">Save</button>
        </div>
      )}

      {/* Entries list */}
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {entries.length === 0 ? (
          <p className="text-xs text-gray-600 text-center py-4">No memories yet</p>
        ) : (
          entries.map((e) => (
            <div key={e.id} className="flex items-start gap-2 p-2 bg-gray-800 rounded-lg border border-gray-700 group">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-brand-400 font-mono truncate">{e.key}</p>
                <p className="text-xs text-gray-400 line-clamp-2 mt-0.5">{e.value}</p>
                {e.tags?.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {e.tags.map((t) => (
                      <span key={t} className="px-1.5 py-0.5 bg-gray-700 rounded text-[10px] text-gray-400">{t}</span>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleDelete(e.id)}
                className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-opacity shrink-0"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
