<template>
  <ProductPageShell
    eyebrow="Model Settings"
    title="模型设置"
    description="左侧选择供应商，右侧维护连接配置和模型。"
    sidebar-grid-class="xl:grid-cols-[30%_minmax(0,1fr)]"
  >
    <template #sidebar>
      <section class="oda-card p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-base font-semibold text-gray-900">供应商</div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="oda-btn-secondary h-9 px-3" @click="openProviderDialog">
              <Plus class="h-4 w-4" />
              新增供应商
            </button>
          </div>
        </div>

        <div class="mt-5 overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div class="grid grid-cols-[minmax(0,1fr)_84px_84px] gap-3 border-b border-slate-200 bg-slate-50/70 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-gray-500">
            <span>供应商</span>
            <span class="text-center">启用</span>
            <span class="text-center">默认</span>
          </div>

          <div class="divide-y divide-slate-200">
            <div
              v-for="provider in orderedProviders"
              :key="provider.provider_id"
              class="grid grid-cols-[minmax(0,1fr)_84px_84px] items-center gap-3 px-4 py-3 transition"
              :class="provider.provider_id === inspectedProviderId ? 'bg-slate-100' : 'bg-white'"
            >
              <button
                type="button"
                class="min-w-0 text-left"
                @click="selectProvider(provider.provider_id)"
              >
                <div class="flex items-center gap-2">
                  <div class="truncate text-sm font-semibold text-gray-900">
                    {{ provider.display_name || provider.provider_id }}
                  </div>
                  <span
                    v-if="provider.provider_id === inspectedProviderId"
                    class="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                  >
                    当前
                  </span>
                </div>
              </button>

              <div class="flex justify-center" @click.stop>
                <el-switch
                  :model-value="provider.enabled"
                  @update:model-value="toggleProviderEnabled(provider, $event)"
                />
              </div>

              <div class="flex justify-center" @click.stop>
                <el-switch
                  :model-value="provider.provider_id === form.default_provider_id"
                  :disabled="!provider.enabled"
                  @update:model-value="toggleProviderDefault(provider, $event)"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <template v-if="selectedProvider">
      <form class="oda-card p-6" @submit.prevent>
        <div class="flex flex-col gap-5 border-b border-slate-200 pb-5 xl:flex-row xl:items-start xl:justify-between">
          <div class="min-w-0">
            <div class="text-xl font-semibold tracking-tight text-gray-900">
              {{ selectedProvider.display_name || selectedProvider.provider_id }}
            </div>
            <div class="mt-3 flex flex-wrap gap-2">
              <span :class="selectedProvider.enabled ? 'oda-chip-success' : 'oda-chip-neutral'">
                {{ selectedProvider.enabled ? '可用' : '已停用' }}
              </span>
              <span v-if="selectedProvider.provider_id === form.default_provider_id" class="oda-chip-warning">当前默认供应商</span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              v-if="canDeleteSelectedProvider"
              type="button"
              class="oda-btn-secondary h-10 px-3 text-red-600"
              @click="removeSelectedProvider"
            >
              <Trash2 class="h-4 w-4" />
              删除供应商
            </button>
          </div>
        </div>

        <div v-if="selectedProvider.provider_id !== 'mock'" class="mt-5 border-t border-slate-200 pt-5">
          <div class="text-base font-semibold text-gray-900">Base URL</div>
          <div class="mt-2 text-sm leading-relaxed text-gray-500">
            当前供应商的模型请求地址。
          </div>
          <div class="mt-4 space-y-5">
            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">Base URL</label>
              <input
                v-model="selectedProvider.base_url"
                class="oda-input"
                type="text"
                autocomplete="url"
                :placeholder="providerBaseURLPlaceholder"
              >
            </div>

            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">API Token</label>
              <input
                v-model="selectedProvider.api_token"
                class="oda-input"
                type="password"
                autocomplete="off"
                spellcheck="false"
                :placeholder="providerTokenPlaceholder"
              >
            </div>
          </div>
        </div>

        <div v-else class="mt-5 border-t border-slate-200 pt-5 text-sm leading-relaxed text-gray-600">
          Mock Runtime 仅用于本地调试，不需要配置 Base URL 或 API Token。
        </div>

        <div class="mt-5 border-t border-slate-200 pt-5">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div class="min-w-0">
              <div class="text-base font-semibold text-gray-900">模型</div>
              <div class="mt-2 text-sm leading-relaxed text-gray-500">
                直接维护当前供应商的模型启用状态和默认模型。
              </div>
            </div>
            <button type="button" class="oda-btn-secondary h-10 px-3" @click="addModelPrompt">
              <Plus class="h-4 w-4" />
              新增模型
            </button>
          </div>

          <div class="mt-4">
            <div class="grid grid-cols-[minmax(0,1fr)_112px_112px_auto] gap-3 border-b border-slate-200 px-1 py-3 text-xs font-medium uppercase tracking-[0.08em] text-gray-500">
              <span>模型名称</span>
              <span class="text-center">是否启用</span>
              <span class="text-center">是否默认</span>
              <span class="text-right">操作</span>
            </div>

            <div v-if="(selectedProvider.models || []).length" class="divide-y divide-slate-200">
              <div
                v-for="model in selectedProvider.models || []"
                :key="model.name"
                class="grid grid-cols-[minmax(0,1fr)_112px_112px_auto] items-center gap-3 px-1 py-3"
              >
                <div class="min-w-0">
                  <div class="truncate text-sm font-medium text-gray-900">{{ model.name }}</div>
                </div>

                <div class="flex justify-center">
                  <el-switch
                    :model-value="model.enabled"
                    @update:model-value="toggleModelEnabled(model, $event)"
                  />
                </div>

                <div class="flex justify-center">
                  <el-switch
                    :model-value="isProviderDefaultModel(model)"
                    :disabled="!selectedProvider.enabled || !model.enabled"
                    @update:model-value="toggleModelDefault(model, $event)"
                  />
                </div>

                <div class="flex items-center justify-end gap-2">
                  <button
                    v-if="(selectedProvider.models || []).length > 1"
                    type="button"
                    class="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 hover:text-slate-700"
                    @click="removeModel(model)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="px-1 py-6 text-sm text-gray-500">
              当前供应商还没有模型，请先新增一个模型。
            </div>
          </div>
        </div>
      </form>
    </template>

    <section v-else class="oda-card p-10 text-center">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
        <Cpu class="h-6 w-6" />
      </div>
      <div class="mt-4 text-lg font-semibold text-gray-900">还没有可用的供应商配置</div>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-gray-600">
        当前没有可用的 Provider 和模型，请先补充配置后再回来设置默认值。
      </p>
    </section>

    <el-dialog v-model="providerDialogVisible" title="新增供应商" width="min(560px, calc(100vw - 32px))">
      <div class="space-y-5">
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">供应商类型</label>
          <div class="grid gap-3 sm:grid-cols-3">
            <button
              v-for="option in providerTypeOptions"
              :key="option.value"
              type="button"
              class="rounded-lg border px-4 py-3 text-left transition"
              :class="providerDraft.provider_type === option.value
                ? 'border-[#2f5f9f] bg-[#2f5f9f] text-white'
                : 'border-slate-200 bg-white text-gray-700 hover:bg-slate-50/70'"
              @click="selectProviderType(option.value)"
            >
              <div class="text-sm font-medium">{{ option.label }}</div>
              <div class="mt-1 text-xs" :class="providerDraft.provider_type === option.value ? 'text-slate-100' : 'text-gray-500'">
                {{ option.hint }}
              </div>
            </button>
          </div>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">显示名称</label>
          <input
            v-model="providerDraft.display_name"
            class="oda-input"
            type="text"
            autocomplete="organization"
            placeholder="例如 Anthropic China"
            @input="syncProviderIDFromDraft"
          >
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">供应商标识</label>
          <input
            v-model="providerDraft.provider_id"
            class="oda-input"
            type="text"
            autocomplete="off"
            placeholder="例如 anthropic-cn"
            @input="providerIDTouched = true"
          >
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700">初始模型</label>
          <input
            v-model="providerDraft.initial_model"
            class="oda-input"
            type="text"
            autocomplete="off"
            placeholder="例如 claude-sonnet-4-5-20250929"
          >
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button type="button" class="oda-btn-secondary" @click="providerDialogVisible = false">取消</button>
          <button type="button" class="oda-btn-primary" @click="addProvider">
            <Plus class="h-4 w-4" />
            新增
          </button>
        </div>
      </template>
    </el-dialog>

  </ProductPageShell>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu, Plus, Trash2 } from 'lucide-vue-next'
