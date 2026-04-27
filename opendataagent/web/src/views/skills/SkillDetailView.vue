<template>
  <ProductPageShell title="Skill 详情" description="">
    <template #actions>
      <button type="button" class="oda-btn-secondary" @click="goBack">
        <ArrowLeft class="h-4 w-4" />
        返回 Skills
      </button>

      <button
        v-if="skillItem && !skillItem.installed"
        type="button"
        class="oda-btn-primary"
        :disabled="installing"
        @click="installSkill"
      >
        <Download class="h-4 w-4" />
        {{ installing ? '安装中' : '安装 Skill' }}
      </button>

      <button type="button" class="oda-btn-secondary" :disabled="syncLoading" @click="triggerSync">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': syncLoading }" />
        {{ syncLoading ? '刷新中' : '刷新目录' }}
      </button>
    </template>

    <template #sidebar>
      <section class="oda-card p-5">
        <div v-if="skillItem" class="border-b border-slate-200 pb-5">
          <div class="flex items-start gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
              <component :is="iconForItem(skillItem)" class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <div class="text-base font-semibold text-gray-900">{{ skillItem.name }}</div>
              <div class="mt-1 text-sm leading-relaxed text-gray-500">{{ skillItem.description || '暂无描述' }}</div>
            </div>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <span :class="skillEnabled ? 'oda-chip-success' : 'oda-chip-neutral'">
              {{ skillEnabled ? '已激活' : (skillItem.installed ? '已安装' : '未安装') }}
            </span>
            <span class="oda-chip">{{ skillItem.source === 'managed' ? '本地导入' : '内置 Skill' }}</span>
            <span v-if="skillItem.version" class="oda-chip">{{ skillItem.version }}</span>
          </div>

          <div class="mt-4 text-xs leading-relaxed text-gray-400">{{ skillItem.folder }}</div>
        </div>

        <div class="mt-5">
          <div class="flex items-center justify-between">
            <div class="text-base font-semibold text-gray-900">文件树</div>
            <span class="oda-chip">{{ filteredDocuments.length }}</span>
          </div>
          <div class="mt-1 text-sm leading-relaxed text-gray-500">
            左侧按文件夹浏览，右侧查看和编辑当前文件。
          </div>
        </div>

        <div class="mt-4">
          <input
            v-model="searchKeyword"
            class="oda-input"
            type="text"
            placeholder="搜索文件名或路径"
          >
        </div>

        <div class="mt-5 rounded-lg border border-slate-200 bg-slate-50/70 p-3">
          <div class="mb-3 flex items-center gap-2 text-sm font-medium text-gray-700">
            <FolderTree class="h-4 w-4 text-gray-400" />
            <span>{{ folder }}</span>
          </div>

          <div v-if="treeNodes.length" class="space-y-1">
            <SkillFileTreeNode
              v-for="node in treeNodes"
              :key="node.key"
              :node="node"
              :selected-document-id="selectedDocumentId || ''"
              @select="loadDocument"
            />
          </div>

          <div v-else class="rounded-md border border-dashed border-slate-200 bg-white px-3 py-5 text-center text-sm text-gray-500">
            当前 Skill 还没有可展示的文件。
          </div>
        </div>
      </section>
    </template>

    <template v-if="skillItem">
      <section class="oda-card p-6">
        <div class="flex flex-col gap-5 border-b border-slate-200 pb-5 xl:flex-row xl:items-start xl:justify-between">
          <div class="min-w-0">
            <div class="text-xl font-semibold tracking-tight text-gray-900">
              {{ detail ? displayName(detail) : skillItem.name }}
            </div>
            <div class="mt-2 text-sm leading-relaxed text-gray-500">
              {{ detail?.relative_path || `${folder}/SKILL.md` }}
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="oda-chip">{{ skillItem.source === 'managed' ? '本地导入' : '内置 Skill' }}</span>
              <span v-if="detail" class="oda-chip">{{ detail.content_type }}</span>
              <span v-if="detail" :class="detail.enabled ? 'oda-chip-success' : 'oda-chip-neutral'">
                {{ detail.enabled ? '已激活' : '已停用' }}
              </span>
              <span v-if="currentVersionLabel !== '-'" class="oda-chip">{{ currentVersionLabel }}</span>
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <div v-if="primaryDocument" class="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50/70 px-4 py-2.5">
              <span class="text-sm font-medium text-gray-600">启用 Skill</span>
              <el-switch
                :model-value="skillEnabled"
                :loading="runtimeUpdating"
                @update:model-value="toggleSkillEnabled"
              />
            </div>
            <button type="button" class="oda-btn-secondary" :disabled="!detail" @click="openCompareDialog()">
              <GitCompareArrows class="h-4 w-4" />
              版本比对
            </button>
            <button
              v-if="detail?.source === 'managed'"
              type="button"
              class="oda-btn-danger"
              @click="deleteDocument"
            >
              <Trash2 class="h-4 w-4" />
              删除文件
            </button>
            <button type="button" class="oda-btn-secondary" :disabled="!editorDirty" @click="resetEditor">
              <RotateCcw class="h-4 w-4" />
              重置
            </button>
            <button
              type="button"
              class="oda-btn-primary"
              :disabled="!detail || !editorDirty || saveLoading || detail.editable === false"
              @click="saveDocument"
            >
              <Save class="h-4 w-4" />
              {{ saveLoading ? '保存中' : '保存' }}
            </button>
          </div>
        </div>

        <div class="mt-5 grid gap-4 lg:grid-cols-3">
          <div class="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">Skill 文件夹</div>
            <div class="mt-2 text-sm font-medium text-gray-900">{{ folder }}</div>
            <div class="mt-1 text-sm text-gray-500">{{ filteredDocuments.length }} 个文件</div>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">最近更新</div>
            <div class="mt-2 text-sm font-medium text-gray-900">{{ detail ? formatTime(detail.updated_at) : '-' }}</div>
            <div class="mt-1 text-sm text-gray-500">{{ detail?.last_change_summary || '最近一次更新未填写说明' }}</div>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
            <div class="text-xs font-semibold uppercase tracking-[0.08em] text-gray-400">文件状态</div>
            <div class="mt-2 text-sm font-medium text-gray-900">
              {{ detail?.editable === false ? '只读' : '可编辑' }}
            </div>
            <div class="mt-1 text-sm text-gray-500">当前文件的保存和版本都在右侧管理。</div>
          </div>
        </div>

        <div v-if="detail" class="mt-5">
          <label class="mb-2 block text-sm font-medium text-gray-700">本次修改说明</label>
          <input
            v-model="changeSummary"
            class="oda-input"
            type="text"
            maxlength="120"
            placeholder="例如：补充文件树视图的页面说明"
          >
        </div>

        <div class="mt-5 rounded-lg border border-slate-200 bg-white">
          <TextCodeEditor
            v-if="detail"
            v-model="editorContent"
            :read-only="detail.editable === false"
            :placeholder="detail.content_type === 'json' ? '请输入 JSON 内容' : '请输入文件内容'"
          />
          <div v-else class="px-4 py-10 text-center text-sm text-gray-500">
            请先从左侧文件树选择一个文件。
          </div>
        </div>
      </section>

      <section v-if="detail" class="oda-card p-6">
        <div class="flex flex-col gap-2 border-b border-slate-200 pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="oda-section-title">版本历史</div>
            <div class="mt-1 text-sm text-gray-500">查看当前文件的版本记录，并支持回滚。</div>
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
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-slate-100 text-gray-500">
        <FileCode2 class="h-6 w-6" />
      </div>
      <div class="mt-4 text-lg font-semibold text-gray-900">没有找到这个 Skill</div>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-gray-600">
        这个 Skill 可能已被删除，或者当前目录尚未同步。你可以返回 Skills 列表重新选择。
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
          <div class="rounded-lg border border-slate-200 bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">{{ compareResult.left_label }}</div>
            <TextCodeEditor :model-value="compareResult.left_content" read-only />
          </div>
          <div class="rounded-lg border border-slate-200 bg-white p-4">
            <div class="mb-3 text-sm font-semibold text-gray-900">{{ compareResult.right_label }}</div>
            <TextCodeEditor :model-value="compareResult.right_content" read-only />
          </div>
        </div>

        <div v-if="compareResult" class="rounded-lg border border-slate-200 bg-white p-4">
          <div class="mb-3 text-sm font-semibold text-gray-900">Unified Diff</div>
          <TextCodeEditor :model-value="compareResult.diff_text" read-only />
        </div>
      </div>
    </el-dialog>
  </ProductPageShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  ArrowLeft,
  Blocks,
  Download,
  FileCode2,
  FolderTree,
  GitCompareArrows,
  LayoutGrid,
  RefreshCw,
  RotateCcw,
  Save,
  Sparkles,
  Trash2,
  Wrench
} from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import ProductPageShell from '@/components/ProductPageShell.vue'
import TextCodeEditor from '@/components/TextCodeEditor.vue'
import SkillFileTreeNode from './SkillFileTreeNode.vue'
import { dataagentApi } from '@/api/dataagent'
import { marketApi } from '@/api/market'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const installing = ref(false)
const syncLoading = ref(false)
const saveLoading = ref(false)
const compareLoading = ref(false)
const runtimeUpdating = ref(false)
const searchKeyword = ref('')

