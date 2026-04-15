package compat

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"
)

func TestExtractTaggedToolCallsParsesArgumentsString(t *testing.T) {
	toolCalls, stripped := extractTaggedToolCalls(`<tool_call>{"name":"echo","arguments":"{\"text\":\"smoke-ok\"}"}</tool_call>`, nil)
	if stripped != "" {
		t.Fatalf("expected stripped text to be empty, got %q", stripped)
	}
	if len(toolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(toolCalls))
	}
	if toolCalls[0].Name != "echo" {
		t.Fatalf("expected tool name echo, got %q", toolCalls[0].Name)
	}
	if toolCalls[0].Arguments["text"] != "smoke-ok" {
		t.Fatalf("expected parsed argument, got %#v", toolCalls[0].Arguments)
	}
}

func TestAdaptResponseConvertsTaggedToolCallToStructuredToolCall(t *testing.T) {
	adapted := adaptResponse(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: `<tool_call>{"name":"runtime_context","arguments":"{}"}</tool_call>`,
		},
		StopReason: "end_turn",
	})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if adapted.Message.Content != "" {
		t.Fatalf("expected content stripped, got %q", adapted.Message.Content)
	}
}

func TestAdaptResponseConvertsPlainFunctionCallToStructuredToolCall(t *testing.T) {
	adapted := adaptResponse(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: `runtime_context()`,
		},
		StopReason: "end_turn",
	})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if adapted.Message.Content != "" {
		t.Fatalf("expected content stripped, got %q", adapted.Message.Content)
	}
}

func TestAdaptResponseForToolsConvertsBareToolNameToStructuredToolCall(t *testing.T) {
	adapted := adaptResponseForTools(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: `runtime_context`,
		},
		StopReason: "end_turn",
	}, map[string]struct{}{"runtime_context": {}})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if adapted.Message.Content != "" {
		t.Fatalf("expected content stripped, got %q", adapted.Message.Content)
	}
}

func TestAdaptResponseForToolsConvertsLeadingBareToolNameWithTrailingText(t *testing.T) {
	adapted, pending := adaptResponseForToolsDetailed(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: "runtime_context\nsmoke-ok",
		},
		StopReason: "end_turn",
	}, map[string]struct{}{"runtime_context": {}})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if adapted.Message.Content != "smoke-ok" {
		t.Fatalf("expected pending text preserved in message content, got %q", adapted.Message.Content)
	}
	if pending != "smoke-ok" {
		t.Fatalf("expected pending text smoke-ok, got %q", pending)
	}
}

func TestAdaptResponseForToolsConvertsLeadingFunctionCallWithTrailingText(t *testing.T) {
	adapted, pending := adaptResponseForToolsDetailed(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: "runtime_context()\nsmoke-ok",
		},
		StopReason: "end_turn",
	}, map[string]struct{}{"runtime_context": {}})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if adapted.Message.Content != "smoke-ok" {
		t.Fatalf("expected pending text preserved in message content, got %q", adapted.Message.Content)
	}
	if pending != "smoke-ok" {
		t.Fatalf("expected pending text smoke-ok, got %q", pending)
	}
}

func TestAdaptResponseForToolsConvertsBracketToolCallToStructuredToolCall(t *testing.T) {
	adapted, pending := adaptResponseForToolsDetailed(&sdkmodel.Response{
		Message: sdkmodel.Message{
			Role:    "assistant",
			Content: "[Tool Call: runtime_context]\nsmoke-ok",
		},
		StopReason: "end_turn",
	}, map[string]struct{}{"runtime_context": {}})
	if adapted.StopReason != "tool_use" {
		t.Fatalf("expected stop reason tool_use, got %q", adapted.StopReason)
	}
	if len(adapted.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(adapted.Message.ToolCalls))
	}
	if adapted.Message.ToolCalls[0].Name != "runtime_context" {
		t.Fatalf("unexpected tool name %q", adapted.Message.ToolCalls[0].Name)
	}
	if pending != "smoke-ok" {
		t.Fatalf("expected pending text smoke-ok, got %q", pending)
	}
}

func TestOpenAICompatResponsePreservesReasoningContent(t *testing.T) {
	resp := openAICompatResponse{
		Choices: []openAICompatChoice{{
			FinishReason: "stop",
			Message: openAICompatChoiceMessage{
				Role:             "assistant",
				Content:          "smoke-ok",
				ReasoningContent: "先查看上下文，再决定是否调用工具",
			},
		}},
	}
	adapted := resp.toSDKResponse()
	if adapted.Message.ReasoningContent != "先查看上下文，再决定是否调用工具" {
		t.Fatalf("unexpected reasoning content %q", adapted.Message.ReasoningContent)
	}
}

func TestCompatModelCompleteStreamUsesHTTPAnthropicPayloadAndAdaptsToolCall(t *testing.T) {
	var captured anthropicCompatRequest
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/messages" {
			http.NotFound(w, r)
			return
		}
		if got := r.Header.Get("x-api-key"); got != "token" {
			t.Fatalf("unexpected api key header %q", got)
		}
		body, err := io.ReadAll(r.Body)
		if err != nil {
			t.Fatalf("read body: %v", err)
		}
		if err := json.Unmarshal(body, &captured); err != nil {
			t.Fatalf("decode request: %v", err)
		}
		w.Header().Set("content-type", "application/json")
		_, _ = w.Write([]byte(`{
			"role":"assistant",
			"content":[{"type":"text","text":"<tool_call>{\"name\":\"echo\",\"arguments\":\"{\\\"text\\\":\\\"smoke-ok\\\"}\"}</tool_call>"}],
			"stop_reason":"end_turn",
			"usage":{"input_tokens":11,"output_tokens":7}
		}`))
	}))
	defer server.Close()

	model := &anthropicTextToolCallModel{
		apiKey:     "token",
		baseURL:    server.URL,
		modelName:  DefaultCompatModel,
		maxTokens:  256,
		httpClient: server.Client(),
	}
	var final *sdkmodel.Response
	req := sdkmodel.Request{
		System: "system prompt",
		Messages: []sdkmodel.Message{
			{Role: "user", Content: "hello"},
		},
		Tools: []sdkmodel.ToolDefinition{
			{
				Name:        "echo",
				Description: "Echo text",
				Parameters: map[string]any{
					"type": "object",
					"properties": map[string]any{
						"text": map[string]any{"type": "string"},
					},
				},
			},
		},
	}
	if err := model.CompleteStream(context.Background(), req, func(result sdkmodel.StreamResult) error {
		if result.Final {
			final = result.Response
		}
		return nil
	}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if captured.Model != DefaultCompatModel {
		t.Fatalf("expected model %q, got %q", DefaultCompatModel, captured.Model)
	}
	if len(captured.System) != 1 || captured.System[0].Text != "system prompt" {
		t.Fatalf("unexpected system blocks %#v", captured.System)
	}
	if len(captured.Messages) != 1 || captured.Messages[0].Role != "user" {
		t.Fatalf("unexpected messages %#v", captured.Messages)
	}
	if len(captured.Tools) != 1 || captured.Tools[0].Name != "echo" {
		t.Fatalf("unexpected tools %#v", captured.Tools)
	}
	if final == nil {
		t.Fatal("expected final response")
	}
	if len(final.Message.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(final.Message.ToolCalls))
	}
	if final.Message.ToolCalls[0].Arguments["text"] != "smoke-ok" {
		t.Fatalf("expected parsed text argument, got %#v", final.Message.ToolCalls[0].Arguments)
	}
	if final.Usage.TotalTokens != 18 {
		t.Fatalf("unexpected usage %#v", final.Usage)
	}
}