import ProductPageShell from '@/components/ProductPageShell.vue'
import { settingsApi } from '@/api/settings'

const saving = ref(false)
const hydrating = ref(false)
const inspectedProviderId = ref('')
const providerDialogVisible = ref(false)
const providerIDTouched = ref(false)
const lastPersistedSnapshot = ref('')
const form = reactive({
  default_provider_id: '',
  default_model: '',
  managed_skills_dir: '',
  skills_root_dir: '',
  session_mysql_database: '',
  admin_token: '',
  providers: []
})
const providerDraft = reactive(resetProviderDraft())

const builtInProviderIDs = ['mock', 'anthropic', 'openai', 'anthropic_compat']
const providerTypeOptions = [
  { value: 'anthropic', label: 'Anthropic', hint: '官方或代理 Anthropic 接口' },
  { value: 'openai', label: 'OpenAI Compatible', hint: 'OpenAI 或兼容网关' },
  { value: 'anthropic_compat', label: 'Anthropic Compat', hint: '非标准 Claude 兼容网关' }
]

const orderedProviders = computed(() => {
  const providers = Array.isArray(form.providers) ? [...form.providers] : []
  return providers.sort((a, b) => {
    const aDefault = a.provider_id === form.default_provider_id ? 1 : 0
    const bDefault = b.provider_id === form.default_provider_id ? 1 : 0
    if (aDefault !== bDefault) return bDefault - aDefault
    const aEnabled = a.enabled ? 1 : 0
    const bEnabled = b.enabled ? 1 : 0
    if (aEnabled !== bEnabled) return bEnabled - aEnabled
    return String(a.display_name || a.provider_id).localeCompare(String(b.display_name || b.provider_id))
  })
})

