import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem('token', token)
        set({ token, user })
      },
      logout: () => {
        localStorage.removeItem('token')
        set({ token: null, user: null })
      },
    }),
    { name: 'auth-store' }
  )
)

export const useChatStore = create((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  streamingContent: '',

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (id) => set({ currentSessionId: id, messages: [] }),
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (loading) => set({ loading }),

  addSession: (session) =>
    set((s) => ({ sessions: [session, ...s.sessions] })),
  removeSession: (id) =>
    set((s) => ({ sessions: s.sessions.filter((s) => s.id !== id) })),
}))

export const useSettingsStore = create(
  persist(
    (set) => ({
      provider: '',
      model: '',
      strategy: 'adaptive',
      temperature: 0.7,
      maxTokens: 2048,
      setProvider: (provider) => set({ provider }),
      setModel: (model) => set({ model }),
      setStrategy: (strategy) => set({ strategy }),
      setTemperature: (temperature) => set({ temperature }),
      setMaxTokens: (maxTokens) => set({ maxTokens }),
    }),
    { name: 'settings-store' }
  )
)
