<template>
  <ProductPageShell
    eyebrow="Runtime Settings"
    title="设置"
    description="统一维护运行参数。"
  >
    <template #actions>
      <button type="button" class="oda-btn-primary" :disabled="saving" @click="saveSettings">
        <Save class="h-4 w-4" />
        {{ saving ? '保存中' : '保存设置' }}
      </button>
    </template>

    <section class="oda-card p-6">
      <div class="space-y-8">
        <section>
          <div class="text-xl font-semibold tracking-tight text-gray-900">访问控制</div>
          <div class="mt-2 text-sm leading-relaxed text-gray-500">
            管理员访问令牌和会话库配置。
          </div>
        
          <div class="mt-5 space-y-5">
            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">管理员令牌</label>
              <input
                v-model="form.admin_token"
                class="oda-input"
                type="password"
                placeholder="留空则沿用当前配置"
              >
            </div>

            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">会话数据库</label>
              <input
                v-model="form.session_mysql_database"
                class="oda-input"
                type="text"
                placeholder="例如 dataagent"
              >
            </div>
          </div>
        </section>

        <section class="border-t border-blue-100 pt-8">
          <div class="text-xl font-semibold tracking-tight text-gray-900">Skill 目录</div>
          <div class="mt-2 text-sm leading-relaxed text-gray-500">
            托管 Skill 与内置 Skill 的本地目录。
          </div>

          <div class="mt-5 space-y-5">
            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">托管 Skill 目录</label>
              <input v-model="form.managed_skills_dir" class="oda-input" type="text">
            </div>

            <div>
              <label class="mb-2 block text-sm font-medium text-gray-700">内置 Skill 目录</label>
              <input v-model="form.skills_root_dir" class="oda-input" type="text">
            </div>
          </div>
        </section>
      </div>
    </section>

  </ProductPageShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Save } from 'lucide-vue-next'
import ProductPageShell from '@/components/ProductPageShell.vue'
import { settingsApi } from '@/api/settings'

const saving = ref(false)
const form = reactive({
  default_provider_id: '',
  default_model: '',
  managed_skills_dir: '',
  skills_root_dir: '',
  session_mysql_database: '',
  admin_token: '',
  providers: []
})

const loadSettings = async () => {
  const payload = await settingsApi.getAgentSettings()
  Object.assign(form, payload)
}

const saveSettings = async () => {
  saving.value = true
  try {
    await settingsApi.updateAgentSettings(form)
    ElMessage.success('设置已保存')
    await loadSettings()
  } catch (error) {
    ElMessage.error(error.message || '保存设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>
