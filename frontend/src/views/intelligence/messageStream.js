const isPlainObject = (value) => value && typeof value === 'object' && !Array.isArray(value)

const textOrEmpty = (value) => (value == null ? '' : String(value))

export const appendStr = (base, delta) => {
  const next = String(delta || '')
  if (!next) return String(base || '')
  const prev = String(base || '')
  if (!prev) return next
  if (next === prev) return prev
  if (next.startsWith(prev)) return next
  return prev + next
}

export const parseMaybeJson = (value) => {
  if (typeof value !== 'string') return null
  const raw = value.trim()
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (_error) {
    return null
  }
}

const normalizeToolId = (value) => {
  const text = textOrEmpty(value).trim()
  return text || ''
}

const toolStatusFromEvent = (eventType) => {
  if (eventType === 'tool.pending') return 'pending'
  if (eventType === 'tool.complete') return 'success'
  if (eventType === 'tool.failed') return 'failed'
  return 'streaming'
}

const ensureRenderBlock = (msg, blockId, kind, defaults = {}) => {
  const key = String(blockId || '').trim() || `block-${msg.renderBlocks.length + 1}`
  if (!msg._renderBlockMap[key]) {
    const block = {
      id: key,
      kind,
      status: defaults.status || 'streaming',
      text: defaults.text || '',
      payload: defaults.payload || {},
      tool: defaults.tool || null,
      _partialJson: ''
    }
    msg._renderBlockMap[key] = block
    msg.renderBlocks.push(block)
  }
  const block = msg._renderBlockMap[key]
  if (kind && (!block.kind || block.kind === 'raw')) block.kind = kind
  return block
}

const extractToolEnvelope = (block) => {
  if (!isPlainObject(block)) return null
  const payload = isPlainObject(block.payload) ? block.payload : {}
  const toolId = normalizeToolId(block.tool_id || payload.tool_id || payload.tool_use_id || payload.id)
  const toolName = textOrEmpty(block.tool_name || payload.tool_name || payload.name).trim()
  const hasEnvelope = Boolean(
    toolId
    || toolName
    || Object.prototype.hasOwnProperty.call(block, 'input')
    || Object.prototype.hasOwnProperty.call(block, 'output')
    || Object.prototype.hasOwnProperty.call(payload, 'input')
    || Object.prototype.hasOwnProperty.call(payload, 'output')
    || Object.prototype.hasOwnProperty.call(payload, 'content')
  )
  if (!hasEnvelope) return null
  return {
    toolId,
    name: toolName || 'Tool',
    input: Object.prototype.hasOwnProperty.call(block, 'input') ? block.input : payload.input,
    output: Object.prototype.hasOwnProperty.call(block, 'output') ? block.output : (payload.output ?? payload.content),
    status: textOrEmpty(block.status).trim() || 'success'
  }
}

const ensureToolRenderBlock = (msg, patch = {}) => {
  const toolId = normalizeToolId(patch.toolId)
  const blockKey = textOrEmpty(patch.blockKey).trim()
  const mappedBlockId = toolId ? msg._toolBlockIds[toolId] : ''
  const renderId = mappedBlockId || blockKey || `tool-${toolId || msg.renderBlocks.length + 1}`
  const block = ensureRenderBlock(msg, renderId, 'tool', {
    status: textOrEmpty(patch.status).trim() || 'pending',
    tool: {
      id: toolId || renderId,
      _toolId: toolId || '',
      _blockKey: blockKey,
      name: textOrEmpty(patch.name).trim() || 'Tool',
      status: textOrEmpty(patch.status).trim() || 'pending',
      input: null,
      output: null
    }
  })

  if (!block.tool) {
    block.tool = {
      id: toolId || renderId,
      _toolId: toolId || '',
      _blockKey: blockKey,
      name: textOrEmpty(patch.name).trim() || 'Tool',
      status: textOrEmpty(patch.status).trim() || 'pending',
      input: null,
      output: null
    }
  }

  const tool = block.tool
  if (toolId) {
    tool.id = toolId
    tool._toolId = toolId
    msg._toolBlockIds[toolId] = renderId
  }
  if (blockKey) tool._blockKey = blockKey
  if (patch.name) tool.name = textOrEmpty(patch.name).trim()
  if (Object.prototype.hasOwnProperty.call(patch, 'input') && patch.input !== undefined) {
    tool.input = patch.input
  }
  if (Object.prototype.hasOwnProperty.call(patch, 'output') && patch.output !== undefined) {
    if (typeof tool.output === 'string' && typeof patch.output === 'string') {
      tool.output = appendStr(tool.output, patch.output)
    } else {
      tool.output = patch.output
    }
  }

  if (patch.status) {
    tool.status = textOrEmpty(patch.status).trim()
    block.status = tool.status
  }

  if (['pending', 'streaming'].includes(tool.status)) {
    tool._startedAt = tool._startedAt || Date.now()
    delete tool._completedAt
  }
  if (['success', 'failed'].includes(tool.status)) {
    tool._completedAt = tool._completedAt || Date.now()
  }

  return block
}

