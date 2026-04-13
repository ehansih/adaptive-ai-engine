import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import Chat from './components/Chat'
import ModelSelector from './components/ModelSelector'
import MetricsPanel from './components/MetricsPanel'
import MemoryViewer from './components/MemoryViewer'
import LoginPage from './pages/LoginPage'
import ServerSettings from './pages/ServerSettings'
import { useAuthStore } from './hooks/useStore'
import { Bot, Brain, BarChart2, Settings, LogOut, Menu, X, ServerCog } from 'lucide-react'
import clsx from 'clsx'

function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [sideTab, setSideTab] = useState('metrics')
  const [showServerSettings, setShowServerSettings] = useState(false)
  const [rightOpen, setRightOpen] = useState(true)

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100">
      {/* Top bar */}
      <header className="h-12 border-b border-gray-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <Bot size={15} className="text-white" />
          </div>
          <span className="font-semibold text-sm text-white">Adaptive AI Engine</span>
          <span className="text-[10px] text-gray-600 ml-1">v1.0.0</span>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-xs text-gray-500">
              {user.username} <span className="text-gray-700">({user.role})</span>
            </span>
          )}
          {user ? (
            <button onClick={handleLogout} className="text-gray-500 hover:text-gray-300 text-xs flex items-center gap-1">
              <LogOut size={13} /> Sign out
            </button>
          ) : (
            <button onClick={() => navigate('/login')} className="text-brand-400 hover:text-brand-300 text-xs">
              Sign in
            </button>
          )}
          <button
            onClick={() => setShowServerSettings(true)}
            title="Server URL"
            className="text-gray-500 hover:text-gray-300"
          >
            <ServerCog size={16} />
          </button>
          <button
            onClick={() => setRightOpen(!rightOpen)}
            className="text-gray-500 hover:text-gray-300"
          >
            {rightOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </header>

      {showServerSettings && <ServerSettings onClose={() => setShowServerSettings(false)} />}
      <div className="flex-1 flex overflow-hidden">
        {/* Main chat */}
        <div className="flex-1 overflow-hidden">
          <Chat />
        </div>

        {/* Right panel */}
        {rightOpen && (
          <div className="w-72 border-l border-gray-800 flex flex-col bg-gray-950 shrink-0">
            {/* Tab bar */}
            <div className="flex border-b border-gray-800 shrink-0">
              {[
                { id: 'metrics', icon: BarChart2, label: 'Metrics' },
                { id: 'memory', icon: Brain, label: 'Memory' },
                { id: 'settings', icon: Settings, label: 'Settings' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSideTab(tab.id)}
                  className={clsx(
                    'flex-1 flex flex-col items-center py-2.5 text-[10px] gap-1 transition-colors',
                    sideTab === tab.id
                      ? 'text-brand-400 border-b-2 border-brand-500'
                      : 'text-gray-600 hover:text-gray-400'
                  )}
                >
                  <tab.icon size={14} />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-3">
              {sideTab === 'metrics' && <MetricsPanel />}
              {sideTab === 'memory' && <MemoryViewer />}
              {sideTab === 'settings' && <ModelSelector />}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<Layout />} />
    </Routes>
  )
}
