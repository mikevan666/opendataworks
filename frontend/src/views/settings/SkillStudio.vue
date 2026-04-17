<template>
  <div class="skill-studio">
    <div class="skill-studio__toolbar">
      <div>
        <div class="skill-studio__title">Skill 列表</div>
        <div class="skill-studio__subtitle">{{ enabledSummary }}</div>
      </div>
      <div class="skill-studio__actions">
        <el-input
          v-model="searchKeyword"
          clearable
          placeholder="搜索 Skill 名称或文件路径"
          class="skill-studio__search"
        />
        <el-upload
          accept=".zip,application/zip"
          :show-file-list="false"
          :disabled="importLoading"
          :before-upload="beforeSkillUpload"
          :http-request="handleSkillUpload"
        >
          <el-button type="primary" :loading="importLoading">导入 Skill</el-button>
        </el-upload>
        <el-button :loading="syncLoading" @click="triggerSync">刷新目录</el-button>
      </div>
    </div>

    <el-alert
      v-if="syncResult"
      type="success"
      :closable="true"
      show-icon
      class="skill-studio__alert"
      @close="syncResult = null"
    >
      <template #title>
        Skill 目录已刷新：共处理 {{ syncResult.document_count }} 个文件，更新 {{ syncResult.changed_documents?.length || 0 }} 个。
      </template>
    </el-alert>

    <div v-loading="listLoading" class="skill-grid">
      <div
        v-for="skill in filteredSkills"
        :key="skill.folder"
        class="skill-card"
      >
        <div class="skill-card__header">
          <div class="skill-card__heading">
            <div class="skill-card__title">{{ skill.folder }}</div>
            <div class="skill-card__path">{{ skill.folder }}/{{ skill.primaryPath || skill.primaryFileName }}</div>
          </div>
          <div class="skill-card__switch">
            <span class="skill-card__switch-label">启用</span>
            <el-switch
              :model-value="skill.enabled"
              :loading="runtimeUpdatingFolder === skill.folder"
              @update:model-value="setSkillEnabled(skill, $event)"
            />
          </div>
        </div>

        <div class="skill-card__tags">
          <el-tag size="small" effect="plain">{{ sourceLabel(skill.source) }}</el-tag>
          <el-tag size="small" :type="skill.enabled ? 'success' : 'info'">
            {{ skill.enabled ? '已启用' : '未启用' }}
          </el-tag>
          <el-tag size="small" effect="plain">{{ skill.documentCount }} 个文件</el-tag>
        </div>

        <div class="skill-card__stats">
          <div class="skill-stat">
            <div class="skill-stat__label">最近更新</div>
            <div class="skill-stat__value">{{ formatTime(skill.updatedAt) }}</div>
          </div>
        </div>

        <div class="skill-card__footer">
          <el-button text type="primary" @click="openSkillDetail(skill.folder)">查看详情</el-button>
          <el-button
            v-if="skill.source === 'managed'"
            text
            type="danger"
            @click="confirmUninstallSkill(skill)"
          >
            卸载
          </el-button>
        </div>
      </div>
    </div>

    <el-empty
      v-if="!listLoading && !filteredSkills.length"
      description="当前目录还没有可管理的 Skill"
      :image-size="120"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dataagentApi } from '@/api/dataagent'
import { buildSkillItems, sourceLabel } from './skillAdminShared'

const router = useRouter()

const listLoading = ref(false)
const syncLoading = ref(false)
const importLoading = ref(false)
const searchKeyword = ref('')
const documents = ref([])
const syncResult = ref(null)
const runtimeUpdatingFolder = ref('')

const skillItems = computed(() => buildSkillItems(documents.value))

const filteredSkills = computed(() => {
  const keyword = String(searchKeyword.value || '').trim().toLowerCase()
  if (!keyword) {
    return skillItems.value
  }
  return skillItems.value.filter((item) => {
    if (String(item.folder || '').toLowerCase().includes(keyword)) {
      return true
    }
    return (item.documents || []).some((document) => {
      return String(document.relative_path || '').toLowerCase().includes(keyword)
    })
  })
})

