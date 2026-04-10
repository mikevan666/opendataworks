import { formatFieldValue } from './publishPreviewHelper'
import { buildInlineChangeSegments } from './workflowRawDiffHelper'

export const PUBLISH_DIFF_ROW_TYPES = {
  ADDED: 'added',
  REMOVED: 'removed',
  MODIFIED: 'modified'
}

const splitLines = (value) => {
  const normalized = String(value ?? '').replace(/\r\n/g, '\n')
  if (!normalized) {
    return []
  }
  const lines = normalized.split('\n')
  if (lines.length > 1 && lines[lines.length - 1] === '') {
    lines.pop()
  }
  return lines
}

const buildLcsMatrix = (leftLines, rightLines) => {
  const rowCount = leftLines.length
  const columnCount = rightLines.length
  const matrix = Array.from({ length: rowCount + 1 }, () => Array(columnCount + 1).fill(0))

  for (let leftIndex = rowCount - 1; leftIndex >= 0; leftIndex -= 1) {
    for (let rightIndex = columnCount - 1; rightIndex >= 0; rightIndex -= 1) {
      matrix[leftIndex][rightIndex] = leftLines[leftIndex] === rightLines[rightIndex]
        ? matrix[leftIndex + 1][rightIndex + 1] + 1
        : Math.max(matrix[leftIndex + 1][rightIndex], matrix[leftIndex][rightIndex + 1])
    }
  }

  return matrix
}

const createSegments = (text) => [{ text, changed: false }]

const createLineCell = (text, lineNumber) => ({
  text,
  lineNumber,
  segments: createSegments(text)
})

const pairDiffBlock = (rows, removedBlock, addedBlock) => {
  const pairCount = Math.max(removedBlock.length, addedBlock.length)

  for (let index = 0; index < pairCount; index += 1) {
    const left = removedBlock[index] || null
    const right = addedBlock[index] || null

    if (left && right) {
      const inlineSegments = buildInlineChangeSegments(left.text, right.text)
      rows.push({
        key: `modified-${left.lineNumber}-${right.lineNumber}-${index}`,
        type: PUBLISH_DIFF_ROW_TYPES.MODIFIED,
        left: {
          ...left,
          prefix: '~',
          segments: inlineSegments.removed
        },
        right: {
          ...right,
          prefix: '~',
          segments: inlineSegments.added
        }
      })
      continue
    }

    if (left) {
      rows.push({
        key: `removed-${left.lineNumber}-${index}`,
        type: PUBLISH_DIFF_ROW_TYPES.REMOVED,
        left: {
          ...left,
          prefix: '-'
        },
        right: null
      })
      continue
    }

    rows.push({
      key: `added-${right?.lineNumber || index}-${index}`,
      type: PUBLISH_DIFF_ROW_TYPES.ADDED,
      left: null,
      right: {
        ...right,
        prefix: '+'
      }
    })
  }
}

export const buildTaskFieldDiffRows = (beforeValue, afterValue) => {
  const beforeText = formatFieldValue(beforeValue, { preserveEmpty: true })
  const afterText = formatFieldValue(afterValue, { preserveEmpty: true })
  const leftLines = splitLines(beforeText)
  const rightLines = splitLines(afterText)

  if (!leftLines.length && !rightLines.length) {
    return []
  }

  const matrix = buildLcsMatrix(leftLines, rightLines)
  const rows = []
  let leftIndex = 0
  let rightIndex = 0
  let leftLineNumber = 1
  let rightLineNumber = 1

  while (leftIndex < leftLines.length && rightIndex < rightLines.length) {
    if (leftLines[leftIndex] === rightLines[rightIndex]) {
      leftIndex += 1
      rightIndex += 1
      leftLineNumber += 1
      rightLineNumber += 1
      continue
    }

    const removedBlock = []
    const addedBlock = []

    while (
      leftIndex < leftLines.length
      && rightIndex < rightLines.length
      && leftLines[leftIndex] !== rightLines[rightIndex]
    ) {
      if (matrix[leftIndex + 1][rightIndex] >= matrix[leftIndex][rightIndex + 1]) {
        removedBlock.push(createLineCell(leftLines[leftIndex], leftLineNumber))
        leftIndex += 1
        leftLineNumber += 1
      } else {
        addedBlock.push(createLineCell(rightLines[rightIndex], rightLineNumber))
        rightIndex += 1
        rightLineNumber += 1
      }
    }

    pairDiffBlock(rows, removedBlock, addedBlock)
  }

  const remainingRemoved = []
  const remainingAdded = []

  while (leftIndex < leftLines.length) {
    remainingRemoved.push(createLineCell(leftLines[leftIndex], leftLineNumber))
    leftIndex += 1
    leftLineNumber += 1
  }

  while (rightIndex < rightLines.length) {
    remainingAdded.push(createLineCell(rightLines[rightIndex], rightLineNumber))
    rightIndex += 1
    rightLineNumber += 1
  }

  pairDiffBlock(rows, remainingRemoved, remainingAdded)

  return rows
}

export const summarizeTaskFieldDiffRows = (rows = []) => {
  return rows.reduce((summary, row) => {
    if (row?.type === PUBLISH_DIFF_ROW_TYPES.ADDED) {
      summary.added += 1
    } else if (row?.type === PUBLISH_DIFF_ROW_TYPES.REMOVED) {
      summary.removed += 1
    } else if (row?.type === PUBLISH_DIFF_ROW_TYPES.MODIFIED) {
      summary.modified += 1
    }
    return summary
  }, {
    added: 0,
    removed: 0,
    modified: 0
  })
}
