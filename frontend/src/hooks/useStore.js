import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { secureSet, secureRemove } from '../services/storage'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: async (token, user) => {
        // Store JWT in secure storage (Capacitor Preferences on Android,
        // sessionStorage on web) — NOT localStorage
        await secureSet('token', token)
        set({ token, user })
      },
      logout: async () => {
        await secureRemove('token')
        set({ token: null, user: null })
      },
    }),
    {
      name: 'auth-store',
      // Only persist user metadata (non-sensitive) — token lives in secureSet
      partialize: (state) => ({ user: state.user }),
    }
  )
)

export const useChatStore = create((set) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (id) => set({ currentSessionId: id, messages: [] }),
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (loading) => set({ loading }),
  addSession: (session) => set((s) => ({ sessions: [session, ...s.sessions] })),
  removeSession: (id) => set((s) => ({ sessions: s.sessions.filter((x) => x.id !== id) })),
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
