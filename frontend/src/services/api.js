import axios from 'axios'
import { secureGet, secureRemove, getBackendUrl } from './storage'

// Resolve base URL at startup — Capacitor reads from secure storage,
// web dev proxy uses /api which Vite forwards to localhost:8000
const isCapacitorNative = () =>
  typeof window !== 'undefined' && window?.Capacitor?.isNativePlatform?.()

async function resolveBaseUrl() {
  if (isCapacitorNative()) {
    const url = await getBackendUrl()
    return url  // e.g. https://yourserver.com or http://192.168.1.x:8000
  }
  return '/api'  // Vite dev proxy → localhost:8000
}

const api = axios.create({ timeout: 120000 })

// Set base URL once at startup
resolveBaseUrl().then((url) => { api.defaults.baseURL = url })

api.interceptors.request.use(async (config) => {
  // Use secure storage on native, sessionStorage on web
  const token = await secureGet('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      await secureRemove('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const register = (data) => api.post('/auth/register', data)
export const login = (data) => api.post('/auth/login', data)

// Chat
export const sendMessage = (data) => api.post('/chat/', data)
export const getSessions = () => api.get('/chat/sessions')
export const getMessages = (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`)
export const deleteSession = (sessionId) => api.delete(`/chat/sessions/${sessionId}`)

// Feedback
export const submitFeedback = (data) => api.post('/feedback/', data)
export const getFeedbackStats = () => api.get('/feedback/stats')
export const getFeedbackHistory = (limit = 20) => api.get(`/feedback/history?limit=${limit}`)

// Memory
export const storeMemory = (data) => api.post('/memory/', data)
export const listMemory = (tag, limit = 50) =>
  api.get(`/memory/?limit=${limit}${tag ? `&tag=${tag}` : ''}`)
export const searchMemory = (data) => api.post('/memory/search', data)
export const deleteMemory = (id) => api.delete(`/memory/${id}`)
export const exportMemory = () => api.get('/memory/export', { responseType: 'blob' })

// Models
export const getProviders = () => api.get('/models/providers')
export const getModelHealth = () => api.get('/models/health')

export default api
