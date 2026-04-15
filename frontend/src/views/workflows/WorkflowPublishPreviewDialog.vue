<template>
  <div class="publish-preview-dialog">
    <el-scrollbar class="publish-preview-dialog__scrollbar">
      <div class="publish-preview-dialog__content">
        <div class="publish-preview-dialog__intro">
          检测到平台定义与 Dolphin 运行态存在差异，确认后将按平台定义发布。
        </div>
        <div class="publish-preview-dialog__tip">
          变更前为 Dolphin 运行态当前值，变更后为平台本次发布目标值。
        </div>

        <section v-if="warnings.length" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">预检告警</div>
          <div class="publish-preview-dialog__warning-list">
            <div
              v-for="(issue, index) in warnings"
              :key="`warning-${index}`"
              class="publish-preview-dialog__warning-item"
            >
              <el-tag v-if="issue?.code" size="small" type="warning" effect="plain">
                {{ issue.code }}
              </el-tag>
              <span class="publish-preview-dialog__warning-text">{{ formatIssueText(issue) }}</span>
            </div>
          </div>
        </section>

        <section v-if="workflowFieldSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">
            Workflow 字段变更（{{ workflowFieldSection.count }}）
          </div>
          <div class="publish-preview-dialog__value-table">
            <div class="publish-preview-dialog__value-row is-head">
              <div>字段</div>
              <div>变更前（运行态）</div>
              <div>变更后（平台）</div>
            </div>
            <div
              v-for="(change, index) in workflowFieldSection.items"
              :key="`workflow-field-${index}`"
              class="publish-preview-dialog__value-row"
            >
              <div class="publish-preview-dialog__field-name">{{ change?.field || '-' }}</div>
              <div class="publish-preview-dialog__value-text">{{ formatSimpleFieldValue(change?.before) }}</div>
              <div class="publish-preview-dialog__value-text">{{ formatSimpleFieldValue(change?.after) }}</div>
            </div>
          </div>
          <div v-if="workflowFieldSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ workflowFieldSection.remain }} 项
          </div>
        </section>

        <section v-if="taskAddedSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">任务新增（{{ taskAddedSection.count }}）</div>
          <div class="publish-preview-dialog__tag-list">
            <el-tag
              v-for="(task, index) in taskAddedSection.items"
              :key="`task-added-${index}`"
              size="small"
              type="success"
              effect="plain"
            >
              {{ formatTaskLabel(task) }}
            </el-tag>
          </div>
          <div v-if="taskAddedSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ taskAddedSection.remain }} 项
          </div>
        </section>

        <section v-if="taskRemovedSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">任务删除（{{ taskRemovedSection.count }}）</div>
          <div class="publish-preview-dialog__tag-list">
            <el-tag
              v-for="(task, index) in taskRemovedSection.items"
              :key="`task-removed-${index}`"
              size="small"
              type="danger"
              effect="plain"
            >
              {{ formatTaskLabel(task) }}
            </el-tag>
          </div>
          <div v-if="taskRemovedSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ taskRemovedSection.remain }} 项
          </div>
        </section>

        <section v-if="taskModifiedSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">任务修改（{{ taskModifiedSection.count }}）</div>

          <div
            v-for="(task, taskIndex) in taskModifiedSection.items"
            :key="`task-modified-${taskIndex}`"
            class="publish-preview-dialog__task-card"
          >
            <div class="publish-preview-dialog__task-header">
              <div class="publish-preview-dialog__task-title">{{ formatTaskLabel(task) }}</div>
              <el-tag size="small" type="warning" effect="plain">
                字段 {{ task.fieldChangesCount }}
              </el-tag>
            </div>

            <div
              v-for="(fieldChange, fieldIndex) in task.fieldChanges"
              :key="`task-field-${taskIndex}-${fieldIndex}`"
              class="publish-preview-dialog__task-field"
            >
              <div class="publish-preview-dialog__task-field-header">
                <div class="publish-preview-dialog__field-name">{{ fieldChange?.field || '-' }}</div>
                <div class="publish-preview-dialog__stat-tags">
                  <el-tag
                    v-if="fieldChange.stats.added"
                    size="small"
                    type="success"
                    effect="plain"
                  >
                    新增 {{ fieldChange.stats.added }}
                  </el-tag>
                  <el-tag
                    v-if="fieldChange.stats.removed"
                    size="small"
                    type="danger"
                    effect="plain"
                  >
                    删除 {{ fieldChange.stats.removed }}
                  </el-tag>
                  <el-tag
                    v-if="fieldChange.stats.modified"
                    size="small"
                    type="warning"
                    effect="plain"
                  >
                    修改 {{ fieldChange.stats.modified }}
                  </el-tag>
                </div>
              </div>

              <div class="publish-preview-dialog__diff-header">
                <div>变更前（运行态）</div>
                <div>变更后（平台）</div>
              </div>

              <el-scrollbar :max-height="360" class="publish-preview-dialog__diff-scrollbar">
                <div class="publish-preview-dialog__diff-table">
                  <div
                    v-for="row in fieldChange.rows"
                    :key="row.key"
                    class="publish-preview-dialog__diff-row"
                    :class="`is-${row.type}`"
                  >
                    <div
                      :class="[
                        'publish-preview-dialog__diff-cell',
                        'is-left',
                        `is-${resolveCellType(row, 'left')}`
                      ]"
                    >
                      <template v-if="row.left">
                        <span class="publish-preview-dialog__diff-line-no">{{ row.left.lineNumber }}</span>
                        <span class="publish-preview-dialog__diff-line">
                          <span class="publish-preview-dialog__diff-prefix">{{ row.left.prefix }}</span>
                          <template
                            v-for="(segment, segmentIndex) in resolveCellSegments(row.left)"
                            :key="`${row.key}-left-${segmentIndex}`"
                          >
                            <span
                              :class="[
                                'publish-preview-dialog__diff-segment',
                                { 'is-inline-changed': segment.changed }
                              ]"
                            >
                              {{ segment.text || ' ' }}
                            </span>
                          </template>
                        </span>
                      </template>
                    </div>

                    <div
                      :class="[
                        'publish-preview-dialog__diff-cell',
                        'is-right',
                        `is-${resolveCellType(row, 'right')}`
                      ]"
                    >
                      <template v-if="row.right">
                        <span class="publish-preview-dialog__diff-line-no">{{ row.right.lineNumber }}</span>
                        <span class="publish-preview-dialog__diff-line">
                          <span class="publish-preview-dialog__diff-prefix">{{ row.right.prefix }}</span>
                          <template
                            v-for="(segment, segmentIndex) in resolveCellSegments(row.right)"
                            :key="`${row.key}-right-${segmentIndex}`"
                          >
                            <span
                              :class="[
                                'publish-preview-dialog__diff-segment',
                                { 'is-inline-changed': segment.changed }
                              ]"
                            >
                              {{ segment.text || ' ' }}
                            </span>
                          </template>
                        </span>
                      </template>
                    </div>
                  </div>
                </div>
              </el-scrollbar>

              <div v-if="fieldChange.rows.length === 0" class="publish-preview-dialog__empty">
                未检测到可展示的行级差异
              </div>
            </div>

            <div v-if="task.fieldChangesRemain" class="publish-preview-dialog__more">
              ... 另有 {{ task.fieldChangesRemain }} 个字段修改
            </div>
          </div>

          <div v-if="taskModifiedSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ taskModifiedSection.remain }} 个任务修改
          </div>
        </section>

        <section v-if="edgeSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">边变更</div>
          <div v-if="edgeSection.added.length" class="publish-preview-dialog__edge-group">
            <div class="publish-preview-dialog__edge-title is-added">边新增（{{ edgeSection.addedCount }}）</div>
            <div class="publish-preview-dialog__tag-list">
              <el-tag
                v-for="(item, index) in edgeSection.added"
                :key="`edge-added-${index}`"
                size="small"
                type="success"
                effect="plain"
              >
                {{ formatRelationLabel(item) }}
              </el-tag>
            </div>
          </div>
          <div v-if="edgeSection.removed.length" class="publish-preview-dialog__edge-group">
            <div class="publish-preview-dialog__edge-title is-removed">边删除（{{ edgeSection.removedCount }}）</div>
            <div class="publish-preview-dialog__tag-list">
              <el-tag
                v-for="(item, index) in edgeSection.removed"
                :key="`edge-removed-${index}`"
                size="small"
                type="danger"
                effect="plain"
              >
                {{ formatRelationLabel(item) }}
              </el-tag>
            </div>
          </div>
          <div v-if="edgeSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ edgeSection.remain }} 项
          </div>
        </section>

        <section v-if="scheduleFieldSection.count" class="publish-preview-dialog__section">
          <div class="publish-preview-dialog__section-title">
            调度变更（{{ scheduleFieldSection.count }}）
          </div>
          <div class="publish-preview-dialog__value-table">
            <div class="publish-preview-dialog__value-row is-head">
              <div>字段</div>
              <div>变更前（运行态）</div>
              <div>变更后（平台）</div>
            </div>
            <div
              v-for="(change, index) in scheduleFieldSection.items"
              :key="`schedule-field-${index}`"
              class="publish-preview-dialog__value-row"
            >
              <div class="publish-preview-dialog__field-name">{{ change?.field || '-' }}</div>
              <div class="publish-preview-dialog__value-text">{{ formatSimpleFieldValue(change?.before) }}</div>
              <div class="publish-preview-dialog__value-text">{{ formatSimpleFieldValue(change?.after) }}</div>
            </div>
          </div>
          <div v-if="scheduleFieldSection.remain" class="publish-preview-dialog__more">
            ... 另有 {{ scheduleFieldSection.remain }} 项
          </div>
        </section>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { MAX_RENDER_COUNT, formatFieldValue, formatRelation, formatTask } from './publishPreviewHelper'
