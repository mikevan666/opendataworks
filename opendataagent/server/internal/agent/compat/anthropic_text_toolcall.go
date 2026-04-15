package compat

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	sdkapi "github.com/stellarlinkco/agentsdk-go/pkg/api"
	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"
)

const (
	AnthropicCompatProviderID = "anthropic_compat"
	DefaultCompatModel        = "GLM-4.7"
)

var toolCallPattern = regexp.MustCompile(`(?s)<tool_call>\s*(.*?)\s*</tool_call>`)
var plainFunctionCallPattern = regexp.MustCompile(`^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\((.*)\)\s*$`)
var openAICallPattern = regexp.MustCompile(`(?s)^\s*call_([a-zA-Z_][a-zA-Z0-9_-]*)\s*(?:\((.*?)\)|:\s*(\{.*?\}|\[.*?\]))\s*(.*)$`)
var bracketToolCallPattern = regexp.MustCompile(`(?s)^\s*\[Tool Call:\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*\]\s*(.*)$`)

type AnthropicTextToolCallConfig struct {
	APIKey     string
	BaseURL    string
	ModelName  string
	MaxTokens  int
	HTTPClient *http.Client
}

func NewAnthropicTextToolCallFactory(cfg AnthropicTextToolCallConfig) sdkapi.ModelFactory {
	return sdkapi.ModelFactoryFunc(func(ctx context.Context) (sdkmodel.Model, error) {
		_ = ctx
		apiKey := strings.TrimSpace(cfg.APIKey)
		baseURL := strings.TrimSpace(cfg.BaseURL)
		if apiKey == "" {
			return nil, errors.New("anthropic compat provider requires API token")
		}
		if baseURL == "" {
			return nil, errors.New("anthropic compat provider requires base URL")
		}
		return &openAICompatGatewayModel{
			apiKey:       apiKey,
			baseURL:      strings.TrimRight(baseURL, "/"),
			modelName:    strings.TrimSpace(cfg.ModelName),
			maxTokens:    cfg.MaxTokens,
			httpClient:   resolveHTTPClient(cfg.HTTPClient),
			pendingFinal: make(map[string]string),
		}, nil
	})
}

func SupportsAnthropicTextToolCall(baseURL string) bool {
	raw := strings.TrimSpace(baseURL)
	if raw == "" {
		return false
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return false
	}
	switch strings.ToLower(strings.TrimSpace(parsed.Hostname())) {
	case "wzw.pp.ua":
		return true
	default:
		return false
	}
}

type anthropicTextToolCallModel struct {
	apiKey     string
	baseURL    string
	modelName  string
	maxTokens  int
	httpClient *http.Client
}

func (m *anthropicTextToolCallModel) Complete(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	resp, err := m.complete(ctx, req)
	if err != nil {
		return nil, err
	}
	return adaptResponseForTools(resp, knownToolNames(req.Tools)), nil
}

func (m *anthropicTextToolCallModel) CompleteStream(ctx context.Context, req sdkmodel.Request, cb sdkmodel.StreamHandler) error {
	if cb == nil {
		return errors.New("stream callback required")
	}
	final, err := m.Complete(ctx, req)
	if err != nil {
		return err
	}
	return cb(sdkmodel.StreamResult{Final: true, Response: final})
}

func (m *anthropicTextToolCallModel) complete(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	payload, err := m.buildPayload(req)
	if err != nil {
		return nil, err
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal anthropic compat payload: %w", err)
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, m.baseURL+"/v1/messages", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("build anthropic compat request: %w", err)
	}
	httpReq.Header.Set("x-api-key", m.apiKey)
	httpReq.Header.Set("anthropic-version", "2023-06-01")
	httpReq.Header.Set("content-type", "application/json")
	httpReq.Header.Set("accept", "application/json")

	resp, err := m.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil {
		return nil, fmt.Errorf("read anthropic compat response: %w", err)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("POST %q: %s", httpReq.URL.String(), formatHTTPError(resp.StatusCode, respBody))
	}

	var raw anthropicCompatResponse
	if err := json.Unmarshal(respBody, &raw); err != nil {
		return nil, fmt.Errorf("decode anthropic compat response: %w", err)
	}
	return raw.toSDKResponse(), nil
}

