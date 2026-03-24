<template>
  <div class="version-compare-panel" v-loading="loading">
    <div class="toolbar">
      <el-button @click="$emit('back')">返回记录列表</el-button>
    </div>

    <div class="version-navigator" v-if="compareResult">
      <el-button
        circle
        size="small"
        :icon="ArrowLeft"
        :disabled="!canStepLeft"
        @click="$emit('step', 'left')"
      />
      <div class="version-pair">
        <div class="version-card is-left">
          <div class="version-card-title">左侧版本</div>
          <div class="version-card-no">{{ leftVersionLabel }}</div>
          <div class="version-card-meta">{{ formatDateTime(leftVersionMeta?.createdAt) }}</div>
          <div class="version-card-meta">{{ leftVersionMeta?.createdBy || '-' }}</div>
        </div>
        <div class="version-card is-right">
          <div class="version-card-title">右侧版本</div>
          <div class="version-card-no">{{ rightVersionLabel }}</div>
          <div class="version-card-meta">{{ formatDateTime(rightVersionMeta?.createdAt) }}</div>
          <div class="version-card-meta">{{ rightVersionMeta?.createdBy || '-' }}</div>
        </div>
      </div>
      <el-button
        circle
        size="small"
        :icon="ArrowRight"
        :disabled="!canStepRight"
        @click="$emit('step', 'right')"
      />
    </div>

    <div v-if="compareResult" class="summary-row">
      <span>新增: {{ compareResult.summary?.added || 0 }}</span>
      <span>删除: {{ compareResult.summary?.removed || 0 }}</span>
      <span>修改: {{ compareResult.summary?.modified || 0 }}</span>
      <span>不变: {{ compareResult.summary?.unchanged || 0 }}</span>
      <el-tag size="small" :type="compareResult.changed ? 'warning' : 'success'">
        {{ compareResult.changed ? '有变化' : '无变化' }}
      </el-tag>
    </div>

    <el-tabs v-if="compareResult" v-model="activeView" class="compare-tabs">
      <el-tab-pane label="结构化差异" name="structured">
        <div class="functional-sections">
          <div v-for="area in areaSections" :key="area.key" class="area-card">
            <div class="area-title">{{ area.label }}</div>
            <div class="status-grid">
              <div v-for="status in statusConfigs" :key="`${area.key}-${status.key}`" class="status-col">
                <div class="status-title">{{ status.label }} ({{ area[status.key].length }})</div>
                <div v-if="area[status.key].length" class="tag-wrap">
                  <el-tag
                    v-for="(item, index) in area[status.key]"
                    :key="`${area.key}-${status.key}-${index}`"
                    :type="status.type"
                    size="small"
                    class="item-tag"
                  >
                    {{ item }}
                  </el-tag>
                </div>
                <span v-else class="empty-text">-</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="原始JSON差异" name="raw">
        <div class="raw-diff-wrap">
          <div class="raw-diff-toolbar">
            <div class="raw-diff-toolbar-group">
              <span class="raw-diff-toolbar-label">布局</span>
              <el-radio-group v-model="rawDiffLayout" size="small">
                <el-radio-button :label="RAW_DIFF_LAYOUTS.UNIFIED">Unified</el-radio-button>
                <el-radio-button :label="RAW_DIFF_LAYOUTS.SPLIT">Split</el-radio-button>
              </el-radio-group>
            </div>
            <div class="raw-diff-toolbar-group">
              <span class="raw-diff-toolbar-label">内容</span>
              <el-radio-group v-model="rawDiffFilterMode" size="small">
                <el-radio-button :label="RAW_DIFF_FILTERS.DIFF_ONLY">只看差异</el-radio-button>
                <el-radio-button :label="RAW_DIFF_FILTERS.SHOW_ALL">查看全部</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div v-if="activeRawDiffRows.length" class="raw-diff-text">
            <template v-if="!isSplitRawDiffLayout">
              <div
                v-for="row in unifiedRawDiffRows"
                :key="row.key"
                :class="[
                  'raw-diff-row',
                  'raw-diff-row--unified',
                  `is-${row.type}`,
                  { 'is-control': isControlDiffType(row.type) }
                ]"
              >
                <template v-if="isControlDiffType(row.type)">
                  <span class="raw-diff-control-line">
                    <template v-for="(segment, index) in row.segments" :key="`${row.key}-${index}`">
                      <span :class="['raw-diff-segment', { 'is-inline-changed': segment.changed }]">
                        {{ segment.text }}
                      </span>
                    </template>
                  </span>
                </template>
                <template v-else>
                  <span :class="['raw-diff-line-no', `is-${row.type}`]">
                    {{ formatLineNumber(row.leftLineNumber) }}
                  </span>
                  <span :class="['raw-diff-line-no', `is-${row.type}`]">
                    {{ formatLineNumber(row.rightLineNumber) }}
                  </span>
                  <span :class="['raw-diff-line', `is-${row.type}`]">
                    <span class="raw-diff-prefix">{{ row.prefix || ' ' }}</span>
                    <template v-for="(segment, index) in row.segments" :key="`${row.key}-${index}`">
                      <span :class="['raw-diff-segment', { 'is-inline-changed': segment.changed }]">
                        {{ segment.text }}
                      </span>
                    </template>
                  </span>
                </template>
              </div>
            </template>
            <template v-else>
              <div
                v-for="row in splitRawDiffRows"
                :key="row.key"
                :class="[
                  'raw-diff-row',
                  'raw-diff-row--split',
                  `is-${row.type}`,
                  { 'is-control': row.isControl }
                ]"
              >
                <template v-if="row.isControl">
                  <span class="raw-diff-control-line">
                    <template v-for="(segment, index) in row.segments" :key="`${row.key}-${index}`">
                      <span :class="['raw-diff-segment', { 'is-inline-changed': segment.changed }]">
                        {{ segment.text }}
                      </span>
                    </template>
                  </span>
                </template>
                <template v-else>
                  <span :class="['raw-diff-line-no', 'is-left', `is-${resolveRawDiffCellType(row.left)}`]">
                    {{ formatLineNumber(row.left?.leftLineNumber) }}
                  </span>
                  <span :class="['raw-diff-line', 'raw-diff-split-cell', 'is-left', `is-${resolveRawDiffCellType(row.left)}`]">
                    <template v-if="row.left">
                      <span class="raw-diff-prefix">{{ row.left.prefix || ' ' }}</span>
                      <template v-for="(segment, index) in row.left.segments" :key="`${row.key}-left-${index}`">
                        <span :class="['raw-diff-segment', { 'is-inline-changed': segment.changed }]">
                          {{ segment.text }}
                        </span>
                      </template>
                    </template>
                  </span>
                  <span :class="['raw-diff-line-no', 'is-right', `is-${resolveRawDiffCellType(row.right)}`]">
                    {{ formatLineNumber(row.right?.rightLineNumber) }}
                  </span>
                  <span :class="['raw-diff-line', 'raw-diff-split-cell', 'is-right', `is-${resolveRawDiffCellType(row.right)}`]">
                    <template v-if="row.right">
                      <span class="raw-diff-prefix">{{ row.right.prefix || ' ' }}</span>
                      <template v-for="(segment, index) in row.right.segments" :key="`${row.key}-right-${index}`">
                        <span :class="['raw-diff-segment', { 'is-inline-changed': segment.changed }]">
                          {{ segment.text }}
                        </span>
                      </template>
                    </template>
                  </span>
                </template>
              </div>
            </template>
          </div>
          <div v-else class="raw-diff-empty">-</div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { buildRawDiffRows, buildSplitViewRows, buildUnifiedViewRows, RAW_DIFF_TYPES } from './workflowRawDiffHelper'