const ensureTextBlock = (msg, blockId, kind) => ensureRenderBlock(msg, blockId, kind, { status: 'streaming', text: '' })

const markAllStreamingBlocksComplete = (msg) => {
  for (const block of msg.renderBlocks) {
    if (block.kind === 'tool' && block.tool && ['pending', 'streaming'].includes(block.tool.status)) {
      block.tool.status = 'success'
      block.status = 'success'
      block.tool._completedAt = block.tool._completedAt || Date.now()
      continue
    }
    if (['pending', 'streaming', 'in_progress'].includes(textOrEmpty(block.status))) {
      block.status = 'success'
    }
  }
}

const markMessageBlocksComplete = (msg) => {
  for (const block of msg.renderBlocks) {
    if (block.kind === 'tool') continue
    if (['pending', 'streaming', 'in_progress'].includes(textOrEmpty(block.status))) {
      block.status = 'success'
    }
  }
}

const createErrorBlock = (msg, text) => {
  const block = ensureRenderBlock(msg, `error-${msg.renderBlocks.length + 1}`, 'error', { status: 'failed', text })
  block.status = 'failed'
  block.text = textOrEmpty(text)
  return block
}

const hasRenderableMainText = (msg) => msg.renderBlocks.some((block) => block.kind === 'main_text' && textOrEmpty(block.text).trim())

export const createAssistantMessageState = (seed = {}) => ({
  id: textOrEmpty(seed.id).trim() || '',
  message_id: textOrEmpty(seed.message_id || seed.id).trim() || '',
  role: 'assistant',
  content: textOrEmpty(seed.content),
  status: textOrEmpty(seed.status).trim() || 'streaming',
  mainText: textOrEmpty(seed.mainText || seed.content),
  thinkingText: textOrEmpty(seed.thinkingText),
  citations: Array.isArray(seed.citations) ? [...seed.citations] : [],
  error: seed.error || null,
  stop_reason: textOrEmpty(seed.stop_reason),
  provider_id: seed.provider_id || null,
  model: seed.model || null,
  created_at: seed.created_at || new Date().toISOString(),
  renderBlocks: [],
  _renderBlockMap: Object.create(null),
  _toolBlockIds: Object.create(null),
  _streamMessageSeq: 0,
  _activeMessageKey: 'm0',
  _rawBlockIds: Object.create(null)
})