func (m *anthropicTextToolCallModel) buildPayload(req sdkmodel.Request) (anthropicCompatRequest, error) {
	maxTokens := req.MaxTokens
	if maxTokens <= 0 {
		maxTokens = m.maxTokens
	}
	if maxTokens <= 0 {
		maxTokens = 4096
	}
	payload := anthropicCompatRequest{
		Model:     firstNonEmpty(strings.TrimSpace(req.Model), m.modelName),
		MaxTokens: maxTokens,
		Messages:  make([]anthropicCompatMessage, 0, len(req.Messages)),
	}
	if payload.Model == "" {
		payload.Model = DefaultCompatModel
	}
	for _, sys := range collectSystemMessages(req) {
		payload.System = append(payload.System, anthropicCompatTextBlock{Type: "text", Text: sys})
	}
	if len(req.Tools) > 0 {
		tools, err := convertCompatTools(req.Tools)
		if err != nil {
			return anthropicCompatRequest{}, err
		}
		payload.Tools = tools
	}
	for _, msg := range req.Messages {
		converted, ok, err := convertCompatMessage(msg)
		if err != nil {
			return anthropicCompatRequest{}, err
		}
		if ok {
			payload.Messages = append(payload.Messages, converted)
		}
	}
	if len(payload.Messages) == 0 {
		payload.Messages = append(payload.Messages, anthropicCompatMessage{
			Role: "user",
			Content: []anthropicCompatContentBlock{
				{Type: "text", Text: "."},
			},
		})
	}
	return payload, nil
}

func collectSystemMessages(req sdkmodel.Request) []string {
	items := make([]string, 0, 2)
	if trimmed := strings.TrimSpace(req.System); trimmed != "" {
		items = append(items, trimmed)
	}
	for _, msg := range req.Messages {
		if !strings.EqualFold(strings.TrimSpace(msg.Role), "system") {
			continue
		}
		if trimmed := strings.TrimSpace(msg.Content); trimmed != "" {
			items = append(items, trimmed)
		}
	}
	return items
}

func convertCompatTools(defs []sdkmodel.ToolDefinition) ([]anthropicCompatTool, error) {
	out := make([]anthropicCompatTool, 0, len(defs))
	for _, def := range defs {
		name := strings.TrimSpace(def.Name)
		if name == "" {
			continue
		}
		schema := def.Parameters
		if len(schema) == 0 {
			schema = map[string]any{"type": "object"}
		}
		raw, err := json.Marshal(schema)
		if err != nil {
			return nil, fmt.Errorf("tool %s schema: %w", name, err)
		}
		var inputSchema map[string]any
		if err := json.Unmarshal(raw, &inputSchema); err != nil {
			return nil, fmt.Errorf("tool %s schema: %w", name, err)
		}
		out = append(out, anthropicCompatTool{
			Name:        name,
			Description: strings.TrimSpace(def.Description),
			InputSchema: inputSchema,
		})
	}
	return out, nil
}

func convertCompatMessage(msg sdkmodel.Message) (anthropicCompatMessage, bool, error) {
	role := strings.ToLower(strings.TrimSpace(msg.Role))
	switch role {
	case "system":
		return anthropicCompatMessage{}, false, nil
	case "assistant":
		content := make([]anthropicCompatContentBlock, 0, 1+len(msg.ToolCalls))
		if text := strings.TrimSpace(msg.Content); text != "" {
			content = append(content, anthropicCompatContentBlock{Type: "text", Text: msg.Content})
		}
		for _, call := range msg.ToolCalls {
			name := strings.TrimSpace(call.Name)
			id := strings.TrimSpace(call.ID)
			if name == "" || id == "" {
				continue
			}
			content = append(content, anthropicCompatContentBlock{
				Type:  "tool_use",
				ID:    id,
				Name:  name,
				Input: cloneMap(call.Arguments),
			})
		}
		if len(content) == 0 {
			content = append(content, anthropicCompatContentBlock{Type: "text", Text: "."})
		}
		return anthropicCompatMessage{Role: "assistant", Content: content}, true, nil
	case "tool":
		content := make([]anthropicCompatContentBlock, 0, len(msg.ToolCalls))
		for _, call := range msg.ToolCalls {
			id := strings.TrimSpace(call.ID)
			if id == "" {
				continue
			}
			text := call.Result
			if strings.TrimSpace(text) == "" {
				text = msg.Content
			}
			content = append(content, anthropicCompatContentBlock{
				Type:      "tool_result",
				ToolUseID: id,
				Content:   text,
				IsError:   toolResultIsError(text),
			})
		}
		if len(content) == 0 {
			content = append(content, anthropicCompatContentBlock{Type: "text", Text: defaultCompatText(msg.Content)})
		}
		return anthropicCompatMessage{Role: "user", Content: content}, true, nil
	default:
		content := make([]anthropicCompatContentBlock, 0, max(1, len(msg.ContentBlocks)))
		if len(msg.ContentBlocks) > 0 {
			for _, block := range msg.ContentBlocks {
				switch block.Type {
				case sdkmodel.ContentBlockText:
					content = append(content, anthropicCompatContentBlock{Type: "text", Text: defaultCompatText(block.Text)})
				default:
					continue
				}
			}
		}
		if len(content) == 0 {
			content = append(content, anthropicCompatContentBlock{Type: "text", Text: defaultCompatText(msg.Content)})
		}
		return anthropicCompatMessage{Role: "user", Content: content}, true, nil
	}
}

