<template>
  <div class="query-workbench">
    <aside class="query-sidebar">
      <div class="query-sidebar-head">
          <div>
            <div class="query-brand">智能问数</div>
            <div class="query-brand-meta">数据分析</div>
          </div>
          <button class="query-btn-new" @click="handleNewTopic">新建</button>
        </div>

      <div class="query-sidebar-search">
        <input
          v-model="searchKeyword"
          class="query-search-input"
          type="text"
          placeholder="搜索话题"
        >
      </div>

      <div class="query-session-list">
        <button
          v-for="topic in filteredTopics"
          :key="topic.topic_id"
          class="query-session-item"
          :class="{ active: topic.topic_id === activeTopicId }"
          @click="handleSelectTopic(topic.topic_id)"
        >
          <div class="query-session-title">{{ truncate(topic.title, 26) }}</div>
          <div class="query-session-meta">{{ formatTime(topic.updated_at || topic.created_at) }}</div>
        </button>
        <div v-if="!filteredTopics.length" class="query-empty-sessions">暂无话题</div>
      </div>
    </aside>

    <main class="query-main">
      <div ref="messagesRef" class="query-messages" @scroll="handleScroll">
        <div class="query-messages-inner">
          <div class="query-main-head">
            <div>
              <p class="query-main-kicker">数据分析助手</p>
              <h3>{{ activeTopic ? truncate(activeTopic.title, 48) : '开始一次新的数据分析' }}</h3>
              <p class="query-main-subtitle">围绕数据查询与分析开展连续对话。</p>
            </div>
            <div class="query-model-badge">
              <span>{{ activeProviderConfig?.display_name || '未配置' }}</span>
              <strong>{{ selectedModel || settings.default_model || '默认模型' }}</strong>
            </div>
          </div>

          <div v-if="!settings.providers.length" class="query-config-empty">
            <div class="query-config-empty-title">还没有可用的智能问数模型</div>
            <div class="query-config-empty-text">请先完成模型配置。</div>
          </div>

          <div v-if="!activeMessages.length" class="query-empty">
            <div class="query-empty-mark">AI</div>
            <div class="query-empty-title">请输入你的数据问题</div>
            <div class="query-empty-subtitle">支持数据查询、趋势分析与结果可视化。</div>
            <div class="query-suggestions">
              <button
                v-for="suggestion in suggestions"
                :key="suggestion"
                class="query-suggestion"
                @click="handleSuggestion(suggestion)"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>

          <template v-for="msg in activeMessages" :key="msg.id">
            <div v-if="msg.role === 'user'" class="query-message-row query-message-user">
              <div class="query-user-bubble">{{ msg.content }}</div>
            </div>

            <div v-else class="query-message-row query-message-assistant">
              <div class="query-assistant-body">
                <div
                  v-if="hasProcessPanel(msg)"
                  class="query-process-panel"
                  :class="{ expanded: isProcessPanelExpanded(msg), complete: hasFinalResult(msg) && !isActiveTaskStatus(msg.status) }"
                >
                  <div class="query-process-summary-row">
                    <button type="button" class="query-process-summary" @click.stop="toggleProcessPanel(msg)">
                      <span class="query-process-badge">
                        <span v-if="isActiveTaskStatus(msg.status)" class="query-process-badge-dot" />
                        思考过程
                      </span>
                      <span v-if="processSummaryPreview(msg)" class="query-process-summary-preview">{{ processSummaryPreview(msg) }}</span>
                      <span class="query-process-summary-meta">{{ processSummaryMeta(msg) }}</span>
                      <span class="query-process-summary-chevron" :class="{ open: isProcessPanelExpanded(msg) }">⌄</span>
                    </button>
                    <button
                      v-if="msg.task_id && isActiveTaskStatus(msg.status)"
                      type="button"
                      class="query-process-cancel"
                      @click="cancelTask(msg)"
                    >
                      取消
                    </button>
                  </div>

                  <div v-show="isProcessPanelExpanded(msg)" class="query-process-content">
                    <div v-if="processPlaceholder(msg)" class="query-process-placeholder">
                      <span class="query-process-placeholder-text">{{ processPlaceholder(msg)?.text }}</span>
                      <span v-if="processPlaceholder(msg)?.preview" class="query-process-placeholder-preview">{{ processPlaceholder(msg)?.preview }}</span>
                      <span class="query-loading-dots">
                        <span>.</span>
                        <span>.</span>
                        <span>.</span>
                      </span>
                    </div>

                    <div v-for="block in processBlocksForMessage(msg)" :key="block.id" class="query-step-row">
                      <div v-if="block.kind === 'thinking' && block.text" class="query-process-note">
                        <div class="query-process-note-head">
                          <span class="query-process-note-badge">{{ block.status === 'streaming' ? '思考中' : '思考' }}</span>
                        </div>
                        <div class="query-process-note-text">
                          {{ block.text }}
                          <span v-if="msg.status === 'streaming' && block.status === 'streaming'" class="query-cursor">|</span>
                        </div>
                      </div>

                      <ToolOutputRenderer v-else-if="block.kind === 'tool' && block.tool" :tool="block.tool" />
                    </div>
                  </div>
                </div>

                <div v-for="block in finalBlocksForMessage(msg)" :key="block.id" class="query-step-row">
                  <template v-if="block.kind === 'main_text'">
                    <div v-if="displayTextBlock(block, msg)" class="query-main-text">
                      <div v-html="renderMarkdown(displayTextBlock(block, msg))"></div>
                      <span v-if="msg.status === 'streaming' && block.status === 'streaming'" class="query-cursor">|</span>
                    </div>

                    <div v-for="tool in inlineChartToolsForBlock(block, msg)" :key="tool.id" class="query-step-row">
                      <ToolOutputRenderer :tool="tool" />
                    </div>
                  </template>

                  <div v-else-if="block.kind === 'error' && block.text" class="query-error-card">
                    <span class="query-error-label">错误</span>
                    <span>{{ block.text }}</span>
                  </div>
                </div>

                <div v-if="msg.citations.length" class="query-citations">
                  <a
                    v-for="(citation, index) in msg.citations"
                    :key="index"
                    :href="citation.url || '#'"
                    target="_blank"
                    rel="noopener"
                    class="query-citation-chip"
                  >
                    <span class="query-citation-index">{{ index + 1 }}</span>
                    <span>{{ citation.title || citation.url || '来源' }}</span>
                  </a>
                </div>

                <div v-if="msg.error && !hasErrorBlock(msg)" class="query-error-card">
                  <span class="query-error-label">错误</span>
                  <span>{{ errorMessage(msg.error) }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="query-composer-wrap">
        <div class="query-composer">
          <div class="query-composer-top">
            <div class="query-composer-control">
              <select v-model="selectedProvider" class="query-select" :disabled="!settings.providers.length">
                <option
                  v-for="provider in settings.providers"
                  :key="provider.provider_id"
                  :value="provider.provider_id"
                >
                  {{ provider.display_name }}
                </option>
              </select>
            </div>
            <div class="query-composer-control">
              <select v-model="selectedModel" class="query-select" :disabled="!availableModels.length">
                <option v-for="model in availableModels" :key="model" :value="model">
                  {{ model }}
                </option>
              </select>
            </div>
          </div>

          <div class="query-composer-input-row">
            <textarea
              v-model="inputText"
              class="query-textarea"
              rows="2"
              :disabled="!settings.providers.length || !availableModels.length"
              placeholder="例如：查询最近 30 天工作流发布次数趋势"
              @keydown.ctrl.enter.prevent="handleSend"
              @keydown.meta.enter.prevent="handleSend"
            />
            <button class="query-btn-send" :disabled="!inputText.trim() || activeTopicSubmitting || !selectedProvider || !selectedModel" @click="handleSend">
              发送
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, triggerRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { createNl2SqlApiClient } from '@/api/nl2sql'
import ToolOutputRenderer from './ToolOutputRenderer.vue'
import { extractChartSpecsFromText, parseChartSpec, stripChartSpecsFromText } from './chartSpec'
import {
  activeStreamingBlock as activeStreamingMessageBlock,
  createAssistantMessageState,
  hydrateAssistantMessageState,
  parseMaybeJson,
  processAssistantStreamEvent
} from './messageStream'

marked.setOptions({ breaks: true, gfm: true })

const api = createNl2SqlApiClient({ timeout: 300000 })
const { topicApi, taskApi, adminApi } = api

const topics = ref([])
const activeTopicId = ref('')
const inputText = ref('')
const searchKeyword = ref('')
const messagesRef = ref(null)
const autoScroll = ref(true)
const hydratedIds = new Set()
const taskSubscriptions = new Map()
const pendingSubmitKeys = ref(new Set())

const settings = reactive({
  default_provider_id: 'openrouter',
  default_model: 'anthropic/claude-sonnet-4.5',
  providers: []
})

const selectedProvider = ref(settings.default_provider_id)
const selectedModel = ref(settings.default_model)

const suggestions = [
  '各数据层表数量对比',
  '最近 30 天工作流发布次数趋势',
  '各工作流发布操作类型占比',
  '查看 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘'
]

const activeTopic = computed(() => topics.value.find((topic) => topic.topic_id === activeTopicId.value) || null)
const activeMessages = computed(() => activeTopic.value?.messages || [])
const filteredTopics = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return topics.value
  return topics.value.filter((topic) => String(topic.title || '').toLowerCase().includes(keyword))
})