const selectedProvider = computed(() => (
  orderedProviders.value.find((item) => item.provider_id === inspectedProviderId.value) || null
))

const selectedProviderType = computed(() => (
  selectedProvider.value?.provider_type || selectedProvider.value?.provider_id || ''
))
const providerBaseURLPlaceholder = computed(() => {
  if (!selectedProviderType.value) return 'https://api.example.com'
  switch (selectedProviderType.value) {
    case 'anthropic':
      return '留空则使用官方 Anthropic 地址'
    case 'openai':
      return '留空则使用官方 OpenAI Compatible 地址'
    case 'anthropic_compat':
      return '例如 https://wzw.pp.ua'
    default:
      return 'https://api.example.com'
  }
})
const providerTokenPlaceholder = computed(() => (
  selectedProviderType.value === 'anthropic_compat'
    ? '填写兼容网关 Token'
    : '填写当前 provider 的 API Token'
))
const canDeleteSelectedProvider = computed(() => (
  !!selectedProvider.value && !builtInProviderIDs.includes(selectedProvider.value.provider_id)
))

const normalizeProviderRows = (items) => (
  Array.isArray(items)
    ? items.map((item) => ({
      ...item,
      provider_type: String(item?.provider_type || item?.provider_id || '').trim(),
      base_url: String(item?.base_url || '').trim(),
      api_token: String(item?.api_token || '').trim(),
      models: normalizeModelRows(item?.models),
      default_model: normalizeDefaultModel(item?.default_model, item?.models)
    }))
    : []
)

const normalizeModelRows = (items) => {
  if (!Array.isArray(items)) return []
  const seen = new Set()
  return items.reduce((out, item) => {
    const name = String(typeof item === 'string' ? item : item?.name || '').trim()
    if (!name) return out
    const key = name.toLowerCase()
    if (seen.has(key)) return out
    seen.add(key)
    out.push({
      name,
      enabled: typeof item === 'string' ? true : item?.enabled !== false
    })
    return out
  }, [])
}

const firstEnabledModel = (provider) => {
  const models = Array.isArray(provider?.models) ? provider.models : []
  return models.find((item) => item.enabled)?.name || ''
}

const normalizeDefaultModel = (defaultModel, models) => {
  const normalizedModels = normalizeModelRows(models)
  const target = String(defaultModel || '').trim()
  if (target && normalizedModels.some((item) => item.enabled && item.name === target)) {
    return target
  }
  return normalizedModels.find((item) => item.enabled)?.name || ''
}