func defaultCompatText(text string) string {
	if strings.TrimSpace(text) == "" {
		return "."
	}
	return text
}

func toolResultIsError(text string) bool {
	trimmed := strings.TrimSpace(text)
	if !strings.HasPrefix(trimmed, "{") || !strings.HasSuffix(trimmed, "}") {
		return false
	}

	var payload map[string]any
	if err := json.Unmarshal([]byte(trimmed), &payload); err != nil {
		return false
	}

	val, ok := payload["error"]
	if !ok {
		return false
	}

	switch typed := val.(type) {
	case bool:
		return typed
	case string:
		return strings.TrimSpace(typed) != ""
	default:
		return typed != nil
	}
}

func resolveHTTPClient(client *http.Client) *http.Client {
	if client != nil {
		return client
	}
	return &http.Client{Timeout: 120 * time.Second}
}

func formatHTTPError(status int, body []byte) string {
	text := strings.TrimSpace(string(body))
	if text == "" {
		return http.StatusText(status)
	}
	if len(text) > 600 {
		text = text[:600]
	}
	return fmt.Sprintf("%d %s", status, text)
}

type anthropicCompatRequest struct {
	Model     string                     `json:"model"`
	MaxTokens int                        `json:"max_tokens"`
	System    []anthropicCompatTextBlock `json:"system,omitempty"`
	Messages  []anthropicCompatMessage   `json:"messages"`
	Tools     []anthropicCompatTool      `json:"tools,omitempty"`
}

type anthropicCompatTextBlock struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type anthropicCompatMessage struct {
	Role    string                        `json:"role"`
	Content []anthropicCompatContentBlock `json:"content"`
}

type anthropicCompatContentBlock struct {
	Type      string         `json:"type"`
	Text      string         `json:"text,omitempty"`
	ID        string         `json:"id,omitempty"`
	Name      string         `json:"name,omitempty"`
	Input     map[string]any `json:"input,omitempty"`
	ToolUseID string         `json:"tool_use_id,omitempty"`
	Content   string         `json:"content,omitempty"`
	IsError   bool           `json:"is_error,omitempty"`
}

type anthropicCompatTool struct {
	Name        string         `json:"name"`
	Description string         `json:"description,omitempty"`
	InputSchema map[string]any `json:"input_schema"`
}

type anthropicCompatResponse struct {
	Role       string                         `json:"role"`
	Content    []anthropicCompatResponseBlock `json:"content"`
	StopReason string                         `json:"stop_reason"`
	Usage      anthropicCompatUsage           `json:"usage"`
}

type anthropicCompatResponseBlock struct {
	Type     string         `json:"type"`
	Text     string         `json:"text,omitempty"`
	Thinking string         `json:"thinking,omitempty"`
	ID       string         `json:"id,omitempty"`
	Name     string         `json:"name,omitempty"`
	Input    map[string]any `json:"input,omitempty"`
}

type anthropicCompatUsage struct {
	InputTokens         int `json:"input_tokens"`
	OutputTokens        int `json:"output_tokens"`
	CacheCreationTokens int `json:"cache_creation_input_tokens"`
	CacheReadTokens     int `json:"cache_read_input_tokens"`
}

