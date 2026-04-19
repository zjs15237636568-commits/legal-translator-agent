import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.detail || err?.message || 'Network error'
    return Promise.reject(new Error(msg))
  }
)

// ========== 项目 ==========
export const listProjects = () => api.get('/projects').then((r) => r.data)
export const getProject = (id) => api.get(`/projects/${id}`).then((r) => r.data)
export const deleteProject = (id) => api.delete(`/projects/${id}`).then((r) => r.data)
export const uploadProject = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return api
    .post('/projects/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then((r) => r.data)
}
export const listSegments = (id) =>
  api.get(`/projects/${id}/segments`).then((r) => r.data)

export const retrySegment = (segmentId) =>
  api.post(`/segments/${segmentId}/retry`).then((r) => r.data)

// ========== 翻译 SSE ==========
export const openTranslateStream = (projectId, handlers) => {
  const url = `/api/projects/${projectId}/translate/stream`
  const es = new EventSource(url)
  const { onStart, onDelta, onDone, onError, onAllDone, onFatal } = handlers
  es.addEventListener('segment_start', (e) => onStart && onStart(JSON.parse(e.data)))
  es.addEventListener('segment_delta', (e) => onDelta && onDelta(JSON.parse(e.data)))
  es.addEventListener('segment_done', (e) => onDone && onDone(JSON.parse(e.data)))
  es.addEventListener('segment_error', (e) => onError && onError(JSON.parse(e.data)))
  es.addEventListener('all_done', (e) => {
    onAllDone && onAllDone(JSON.parse(e.data))
    es.close()
  })
  es.addEventListener('fatal', (e) => {
    onFatal && onFatal(JSON.parse(e.data))
    es.close()
  })
  es.onerror = () => {
    // 浏览器默认会自动重连；all_done 后已 close
  }
  return es
}

// ========== 风险 ==========
export const scanRisks = (id) =>
  api.post(`/projects/${id}/risks/scan`).then((r) => r.data)
export const listRisks = (id) =>
  api.get(`/projects/${id}/risks`).then((r) => r.data)

// ========== QA ==========
export const askQA = (id, question) =>
  api.post(`/projects/${id}/qa`, { question }).then((r) => r.data)
export const qaHistory = (id) =>
  api.get(`/projects/${id}/qa/history`).then((r) => r.data)

// ========== Diff ==========
export const diffProjects = (leftId, rightId) =>
  api
    .post('/diff', { left_project_id: leftId, right_project_id: rightId })
    .then((r) => r.data)

// ========== 术语 ==========
export const listGlossary = () => api.get('/glossary').then((r) => r.data)
export const putGlossary = (items) =>
  api.put('/glossary', { items }).then((r) => r.data)
export const upsertTerm = (term) =>
  api.post('/glossary', term).then((r) => r.data)
export const deleteTerm = (en) =>
  api.delete('/glossary', { data: { en } }).then((r) => r.data)

// ========== 配置 ==========
export const getConfig = () => api.get('/config').then((r) => r.data)
export const updateConfig = (cfg) => api.put('/config', cfg).then((r) => r.data)

// ========== 导出 ==========
export const exportDocxUrl = (id) => `/api/projects/${id}/export/docx`
