package agent

import (
	"context"
	"testing"

	sdkapi "github.com/stellarlinkco/agentsdk-go/pkg/api"
	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"
)

type stubReasoningModel struct {
	lastRequest sdkmodel.Request
	response    *sdkmodel.Response
}

func (m *stubReasoningModel) Complete(_ context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	m.lastRequest = req
	return m.response, nil
}

func (m *stubReasoningModel) CompleteStream(ctx context.Context, req sdkmodel.Request, cb sdkmodel.StreamHandler) error {
	resp, err := m.Complete(ctx, req)
	if err != nil {
		return err
	}
	return cb(sdkmodel.StreamResult{Final: true, Response: resp})
}

func TestStripReasoningEnvelopeRemovesMarkersFromAssistantHistory(t *testing.T) {
	content := EncodeReasoningEnvelope("先确认上下文", "smoke-ok")
	cleaned, reasoning := StripReasoningEnvelope(content)
	if cleaned != "smoke-ok" {
		t.Fatalf("unexpected cleaned content %q", cleaned)
	}
	if reasoning != "先确认上下文" {
		t.Fatalf("unexpected reasoning %q", reasoning)
	}
}

func TestWrapModelFactoryWithReasoningEnvelopeDecoratesFinalResponseAndSanitizesRequest(t *testing.T) {
	inner := &stubReasoningModel{
		response: &sdkmodel.Response{
			Message: sdkmodel.Message{
				Role:             "assistant",
				Content:          "smoke-ok",
				ReasoningContent: "先确认上下文",
			},
			StopReason: "end_turn",
		},
	}
	factory := WrapModelFactoryWithReasoningEnvelope(sdkapi.ModelFactoryFunc(func(context.Context) (sdkmodel.Model, error) {
		return inner, nil
	}))

	model, err := factory.Model(context.Background())
	if err != nil {
		t.Fatalf("unexpected factory error: %v", err)
	}

	resp, err := model.Complete(context.Background(), sdkmodel.Request{
		Messages: []sdkmodel.Message{{
			Role:    "assistant",
			Content: EncodeReasoningEnvelope("旧推理", "旧答案"),
		}},
	})
	if err != nil {
		t.Fatalf("unexpected complete error: %v", err)
	}

	if got := inner.lastRequest.Messages[0].Content; got != "旧答案" {
		t.Fatalf("expected sanitized assistant content, got %q", got)
	}
	if got := inner.lastRequest.Messages[0].ReasoningContent; got != "旧推理" {
		t.Fatalf("expected sanitized reasoning content, got %q", got)
	}
	if got := resp.Message.Content; got != EncodeReasoningEnvelope("先确认上下文", "smoke-ok") {
		t.Fatalf("unexpected decorated content %q", got)
	}
}