func (r anthropicCompatResponse) toSDKResponse() *sdkmodel.Response {
	message := sdkmodel.Message{Role: firstNonEmpty(strings.TrimSpace(r.Role), "assistant")}
	parts := make([]string, 0, len(r.Content))
	thinkingParts := make([]string, 0, len(r.Content))
	for _, block := range r.Content {
		switch strings.TrimSpace(block.Type) {
		case "text":
			if strings.TrimSpace(block.Text) != "" {
				parts = append(parts, block.Text)
			}
		case "thinking":
			if strings.TrimSpace(block.Thinking) != "" {
				thinkingParts = append(thinkingParts, block.Thinking)
			}
			if strings.TrimSpace(block.Text) != "" {
				thinkingParts = append(thinkingParts, block.Text)
			}
		case "tool_use":
			message.ToolCalls = append(message.ToolCalls, sdkmodel.ToolCall{
				ID:        strings.TrimSpace(block.ID),
				Name:      strings.TrimSpace(block.Name),
				Arguments: cloneMap(block.Input),
			})
		}
	}
	message.Content = strings.TrimSpace(strings.Join(parts, "\n"))
	message.ReasoningContent = strings.TrimSpace(strings.Join(thinkingParts, "\n"))
	usage := sdkmodel.Usage{
		InputTokens:         r.Usage.InputTokens,
		OutputTokens:        r.Usage.OutputTokens,
		TotalTokens:         r.Usage.InputTokens + r.Usage.OutputTokens,
		CacheCreationTokens: r.Usage.CacheCreationTokens,
		CacheReadTokens:     r.Usage.CacheReadTokens,
	}
	return &sdkmodel.Response{
		Message:    message,
		Usage:      usage,
		StopReason: strings.TrimSpace(r.StopReason),
	}
}

func adaptResponse(resp *sdkmodel.Response) *sdkmodel.Response {
	return adaptResponseForTools(resp, nil)
}

func adaptResponseForTools(resp *sdkmodel.Response, toolNames map[string]struct{}) *sdkmodel.Response {
	adapted, _ := adaptResponseForToolsDetailed(resp, toolNames)
	return adapted
}

func adaptResponseForToolsDetailed(resp *sdkmodel.Response, toolNames map[string]struct{}) (*sdkmodel.Response, string) {
	if resp == nil {
		return nil, ""
	}
	clone := *resp
	clone.Message = cloneMessage(resp.Message)
	if len(clone.Message.ToolCalls) > 0 {
		return &clone, ""
	}
	toolCalls, strippedText := extractTaggedToolCalls(clone.Message.Content, toolNames)
	if len(toolCalls) == 0 {
		return &clone, ""
	}
	clone.Message.Content = strippedText
	clone.Message.ToolCalls = toolCalls
	clone.StopReason = "tool_use"
	return &clone, strippedText
}

func cloneMessage(msg sdkmodel.Message) sdkmodel.Message {
	out := msg
	if len(msg.ToolCalls) > 0 {
		out.ToolCalls = make([]sdkmodel.ToolCall, len(msg.ToolCalls))
		for idx, call := range msg.ToolCalls {
			out.ToolCalls[idx] = sdkmodel.ToolCall{
				ID:        call.ID,
				Name:      call.Name,
				Result:    call.Result,
				Arguments: cloneMap(call.Arguments),
			}
		}
	}
	if len(msg.ContentBlocks) > 0 {
		out.ContentBlocks = append([]sdkmodel.ContentBlock(nil), msg.ContentBlocks...)
	}
	return out
}

func cloneMap(src map[string]any) map[string]any {
	if len(src) == 0 {
		return nil
	}
	out := make(map[string]any, len(src))
	for key, value := range src {
		out[key] = cloneValue(value)
	}
	return out
}

func cloneValue(value any) any {
	switch typed := value.(type) {
	case map[string]any:
		return cloneMap(typed)
	case []any:
		out := make([]any, len(typed))
		for idx, item := range typed {
			out[idx] = cloneValue(item)
		}
		return out
	default:
		return typed
	}
}

