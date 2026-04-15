<template>
  <ProductPageShell
    eyebrow="Skill Library"
    title="Skill 管理"
    description="集中维护当前可用的 Skill。先选中一个 Skill，再处理启停、编辑和版本回滚。"
    :stats="skillStats"
  >
    <template #actions>
      <button type="button" class="oda-btn-secondary" :disabled="syncLoading" @click="triggerSync">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': syncLoading }" />
        {{ syncLoading ? '刷新中' : '刷新目录' }}
      </button>
    </template>

    <template #sidebar>
      <section class="oda-card p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-base font-semibold text-gray-900">Skill 列表</div>
            <div class="mt-1 text-sm leading-relaxed text-gray-500">
              按来源筛选后选择一个 Skill 开始管理。
            </div>
          </div>
          <span class="oda-chip">{{ filteredDocuments.length }}</span>
        </div>

        <div class="mt-5 flex flex-wrap gap-2">
          <button
            v-for="option in sourceOptions"
            :key="option.value"
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition"
            :class="selectedSource === option.value
              ? 'border-blue-700 bg-blue-700 text-white'
              : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'"
            @click="selectedSource = option.value"
          >
            <span>{{ option.label }}</span>
            <span class="text-xs" :class="selectedSource === option.value ? 'text-blue-100' : 'text-gray-400'">
              {{ option.count }}
            </span>
          </button>
        </div>

        <div class="mt-4">
          <input
            v-model="searchKeyword"
            class="oda-input"
            type="text"
            placeholder="搜索 Skill 名称或路径"
          >
          <div class="mt-2 text-xs leading-relaxed text-gray-400">
            目录：{{ settings.skills_root_dir || '-' }}
          </div>
        </div>

        <div class="mt-5 space-y-5">
          <section
            v-for="group in groupedDocuments"
            :key="group.key"
            class="space-y-2"
          >
            <div class="flex items-center justify-between">
              <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">{{ group.label }}</div>
              <span class="text-xs text-gray-400">{{ group.items.length }}</span>
            </div>

            <div class="space-y-2">
              <button
                v-for="row in group.items"
                :key="row.id"
                type="button"
                class="w-full rounded-lg border p-3 text-left transition"
                :class="row.id === selectedDocumentId
                  ? 'border-blue-700 bg-blue-700 text-white shadow-sm'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'"
                @click="loadDocument(row.id)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="truncate text-sm font-semibold">
                      {{ displayName(row) }}
                    </div>
                    <div
                      class="mt-1 truncate text-xs"
                      :class="row.id === selectedDocumentId ? 'text-slate-200' : 'text-gray-500'"
                    >
                      {{ row.file_name }}
                    </div>
                  </div>
                  <el-switch
                    :model-value="row.enabled"
                    :loading="runtimeUpdatingId === row.id"
                    @click.stop
                    @change="toggleSkillEnabled(row, $event)"
                  />
                </div>

                <div class="mt-3 flex flex-wrap gap-2">
                  <span :class="row.id === selectedDocumentId ? 'oda-chip-warning' : (row.enabled ? 'oda-chip-success' : 'oda-chip-neutral')">
                    {{ row.enabled ? '已激活' : '已停用' }}
                  </span>
                  <span :class="row.id === selectedDocumentId ? 'oda-chip-warning' : 'oda-chip'">
                    {{ sourceLabel(row.source) }}
                  </span>
                  <span :class="row.id === selectedDocumentId ? 'oda-chip-warning' : 'oda-chip'">
                    {{ row.version_count }} 个版本
                  </span>
                </div>

                <div
                  class="mt-3 truncate text-xs"
                  :class="row.id === selectedDocumentId ? 'text-slate-200' : 'text-gray-400'"
                >
                  {{ row.relative_path }}
                </div>
              </button>
            </div>
          </section>
        </div>
      </section>
    </template>

    <el-alert
      v-if="syncResult"
      type="success"
      :closable="true"
      show-icon
      @close="syncResult = null"
    >
      <template #title>
        Skill 目录已刷新：共处理 {{ syncResult.document_count }} 个文件，更新 {{ syncResult.changed_documents?.length || 0 }} 个。
      </template>
    </el-alert>

    <template v-if="detail">
      <section v-loading="detailLoading" class="oda-card p-5">
        <div class="flex flex-col gap-5 border-b border-gray-200 pb-5 xl:flex-row xl:items-start xl:justify-between">
          <div class="min-w-0">
            <div class="text-xl font-semibold tracking-tight text-gray-900">{{ displayName(detail) }}</div>
            <div class="mt-2 text-sm leading-relaxed text-gray-600">
              {{ detail.relative_path }}
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="oda-chip">{{ sourceLabel(detail.source) }}</span>
              <span :class="detail.enabled ? 'oda-chip-success' : 'oda-chip-neutral'">
                {{ detail.enabled ? '已激活' : '已停用' }}
              </span>
              <span class="oda-chip">{{ currentVersionLabel }}</span>
              <span :class="editorDirty ? 'oda-chip-warning' : 'oda-chip-success'">
                {{ editorDirty ? '未保存' : '已同步' }}
              </span>
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <button type="button" class="oda-btn-secondary" @click="openCompareDialog()">
              <GitCompareArrows class="h-4 w-4" />
              版本比对
            </button>
            <button
              v-if="detail.source === 'managed'"
              type="button"
              class="oda-btn-danger"
              @click="deleteDocument"
            >
              <Trash2 class="h-4 w-4" />
              删除 Skill
            </button>
            <button type="button" class="oda-btn-secondary" :disabled="!editorDirty" @click="resetEditor">
              <RotateCcw class="h-4 w-4" />
              重置
            </button>
            <button type="button" class="oda-btn-primary" :disabled="!editorDirty || saveLoading" @click="saveDocument">
              <Save class="h-4 w-4" />
              {{ saveLoading ? '保存中' : '保存' }}
            </button>
          </div>
        </div>

        <div class="mt-5 grid gap-4 lg:grid-cols-3">
          <div class="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">最近更新</div>
            <div class="mt-2 text-sm font-medium text-gray-900">{{ formatTime(detail.updated_at) }}</div>
            <div class="mt-1 text-sm text-gray-500">
              {{ detail.last_change_summary || '最近一次更新未填写说明' }}
            </div>
          </div>
          <div class="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">变更来源</div>
            <div class="mt-2 text-sm font-medium text-gray-900">{{ detail.last_change_source || '-' }}</div>
            <div class="mt-1 text-sm text-gray-500">用于标记最近一次版本是如何产生的。</div>
          </div>
          <div class="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">文件类型</div>
            <div class="mt-2 text-sm font-medium text-gray-900">{{ detail.content_type }}</div>
            <div class="mt-1 text-sm text-gray-500">正文内容会直接同步到当前托管 Skill。</div>
          </div>
        </div>

        <div class="mt-5">
          <label class="mb-2 block text-sm font-medium text-gray-700">本次修改说明</label>
          <input
            v-model="changeSummary"
            class="oda-input"
            type="text"
            maxlength="120"
            placeholder="例如：补充企业级前端设计约束"
          >
        </div>

        <div class="mt-5 rounded-lg border border-gray-200 bg-white">
          <TextCodeEditor
            v-model="editorContent"
            :placeholder="detail.content_type === 'json' ? '请输入 JSON 内容' : '请输入文件内容'"
          />
        </div>
      </section>

      <section class="oda-card p-5">
        <div class="flex flex-col gap-2 border-b border-gray-200 pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="oda-section-title">版本历史</div>
            <div class="mt-1 text-sm text-gray-500">保留每次保存记录，方便回看或回滚。</div>
          </div>
          <span class="oda-chip">{{ detail.versions?.length || 0 }} 个版本</span>
        </div>

        <el-table :data="detail.versions || []" size="small" class="mt-5" height="320">
          <el-table-column prop="version_no" label="版本" width="90">
            <template #default="{ row }">
              <span>V{{ row.version_no }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <span :class="row.is_current ? 'oda-chip-success' : 'oda-chip-neutral'">
                {{ row.is_current ? '当前' : '历史' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_source" label="来源" width="110" />
          <el-table-column prop="change_summary" label="说明" min-width="220" show-overflow-tooltip />
          <el-table-column label="时间" min-width="170">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" @click="openCompareDialog(row.id)">对比</el-button>
              <el-button
                text
                type="danger"
                :disabled="row.is_current"
                @click="confirmRollback(row)"
              >
                回滚
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>

    <section v-else class="oda-card p-10 text-center">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100 text-gray-500">
        <FileCode2 class="h-6 w-6" />
      </div>
      <div class="mt-4 text-lg font-semibold text-gray-900">先从左侧选择一个 Skill</div>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-gray-600">
        选中后可以查看正文、调整启停状态、保存版本并执行回滚。
      </p>
    </section>

    <el-dialog
      v-model="compareDialogVisible"
      title="版本比对"
      width="86%"
      :close-on-click-modal="false"
    >
      <div v-if="detail" class="mb-5 flex flex-wrap items-center gap-3">
        <el-select v-model="leftCompareVersionId" class="w-56" @change="loadCompare">
          <el-option :value="null" label="当前版本" />
          <el-option
            v-for="item in detail.versions || []"
            :key="item.id"
            :value="item.id"
            :label="`V${item.version_no} · ${item.change_source}`"
          />
        </el-select>
        <span class="oda-chip-neutral">vs</span>
        <el-select v-model="rightCompareVersionId" class="w-56" @change="loadCompare">
          <el-option :value="null" label="当前版本" />
          <el-option
            v-for="item in detail.versions || []"
            :key="item.id"
            :value="item.id"
            :label="`V${item.version_no} · ${item.change_source}`"
          />
        </el-select>
      </div>

      <div v-loading="compareLoading" class="space-y-5">
        <div v-if="compareResult" class="flex flex-wrap gap-2">
          <span class="oda-chip">{{ compareResult.left_label }}</span>
          <span class="oda-chip-success">{{ compareResult.right_label }}</span>
          <span class="oda-chip-warning">变更行 {{ compareResult.changed_lines }}</span>
          <span class="oda-chip">+{{ compareResult.added_lines }}</span>
          <span class="oda-chip">-{{ compareResult.removed_lines }}</span>
        </div>

        <div v-if="compareResult" class="grid gap-4 xl:grid-cols-2">
          <div class="rounded-lg border border-gray-200 bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">{{ compareResult.left_label }}</div>
            <TextCodeEditor :model-value="compareResult.left_content" read-only />
          </div>
          <div class="rounded-lg border border-gray-200 bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">{{ compareResult.right_label }}</div>
            <TextCodeEditor :model-value="compareResult.right_content" read-only />
          </div>
        </div>

        <div v-if="compareResult" class="rounded-lg border border-gray-200 bg-white p-4">
          <div class="mb-3 text-sm font-semibold text-gray-900">Unified Diff</div>
          <TextCodeEditor :model-value="compareResult.diff_text" read-only />
        </div>
      </div>
    </el-dialog>
  </ProductPageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  FileCode2,
  GitCompareArrows,
  RefreshCw,
  RotateCcw,
  Save,
  Trash2
} from 'lucide-vue-next'
import ProductPageShell from '@/components/ProductPageShell.vue'
import { dataagentApi } from '@/api/dataagent'
import TextCodeEditor from '@/components/TextCodeEditor.vue'

const listLoading = ref(false)
const detailLoading = ref(false)
const saveLoading = ref(false)
const syncLoading = ref(false)
const compareLoading = ref(false)
const runtimeUpdatingId = ref('')

const searchKeyword = ref('')
const selectedSource = ref('all')
const documents = ref([])
const selectedDocumentId = ref(null)
const detail = ref(null)
const editorContent = ref('')
const changeSummary = ref('')
const syncResult = ref(null)
const settings = ref({
  skills_root_dir: ''
})

const compareDialogVisible = ref(false)
const compareResult = ref(null)
const leftCompareVersionId = ref(null)
const rightCompareVersionId = ref(null)

const filteredDocuments = computed(() => {
  const keyword = String(searchKeyword.value || '').trim().toLowerCase()
  return documents.value.filter((item) => {
    const sourceMatched = selectedSource.value === 'all' || String(item.source || '') === selectedSource.value
    if (!sourceMatched) return false
    if (!keyword) return true
    return String(item.file_name || '').toLowerCase().includes(keyword)
      || String(item.relative_path || '').toLowerCase().includes(keyword)
  })
})

const groupedDocuments = computed(() => {
  const definitions = [
    { key: 'bundled', label: '内置 Skill', match: (item) => item.source === 'bundled' },
    { key: 'managed', label: '本地导入', match: (item) => item.source === 'managed' },
    { key: 'other', label: '其他', match: (item) => item.source !== 'bundled' && item.source !== 'managed' }
  ]
  return definitions
    .map((definition) => ({
      key: definition.key,
      label: definition.label,
      items: filteredDocuments.value.filter((item) => definition.match(item))
    }))
    .filter((group) => group.items.length)
})

const sourceOptions = computed(() => {
  const counts = {
    all: documents.value.length,
    bundled: documents.value.filter((item) => item.source === 'bundled').length,
    managed: documents.value.filter((item) => item.source === 'managed').length,
    other: documents.value.filter((item) => item.source !== 'bundled' && item.source !== 'managed').length
  }
  return [
    { value: 'all', label: '全部', count: counts.all },
    { value: 'bundled', label: '内置', count: counts.bundled },
    { value: 'managed', label: '本地导入', count: counts.managed },
    { value: 'other', label: '其他', count: counts.other }
  ]
})

const editorDirty = computed(() => !!detail.value && editorContent.value !== (detail.value.current_content || ''))

const currentVersionLabel = computed(() => {
  const current = (detail.value?.versions || []).find((item) => item.is_current)
  return current ? `V${current.version_no}` : '-'
})

const skillStats = computed(() => {
  const enabledCount = documents.value.filter((item) => item.enabled).length
  const managedCount = documents.value.filter((item) => item.source === 'managed').length
  return [
    { label: '全部 Skill', value: String(documents.value.length) },
    { label: '已激活', value: String(enabledCount) },
    { label: '本地导入', value: String(managedCount) },
    { label: '当前编辑', value: detail.value ? displayName(detail.value) : '未选择' }
  ]
})

const sourceLabel = (source) => {
  if (source === 'bundled') return '内置 Skill'
  if (source === 'managed') return '本地导入'
  return '其他'
}

const displayName = (row) => {
  const fileName = String(row?.file_name || row?.folder || '未命名')
  return fileName.replace(/\.(md|markdown|json)$/i, '')
}

const formatTime = (value) => {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

const loadSettings = async () => {
  const payload = await dataagentApi.getSettings()
  settings.value = {
    skills_root_dir: payload?.skills_root_dir || ''
  }
}

const loadDocuments = async () => {
  listLoading.value = true
  try {
    documents.value = await dataagentApi.listSkillDocuments()
    if (!documents.value.length) {
      selectedDocumentId.value = null
      detail.value = null
      editorContent.value = ''
      return
    }
    if (!selectedDocumentId.value && documents.value.length) {
      await loadDocument(documents.value[0].id)
      return
    }
    if (selectedDocumentId.value) {
      const matched = documents.value.find((item) => item.id === selectedDocumentId.value)
      if (!matched && documents.value.length) {
        await loadDocument(documents.value[0].id)
      }
    }
  } finally {
    listLoading.value = false
  }
}

const loadDocument = async (documentId) => {
  selectedDocumentId.value = documentId
  detailLoading.value = true
  try {
    const payload = await dataagentApi.getSkillDocument(documentId)
    detail.value = payload
    editorContent.value = payload?.current_content || ''
    changeSummary.value = ''
  } finally {
    detailLoading.value = false
  }
}

const saveDocument = async () => {
  if (!detail.value) return
  saveLoading.value = true
  try {
    const payload = await dataagentApi.updateSkillDocument(detail.value.id, {
      content: editorContent.value,
      change_summary: changeSummary.value || '前端保存'
    })
    detail.value = payload
    editorContent.value = payload.current_content || ''
    changeSummary.value = ''
    await loadDocuments()
    ElMessage.success('Skill 已保存')
  } finally {
    saveLoading.value = false
  }
}

const deleteDocument = async () => {
  if (!detail.value?.id || detail.value.source !== 'managed') return
  try {
    await ElMessageBox.confirm(
      `确认删除 ${displayName(detail.value)} 吗？删除后会移除当前托管版本和版本历史。`,
      '删除 Skill',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  await dataagentApi.deleteSkillDocument(detail.value.id)
  ElMessage.success('托管 Skill 已删除')
  selectedDocumentId.value = null
  detail.value = null
  editorContent.value = ''
  changeSummary.value = ''
  await loadDocuments()
}

const toggleSkillEnabled = async (row, enabled) => {
  if (!row?.id) return
  runtimeUpdatingId.value = row.id
  try {
    await dataagentApi.updateSkillRuntime(row.id, { enabled })
    const target = documents.value.find((item) => item.id === row.id)
    if (target) target.enabled = Boolean(enabled)
    if (detail.value?.id === row.id) detail.value.enabled = Boolean(enabled)
    ElMessage.success(enabled ? 'Skill 已启用' : 'Skill 已禁用')
  } finally {
    runtimeUpdatingId.value = ''
  }
}

const resetEditor = () => {
  if (!detail.value) return
  editorContent.value = detail.value.current_content || ''
  changeSummary.value = ''
}

const loadCompare = async () => {
  if (!detail.value) return
  compareLoading.value = true
  try {
    compareResult.value = await dataagentApi.compareSkillDocument(detail.value.id, {
      left_version_id: leftCompareVersionId.value,
      right_version_id: rightCompareVersionId.value
    })
  } finally {
    compareLoading.value = false
  }
}

const openCompareDialog = async (leftVersionId = null) => {
  if (!detail.value) return
  const fallbackHistory = (detail.value.versions || []).find((item) => !item.is_current)
  leftCompareVersionId.value = leftVersionId ?? fallbackHistory?.id ?? null
  rightCompareVersionId.value = null
  compareDialogVisible.value = true
  await loadCompare()
}

const confirmRollback = async (version) => {
  if (!detail.value || !version?.id || version.is_current) return
  try {
    await ElMessageBox.confirm(
      `确认回滚 ${displayName(detail.value)} 到 V${version.version_no} 吗？`,
      '版本回滚',
      {
        type: 'warning',
        confirmButtonText: '确认回滚',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  const payload = await dataagentApi.rollbackSkillDocument(detail.value.id, version.id)
  detail.value = payload
  editorContent.value = payload.current_content || ''
  changeSummary.value = ''
  await loadDocuments()
  ElMessage.success(`已回滚到 V${version.version_no}`)
}

const triggerSync = async () => {
  try {
    await ElMessageBox.confirm(
      '确认重新扫描 Skill 目录并刷新运行时吗？',
      '刷新 Skill 目录',
      {
        type: 'warning',
        confirmButtonText: '开始刷新',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  syncLoading.value = true
  try {
    syncResult.value = await dataagentApi.syncSkills()
    await loadDocuments()
    if (selectedDocumentId.value) {
      await loadDocument(selectedDocumentId.value)
    }
    ElMessage.success('Skill 目录已刷新')
  } finally {
    syncLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadDocuments()])
})
</script>
