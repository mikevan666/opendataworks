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

const deferred = () => {
  let resolve
  let reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

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
    expect(wrapper.text()).toContain('思考过程')
    expect(wrapper.find('tool-output-renderer-stub').exists()).toBe(true)
    expect(wrapper.find('.query-process-panel').exists()).toBe(true)
    expect(wrapper.find('.query-process-content').attributes('style') || '').not.toContain('display: none')
  })

  it('collapses the process panel after the final answer is ready', async () => {
    apiMocks.getSession.mockResolvedValue({
      session_id: 's1',
      title: '已完成会话',
      created_at: '2026-03-10T02:00:00Z',
      updated_at: '2026-03-10T02:00:00Z',
      messages: [
        {
          message_id: 'a1',
          role: 'assistant',
          status: 'success',
          created_at: '2026-03-10T02:00:00Z',
          blocks: [
            {
              block_id: 'think-1',
              type: 'thinking',
              status: 'success',
              text: '先检查可用数据表，再决定聚合方式。'
            },
            {
              block_id: 'tool-1',
              type: 'tool',
              status: 'success',
              tool_id: 'tool-bash-1',
              tool_name: 'Bash',
              input: {
                command: 'python scripts/run_sql.py --question top10'
              },
              output: {
                kind: 'python_execution',
                summary: '查询执行完成',
                stdout: 'done'
              }
            },
            {
              block_id: 'main-1',
              type: 'main_text',
              status: 'success',
              text: '最终结果：北区的下单量最高。'
            }
          ]
        }
      ]
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('最终结果：北区的下单量最高。')
    expect(wrapper.find('.query-process-panel').exists()).toBe(true)
    expect(wrapper.find('.query-process-content').attributes('style')).toContain('display: none')

    await wrapper.find('.query-process-summary').trigger('click')
    await flushPromises()

    expect(wrapper.find('.query-process-content').attributes('style') || '').not.toContain('display: none')
  })

  it('allows another session to submit while the current session is still awaiting acceptance', async () => {
    const firstPending = deferred()
    const secondPending = deferred()

    apiMocks.listSessions.mockResolvedValue([
      {
        session_id: 's1',
        title: '会话一',
        created_at: '2026-03-10T02:00:00Z',
        updated_at: '2026-03-10T02:00:00Z'
      },
      {
        session_id: 's2',
        title: '会话二',
        created_at: '2026-03-10T03:00:00Z',
        updated_at: '2026-03-10T03:00:00Z'
      }
    ])
    apiMocks.getSession.mockImplementation(async (sessionId) => ({
      session_id: sessionId,
      title: sessionId === 's1' ? '会话一' : '会话二',
      created_at: '2026-03-10T02:00:00Z',
      updated_at: '2026-03-10T02:00:00Z',
      messages: []
    }))
    apiMocks.sendMessage
      .mockImplementationOnce(() => firstPending.promise)
      .mockImplementationOnce(() => secondPending.promise)

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('第一个问题')
    await wrapper.find('.query-btn-send').trigger('click')
    expect(apiMocks.sendMessage).toHaveBeenCalledTimes(1)

    const sessionButtons = wrapper.findAll('.query-session-item')
    await sessionButtons[1].trigger('click')
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('第二个问题')
    await wrapper.find('.query-btn-send').trigger('click')

    expect(apiMocks.sendMessage).toHaveBeenCalledTimes(2)
    const requestedSessionIds = apiMocks.sendMessage.mock.calls.map((call) => call[0]).sort()
    expect(requestedSessionIds).toEqual(['s1', 's2'])

    firstPending.resolve({
      accepted: true,
      run_id: 'run-1',
      message_id: 'a-run-1',
      status: 'queued',
      message: {
        message_id: 'a-run-1',
        run_id: 'run-1',
        status: 'queued',
        content: '',
        blocks: [],
        error: null,
        provider_id: 'anyrouter',
        model: 'claude-opus-4-6',
        created_at: '2026-03-10T02:00:00Z'
      }
    })
    secondPending.resolve({
      accepted: true,
      run_id: 'run-2',
      message_id: 'a-run-2',
      status: 'queued',
      message: {
        message_id: 'a-run-2',
        run_id: 'run-2',
        status: 'queued',
        content: '',
        blocks: [],
        error: null,
        provider_id: 'anyrouter',
        model: 'claude-opus-4-6',
        created_at: '2026-03-10T02:00:00Z'
      }
    })

    await flushPromises()
    await flushPromises()
  })
})
