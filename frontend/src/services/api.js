import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
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