const activeProviderConfig = computed(() => {
  const list = Array.isArray(settings.providers) ? settings.providers : []
  return list.find((provider) => provider.provider_id === selectedProvider.value) || list[0] || null
})

const availableModels = computed(() => {
  const provider = activeProviderConfig.value
  const models = Array.isArray(provider?.models) ? [...provider.models] : []
  const fallbackModel = provider?.default_model || settings.default_model
  if (fallbackModel && !models.includes(fallbackModel)) {
    models.unshift(fallbackModel)
  }
  return models
})

const NEW_TOPIC_PENDING_KEY = '__new_topic__'

const normalizePendingTopicKey = (topicId) => String(topicId || NEW_TOPIC_PENDING_KEY)

const isTopicSubmitting = (topicId) => pendingSubmitKeys.value.has(normalizePendingTopicKey(topicId))

const markTopicSubmitting = (topicId) => {
  const key = normalizePendingTopicKey(topicId)
  const next = new Set(pendingSubmitKeys.value)
  next.add(key)
  pendingSubmitKeys.value = next
  return key
}

const moveTopicSubmitting = (fromTopicId, toTopicId) => {
  const fromKey = normalizePendingTopicKey(fromTopicId)
  const toKey = normalizePendingTopicKey(toTopicId)
  const next = new Set(pendingSubmitKeys.value)
  next.delete(fromKey)
  next.add(toKey)
  pendingSubmitKeys.value = next
  return toKey
}

const clearTopicSubmitting = (key) => {
  const next = new Set(pendingSubmitKeys.value)
  next.delete(String(key || ''))
  pendingSubmitKeys.value = next
}

const activeTopicSubmitting = computed(() => isTopicSubmitting(activeTopicId.value))

const truncate = (value, max) => {
  const text = String(value || '新话题')
  return text.length > max ? `${text.slice(0, max)}...` : text
}

const formatTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const uid = () => `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

const normalizeToolPayload = (value) => {
  if (value && typeof value === 'object' && !Array.isArray(value) && value.kind) {
    return value
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      if (item && typeof item === 'object' && item.kind) return item
      if (typeof item === 'string') {
        const parsed = parseMaybeJson(item)
        if (parsed?.kind) return parsed
      }
      if (item && typeof item === 'object' && typeof item.text === 'string') {
        const parsed = parseMaybeJson(item.text)
        if (parsed?.kind) return parsed
      }
    }
  }
  if (typeof value === 'string') {
    return parseMaybeJson(value)
  }
  return null
}

const cleanTextContent = (value) => {
  let text = String(value || '')
  text = text.replace(/Base directory for this skill:[\s\S]*?(?:ARGUMENTS:\s*[^\n]*\n?)/gi, '')
  text = text.replace(/^ARGUMENTS:\s*[^\n]*\n?/gm, '')
  return text.replace(/^\s+/, '')
}

const thinkingPreview = (block) => {
  const lines = String(block?.text || '')
    .split('\n')
    .map((line) => line.replace(/^[-*]\s*/, '').trim())
    .filter(Boolean)

  if (!lines.length) return ''
  const preview = lines[lines.length - 1]
  return preview.length > 38 ? `${preview.slice(0, 38)}...` : preview
}

const stripMarkdownTables = (text) => {
  const lines = String(text || '').split('\n')
  const output = []

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    const nextLine = lines[index + 1]
    const trimmed = line.trim()
    const nextTrimmed = String(nextLine || '').trim()
    const isTableHeader = trimmed.startsWith('|') && trimmed.endsWith('|')
    const isTableDivider = /^\|?[\s:-|]+\|?\s*$/.test(nextTrimmed) && nextTrimmed.includes('-')

    if (!isTableHeader || !isTableDivider) {
      output.push(line)
      continue
    }

    index += 1
    while (index + 1 < lines.length) {
      const rowLine = String(lines[index + 1] || '').trim()
      if (!rowLine.startsWith('|') || !rowLine.endsWith('|')) break
      index += 1
    }

    if (output.length && output[output.length - 1] !== '') {
      output.push('')
    }
  }

  return output.join('\n').replace(/\n{3,}/g, '\n\n').trim()
}

const renderBlocksForMessage = (msg) => (Array.isArray(msg?.renderBlocks) ? msg.renderBlocks : []).filter((block) => {
  if (!block || typeof block !== 'object') return false
  if (block.kind === 'tool') {
    const name = String(block.tool?.name || '').toLowerCase()
    if (name === 'glob' && String(block.tool?.status || '') === 'success') return false
    return true
  }
  return ['thinking', 'main_text', 'error'].includes(String(block.kind || ''))
})

const processBlocksForMessage = (msg) => renderBlocksForMessage(msg)
  .filter((block) => ['thinking', 'tool'].includes(block.kind))

const finalBlocksForMessage = (msg) => renderBlocksForMessage(msg)
  .filter((block) => ['main_text', 'error'].includes(block.kind))

const toolBlocks = (msg) => renderBlocksForMessage(msg)
  .filter((block) => block.kind === 'tool' && block.tool)
  .map((block) => block.tool)

const hasToolChart = (msg) => toolBlocks(msg).some((tool) => Boolean(parseChartSpec(normalizeToolPayload(tool.output))))

const displayTextBlock = (block, msg) => {
  let text = stripChartSpecsFromText(cleanTextContent(block?.text))
  const hasInlineCharts = extractChartSpecsFromText(cleanTextContent(block?.text)).length > 0
  if (hasToolChart(msg) || hasInlineCharts) {
    text = stripMarkdownTables(text)
  }
  if (!text) return ''
  return text
}

const inlineChartToolsForBlock = (block, msg) => {
  if (hasToolChart(msg)) return []
  return extractChartSpecsFromText(cleanTextContent(block?.text)).map((spec, index) => ({
    id: `inline_chart_${msg.id}_${block?.id || index}_${index}`,
    name: 'chart_spec',
    status: 'success',
    output: spec
  }))
}

const hasErrorBlock = (msg) => renderBlocksForMessage(msg).some((block) => block.kind === 'error' && String(block.text || '').trim())

const errorMessage = (error) => {
  if (!error) return ''
  if (typeof error === 'string') return error
  if (typeof error === 'object') return String(error.message || error.detail || '请求失败')
  return String(error)
}

const escapeHtml = (text) => String(text || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(escapeHtml(text))
  } catch (_error) {
    return escapeHtml(text)
  }
}

const sortTopics = () => {
  topics.value.sort((left, right) => new Date(right.updated_at || right.created_at || 0) - new Date(left.updated_at || left.created_at || 0))
}

const normalizeTopicSummary = (topic) => ({
  topic_id: String(topic?.topic_id || ''),
  title: String(topic?.title || '新话题'),
  message_count: Number(topic?.message_count || 0),
  current_task_id: String(topic?.current_task_id || ''),
  current_task_status: String(topic?.current_task_status || ''),
  created_at: String(topic?.created_at || new Date().toISOString()),
  updated_at: String(topic?.updated_at || new Date().toISOString()),
  messages: []
})

const makeAssistantMsg = () => reactive(createAssistantMessageState({
  id: `a_${uid()}`,
  created_at: new Date().toISOString()
}))

const syncAssistantMessage = (target, source) => {
  if (!target || !source) return
  Object.assign(target, source)
}

const toUiTaskStatus = (status) => {
  const raw = String(status || '').trim()
  if (!raw) return 'queued'
  if (raw === 'waiting') return 'queued'
  if (raw === 'finished') return 'success'
  if (raw === 'error') return 'failed'
  if (raw === 'suspended') return 'cancelled'
  return raw
}

const isActiveTaskStatus = (status) => ['queued', 'running', 'streaming'].includes(String(status || '').trim())

const parseToolInput = (value) => {
  if (value && typeof value === 'object' && !Array.isArray(value)) return value
  if (typeof value === 'string') {
    const parsed = parseMaybeJson(value)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed
    const text = value.trim()
    return text ? { command: text } : {}
  }
  return {}
}

const describeToolActivity = (tool) => {
  const input = parseToolInput(tool?.input)
  const name = String(tool?.name || '').trim()
  const lowerName = name.toLowerCase()
  const preview = String(input.description || input.summary || input.command || '').trim()

  if (['bash', 'shell', 'terminal'].includes(lowerName)) {
    return {
      text: '正在运行命令',
      preview: preview || '等待脚本输出'
    }
  }

  if (['read', 'read_file', 'readfile'].includes(lowerName)) {
    return {
      text: '正在浏览',
      preview: preview || '正在读取参考内容'
    }
  }

  if (lowerName === 'skill') {
    return {
      text: '正在加载技能',
      preview: preview || '正在准备技能上下文'
    }
  }

  return {
    text: `正在执行 ${name || '工具'}`,
    preview
  }
}

const streamingActivity = (msg) => {
  const status = String(msg?.status || '').trim()
  if (!isActiveTaskStatus(status)) return null
  if (status === 'queued') {
    return {
      kind: 'thinking',
      text: '等待执行',
      preview: ''
    }
  }
  const activeBlock = activeStreamingMessageBlock(msg)
  if (activeBlock?.kind === 'tool' && activeBlock.tool) {
    return {
      kind: 'executing',
      ...describeToolActivity(activeBlock.tool)
    }
  }
  if (activeBlock?.kind === 'main_text') {
    return {
      kind: 'thinking',
      text: '正在整理回答',
      preview: ''
    }
  }
  const latestThinking = [...renderBlocksForMessage(msg)].reverse().find((block) => block.kind === 'thinking' && String(block.text || '').trim())
  const preview = thinkingPreview(activeBlock?.kind === 'thinking' ? activeBlock : latestThinking)
  return {
    kind: 'thinking',
    text: '正在思考',
    preview
  }
}

const processPlaceholder = (msg) => {
  const hasRenderableProcessBlock = processBlocksForMessage(msg).some((block) => {
    if (block.kind === 'tool' && block.tool) return true
    return Boolean(String(block.text || '').trim())
  })
  if (hasRenderableProcessBlock) return null
  return streamingActivity(msg)
}

const hasFinalResult = (msg) => finalBlocksForMessage(msg)
  .some((block) => block.kind === 'main_text' && Boolean(displayTextBlock(block, msg)))

const hasProcessPanel = (msg) => processBlocksForMessage(msg).some((block) => {
  if (block.kind === 'tool' && block.tool) return true
  return Boolean(String(block.text || '').trim())
}) || Boolean(processPlaceholder(msg))

const processSummaryPreview = (msg) => {
  const activity = streamingActivity(msg)
  if (activity) return activity.preview || activity.text

  const latestProcessBlock = [...processBlocksForMessage(msg)].reverse().find((block) => {
    if (block.kind === 'tool' && block.tool) return true
    return Boolean(String(block.text || '').trim())
  })

  if (latestProcessBlock?.kind === 'tool' && latestProcessBlock.tool) {
    const summary = describeToolActivity(latestProcessBlock.tool)
    return summary.preview || summary.text
  }

  if (latestProcessBlock?.kind === 'thinking') {
    return thinkingPreview(latestProcessBlock)
  }

  return hasFinalResult(msg) ? '已完成' : ''
}

const processSummaryMeta = (msg) => {
  if (isActiveTaskStatus(msg?.status)) return '进行中'
  const steps = processBlocksForMessage(msg).filter((block) => {
    if (block.kind === 'tool' && block.tool) return true
    return Boolean(String(block.text || '').trim())
  }).length
  return `${steps || 1} 步`
}

const processPanelKey = (msg) => String(msg?.message_id || msg?.id || '')

const defaultProcessPanelExpanded = (msg) => isActiveTaskStatus(msg?.status) || !hasFinalResult(msg)

const isProcessPanelExpanded = (msg) => {
  if (msg?._processPanelTouched) return Boolean(msg._processPanelExpanded)
  return defaultProcessPanelExpanded(msg)
}

const toggleProcessPanel = (msg) => {
  if (!processPanelKey(msg) || !msg || typeof msg !== 'object') return
  msg._processPanelTouched = true
  msg._processPanelExpanded = !isProcessPanelExpanded(msg)
}

const processEvent = processAssistantStreamEvent

const stopTaskSubscription = (taskId) => {
  const key = String(taskId || '').trim()
  const current = taskSubscriptions.get(key)
  if (!current) return
  current.controller.abort()
  taskSubscriptions.delete(key)
}

const stopAllTaskSubscriptions = () => {
  for (const taskId of taskSubscriptions.keys()) {
    stopTaskSubscription(taskId)
  }
}

const subscribeTask = (taskId, assistantMsg) => {
  const key = String(taskId || assistantMsg?.task_id || '').trim()
  if (!key || !assistantMsg || taskSubscriptions.has(key)) return

  const controller = new AbortController()
  let afterSeq = 0

  const finalizeWithTaskState = async () => {
    try {
      const task = await taskApi.getTask(key)
      if (!task) return false
      const taskStatus = String(task.task_status || task.status || '').trim()
      if (taskStatus === 'suspended' && assistantMsg.status === 'queued') {
        processEvent(assistantMsg, {
          task_id: key,
          message_id: assistantMsg.message_id,
          record_type: 'event',
          event_type: 'AGENT_SUSPENDED',
          data: {
            status: 'suspended',
            error: { code: 'task_cancelled', message: '任务已取消' }
          }
        })
      } else if (taskStatus === 'error' && assistantMsg.status === 'queued') {
        assistantMsg.status = 'failed'
        if (task.error?.message) {
          assistantMsg.error = { message: String(task.error.message) }
        }
      } else if (taskStatus === 'finished') {
        assistantMsg.status = 'success'
      } else if (isActiveTaskStatus(taskStatus === 'waiting' ? 'queued' : taskStatus)) {
        assistantMsg.status = taskStatus === 'waiting' ? 'queued' : taskStatus
        return true
      }
      triggerRef(topics)
      scrollToBottom()
      return false
    } catch (_error) {
      return false
    }
  }

  const pump = async () => {
    try {
      while (!controller.signal.aborted) {
        try {
          await taskApi.streamTaskEvents(key, {
            afterSeq,
            signal: controller.signal,
            onEvent: (event) => {
              afterSeq = Math.max(afterSeq, Number(event?.seq_id || event?.seq || 0))
              processEvent(assistantMsg, event)
              triggerRef(topics)
              scrollToBottom()
            }
          })
          const shouldContinue = await finalizeWithTaskState()
          if (!shouldContinue) break
        } catch (error) {
          if (controller.signal.aborted) break
          const shouldContinue = await finalizeWithTaskState()
          if (!shouldContinue) break
          await new Promise((resolve) => window.setTimeout(resolve, 1500))
        }
      }
    } finally {
      taskSubscriptions.delete(key)
    }
  }

  taskSubscriptions.set(key, { controller })
  void pump()
}

const resumePendingTasks = (topic) => {
  if (!topic || !Array.isArray(topic.messages)) return
  for (const message of topic.messages) {
    if (message?.role !== 'assistant') continue
    if (!message?.task_id) continue
    if (!isActiveTaskStatus(message?.status)) continue
    subscribeTask(message.task_id, message)
  }
}

const cancelTask = async (msg) => {
  const taskId = String(msg?.task_id || '').trim()
  if (!taskId) return
  try {
    await taskApi.cancelTask(taskId)
    stopTaskSubscription(taskId)
    processEvent(msg, {
      task_id: taskId,
      message_id: msg.message_id,
      record_type: 'event',
      event_type: 'AGENT_SUSPENDED',
      data: {
        status: 'suspended',
        error: { code: 'task_cancelled', message: '任务已取消' }
      }
    })
    triggerRef(topics)
    scrollToBottom()
  } catch (error) {
    ElMessage.error(String(error?.message || '取消任务失败'))
  }
}

const loadSettings = async () => {
  try {
    const payload = await adminApi.getSettings()
    settings.default_provider_id = payload?.provider_id || payload?.default_provider_id || settings.default_provider_id
    settings.default_model = payload?.model || payload?.default_model || settings.default_model
    settings.providers = Array.isArray(payload?.providers) ? payload.providers : []
    selectedProvider.value = settings.default_provider_id || settings.providers[0]?.provider_id || ''
    const provider = settings.providers.find((item) => item.provider_id === selectedProvider.value)
    selectedModel.value = provider?.default_model || settings.default_model || ''
  } catch (error) {
    console.warn('load settings failed', error)
  }
}

const hydrateTopic = async (topicId) => {
  if (!topicId || hydratedIds.has(topicId)) return

  try {
    const [detail, messagePage] = await Promise.all([
      topicApi.getTopic(topicId),
      topicApi.getTopicMessages(topicId, { page: 1, page_size: 500, order: 'asc' })
    ])
    const target = topics.value.find((topic) => topic.topic_id === topicId)
    if (target && detail) {
      target.title = String(detail.title || target.title)
      target.updated_at = String(detail.updated_at || target.updated_at)
      target.current_task_id = String(detail.current_task_id || target.current_task_id || '')
      target.current_task_status = String(detail.current_task_status || target.current_task_status || '')
      const rawMessages = Array.isArray(messagePage?.items) ? messagePage.items : []
      target.messages = rawMessages.map((message) => {
        if (!message) return null
        const senderType = String(message.sender_type || message.role || 'assistant')
        if (senderType === 'user') {
          return {
            id: String(message.message_id || uid()),
            role: 'user',
            content: String(message.content || ''),
            created_at: message.created_at
          }
        }

        return reactive(hydrateAssistantMessageState(message))
      }).filter(Boolean)
      target.message_count = Number(messagePage?.total || target.messages.length)
      resumePendingTasks(target)
    }

    hydratedIds.add(topicId)
  } catch (error) {
    console.warn('hydrate topic failed', error)
  }
}

const loadTopics = async () => {
  try {
    const list = await topicApi.listTopics()
    topics.value = (Array.isArray(list) ? list : []).map(normalizeTopicSummary)
    sortTopics()
    if (!activeTopicId.value && topics.value.length) {
      activeTopicId.value = topics.value[0].topic_id
    }
    if (activeTopicId.value) {
      await hydrateTopic(activeTopicId.value)
    }
  } catch (error) {
    console.warn('load topics failed', error)
  }
}

const handleNewTopic = async () => {
  const topic = normalizeTopicSummary(await topicApi.createTopic())
  topics.value.unshift(topic)
  hydratedIds.add(topic.topic_id)
  activeTopicId.value = topic.topic_id
  autoScroll.value = true
  scrollToBottom(true)
}

const handleSelectTopic = async (topicId) => {
  activeTopicId.value = topicId
  await hydrateTopic(topicId)
  autoScroll.value = true
  scrollToBottom(true)
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || isTopicSubmitting(activeTopicId.value) || !selectedProvider.value || !selectedModel.value) return

  inputText.value = ''
  autoScroll.value = true
  scrollToBottom(true)

  let topic = null
  let assistantMsg = null
  let submitTopicId = activeTopicId.value
  let pendingKey = markTopicSubmitting(submitTopicId)

  try {
    if (!activeTopicId.value) {
      const title = text.length > 20 ? `${text.slice(0, 20)}...` : text
      const created = normalizeTopicSummary(await topicApi.createTopic(title))
      topics.value.unshift(created)
      hydratedIds.add(created.topic_id)
      activeTopicId.value = created.topic_id
      submitTopicId = created.topic_id
      pendingKey = moveTopicSubmitting('', submitTopicId)
    }

    submitTopicId = activeTopicId.value
    await hydrateTopic(submitTopicId)

    topic = topics.value.find((item) => item.topic_id === submitTopicId) || null
    if (!topic) {
      throw new Error('话题初始化失败')
    }

    if (!Array.isArray(topic.messages)) {
      topic.messages = []
    }

    topic.messages.push({
      id: `u_${uid()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    })

    assistantMsg = makeAssistantMsg()
    assistantMsg.status = 'queued'
    topic.messages.push(assistantMsg)
    scrollToBottom(true)

    const response = await taskApi.deliverMessage({
      topic_id: submitTopicId,
      content: text,
      provider_id: selectedProvider.value,
      model: selectedModel.value,
      debug: true,
      execution_mode: 'auto'
    })

    assistantMsg.message_id = String(response?.assistant_message_id || assistantMsg.message_id || '')
    assistantMsg.task_id = String(response?.task_id || assistantMsg.task_id || '')
    assistantMsg.status = toUiTaskStatus(response?.task_status)
    topic.current_task_id = assistantMsg.task_id
    topic.current_task_status = String(response?.task_status || topic.current_task_status || '')
    if (assistantMsg.task_id) {
      subscribeTask(assistantMsg.task_id, assistantMsg)
    }

    topic.updated_at = new Date().toISOString()
    topic.message_count = topic.messages.length
    if (topic.title === '新话题') {
      topic.title = text.length > 30 ? `${text.slice(0, 30)}...` : text
    }
    sortTopics()
    triggerRef(topics)
    scrollToBottom(true)
  } catch (error) {
    const message = String(error?.message || '请求失败')
    if (assistantMsg) {
      assistantMsg.status = 'failed'
      assistantMsg.error = message
    } else {
      ElMessage.error(message)
    }
  } finally {
    clearTopicSubmitting(pendingKey)
  }
}