function resetProviderDraft() {
  return {
    provider_type: 'anthropic',
    provider_id: '',
    display_name: '',
    initial_model: ''
  }
}

const slugifyProviderID = (value) => String(value || '')
  .trim()
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-+|-+$/g, '')

const resolveModelForProvider = (provider, preferredModel = '') => {
  if (!provider) return ''
  const models = Array.isArray(provider.models) ? provider.models : []
  if (preferredModel && models.some((item) => item.enabled && item.name === preferredModel)) return preferredModel
  if (provider.default_model && models.some((item) => item.enabled && item.name === provider.default_model)) return provider.default_model
  return firstEnabledModel(provider)
}

const syncInspection = () => {
  const providers = orderedProviders.value
  if (!providers.length) {
    inspectedProviderId.value = ''
    return
  }

  const provider = providers.find((item) => item.provider_id === inspectedProviderId.value)
    || providers.find((item) => item.provider_id === form.default_provider_id)
    || providers[0]

  inspectedProviderId.value = provider.provider_id
}

const normalizeDefaults = () => {
  const providers = orderedProviders.value
  if (!providers.length) {
    form.default_provider_id = ''
    form.default_model = ''
    return
  }

  const enabledProviders = providers.filter((item) => item.enabled)
  const fallbackProvider = enabledProviders[0] || providers[0]
  const current = providers.find((item) => item.provider_id === form.default_provider_id)
  const usable = current && current.enabled ? current : fallbackProvider

  form.default_provider_id = usable?.provider_id || ''
  form.default_model = resolveModelForProvider(usable, form.default_model)
}

const selectProvider = (providerID) => {
  const provider = orderedProviders.value.find((item) => item.provider_id === providerID)
  if (!provider) return
  inspectedProviderId.value = provider.provider_id
}

const selectProviderType = (providerType) => {
  providerDraft.provider_type = providerType
  syncProviderIDFromDraft()
}

const isProviderDefaultModel = (model) => (
  !!selectedProvider.value
  && selectedProvider.value.default_model === model.name
)

const syncDefaultModelForProvider = (provider) => {
  if (!provider) return
  provider.default_model = resolveModelForProvider(provider, provider.default_model)
  if (provider.provider_id === form.default_provider_id) {
    form.default_model = resolveModelForProvider(provider, form.default_model || provider.default_model)
  }
}

const toggleModelEnabled = (model, enabled) => {
  if (!selectedProvider.value) return
  model.enabled = Boolean(enabled)
  syncDefaultModelForProvider(selectedProvider.value)
  normalizeDefaults()
}

const toggleModelDefault = (model, enabled) => {
  if (!selectedProvider.value) return
  if (enabled) {
    if (!model.enabled) {
      model.enabled = true
    }
    selectedProvider.value.default_model = model.name
  } else if (selectedProvider.value.default_model === model.name) {
    selectedProvider.value.default_model = firstEnabledModel(selectedProvider.value)
  }
  syncDefaultModelForProvider(selectedProvider.value)
}

const toggleProviderEnabled = (provider, enabled) => {
  if (!provider) return
  provider.enabled = Boolean(enabled)
  normalizeDefaults()
  syncInspection()
}

const toggleProviderDefault = (provider, enabled) => {
  if (!provider) return
  if (enabled) {
    form.default_provider_id = provider.provider_id
    form.default_model = resolveModelForProvider(provider, provider.default_model)
  } else if (form.default_provider_id === provider.provider_id) {
    form.default_provider_id = ''
    form.default_model = ''
    normalizeDefaults()
  }
  syncInspection()
}

const openProviderDialog = () => {
  Object.assign(providerDraft, resetProviderDraft())
  providerIDTouched.value = false
  providerDialogVisible.value = true
}

const syncProviderIDFromDraft = () => {
  if (providerIDTouched.value) return
  const base = slugifyProviderID(providerDraft.display_name) || providerDraft.provider_type
  let candidate = base
  let suffix = 2
  while (form.providers.some((item) => item.provider_id === candidate)) {
    candidate = `${base}-${suffix}`
    suffix += 1
  }
  providerDraft.provider_id = candidate
}

