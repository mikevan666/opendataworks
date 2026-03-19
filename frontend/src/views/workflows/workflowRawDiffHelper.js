const RAW_DIFF_TYPES = {
  META_OLD: 'meta-old',
  META_NEW: 'meta-new',
  HUNK: 'hunk',
  ADDED: 'added',
  REMOVED: 'removed',
  CONTEXT: 'context'
}

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
      segments: [{ text: line, changed: false }]
    }
  }
  if (line.startsWith('+++ ')) {
    return {
      key: `${index}-meta-new`,
      type: RAW_DIFF_TYPES.META_NEW,
      prefix: '',
      text: line,
      segments: [{ text: line, changed: false }]
    }
  }
  if (line.startsWith('@@')) {
    return {
      key: `${index}-hunk`,
      type: RAW_DIFF_TYPES.HUNK,
      prefix: '',
      text: line,
      segments: [{ text: line, changed: false }]
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
    segments: [{ text, changed: false }]
  }
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

  return rows
}

export { RAW_DIFF_TYPES }
