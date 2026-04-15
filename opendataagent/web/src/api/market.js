import { createJsonClient } from './request'

const request = createJsonClient('/api/v1/skill-market', 120000)

export const marketApi = {
  listItems(params = {}) {
    return request.get('/items', { params })
  },
  getItem(itemId) {
    return request.get(`/items/${itemId}`)
  },
  install(data) {
    return request.post('/install', data)
  },
  importPackage(formData) {
    return request.post('/import', formData)
  }
}