const props = defineProps({
  versions: {
    type: Array,
    default: () => []
  },
  leftVersionId: {
    type: Number,
    default: null
  },
  rightVersionId: {
    type: Number,
    default: null
  },
  compareResult: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['back', 'step'])

const activeView = ref('structured')
const RAW_DIFF_LAYOUTS = {
  UNIFIED: 'unified',
  SPLIT: 'split'
}
const RAW_DIFF_FILTERS = {
  DIFF_ONLY: 'diff-only',
  SHOW_ALL: 'show-all'
}
const rawDiffLayout = ref(RAW_DIFF_LAYOUTS.UNIFIED)
const rawDiffFilterMode = ref(RAW_DIFF_FILTERS.DIFF_ONLY)

watch(
  () => props.compareResult,
  () => {
    activeView.value = 'structured'
    rawDiffLayout.value = RAW_DIFF_LAYOUTS.UNIFIED
    rawDiffFilterMode.value = RAW_DIFF_FILTERS.DIFF_ONLY
  }
)

const statusConfigs = [
  { key: 'added', label: '新增', type: 'success' },
  { key: 'removed', label: '删除', type: 'danger' },
  { key: 'modified', label: '修改', type: 'warning' },
  { key: 'unchanged', label: '不变', type: 'info' }
]

const orderedVersions = computed(() => {
  return [...(props.versions || [])].sort((a, b) => (a.versionNo || 0) - (b.versionNo || 0))
})

const versionMap = computed(() => {
  return orderedVersions.value.reduce((acc, item) => {
    if (item?.id) {
      acc[Number(item.id)] = item
    }
    return acc
  }, {})
})

const rightVersionIndex = computed(() => {
  const rightId = Number(props.rightVersionId)
  if (!Number.isFinite(rightId)) {
    return -1
  }
  return orderedVersions.value.findIndex((item) => Number(item.id) === rightId)
})

const canStepLeft = computed(() => rightVersionIndex.value > 1)
const canStepRight = computed(() => {
  if (rightVersionIndex.value < 0) {
    return false
  }
  return rightVersionIndex.value < orderedVersions.value.length - 1
})

const leftVersionMeta = computed(() => {
  const id = Number(props.leftVersionId)
  return Number.isFinite(id) ? (versionMap.value[id] || null) : null
})

const rightVersionMeta = computed(() => {
  const id = Number(props.rightVersionId)
  return Number.isFinite(id) ? (versionMap.value[id] || null) : null
})

const leftVersionLabel = computed(() => {
  if (props.compareResult?.leftVersionNo === null || props.compareResult?.leftVersionNo === undefined) {
    return '空基线'
  }
  return `v${props.compareResult.leftVersionNo}`
})

const rightVersionLabel = computed(() => {
  if (props.compareResult?.rightVersionNo === null || props.compareResult?.rightVersionNo === undefined) {
    return '-'
  }
  return `v${props.compareResult.rightVersionNo}`
})

const isGlobalField = (item) => String(item || '').includes('workflow.globalParams')

const getSectionArray = (statusKey, sectionKey) => {
  const section = props.compareResult?.[statusKey]
  const list = section?.[sectionKey]
  return Array.isArray(list) ? list : []
}

const pickWorkflowFields = (statusKey, includeGlobalField) => {
  const fields = getSectionArray(statusKey, 'workflowFields')
  return fields.filter((item) => {
    if (includeGlobalField) {
      return isGlobalField(item)
    }
    return !isGlobalField(item)
  })
}

const buildAreaSection = (key, label, resolver) => {
  return {
    key,
    label,
    added: resolver('added'),
    removed: resolver('removed'),
    modified: resolver('modified'),
    unchanged: resolver('unchanged')
  }
}

const hasAnyItems = (section) => {
  return ['added', 'removed', 'modified', 'unchanged']
    .some((statusKey) => (section?.[statusKey] || []).length > 0)
}

const areaSections = computed(() => {
  if (!props.compareResult) {
    return []
  }
  const sections = [
    buildAreaSection('global-params', '全局变量', (statusKey) => pickWorkflowFields(statusKey, true)),
    buildAreaSection('schedule', '定时调度', (statusKey) => getSectionArray(statusKey, 'schedules')),
    buildAreaSection('task-list', '任务列表', (statusKey) => getSectionArray(statusKey, 'edges')),
    buildAreaSection('task-definitions', '任务定义', (statusKey) => getSectionArray(statusKey, 'tasks'))
  ]

  const workflowFields = buildAreaSection(
    'workflow-fields',
    '工作流属性',
    (statusKey) => pickWorkflowFields(statusKey, false)
  )

  if (hasAnyItems(workflowFields)) {
    sections.push(workflowFields)
  }
  return sections
})

const rawDiffRows = computed(() => buildRawDiffRows(props.compareResult?.rawDiff))
const showAllRawDiff = computed(() => rawDiffFilterMode.value === RAW_DIFF_FILTERS.SHOW_ALL)
const unifiedRawDiffRows = computed(() => buildUnifiedViewRows(rawDiffRows.value, { showAll: showAllRawDiff.value }))
const splitRawDiffRows = computed(() => buildSplitViewRows(rawDiffRows.value, { showAll: showAllRawDiff.value }))
const isSplitRawDiffLayout = computed(() => rawDiffLayout.value === RAW_DIFF_LAYOUTS.SPLIT)
const activeRawDiffRows = computed(() => (isSplitRawDiffLayout.value ? splitRawDiffRows.value : unifiedRawDiffRows.value))

const isControlDiffType = (type) => {
  return [RAW_DIFF_TYPES.META_OLD, RAW_DIFF_TYPES.META_NEW, RAW_DIFF_TYPES.HUNK].includes(type)
}

const resolveRawDiffCellType = (row) => row?.type || 'empty'

const formatDateTime = (value) => {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '-'
}

const formatLineNumber = (value) => {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? String(normalized) : ''
}
</script>

<style scoped>
.version-compare-panel {
  margin-top: 12px;
}

.toolbar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 10px;
}