const skillItem = ref(null)
const documents = ref([])
const selectedDocumentId = ref(null)
const detail = ref(null)
const editorContent = ref('')
const changeSummary = ref('')
const compareDialogVisible = ref(false)
const compareResult = ref(null)
const leftCompareVersionId = ref(null)
const rightCompareVersionId = ref(null)

const folder = computed(() => decodeURIComponent(String(route.params.folder || '')).trim())

const filteredDocuments = computed(() => {
  const keyword = String(searchKeyword.value || '').trim().toLowerCase()
  return documents.value.filter((item) => {
    if (String(item.folder || '') !== folder.value) return false
    if (!keyword) return true
    return String(item.file_name || '').toLowerCase().includes(keyword)
      || String(item.relative_path || '').toLowerCase().includes(keyword)
  })
})

const primaryDocument = computed(() => {
  return filteredDocuments.value.find((item) => String(item.file_name || '').toUpperCase() === 'SKILL.MD')
    || filteredDocuments.value[0]
    || null
})

const skillEnabled = computed(() => primaryDocument.value?.enabled ?? false)

const treeNodes = computed(() => {
  const root = []
  const nodeMap = new Map()

  const ensureFolder = (parent, key, label) => {
    const mapKey = `folder:${key}`
    if (!nodeMap.has(mapKey)) {
      const node = { key: mapKey, label, type: 'folder', children: [] }
      nodeMap.set(mapKey, node)
      parent.push(node)
    }
    return nodeMap.get(mapKey)
  }

  for (const doc of filteredDocuments.value) {
    const relative = String(doc.relative_path || doc.file_name || '')
    const trimmed = relative.startsWith(`${folder.value}/`) ? relative.slice(folder.value.length + 1) : relative
    const segments = trimmed.split('/').filter(Boolean)
    let parent = root
    let path = folder.value

    for (let i = 0; i < segments.length; i += 1) {
      const segment = segments[i]
      const isFile = i === segments.length - 1
      path = `${path}/${segment}`
      if (isFile) {
        parent.push({
          key: `file:${doc.id}`,
          label: segment,
          type: 'file',
          documentId: doc.id
        })
      } else {
        const folderNode = ensureFolder(parent, path, segment)
        parent = folderNode.children
      }
    }
  }

  const sortNodes = (nodes) => {
    nodes.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
      return String(a.label).localeCompare(String(b.label))
    })
    for (const node of nodes) {
      if (node.children) sortNodes(node.children)
    }
    return nodes
  }

  return sortNodes(root)
})