export const hydrateAssistantMessageState = (message) => {
  const msg = createAssistantMessageState({
    id: textOrEmpty(message?.message_id).trim(),
    message_id: textOrEmpty(message?.message_id).trim(),
    content: textOrEmpty(message?.content),
    status: textOrEmpty(message?.status).trim() || 'success',
    stop_reason: textOrEmpty(message?.stop_reason),
    created_at: message?.created_at,
    error: isPlainObject(message?.error) ? message.error : null,
    provider_id: message?.provider_id || null,
    model: message?.model || null
  })

  const rawBlocks = Array.isArray(message?.blocks) ? message.blocks : []
  for (const rawBlock of rawBlocks) {
    if (!isPlainObject(rawBlock)) continue
    const blockId = textOrEmpty(rawBlock.block_id).trim() || `stored-${msg.renderBlocks.length + 1}`
    const blockType = textOrEmpty(rawBlock.type).trim()
    const blockStatus = textOrEmpty(rawBlock.status).trim() || 'success'

    if (blockType === 'thinking') {
      const block = ensureTextBlock(msg, blockId, 'thinking')
      block.status = blockStatus
      block.text = textOrEmpty(rawBlock.text)
      msg.thinkingText = appendStr(msg.thinkingText, block.text)
    } else if (blockType === 'main_text') {
      const block = ensureTextBlock(msg, blockId, 'main_text')
      block.status = blockStatus
      block.text = textOrEmpty(rawBlock.text)
      msg.mainText = appendStr(msg.mainText, block.text)
    } else if (blockType === 'error') {
      const block = ensureRenderBlock(msg, blockId, 'error', { status: 'failed', text: textOrEmpty(rawBlock.text) })
      block.status = 'failed'
      block.text = textOrEmpty(rawBlock.text)
      msg.error = msg.error || { message: block.text }
    }

    const envelope = extractToolEnvelope(rawBlock)
    if (envelope) {
      ensureToolRenderBlock(msg, {
        toolId: envelope.toolId,
        blockKey: `${blockId}::tool`,
        name: envelope.name,
        input: envelope.input,
        output: envelope.output,
        status: envelope.status
      })
    }

    const payloadCitations = isPlainObject(rawBlock.payload) ? rawBlock.payload.citations : null
    if (Array.isArray(payloadCitations)) {
      msg.citations.push(...payloadCitations)
    }
  }

  if (!hasRenderableMainText(msg) && msg.content) {
    const block = ensureTextBlock(msg, 'main-text', 'main_text')
    block.status = msg.status === 'failed' ? 'failed' : 'success'
    block.text = msg.content
  }

  return msg
}

