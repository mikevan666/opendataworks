const UTF8_BOM = '\uFEFF'
const CSV_LINE_SEPARATOR = '\r\n'

const startsWithSpreadsheetFormulaPrefix = (value) => /^[=+\-@]/.test(value)

export const formatCsvValue = (value) => {
  if (value === null || value === undefined) return ''
  const str = String(value)
  if (
    str.includes(',') ||
    str.includes('"') ||
    str.includes('\n') ||
    str.includes('\r') ||
    startsWithSpreadsheetFormulaPrefix(str)
  ) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export const buildCsvContent = (columns = [], rows = []) => {
  const header = columns.map((col) => formatCsvValue(col)).join(',')
  const body = rows
    .map((row) => columns.map((col) => formatCsvValue(row?.[col])).join(','))
    .join(CSV_LINE_SEPARATOR)
  return `${UTF8_BOM}${header}${CSV_LINE_SEPARATOR}${body ? `${body}${CSV_LINE_SEPARATOR}` : ''}`
}
