<template>
  <ProductPageShell
    eyebrow="Skill Catalog"
    title="Skill 市场"
    description="浏览、导入和安装可用 Skill。优先展示可直接使用的能力，把目录细节和系统状态降到二级信息。"
  >
    <section class="oda-card p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="option in sourceOptions"
            :key="option.value || 'all'"
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition"
            :class="filters.source === option.value
              ? 'border-[#2f5f9f] bg-[#2f5f9f] text-white'
              : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50/70'"
            @click="setSourceFilter(option.value)"
          >
            <span>{{ option.label }}</span>
          </button>
        </div>

        <div class="lg:min-w-[420px]">
          <input
            v-model="filters.q"
            class="oda-input"
            type="text"
            placeholder="搜索 Skill 名称或描述"
            @change="loadItems"
          >
        </div>
      </div>
    </section>

    <section class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-3">
        <button type="button" class="oda-btn-primary" @click="openImportDialog">
          <Upload class="h-4 w-4" />
          导入 Skill
        </button>
        <button type="button" class="oda-btn-secondary" @click="loadItems">
          <RefreshCw class="h-4 w-4" />
          刷新目录
        </button>
      </div>
    </section>

    <section v-if="installedItems.length" class="space-y-4">
      <div class="oda-section-title">已安装</div>

      <div class="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
        <article
          v-for="item in installedItems"
          :key="item.id"
          class="oda-card cursor-pointer p-5 transition hover:border-slate-300"
          tabindex="0"
          @click="openSkillDetail(item)"
          @keydown.enter.prevent="openSkillDetail(item)"
          @keydown.space.prevent="openSkillDetail(item)"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <component :is="iconForItem(item)" class="h-5 w-5" />
              </div>
              <div class="min-w-0">
                <div class="text-base font-semibold text-gray-900">{{ item.name }}</div>
                <div class="mt-1 text-sm leading-relaxed text-gray-500">{{ shortCategory(item) }}</div>
              </div>
            </div>
            <span :class="item.enabled ? 'oda-chip-success' : 'oda-chip-neutral'">
              {{ item.enabled ? '已激活' : '已安装' }}
            </span>
          </div>

          <p class="mt-4 text-sm leading-relaxed text-gray-600">{{ item.description || '暂无描述' }}</p>

          <div class="mt-4 flex flex-wrap gap-2">
            <span v-if="item.source === 'managed'" class="oda-chip">本地导入</span>
            <span v-else class="oda-chip">内置 Skill</span>
            <span v-if="item.version" class="oda-chip">{{ item.version }}</span>
          </div>

          <div class="mt-5 flex items-center justify-between">
            <span class="text-xs text-gray-400" :title="item.folder">{{ item.folder }}</span>
            <button type="button" class="oda-btn-secondary h-10 px-3" @click.stop="openSkillDetail(item)">
              <Eye class="h-4 w-4" />
              打开
            </button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="availableItems.length" class="space-y-4">
      <div class="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
        <article
          v-for="item in availableItems"
          :key="item.id"
          class="oda-card cursor-pointer p-5 transition hover:border-slate-300"
          tabindex="0"
          @click="openSkillDetail(item)"
          @keydown.enter.prevent="openSkillDetail(item)"
          @keydown.space.prevent="openSkillDetail(item)"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <component :is="iconForItem(item)" class="h-5 w-5" />
              </div>
              <div class="min-w-0">
                <div class="text-base font-semibold text-gray-900">{{ item.name }}</div>
                <div class="mt-1 text-sm leading-relaxed text-gray-500">{{ shortCategory(item) }}</div>
              </div>
            </div>
            <span class="oda-chip">{{ item.source === 'managed' ? '本地导入' : '内置' }}</span>
          </div>

          <p class="mt-4 text-sm leading-relaxed text-gray-600">{{ item.description || '暂无描述' }}</p>

          <div class="mt-4 flex flex-wrap gap-2">
            <span v-if="item.enabled" class="oda-chip-success">已激活</span>
            <span v-if="item.version" class="oda-chip">{{ item.version }}</span>
          </div>

          <div class="mt-5 flex items-center justify-between gap-3">
            <button type="button" class="oda-btn-secondary h-10 px-3" @click.stop="openSkillDetail(item)">
              <Eye class="h-4 w-4" />
              打开
            </button>
            <button
              type="button"
              class="oda-btn-primary h-10 px-3"
              :disabled="installingId === item.id"
              @click.stop="installItem(item)"
            >
              <Download class="h-4 w-4" />
              {{ installingId === item.id ? '安装中' : '安装' }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="!loading && !items.length" class="oda-card p-10 text-center">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
        <PackageSearch class="h-6 w-6" />
      </div>
      <div class="mt-4 text-lg font-semibold text-gray-900">还没有可展示的 Skill</div>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-gray-600">
        当前筛选下没有可用条目。你可以导入一个新的 Skill，或者切换筛选查看其他来源。
      </p>
    </section>

    <el-dialog v-model="importDialogVisible" title="导入 Skill 包" width="560px">
      <div class="space-y-5">
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">文件夹名称</label>
          <input
            v-model="importForm.folder"
            class="oda-input"
            type="text"
            placeholder="可选，不填则从文件名或压缩包目录推断"
          >
        </div>
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">上传文件</label>
          <input
            ref="fileInputRef"
            class="block w-full rounded-lg border border-dashed border-slate-300 bg-slate-50/70 px-4 py-4 text-sm text-slate-700"
            type="file"
            accept=".zip,.md,.markdown,text/markdown,application/zip"
            @change="handleImportFileChange"
          >
          <div class="mt-2 text-sm text-gray-500">{{ importForm.file?.name || '请选择 zip 包或 markdown 文件' }}</div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button type="button" class="oda-btn-secondary" @click="importDialogVisible = false">取消</button>
          <button type="button" class="oda-btn-primary" :disabled="importing" @click="submitImport">
            <Upload class="h-4 w-4" />
            {{ importing ? '导入中' : '导入' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </ProductPageShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Blocks,
  Download,
  Eye,
  LayoutGrid,
  PackageSearch,
  RefreshCw,
  Sparkles,
  Upload,
  Wrench
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import ProductPageShell from '@/components/ProductPageShell.vue'
import { marketApi } from '@/api/market'

const router = useRouter()
const loading = ref(false)
const installingId = ref('')
const importDialogVisible = ref(false)
const importing = ref(false)
const fileInputRef = ref(null)
const items = ref([])
const filters = reactive({
  q: '',
  source: ''
})
const importForm = reactive({
  folder: '',
  file: null
})

const installedItems = computed(() => items.value.filter((item) => item.installed))
const availableItems = computed(() => items.value.filter((item) => !item.installed))
const sourceOptions = computed(() => {
  return [
    { label: '全部', value: '' },
    { label: '内置', value: 'bundled' },
    { label: '本地导入', value: 'managed' }
  ]
})

const shortCategory = (item) => item.category || item.summary || '通用能力'

const iconForItem = (item) => {
  const key = String(item.folder || item.name || '').toLowerCase()
  if (key.includes('frontend') || key.includes('ui')) return LayoutGrid
  if (key.includes('smoke') || key.includes('test')) return Sparkles
  if (key.includes('sql') || key.includes('data')) return Blocks
  return Wrench
}

const setSourceFilter = (source) => {
  filters.source = source
  loadItems()
}

const loadItems = async () => {
  loading.value = true
  try {
    items.value = await marketApi.listItems(filters)
  } catch (error) {
    ElMessage.error(error.message || '加载 Skill 市场失败')
  } finally {
    loading.value = false
  }
}

const openSkillDetail = async (item) => {
  await router.push(`/skills/detail/${encodeURIComponent(item.folder)}`)
}

const installItem = async (item) => {
  installingId.value = item.id
  try {
    await marketApi.install({ item_id: item.id })
    ElMessage.success(`已安装 ${item.name}`)
    await loadItems()
  } catch (error) {
    ElMessage.error(error.message || '安装 Skill 失败')
  } finally {
    installingId.value = ''
  }
}

const openImportDialog = () => {
  importForm.folder = ''
  importForm.file = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  importDialogVisible.value = true
}

const handleImportFileChange = (event) => {
  importForm.file = event?.target?.files?.[0] || null
}

const submitImport = async () => {
  if (!importForm.file) {
    ElMessage.error('请先选择要导入的文件')
    return
  }
  const formData = new FormData()
  formData.append('file', importForm.file)
  if (String(importForm.folder || '').trim()) {
    formData.append('folder', String(importForm.folder).trim())
  }
  importing.value = true
  try {
    const item = await marketApi.importPackage(formData)
    importDialogVisible.value = false
    ElMessage.success(`已导入 ${item.name || item.folder}`)
    await loadItems()
  } catch (error) {
    ElMessage.error(error.message || '导入 Skill 失败')
  } finally {
    importing.value = false
  }
}

onMounted(loadItems)
</script>
