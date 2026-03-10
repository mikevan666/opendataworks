import {
  buildChartRenderModel,
  extractChartSpecsFromText,
  parseChartSpec,
  validateChartSpec
} from '../chartSpec'

describe('chartSpec', () => {
  it('parses and validates line chart specs without reordering dataset', () => {
    const spec = {
      kind: 'chart_spec',
      version: 1,
      chart_type: 'line',
      title: '最近30天工作流发布趋势',
      description: '按天展示工作流发布次数',
      x_field: 'stat_day',
      series: [{ name: '发布次数', field: 'publish_cnt', type: 'line' }],
      dataset: [
        { stat_day: '2026-03-03', publish_cnt: 8 },
        { stat_day: '2026-03-01', publish_cnt: 3 },
        { stat_day: '2026-03-02', publish_cnt: 5 }
      ],
      error: null
    }

    const parsed = parseChartSpec(spec)
    const validation = validateChartSpec(parsed)
    const renderModel = buildChartRenderModel(parsed)

    expect(validation.valid).toBe(true)
    expect(renderModel.state).toBe('renderable')
    expect(renderModel.kind).toBe('echarts')
    expect(renderModel.option.xAxis.data).toEqual(['2026-03-03', '2026-03-01', '2026-03-02'])
    expect(renderModel.option.series[0].data).toEqual([8, 3, 5])
  })

  it('validates pie chart with a single series only', () => {
    const renderModel = buildChartRenderModel({
      kind: 'chart_spec',
      version: 1,
      chart_type: 'pie',
      title: '各工作流发布操作类型占比',
      x_field: 'operation',
      series: [
        { name: '发布次数', field: 'publish_cnt', type: 'pie' },
        { name: '占比', field: 'ratio', type: 'pie' }
      ],
      dataset: [
        { operation: 'deploy', publish_cnt: 33, ratio: 0.68 },
        { operation: 'online', publish_cnt: 9, ratio: 0.18 }
      ],
      error: null
    })

    expect(renderModel.state).toBe('invalid')
    expect(renderModel.errorText).toContain('pie 类型必须且只能提供一个 series')
  })

  it('builds table render models only when columns are explicit', () => {
    const renderModel = buildChartRenderModel({
      kind: 'chart_spec',
      version: 1,
      chart_type: 'table',
      title: '最近工作流发布记录',
      columns: ['workflow_id', 'status'],
      dataset: [{ workflow_id: 173, status: 'success' }],
      error: null
    })

    expect(renderModel.state).toBe('renderable')
    expect(renderModel.kind).toBe('table')
    expect(renderModel.columns).toEqual(['workflow_id', 'status'])
    expect(renderModel.rows).toEqual([{ workflow_id: 173, status: 'success' }])
  })

  it('fails invalid specs with explicit field errors', () => {
    const validation = validateChartSpec({
      kind: 'chart_spec',
      version: 1,
      chart_type: 'bar',
      title: '各数据层表数量对比',
      dataset: [{ layer: 'DWD', table_cnt: 18 }],
      error: null
    })

    expect(validation.valid).toBe(false)
    expect(validation.errors).toContain('bar 类型必须提供 x_field')
    expect(validation.errors).toContain('bar 类型必须提供 series')
  })

  it('extracts fenced chart specs using the same parser', () => {
    const message = `
结论如下：

\`\`\`chart
{"kind":"chart_spec","version":1,"chart_type":"pie","title":"各工作流发布操作类型占比","x_field":"operation","series":[{"name":"发布次数","field":"publish_cnt","type":"pie"}],"dataset":[{"operation":"deploy","publish_cnt":33},{"operation":"online","publish_cnt":9}],"error":null}
\`\`\`
`

    const specs = extractChartSpecsFromText(message)

    expect(specs).toHaveLength(1)
    expect(specs[0].chart_type).toBe('pie')
    expect(specs[0].series[0].field).toBe('publish_cnt')
  })
})