import { buildTaskFieldDiffRows, summarizeTaskFieldDiffRows } from './publishPreviewDiffHelper'

const props = defineProps({
  preview: {
    type: Object,
    default: null
  }
})

const normalizeArray = (value) => (Array.isArray(value) ? value : [])

const createSectionState = (value, limit = MAX_RENDER_COUNT) => {
  const items = normalizeArray(value)
  return {
    items: items.slice(0, limit),
    count: items.length,
    remain: Math.max(items.length - limit, 0)
  }
}

const summary = computed(() => props.preview?.diffSummary || {})
const warnings = computed(() => normalizeArray(props.preview?.warnings))
const workflowFieldSection = computed(() => createSectionState(summary.value.workflowFieldChanges))
const taskAddedSection = computed(() => createSectionState(summary.value.taskAdded))
const taskRemovedSection = computed(() => createSectionState(summary.value.taskRemoved))
const scheduleFieldSection = computed(() => createSectionState(summary.value.scheduleChanges))

const taskModifiedSection = computed(() => {
  const section = createSectionState(summary.value.taskModified)
  return {
    ...section,
    items: section.items.map((task) => {
      const fieldChanges = normalizeArray(task?.fieldChanges)
      return {
        ...task,
        fieldChangesCount: fieldChanges.length,
        fieldChangesRemain: Math.max(fieldChanges.length - 10, 0),
        fieldChanges: fieldChanges.slice(0, 10).map((fieldChange) => {
          const rows = buildTaskFieldDiffRows(fieldChange?.before, fieldChange?.after)
          return {
            ...fieldChange,
            rows,
            stats: summarizeTaskFieldDiffRows(rows)
          }
        })
      }
    })
  }
})

