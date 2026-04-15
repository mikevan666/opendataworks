package compat

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"

	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"
)

type openAICompatGatewayModel struct {
	apiKey       string
	baseURL      string
	modelName    string
	maxTokens    int
	httpClient   *http.Client
	mu           sync.Mutex
	pendingFinal map[string]string
}

func (m *openAICompatGatewayModel) Complete(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	sessionKey := compatSessionKey(req.SessionID)
	if hasToolContinuation(req.Messages) {
		if pending, ok := m.popPendingFinal(sessionKey); ok {
			return &sdkmodel.Response{
				Message: sdkmodel.Message{
					Role:    "assistant",
					Content: pending,
				},
				Usage:      sdkmodel.Usage{OutputTokens: max(1, len(pending)/2), TotalTokens: max(1, len(pending)/2)},
				StopReason: "end_turn",
			}, nil
		}
		return m.completeFromToolResults(ctx, req)
	}

	resp, err := m.completeUpstream(ctx, req)
	if err != nil {
		if !hasToolContinuation(req.Messages) {
			resp, err = m.completeAnthropicFallback(ctx, req)
		}
		if err != nil {
			return nil, err
		}
	}
	adapted, pending := adaptResponseForToolsDetailed(resp, knownToolNames(req.Tools))
	if len(adapted.Message.ToolCalls) > 0 && strings.TrimSpace(pending) != "" {
		m.storePendingFinal(sessionKey, pending)
		adapted.Message.Content = ""
	}
	return adapted, nil
}

func (m *openAICompatGatewayModel) CompleteStream(ctx context.Context, req sdkmodel.Request, cb sdkmodel.StreamHandler) error {
	if cb == nil {
		return fmt.Errorf("stream callback required")
	}
	final, err := m.Complete(ctx, req)
	if err != nil {
		return err
	}
	return cb(sdkmodel.StreamResult{Final: true, Response: final})
}

func (m *openAICompatGatewayModel) completeUpstream(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	payload, err := m.buildPayload(req)
	if err != nil {
		return nil, err
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal compat payload: %w", err)
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, m.baseURL+"/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("build compat request: %w", err)
	}
	httpReq.Header.Set("authorization", "Bearer "+m.apiKey)
	httpReq.Header.Set("content-type", "application/json")
	httpReq.Header.Set("accept", "application/json")

	resp, err := m.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil {
		return nil, fmt.Errorf("read compat response: %w", err)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("POST %q: %s", httpReq.URL.String(), formatHTTPError(resp.StatusCode, respBody))
	}

	var raw openAICompatResponse
	if err := json.Unmarshal(respBody, &raw); err != nil {
		return nil, fmt.Errorf("decode compat response: %w", err)
	}
	if raw.Error != nil && strings.TrimSpace(raw.Error.Message) != "" {
		return nil, fmt.Errorf("POST %q: %s", httpReq.URL.String(), strings.TrimSpace(raw.Error.Message))
	}
	return raw.toSDKResponse(), nil
}

func (m *openAICompatGatewayModel) completeFromToolResults(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	summaryReq := sdkmodel.Request{
		System:    "Use the provided tool outputs to answer the user's request. Do not call or mention any tools.",
		SessionID: req.SessionID,
		Model:     req.Model,
		MaxTokens: req.MaxTokens,
		Messages: []sdkmodel.Message{{
			Role:    "user",
			Content: buildToolSummaryPrompt(req.Messages),
		}},
	}
	return m.completeUpstream(ctx, summaryReq)
}

func (m *openAICompatGatewayModel) completeAnthropicFallback(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	legacy := &anthropicTextToolCallModel{
		apiKey:     m.apiKey,
		baseURL:    m.baseURL,
		modelName:  m.modelName,
		maxTokens:  m.maxTokens,
		httpClient: m.httpClient,
	}
	return legacy.complete(ctx, req)
}

func (m *openAICompatGatewayModel) buildPayload(req sdkmodel.Request) (openAICompatRequest, error) {
	maxTokens := req.MaxTokens
	if maxTokens <= 0 {
		maxTokens = m.maxTokens
	}
	if maxTokens <= 0 {
		maxTokens = 4096
	}

	payload := openAICompatRequest{
		Model:     firstNonEmpty(strings.TrimSpace(req.Model), m.modelName, DefaultCompatModel),
		MaxTokens: maxTokens,
		Messages:  make([]openAICompatMessage, 0, len(req.Messages)+2),
	}
	for _, sys := range collectSystemMessages(req) {
		payload.Messages = append(payload.Messages, openAICompatMessage{
			Role:    "system",
			Content: sys,
		})
	}
	for _, msg := range req.Messages {
		converted, err := convertOpenAICompatMessages(msg)
		if err != nil {
			return openAICompatRequest{}, err
		}
		payload.Messages = append(payload.Messages, converted...)
	}
	if len(payload.Messages) == 0 {
		payload.Messages = append(payload.Messages, openAICompatMessage{Role: "user", Content: "."})
	}
	if len(req.Tools) > 0 && !hasToolResults(req.Messages) {
		tools, err := convertOpenAICompatTools(req.Tools)
		if err != nil {
			return openAICompatRequest{}, err
		}
		payload.Tools = tools
		payload.ToolChoice = "auto"
	}
	return payload, nil
}

