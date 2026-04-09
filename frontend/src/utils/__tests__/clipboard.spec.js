import { afterEach, describe, expect, it, vi } from 'vitest'
import { copyText } from '../clipboard'

const originalClipboard = navigator.clipboard
const originalExecCommand = document.execCommand

afterEach(() => {
  vi.restoreAllMocks()

  if (originalClipboard === undefined) {
    Reflect.deleteProperty(navigator, 'clipboard')
  } else {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: originalClipboard
    })
  }

  if (originalExecCommand === undefined) {
    Reflect.deleteProperty(document, 'execCommand')
  } else {
    document.execCommand = originalExecCommand
  }

  document.body.innerHTML = ''
})

describe('copyText', () => {
  it('uses the clipboard api when available', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText }
    })
    document.execCommand = vi.fn()

    await copyText('CREATE TABLE demo')

    expect(writeText).toHaveBeenCalledWith('CREATE TABLE demo')
    expect(document.execCommand).not.toHaveBeenCalled()
  })

  it('falls back to execCommand when clipboard api rejects', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('denied'))
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText }
    })
    document.execCommand = vi.fn(() => true)

    await copyText('CREATE TABLE demo')

    expect(writeText).toHaveBeenCalledWith('CREATE TABLE demo')
    expect(document.execCommand).toHaveBeenCalledWith('copy')
    expect(document.querySelector('textarea')).toBeNull()
  })
})
