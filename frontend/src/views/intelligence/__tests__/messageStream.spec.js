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

  it('marks tool invocation complete at content_block_stop before runtime starts', () => {
    const msg = createAssistantMessageState({ id: 'a4' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a4' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'tool_use', id: 'tool-read-2', name: 'Read' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'input_json_delta', partial_json: '{"file_path":"reference/11-datasource-routing.md"}' }
    })

    expect(msg.renderBlocks[0].tool._callComplete).toBe(false)
    expect(msg.renderBlocks[0].tool._runtimeStarted).toBe(false)

    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })

    expect(msg.renderBlocks[0].tool._callComplete).toBe(true)
    expect(msg.renderBlocks[0].tool._runtimeStarted).toBe(false)

    processAssistantStreamEvent(msg, {
      type: 'tool.pending',
      payload: { tool_id: 'tool-read-2', tool_name: 'Read' }
    })

    expect(msg.renderBlocks[0].tool._runtimeStarted).toBe(true)
    expect(msg.renderBlocks[0].tool.status).toBe('pending')
  })

  it('keeps a stable frontend id across multiple message_start events', () => {
    const msg = createAssistantMessageState({ id: 'view-1' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-a' } })
    processAssistantStreamEvent(msg, { type: 'message_stop' })
    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-b' } })

    expect(msg.id).toBe('view-1')
    expect(msg.message_id).toBe('msg-b')
  })

  it('does not merge blocks from different assistant messages in one run', () => {
    const msg = createAssistantMessageState({ id: 'view-2' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-a' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'tool_use', id: 'tool-skill-1', name: 'Skill' }
    })
    processAssistantStreamEvent(msg, { type: 'message_stop' })
    processAssistantStreamEvent(msg, {
      type: 'tool.complete',
      payload: { block_id: 'cb-0', tool_id: 'tool-skill-1', tool_name: 'Skill', output: 'Launching skill' }
    })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'msg-b' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'tool_use', id: 'tool-read-1', name: 'Read' }
    })

    expect(msg.renderBlocks).toHaveLength(2)
    expect(msg.renderBlocks[0].tool.name).toBe('Skill')
    expect(msg.renderBlocks[0].tool.output).toBe('Launching skill')
    expect(msg.renderBlocks[1].tool.name).toBe('Read')
    expect(msg.renderBlocks[0].id).not.toBe(msg.renderBlocks[1].id)
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

  it('handles server_tool_use blocks using the same tool trace path', () => {
    const msg = createAssistantMessageState({ id: 'a5' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a5' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'server_tool_use', id: 'srv-1', name: 'WebFetch' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'input_json_delta', partial_json: '{"url":"https://example.com"}' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })

    expect(msg.renderBlocks[0].kind).toBe('tool')
    expect(msg.renderBlocks[0].tool.name).toBe('WebFetch')
    expect(msg.renderBlocks[0].tool.input).toEqual({ url: 'https://example.com' })
    expect(msg.renderBlocks[0].tool._callComplete).toBe(true)
  })

  it('captures signature deltas and message usage metadata', () => {
    const msg = createAssistantMessageState({ id: 'a6' })

    processAssistantStreamEvent(msg, {
      type: 'message_start',
      message: { id: 'a6', usage: { input_tokens: 12 } }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'thinking' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'signature_delta', signature: 'sig-part-1' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'signature_delta', signature: 'sig-part-2' }
    })
    processAssistantStreamEvent(msg, {
      type: 'message_delta',
      delta: { stop_reason: 'end_turn', stop_sequence: '\n\n', usage: { output_tokens: 8 } }
    })

    expect(msg.renderBlocks[0].payload.signature).toBe('sig-part-1sig-part-2')
    expect(msg.stop_reason).toBe('end_turn')
    expect(msg.stop_sequence).toBe('\n\n')
    expect(msg.usage).toEqual({ input_tokens: 12, output_tokens: 8 })
  })

  it('keeps usage metadata scoped to each assistant message segment', () => {
    const msg = createAssistantMessageState({ id: 'a8' })

    processAssistantStreamEvent(msg, {
      type: 'message_start',
      message: { id: 'seg-1', usage: { input_tokens: 10 } }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'text' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'text_delta', text: '第一段' }
    })
    processAssistantStreamEvent(msg, {
      type: 'message_delta',
      delta: { usage: { output_tokens: 3 } }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })
    processAssistantStreamEvent(msg, { type: 'message_stop' })

    processAssistantStreamEvent(msg, {
      type: 'message_start',
      message: { id: 'seg-2', usage: { input_tokens: 20 } }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'text' }
    })
    processAssistantStreamEvent(msg, {
      type: 'content_block_delta',
      index: 0,
      delta: { type: 'text_delta', text: '第二段' }
    })
    processAssistantStreamEvent(msg, {
      type: 'message_delta',
      delta: { usage: { output_tokens: 6 } }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })
    processAssistantStreamEvent(msg, { type: 'message_stop' })

    expect(msg.renderBlocks[0].messageKey).toBe('m1')
    expect(msg.renderBlocks[1].messageKey).toBe('m2')
    expect(msg._messageMeta.m1.usage).toEqual({ input_tokens: 10, output_tokens: 3 })
    expect(msg._messageMeta.m2.usage).toEqual({ input_tokens: 20, output_tokens: 6 })
  })

  it('treats tool_result block stop as terminal tool completion', () => {
    const msg = createAssistantMessageState({ id: 'a7' })

    processAssistantStreamEvent(msg, { type: 'message_start', message: { id: 'a7' } })
    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 0,
      content_block: { type: 'tool_use', id: 'tool-read-3', name: 'Read' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 0 })
    processAssistantStreamEvent(msg, {
      type: 'tool.output',
      payload: { tool_id: 'tool-read-3', tool_name: 'Read', output: '## 引用内容' }
    })

    expect(msg.renderBlocks[0].tool.status).toBe('streaming')

    processAssistantStreamEvent(msg, {
      type: 'content_block_start',
      index: 1,
      content_block: { type: 'tool_result', tool_use_id: 'tool-read-3', content: '## 引用内容' }
    })
    processAssistantStreamEvent(msg, { type: 'content_block_stop', index: 1 })

    expect(msg.renderBlocks).toHaveLength(1)
    expect(msg.renderBlocks[0].tool._resultStarted).toBe(true)
    expect(msg.renderBlocks[0].tool.status).toBe('success')
  })
})
