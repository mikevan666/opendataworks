import { describe, expect, it } from 'vitest'
import { buildTaskPayload, createDefaultTaskModel } from '../taskEditForm'

describe('taskEditForm', () => {
  it('defaults dolphinFlag to YES for new tasks', () => {
    expect(createDefaultTaskModel().dolphinFlag).toBe('YES')
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
})
