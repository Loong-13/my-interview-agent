import { http, toFormData } from './http'

export const authApi = {
  register: (payload) => http.post('/auth/register', payload),
  login: (payload) => http.post('/auth/login', payload),
  me: () => http.get('/auth/me'),
}

export const projectApi = {
  list: () => http.get('/projects'),
  create: (payload) => http.post('/projects', payload),
  get: (id) => http.get(`/projects/${id}`),
  update: (id, payload) => http.patch(`/projects/${id}`, payload),
  archive: (id) => http.delete(`/projects/${id}`),
}

export const resumeApi = {
  upload: (projectId, file) => http.post(`/projects/${projectId}/resumes`, toFormData({ file })),
  parse: (resumeId) => http.post(`/resumes/${resumeId}/parse`),
  analyze: (resumeId, payload) => http.post(`/resumes/${resumeId}/analyze`, payload),
  get: (resumeId) => http.get(`/resumes/${resumeId}`),
}

export const jdApi = {
  create: (projectId, payload) => http.post(`/projects/${projectId}/job-descriptions`, payload),
  analyze: (jdId) => http.post(`/job-descriptions/${jdId}/analyze`),
}

export const matchApi = {
  create: (projectId, payload) => http.post(`/projects/${projectId}/match-reports`, payload),
}

export const questionApi = {
  generate: (projectId, payload) => http.post(`/projects/${projectId}/questions/generate`, payload),
  generateFromKnowledge: (projectId, payload) =>
    http.post(`/projects/${projectId}/questions/generate-from-knowledge`, payload),
  list: (projectId) => http.get(`/projects/${projectId}/questions`),
}

export const interviewApi = {
  create: (projectId, payload) => http.post(`/projects/${projectId}/interviews`, payload),
  start: (sessionId) => http.post(`/interviews/${sessionId}/start`),
  answer: (sessionId, payload) => http.post(`/interviews/${sessionId}/answers`, payload),
  finish: (sessionId) => http.post(`/interviews/${sessionId}/finish`),
  generateReport: (sessionId) => http.post(`/interviews/${sessionId}/report`),
  getReport: (sessionId) => http.get(`/interviews/${sessionId}/report`),
  messages: (sessionId) => http.get(`/interviews/${sessionId}/messages`),
}

export const taskApi = {
  get: (taskId) => http.get(`/tasks/${taskId}`),
}

export const knowledgeApi = {
  collections: () => http.get('/knowledge/collections'),
  createCollection: (payload) => http.post('/knowledge/collections', payload),
  documents: (collectionId) =>
    http.get('/knowledge/documents', { params: collectionId ? { collection_id: collectionId } : {} }),
  uploadDocument: (collectionId, payload) =>
    http.post(`/knowledge/collections/${collectionId}/documents`, toFormData(payload)),
  createTextDocument: (collectionId, payload) =>
    http.post(`/knowledge/collections/${collectionId}/documents/text`, payload),
  indexDocument: (documentId, payload) => http.post(`/knowledge/documents/${documentId}/index`, payload),
  search: (payload) => http.post('/knowledge/search', payload),
}

export const questionBankApi = {
  list: (params) => http.get('/question-bank/items', { params }),
  create: (payload) => http.post('/question-bank/items', payload),
  import: (payload) => http.post('/question-bank/import', payload),
}
