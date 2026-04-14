package agent

import (
	"context"
	"encoding/json"
	"testing"

	sdkapi "github.com/stellarlinkco/agentsdk-go/pkg/api"
	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"

	"opendataagent/server/internal/models"
)

func unwrapConfiguredModel(t *testing.T, factory sdkapi.ModelFactory) sdkmodel.Model {
	t.Helper()
	model, err := factory.Model(context.Background())
	if err != nil {
		t.Fatalf("unexpected create model error: %v", err)
	}
	if wrapped, ok := model.(*reasoningEnvelopeModel); ok {
		return wrapped.inner
	}
	return model
}

func TestDefaultModelFactoryReturnsAnthropicProvider(t *testing.T) {
	factory := DefaultModelFactory()
	provider, ok := factory.(*sdkmodel.AnthropicProvider)
	if !ok {
		t.Fatalf("expected AnthropicProvider, got %T", factory)
	}
	if provider.ModelName != defaultModelID {
		t.Fatalf("expected default model %q, got %q", defaultModelID, provider.ModelName)
	}
}

func TestNormalizeSettingsDefaultsToAnthropicCatalog(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{})
	if settings.DefaultProviderID != defaultProviderID {
		t.Fatalf("expected default provider %q, got %q", defaultProviderID, settings.DefaultProviderID)
	}
	if settings.DefaultModel != defaultModelID {
		t.Fatalf("expected default model %q, got %q", defaultModelID, settings.DefaultModel)
	}
	if settings.ProviderID != defaultProviderID {
		t.Fatalf("expected current provider %q, got %q", defaultProviderID, settings.ProviderID)
	}
	if settings.Model != defaultModelID {
		t.Fatalf("expected current model %q, got %q", defaultModelID, settings.Model)
	}
	if len(settings.Providers) != 4 {
		t.Fatalf("expected 4 built-in providers by default, got %d", len(settings.Providers))
	}
	if provider := findProvider(settings.Providers, "anthropic"); provider == nil || provider.ProviderType != "anthropic" {
		t.Fatalf("expected anthropic provider type to default correctly: %#v", provider)
	}
}

func TestResolveSelectionRejectsUnsupportedOpenAIModel(t *testing.T) {
	settings := models.AgentSettings{
		Providers: DefaultProviderCatalog(),
	}
	_, err := ResolveSelection(settings, "openai", "GLM-4.7")
	if err == nil {
		t.Fatal("expected unsupported model error")
	}
}

func TestCreateModelFactoryFromSettingsBuildsAnthropicProvider(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{})
	provider := findProvider(settings.Providers, "anthropic")
	if provider == nil {
		t.Fatal("expected anthropic provider in settings")
	}
	provider.APIToken = "anthropic-token"
	provider.BaseURL = "https://api.anthropic.example"
	factory, selection, err := CreateModelFactoryFromSettings(settings, "anthropic", defaultModelID, nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if selection.ProviderID != "anthropic" || selection.Model != defaultModelID {
		t.Fatalf("unexpected selection: %#v", selection)
	}
	if model := unwrapConfiguredModel(t, factory); model == nil {
		t.Fatal("expected anthropic model instance")
	}
}

func TestNormalizeSettingsKeepsCustomProviderInstance(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{
		Providers: []models.ProviderConfig{
			{
				ProviderID:   "anthropic-cn",
				ProviderType: "anthropic",
				DisplayName:  "Anthropic CN",
				DefaultModel: "claude-sonnet-4-5-20250929",
				Models: []models.ModelConfig{
					{Name: "claude-sonnet-4-5-20250929", Enabled: true},
					{Name: "claude-opus-4-1", Enabled: true},
				},
				BaseURL:  "https://anthropic.cn-proxy.example",
				APIToken: "cn-token",
				Enabled:  true,
			},
		},
		DefaultProviderID: "anthropic-cn",
		DefaultModel:      "claude-sonnet-4-5-20250929",
		ProviderID:        "anthropic-cn",
		Model:             "claude-sonnet-4-5-20250929",
	})
	provider := findProvider(settings.Providers, "anthropic-cn")
	if provider == nil {
		t.Fatal("expected custom provider to be preserved")
	}
	if provider.ProviderType != "anthropic" {
		t.Fatalf("expected provider type anthropic, got %q", provider.ProviderType)
	}
	if provider.BaseURL != "https://anthropic.cn-proxy.example" {
		t.Fatalf("expected custom base URL, got %q", provider.BaseURL)
	}
}

func TestCreateModelFactoryFromSettingsUsesMockFactoryWhenRequested(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{})
	mockFactory := sdkapi.ModelFactory(&sdkmodel.AnthropicProvider{ModelName: "mock-agent-1"})
	factory, selection, err := CreateModelFactoryFromSettings(settings, "mock", "mock-agent-1", mockFactory)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if selection.ProviderID != "mock" || selection.Model != "mock-agent-1" {
		t.Fatalf("unexpected selection: %#v", selection)
	}
	if factory != mockFactory {
		t.Fatalf("expected mock factory to be returned unchanged")
	}
}

