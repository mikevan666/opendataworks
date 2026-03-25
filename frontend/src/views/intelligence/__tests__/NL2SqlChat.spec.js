import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  topicApi: {
    createTopic: vi.fn(),
    listTopics: vi.fn(),
    getTopic: vi.fn(),
    updateTopic: vi.fn(),
    deleteTopic: vi.fn(),
    getTopicMessages: vi.fn()
  },
  taskApi: {
    deliverMessage: vi.fn(),
    createTask: vi.fn(),
    getTask: vi.fn(),
    getTaskEvents: vi.fn(),
    cancelTask: vi.fn(),
    streamTaskEvents: vi.fn()
  },
  messageQueueApi: {
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    consume: vi.fn()
  },
  scheduleApi: {
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    get: vi.fn(),
    logs: vi.fn()
  },
  adminApi: {
    getSettings: vi.fn(),
    updateSettings: vi.fn()
  },
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

const makeTopicSummary = (topicId, title) => ({
  topic_id: topicId,
  title,
  chat_topic_id: `chat_${topicId}`,
  chat_conversation_id: `conversation_${topicId}`,
  current_task_id: '',
  current_task_status: '',
  message_count: 0,
  last_message_preview: '',
  created_at: '2026-03-10T02:00:00Z',
  updated_at: '2026-03-10T02:00:00Z'
})

const makeTopicDetail = (topicId, title) => ({
  topic_id: topicId,
  title,
  chat_topic_id: `chat_${topicId}`,
  chat_conversation_id: `conversation_${topicId}`,
  current_task_id: '',
  current_task_status: '',
  created_at: '2026-03-10T02:00:00Z',
  updated_at: '2026-03-10T02:00:00Z'
})