const handleSuggestion = (value) => {
  inputText.value = value
  void handleSend()
}

const isNearBottom = () => {
  const element = messagesRef.value
  if (!element) return true
  return element.scrollHeight - element.scrollTop - element.clientHeight < 60
}

const handleScroll = () => {
  autoScroll.value = isNearBottom()
}

const scrollToBottom = (force = false) => {
  if (!force && !autoScroll.value) return
  nextTick(() => {
    const element = messagesRef.value
    if (element) element.scrollTop = element.scrollHeight
  })
}

watch(
  () => [selectedProvider.value, availableModels.value.join('|')],
  () => {
    if (!availableModels.value.includes(selectedModel.value)) {
      selectedModel.value = availableModels.value[0] || settings.default_model || ''
    }
  }
)

onMounted(async () => {
  await loadSettings()
  await loadTopics()
  scrollToBottom(true)
})

onBeforeUnmount(() => {
  stopAllTaskSubscriptions()
})
</script>

<style scoped>
.query-workbench {
  --sidebar-bg: linear-gradient(180deg, #243961 0%, #2d4a79 100%);
  --sidebar-border: rgba(255, 255, 255, 0.08);
  --sidebar-text: rgba(241, 246, 255, 0.94);
  --sidebar-text-muted: rgba(205, 217, 238, 0.72);
  --surface: #fbfcfe;
  --surface-muted: #f4f7fd;
  --surface-soft: #eef2fb;
  --line: #d8e1f1;
  --line-soft: #e7edf8;
  --text: #162131;
  --text-muted: #5f7087;
  --text-soft: #899bb1;
  --accent: #667eea;
  --accent-soft: rgba(102, 126, 234, 0.12);
  --primary: #409eff;
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(240px, 280px) 1fr;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 28px;
  overflow: hidden;
  background: var(--surface);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.08);
}