func extractTaggedToolCalls(text string, toolNames map[string]struct{}) ([]sdkmodel.ToolCall, string) {
	text = strings.TrimSpace(text)
	matches := toolCallPattern.FindAllStringSubmatchIndex(text, -1)
	if len(matches) == 0 {
		if call, trailing, ok := parseBracketToolCall(text, toolNames); ok {
			return []sdkmodel.ToolCall{call}, trailing
		}
		if call, trailing, ok := parseOpenAICallToolCall(text, toolNames); ok {
			return []sdkmodel.ToolCall{call}, trailing
		}
		if call, trailing, ok := parseLeadingPlainFunctionToolCall(text); ok {
			return []sdkmodel.ToolCall{call}, trailing
		}
		if call, trailing, ok := parseLeadingBareToolName(text, toolNames); ok {
			return []sdkmodel.ToolCall{call}, trailing
		}
		if call, ok := parsePlainFunctionToolCall(text); ok {
			return []sdkmodel.ToolCall{call}, ""
		}
		if call, ok := parseBareToolName(text, toolNames); ok {
			return []sdkmodel.ToolCall{call}, ""
		}
		return nil, text
	}
	toolCalls := make([]sdkmodel.ToolCall, 0, len(matches))
	var stripped strings.Builder
	cursor := 0
	for idx, match := range matches {
		if match[0] > cursor {
			stripped.WriteString(text[cursor:match[0]])
		}
		payload := strings.TrimSpace(text[match[2]:match[3]])
		call, ok := parseTaggedToolCall(payload, idx)
		if ok {
			toolCalls = append(toolCalls, call)
		} else {
			stripped.WriteString(text[match[0]:match[1]])
		}
		cursor = match[1]
	}
	if cursor < len(text) {
		stripped.WriteString(text[cursor:])
	}
	return toolCalls, strings.TrimSpace(stripped.String())
}

func parseBracketToolCall(text string, toolNames map[string]struct{}) (sdkmodel.ToolCall, string, bool) {
	matches := bracketToolCallPattern.FindStringSubmatch(strings.TrimSpace(text))
	if len(matches) != 3 {
		return sdkmodel.ToolCall{}, "", false
	}
	name := strings.TrimSpace(matches[1])
	if name == "" {
		return sdkmodel.ToolCall{}, "", false
	}
	if len(toolNames) > 0 {
		if _, ok := toolNames[name]; !ok {
			return sdkmodel.ToolCall{}, "", false
		}
	}
	return sdkmodel.ToolCall{
		ID:        "compat_tool_1",
		Name:      name,
		Arguments: map[string]any{},
	}, strings.TrimSpace(matches[2]), true
}

func splitLeadingLine(text string) (string, string, bool) {
	trimmed := strings.TrimSpace(text)
	if trimmed == "" {
		return "", "", false
	}
	parts := strings.SplitN(trimmed, "\n", 2)
	firstLine := strings.TrimSpace(parts[0])
	if firstLine == "" {
		return "", "", false
	}
	trailing := ""
	if len(parts) == 2 {
		trailing = strings.TrimSpace(parts[1])
	}
	return firstLine, trailing, true
}

func parseLeadingPlainFunctionToolCall(text string) (sdkmodel.ToolCall, string, bool) {
	firstLine, trailing, ok := splitLeadingLine(text)
	if !ok || trailing == "" {
		return sdkmodel.ToolCall{}, "", false
	}
	call, matched := parsePlainFunctionToolCall(firstLine)
	if !matched {
		return sdkmodel.ToolCall{}, "", false
	}
	return call, trailing, true
}

func parseLeadingBareToolName(text string, toolNames map[string]struct{}) (sdkmodel.ToolCall, string, bool) {
	firstLine, trailing, ok := splitLeadingLine(text)
	if !ok || trailing == "" {
		return sdkmodel.ToolCall{}, "", false
	}
	call, matched := parseBareToolName(firstLine, toolNames)
	if !matched {
		return sdkmodel.ToolCall{}, "", false
	}
	return call, trailing, true
}

