import { vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'

vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option'],
    template: '<div class="chart-stub" />'
  }
}))

vi.mock('echarts/core', () => ({
  use: () => {}
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

    const chartStub = wrapper.findComponent({ name: 'VChart' })

    expect(chartStub.exists()).toBe(true)
    expect(chartStub.props('option').series[0].type).toBe('line')
    expect(chartStub.props('option').xAxis.data).toEqual(['2026-03-01', '2026-03-02'])
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
})
