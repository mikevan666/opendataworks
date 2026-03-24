const RAW_DIFF_TYPES = {
  META_OLD: 'meta-old',
  META_NEW: 'meta-new',
  HUNK: 'hunk',
  ADDED: 'added',
  REMOVED: 'removed',
  CONTEXT: 'context'
}

const CONTROL_ROW_TYPES = [RAW_DIFF_TYPES.META_OLD, RAW_DIFF_TYPES.META_NEW, RAW_DIFF_TYPES.HUNK]

const toSegments = (text, start, end) => {
  const segments = []
  const safeStart = Math.max(0, start)
  const safeEnd = Math.max(safeStart, end)

  if (safeStart > 0) {
    segments.push({ text: text.slice(0, safeStart), changed: false })
  }
  if (safeEnd > safeStart) {
    segments.push({ text: text.slice(safeStart, safeEnd), changed: true })
  }
  if (safeEnd < text.length) {
    segments.push({ text: text.slice(safeEnd), changed: false })
  }
  if (!segments.length) {
    segments.push({ text, changed: false })
  }
  return segments
}

export const buildInlineChangeSegments = (removedText, addedText) => {
  if (removedText === addedText) {
    return {
      removed: [{ text: removedText, changed: false }],
      added: [{ text: addedText, changed: false }]
    }
  }

  let prefixLength = 0
  const maxPrefixLength = Math.min(removedText.length, addedText.length)
  while (prefixLength < maxPrefixLength && removedText[prefixLength] === addedText[prefixLength]) {
    prefixLength += 1
  }

  let suffixLength = 0
  const maxSuffixLength = Math.min(removedText.length - prefixLength, addedText.length - prefixLength)
  while (
    suffixLength < maxSuffixLength
    && removedText[removedText.length - 1 - suffixLength] === addedText[addedText.length - 1 - suffixLength]
  ) {
    suffixLength += 1
  }

  const removedChangeEnd = removedText.length - suffixLength
  const addedChangeEnd = addedText.length - suffixLength

  return {
    removed: toSegments(removedText, prefixLength, removedChangeEnd),
    added: toSegments(addedText, prefixLength, addedChangeEnd)
  }
}

const createRow = (line, index) => {
  if (line.startsWith('--- ')) {
    return {
      key: `${index}-meta-old`,
      type: RAW_DIFF_TYPES.META_OLD,
      prefix: '',
      text: line,
      segments: [{ text: line, changed: false }],
      leftLineNumber: null,
      rightLineNumber: null
    }
  }
  if (line.startsWith('+++ ')) {
    return {
      key: `${index}-meta-new`,
      type: RAW_DIFF_TYPES.META_NEW,
      prefix: '',
      text: line,
      segments: [{ text: line, changed: false }],
      leftLineNumber: null,
      rightLineNumber: null
    }
  }
  if (line.startsWith('@@')) {
    return {
      key: `${index}-hunk`,
      type: RAW_DIFF_TYPES.HUNK,
      prefix: '',
      text: line,
      segments: [{ text: line, changed: false }],
      leftLineNumber: null,
      rightLineNumber: null
    }
  }

  const prefix = line.charAt(0)
  const text = line.slice(1)
  const type = prefix === '+'
    ? RAW_DIFF_TYPES.ADDED
    : prefix === '-'
      ? RAW_DIFF_TYPES.REMOVED
      : RAW_DIFF_TYPES.CONTEXT

  return {
    key: `${index}-${type}`,
    type,
    prefix,
    text,
    segments: [{ text, changed: false }],
    leftLineNumber: null,
    rightLineNumber: null
  }
}

const isControlRow = (row) => CONTROL_ROW_TYPES.includes(row?.type)

const highlightInlineChanges = (rows) => {
  let index = 0
  while (index < rows.length) {
    if (rows[index].type !== RAW_DIFF_TYPES.REMOVED) {
      index += 1
      continue
    }

    const removedIndexes = []
    while (index < rows.length && rows[index].type === RAW_DIFF_TYPES.REMOVED) {
      removedIndexes.push(index)
      index += 1
    }

    const addedIndexes = []
    while (index < rows.length && rows[index].type === RAW_DIFF_TYPES.ADDED) {
      addedIndexes.push(index)
      index += 1
    }

    const pairCount = Math.min(removedIndexes.length, addedIndexes.length)
    for (let offset = 0; offset < pairCount; offset += 1) {
      const removedRow = rows[removedIndexes[offset]]
      const addedRow = rows[addedIndexes[offset]]
      const segments = buildInlineChangeSegments(removedRow.text, addedRow.text)
      removedRow.segments = segments.removed
      addedRow.segments = segments.added
    }
  }
}