export const processAssistantStreamEvent = (msg, event) => {
  if (!isPlainObject(msg) || !isPlainObject(event)) return

  const type = textOrEmpty(event.type).trim()
  const payload = isPlainObject(event.payload) ? event.payload : {}

  if (event.message_id) msg.message_id = textOrEmpty(event.message_id)
  if (payload.provider_id) msg.provider_id = textOrEmpty(payload.provider_id)
  if (payload.model) msg.model = textOrEmpty(payload.model)

  const ensureActiveMessageKey = () => {
    if (!textOrEmpty(msg._activeMessageKey)) {
      msg._activeMessageKey = `m${Number(msg._streamMessageSeq || 0)}`
    }
    return msg._activeMessageKey
  }

  const beginNewStreamMessage = () => {
    msg._streamMessageSeq = Number(msg._streamMessageSeq || 0) + 1
    msg._activeMessageKey = `m${msg._streamMessageSeq}`
  }

  const bindRawBlockId = (rawId, renderId) => {
    const raw = textOrEmpty(rawId).trim()
    if (!raw || !renderId) return
    msg._rawBlockIds[`${ensureActiveMessageKey()}:${raw}`] = renderId
  }

  const resolveRenderBlockId = (rawId) => {
    const raw = textOrEmpty(rawId).trim()
    if (!raw) return ''
    return msg._rawBlockIds[`${ensureActiveMessageKey()}:${raw}`] || `${ensureActiveMessageKey()}:${raw}`
  }

  if (type === 'message_start') {
    const message = isPlainObject(event.message) ? event.message : (isPlainObject(payload.message) ? payload.message : {})
    beginNewStreamMessage()
    if (message.id) msg.message_id = textOrEmpty(message.id)
    if (message.model) msg.model = textOrEmpty(message.model)
    msg.status = 'streaming'
    return
  }

  if (type === 'ping' || type === 'llm_response_created' || type === 'block_complete' || type === 'raw') {
    return
  }

  if (type === 'content_block_start') {
    const index = event.index ?? payload.index
    const contentBlock = isPlainObject(event.content_block) ? event.content_block : (isPlainObject(payload.content_block) ? payload.content_block : {})
    const contentType = textOrEmpty(contentBlock.type).trim()
    const rawBlockId = `cb-${index}`
    const blockId = `${ensureActiveMessageKey()}:${rawBlockId}`
    bindRawBlockId(rawBlockId, blockId)

    if (contentType === 'text') {
      const block = ensureTextBlock(msg, blockId, 'main_text')
      block.status = 'streaming'
      if (contentBlock.text) {
        block.text = appendStr(block.text, contentBlock.text)
        msg.mainText = appendStr(msg.mainText, contentBlock.text)
        msg.content = appendStr(msg.content, contentBlock.text)
      }
      return
    }

    if (contentType === 'thinking') {
      const block = ensureTextBlock(msg, blockId, 'thinking')
      block.status = 'streaming'
      if (contentBlock.thinking) {
        block.text = appendStr(block.text, contentBlock.thinking)
        msg.thinkingText = appendStr(msg.thinkingText, contentBlock.thinking)
      }
      return
    }

    if (contentType === 'tool_use') {
      ensureToolRenderBlock(msg, {
        toolId: contentBlock.id,
        blockKey: blockId,
        name: contentBlock.name || 'Tool',
        input: Object.prototype.hasOwnProperty.call(contentBlock, 'input') ? contentBlock.input : undefined,
        status: 'streaming'
      })
      return
    }

    if (contentType === 'tool_result') {
      ensureToolRenderBlock(msg, {
        toolId: contentBlock.tool_use_id,
        blockKey: blockId,
        name: contentBlock.name || 'Tool',
        output: Object.prototype.hasOwnProperty.call(contentBlock, 'content') ? contentBlock.content : undefined,
        status: 'streaming'
      })
    }
    return
  }

  if (type === 'content_block_delta') {
    const index = event.index ?? payload.index
    const rawBlockId = `cb-${index}`
    const blockId = resolveRenderBlockId(rawBlockId) || `${ensureActiveMessageKey()}:${rawBlockId}`
    const delta = isPlainObject(event.delta) ? event.delta : (isPlainObject(payload.delta) ? payload.delta : {})
    const deltaType = textOrEmpty(delta.type).trim()

    if (deltaType === 'text_delta') {
      const block = ensureTextBlock(msg, blockId, 'main_text')
      block.status = 'streaming'
      block.text = appendStr(block.text, delta.text)
      msg.mainText = appendStr(msg.mainText, delta.text)
      msg.content = appendStr(msg.content, delta.text)
      return
    }

    if (deltaType === 'thinking_delta') {
      const block = ensureTextBlock(msg, blockId, 'thinking')
      block.status = 'streaming'
      block.text = appendStr(block.text, delta.thinking)
      msg.thinkingText = appendStr(msg.thinkingText, delta.thinking)
      return
    }

    if (deltaType === 'input_json_delta') {
      const block = ensureToolRenderBlock(msg, { blockKey: blockId, status: 'streaming' })
      block._partialJson = appendStr(block._partialJson, delta.partial_json || '')
      const parsed = parseMaybeJson(block._partialJson)
      block.tool.input = parsed !== null ? parsed : block._partialJson
      return
    }

    if (deltaType === 'citation_start_delta' && delta.citation) {
      msg.citations.push(delta.citation)
    }
    return
  }

  if (type === 'content_block_stop') {
    const index = event.index ?? payload.index
    const block = msg._renderBlockMap[resolveRenderBlockId(`cb-${index}`)]
    if (!block) return
    if (block.kind === 'tool' && block.tool && block.status !== 'failed') {
      block.status = block.tool.status === 'failed' ? 'failed' : (block.tool.status === 'success' ? 'success' : 'streaming')
      return
    }
    if (block.status !== 'failed') block.status = 'success'
    return
  }

  if (type === 'message_delta') {
    const delta = isPlainObject(event.delta) ? event.delta : (isPlainObject(payload.delta) ? payload.delta : {})
    if (delta.stop_reason != null) msg.stop_reason = textOrEmpty(delta.stop_reason)
    return
  }

  if (type === 'message_stop') {
    markMessageBlocksComplete(msg)
    return
  }

  if (type === 'text.delta') {
    const block = ensureTextBlock(msg, 'main-text', 'main_text')
    block.status = 'streaming'
    block.text = appendStr(block.text, payload.text)
    msg.mainText = appendStr(msg.mainText, payload.text)
    msg.content = appendStr(msg.content, payload.text)
    return
  }

  if (type === 'text.complete') {
    const block = ensureTextBlock(msg, 'main-text', 'main_text')
    block.status = 'success'
    if (typeof payload.text === 'string') {
      block.text = payload.text
      msg.mainText = payload.text
      msg.content = payload.text
    }
    return
  }

  if (type === 'thinking.delta') {
    const block = ensureTextBlock(msg, 'thinking-main', 'thinking')
    block.status = 'streaming'
    block.text = appendStr(block.text, payload.text)
    msg.thinkingText = appendStr(msg.thinkingText, payload.text)
    return
  }

  if (type === 'thinking.complete') {
    const block = ensureTextBlock(msg, 'thinking-main', 'thinking')
    block.status = 'success'
    if (typeof payload.text === 'string') {
      block.text = payload.text
      msg.thinkingText = payload.text
    }
    return
  }

  if (type.startsWith('tool.')) {
    ensureToolRenderBlock(msg, {
      toolId: payload.tool_id || payload.block_id,
      blockKey: resolveRenderBlockId(payload.block_id) || payload.block_id,
      name: payload.tool_name || 'Tool',
      input: Object.prototype.hasOwnProperty.call(payload, 'input') ? payload.input : undefined,
      output: Object.prototype.hasOwnProperty.call(payload, 'output') ? payload.output : undefined,
      status: toolStatusFromEvent(type)
    })
    return
  }

  if (type === 'error') {
    msg.status = 'failed'
    msg.error = { message: textOrEmpty(payload.message || '请求失败') }
    createErrorBlock(msg, msg.error.message)
    return
  }

  if (type === 'done') {
    msg.status = textOrEmpty(payload.status).trim() || msg.status || 'success'
    if (payload.model) msg.model = textOrEmpty(payload.model)
    if (payload.error) {
      const errorMessage = isPlainObject(payload.error)
        ? textOrEmpty(payload.error.message || '请求失败')
        : textOrEmpty(payload.error)
      msg.error = { message: errorMessage }
      createErrorBlock(msg, errorMessage)
    }
    if (Array.isArray(payload.blocks) && !msg.renderBlocks.length) {
      const hydrated = hydrateAssistantMessageState({
        message_id: msg.message_id || msg.id,
        content: payload.content,
        status: msg.status,
        created_at: msg.created_at,
        blocks: payload.blocks,
        error: msg.error,
        provider_id: msg.provider_id,
        model: msg.model
      })
      Object.assign(msg, hydrated)
      return
    }
    if (!hasRenderableMainText(msg) && payload.content) {
      const block = ensureTextBlock(msg, 'main-text', 'main_text')
      block.status = msg.status === 'failed' ? 'failed' : 'success'
      block.text = textOrEmpty(payload.content)
    }
    if (payload.content) {
      msg.content = textOrEmpty(payload.content)
    }
    markAllStreamingBlocksComplete(msg)
  }
}

export const activeStreamingBlock = (msg) => [...(Array.isArray(msg?.renderBlocks) ? msg.renderBlocks : [])]
  .reverse()
  .find((block) => {
    if (block?.kind === 'tool' && block.tool) {
      return ['pending', 'streaming'].includes(textOrEmpty(block.tool.status))
    }
    return ['pending', 'streaming'].includes(textOrEmpty(block?.status))
  })
