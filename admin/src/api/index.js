import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      window.location.hash = '#/login'
    }
    return Promise.reject(error)
  }
)

export function login(email, password) {
  // 后端登录接口用的是 PUT /api/user/login + Form (application/x-www-form-urlencoded)
  const params = new URLSearchParams()
  params.append('email', email)
  params.append('password', password)
  return api.put('/user/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export function getStats() {
  return api.get('/admin/stats')
}

export function getUsers(page = 1, pageSize = 20, keyword = '') {
  return api.get('/admin/users', { params: { page, page_size: pageSize, keyword } })
}

export function exportUsers(page = 1, pageSize = 20, keyword = '') {
  return api.get('/admin/users', { params: { keyword, export: true }, responseType: 'blob' }).then(r => r)
}

export function createUser(email, password, role = 0) {
  return api.post('/admin/user', null, { params: { email, password, role } })
}

export function updateUser(id, data) {
  return api.put(`/admin/user/${id}`, null, { params: data })
}

export function deleteUser(id) {
  return api.delete(`/admin/user/${id}`)
}

export function getRecords(page = 1, pageSize = 20, userId = null, state = null) {
  return api.get('/admin/records', { params: { page, page_size: pageSize, user_id: userId, state } })
}

export function exportRecords(page = 1, pageSize = 20, userId = null, state = null) {
  return api.get('/admin/records', { params: { user_id: userId, state, export: true }, responseType: 'blob' }).then(r => r)
}

export function deleteRecord(id) {
  return api.delete(`/admin/record/${id}`)
}

export function getAnalysisStats() {
  return api.get('/admin/analysis-stats')
}

export function getUserChatStats() {
  return api.get('/admin/stats/user-chats')
}

export function getChatSessions(page = 1, pageSize = 20, keyword = '', userId = null) {
  return api.get('/admin/chat-sessions', { params: { page, page_size: pageSize, keyword, user_id: userId } })
}

export function exportChatSessions(page = 1, pageSize = 20, keyword = '', userId = null) {
  return api.get('/admin/chat-sessions', { params: { keyword, user_id: userId, export: true }, responseType: 'blob' }).then(r => r)
}

export function getChatSessionDetail(sessionId) {
  return api.get(`/admin/chat-session/${sessionId}`)
}

export function deleteChatSession(sessionId) {
  return api.delete(`/admin/chat-session/${sessionId}`)
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(new Blob([blob]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export default api