const editorDirty = computed(() => !!detail.value && editorContent.value !== (detail.value.current_content || ''))

const currentVersionLabel = computed(() => {
  const current = (detail.value?.versions || []).find((item) => item.is_current)
  return current ? `V${current.version_no}` : '-'
})

const iconForItem = (item) => {
  const key = String(item?.folder || item?.name || '').toLowerCase()
  if (key.includes('frontend') || key.includes('ui')) return LayoutGrid
  if (key.includes('smoke') || key.includes('test')) return Sparkles
  if (key.includes('sql') || key.includes('data')) return Blocks
  return Wrench
}

const displayName = (row) => {
  const fileName = String(row?.file_name || row?.folder || '未命名')
  return fileName.replace(/\.(md|markdown|json)$/i, '')
}

const formatTime = (value) => {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

const findSkillItem = async () => {
  const items = await marketApi.listItems()
  const matched = items.find((item) => String(item.folder || '') === folder.value)
  skillItem.value = matched || null
}

const loadDocuments = async () => {
  documents.value = await dataagentApi.listSkillDocuments()
  const currentExists = filteredDocuments.value.find((item) => item.id === selectedDocumentId.value)
  const nextDocument = currentExists || primaryDocument.value
  if (nextDocument?.id) {
    await loadDocument(nextDocument.id)
    return
  }
  selectedDocumentId.value = null
  detail.value = null
  editorContent.value = ''
}

const loadDocument = async (documentId) => {
  selectedDocumentId.value = documentId
  const payload = await dataagentApi.getSkillDocument(documentId)
  detail.value = payload
  editorContent.value = payload?.current_content || ''
  changeSummary.value = ''
}

const loadPage = async () => {
  loading.value = true
  try {
    await Promise.all([findSkillItem(), loadDocuments()])
  } finally {
    loading.value = false
  }
}

const goBack = async () => {
  await router.push('/skills?tab=market')
}

const installSkill = async () => {
  if (!skillItem.value?.id) return
  installing.value = true
  try {
    await marketApi.install({ item_id: skillItem.value.id })
    ElMessage.success(`已安装 ${skillItem.value.name}`)
    await loadPage()
  } finally {
    installing.value = false
  }
}

const toggleSkillEnabled = async (enabled) => {
  if (!primaryDocument.value?.id) return
  runtimeUpdating.value = true
  try {
    await dataagentApi.updateSkillRuntime(primaryDocument.value.id, { enabled })
    const target = documents.value.find((item) => item.id === primaryDocument.value.id)
    if (target) target.enabled = Boolean(enabled)
    if (detail.value?.id === primaryDocument.value.id) detail.value.enabled = Boolean(enabled)
    ElMessage.success(enabled ? 'Skill 已启用' : 'Skill 已禁用')
  } finally {
    runtimeUpdating.value = false
  }
}

const saveDocument = async () => {
  if (!detail.value) return
  saveLoading.value = true
  try {
    const payload = await dataagentApi.updateSkillDocument(detail.value.id, {
      content: editorContent.value,
      change_summary: changeSummary.value || '详情页保存'
    })
    detail.value = payload
    editorContent.value = payload.current_content || ''
    changeSummary.value = ''
    await loadDocuments()
    ElMessage.success('文件已保存')
  } finally {
    saveLoading.value = false
  }
}

const deleteDocument = async () => {
  if (!detail.value?.id || detail.value.source !== 'managed') return
  try {
    await ElMessageBox.confirm(
      `确认删除 ${displayName(detail.value)} 吗？删除后会移除当前托管版本和版本历史。`,
      '删除文件',
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
  ElMessage.success('文件已删除')
  await loadPage()
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
    await dataagentApi.syncSkills()
    await loadPage()
    ElMessage.success('Skill 目录已刷新')
  } finally {
    syncLoading.value = false
  }
}

watch(() => route.params.folder, () => {
  searchKeyword.value = ''
  void loadPage()
})

onMounted(loadPage)
</script>