func convertOpenAICompatMessages(msg sdkmodel.Message) ([]openAICompatMessage, error) {
	role := strings.ToLower(strings.TrimSpace(msg.Role))
	switch role {
	case "system":
		return nil, nil
	case "assistant":
		item := openAICompatMessage{Role: "assistant"}
		if strings.TrimSpace(msg.Content) != "" {
			item.Content = msg.Content
		}
		if len(msg.ToolCalls) > 0 {
			item.ToolCalls = make([]openAICompatToolCall, 0, len(msg.ToolCalls))
			for _, call := range msg.ToolCalls {
				name := strings.TrimSpace(call.Name)
				id := strings.TrimSpace(call.ID)
				if name == "" || id == "" {
					continue
				}
				args := "{}"
				if len(call.Arguments) > 0 {
					raw, err := json.Marshal(call.Arguments)
					if err != nil {
						return nil, fmt.Errorf("marshal tool call arguments: %w", err)
					}
					args = string(raw)
				}
				item.ToolCalls = append(item.ToolCalls, openAICompatToolCall{
					ID:   id,
					Type: "function",
					Function: openAICompatFunctionCall{
						Name:      name,
						Arguments: args,
					},
				})
			}
		}
		if item.Content == "" && len(item.ToolCalls) == 0 {
			item.Content = "."
		}
		return []openAICompatMessage{item}, nil
	case "tool":
		if len(msg.ToolCalls) == 0 {
			return []openAICompatMessage{{
				Role:    "tool",
				Content: defaultCompatText(msg.Content),
			}}, nil
		}
		out := make([]openAICompatMessage, 0, len(msg.ToolCalls))
		for _, call := range msg.ToolCalls {
			id := strings.TrimSpace(call.ID)
			if id == "" {
				continue
			}
			text := call.Result
			if strings.TrimSpace(text) == "" {
				text = msg.Content
			}
			out = append(out, openAICompatMessage{
				Role:       "tool",
				ToolCallID: id,
				Content:    defaultCompatText(text),
			})
		}
		return out, nil
	default:
		return []openAICompatMessage{{
			Role:    "user",
			Content: defaultCompatText(msg.TextContent()),
		}}, nil
	}
}

func convertOpenAICompatTools(defs []sdkmodel.ToolDefinition) ([]openAICompatTool, error) {
	out := make([]openAICompatTool, 0, len(defs))
	for _, def := range defs {
		name := strings.TrimSpace(def.Name)
		if name == "" {
			continue
		}
		params := def.Parameters
		if len(params) == 0 {
			params = map[string]any{"type": "object"}
		}
		raw, err := json.Marshal(params)
		if err != nil {
			return nil, fmt.Errorf("tool %s schema: %w", name, err)
		}
		var schema map[string]any
		if err := json.Unmarshal(raw, &schema); err != nil {
			return nil, fmt.Errorf("tool %s schema: %w", name, err)
		}
		out = append(out, openAICompatTool{
			Type: "function",
			Function: openAICompatToolSpec{
				Name:        name,
				Description: strings.TrimSpace(def.Description),
				Parameters:  schema,
			},
		})
	}
	return out, nil
}

