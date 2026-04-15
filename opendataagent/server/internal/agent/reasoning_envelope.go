package agent

import (
	"context"
	"strings"

	sdkapi "github.com/stellarlinkco/agentsdk-go/pkg/api"
	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"
)

const (
	ReasoningEnvelopeStart = "[[ODA_REASONING_START]]"
	ReasoningEnvelopeEnd   = "[[ODA_REASONING_END]]"
)

func WrapModelFactoryWithReasoningEnvelope(factory sdkapi.ModelFactory) sdkapi.ModelFactory {
	if factory == nil {
		return nil
	}
	return sdkapi.ModelFactoryFunc(func(ctx context.Context) (sdkmodel.Model, error) {
		model, err := factory.Model(ctx)
		if err != nil {
			return nil, err
		}
		if model == nil {
			return nil, nil
		}
		return &reasoningEnvelopeModel{inner: model}, nil
	})
}

type reasoningEnvelopeModel struct {
	inner sdkmodel.Model
}

func (m *reasoningEnvelopeModel) Complete(ctx context.Context, req sdkmodel.Request) (*sdkmodel.Response, error) {
	resp, err := m.inner.Complete(ctx, sanitizeReasoningEnvelopeRequest(req))
	if err != nil {
		return nil, err
	}
	return decorateReasoningEnvelopeResponse(resp), nil
}

func (m *reasoningEnvelopeModel) CompleteStream(ctx context.Context, req sdkmodel.Request, cb sdkmodel.StreamHandler) error {
	return m.inner.CompleteStream(ctx, sanitizeReasoningEnvelopeRequest(req), func(result sdkmodel.StreamResult) error {
		if result.Final && result.Response != nil {
			result.Response = decorateReasoningEnvelopeResponse(result.Response)
		}
		return cb(result)
	})
}

func sanitizeReasoningEnvelopeRequest(req sdkmodel.Request) sdkmodel.Request {
	if len(req.Messages) == 0 {
		return req
	}
	req.Messages = append([]sdkmodel.Message(nil), req.Messages...)
	for idx, msg := range req.Messages {
		if !strings.EqualFold(strings.TrimSpace(msg.Role), "assistant") {
			continue
		}
		cleaned, reasoning := StripReasoningEnvelope(msg.Content)
		if reasoning != "" && strings.TrimSpace(msg.ReasoningContent) == "" {
			msg.ReasoningContent = reasoning
		}
		msg.Content = cleaned
		req.Messages[idx] = msg
	}
	return req
}

func decorateReasoningEnvelopeResponse(resp *sdkmodel.Response) *sdkmodel.Response {
	if resp == nil {
		return nil
	}
	clone := *resp
	clone.Message = resp.Message
	if strings.TrimSpace(clone.Message.ReasoningContent) == "" {
		return &clone
	}
	if strings.Contains(clone.Message.Content, ReasoningEnvelopeStart) && strings.Contains(clone.Message.Content, ReasoningEnvelopeEnd) {
		return &clone
	}
	clone.Message.Content = EncodeReasoningEnvelope(clone.Message.ReasoningContent, clone.Message.Content)
	return &clone
}

func EncodeReasoningEnvelope(reasoning string, content string) string {
	reasoning = strings.TrimSpace(reasoning)
	content = strings.TrimSpace(content)
	if reasoning == "" {
		return content
	}
	if content == "" {
		return ReasoningEnvelopeStart + reasoning + ReasoningEnvelopeEnd
	}
	return ReasoningEnvelopeStart + reasoning + ReasoningEnvelopeEnd + "\n\n" + content
}

func StripReasoningEnvelope(text string) (string, string) {
	if text == "" {
		return "", ""
	}
	var contentBuilder strings.Builder
	reasoningParts := make([]string, 0, 1)
	remaining := text
	for {
		start := strings.Index(remaining, ReasoningEnvelopeStart)
		if start < 0 {
			contentBuilder.WriteString(remaining)
			break
		}
		contentBuilder.WriteString(remaining[:start])
		remaining = remaining[start+len(ReasoningEnvelopeStart):]
		end := strings.Index(remaining, ReasoningEnvelopeEnd)
		if end < 0 {
			contentBuilder.WriteString(ReasoningEnvelopeStart)
			contentBuilder.WriteString(remaining)
			break
		}
		reasoning := strings.TrimSpace(remaining[:end])
		if reasoning != "" {
			reasoningParts = append(reasoningParts, reasoning)
		}
		remaining = remaining[end+len(ReasoningEnvelopeEnd):]
	}
	return strings.TrimSpace(contentBuilder.String()), strings.TrimSpace(strings.Join(reasoningParts, "\n\n"))
}