.version-navigator {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 10px;
}

.version-pair {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 8px;
}

.version-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
}

.version-card.is-left {
  border-color: #67c23a;
}

.version-card.is-right {
  border-color: #409eff;
}

.version-card-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.version-card-no {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.version-card-meta {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.summary-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin: 12px 0;
  color: #606266;
  font-size: 13px;
}

.compare-tabs {
  margin-top: 8px;
}

.functional-sections {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.area-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px;
  background: #fff;
}

.area-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.status-col {
  border: 1px solid #f0f2f5;
  border-radius: 6px;
  background: #fafafa;
  padding: 8px;
  min-height: 72px;
}

.status-title {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 600;
}

.tag-wrap {
  display: flex;
  flex-wrap: wrap;
}

.item-tag {
  margin: 0 6px 6px 0;
}

.empty-text {
  color: #c0c4cc;
  font-size: 12px;
}

.raw-diff-wrap {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fcfcfd;
  overflow: hidden;
}

.raw-diff-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap;
}

.raw-diff-toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.raw-diff-toolbar-label {
  color: #909399;
  font-size: 12px;
}

.raw-diff-text {
  font-family: Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  overflow: auto;
  font-size: 12px;
  line-height: 1.45;
  color: #303133;
  max-height: 540px;
}

.raw-diff-row + .raw-diff-row {
  border-top: 1px solid rgba(235, 238, 245, 0.7);
}