const enabledSummary = computed(() => {
  const enabledCount = skillItems.value.filter((item) => item.enabled).length
  return `已启用 ${enabledCount} / 共 ${skillItems.value.length}`
})

const formatTime = (value) => {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

const loadDocuments = async () => {
  listLoading.value = true
  try {
    documents.value = await dataagentApi.listSkillDocuments()
  } finally {
    listLoading.value = false
  }
}

const openSkillDetail = (folder) => {
  if (!folder) return
  router.push({
    name: 'SkillDetail',
    params: { folder }
  })
}

const setSkillEnabled = async (skill, enabled) => {
  if (!skill?.folder || Boolean(enabled) === Boolean(skill.enabled)) return
  runtimeUpdatingFolder.value = skill.folder
  try {
    await dataagentApi.updateSkillRuntime(skill.folder, { enabled: Boolean(enabled) })
    await loadDocuments()
    ElMessage.success(enabled ? `Skill「${skill.folder}」已启用` : `Skill「${skill.folder}」已禁用`)
  } finally {
    runtimeUpdatingFolder.value = ''
  }
}

const beforeSkillUpload = (file) => {
  const fileName = String(file?.name || '').toLowerCase()
  if (!fileName.endsWith('.zip')) {
    ElMessage.error('请上传 ZIP 格式的 Skill 包')
    return false
  }
  return true
}

const handleSkillUpload = async ({ file }) => {
  if (!file) return
  importLoading.value = true
  try {
    const payload = await dataagentApi.importSkill(file)
    await loadDocuments()
    ElMessage.success(`Skill「${payload.skill_id}」已导入，默认未启用`)
  } finally {
    importLoading.value = false
  }
}

const confirmUninstallSkill = async (skill) => {
  if (!skill?.folder || skill.source !== 'managed') return
  try {
    await ElMessageBox.prompt(
      `请输入 ${skill.folder} 确认卸载。`,
      '卸载 Skill',
      {
        type: 'warning',
        confirmButtonText: '确认卸载',
        cancelButtonText: '取消',
        inputPlaceholder: skill.folder,
        inputValidator: (value) => String(value || '').trim() === skill.folder || `请输入 ${skill.folder}`
      }
    )
  } catch {
    return
  }

  await dataagentApi.uninstallSkill(skill.folder)
  await loadDocuments()
  ElMessage.success(`Skill「${skill.folder}」已卸载`)
}

const triggerSync = async () => {
  try {
    await ElMessageBox.confirm(
      '确认重新扫描 Skill 目录并刷新 DataAgent 运行时吗？',
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
    ElMessage.success('Skill 目录刷新完成')
  } finally {
    syncLoading.value = false
  }
}

onMounted(async () => {
  await loadDocuments()
})
</script>

<style scoped>
.skill-studio {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-studio__toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.skill-studio__title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.skill-studio__subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.skill-studio__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skill-studio__search {
  width: 280px;
}

.skill-studio__alert {
  margin-top: -4px;
}

.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.skill-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border: 1px solid #dbe2ea;
  border-radius: 10px;
  background: #fff;
}

.skill-card__header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.skill-card__heading {
  min-width: 0;
}

.skill-card__title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.skill-card__path {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  word-break: break-all;
}

.skill-card__switch {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.skill-card__switch-label {
  font-size: 12px;
  color: #64748b;
}

.skill-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-card__stats {
  display: block;
}

.skill-stat {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
}

.skill-stat__label {
  font-size: 12px;
  color: #64748b;
}

.skill-stat__value {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.skill-card__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: auto;
}

@media (max-width: 768px) {
  .skill-studio__toolbar,
  .skill-studio__actions,
  .skill-card__header {
    flex-direction: column;
  }

  .skill-studio__search {
    width: 100%;
  }

  .skill-card__switch {
    align-items: flex-start;
  }
}
</style>