func (m *openAICompatGatewayModel) storePendingFinal(key, text string) {
	if strings.TrimSpace(text) == "" {
		return
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	m.pendingFinal[key] = text
}

func (m *openAICompatGatewayModel) popPendingFinal(key string) (string, bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	text, ok := m.pendingFinal[key]
	if ok {
		delete(m.pendingFinal, key)
	}
	return text, ok
}

func compatSessionKey(sessionID string) string {
	if trimmed := strings.TrimSpace(sessionID); trimmed != "" {
		return trimmed
	}
	return "default"
}

func hasToolResults(messages []sdkmodel.Message) bool {
	for _, msg := range messages {
		if strings.EqualFold(strings.TrimSpace(msg.Role), "tool") {
			return true
		}
		for _, call := range msg.ToolCalls {
			if strings.TrimSpace(call.Result) != "" {
				return true
			}
		}
	}
	return false
}

func hasToolContinuation(messages []sdkmodel.Message) bool {
	if hasToolResults(messages) {
		return true
	}
	for _, msg := range messages {
		if len(msg.ToolCalls) > 0 {
			return true
		}
	}
	return false
}

func buildToolSummaryPrompt(messages []sdkmodel.Message) string {
	original := latestNonToolUserPrompt(messages)
	toolSections := make([]string, 0, 4)
	for _, msg := range messages {
		if len(msg.ToolCalls) == 0 {
			if strings.EqualFold(strings.TrimSpace(msg.Role), "tool") {
				toolSections = append(toolSections, defaultCompatText(msg.Content))
			}
			continue
		}
		for _, call := range msg.ToolCalls {
			if strings.TrimSpace(call.Result) == "" && !strings.EqualFold(strings.TrimSpace(msg.Role), "tool") {
				continue
			}
			name := strings.TrimSpace(call.Name)
			if name == "" {
				name = "tool"
			}
			text := strings.TrimSpace(call.Result)
			if text == "" {
				text = defaultCompatText(msg.Content)
			}
			toolSections = append(toolSections, fmt.Sprintf("[%s]\n%s", name, text))
		}
	}
	if len(toolSections) == 0 {
		toolSections = append(toolSections, "[tool]\n(no tool output)")
	}
	return fmt.Sprintf(
		"Original user request:\n%s\n\nTool results:\n%s\n\nNow answer the original user request exactly.",
		defaultCompatText(original),
		strings.Join(toolSections, "\n\n"),
	)
}

func latestNonToolUserPrompt(messages []sdkmodel.Message) string {
	for idx := len(messages) - 1; idx >= 0; idx-- {
		if !strings.EqualFold(strings.TrimSpace(messages[idx].Role), "user") {
			continue
		}
		text := strings.TrimSpace(messages[idx].TextContent())
		if text != "" {
			return text
		}
	}
	return ""
}

type openAICompatRequest struct {
	Model      string                `json:"model"`
	MaxTokens  int                   `json:"max_tokens"`
	Messages   []openAICompatMessage `json:"messages"`
	Tools      []openAICompatTool    `json:"tools,omitempty"`
	ToolChoice any                   `json:"tool_choice,omitempty"`
}

type openAICompatMessage struct {
	Role       string                 `json:"role"`
	Content    any                    `json:"content"`
	ToolCalls  []openAICompatToolCall `json:"tool_calls,omitempty"`
	ToolCallID string                 `json:"tool_call_id,omitempty"`
}

type openAICompatTool struct {
	Type     string               `json:"type"`
	Function openAICompatToolSpec `json:"function"`
}

type openAICompatToolSpec struct {
	Name        string         `json:"name"`
	Description string         `json:"description,omitempty"`
	Parameters  map[string]any `json:"parameters"`
}

type openAICompatToolCall struct {
	ID       string                   `json:"id"`
	Type     string                   `json:"type"`
	Function openAICompatFunctionCall `json:"function"`
}

type openAICompatFunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

type openAICompatResponse struct {
	Choices []openAICompatChoice `json:"choices"`
	Usage   openAICompatUsage    `json:"usage"`
	Error   *openAICompatError   `json:"error,omitempty"`
}

type openAICompatChoice struct {
	FinishReason string                    `json:"finish_reason"`
	Message      openAICompatChoiceMessage `json:"message"`
}

type openAICompatChoiceMessage struct {
	Role             string                 `json:"role"`
	Content          any                    `json:"content"`
	ReasoningContent string                 `json:"reasoning_content,omitempty"`
	ToolCalls        []openAICompatToolCall `json:"tool_calls,omitempty"`
}

type openAICompatUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
	InputTokens      int `json:"input_tokens"`
	OutputTokens     int `json:"output_tokens"`
}

type openAICompatError struct {
	Message string `json:"message"`
	Type    string `json:"type"`
}

func (r openAICompatResponse) toSDKResponse() *sdkmodel.Response {
	if len(r.Choices) == 0 {
		return &sdkmodel.Response{
			Message:    sdkmodel.Message{Role: "assistant"},
			StopReason: "end_turn",
		}
	}
	choice := r.Choices[0]
	msg := sdkmodel.Message{Role: firstNonEmpty(strings.TrimSpace(choice.Message.Role), "assistant")}
	switch typed := choice.Message.Content.(type) {
	case string:
		msg.Content = strings.TrimSpace(typed)
	case []any:
		parts := make([]string, 0, len(typed))
		for _, item := range typed {
			if text, ok := item.(string); ok && strings.TrimSpace(text) != "" {
				parts = append(parts, text)
			}
		}
		msg.Content = strings.TrimSpace(strings.Join(parts, "\n"))
	}
	msg.ReasoningContent = strings.TrimSpace(choice.Message.ReasoningContent)
	for _, call := range choice.Message.ToolCalls {
		msg.ToolCalls = append(msg.ToolCalls, sdkmodel.ToolCall{
			ID:        strings.TrimSpace(call.ID),
			Name:      strings.TrimSpace(call.Function.Name),
			Arguments: normalizeArguments(call.Function.Arguments),
		})
	}
	inputTokens := r.Usage.PromptTokens
	if inputTokens == 0 {
		inputTokens = r.Usage.InputTokens
	}
	outputTokens := r.Usage.CompletionTokens
	if outputTokens == 0 {
		outputTokens = r.Usage.OutputTokens
	}
	totalTokens := r.Usage.TotalTokens
	if totalTokens == 0 {
		totalTokens = inputTokens + outputTokens
	}
	return &sdkmodel.Response{
		Message: msg,
		Usage: sdkmodel.Usage{
			InputTokens:  inputTokens,
			OutputTokens: outputTokens,
			TotalTokens:  totalTokens,
		},
		StopReason: strings.TrimSpace(choice.FinishReason),
	}
}
