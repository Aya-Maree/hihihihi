import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Session
export const createSession = (hostName) =>
  api.post('/session/create', { host_name: hostName })

export const getSession = (sessionId) =>
  api.get(`/session/${sessionId}`)

export const getEventContext = (sessionId) =>
  api.get(`/session/${sessionId}/context`)

export const updateEventContext = (sessionId, updates) =>
  api.patch(`/session/${sessionId}/context`, { session_id: sessionId, updates })

// Chat
export const sendChat = (sessionId, message) =>
  api.post('/chat', { session_id: sessionId, message })

export const getChatHistory = (sessionId, limit = 50) =>
  api.get(`/chat/${sessionId}/history`, { params: { limit } })

// Planning
export const startPlanning = (sessionId, eventData) =>
  api.post('/plan/start', { session_id: sessionId, ...eventData })

// Artifacts
export const generateArtifacts = (sessionId, enrichWithSpoonacular = false) =>
  api.post('/artifacts/generate', {
    session_id: sessionId,
    enrich_with_spoonacular: enrichWithSpoonacular,
  })

export const getArtifacts = (sessionId) =>
  api.get(`/artifacts/${sessionId}`)

export const getArtifactMarkdown = (sessionId, artifactType) =>
  api.get(`/artifacts/${sessionId}/${artifactType}/markdown`)

export const downloadArtifacts = (sessionId) =>
  api.get(`/artifacts/${sessionId}/download`, { responseType: 'blob' })

// RAG
export const listDocuments = () => api.get('/rag/documents')

export const retrieveDocuments = (query, sessionId, topK = 5) =>
  api.post('/rag/retrieve', { query, session_id: sessionId, top_k: topK })

// Spoonacular
export const getRecipes = (eventType, servings, dietary) =>
  api.get('/spoonacular/recipes', {
    params: { event_type: eventType, servings, dietary },
  })

export const getHealth = () => api.get('/health')

export default api