describe('NL2SqlChat', () => {
  beforeEach(() => {
    Object.values(apiMocks.topicApi).forEach((fn) => fn.mockReset())
    Object.values(apiMocks.taskApi).forEach((fn) => fn.mockReset())
    Object.values(apiMocks.messageQueueApi).forEach((fn) => fn.mockReset())
    Object.values(apiMocks.scheduleApi).forEach((fn) => fn.mockReset())
    Object.values(apiMocks.adminApi).forEach((fn) => fn.mockReset())
    apiMocks.health.mockReset()

    apiMocks.adminApi.getSettings.mockResolvedValue({
      provider_id: 'anyrouter',
      model: 'claude-opus-4-6',
      providers: [
        {
          provider_id: 'anyrouter',
          display_name: 'AnyRouter',
          models: ['claude-opus-4-6'],
          default_model: 'claude-opus-4-6',
          supports_partial_messages: true
        }
      ]
    })
    apiMocks.topicApi.createTopic.mockResolvedValue(makeTopicSummary('topic-new', '新话题'))
    apiMocks.topicApi.listTopics.mockResolvedValue([
      makeTopicSummary('topic-1', '流式话题')
    ])
    apiMocks.topicApi.getTopic.mockImplementation(async (topicId) => makeTopicDetail(topicId, topicId === 'topic-1' ? '流式话题' : '新话题'))
    apiMocks.topicApi.updateTopic.mockImplementation(async (topicId, data) => makeTopicDetail(topicId, data?.title || '新话题'))
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 1,
      items: [
        {
          message_id: 'a1',
          topic_id: 'topic-1',
          task_id: 'task-1',
          sender_type: 'assistant',
          type: 'assistant',
          status: 'running',
          content: '',
          resume_after_seq: 12,
          blocks: [
            {
              block_id: 'think-1',
              type: 'thinking',
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
          ],
          created_at: '2026-03-10T02:00:00Z'
        }
      ]
    })
    apiMocks.taskApi.streamTaskEvents.mockResolvedValue(undefined)
    apiMocks.taskApi.getTask.mockResolvedValue({
      task_id: 'task-1',
      topic_id: 'topic-1',
      task_status: 'finished'
    })
  })

  it('formats sidebar timestamps in Asia/Shanghai for backend naive datetimes', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-10T04:00:00Z'))

    apiMocks.topicApi.listTopics.mockResolvedValue([
      {
        ...makeTopicSummary('topic-1', '流式话题'),
        created_at: '2026-03-10T10:00:00',
        updated_at: '2026-03-10T10:00:00'
      }
    ])
    apiMocks.topicApi.getTopic.mockResolvedValue({
      ...makeTopicDetail('topic-1', '流式话题'),
      created_at: '2026-03-10T10:00:00',
      updated_at: '2026-03-10T10:00:00'
    })
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 0,
      items: []
    })

    try {
      const wrapper = shallowMount(NL2SqlChat)

      await flushPromises()
      await flushPromises()

      expect(wrapper.find('.query-session-meta').text()).toBe('10:00')
    } finally {
      vi.useRealTimers()
    }
  })

  it('keeps streamed main text visible while tools are still running', async () => {
    apiMocks.taskApi.streamTaskEvents.mockImplementation(() => new Promise(() => {}))
    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('问题类型：趋势分析')
    expect(wrapper.text()).toContain('workflow_publish_record')
    expect(wrapper.text()).toContain('opendataworks MySQL')
    expect(wrapper.text()).toContain('深度思考')
    expect(wrapper.find('tool-output-renderer-stub').exists()).toBe(true)
    expect(wrapper.find('.query-process-panel').exists()).toBe(true)
    expect(wrapper.find('.query-process-content').attributes('style') || '').not.toContain('display: none')
    expect(wrapper.find('.query-process-summary-preview').exists()).toBe(false)
    expect(apiMocks.taskApi.streamTaskEvents).toHaveBeenCalledWith(
      'task-1',
      expect.objectContaining({ afterSeq: 12 })
    )
  })

  it('hides empty trace placeholders and only keeps meaningful tool blocks', async () => {
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 1,
      items: [
        {
          message_id: 'a1',
          topic_id: 'topic-1',
          task_id: 'task-1',
          sender_type: 'assistant',
          type: 'assistant',
          status: 'running',
          content: '',
          resume_after_seq: 12,
          blocks: [
            {
              block_id: 'tool-empty-read',
              type: 'tool',
              status: 'streaming',
              tool_id: 'tool-empty-read',
              tool_name: 'Read'
            },
            {
              block_id: 'tool-empty-bash',
              type: 'tool',
              status: 'streaming',
              tool_id: 'tool-empty-bash',
              tool_name: 'Bash'
            },
            {
              block_id: 'tool-real-read',
              type: 'tool',
              status: 'streaming',
              tool_id: 'tool-real-read',
              tool_name: 'Read',
              input: {
                file_path: '/tmp/reference/30-tool-recipes.md'
              },
              output: '## tool recipes'
            }
          ],
          created_at: '2026-03-10T02:00:00Z'
        }
      ]
    })
    apiMocks.taskApi.streamTaskEvents.mockImplementation(() => new Promise(() => {}))

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).not.toContain('读取文件：正在读取文件')
    expect(wrapper.text()).not.toContain('执行命令：正在执行命令')
    expect(wrapper.findAll('tool-output-renderer-stub')).toHaveLength(1)
  })

  it('moves the cancel action into the composer while the active task is running', async () => {
    apiMocks.taskApi.streamTaskEvents.mockImplementation(() => new Promise(() => {}))
    apiMocks.taskApi.cancelTask.mockResolvedValue({
      task_id: 'task-1',
      task_status: 'suspended'
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.find('.query-process-cancel').exists()).toBe(false)

    const cancelButton = wrapper.find('.query-btn-cancel')
    expect(cancelButton.exists()).toBe(true)
    expect(cancelButton.attributes('aria-label')).toBe('取消当前任务')
    expect(cancelButton.text()).toContain('停止回答')

    await cancelButton.trigger('click')
    await flushPromises()

    expect(apiMocks.taskApi.cancelTask).toHaveBeenCalledWith('task-1')
  })

  it('shows a visible stop-answer button after a newly sent question enters the running state', async () => {
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 0,
      items: []
    })
    apiMocks.taskApi.deliverMessage.mockResolvedValue({
      accepted: true,
      topic_id: 'topic-1',
      task_id: 'task-new',
      task_status: 'waiting',
      user_message_id: 'u-new',
      assistant_message_id: 'a-new'
    })
    apiMocks.taskApi.streamTaskEvents.mockImplementation(() => new Promise(() => {}))

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('最近 30 天工作流发布次数趋势')
    await wrapper.find('.query-btn-send').trigger('click')
    await flushPromises()
    await flushPromises()

    const cancelButton = wrapper.find('.query-btn-cancel')
    expect(cancelButton.exists()).toBe(true)
    expect(cancelButton.text()).toContain('停止回答')
    expect(cancelButton.attributes('aria-label')).toBe('取消当前任务')
  })

  it('collapses the process panel after the final answer is ready', async () => {
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 1,
      items: [
        {
          message_id: 'a1',
          topic_id: 'topic-1',
          task_id: 'task-1',
          sender_type: 'assistant',
          type: 'assistant',
          status: 'finished',
          content: '最终结果：北区的下单量最高。',
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
          ],
          created_at: '2026-03-10T02:00:00Z'
        }
      ]
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('最终结果：北区的下单量最高。')
    expect(wrapper.find('.query-process-panel').exists()).toBe(true)
    expect(wrapper.find('.query-process-content').exists()).toBe(false)

    await wrapper.find('.query-process-summary').trigger('click')
    await flushPromises()

    expect(wrapper.find('.query-process-content').exists()).toBe(true)
  })

  it('does not inject inline chart tools into the conclusion area', async () => {
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-1',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 1,
      items: [
        {
          message_id: 'a1',
          topic_id: 'topic-1',
          task_id: 'task-1',
          sender_type: 'assistant',
          type: 'assistant',
          status: 'finished',
          content: '最近 30 天共发布 4 次。',
          blocks: [
            {
              block_id: 'main-1',
              type: 'main_text',
              status: 'success',
              text: [
                '最近 30 天共发布 4 次。',
                '<chart_spec>',
                '{"kind":"chart_spec","chart_type":"line","title":"发布趋势","x_field":"stat_day","series":[{"name":"发布次数","field":"publish_cnt","type":"line"}],"dataset":[{"stat_day":"2026-03-10","publish_cnt":3}]}',
                '</chart_spec>'
              ].join('\n')
            }
          ],
          created_at: '2026-03-10T02:00:00Z'
        }
      ]
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('最近 30 天共发布 4 次。')
    expect(wrapper.text()).not.toContain('<chart_spec>')
    expect(wrapper.text()).not.toContain('发布趋势')
    expect(wrapper.find('tool-output-renderer-stub').exists()).toBe(false)
  })

  it('allows another topic to submit while the current topic is still awaiting acceptance', async () => {
    const firstPending = deferred()
    const secondPending = deferred()

    apiMocks.topicApi.listTopics.mockResolvedValue([
      makeTopicSummary('topic-1', '话题一'),
      makeTopicSummary('topic-2', '话题二')
    ])
    apiMocks.topicApi.getTopic.mockImplementation(async (topicId) => makeTopicDetail(topicId, topicId === 'topic-1' ? '话题一' : '话题二'))
    apiMocks.topicApi.getTopicMessages.mockImplementation(async (topicId) => ({
      topic_id: topicId,
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 0,
      items: []
    }))
    apiMocks.taskApi.deliverMessage
      .mockImplementationOnce(() => firstPending.promise)
      .mockImplementationOnce(() => secondPending.promise)
    apiMocks.taskApi.getTask.mockResolvedValue({
      task_id: 'task-finished',
      topic_id: 'topic-1',
      task_status: 'finished'
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('第一个问题')
    await wrapper.find('.query-btn-send').trigger('click')
    expect(apiMocks.taskApi.deliverMessage).toHaveBeenCalledTimes(1)

    const topicButtons = wrapper.findAll('.query-session-item')
    await topicButtons[1].trigger('click')
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('第二个问题')
    await wrapper.find('.query-btn-send').trigger('click')

    expect(apiMocks.taskApi.deliverMessage).toHaveBeenCalledTimes(2)
    const requestedTopicIds = apiMocks.taskApi.deliverMessage.mock.calls.map((call) => call[0].topic_id).sort()
    expect(requestedTopicIds).toEqual(['topic-1', 'topic-2'])

    firstPending.resolve({
      accepted: true,
      topic_id: 'topic-1',
      task_id: 'task-1',
      task_status: 'waiting',
      user_message_id: 'u-1',
      assistant_message_id: 'a-1'
    })
    secondPending.resolve({
      accepted: true,
      topic_id: 'topic-2',
      task_id: 'task-2',
      task_status: 'waiting',
      user_message_id: 'u-2',
      assistant_message_id: 'a-2'
    })

    await flushPromises()
    await flushPromises()
  })

  it('persists the first real question as the title for a newly created placeholder topic', async () => {
    apiMocks.topicApi.listTopics.mockResolvedValue([])
    apiMocks.topicApi.getTopic.mockImplementation(async (topicId) => makeTopicDetail(topicId, '新话题'))
    apiMocks.topicApi.getTopicMessages.mockResolvedValue({
      topic_id: 'topic-new',
      page: 1,
      page_size: 500,
      order: 'asc',
      total: 0,
      items: []
    })
    apiMocks.taskApi.deliverMessage.mockResolvedValue({
      accepted: true,
      topic_id: 'topic-new',
      task_id: 'task-new',
      task_status: 'waiting',
      user_message_id: 'u-new',
      assistant_message_id: 'a-new'
    })

    const wrapper = shallowMount(NL2SqlChat)

    await flushPromises()
    await flushPromises()

    await wrapper.find('.query-textarea').setValue('这是一个新的会话标题')
    await wrapper.find('.query-btn-send').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(apiMocks.topicApi.updateTopic).toHaveBeenCalledWith(
      'topic-new',
      { title: '这是一个新的会话标题' }
    )
    expect(wrapper.text()).toContain('这是一个新的会话标题')
  })
})