.raw-diff-row--unified {
  display: grid;
  grid-template-columns: 64px 64px minmax(0, 1fr);
  min-width: max-content;
}

.raw-diff-row--split {
  display: grid;
  grid-template-columns: 64px minmax(320px, 1fr) 64px minmax(320px, 1fr);
  min-width: max-content;
}

.raw-diff-row.is-control {
  grid-template-columns: 1fr;
}

.raw-diff-line-no,
.raw-diff-line,
.raw-diff-control-line {
  padding: 4px 8px;
  white-space: pre;
}

.raw-diff-line-no {
  text-align: right;
  user-select: none;
  color: #909399;
  background: #f8f9fb;
  border-right: 1px solid rgba(235, 238, 245, 0.8);
}

.raw-diff-line-no.is-left,
.raw-diff-line.is-left {
  border-right: 1px solid rgba(235, 238, 245, 0.8);
}

.raw-diff-line {
  overflow-x: auto;
}

.raw-diff-line.is-added,
.raw-diff-split-cell.is-added {
  background: #f0f9eb;
}

.raw-diff-line.is-removed,
.raw-diff-split-cell.is-removed {
  background: #fef0f0;
}

.raw-diff-line.is-context,
.raw-diff-split-cell.is-context {
  background: #fcfcfd;
}

.raw-diff-line.is-empty,
.raw-diff-split-cell.is-empty {
  background: #f8f9fb;
}

.raw-diff-line-no.is-added {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.raw-diff-line-no.is-removed {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.raw-diff-line-no.is-empty {
  color: transparent;
}

.raw-diff-control-line {
  grid-column: 1 / -1;
  overflow-x: auto;
}

.raw-diff-row.is-hunk .raw-diff-control-line {
  background: #ecf5ff;
  color: #409eff;
}

.raw-diff-row.is-meta-old .raw-diff-control-line,
.raw-diff-row.is-meta-new .raw-diff-control-line {
  background: #f4f4f5;
  color: #606266;
}

.raw-diff-prefix {
  display: inline-block;
  width: 14px;
  margin-right: 6px;
  text-align: center;
  color: #909399;
  user-select: none;
}

.raw-diff-line.is-added .raw-diff-prefix,
.raw-diff-split-cell.is-added .raw-diff-prefix {
  color: #67c23a;
}

.raw-diff-line.is-removed .raw-diff-prefix,
.raw-diff-split-cell.is-removed .raw-diff-prefix {
  color: #f56c6c;
}

.raw-diff-segment.is-inline-changed {
  border-radius: 3px;
  font-weight: 600;
}

.raw-diff-line.is-added .raw-diff-segment.is-inline-changed,
.raw-diff-split-cell.is-added .raw-diff-segment.is-inline-changed {
  background: rgba(103, 194, 58, 0.24);
  color: #2f7d32;
}

.raw-diff-line.is-removed .raw-diff-segment.is-inline-changed,
.raw-diff-split-cell.is-removed .raw-diff-segment.is-inline-changed {
  background: rgba(245, 108, 108, 0.22);
  color: #c45656;
}

.raw-diff-empty {
  padding: 12px;
  color: #909399;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .version-pair {
    grid-template-columns: 1fr;
  }

  .raw-diff-toolbar {
    align-items: flex-start;
  }

  .raw-diff-toolbar-group {
    width: 100%;
    justify-content: space-between;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