const edgeSection = computed(() => {
  const addedSection = createSectionState(summary.value.edgeAdded)
  const removedSection = createSectionState(summary.value.edgeRemoved)
  return {
    added: addedSection.items,
    removed: removedSection.items,
    addedCount: addedSection.count,
    removedCount: removedSection.count,
    count: addedSection.count + removedSection.count,
    remain: addedSection.remain + removedSection.remain
  }
})

const formatSimpleFieldValue = (value) => formatFieldValue(value)
const formatTaskLabel = (task) => formatTask(task)
const formatRelationLabel = (relation) => formatRelation(relation)

const formatIssueText = (issue) => {
  const parts = []
  if (issue?.taskName) {
    parts.push(`任务: ${issue.taskName}`)
  }
  if (issue?.message) {
    parts.push(issue.message)
  }
  return parts.length ? parts.join(' | ') : '-'
}

const resolveCellType = (row, side) => {
  if (row?.type === 'modified') {
    return 'modified'
  }
  if (side === 'left') {
    return row?.type === 'removed' ? 'removed' : 'empty'
  }
  return row?.type === 'added' ? 'added' : 'empty'
}

const resolveCellSegments = (cell) => {
  return Array.isArray(cell?.segments) && cell.segments.length
    ? cell.segments
    : [{ text: cell?.text || '', changed: false }]
}
</script>

<style scoped lang="scss">
.publish-preview-dialog {
  min-width: 0;
}

.publish-preview-dialog__scrollbar {
  height: min(72vh, 860px);
}

.publish-preview-dialog__content {
  padding-right: 8px;
}

.publish-preview-dialog__intro {
  color: #303133;
  font-weight: 500;
}

.publish-preview-dialog__tip {
  margin-top: 6px;
  color: #909399;
  font-size: 13px;
}

.publish-preview-dialog__section {
  margin-top: 16px;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}

.publish-preview-dialog__section-title {
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.publish-preview-dialog__warning-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.publish-preview-dialog__warning-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #e6a23c;
  line-height: 1.5;
}

.publish-preview-dialog__warning-text {
  color: #606266;
}

