<template>
  <ProductPageShell
    eyebrow="MCP Servers"
    title="MCP 管理"
    description="管理当前工作台可连接的 MCP 服务。优先展示哪些服务可用、如何编辑，以及下一步能不能直接接入会话。"
  >
    <section class="oda-card p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="option in filterOptions"
            :key="option.value"
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition"
            :class="activeFilter === option.value
              ? 'border-[#2f5f9f] bg-[#2f5f9f] text-white'
              : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'"
            @click="activeFilter = option.value"
          >
            <span>{{ option.label }}</span>
          </button>
        </div>

        <div class="lg:min-w-[420px]">
          <input
            v-model="searchKeyword"
            class="oda-input"
            type="text"
            placeholder="搜索服务名称、命令或地址"
          >
        </div>
      </div>
    </section>

    <section class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-3">
        <button type="button" class="oda-btn-primary" @click="openCreate">
          <Plus class="h-4 w-4" />
          新增服务
        </button>
        <button type="button" class="oda-btn-secondary" @click="loadServers">
          <RefreshCw class="h-4 w-4" />
          刷新列表
        </button>
      </div>
    </section>

    <section v-if="!loading && !filteredServers.length" class="oda-card p-10 text-center">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100 text-gray-500">
        <PlugZap class="h-6 w-6" />
      </div>
      <div class="mt-4 text-lg font-semibold text-gray-900">还没有可用的 MCP 服务</div>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-gray-600">
        你可以新增一个本地进程服务，或者接入一个远程 MCP 服务地址。
      </p>
    </section>

    <section class="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
      <article
        v-for="row in filteredServers"
        :key="row.id"
        class="oda-card p-5"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-start gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
              <Server class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <div class="text-base font-semibold text-gray-900">{{ row.name }}</div>
              <div class="mt-1 text-sm leading-relaxed text-gray-500">{{ typeSummary(row.connection_type) }}</div>
            </div>
          </div>
          <span :class="row.enabled ? 'oda-chip-success' : 'oda-chip-neutral'">
            {{ row.enabled ? '已启用' : '已停用' }}
          </span>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <span v-if="row.tool_prefix" class="oda-chip">{{ row.tool_prefix }}</span>
          <span class="oda-chip">{{ typeSummary(row.connection_type) }}</span>
        </div>

        <div class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm leading-relaxed text-gray-600">
          {{ summarizeEndpoint(row) }}
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <button type="button" class="oda-btn-secondary h-10 px-3" @click="openEdit(row)">
            <PencilLine class="h-4 w-4" />
            编辑
          </button>
          <el-dropdown trigger="click" placement="bottom-end">
            <button type="button" class="oda-icon-button h-10 w-10">
              <Ellipsis class="h-4 w-4" />
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :disabled="testingId === row.id" @click="testServer(row)">
                  {{ testingId === row.id ? '测试中' : '测试连接' }}
                </el-dropdown-item>
                <el-dropdown-item @click="toggleEnabled(row)">
                  {{ row.enabled ? '停用服务' : '启用服务' }}
                </el-dropdown-item>
                <el-dropdown-item class="!text-red-600" @click="removeServer(row)">
                  删除服务
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </article>
    </section>

    <el-dialog v-model="dialogVisible" :title="draft.id ? '编辑 MCP 服务' : '新增 MCP 服务'" width="760px">
      <div class="grid gap-5 xl:grid-cols-2">
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">名称</label>
          <input v-model="draft.name" class="oda-input" type="text">
        </div>
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">Tool Prefix</label>
          <input v-model="draft.tool_prefix" class="oda-input" type="text" placeholder="例如 portal">
        </div>
        <div class="xl:col-span-2">
          <label class="mb-2 block text-sm font-medium text-gray-700">连接方式</label>
          <div class="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              class="rounded-lg border px-4 py-3 text-left transition"
              :class="draft.connection_type === 'process'
                ? 'border-[#2f5f9f] bg-[#2f5f9f] text-white'
                : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
              @click="draft.connection_type = 'process'"
            >
              <div class="text-sm font-medium">本地进程</div>
              <div class="mt-1 text-xs" :class="draft.connection_type === 'process' ? 'text-slate-100' : 'text-gray-500'">
                适合 CLI、脚本和受控命令
              </div>
            </button>
            <button
              type="button"
              class="rounded-lg border px-4 py-3 text-left transition"
              :class="draft.connection_type === 'remote'
                ? 'border-[#2f5f9f] bg-[#2f5f9f] text-white'
                : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
              @click="draft.connection_type = 'remote'"
            >
              <div class="text-sm font-medium">远程服务</div>
              <div class="mt-1 text-xs" :class="draft.connection_type === 'remote' ? 'text-slate-100' : 'text-gray-500'">
                适合已有网关或 HTTP MCP 服务
              </div>
            </button>
          </div>
        </div>
        <div class="xl:col-span-2">
          <label class="mb-2 flex items-center gap-3 text-sm font-medium text-gray-700">
            <span>启用</span>
            <el-switch v-model="draft.enabled" />
          </label>
        </div>

        <template v-if="draft.connection_type === 'process'">
          <div class="xl:col-span-2">
            <label class="mb-2 block text-sm font-medium text-gray-700">Command</label>
            <input v-model="draft.command" class="oda-input" type="text">
          </div>
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Args</label>
            <textarea v-model="draft.args_text" class="oda-textarea min-h-[140px]" />
          </div>
          <div>
            <label class="mb-2 block text-sm font-medium text-gray-700">Env JSON</label>
            <textarea v-model="draft.env_text" class="oda-textarea min-h-[140px]" />
          </div>
        </template>

        <template v-else>
          <div class="xl:col-span-2">
            <label class="mb-2 block text-sm font-medium text-gray-700">URL</label>
            <input v-model="draft.url" class="oda-input" type="text">
          </div>
          <div class="xl:col-span-2">
            <label class="mb-2 block text-sm font-medium text-gray-700">Headers JSON</label>
            <textarea v-model="draft.headers_text" class="oda-textarea min-h-[160px]" />
          </div>
        </template>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <button type="button" class="oda-btn-secondary" @click="dialogVisible = false">取消</button>
          <button type="button" class="oda-btn-primary" @click="saveDraft">
            <Save class="h-4 w-4" />
            保存
          </button>
        </div>
      </template>
    </el-dialog>
  </ProductPageShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Ellipsis,
  PencilLine,
  PlugZap,
  Plus,
  RefreshCw,
  Save,
  Server
} from 'lucide-vue-next'
import ProductPageShell from '@/components/ProductPageShell.vue'
import { mcpApi } from '@/api/mcp'

