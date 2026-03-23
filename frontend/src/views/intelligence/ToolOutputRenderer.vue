<template>
  <div class="tool-output" :class="{ failed: hasError, 'tool-output-shell': showTrace }">
    <div v-if="showTrace" class="shell-trace">
      <button
        v-if="traceHasPanel"
        type="button"
        class="shell-trace-summary"
        @click="shellOpen = !shellOpen"
      >
        <span class="shell-trace-summary-text">
          {{ traceSummaryText }}
        </span>
        <span class="shell-trace-summary-status" :class="`is-${traceStatusTone}`">
          {{ statusLabel }}
        </span>
        <span class="shell-trace-summary-chevron" :class="{ open: shellOpen }">⌄</span>
      </button>

      <div v-else class="shell-trace-summary shell-trace-summary-static">
        <span class="shell-trace-summary-text">
          {{ traceSummaryText }}
        </span>
        <span class="shell-trace-summary-status" :class="`is-${traceStatusTone}`">
          {{ statusLabel }}
        </span>
      </div>

      <div v-if="traceHasPanel && shellOpen" class="shell-trace-panel">
        <div class="shell-trace-panel-title">{{ traceTitle }}</div>
        <pre v-if="traceCommand" class="shell-trace-command"><code>{{ traceCommandPrefix }}{{ traceCommand }}</code></pre>
        <div v-if="traceDescription && traceDescription !== traceCommand" class="shell-trace-description">
          {{ traceDescription }}
        </div>
        <template v-if="traceOutputText">
          <div v-if="showTraceMarkdown" class="tool-markdown">
            <div class="tool-markdown-body" v-html="traceMarkdownExpanded ? renderedTraceMarkdown : renderedTraceMarkdownPreview" />
            <button
              v-if="traceMarkdownCollapsible"
              type="button"
              class="tool-markdown-toggle"
              @click="traceMarkdownExpanded = !traceMarkdownExpanded"
            >
              {{ traceMarkdownExpanded ? '收起' : '展开...' }}
            </button>
          </div>
          <pre v-else class="shell-trace-output"><code>{{ traceOutputText }}</code></pre>
        </template>
        <div v-else class="shell-trace-empty">无输出</div>
        <div class="shell-trace-footer">
          <span class="shell-trace-footer-label">状态</span>
          <span class="shell-trace-footer-value" :class="`is-${traceStatusTone}`">{{ statusLabel }}</span>
        </div>
      </div>
    </div>

    <div v-if="showMainHeader" class="tool-output-head">
      <div>
        <div class="tool-output-label">{{ displayLabel }}</div>
        <div class="tool-output-meta">
          <span>{{ statusLabel }}</span>
          <span v-if="toolName">· {{ toolName }}</span>
          <span v-if="kind === 'sql_execution' && rowCountText">· {{ rowCountText }}</span>
          <span v-if="kind === 'sql_execution' && durationText">· {{ durationText }}</span>
        </div>
      </div>
      <div v-if="scriptName" class="tool-output-chip">{{ scriptName }}</div>
    </div>

    <div v-if="summaryText && showMainHeader" class="tool-output-summary">{{ summaryText }}</div>

    <div v-if="errorText && showMainHeader" class="tool-output-error">{{ errorText }}</div>

    <template v-if="kind === 'sql_execution'">
      <pre v-if="sqlText" class="tool-code"><code>{{ sqlText }}</code></pre>

      <div v-if="columns.length && rows.length" class="tool-table-wrap">
        <table class="tool-table">
          <thead>
            <tr>
              <th v-for="column in columns" :key="column">{{ column }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in rows" :key="rowIndex">
              <td v-for="column in columns" :key="column">{{ row[column] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!errorText" class="tool-output-empty">无数据</div>
    </template>

    <template v-else-if="kind === 'chart_spec'">
      <div v-if="chartRenderState === 'invalid'" class="tool-output-error">{{ chartRenderError }}</div>
      <div v-else-if="chartRenderState === 'error' && !errorText" class="tool-output-error">{{ chartRenderError }}</div>

      <div v-if="chartRenderState === 'renderable' && chartRenderKind === 'table'" class="tool-table-wrap">
        <table class="tool-table">
          <thead>
            <tr>
              <th v-for="column in chartColumns" :key="column">{{ column }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in chartRows" :key="rowIndex">
              <td v-for="column in chartColumns" :key="column">{{ row[column] }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-else-if="chartRenderState === 'renderable' && chartOption"
        ref="chartCanvasRef"
        class="tool-chart"
      />
      <div v-else-if="chartRenderState === 'empty'" class="tool-output-empty">图表暂无可渲染数据</div>
      <div v-else-if="chartRenderState !== 'invalid' && chartRenderState !== 'error'" class="tool-output-empty">图表数据为空</div>

      <pre v-if="showChartRawText" class="tool-code tool-code-light"><code>{{ rawText }}</code></pre>
    </template>

    <template v-else-if="kind === 'python_execution'">
      <pre v-if="stdoutText" class="tool-code"><code>{{ stdoutText }}</code></pre>
      <pre v-if="resultText" class="tool-code tool-code-light"><code>{{ resultText }}</code></pre>
    </template>

    <pre v-else-if="showRawPayload" class="tool-code tool-code-light"><code>{{ rawText }}</code></pre>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { marked } from 'marked'
import * as echarts from 'echarts/core'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { buildChartRenderModel, parseChartSpec, parseMaybeJson } from './chartSpec'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

const props = defineProps({
  tool: {
    type: Object,
    default: () => ({})
  }
})

const chartCanvasRef = ref(null)
const shellOpen = ref(false)
const nowTick = ref(Date.now())
const traceMarkdownExpanded = ref(false)

const isPlainObject = (value) => value && typeof value === 'object' && !Array.isArray(value)

const MARKDOWN_PREVIEW_LINES = 5

const escapeHtml = (text) => String(text || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')

const TOOL_LINE_PREFIX_PATTERN = /^\s*\d+\s*(?:→|->)\s?/

const stripToolLinePrefixes = (text) => {
  const value = String(text || '')
  if (!value.trim()) return ''

  const lines = value.split('\n')
  const nonEmptyLines = lines.filter((line) => line.trim().length > 0)
  if (!nonEmptyLines.length) return value

  const prefixedCount = nonEmptyLines.filter((line) => TOOL_LINE_PREFIX_PATTERN.test(line)).length
  const shouldStrip = prefixedCount >= 2 || prefixedCount === nonEmptyLines.length
  if (!shouldStrip) return value

  return lines.map((line) => line.replace(TOOL_LINE_PREFIX_PATTERN, '')).join('\n')
}

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(escapeHtml(text), { breaks: true, gfm: true })
  } catch (_error) {
    return escapeHtml(text)
  }
}

const looksLikeMarkdown = (text) => {
  const value = String(text || '').trim()
  if (!value) return false
  return /^#{1,6}\s/m.test(value)
    || /^>\s/m.test(value)
    || /^[-*+]\s/m.test(value)
    || /^\d+\.\s/m.test(value)
    || /```/.test(value)
    || /\[[^\]]+\]\([^)]+\)/.test(value)
}

const extractTextParts = (value) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map((item) => {
      if (typeof item === 'string') return item
      if (isPlainObject(item)) {
        if (typeof item.text === 'string') return item.text
        if (typeof item.content === 'string') return item.content
      }
      return ''
    }).filter(Boolean).join('\n')
  }
  if (isPlainObject(value)) {
    if (typeof value.text === 'string') return value.text
    if (typeof value.content === 'string') return value.content
    if (typeof value.stdout === 'string') return value.stdout
    if (typeof value.result === 'string') return value.result
  }
  return ''
}

const normalizeOutput = (value) => {
  const normalizedChart = parseChartSpec(value)
  if (normalizedChart) return normalizedChart
  if (isPlainObject(value) && value.kind) return value
  if (Array.isArray(value)) {
    for (const item of value) {
      const normalizedItemChart = parseChartSpec(item)
      if (normalizedItemChart) return normalizedItemChart
      if (isPlainObject(item) && item.kind) return item
      const text = extractTextParts(item)
      const parsed = parseMaybeJson(text)
      const normalizedParsedChart = parseChartSpec(parsed)
      if (normalizedParsedChart) return normalizedParsedChart
      if (isPlainObject(parsed) && parsed.kind) return parsed
    }
  }

  const text = extractTextParts(value)
  const parsed = parseMaybeJson(text)
  const normalizedParsedChart = parseChartSpec(parsed)
  if (normalizedParsedChart) return normalizedParsedChart
  if (isPlainObject(parsed) && parsed.kind) return parsed
  return null
}

const prettyPrint = (value) => {
  if (!value && value !== 0) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch (_error) {
    return String(value)
  }
}

const outputPayload = computed(() => normalizeOutput(props.tool?.output) || {})
const kind = computed(() => String(outputPayload.value.kind || 'raw'))
const toolName = computed(() => String(props.tool?.name || '').trim())
const toolNameLower = computed(() => toolName.value.toLowerCase())
const scriptName = computed(() => String(outputPayload.value.script || '').trim())
const summaryText = computed(() => String(outputPayload.value.summary || outputPayload.value.description || '').trim())
const sqlText = computed(() => String(outputPayload.value.sql || '').trim())
const rows = computed(() => Array.isArray(outputPayload.value.rows) ? outputPayload.value.rows : [])
const columns = computed(() => {
  if (Array.isArray(outputPayload.value.columns) && outputPayload.value.columns.length) {
    return outputPayload.value.columns
  }
  const firstRow = rows.value[0]
  return isPlainObject(firstRow) ? Object.keys(firstRow) : []
})
const stdoutText = computed(() => String(outputPayload.value.stdout || '').trim())
const resultText = computed(() => prettyPrint(outputPayload.value.result))
const rawText = computed(() => {
  const source = outputPayload.value.kind ? outputPayload.value : props.tool?.output
  return prettyPrint(source)
})
const errorText = computed(() => String(outputPayload.value.error || '').trim())
const hasError = computed(() => Boolean(errorText.value) || String(props.tool?.status || '') === 'failed')
const rowCountText = computed(() => {
  const value = Number(outputPayload.value.row_count)
  return Number.isFinite(value) && value > 0 ? `${value} 行` : ''
})
const durationText = computed(() => {
  const value = Number(outputPayload.value.duration_ms)
  return Number.isFinite(value) && value >= 0 ? `${value} ms` : ''
})

const displayLabel = computed(() => {
  if (outputPayload.value.tool_label) return String(outputPayload.value.tool_label)
  if (kind.value === 'sql_execution') return 'SQL 执行'
  if (kind.value === 'python_execution') return 'Python 执行'
  if (kind.value === 'chart_spec') return '图表渲染'
  return toolName.value || '工具输出'
})

const parsedInput = computed(() => {
  const input = props.tool?.input
  if (isPlainObject(input)) return input
  if (typeof input === 'string') {
    const parsed = parseMaybeJson(input)
    if (isPlainObject(parsed)) return parsed
    const text = input.trim()
    return text ? { command: text } : {}
  }
  return {}
})

const shellCommand = computed(() => {
  const payload = parsedInput.value
  return String(payload.command || payload.cmd || '').trim()
})

const readPath = computed(() => {
  const payload = parsedInput.value
  return String(payload.file_path || payload.path || '').trim()
})

const shellDescription = computed(() => {
  const payload = parsedInput.value
  return String(payload.description || payload.summary || '').trim()
})

const traceKind = computed(() => {
  if (['bash', 'shell', 'terminal'].includes(toolNameLower.value)) return 'shell'
  if (['read', 'read_file', 'readfile'].includes(toolNameLower.value)) return 'read'
  if (['skill', 'launch_skill'].includes(toolNameLower.value)) return 'skill'
  return ''
})

const showTrace = computed(() => Boolean(traceKind.value))
const traceHasPanel = computed(() => traceKind.value !== 'read')
const showMainHeader = computed(() => {
  if (!showTrace.value) return true
  if (kind.value === 'chart_spec') return false
  return ['sql_execution', 'python_execution'].includes(kind.value)
})

const traceOutputText = computed(() => {
  const directText = extractTextParts(props.tool?.output).trim()
  if (directText) return stripToolLinePrefixes(directText).trim()
  return stripToolLinePrefixes(rawText.value).trim()
})
const traceOutputLines = computed(() => String(traceOutputText.value || '').split('\n'))
const traceMarkdownSource = computed(() => String(traceOutputText.value || '').trim())
const showTraceMarkdown = computed(() => {
  if (!traceOutputText.value) return false
  if (traceKind.value === 'skill') return looksLikeMarkdown(traceMarkdownSource.value)
  const path = traceCommand.value || readPath.value
  if (/\.(md|markdown)$/i.test(String(path || '').trim())) {
    return looksLikeMarkdown(traceMarkdownSource.value) || Boolean(traceMarkdownSource.value)
  }
  return false
})
const traceMarkdownCollapsible = computed(() => showTraceMarkdown.value && traceOutputLines.value.length > MARKDOWN_PREVIEW_LINES)
const traceMarkdownPreview = computed(() => {
  if (!traceMarkdownCollapsible.value) return traceMarkdownSource.value
  return traceOutputLines.value.slice(0, MARKDOWN_PREVIEW_LINES).join('\n')
})
const renderedTraceMarkdown = computed(() => renderMarkdown(traceMarkdownSource.value))
const renderedTraceMarkdownPreview = computed(() => renderMarkdown(traceMarkdownPreview.value))

const traceTitle = computed(() => {
  if (traceKind.value === 'read') return 'Read'
  if (traceKind.value === 'skill') return 'Skill'
  return 'Shell'
})

const traceCommand = computed(() => {
  if (traceKind.value === 'shell') return shellCommand.value
  if (traceKind.value === 'read') return readPath.value
  if (traceKind.value === 'skill') return shellCommand.value || readPath.value
  return ''
})

const traceCommandPrefix = computed(() => (traceKind.value === 'shell' ? '$ ' : ''))

const traceDescription = computed(() => {
  if (traceKind.value === 'read') return shellDescription.value || '正在读取参考内容'
  if (traceKind.value === 'skill') return shellDescription.value || '正在准备技能上下文'
  return shellDescription.value
})

const traceSummaryText = computed(() => {
  if (traceKind.value === 'read') {
    return traceCommand.value || traceDescription.value || '读取参考内容'
  }
  if (traceKind.value === 'skill') {
    return traceDescription.value || traceCommand.value || '加载技能'
  }
  const leading = traceDescription.value || traceCommand.value || displayLabel.value
  return leading || 'Shell 执行'
})

const traceStatusTone = computed(() => {
  const status = String(props.tool?.status || 'success')
  const callComplete = Boolean(props.tool?._callComplete)
  const runtimeStarted = Boolean(props.tool?._runtimeStarted)
  if (status === 'failed') return 'failed'
  if (!callComplete) return 'running'
  if (callComplete && !runtimeStarted) return 'success'
  if (status === 'pending' || status === 'streaming') return 'running'
  return 'success'
})

const toolStartedAt = computed(() => Number(props.tool?._startedAt || 0))
const elapsedSeconds = computed(() => {
  if (!toolStartedAt.value) return 0
  return Math.max(0, Math.floor((nowTick.value - toolStartedAt.value) / 1000))
})

const statusLabel = computed(() => {
  const status = String(props.tool?.status || 'success')
  const callComplete = Boolean(props.tool?._callComplete)
  const runtimeStarted = Boolean(props.tool?._runtimeStarted)
  if (traceKind.value === 'shell') {
    if (!callComplete) return '正在发起命令'
    if (callComplete && !runtimeStarted) return '已发起命令'
    if (status === 'pending' || status === 'streaming') return `正在运行命令（${elapsedSeconds.value}s）`
    if (status === 'failed') return '命令失败'
    return '已运行命令'
  }

  if (traceKind.value === 'read') {
    if (!callComplete) return '正在发起浏览'
    if (callComplete && !runtimeStarted) return '已发起浏览'
    if (status === 'pending' || status === 'streaming') return '正在浏览'
    if (status === 'failed') return '浏览失败'
    return '已浏览'
  }

  if (traceKind.value === 'skill') {
    if (!callComplete) return '正在发起技能'
    if (callComplete && !runtimeStarted) return '已发起技能'
    if (status === 'pending' || status === 'streaming') return '正在加载技能'
    if (status === 'failed') return '技能加载失败'
    return '已加载技能'
  }

  if (status === 'pending') return '等待执行'
  if (status === 'streaming') return '执行中'
  if (status === 'failed') return '执行失败'
  return '执行完成'
})

const chartRenderModel = computed(() => (kind.value === 'chart_spec' ? buildChartRenderModel(outputPayload.value) : null))
const chartRenderState = computed(() => String(chartRenderModel.value?.state || 'empty'))
const chartRenderKind = computed(() => String(chartRenderModel.value?.kind || ''))
const chartRenderError = computed(() => String(chartRenderModel.value?.errorText || '').trim())
const chartColumns = computed(() => Array.isArray(chartRenderModel.value?.columns) ? chartRenderModel.value.columns : [])
const chartRows = computed(() => Array.isArray(chartRenderModel.value?.rows) ? chartRenderModel.value.rows : [])
const chartOption = computed(() => {
  if (kind.value !== 'chart_spec') return null
  return chartRenderModel.value?.kind === 'echarts' ? chartRenderModel.value.option : null
})
const showChartRawText = computed(() => {
  if (kind.value !== 'chart_spec') return false
  return ['invalid', 'error'].includes(chartRenderState.value) && Boolean(rawText.value)
})
const showRawPayload = computed(() => Boolean(rawText.value) && !showTrace.value)

let chartRefreshFrame = 0
let chartInstance = null
let statusTimer = 0

const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

const refreshChart = async () => {
  if (typeof window === 'undefined') return
  await nextTick()
  if (chartRefreshFrame) window.cancelAnimationFrame(chartRefreshFrame)
  chartRefreshFrame = window.requestAnimationFrame(() => {
    const container = chartCanvasRef.value
    if (!container || !chartOption.value) return
    try {
      if (!chartInstance) {
        chartInstance = echarts.init(container, undefined, { renderer: 'canvas' })
      }
      chartInstance.clear()
      chartInstance.setOption(chartOption.value, { notMerge: true, lazyUpdate: false })
      chartInstance.resize()
    } catch (_error) {
      // Swallow redraw failures and let the empty/error state remain visible.
    }
  })
}

watch(
  () => [chartRenderState.value, chartOption.value, props.tool?.id],
  () => {
    if (chartRenderState.value === 'renderable' && chartOption.value) {
      refreshChart()
      return
    }
    disposeChart()
  },
  { deep: true }
)

onMounted(() => {
  if (showTrace.value && traceHasPanel.value) {
    const status = String(props.tool?.status || 'success')
    const callComplete = Boolean(props.tool?._callComplete)
    const runtimeStarted = Boolean(props.tool?._runtimeStarted)
    shellOpen.value = (!callComplete) || (runtimeStarted && (status === 'pending' || status === 'streaming'))
  }
  if (chartRenderState.value === 'renderable' && chartOption.value) {
    refreshChart()
  }

  if (typeof window !== 'undefined') {
    statusTimer = window.setInterval(() => {
      nowTick.value = Date.now()
    }, 1000)
  }
})

watch(
  () => [props.tool?.status, props.tool?._callComplete, props.tool?._runtimeStarted],
  ([status, callComplete, runtimeStarted]) => {
    if (!showTrace.value || !traceHasPanel.value) return
    const value = String(status || 'success')
    shellOpen.value = !Boolean(callComplete) || (Boolean(runtimeStarted) && (value === 'pending' || value === 'streaming'))
  },
  { immediate: true }
)

watch(
  () => props.tool?.id,
  () => {
    traceMarkdownExpanded.value = false
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (chartRefreshFrame && typeof window !== 'undefined') {
    window.cancelAnimationFrame(chartRefreshFrame)
  }
  if (statusTimer && typeof window !== 'undefined') {
    window.clearInterval(statusTimer)
  }
  disposeChart()
})
</script>

<style scoped>
.tool-output {
  padding: 16px 18px;
  border: 1px solid #dfe8f1;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.tool-output-shell {
  padding: 2px 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.tool-output.failed {
  border-color: rgba(190, 24, 93, 0.2);
  background: linear-gradient(180deg, #fff8fb 0%, #fff 100%);
}

.tool-output-shell.failed {
  background: transparent;
}

.shell-trace + .tool-output-head,
.shell-trace + .tool-output-summary,
.shell-trace + .tool-output-error {
  margin-top: 14px;
}

.shell-trace-summary {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.shell-trace-summary-static {
  cursor: default;
}

.shell-trace-summary-text {
  flex: 1;
  min-width: 0;
  color: #6a6a6a;
  font-size: 14px;
  line-height: 1.55;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.shell-trace-summary-status {
  font-size: 12px;
  font-weight: 600;
  color: #8a8a8a;
}

.shell-trace-summary-status.is-running {
  color: #6b7280;
}

.shell-trace-summary-status.is-success {
  color: #6b7280;
}

.shell-trace-summary-status.is-failed {
  color: #9f1239;
}

.shell-trace-summary-chevron {
  color: #9a9a9a;
  font-size: 14px;
  transition: transform 0.18s ease;
}

.shell-trace-summary-chevron.open {
  transform: rotate(180deg);
}

.shell-trace-panel {
  margin-top: 8px;
  padding: 12px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 14px;
  background: linear-gradient(180deg, #f3f3f3 0%, #ececec 100%);
}

.shell-trace-panel-title {
  color: #8a8a8a;
  font-size: 12px;
  font-weight: 600;
}

.shell-trace-command,
.shell-trace-output {
  margin: 12px 0 0;
  padding: 0;
  background: transparent;
  color: #3f3f3f;
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.shell-trace-description {
  margin-top: 10px;
  color: #7b7b7b;
  font-size: 12px;
  line-height: 1.6;
}

.shell-trace-empty {
  margin-top: 12px;
  color: #9a9a9a;
  font-size: 12px;
  line-height: 1.6;
}

.tool-markdown {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #dbe3ec;
}

.tool-markdown-body {
  color: #334155;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;
}

.tool-markdown-body :deep(h1),
.tool-markdown-body :deep(h2),
.tool-markdown-body :deep(h3),
.tool-markdown-body :deep(h4),
.tool-markdown-body :deep(h5),
.tool-markdown-body :deep(h6) {
  margin: 0 0 10px;
  color: #162131;
  font-weight: 700;
  line-height: 1.4;
}

.tool-markdown-body :deep(p),
.tool-markdown-body :deep(ul),
.tool-markdown-body :deep(ol),
.tool-markdown-body :deep(blockquote) {
  margin: 0 0 10px;
}

.tool-markdown-body :deep(ul),
.tool-markdown-body :deep(ol) {
  padding-left: 18px;
}

.tool-markdown-body :deep(code) {
  padding: 1px 5px;
  border-radius: 6px;
  background: #f4f7fb;
  color: #1f3b57;
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.tool-markdown-body :deep(pre) {
  margin: 10px 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #102033;
  color: #edf5ff;
  overflow: auto;
}

.tool-markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.tool-markdown-toggle {
  margin-top: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #31567a;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.tool-markdown-toggle:hover {
  color: #1d3f5e;
}

.shell-trace-footer {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  font-size: 12px;
}

.shell-trace-footer-label {
  color: #a0a0a0;
}

.shell-trace-footer-value {
  color: #7a7a7a;
  font-weight: 600;
}

.shell-trace-footer-value.is-failed {
  color: #9f1239;
}

.tool-output-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.tool-output-label {
  font-size: 14px;
  font-weight: 700;
  color: #162131;
}

.tool-output-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #607185;
}

.tool-output-chip {
  padding: 5px 10px;
  border-radius: 999px;
  background: #eef6ff;
  color: #31567a;
  font-size: 12px;
  font-weight: 600;
}

.tool-output-summary {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.65;
  color: #334155;
}

.tool-output-error {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(190, 24, 93, 0.08);
  color: #9f1239;
  font-size: 13px;
  line-height: 1.6;
}

.tool-code {
  margin: 14px 0 0;
  padding: 14px 16px;
  border-radius: 14px;
  background: #102033;
  color: #edf5ff;
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
}

.tool-code-light {
  background: #f3f7fb;
  color: #233142;
}

.tool-table-wrap {
  margin-top: 14px;
  overflow: auto;
  border: 1px solid #e1e8f0;
  border-radius: 14px;
  background: #fff;
}

.tool-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 480px;
}

.tool-table th,
.tool-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  font-size: 12px;
  color: #233142;
  white-space: pre-wrap;
  word-break: break-word;
  vertical-align: top;
}

.tool-table th {
  background: #f8fbff;
  color: #607185;
  font-weight: 700;
  white-space: nowrap;
}

.tool-chart {
  display: block;
  margin-top: 14px;
  min-height: 320px;
  height: 320px;
  width: 100%;
  min-width: 0;
}

.tool-output-empty {
  margin-top: 14px;
  color: #8da0b3;
  font-size: 13px;
}
</style>