const assignLineNumbers = (rows) => {
  let leftLineNumber = 1
  let rightLineNumber = 1

  rows.forEach((row) => {
    if (isControlRow(row)) {
      row.leftLineNumber = null
      row.rightLineNumber = null
      return
    }

    if (row.type === RAW_DIFF_TYPES.REMOVED) {
      row.leftLineNumber = leftLineNumber
      row.rightLineNumber = null
      leftLineNumber += 1
      return
    }

    if (row.type === RAW_DIFF_TYPES.ADDED) {
      row.leftLineNumber = null
      row.rightLineNumber = rightLineNumber
      rightLineNumber += 1
      return
    }

    row.leftLineNumber = leftLineNumber
    row.rightLineNumber = rightLineNumber
    leftLineNumber += 1
    rightLineNumber += 1
  })
}

export const buildRawDiffRows = (rawDiff) => {
  if (!rawDiff) {
    return []
  }

  const lines = String(rawDiff)
    .replace(/\r\n/g, '\n')
    .split('\n')

  if (lines.length && lines[lines.length - 1] === '') {
    lines.pop()
  }

  const rows = lines.map((line, index) => createRow(line, index))
  highlightInlineChanges(rows)
  assignLineNumbers(rows)
  return rows
}

const shouldKeepRow = (row, showAll) => {
  if (showAll) {
    return true
  }
  return row.type !== RAW_DIFF_TYPES.CONTEXT || isControlRow(row)
}

export const buildUnifiedViewRows = (rows, options = {}) => {
  const showAll = options?.showAll === true
  return Array.isArray(rows) ? rows.filter((row) => shouldKeepRow(row, showAll)) : []
}

const collectRows = (rows, startIndex, targetType) => {
  const items = []
  let index = startIndex
  while (index < rows.length && rows[index].type === targetType) {
    items.push(rows[index])
    index += 1
  }
  return {
    items,
    nextIndex: index
  }
}

const createSplitControlRow = (row) => ({
  key: `split-${row.key}`,
  type: row.type,
  isControl: true,
  segments: row.segments,
  text: row.text
})

const createSplitContentRow = (key, left, right) => ({
  key,
  type: left && right ? 'modified' : (left?.type || right?.type || RAW_DIFF_TYPES.CONTEXT),
  isControl: false,
  left,
  right
})

export const buildSplitViewRows = (rows, options = {}) => {
  if (!Array.isArray(rows) || !rows.length) {
    return []
  }

  const showAll = options?.showAll === true
  const splitRows = []
  let index = 0

  while (index < rows.length) {
    const row = rows[index]

    if (isControlRow(row)) {
      splitRows.push(createSplitControlRow(row))
      index += 1
      continue
    }

    if (row.type === RAW_DIFF_TYPES.CONTEXT) {
      if (showAll) {
        splitRows.push(createSplitContentRow(`split-${row.key}`, row, row))
      }
      index += 1
      continue
    }

    if (row.type === RAW_DIFF_TYPES.REMOVED) {
      const removedBlock = collectRows(rows, index, RAW_DIFF_TYPES.REMOVED)
      const addedBlock = collectRows(rows, removedBlock.nextIndex, RAW_DIFF_TYPES.ADDED)
      const pairCount = Math.max(removedBlock.items.length, addedBlock.items.length)

      for (let offset = 0; offset < pairCount; offset += 1) {
        const left = removedBlock.items[offset] || null
        const right = addedBlock.items[offset] || null
        splitRows.push(createSplitContentRow(
          `split-${left?.key || 'empty-left'}-${right?.key || 'empty-right'}`,
          left,
          right
        ))
      }

      index = addedBlock.nextIndex
      continue
    }

    const addedBlock = collectRows(rows, index, RAW_DIFF_TYPES.ADDED)
    addedBlock.items.forEach((addedRow) => {
      splitRows.push(createSplitContentRow(`split-empty-${addedRow.key}`, null, addedRow))
    })
    index = addedBlock.nextIndex
  }

  return splitRows
}

export { RAW_DIFF_TYPES }