func TestCreateModelFactoryFromSettingsBuildsOpenAIProviderFromSettings(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{})
	provider := findProvider(settings.Providers, "openai")
	if provider == nil {
		t.Fatal("expected openai provider in settings")
	}
	provider.APIToken = "openai-token"
	provider.BaseURL = "https://api.openai.example"

	factory, selection, err := CreateModelFactoryFromSettings(settings, "openai", "gpt-5.4-mini", nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if selection.ProviderID != "openai" || selection.Model != "gpt-5.4-mini" {
		t.Fatalf("unexpected selection: %#v", selection)
	}
	if model := unwrapConfiguredModel(t, factory); model == nil {
		t.Fatal("expected openai model instance")
	}
}

func TestCreateModelFactoryFromSettingsBuildsCustomAnthropicInstance(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{
		Providers: []models.ProviderConfig{
			{
				ProviderID:   "anthropic-alt",
				ProviderType: "anthropic",
				DisplayName:  "Anthropic Alt",
				DefaultModel: "claude-sonnet-4-5-20250929",
				Models: []models.ModelConfig{
					{Name: "claude-sonnet-4-5-20250929", Enabled: true},
				},
				BaseURL:  "https://anthropic.alt.example",
				APIToken: "alt-token",
				Enabled:  true,
			},
		},
		DefaultProviderID: "anthropic-alt",
		DefaultModel:      "claude-sonnet-4-5-20250929",
		ProviderID:        "anthropic-alt",
		Model:             "claude-sonnet-4-5-20250929",
	})

	factory, selection, err := CreateModelFactoryFromSettings(settings, "anthropic-alt", "claude-sonnet-4-5-20250929", nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if selection.ProviderID != "anthropic-alt" {
		t.Fatalf("unexpected selection provider: %#v", selection)
	}
	if model := unwrapConfiguredModel(t, factory); model == nil {
		t.Fatal("expected custom anthropic model instance")
	}
}

func TestCreateModelFactoryFromSettingsBuildsCompatProviderFromSettings(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{})
	provider := findProvider(settings.Providers, "anthropic_compat")
	if provider == nil {
		t.Fatal("expected anthropic_compat provider in settings")
	}
	provider.Enabled = true
	provider.APIToken = "compat-token"
	provider.BaseURL = "https://wzw.pp.ua"

	factory, selection, err := CreateModelFactoryFromSettings(settings, "anthropic_compat", "GLM-4.7", nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if selection.ProviderID != "anthropic_compat" || selection.Model != "GLM-4.7" {
		t.Fatalf("unexpected selection: %#v", selection)
	}
	model, err := factory.Model(context.Background())
	if err != nil {
		t.Fatalf("unexpected create model error: %v", err)
	}
	if _, ok := model.(sdkmodel.Model); !ok {
		t.Fatalf("expected compat model, got %T", model)
	}
}

func TestModelConfigUnmarshalAcceptsLegacyStringArray(t *testing.T) {
	var settings models.AgentSettings
	raw := []byte(`{
		"providers": [
			{
				"provider_id": "anthropic-cn",
				"provider_type": "anthropic",
				"display_name": "Anthropic CN",
				"default_model": "claude-sonnet-4-5-20250929",
				"models": ["claude-sonnet-4-5-20250929", "claude-opus-4-1"],
				"enabled": true
			}
		]
	}`)
	if err := json.Unmarshal(raw, &settings); err != nil {
		t.Fatalf("unexpected unmarshal error: %v", err)
	}
	if got := len(settings.Providers[0].Models); got != 2 {
		t.Fatalf("expected 2 models, got %d", got)
	}
	if !settings.Providers[0].Models[0].Enabled {
		t.Fatal("expected legacy string model to default to enabled")
	}
}

func TestNormalizeSettingsFallsBackToFirstEnabledModel(t *testing.T) {
	settings := NormalizeSettings(models.AgentSettings{
		Providers: []models.ProviderConfig{
			{
				ProviderID:   "anthropic-alt",
				ProviderType: "anthropic",
				DisplayName:  "Anthropic Alt",
				DefaultModel: "claude-sonnet-4-5-20250929",
				Models: []models.ModelConfig{
					{Name: "claude-sonnet-4-5-20250929", Enabled: false},
					{Name: "claude-opus-4-1", Enabled: true},
				},
				BaseURL:  "https://anthropic.alt.example",
				APIToken: "alt-token",
				Enabled:  true,
			},
		},
		DefaultProviderID: "anthropic-alt",
		DefaultModel:      "claude-sonnet-4-5-20250929",
		ProviderID:        "anthropic-alt",
		Model:             "claude-sonnet-4-5-20250929",
	})

	if settings.DefaultModel != "claude-opus-4-1" {
		t.Fatalf("expected fallback default model, got %q", settings.DefaultModel)
	}
	if settings.Model != "claude-opus-4-1" {
		t.Fatalf("expected fallback current model, got %q", settings.Model)
	}
}