func parseOpenAICallToolCall(text string, toolNames map[string]struct{}) (sdkmodel.ToolCall, string, bool) {
	matches := openAICallPattern.FindStringSubmatch(strings.TrimSpace(text))
	if len(matches) != 5 {
		return sdkmodel.ToolCall{}, "", false
	}
	name := strings.TrimSpace(matches[1])
	if name == "" {
		return sdkmodel.ToolCall{}, "", false
	}
	if len(toolNames) > 0 {
		if _, ok := toolNames[name]; !ok {
			return sdkmodel.ToolCall{}, "", false
		}
	}
	argsText := strings.TrimSpace(firstNonEmpty(matches[2], matches[3]))
	args := map[string]any{}
	switch argsText {
	case "", "[]", "{}":
	default:
		if parsed := normalizeArguments(argsText); len(parsed) > 0 {
			args = parsed
		} else {
			args["raw"] = argsText
		}
	}
	return sdkmodel.ToolCall{
		ID:        "compat_tool_1",
		Name:      name,
		Arguments: args,
	}, strings.TrimSpace(matches[4]), true
}

func parseBareToolName(text string, toolNames map[string]struct{}) (sdkmodel.ToolCall, bool) {
	name := strings.TrimSpace(text)
	if name == "" || strings.ContainsAny(name, " \t\r\n") {
		return sdkmodel.ToolCall{}, false
	}
	if _, ok := toolNames[name]; !ok {
		return sdkmodel.ToolCall{}, false
	}
	return sdkmodel.ToolCall{
		ID:        "compat_tool_1",
		Name:      name,
		Arguments: map[string]any{},
	}, true
}

func knownToolNames(defs []sdkmodel.ToolDefinition) map[string]struct{} {
	if len(defs) == 0 {
		return nil
	}
	out := make(map[string]struct{}, len(defs))
	for _, def := range defs {
		name := strings.TrimSpace(def.Name)
		if name == "" {
			continue
		}
		out[name] = struct{}{}
	}
	return out
}

func parseTaggedToolCall(payload string, idx int) (sdkmodel.ToolCall, bool) {
	var raw struct {
		ID        string `json:"id"`
		Name      string `json:"name"`
		Arguments any    `json:"arguments"`
		Input     any    `json:"input"`
	}
	if err := json.Unmarshal([]byte(payload), &raw); err != nil {
		return sdkmodel.ToolCall{}, false
	}
	name := strings.TrimSpace(raw.Name)
	if name == "" {
		return sdkmodel.ToolCall{}, false
	}
	args := normalizeArguments(raw.Arguments)
	if len(args) == 0 {
		args = normalizeArguments(raw.Input)
	}
	id := strings.TrimSpace(raw.ID)
	if id == "" {
		id = fmt.Sprintf("compat_tool_%d", idx+1)
	}
	return sdkmodel.ToolCall{
		ID:        id,
		Name:      name,
		Arguments: args,
	}, true
}

func parsePlainFunctionToolCall(text string) (sdkmodel.ToolCall, bool) {
	matches := plainFunctionCallPattern.FindStringSubmatch(strings.TrimSpace(text))
	if len(matches) != 3 {
		return sdkmodel.ToolCall{}, false
	}
	name := strings.TrimSpace(matches[1])
	if name == "" {
		return sdkmodel.ToolCall{}, false
	}
	argsText := strings.TrimSpace(matches[2])
	args := map[string]any{}
	switch {
	case argsText == "":
	case argsText == "{}":
	default:
		if parsed := normalizeArguments(argsText); len(parsed) > 0 {
			args = parsed
		} else {
			args["raw"] = argsText
		}
	}
	return sdkmodel.ToolCall{
		ID:        "compat_tool_1",
		Name:      name,
		Arguments: args,
	}, true
}

func normalizeArguments(value any) map[string]any {
	switch typed := value.(type) {
	case nil:
		return nil
	case map[string]any:
		return cloneMap(typed)
	case string:
		trimmed := strings.TrimSpace(typed)
		if trimmed == "" {
			return nil
		}
		var parsed map[string]any
		if err := json.Unmarshal([]byte(trimmed), &parsed); err == nil {
			return parsed
		}
		return map[string]any{"raw": trimmed}
	default:
		raw, err := json.Marshal(typed)
		if err != nil {
			return map[string]any{"raw": fmt.Sprintf("%v", typed)}
		}
		var parsed map[string]any
		if err := json.Unmarshal(raw, &parsed); err == nil {
			return parsed
		}
		return map[string]any{"raw": string(raw)}
	}
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if trimmed := strings.TrimSpace(value); trimmed != "" {
			return trimmed
		}
	}
	return ""
}
