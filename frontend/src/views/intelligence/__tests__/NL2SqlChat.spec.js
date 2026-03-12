import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  createSession: vi.fn(),
  listSessions: vi.fn(),
  getSession: vi.fn(),
  deleteSession: vi.fn(),
  sendMessage: vi.fn(),
  streamMessage: vi.fn(),
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
  health: vi.fn()
}))

vi.mock('@/api/nl2sql', () => ({
  createNl2SqlApiClient: () => apiMocks
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

vi.mock('element-plus/theme-chalk/el-message.css', () => ({}))

import NL2SqlChat from '../NL2SqlChat.vue'

describe('NL2SqlChat', () => {
  beforeEach(() => {
    apiMocks.getSettings.mockResolvedValue({
      default_provider_id: 'anyrouter',
      default_model: 'claude-opus-4-6',
      providers: [
        {
          provider_id: 'anyrouter',
          display_name: 'AnyRouter',
          models: ['claude-opus-4-6'],
          default_model: 'claude-opus-4-6'
        }
      ]
    })
    apiMocks.listSessions.mockResolvedValue([
      {
        session_id: 's1',
        title: '流式会话',
        created_at: '2026-03-10T02:00:00Z',
        updated_at: '2026-03-10T02:00:00Z'
      }
    ])
    apiMocks.getSession.mockResolvedValue({
      session_id: 's1',
      title: '流式会话',
      created_at: '2026-03-10T02:00:00Z',
      updated_at: '2026-03-10T02:00:00Z',
      messages: [
        {
          message_id: 'a1',
          role: 'assistant',
          status: 'streaming',
          created_at: '2026-03-10T02:00:00Z',
          blocks: [
            {
              block_id: 'main-1',
              type: 'main_text',
              status: 'streaming',
              text: '问题类型：趋势分析。指标：workflow_publish_record 的发布记录数，按 created_at 按天聚合，最近 30 天。平台核心表，直接走 opendataworks MySQL。'
            },
            {
              block_id: 'tool-1',
              type: 'tool',
              status: 'streaming',
              tool_id: 'tool-bash-1',
              tool_name: 'Bash',
              input: {
                command: 'python scripts/run_sql.py --question trend'
              },
              output: ''
            }
          ]
        }
      ]
    })
  })

  it('keeps streamed main text visible while tools are still running', async () => {
    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('问题类型：趋势分析')
    expect(wrapper.text()).toContain('workflow_publish_record')
    expect(wrapper.text()).toContain('opendataworks MySQL')
    expect(wrapper.find('tool-output-renderer-stub').exists()).toBe(true)
    expect(wrapper.find('.query-loading').exists()).toBe(false)
  })
})
