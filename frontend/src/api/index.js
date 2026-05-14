import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 5000
})

export const todoApi = {
  getTodos: (completed) => api.get('/todos', { params: { completed } }),
  getTodo: (id) => api.get(`/todos/${id}`),
  createTodo: (data) => api.post('/todos', data),
  updateTodo: (id, data) => api.put(`/todos/${id}`, data),
  completeTodo: (id) => api.post(`/todos/${id}/complete`),
  toggleTodo: (id) => api.post(`/todos/${id}/toggle`),
  deleteTodo: (id) => api.delete(`/todos/${id}`),
  getStats: () => api.get('/todos/stats')
}

export const imageApi = {
  searchImages: (keyword, count = 3, source = 'baidu') => 
    api.get('/images/search', { params: { keyword, count, source } }),
  getCatImages: (count = 3) => api.get('/images/cat', { params: { count } }),
  getLoliconImages: (keyword = '', count = 3, r18 = 0) => 
    api.get('/images/lolicon', { params: { keyword, count, r18 } }),
  getStats: () => api.get('/images/stats')
}

export const agentApi = {
  getTools: () => api.get('/agent/tools'),
  chat: (message) => api.post('/agent/chat', { message })
}

export const biliApi = {
  getStatus: () => api.get('/bili/status'),
  getUps: () => api.get('/bili/ups'),
  addUp: (name, uid, check_interval = 60, enabled = true) => api.post('/bili/ups', null, { params: { name, uid, check_interval, enabled } }),
  removeUp: (up_name) => api.delete(`/bili/ups/${up_name}`),
  toggleUp: (up_name) => api.post(`/bili/ups/${up_name}/toggle`),
  getLoginQr: () => api.get('/bili/login/qr'),
  pollLogin: (qrcode_key) => api.post('/bili/login/poll', { qrcode_key }),
  getLoginResult: (qrcode_key) => api.get(`/bili/login/result/${qrcode_key}`),
  checkUp: (up_name) => api.get(`/bili/check/${up_name}`),
  getCache: (up_name) => api.get(`/bili/cache/${up_name}`),
  // checkAll需要更长的超时时间，因为逐个检查每个UP主
  checkAll: () => api.get('/bili/check', { timeout: 30000 }),
  getImageProxyUrl: (url) => `/api/bili/image/proxy?url=${encodeURIComponent(url)}`,
  updateInterval: (up_name, interval) => api.post('/bili/config/interval', null, { params: { up_name, interval_minutes: interval } }),
  getConfig: () => api.get('/bili/config'),
  saveConfig: (check_on_start) => api.post('/bili/config', null, { params: { check_on_start } }),
  startScheduler: (check_on_start) => api.post('/bili/config/scheduler/start', null, { params: { check_on_start } }),
  stopScheduler: () => api.post('/bili/config/scheduler/stop'),
  getSchedulerStatus: () => api.get('/bili/config/scheduler/status')
}

export const jmApi = {
  download: (album_id) => api.post('/jm/download', { album_id }),
  getStatus: (album_id) => api.get(`/jm/status/${album_id}`),
  getRecent: () => api.get('/jm/recent'),
  getHistory: () => api.get('/jm/history'),
  deleteItem: (album_id) => api.delete(`/jm/item/${album_id}`),
  getPdfUrl: (album_id) => `/api/jm/pdf/${album_id}`,
  getCoverUrl: (album_id) => `/api/jm/cover/${album_id}`
}

export default api
