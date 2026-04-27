import axios from 'axios'
import { ElMessageBox } from 'element-plus'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { authFetch, createJsonClient, getStoredAdminToken } from './request'

vi.mock('element-plus', () => ({
  ElMessageBox: {
    prompt: vi.fn()
  }
}))

const headerValue = (headers, name) => {
  if (!headers) return undefined
  if (typeof headers.get === 'function') return headers.get(name)
  return headers[name]
}

describe('admin token challenge handling', () => {
  let originalAdapter
  let originalFetch

  beforeEach(() => {
    originalAdapter = axios.defaults.adapter
    originalFetch = globalThis.fetch
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    axios.defaults.adapter = originalAdapter
    globalThis.fetch = originalFetch
    window.localStorage.clear()
  })

  it('does not prompt or retry axios requests that hit the admin challenge', async () => {
    const calls = []
    axios.defaults.adapter = vi.fn(async (config) => {
      calls.push(config)
      return Promise.reject({
        config,
        response: {
          status: 401,
          data: { detail: 'admin token required' }
        }
      })
    })
    ElMessageBox.prompt.mockResolvedValue({ value: 'deploy-secret' })

    const client = createJsonClient('/api')
    await expect(client.get('/v1/mcps/servers')).rejects.toMatchObject({
      message: 'admin token required'
    })

    expect(ElMessageBox.prompt).not.toHaveBeenCalled()
    expect(getStoredAdminToken()).toBe('')
    expect(calls).toHaveLength(1)
  })

  it('does not prompt or retry fetch requests that hit the admin challenge', async () => {
    const challengeResponse = new Response(JSON.stringify({ detail: 'admin token required' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' }
    })
    globalThis.fetch = vi.fn().mockResolvedValueOnce(challengeResponse)
    ElMessageBox.prompt.mockResolvedValue({ value: 'stream-secret' })

    const response = await authFetch('/api/v1/agent/tasks/task-1/events/stream', {
      headers: { Accept: 'text/event-stream' }
    })

    expect(response.status).toBe(401)
    expect(ElMessageBox.prompt).not.toHaveBeenCalled()
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    expect(getStoredAdminToken()).toBe('')
    expect(headerValue(globalThis.fetch.mock.calls[0][1].headers, 'Authorization')).toBe(undefined)
  })
})

describe('deployment proxy admin token wiring', () => {
  const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..')

  it('injects the admin token from the web nginx proxy', () => {
    const template = readFileSync(resolve(repoRoot, 'web/deploy/nginx/default.conf.template'), 'utf8')

    expect(template).toContain('proxy_set_header Authorization "Bearer ${OPENDATAAGENT_ADMIN_TOKEN}";')
  })

  it('passes OPENDATAAGENT_ADMIN_TOKEN into the web container', () => {
    const compose = readFileSync(resolve(repoRoot, 'deploy/docker-compose.yml'), 'utf8')

    expect(compose).toContain('opendataagent-web:')
    expect(compose).toContain('OPENDATAAGENT_ADMIN_TOKEN: ${OPENDATAAGENT_ADMIN_TOKEN:-change-me}')
  })
})