const addProvider = () => {
  const providerID = slugifyProviderID(providerDraft.provider_id)
  const displayName = String(providerDraft.display_name || '').trim()
  const initialModel = String(providerDraft.initial_model || '').trim()
  if (!providerDraft.provider_type) {
    ElMessage.error('请选择供应商类型')
    return
  }
  if (!providerID) {
    ElMessage.error('请输入供应商标识')
    return
  }
  if (form.providers.some((item) => item.provider_id === providerID)) {
    ElMessage.error('供应商标识已存在')
    return
  }
  if (!initialModel) {
    ElMessage.error('请输入至少一个模型')
    return
  }
  form.providers.push({
    provider_id: providerID,
    provider_type: providerDraft.provider_type,
    display_name: displayName || providerID,
    default_model: initialModel,
    models: [{ name: initialModel, enabled: true }],
    base_url: '',
    api_token: '',
    enabled: true
  })
  providerDialogVisible.value = false
  inspectedProviderId.value = providerID
  normalizeDefaults()
}

const removeSelectedProvider = async () => {
  if (!selectedProvider.value || !canDeleteSelectedProvider.value) return
  try {
    await ElMessageBox.confirm(`将删除供应商“${selectedProvider.value.display_name || selectedProvider.value.provider_id}”及其模型列表。`, '删除供应商', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  form.providers = form.providers.filter((item) => item.provider_id !== selectedProvider.value.provider_id)
  normalizeDefaults()
  syncInspection()
}

const addModelPrompt = async () => {
  if (!selectedProvider.value) return
  const { value } = await ElMessageBox.prompt('输入要新增的模型名称', '新增模型', {
    confirmButtonText: '新增',
    cancelButtonText: '取消',
    inputValue: '',
    inputPlaceholder: '例如 claude-opus-4-1'
  }).catch(() => ({ value: '' }))
  const model = String(value || '').trim()
  if (!model) return
  if (selectedProvider.value.models.some((item) => item.name === model)) {
    ElMessage.error('模型已存在')
    return
  }
  selectedProvider.value.models = [...selectedProvider.value.models, { name: model, enabled: true }]
  if (!resolveModelForProvider(selectedProvider.value, selectedProvider.value.default_model)) {
    selectedProvider.value.default_model = model
  }
  syncDefaultModelForProvider(selectedProvider.value)
}

const removeModel = async (model) => {
  if (!selectedProvider.value || selectedProvider.value.models.length <= 1) return
  try {
    await ElMessageBox.confirm(`将从当前供应商中删除模型“${model.name}”。`, '删除模型', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  selectedProvider.value.models = selectedProvider.value.models.filter((item) => item.name !== model.name)
  syncDefaultModelForProvider(selectedProvider.value)
  normalizeDefaults()
}

const trimProviderFields = () => {
  form.providers = normalizeProviderRows(form.providers)
}

const serializeModelSettings = () => JSON.stringify({
  default_provider_id: form.default_provider_id,
  default_model: form.default_model,
  providers: normalizeProviderRows(form.providers)
})

const loadSettings = async () => {
  hydrating.value = true
  try {
    const payload = await settingsApi.getAgentSettings()
    Object.assign(form, payload, {
      providers: normalizeProviderRows(payload?.providers)
    })
    normalizeDefaults()
    syncInspection()
    lastPersistedSnapshot.value = serializeModelSettings()
  } finally {
    hydrating.value = false
  }
}

const persistSettings = async () => {
  trimProviderFields()
  normalizeDefaults()
  const snapshot = serializeModelSettings()
  if (!snapshot || snapshot === lastPersistedSnapshot.value) return
  saving.value = true
  try {
    await settingsApi.updateAgentSettings(form)
    await loadSettings()
  } catch (error) {
    ElMessage.error(error.message || '保存设置失败')
  } finally {
    saving.value = false
  }
}

let autosaveTimer = null
const queuePersistSettings = () => {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
  }
  autosaveTimer = window.setTimeout(() => {
    autosaveTimer = null
    void persistSettings()
  }, 500)
}

watch(
  serializeModelSettings,
  () => {
    if (hydrating.value) return
    queuePersistSettings()
  }
)

onBeforeUnmount(() => {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
    autosaveTimer = null
  }
})

onMounted(loadSettings)
</script>
