import {
  buildInlineChangeSegments,
  buildRawDiffRows,
  buildSplitViewRows,
  buildUnifiedViewRows,
  RAW_DIFF_TYPES
} from '../workflowRawDiffHelper'

describe('workflowRawDiffHelper', () => {
  it('classifies diff header and content rows', () => {
    const rows = buildRawDiffRows(['--- v1', '+++ v2', '@@ JSON Snapshot @@', ' {"a":1}', '-  "name": "old"', '+  "name": "new"'].join('\n'))

    expect(rows[0].type).toBe(RAW_DIFF_TYPES.META_OLD)
    expect(rows[1].type).toBe(RAW_DIFF_TYPES.META_NEW)
    expect(rows[2].type).toBe(RAW_DIFF_TYPES.HUNK)
    expect(rows[3].type).toBe(RAW_DIFF_TYPES.CONTEXT)
    expect(rows[4].type).toBe(RAW_DIFF_TYPES.REMOVED)
    expect(rows[5].type).toBe(RAW_DIFF_TYPES.ADDED)
    expect(rows[3].leftLineNumber).toBe(1)
    expect(rows[3].rightLineNumber).toBe(1)
    expect(rows[4].leftLineNumber).toBe(2)
    expect(rows[4].rightLineNumber).toBeNull()
    expect(rows[5].leftLineNumber).toBeNull()
    expect(rows[5].rightLineNumber).toBe(2)
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

  it('filters unified view to diffs while keeping meta rows', () => {
    const rows = buildRawDiffRows(['--- v1', '+++ v2', '@@ JSON Snapshot @@', ' {"a":1}', '-  "name": "old"', '+  "name": "new"'].join('\n'))
    const unifiedRows = buildUnifiedViewRows(rows, { showAll: false })

    expect(unifiedRows.map((row) => row.type)).toEqual([
      RAW_DIFF_TYPES.META_OLD,
      RAW_DIFF_TYPES.META_NEW,
      RAW_DIFF_TYPES.HUNK,
      RAW_DIFF_TYPES.REMOVED,
      RAW_DIFF_TYPES.ADDED
    ])
  })

  it('keeps context rows in unified all mode', () => {
    const rows = buildRawDiffRows(['--- v1', '+++ v2', '@@ JSON Snapshot @@', ' {"a":1}', '-  "name": "old"', '+  "name": "new"'].join('\n'))
    const unifiedRows = buildUnifiedViewRows(rows, { showAll: true })

    expect(unifiedRows.map((row) => row.type)).toEqual([
      RAW_DIFF_TYPES.META_OLD,
      RAW_DIFF_TYPES.META_NEW,
      RAW_DIFF_TYPES.HUNK,
      RAW_DIFF_TYPES.CONTEXT,
      RAW_DIFF_TYPES.REMOVED,
      RAW_DIFF_TYPES.ADDED
    ])
  })

  it('builds split rows with paired additions and removals', () => {
    const rows = buildRawDiffRows([
      '--- v1',
      '+++ v2',
      '@@ JSON Snapshot @@',
      ' {',
      '-  "name": "old",',
      '-  "status": "offline"',
      '+  "name": "new",',
      '+  "status": "online"',
      '+  "extra": true',
      ' }'
    ].join('\n'))
    const splitRows = buildSplitViewRows(rows, { showAll: false })

    expect(splitRows).toHaveLength(6)
    expect(splitRows[0].isControl).toBe(true)
    expect(splitRows[1].isControl).toBe(true)
    expect(splitRows[2].isControl).toBe(true)

    expect(splitRows[3].left?.type).toBe(RAW_DIFF_TYPES.REMOVED)
    expect(splitRows[3].right?.type).toBe(RAW_DIFF_TYPES.ADDED)
    expect(splitRows[3].left?.leftLineNumber).toBe(2)
    expect(splitRows[3].right?.rightLineNumber).toBe(2)

    expect(splitRows[4].left?.type).toBe(RAW_DIFF_TYPES.REMOVED)
    expect(splitRows[4].right?.type).toBe(RAW_DIFF_TYPES.ADDED)
    expect(splitRows[4].left?.leftLineNumber).toBe(3)
    expect(splitRows[4].right?.rightLineNumber).toBe(3)

    expect(splitRows[5].left).toBeNull()
    expect(splitRows[5].right?.type).toBe(RAW_DIFF_TYPES.ADDED)
    expect(splitRows[5].right?.rightLineNumber).toBe(4)
  })

  it('keeps context rows in split all mode', () => {
    const rows = buildRawDiffRows([
      '--- v1',
      '+++ v2',
      '@@ JSON Snapshot @@',
      ' {',
      '-  "name": "old"',
      '+  "name": "new"',
      ' }'
    ].join('\n'))
    const splitRows = buildSplitViewRows(rows, { showAll: true })
    const contextRow = splitRows.find((row) => !row.isControl && row.left?.type === RAW_DIFF_TYPES.CONTEXT)

    expect(contextRow).toBeTruthy()
    expect(contextRow.left?.leftLineNumber).toBe(1)
    expect(contextRow.right?.rightLineNumber).toBe(1)
  })
})