.query-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 18px 14px 16px;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
}

.query-sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 6px 14px;
}

.query-brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.query-brand-meta {
  margin-top: 4px;
  font-size: 12px;
  color: var(--sidebar-text-muted);
}

.query-btn-new {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #409eff;
  border-radius: 999px;
  background: #409eff;
  color: #f8fbff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
  box-shadow: 0 8px 18px rgba(64, 158, 255, 0.2);
}

.query-btn-new:hover {
  background: #66b1ff;
  transform: translateY(-1px);
}

.query-sidebar-search {
  padding: 0 6px 14px;
}

.query-search-input {
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--sidebar-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--sidebar-text);
  outline: none;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.query-search-input::placeholder {
  color: rgba(201, 214, 229, 0.6);
}

.query-search-input:focus {
  border-color: rgba(102, 126, 234, 0.45);
  background: rgba(255, 255, 255, 0.12);
}

.query-session-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 6px;
}

.query-session-item {
  width: 100%;
  margin-bottom: 8px;
  padding: 12px 12px 11px;
  border: 1px solid transparent;
  border-radius: 16px;
  background: transparent;
  color: var(--sidebar-text);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.query-session-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

.query-session-item.active {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.14);
}

.query-session-title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.query-session-meta {
  margin-top: 4px;
  font-size: 11px;
  color: var(--sidebar-text-muted);
}

