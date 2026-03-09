import { describe, expect, it } from 'vitest'
import {
  createAssistantMessageState,
  processAssistantStreamEvent
} from '../messageStream'

describe('messageStream', () => {
  it('appends render blocks in stream order', () => {
    const msg = createAssistantMessageState({ id: 'a1' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a1' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'thinking' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'thinking_delta', thinking: '先定位元数据' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })

    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 1,
      content_block: { type: 'tool_use', id: 'tool-read-1', name: 'Read' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 1,
      delta: { type: 'input_json_delta', partial_json: '{"file_path":"reference/00-skill-map.md"}' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 1 })
    processAssistantStreamEvent(msg, {
      type: 'tool.pending',
      payload: { tool_id: 'tool-read-1', tool_name: 'Read' }
    })
    processAssistantStreamEvent(msg, {
      type: 'tool.complete',
      payload: { tool_id: 'tool-read-1', tool_name: 'Read', output: '读取完成' }
    })

    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 2,
      content_block: { type: 'text' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 2,
      delta: { type: 'text_delta', text: '最终答案' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 2 })
    processAssistantStreamEvent(msg, {
      type: 'done',
      payload: { status: 'success', content: '最终答案' }
    })

    expect(msg.renderBlocks.map((block) => block.kind)).toEqual(['thinking', 'tool', 'main_text'])
    expect(msg.renderBlocks[0].text).toBe('先定位元数据')
    expect(msg.renderBlocks[1].tool.name).toBe('Read')
    expect(msg.renderBlocks[1].tool.status).toBe('success')
    expect(msg.renderBlocks[1].tool.input).toEqual({ file_path: 'reference/00-skill-map.md' })
    expect(msg.renderBlocks[2].text).toBe('最终答案')
  })

  it('keeps message streaming after message_stop until done arrives', () => {
    const msg = createAssistantMessageState({ id: 'a2' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a2' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'tool_use', id: 'tool-bash-1', name: 'Bash' }
    })
    processAssistantStreamEvent(msg, { type: 'message_stop' })

    expect(msg.status).toBe('streaming')
    expect(msg.renderBlocks[0].tool.status).toBe('streaming')

    processAssistantStreamEvent(msg, {
      type: 'tool.output',
      payload: { tool_id: 'tool-bash-1', tool_name: 'Bash', output: 'stdout line 1\n' }
    })

    expect(msg.renderBlocks[0].tool.output).toBe('stdout line 1\n')
  })

  it('keeps a stable frontend id across multiple message_start events', () => {
    const msg = createAssistantMessageState({ id: 'view-1' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-a' } })
    processAssistantStreamEvent(msg, { type: 'message_stop' })
    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-b' } })

    expect(msg.id).toBe('view-1')
    expect(msg.message_id).toBe('msg-b')
  })

  it('does not overwrite streamed text block on done', () => {
    const msg = createAssistantMessageState({ id: 'a3' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a3' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'text' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'text_delta', text: '流式正文' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })
    processAssistantStreamEvent(msg, {
      type: 'done',
      payload: { status: 'success', content: '清理后的最终正文' }
    })

    expect(msg.renderBlocks).toHaveLength(1)
    expect(msg.renderBlocks[0].kind).toBe('main_text')
    expect(msg.renderBlocks[0].text).toBe('流式正文')
    expect(msg.content).toBe('清理后的最终正文')
  })
})
