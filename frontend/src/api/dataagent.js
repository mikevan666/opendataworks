import axios from 'axios'
import { ElMessage } from 'element-plus'

const dataagentRequest = axios.create({
  baseURL: '/api',
  timeout: 120000
})

dataagentRequest.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error?.response?.data?.detail || error?.response?.data?.message || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const dataagentApi = {
  getSettings() {
    return dataagentRequest.get('/v1/nl2sql-admin/settings')
  },

  updateSettings(data) {
    return dataagentRequest.put('/v1/nl2sql-admin/settings', data)
  },

  detectModel(data) {
    return dataagentRequest.post('/v1/nl2sql-admin/model-detections', data)
  },

  listSkillDocuments() {
    return dataagentRequest.get('/v1/dataagent/skills/documents')
  },

  getSkillDocument(documentId) {
    return dataagentRequest.get(`/v1/dataagent/skills/documents/${documentId}`)
  },

  updateSkillDocument(documentId, data) {
    return dataagentRequest.put(`/v1/dataagent/skills/documents/${documentId}`, data)
  },

  updateSkillRuntime(folder, data) {
    return dataagentRequest.put(`/v1/dataagent/skills/runtime/${encodeURIComponent(folder)}`, data)
  },

  compareSkillDocument(documentId, data) {
    return dataagentRequest.post(`/v1/dataagent/skills/documents/${documentId}/compare`, data)
  },

  rollbackSkillDocument(documentId, versionId) {
    return dataagentRequest.post(`/v1/dataagent/skills/documents/${documentId}/versions/${versionId}/rollback`)
  },

  syncSkills() {
    return dataagentRequest.post('/v1/dataagent/skills/sync')
  }
}
