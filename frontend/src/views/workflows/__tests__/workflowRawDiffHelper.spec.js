import { buildInlineChangeSegments, buildRawDiffRows, RAW_DIFF_TYPES } from '../workflowRawDiffHelper'

describe('workflowRawDiffHelper', () => {
  it('classifies diff header and content rows', () => {
    const rows = buildRawDiffRows(['--- v1', '+++ v2', '@@ JSON Snapshot @@', ' {"a":1}', '-  "name": "old"', '+  "name": "new"'].join('\n'))

    expect(rows[0].type).toBe(RAW_DIFF_TYPES.META_OLD)
    expect(rows[1].type).toBe(RAW_DIFF_TYPES.META_NEW)
    expect(rows[2].type).toBe(RAW_DIFF_TYPES.HUNK)
    expect(rows[3].type).toBe(RAW_DIFF_TYPES.CONTEXT)
    expect(rows[4].type).toBe(RAW_DIFF_TYPES.REMOVED)
    expect(rows[5].type).toBe(RAW_DIFF_TYPES.ADDED)
  })

  it('highlights inline changes for adjacent removed and added rows', () => {
    const rows = buildRawDiffRows(['-  "name": "old_value",', '+  "name": "new_value",'].join('\n'))

    const removedChanged = rows[0].segments.filter((segment) => segment.changed).map((segment) => segment.text)
    const addedChanged = rows[1].segments.filter((segment) => segment.changed).map((segment) => segment.text)

    expect(removedChanged).toEqual(['old'])
    expect(addedChanged).toEqual(['new'])
  })

  it('keeps equal text as unchanged segments', () => {
    const segments = buildInlineChangeSegments('  "name": "same"', '  "name": "same"')

    expect(segments.removed).toEqual([{ text: '  "name": "same"', changed: false }])
    expect(segments.added).toEqual([{ text: '  "name": "same"', changed: false }])
  })
})
