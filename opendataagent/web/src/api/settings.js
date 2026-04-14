import { createJsonClient } from './request'

const request = createJsonClient('/api/v1/settings', 120000)

export const settingsApi = {
  getAgentSettings() {
    return request.get('/agent')
  },
  updateAgentSettings(data) {
    return request.put('/agent', data)
  }
}
