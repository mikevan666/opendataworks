import { ElMessage } from 'element-plus'
import { createJsonClient } from './request'

const request = createJsonClient('/api', 120000)

request.interceptors.response.use(
  (response) => response,
  (error) => {
    ElMessage.error(error?.message || '请求失败')
    return Promise.reject(error)
  }
)

export const dataagentApi = {
  getSettings() {
    return request.get('/v1/settings/agent')
  },
  updateSettings(data) {
    return request.put('/v1/settings/agent', data)
  },
  listSkillDocuments() {
    return request.get('/v1/skills/documents')
  },
  getSkillDocument(documentId) {
    return request.get(`/v1/skills/documents/${documentId}`)
  },
  updateSkillDocument(documentId, data) {
    return request.put(`/v1/skills/documents/${documentId}`, data)
  },
  deleteSkillDocument(documentId) {
    return request.delete(`/v1/skills/documents/${documentId}`)
  },
  compareSkillDocument(documentId, data) {
    return request.post(`/v1/skills/documents/${documentId}/compare`, data)
  },
  rollbackSkillDocument(documentId, versionId) {
    return request.post(`/v1/skills/documents/${documentId}/versions/${versionId}/rollback`)
  },
  updateSkillRuntime(skillId, data) {
    return request.put(`/v1/skills/runtime/${skillId}`, data)
  },
  syncSkills() {
    return request.post('/v1/skills/runtime/sync')
  }
}
