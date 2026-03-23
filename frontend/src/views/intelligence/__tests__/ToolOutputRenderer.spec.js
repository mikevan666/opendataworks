import { vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'

const echartsMocks = vi.hoisted(() => {
  const setOption = vi.fn()
  const resize = vi.fn()
  const clear = vi.fn()
  const dispose = vi.fn()
  const init = vi.fn(() => ({
    setOption,
    resize,
    clear,
    dispose
  }))
  return { setOption, resize, clear, dispose, init }
})

vi.mock('echarts/core', () => ({
  use: () => {},
  init: echartsMocks.init
}))

vi.mock('echarts/charts', () => ({
  BarChart: {},
  LineChart: {},
  PieChart: {}
}))

vi.mock('echarts/components', () => ({
  GridComponent: {},
  LegendComponent: {},
  TitleComponent: {},
  TooltipComponent: {}
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: {}
}))

import ToolOutputRenderer from '../ToolOutputRenderer.vue'

const mountRenderer = (tool) => shallowMount(ToolOutputRenderer, {
  props: { tool }
})

describe('ToolOutputRenderer', () => {
  it('renders table chart_spec payloads as tables', () => {
    const wrapper = mountRenderer({
      name: 'build_chart_spec.py',
      status: 'success',
      output: {
        kind: 'chart_spec',
        version: 1,
        chart_type: 'table',
        title: '最近工作流发布记录',
        description: '以表格展示最近工作流发布记录',
        columns: ['workflow_id', 'status'],
        dataset: [{ workflow_id: 173, status: 'success' }],
        error: null
      }
    })

    expect(wrapper.findAll('th').map((node) => node.text())).toEqual(['workflow_id', 'status'])
    expect(wrapper.text()).toContain('173')
    expect(wrapper.text()).toContain('success')
  })

  it('renders chart_spec payloads through the chart renderer', () => {
    const wrapper = mountRenderer({
      name: 'build_chart_spec.py',
      status: 'success',
      output: {
        kind: 'chart_spec',
        version: 1,
        chart_type: 'line',
        title: '最近30天工作流发布趋势',
        x_field: 'stat_day',
        series: [{ name: '发布次数', field: 'publish_cnt', type: 'line' }],
        dataset: [
          { stat_day: '2026-03-01', publish_cnt: 3 },
          { stat_day: '2026-03-02', publish_cnt: 5 }
        ],
        error: null
      }
    })

    expect(wrapper.find('.tool-chart').exists()).toBe(true)
  })

  it('shows explicit invalid-spec feedback and raw payloads', () => {
    const wrapper = mountRenderer({
      name: 'build_chart_spec.py',
      status: 'success',
      output: {
        kind: 'chart_spec',
        version: 1,
        chart_type: 'bar',
        title: '各数据层表数量对比',
        dataset: [{ layer: 'DWD', table_cnt: 18 }],
        error: null
      }
    })

    expect(wrapper.text()).toContain('bar 类型必须提供 x_field')
    expect(wrapper.text()).toContain('"chart_type": "bar"')
  })

  it('renders bash tools as collapsible shell traces', async () => {
    const wrapper = mountRenderer({
      name: 'Bash',
      status: 'streaming',
      _callComplete: true,
      _runtimeStarted: true,
      input: {
        command: 'python scripts/build_chart_spec.py --chart-type pie',
        description: '生成占比图表'
      },
      output: 'processing...'
    })

    expect(wrapper.text()).toContain('生成占比图表')
    expect(wrapper.text()).toContain('Shell')
    expect(wrapper.text()).toContain('$ python scripts/build_chart_spec.py --chart-type pie')
    expect(wrapper.text()).toContain('processing...')
    expect(wrapper.text()).toContain('正在运行命令')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(true)

    await wrapper.setProps({
      tool: {
        name: 'Bash',
        status: 'success',
        _callComplete: true,
        _runtimeStarted: true,
        input: {
          command: 'python scripts/build_chart_spec.py --chart-type pie',
          description: '生成占比图表'
        },
        output: 'done'
      }
    })

    expect(wrapper.text()).toContain('已运行命令')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)
  })

  it('renders read tools as compact one-line traces without output panels', async () => {
    const wrapper = mountRenderer({
      name: 'Read',
      status: 'streaming',
      _callComplete: true,
      _runtimeStarted: true,
      input: {
        file_path: '/tmp/reference/00-skill-map.md'
      },
      output: '## skill map'
    })

    expect(wrapper.text()).toContain('正在浏览')
    expect(wrapper.text()).toContain('/tmp/reference/00-skill-map.md')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('## skill map')

    await wrapper.setProps({
      tool: {
        name: 'Read',
        status: 'success',
        _callComplete: true,
        _runtimeStarted: true,
        input: {
          file_path: '/tmp/reference/00-skill-map.md'
        },
        output: '## skill map'
      }
    })

    expect(wrapper.text()).toContain('已浏览')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('## skill map')
  })

  it('keeps read traces compact across invocation and runtime states', async () => {
    const wrapper = mountRenderer({
      name: 'Read',
      status: 'streaming',
      _callComplete: false,
      _runtimeStarted: false,
      input: {
        file_path: '/tmp/reference/30-tool-recipes.md'
      },
      output: ''
    })

    expect(wrapper.text()).toContain('正在发起浏览')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)

    await wrapper.setProps({
      tool: {
        name: 'Read',
        status: 'streaming',
        _callComplete: true,
        _runtimeStarted: false,
        input: {
          file_path: '/tmp/reference/30-tool-recipes.md'
        },
        output: ''
      }
    })

    expect(wrapper.text()).toContain('已发起浏览')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)

    await wrapper.setProps({
      tool: {
        name: 'Read',
        status: 'streaming',
        _callComplete: true,
        _runtimeStarted: true,
        input: {
          file_path: '/tmp/reference/30-tool-recipes.md'
        },
        output: '正在读取...'
      }
    })

    expect(wrapper.text()).toContain('正在浏览')
    expect(wrapper.find('.shell-trace-panel').exists()).toBe(false)
  })

  it('renders markdown skill output as a collapsed preview and expands on demand', async () => {
    const wrapper = mountRenderer({
      id: 'tool-skill-preview',
      name: 'Skill',
      status: 'success',
      _callComplete: true,
      _runtimeStarted: true,
      input: {
        description: '加载技能说明'
      },
      output: [
        '1→# 场景 Playbooks',
        '2→',
        '3→先结论：优先覆盖统计、对比、趋势、占比、明细、诊断六类问题。',
        '4→',
        '5→## 托管业务表',
        '6→需要先查 metadata，再解析 datasource，最后执行 SQL。'
      ].join('\n')
    })

    await wrapper.find('.shell-trace-summary').trigger('click')

    expect(wrapper.find('.tool-markdown').exists()).toBe(true)
    expect(wrapper.text()).toContain('场景 Playbooks')
    expect(wrapper.text()).toContain('托管业务表')
    expect(wrapper.text()).not.toContain('1→# 场景 Playbooks')
    expect(wrapper.text()).not.toContain('5→## 托管业务表')
    expect(wrapper.text()).not.toContain('需要先查 metadata，再解析 datasource，最后执行 SQL。')
    expect(wrapper.find('.tool-markdown-toggle').text()).toContain('展开')
    expect(wrapper.findAll('.tool-code').length).toBe(0)

    await wrapper.find('.tool-markdown-toggle').trigger('click')

    expect(wrapper.text()).toContain('需要先查 metadata，再解析 datasource，最后执行 SQL。')
    expect(wrapper.text()).not.toContain('6→需要先查 metadata，再解析 datasource，最后执行 SQL。')
    expect(wrapper.find('.tool-markdown-toggle').text()).toContain('收起')
  })
})