.query-empty-sessions {
  padding: 30px 8px;
  color: var(--sidebar-text-muted);
  font-size: 13px;
  text-align: center;
}

.query-main {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at top right, rgba(102, 126, 234, 0.08), transparent 24%),
    linear-gradient(180deg, #fbfcfe 0%, #f5f7fc 100%);
}

.query-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.query-messages-inner {
  max-width: 980px;
  margin: 0 auto;
  padding: 28px 26px 36px;
}

.query-main-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 20px;
  margin-bottom: 18px;
  border-bottom: 1px dashed var(--line);
}

.query-main-kicker {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.query-main-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 28px;
  font-weight: 700;
}

.query-main-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 14px;
}

.query-model-badge {
  min-width: 220px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.query-model-badge span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.query-model-badge strong {
  display: block;
  margin-top: 8px;
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
}

.query-model-badge-note {
  display: block;
  margin-top: 8px;
  color: var(--text-soft);
  font-size: 12px;
  font-style: normal;
  line-height: 1.5;
}

.query-config-empty {
  margin-top: 18px;
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px dashed rgba(245, 158, 11, 0.45);
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.92) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.query-config-empty-title {
  font-size: 15px;
  font-weight: 700;
  color: #9a3412;
}

.query-config-empty-text {
  margin-top: 6px;
  font-size: 13px;
  color: #b45309;
}

.query-empty {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.query-empty-mark {
  width: 78px;
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: linear-gradient(135deg, #667eea 0%, #5369d6 100%);
  color: #f8fbff;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.08em;
  box-shadow: 0 16px 32px rgba(102, 126, 234, 0.22);
}

.query-empty-title {
  margin-top: 18px;
  color: var(--text);
  font-size: 24px;
  font-weight: 700;
}

.query-empty-subtitle {
  margin-top: 10px;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.8;
}

.query-suggestions {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.query-suggestion {
  height: 38px;
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease;
}

.query-suggestion:hover {
  border-color: rgba(102, 126, 234, 0.35);
  background: #ffffff;
  transform: translateY(-1px);
}

.query-message-row {
  margin-bottom: 24px;
  display: flex;
}

.query-message-user {
  justify-content: flex-end;
}

.query-user-bubble {
  max-width: 72%;
  padding: 13px 16px;
  border-radius: 20px 20px 6px 20px;
  background: linear-gradient(135deg, #667eea 0%, #5369d6 100%);
  color: #f8fbff;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  box-shadow: 0 14px 28px rgba(102, 126, 234, 0.18);
}

.query-message-assistant {
  justify-content: flex-start;
}

.query-assistant-body {
  width: 100%;
  max-width: 100%;
}

.query-step-row {
  margin-bottom: 8px;
}

.query-process-panel {
  margin-bottom: 14px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(246, 249, 253, 0.92);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.query-process-panel.complete {
  background: rgba(248, 250, 254, 0.94);
}

.query-process-summary-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
}

.query-process-summary {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-muted);
  text-align: left;
  cursor: pointer;
}

.query-process-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 74px;
  height: 28px;
  padding: 0 11px;
  border-radius: 999px;
  background: rgba(102, 126, 234, 0.1);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.query-process-badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.12);
  animation: query-process-pulse 1.4s ease-in-out infinite;
}

.query-process-summary-preview {
  flex: 1;
  min-width: 0;
  color: var(--text-soft);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.query-process-summary-meta {
  color: var(--text-soft);
  font-size: 12px;
  white-space: nowrap;
}

.query-process-summary-chevron {
  color: var(--text-soft);
  font-size: 15px;
  transition: transform 0.18s ease;
}

.query-process-summary-chevron.open {
  transform: rotate(180deg);
}

.query-process-cancel {
  flex-shrink: 0;
  height: 28px;
  padding: 0 12px;
  border: 1px solid rgba(96, 113, 133, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
}

.query-process-cancel:hover {
  border-color: rgba(96, 113, 133, 0.38);
  color: var(--text);
}

.query-process-content {
  padding: 0 12px 12px;
  border-top: 1px solid var(--line-soft);
}

.query-process-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 4px 6px;
}

.query-process-placeholder-text {
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
}

.query-process-placeholder-preview {
  min-width: 0;
  color: var(--text-soft);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.query-process-note {
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.03);
}

.query-process-note-head {
  display: flex;
  align-items: center;
}

.query-process-note-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
}

.query-process-note-text {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.75;
  white-space: pre-wrap;
}

.query-main-text {
  color: var(--text);
  font-size: 14.5px;
  line-height: 1.8;
}

.query-main-text :deep(p) {
  margin: 0 0 12px;
}

.query-main-text :deep(p:last-child) {
  margin-bottom: 0;
}

.query-main-text :deep(strong) {
  color: var(--text);
  font-weight: 700;
}

.query-main-text :deep(ul),
.query-main-text :deep(ol) {
  margin: 8px 0 12px 20px;
  padding: 0;
}

.query-main-text :deep(li) {
  margin-bottom: 4px;
}

.query-main-text :deep(code) {
  padding: 2px 6px;
  border-radius: 6px;
  background: #edf2ff;
  color: #425cc8;
  font-size: 13px;
}

.query-main-text :deep(pre) {
  margin: 12px 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: #1c2647;
  color: #e6ebff;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.65;
}

.query-main-text :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
  font-size: inherit;
}

.query-main-text :deep(blockquote) {
  margin: 10px 0;
  padding: 8px 14px;
  border-left: 3px solid var(--accent);
  background: rgba(102, 126, 234, 0.06);
  color: var(--text-muted);
}

.query-main-text :deep(a) {
  color: var(--accent);
  text-decoration: none;
}

.query-main-text :deep(a:hover) {
  text-decoration: underline;
}

.query-main-text :deep(table) {
  width: 100%;
  margin: 12px 0;
  border-collapse: collapse;
  font-size: 13px;
}

.query-main-text :deep(th),
.query-main-text :deep(td) {
  padding: 8px 10px;
  border: 1px solid var(--line-soft);
  text-align: left;
}

.query-main-text :deep(th) {
  background: #f3f8fc;
  font-weight: 700;
}

.query-cursor {
  color: var(--accent);
  animation: query-cursor-blink 1s ease-in-out infinite;
}

.query-citations {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.query-citation-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 11px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--text-muted);
  font-size: 12px;
  text-decoration: none;
  transition: border-color 0.18s ease, color 0.18s ease;
}

