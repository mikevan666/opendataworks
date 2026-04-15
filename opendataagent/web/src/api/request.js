import axios from 'axios'

const ADMIN_TOKEN_KEY = 'oda_admin_token'

export function getStoredAdminToken() {
  if (typeof window === 'undefined') return ''
  return String(window.localStorage.getItem(ADMIN_TOKEN_KEY) || '').trim()
}

export function setStoredAdminToken(token) {
  if (typeof window === 'undefined') return
  const value = String(token || '').trim()
  if (value) {
    window.localStorage.setItem(ADMIN_TOKEN_KEY, value)
  } else {
    window.localStorage.removeItem(ADMIN_TOKEN_KEY)
  }
}

export function buildAuthHeaders(headers = {}) {
  const token = getStoredAdminToken()
  if (!token) return { ...headers }
  return {
    ...headers,
    Authorization: `Bearer ${token}`
  }
}

export function createJsonClient(baseURL, timeout = 120000) {
  const request = axios.create({
    baseURL,
    timeout
  })

  request.interceptors.request.use((config) => {
    config.headers = buildAuthHeaders(config.headers || {})
    return config
  })

  request.interceptors.response.use(
    (response) => response.data,
    (error) => {
      const message = error?.response?.data?.detail || error?.response?.data?.message || error?.response?.data?.error || error.message || '请求失败'
      error.message = message
      return Promise.reject(error)
    }
  )

  return request
}

export function authFetch(input, init = {}) {
  return fetch(input, {
    ...init,
    headers: buildAuthHeaders(init.headers || {})
  })
}
