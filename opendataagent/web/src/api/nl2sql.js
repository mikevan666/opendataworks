import { authFetch, createJsonClient } from './request'

const DEFAULT_TIMEOUT = 120000
const RUNTIME_PREFIX = '/api/v1/agent'

async function extractHttpError(response) {
  try {
    const data = await response.clone().json()
    if (data?.detail) return String(data.detail)
    if (data?.error) return String(data.error)
  } catch (_error) {
    // ignore
  }

  try {
    const text = await response.text()
    if (text) return text
  } catch (_error) {
    // ignore
  }

  return `${response.status} ${response.statusText || 'Request failed'}`
}

function parseSseChunk(buffer, onEvent) {
  let rest = buffer
  while (true) {
    const splitAt = rest.indexOf('\n\n')
    if (splitAt < 0) break
    const rawEvent = rest.slice(0, splitAt)
    rest = rest.slice(splitAt + 2)

    let eventName = ''
    const dataLines = []
    const lines = rawEvent.split('\n').map((line) => line.trimEnd())

    for (const line of lines) {
      if (!line || line.startsWith(':')) continue
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
        continue
      }
      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (!dataLines.length) continue

    try {
      const payload = JSON.parse(dataLines.join('\n'))
      if (eventName && !payload.type) payload.type = eventName
      if (eventName) payload.sse_event = eventName
      onEvent?.(payload)
    } catch (_error) {
      // ignore malformed chunks
    }
  }

  return rest
}

export function createNl2SqlApiClient(options = {}) {
  const timeout = options.timeout || DEFAULT_TIMEOUT
  const runtimeRequest = createJsonClient(RUNTIME_PREFIX, timeout)
  const adminRequest = createJsonClient('/api/v1/settings', timeout)

  const topicApi = {
    createTopic(title = '新话题') {
      return runtimeRequest.post('/topics', { title })
    },
    listTopics() {
      return runtimeRequest.get('/topics')
    },
    getTopic(topicId) {
      return runtimeRequest.get(`/topics/${topicId}`)
    },
    updateTopic(topicId, data) {
      return runtimeRequest.put(`/topics/${topicId}`, data)
    },
    deleteTopic(topicId) {
      return runtimeRequest.delete(`/topics/${topicId}`)
    },
    getTopicMessages(topicId, params = {}) {
      return runtimeRequest.get(`/topics/${topicId}/messages`, { params })
    }
  }

  const taskApi = {
    deliverMessage(data) {
      return runtimeRequest.post('/tasks/deliver-message', data)
    },
    createTask(data) {
      return runtimeRequest.post('/tasks', data)
    },
    getTask(taskId) {
      return runtimeRequest.get(`/tasks/${taskId}`)
    },
    getTaskEvents(taskId, params = {}) {
      return runtimeRequest.get(`/tasks/${taskId}/events`, { params })
    },
    cancelTask(taskId) {
      return runtimeRequest.post(`/tasks/${taskId}/cancel`)
    },
    async streamTaskEvents(taskId, options = {}) {
      const { onEvent, signal, afterSeq = 0 } = options
      const response = await authFetch(
        `${RUNTIME_PREFIX}/tasks/${encodeURIComponent(taskId)}/events/stream?after_seq=${encodeURIComponent(afterSeq)}`,
        {
          method: 'GET',
          headers: { Accept: 'text/event-stream' },
          signal
        }
      )

      if (!response.ok) {
        throw new Error(await extractHttpError(response))
      }
      if (!response.body) {
        throw new Error('SSE stream body is empty')
      }

      const decoder = new TextDecoder('utf-8')
      const reader = response.body.getReader()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        buffer = parseSseChunk(buffer, onEvent)
      }

      if (buffer.trim()) {
        parseSseChunk(`${buffer}\n\n`, onEvent)
      }
    }
  }

  const adminApi = {
    getSettings() {
      return adminRequest.get('/agent')
    },
    updateSettings(data) {
      return adminRequest.put('/agent', data)
    }
  }

  return {
    topicApi,
    taskApi,
    adminApi,
    health() {
      return runtimeRequest.get('/health')
    }
  }
}
