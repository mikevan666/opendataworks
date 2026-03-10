import { buildPublishPreviewHtml, resolvePublishVersionId } from '../publishPreviewHelper'

describe('publishPreviewHelper', () => {
  it('renders explicit before and after values for task field changes', () => {
    const html = buildPublishPreviewHtml({
      diffSummary: {
        taskModified: [
          {
            taskCode: 1001,
            taskName: 'sql_task',
            fieldChanges: [
              {
                field: 'task.sql',
                before: 'select *\nfrom ods.user_old',
                after: 'select *\nfrom ods.user_new'
              }
            ]
          }
        ]
      }
    })

    expect(html).toContain('变更前（运行态）')
    expect(html).toContain('变更后（平台）')
    expect(html).toContain('变更前为 Dolphin 运行态当前值，变更后为平台本次发布目标值。')
    expect(html).toContain('sql_task (1001)')
    expect(html).toContain('from ods.user_old')
    expect(html).toContain('from ods.user_new')
  })

  it('prefers last published version when resolving publish version id', () => {
    expect(resolvePublishVersionId({
      currentVersionId: 101,
      lastPublishedVersionId: 88
    })).toBe(88)

    expect(resolvePublishVersionId({
      currentVersionId: 101,
      lastPublishedVersionId: null
    })).toBe(101)

    expect(resolvePublishVersionId({})).toBeUndefined()
  })
})
