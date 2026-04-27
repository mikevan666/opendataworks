import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const settingsApiMocks = vi.hoisted(() => ({
  getAgentSettings: vi.fn(),
  updateAgentSettings: vi.fn()
}))

vi.mock('@/api/settings', () => ({
  settingsApi: settingsApiMocks
}))

import AgentSettingsView from '../AgentSettingsView.vue'

const baseSettings = () => ({
  default_provider_id: 'mock',
  default_model: 'mock-model',
  managed_skills_dir: '',
  skills_root_dir: '',
  session_mysql_database: '',
  admin_token: '',
  providers: [
    {
      provider_id: 'mock',
      provider_type: 'mock',
      display_name: 'Mock',
      default_model: 'mock-model',
      models: [{ name: 'mock-model', enabled: true }],
      base_url: '',
      api_token: '',
      enabled: true
    }
  ]
})

const stubs = {
  ProductPageShell: {
    template: '<div><slot name="sidebar" /><slot /></div>'
  },
  'el-dialog': {
    props: ['modelValue', 'title', 'width'],
    template: `
      <section v-if="modelValue" data-test="provider-dialog" :data-width="width">
        <slot />
        <footer data-test="provider-dialog-footer"><slot name="footer" /></footer>
      </section>
    `
  },
  'el-switch': {
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue'],
    template: '<button :disabled="disabled" @click="$emit(\'update:modelValue\', !modelValue)"><slot /></button>'
  },
  Cpu: { template: '<i />' },
  Plus: { template: '<i />' },
  Trash2: { template: '<i />' }
}

const mountView = () => mount(AgentSettingsView, {
  global: { stubs }
})

describe('AgentSettingsView', () => {
  beforeEach(() => {
    settingsApiMocks.getAgentSettings.mockReset()
    settingsApiMocks.updateAgentSettings.mockReset()
    settingsApiMocks.getAgentSettings.mockResolvedValue(baseSettings())
    settingsApiMocks.updateAgentSettings.mockResolvedValue(baseSettings())
  })

  it('uses a viewport-safe width for the add provider dialog footer actions', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('button.oda-btn-secondary').trigger('click')

    const dialog = wrapper.get('[data-test="provider-dialog"]')
    expect(dialog.attributes('data-width')).toBe('min(560px, calc(100vw - 32px))')
    expect(wrapper.get('[data-test="provider-dialog-footer"]').text()).toContain('新增')
  })
})
