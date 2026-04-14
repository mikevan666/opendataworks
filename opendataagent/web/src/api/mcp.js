import { createJsonClient } from './request'

const request = createJsonClient('/api/v1/mcps', 120000)

export const mcpApi = {
  listServers() {
    return request.get('/servers')
  },
  createServer(data) {
    return request.post('/servers', data)
  },
  updateServer(serverId, data) {
    return request.put(`/servers/${serverId}`, data)
  },
  deleteServer(serverId) {
    return request.delete(`/servers/${serverId}`)
  },
  testServer(serverId) {
    return request.post(`/servers/${serverId}/test`)
  }
}
