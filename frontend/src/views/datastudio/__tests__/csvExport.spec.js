import { describe, expect, it } from 'vitest'
import { buildCsvContent } from '../csvExport'

describe('csvExport', () => {
  it('adds a UTF-8 BOM and escapes headers and values that would break columns', () => {
    const csv = buildCsvContent(
      ['名称', '备注,字段', '公式'],
      [
        {
          名称: '张三',
          '备注,字段': '含逗号,双引号"和\r\n换行',
          公式: '=1+1'
        }
      ]
    )

    expect(csv).toBe(
      '\uFEFF名称,"备注,字段",公式\r\n' +
        '张三,"含逗号,双引号""和\r\n换行","=1+1"\r\n'
    )
  })
})