.publish-preview-dialog__value-table {
  margin-top: 10px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.publish-preview-dialog__value-row {
  display: grid;
  grid-template-columns: minmax(140px, 220px) minmax(0, 1fr) minmax(0, 1fr);
}

.publish-preview-dialog__value-row + .publish-preview-dialog__value-row {
  border-top: 1px solid #ebeef5;
}

.publish-preview-dialog__value-row > div {
  min-width: 0;
  padding: 10px 12px;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.publish-preview-dialog__value-row > div + div {
  border-left: 1px solid #ebeef5;
}

.publish-preview-dialog__value-row.is-head > div {
  background: #f5f7fa;
  color: #303133;
  font-weight: 600;
}

.publish-preview-dialog__field-name {
  color: #303133;
  font-weight: 500;
  word-break: break-word;
}

.publish-preview-dialog__value-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.publish-preview-dialog__tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.publish-preview-dialog__task-card {
  margin-top: 12px;
  padding: 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}

.publish-preview-dialog__task-header,
.publish-preview-dialog__task-field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.publish-preview-dialog__task-title {
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.publish-preview-dialog__task-field {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #ebeef5;
}

.publish-preview-dialog__stat-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.publish-preview-dialog__diff-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  margin-top: 10px;
}

.publish-preview-dialog__diff-header > div {
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  background: #f5f7fa;
  color: #303133;
  font-size: 13px;
  font-weight: 600;
}

.publish-preview-dialog__diff-scrollbar {
  border: 1px solid #ebeef5;
  border-radius: 0 0 8px 8px;
  background: #fff;
}

.publish-preview-dialog__diff-table {
  font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 12px;
}

.publish-preview-dialog__diff-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  padding: 0 12px;
}

.publish-preview-dialog__diff-row + .publish-preview-dialog__diff-row {
  border-top: 1px solid #ebeef5;
}

.publish-preview-dialog__diff-cell {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  min-height: 36px;
}

.publish-preview-dialog__diff-line-no {
  padding: 8px 10px;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  color: #909399;
  text-align: right;
  user-select: none;
}

.publish-preview-dialog__diff-line {
  min-width: 0;
  padding: 8px 10px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.publish-preview-dialog__diff-prefix {
  display: inline-block;
  width: 14px;
  font-weight: 600;
  user-select: none;
}

.publish-preview-dialog__diff-segment.is-inline-changed {
  padding: 0 1px;
  border-radius: 3px;
}

.publish-preview-dialog__diff-cell.is-added {
  background: #f0f9eb;
}

.publish-preview-dialog__diff-cell.is-added .publish-preview-dialog__diff-prefix,
.publish-preview-dialog__edge-title.is-added {
  color: #67c23a;
}

.publish-preview-dialog__diff-cell.is-removed {
  background: #fef0f0;
}

.publish-preview-dialog__diff-cell.is-removed .publish-preview-dialog__diff-prefix,
.publish-preview-dialog__edge-title.is-removed {
  color: #f56c6c;
}

.publish-preview-dialog__diff-cell.is-modified {
  background: #fdf6ec;
}

.publish-preview-dialog__diff-cell.is-modified .publish-preview-dialog__diff-prefix {
  color: #e6a23c;
}

.publish-preview-dialog__diff-cell.is-modified .publish-preview-dialog__diff-segment.is-inline-changed {
  background: rgba(230, 162, 60, 0.22);
}

.publish-preview-dialog__diff-cell.is-added .publish-preview-dialog__diff-segment.is-inline-changed {
  background: rgba(103, 194, 58, 0.18);
}

.publish-preview-dialog__diff-cell.is-removed .publish-preview-dialog__diff-segment.is-inline-changed {
  background: rgba(245, 108, 108, 0.18);
}

.publish-preview-dialog__diff-cell.is-empty {
  background: #fafafa;
}

.publish-preview-dialog__edge-group + .publish-preview-dialog__edge-group {
  margin-top: 12px;
}

.publish-preview-dialog__edge-title {
  font-size: 13px;
  font-weight: 600;
}

.publish-preview-dialog__empty,
.publish-preview-dialog__more {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

@media (max-width: 960px) {
  .publish-preview-dialog__value-row,
  .publish-preview-dialog__diff-row,
  .publish-preview-dialog__diff-header {
    grid-template-columns: 1fr;
  }

  .publish-preview-dialog__diff-row {
    gap: 0;
    padding: 0;
  }

  .publish-preview-dialog__diff-cell + .publish-preview-dialog__diff-cell {
    border-top: 1px solid #ebeef5;
  }
}

:global(.workflow-publish-message-box) {
  width: min(1240px, 96vw) !important;
  max-width: 96vw !important;
}

:global(.workflow-publish-message-box--preview .el-message-box__message) {
  width: 100%;
  margin: 0;
}

:global(.workflow-publish-message-box--preview .el-message-box__content) {
  overflow: hidden;
}
</style>