.query-citation-chip:hover {
  border-color: rgba(102, 126, 234, 0.35);
  color: var(--accent);
}

.query-citation-index {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--text);
  font-size: 11px;
  font-weight: 700;
}

.query-sql-card,
.query-exec-card {
  margin-top: 14px;
  border: 1px solid var(--line);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
}

.query-sql-header,
.query-exec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line-soft);
}

.query-sql-header span,
.query-exec-head span:first-child {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.query-sql-actions {
  display: flex;
  gap: 8px;
}

.query-btn-sm {
  height: 28px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #ffffff;
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.query-btn-sm:hover {
  border-color: rgba(102, 126, 234, 0.28);
  background: #f7f9ff;
}

.query-btn-primary {
  border-color: rgba(102, 126, 234, 0.35);
  color: var(--accent);
}

.query-sql-code {
  margin: 0;
  padding: 15px 16px;
  background: #1c2647;
  color: #e6ebff;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.65;
}

.query-exec-meta {
  color: var(--text-soft);
  font-size: 12px;
}

.query-exec-error {
  padding: 14px;
  color: #b42318;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.query-table-wrap {
  overflow-x: auto;
}

.query-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.query-table th,
.query-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line-soft);
  text-align: left;
  white-space: nowrap;
}

.query-table th {
  background: #f4f7ff;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.query-exec-empty {
  padding: 14px;
  color: var(--text-soft);
  font-size: 13px;
}