const loading = ref(false)
const testingId = ref('')
const servers = ref([])
const dialogVisible = ref(false)
const searchKeyword = ref('')
const activeFilter = ref('all')
const draft = reactive(resetDraft())

function resetDraft() {
  return {
    id: '',
    name: '',
    connection_type: 'process',
    tool_prefix: '',
    enabled: true,
    command: '',
    args_text: '',
    env_text: '{\n  \n}',
    url: '',
    headers_text: '{\n  \n}'
  }
}

const assignDraft = (payload = {}) => {
  Object.assign(draft, resetDraft(), {
    ...payload,
    args_text: Array.isArray(payload.args) ? payload.args.join('\n') : '',
    env_text: JSON.stringify(payload.env || {}, null, 2),
    headers_text: JSON.stringify(payload.headers || {}, null, 2)
  })
}

const filteredServers = computed(() => {
  const keyword = String(searchKeyword.value || '').trim().toLowerCase()
  return servers.value.filter((row) => {
    if (activeFilter.value === 'enabled' && !row.enabled) return false
    if (activeFilter.value === 'disabled' && row.enabled) return false
    if (activeFilter.value === 'process' && row.connection_type !== 'process') return false
    if (activeFilter.value === 'remote' && row.connection_type !== 'remote') return false
    if (!keyword) return true
    const haystack = [row.name, row.tool_prefix, row.command, row.url].join(' ').toLowerCase()
    return haystack.includes(keyword)
  })
})

const filterOptions = computed(() => [
  { label: '全部', value: 'all' },
  { label: '启用中', value: 'enabled' },
  { label: '已停用', value: 'disabled' },
  { label: '本地进程', value: 'process' },
  { label: '远程服务', value: 'remote' }
])

const typeSummary = (value) => value === 'process' ? '本地进程' : '远程服务'

const summarizeEndpoint = (row) => {
  if (row.connection_type === 'process') {
    const args = Array.isArray(row.args) ? row.args.join(' ') : ''
    return [row.command, args].filter(Boolean).join(' ')
  }
  return row.url || '未配置远程地址'
}

const loadServers = async () => {
  loading.value = true
  try {
    servers.value = await mcpApi.listServers()
  } catch (error) {
    ElMessage.error(error.message || '加载 MCP 列表失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  assignDraft()
  dialogVisible.value = true
}

const openEdit = (row) => {
  assignDraft(row)
  dialogVisible.value = true
}

const saveDraft = async () => {
  let env = {}
  let headers = {}
  try {
    env = JSON.parse(draft.env_text || '{}')
    headers = JSON.parse(draft.headers_text || '{}')
  } catch (_error) {
    ElMessage.error('Env / Headers 必须是合法 JSON')
    return
  }

  const payload = {
    name: draft.name,
    connection_type: draft.connection_type,
    tool_prefix: draft.tool_prefix,
    enabled: Boolean(draft.enabled),
    command: draft.command,
    args: String(draft.args_text || '').split('\n').map((item) => item.trim()).filter(Boolean),
    env,
    url: draft.url,
    headers
  }

  try {
    if (draft.id) {
      await mcpApi.updateServer(draft.id, payload)
    } else {
      await mcpApi.createServer(payload)
    }
    dialogVisible.value = false
    ElMessage.success('MCP 服务已保存')
    await loadServers()
  } catch (error) {
    ElMessage.error(error.message || '保存 MCP 服务失败')
  }
}

const removeServer = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除 MCP 服务 ${row.name} 吗？`, '删除确认', {
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    await mcpApi.deleteServer(row.id)
    ElMessage.success('MCP 服务已删除')
    await loadServers()
  } catch (error) {
    ElMessage.error(error.message || '删除 MCP 服务失败')
  }
}

const toggleEnabled = async (row) => {
  try {
    await mcpApi.updateServer(row.id, { enabled: !row.enabled })
    await loadServers()
  } catch (error) {
    ElMessage.error(error.message || '更新 MCP 状态失败')
  }
}

const testServer = async (row) => {
  testingId.value = row.id
  try {
    const result = await mcpApi.testServer(row.id)
    ElMessage.success(result.message || 'MCP 测试通过')
  } catch (error) {
    ElMessage.error(error.message || 'MCP 测试失败')
  } finally {
    testingId.value = ''
  }
}

onMounted(loadServers)
</script>
