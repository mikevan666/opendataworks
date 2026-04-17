import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  listSkillDocuments: vi.fn(),
  syncSkills: vi.fn(),
  updateSkillRuntime: vi.fn()
}))

const routerPush = vi.hoisted(() => vi.fn())

const messageMocks = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn()
}))

const messageBoxMocks = vi.hoisted(() => ({
  confirm: vi.fn()
}))

vi.mock('@/api/dataagent', () => ({
  dataagentApi: apiMocks
}))

vi.mock('vue-router', async (importOriginal) => ({
  ...(await importOriginal()),
  useRouter: () => ({
    push: routerPush
  })
}))

vi.mock('element-plus', async (importOriginal) => ({
  ...(await importOriginal()),
  ElMessage: messageMocks,
  ElMessageBox: messageBoxMocks
}))

import SkillStudio from '../SkillStudio.vue'

const stubs = {
  'el-input': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />'
  },
  'el-button': {
    props: ['loading', 'disabled'],
    template: '<button :disabled="disabled"><slot /></button>'
  },
  'el-alert': { template: '<div><slot /><slot name="title" /></div>' },
  'el-tag': { template: '<span><slot /></span>' },
  'el-empty': { template: '<div><slot /></div>' },
  'el-switch': {
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue'],
    template: '<button :disabled="disabled" @click="$emit(\'update:modelValue\', !modelValue)"><slot /></button>'
  }
}

const documentsPayload = () => ([
  {
    id: 1,
    folder: 'dataagent-nl2sql',
    relative_path: 'SKILL.md',
    file_name: 'SKILL.md',
    category: 'root',
    content_type: 'markdown',
    source: 'bundled',
    version_count: 2,
    updated_at: '2026-04-17T09:00:00',
    editable: true,
    enabled: true
  },
  {
    id: 2,
    folder: 'dataagent-nl2sql',
    relative_path: 'reference/40-runtime-metadata.md',
    file_name: '40-runtime-metadata.md',
    category: 'reference',
    content_type: 'markdown',
    source: 'bundled',
    version_count: 1,
    updated_at: '2026-04-17T10:00:00',
    editable: true,
    enabled: true
  },
  {
    id: 3,
    folder: 'marketing-insights',
    relative_path: 'SKILL.md',
    file_name: 'SKILL.md',
    category: 'root',
    content_type: 'markdown',
    source: 'bundled',
    version_count: 4,
    updated_at: '2026-04-17T11:00:00',
    editable: true,
    enabled: false
  }
])

const mountView = () => shallowMount(SkillStudio, {
  global: { stubs }
})

describe('SkillStudio', () => {
  beforeEach(() => {
    apiMocks.listSkillDocuments.mockReset()
    apiMocks.syncSkills.mockReset()
    apiMocks.updateSkillRuntime.mockReset()
    messageMocks.success.mockReset()
    messageBoxMocks.confirm.mockReset()
    routerPush.mockReset()

    apiMocks.listSkillDocuments.mockResolvedValue(documentsPayload())
    apiMocks.updateSkillRuntime.mockResolvedValue({
      skill_id: 'marketing-insights',
      enabled: true
    })
  })

  it('groups documents into skill cards and routes to detail view', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.vm.filteredSkills).toHaveLength(2)
    expect(wrapper.vm.enabledSummary).toBe('已启用 1 / 共 2')
    expect(wrapper.text()).toContain('dataagent-nl2sql')
    expect(wrapper.text()).toContain('marketing-insights')
    expect(wrapper.text()).toContain('已启用')
    expect(wrapper.text()).toContain('未启用')
    expect(wrapper.text()).not.toContain('当前运行')

    wrapper.vm.openSkillDetail('marketing-insights')
    expect(routerPush).toHaveBeenCalledWith({
      name: 'SkillDetail',
      params: { folder: 'marketing-insights' }
    })
  })

  it('enables the selected skill through runtime update api', async () => {
    const wrapper = mountView()
    await flushPromises()

    const targetSkill = wrapper.vm.filteredSkills.find((item) => item.folder === 'marketing-insights')
    await wrapper.vm.setSkillEnabled(targetSkill, true)
    await flushPromises()

    expect(apiMocks.updateSkillRuntime).toHaveBeenCalledWith('marketing-insights', { enabled: true })
    expect(messageMocks.success).toHaveBeenCalledWith('Skill「marketing-insights」已启用')
  })

  it('disables an enabled skill without changing other cards locally', async () => {
    const wrapper = mountView()
    await flushPromises()

    const currentSkill = wrapper.vm.filteredSkills.find((item) => item.folder === 'dataagent-nl2sql')
    await wrapper.vm.setSkillEnabled(currentSkill, false)
    await flushPromises()

    expect(apiMocks.updateSkillRuntime).toHaveBeenCalledWith('dataagent-nl2sql', { enabled: false })
    expect(messageMocks.success).toHaveBeenCalledWith('Skill「dataagent-nl2sql」已禁用')
  })
})