.query-error-card {
  margin-top: 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid rgba(244, 114, 94, 0.25);
  border-radius: 16px;
  background: #fff6f3;
  color: #a2391c;
  font-size: 13px;
  line-height: 1.65;
}

.query-error-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(244, 114, 94, 0.12);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.query-message-meta {
  margin-top: 8px;
  display: flex;
  width: 100%;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  color: rgba(96, 113, 133, 0.74);
  font-size: 11px;
  line-height: 1.4;
}

.query-message-meta-total {
  color: rgba(96, 113, 133, 0.82);
  font-weight: 400;
}

.query-message-meta-arrow,
.query-message-meta-cache {
  display: inline-flex;
  align-items: center;
  color: rgba(120, 132, 145, 0.76);
}

.query-message-meta-arrow {
  gap: 2px;
}

.query-message-meta-arrow.is-up,
.query-message-meta-arrow.is-down {
  font-variant-numeric: tabular-nums;
}

.query-message-meta-cache {
  margin-left: 1px;
  color: rgba(140, 152, 166, 0.72);
}

.query-loading-dots {
  display: inline-flex;
}

.query-loading-dots span {
  color: var(--text-muted);
  font-size: 14px;
  animation: query-dot 1.4s ease-in-out infinite;
}

.query-loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.query-loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

.query-composer-wrap {
  flex-shrink: 0;
  padding: 12px 22px 22px;
}

.query-composer {
  max-width: 980px;
  margin: 0 auto;
  border: 1px solid var(--line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.query-composer-top {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 14px 0;
}

.query-composer-control {
  display: flex;
  align-items: center;
}

.query-select {
  min-width: 180px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text);
  font-size: 12px;
  outline: none;
}

.query-composer-input-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 8px 14px 14px;
}

.query-textarea {
  flex: 1;
  min-height: 46px;
  max-height: 140px;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  color: var(--text);
  font-size: 14px;
  line-height: 1.75;
  font-family: inherit;
}

.query-textarea::placeholder {
  color: var(--text-soft);
}

.query-btn-send {
  min-width: 84px;
  height: 42px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  background: #409eff;
  color: #f8fbff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.18s ease, transform 0.18s ease, background-color 0.18s ease;
  box-shadow: 0 10px 22px rgba(64, 158, 255, 0.22);
}

.query-btn-send:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.query-btn-send:not(:disabled):hover {
  background: #66b1ff;
  transform: translateY(-1px);
}

@keyframes query-cursor-blink {
  0% {
    opacity: 0.25;
  }

  50% {
    opacity: 1;
  }

  100% {
    opacity: 0.25;
  }
}

@keyframes query-dot {
  0%,
  20% {
    opacity: 0.2;
  }

  50% {
    opacity: 1;
  }

  80%,
  100% {
    opacity: 0.2;
  }
}

@keyframes query-process-pulse {
  0%,
  100% {
    transform: scale(0.9);
    opacity: 0.8;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 1024px) {
  .query-main-head {
    flex-direction: column;
  }

  .query-model-badge {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 960px) {
  .query-workbench {
    grid-template-columns: 1fr;
  }

  .query-sidebar {
    display: none;
  }

  .query-messages-inner,
  .query-composer {
    max-width: 100%;
  }

  .query-user-bubble {
    max-width: 88%;
  }
}

@media (max-width: 768px) {
  .query-workbench {
    border-radius: 22px;
  }

  .query-messages-inner {
    padding: 20px 16px 24px;
  }

  .query-main-head h3 {
    font-size: 24px;
  }

  .query-composer-wrap {
    padding: 10px 12px 14px;
  }

  .query-composer-input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .query-btn-send {
    width: 100%;
  }
}
</style>
