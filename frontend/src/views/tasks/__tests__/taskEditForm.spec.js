import { describe, expect, it } from 'vitest'
import { buildTaskPayload, createDefaultTaskModel, syncTaskDatasourceType } from '../taskEditForm'

describe('taskEditForm', () => {
  it('defaults dolphinFlag to YES and datasourceType to null for new tasks', () => {
    expect(createDefaultTaskModel().dolphinFlag).toBe('YES')
    expect(createDefaultTaskModel().datasourceType).toBeNull()
  })

  it('normalizes dolphinFlag and preserves it in save payload', () => {
    const payload = buildTaskPayload({
      ...createDefaultTaskModel(),
      taskName: 'task_demo',
      dolphinFlag: 'no',
      datasourceName: ' ',
      datasourceType: 'DORIS'
    })

    expect(payload.dolphinFlag).toBe('NO')
    expect(payload.datasourceName).toBeNull()
    expect(payload.datasourceType).toBeNull()
  })

  it('syncs datasourceType from matched dolphin datasource option', () => {
    const task = {
      ...createDefaultTaskModel(),
      datasourceName: 'oceanbase_prod',
      datasourceType: 'DORIS'
    }

    syncTaskDatasourceType(task, [
      { name: 'mysql_ds', type: 'MYSQL' },
      { name: 'oceanbase_prod', type: 'OCEANBASE' }
    ])

    expect(task.datasourceType).toBe('OCEANBASE')
    expect(buildTaskPayload(task).datasourceType).toBe('OCEANBASE')
  })

  it('clears datasourceType when datasourceName is empty', () => {
    const task = {
      ...createDefaultTaskModel(),
      datasourceName: '   ',
      datasourceType: 'OCEANBASE'
    }

    syncTaskDatasourceType(task, [{ name: 'oceanbase_prod', type: 'OCEANBASE' }])

    expect(task.datasourceName).toBe('')
    expect(task.datasourceType).toBeNull()
    expect(buildTaskPayload(task).datasourceType).toBeNull()
  })
})
