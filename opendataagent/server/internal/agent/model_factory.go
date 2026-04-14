package agent

import (
	"fmt"
	"strings"

	sdkapi "github.com/stellarlinkco/agentsdk-go/pkg/api"
	sdkmodel "github.com/stellarlinkco/agentsdk-go/pkg/model"

	"opendataagent/server/internal/agent/compat"
	"opendataagent/server/internal/models"
)

const (
	defaultProviderID = "anthropic"
	defaultModelID    = "claude-sonnet-4-5-20250929"
)

type Selection struct {
	ProviderID string
	Model      string
}

var builtInProviders = []models.ProviderConfig{
	{
		ProviderID:   "mock",
		ProviderType: "mock",
		DisplayName:  "Mock Runtime",
		DefaultModel: "mock-agent-1",
		Models:       defaultModelConfigs("mock-agent-1", "mock-agent-verbose"),
		Enabled:      true,
	},
	{
		ProviderID:   "anthropic",
		ProviderType: "anthropic",
		DisplayName:  "Anthropic",
		DefaultModel: defaultModelID,
		Models:       defaultModelConfigs(defaultModelID, "claude-opus-4-1"),
		Enabled:      true,
	},
	{
		ProviderID:   "openai",
		ProviderType: "openai",
		DisplayName:  "OpenAI Compatible",
		DefaultModel: "gpt-5.4-mini",
		Models:       defaultModelConfigs("gpt-5.4-mini", "gpt-5.4", "gpt-4.1"),
		Enabled:      true,
	},
	{
		ProviderID:   compat.AnthropicCompatProviderID,
		ProviderType: compat.AnthropicCompatProviderID,
		DisplayName:  "Anthropic Compat Gateway",
		DefaultModel: compat.DefaultCompatModel,
		Models:       defaultModelConfigs(compat.DefaultCompatModel, "z-ai/glm4.7"),
		Enabled:      false,
	},
}

func DefaultProviderID() string {
	return defaultProviderID
}

func DefaultModel() string {
	return defaultModelID
}

func DefaultProviderCatalog() []models.ProviderConfig {
	items := make([]models.ProviderConfig, 0, len(builtInProviders))
	for _, provider := range builtInProviders {
		copyItem := provider
		copyItem.Models = append([]models.ModelConfig(nil), provider.Models...)
		items = append(items, copyItem)
	}
	return items
}

func defaultModelConfigs(names ...string) []models.ModelConfig {
	items := make([]models.ModelConfig, 0, len(names))
	for _, name := range names {
		trimmed := strings.TrimSpace(name)
		if trimmed == "" {
			continue
		}
		items = append(items, models.ModelConfig{Name: trimmed, Enabled: true})
	}
	return items
}

func DefaultModelFactory() sdkapi.ModelFactory {
	return &sdkmodel.AnthropicProvider{
		ModelName: defaultModelID,
		MaxTokens: 4096,
	}
}

func NormalizeSettings(settings models.AgentSettings) models.AgentSettings {
	settings.Providers = normalizeProviderConfigs(settings.Providers)

	defaultSelection, err := resolveSelection(settings.Providers, settings.DefaultProviderID, settings.DefaultModel, true)
	if err != nil {
		defaultSelection = Selection{ProviderID: defaultProviderID, Model: defaultModelID}
	}
	settings.DefaultProviderID = defaultSelection.ProviderID
	settings.DefaultModel = defaultSelection.Model

	currentSelection, err := resolveSelection(settings.Providers, settings.ProviderID, settings.Model, false)
	if err != nil {
		currentSelection = defaultSelection
	}
	settings.ProviderID = currentSelection.ProviderID
	settings.Model = currentSelection.Model
	return settings
}

func ResolveSelection(settings models.AgentSettings, requestedProviderID string, requestedModel string) (Selection, error) {
	normalized := NormalizeSettings(settings)
	providerID := strings.TrimSpace(requestedProviderID)
	modelID := strings.TrimSpace(requestedModel)
	if providerID == "" {
		providerID = normalized.ProviderID
	}
	if modelID == "" && providerID == normalized.ProviderID {
		modelID = normalized.Model
	}
	if modelID == "" && providerID == normalized.DefaultProviderID {
		modelID = normalized.DefaultModel
	}
	return resolveSelection(normalized.Providers, providerID, modelID, false)
}

func CreateModelFactoryFromSettings(settings models.AgentSettings, requestedProviderID string, requestedModel string, mockFactory sdkapi.ModelFactory) (sdkapi.ModelFactory, Selection, error) {
	normalized := NormalizeSettings(settings)
	selection, err := ResolveSelection(normalized, requestedProviderID, requestedModel)
	if err != nil {
		return nil, Selection{}, err
	}
	provider := findProvider(normalized.Providers, selection.ProviderID)
	if provider == nil {
		return nil, Selection{}, fmt.Errorf("provider %q is not configured", selection.ProviderID)
	}
	switch normalizeProviderType(provider) {
	case "mock":
		if mockFactory == nil {
			return nil, Selection{}, fmt.Errorf("mock model factory is required for provider %q", selection.ProviderID)
		}
		return mockFactory, selection, nil
	case "anthropic":
		apiToken := strings.TrimSpace(provider.APIToken)
		if apiToken == "" {
			return nil, Selection{}, fmt.Errorf("provider %q requires API token in settings", selection.ProviderID)
		}
		return WrapModelFactoryWithReasoningEnvelope(&sdkmodel.AnthropicProvider{
			APIKey:    apiToken,
			BaseURL:   strings.TrimSpace(provider.BaseURL),
			ModelName: selection.Model,
			MaxTokens: 4096,
		}), selection, nil
	case "openai":
		apiToken := strings.TrimSpace(provider.APIToken)
		if apiToken == "" {
			return nil, Selection{}, fmt.Errorf("provider %q requires API token in settings", selection.ProviderID)
		}
		return WrapModelFactoryWithReasoningEnvelope(&sdkmodel.OpenAIProvider{
			APIKey:    apiToken,
			BaseURL:   strings.TrimSpace(provider.BaseURL),
			ModelName: selection.Model,
			MaxTokens: 4096,
		}), selection, nil
	case compat.AnthropicCompatProviderID:
		apiToken := strings.TrimSpace(provider.APIToken)
		if apiToken == "" {
			return nil, Selection{}, fmt.Errorf("provider %q requires API token in settings", selection.ProviderID)
		}
		baseURL := strings.TrimSpace(provider.BaseURL)
		if baseURL == "" {
			return nil, Selection{}, fmt.Errorf("provider %q requires base URL in settings", selection.ProviderID)
		}
		if !compat.SupportsAnthropicTextToolCall(baseURL) {
			return nil, Selection{}, fmt.Errorf("provider %q only supports configured compat gateways", selection.ProviderID)
		}
		return WrapModelFactoryWithReasoningEnvelope(compat.NewAnthropicTextToolCallFactory(compat.AnthropicTextToolCallConfig{
			APIKey:    apiToken,
			BaseURL:   baseURL,
			ModelName: selection.Model,
			MaxTokens: 4096,
		})), selection, nil
	default:
		return nil, Selection{}, fmt.Errorf("unsupported provider %q", selection.ProviderID)
	}
}

func CreateModelFactoryForModelRef(settings models.AgentSettings, modelRef string, mockFactory sdkapi.ModelFactory) (sdkapi.ModelFactory, Selection, error) {
	providerID, modelID := parseModelRef(modelRef)
	return CreateModelFactoryFromSettings(settings, providerID, modelID, mockFactory)
}

func normalizeProviderConfigs(existing []models.ProviderConfig) []models.ProviderConfig {
	defaults := DefaultProviderCatalog()
	if len(existing) == 0 {
		return defaults
	}

	normalizedExisting := make(map[string]models.ProviderConfig, len(existing))
	customOrder := make([]string, 0, len(existing))
	for _, provider := range existing {
		normalized, ok := normalizeProviderConfig(provider)
		if !ok {
			continue
		}
		key := normalized.ProviderID
		if _, seen := normalizedExisting[key]; !seen && !isBuiltInProviderID(key) {
			customOrder = append(customOrder, key)
		}
		normalizedExisting[key] = normalized
	}

	out := make([]models.ProviderConfig, 0, len(defaults)+len(customOrder))
	for _, provider := range defaults {
		if existingProvider, ok := normalizedExisting[provider.ProviderID]; ok {
			provider = mergeProviderDefaults(provider, existingProvider)
		}
		out = append(out, provider)
	}
	for _, key := range customOrder {
		if provider, ok := normalizedExisting[key]; ok {
			out = append(out, provider)
		}
	}
	return out
}

func normalizeProviderConfig(provider models.ProviderConfig) (models.ProviderConfig, bool) {
	provider.ProviderID = strings.TrimSpace(provider.ProviderID)
	if provider.ProviderID == "" {
		return models.ProviderConfig{}, false
	}
	provider.ProviderType = normalizeProviderType(&provider)
	if !isSupportedProviderType(provider.ProviderType) {
		return models.ProviderConfig{}, false
	}
	provider.DisplayName = strings.TrimSpace(provider.DisplayName)
	if provider.DisplayName == "" {
		provider.DisplayName = provider.ProviderID
	}
	provider.BaseURL = strings.TrimSpace(provider.BaseURL)
	provider.APIToken = strings.TrimSpace(provider.APIToken)
	provider.Models = normalizeModels(provider.Models)
	provider.DefaultModel = strings.TrimSpace(provider.DefaultModel)
	if provider.DefaultModel != "" && !containsModel(provider.Models, provider.DefaultModel) {
		provider.Models = append([]models.ModelConfig{{Name: provider.DefaultModel, Enabled: true}}, provider.Models...)
		provider.Models = normalizeModels(provider.Models)
	}
	if provider.DefaultModel == "" || !containsEnabledModel(provider.Models, provider.DefaultModel) {
		provider.DefaultModel = firstEnabledModel(provider.Models)
	}
	return provider, true
}

func mergeProviderDefaults(base models.ProviderConfig, override models.ProviderConfig) models.ProviderConfig {
	base.ProviderType = normalizeProviderType(&override)
	if strings.TrimSpace(override.DisplayName) != "" {
		base.DisplayName = strings.TrimSpace(override.DisplayName)
	}
	if len(override.Models) > 0 {
		base.Models = normalizeModels(override.Models)
	}
	if strings.TrimSpace(override.DefaultModel) != "" {
		base.DefaultModel = strings.TrimSpace(override.DefaultModel)
	}
	if base.DefaultModel != "" && !containsModel(base.Models, base.DefaultModel) {
		base.Models = append([]models.ModelConfig{{Name: base.DefaultModel, Enabled: true}}, base.Models...)
		base.Models = normalizeModels(base.Models)
	}
	if base.DefaultModel == "" || !containsEnabledModel(base.Models, base.DefaultModel) {
		base.DefaultModel = firstEnabledModel(base.Models)
	}
	base.BaseURL = strings.TrimSpace(override.BaseURL)
	base.APIToken = strings.TrimSpace(override.APIToken)
	base.Enabled = override.Enabled
	return base
}

func normalizeProviderType(provider *models.ProviderConfig) string {
	if provider == nil {
		return ""
	}
	if value := strings.TrimSpace(provider.ProviderType); value != "" {
		return value
	}
	switch strings.TrimSpace(provider.ProviderID) {
	case "mock", "anthropic", "openai", compat.AnthropicCompatProviderID:
		return strings.TrimSpace(provider.ProviderID)
	default:
		return ""
	}
}

func isSupportedProviderType(value string) bool {
	switch strings.TrimSpace(value) {
	case "mock", "anthropic", "openai", compat.AnthropicCompatProviderID:
		return true
	default:
		return false
	}
}

func isBuiltInProviderID(providerID string) bool {
	for _, provider := range builtInProviders {
		if provider.ProviderID == strings.TrimSpace(providerID) {
			return true
		}
	}
	return false
}

func normalizeModels(items []models.ModelConfig) []models.ModelConfig {
	if len(items) == 0 {
		return nil
	}
	seen := map[string]struct{}{}
	out := make([]models.ModelConfig, 0, len(items))
	for _, item := range items {
		trimmed := strings.TrimSpace(item.Name)
		if trimmed == "" {
			continue
		}
		lower := strings.ToLower(trimmed)
		if _, ok := seen[lower]; ok {
			continue
		}
		seen[lower] = struct{}{}
		out = append(out, models.ModelConfig{
			Name:    trimmed,
			Enabled: item.Enabled,
		})
	}
	return out
}

func resolveSelection(providers []models.ProviderConfig, requestedProviderID string, requestedModel string, useDefault bool) (Selection, error) {
	providers = normalizeProviderConfigs(providers)
	providerID := strings.TrimSpace(requestedProviderID)
	modelID := strings.TrimSpace(requestedModel)

	if providerID == "" {
		if useDefault {
			providerID = defaultProviderID
		} else {
			providerID = defaultProviderID
		}
	}

	provider := findProvider(providers, providerID)
	if provider == nil || !provider.Enabled {
		if strings.TrimSpace(requestedProviderID) != "" && !useDefault {
			return Selection{}, fmt.Errorf("provider %q is not enabled", requestedProviderID)
		}
		provider = firstEnabledProvider(providers)
		if provider == nil {
			return Selection{}, fmt.Errorf("no enabled provider available")
		}
		providerID = provider.ProviderID
	}

	if modelID == "" {
		modelID = strings.TrimSpace(provider.DefaultModel)
		if modelID == "" {
			modelID = firstEnabledModel(provider.Models)
		}
	}
	if !containsEnabledModel(provider.Models, modelID) {
		if strings.TrimSpace(requestedModel) != "" && !useDefault {
			return Selection{}, fmt.Errorf("model %q is not available for provider %q", requestedModel, provider.ProviderID)
		}
		modelID = strings.TrimSpace(provider.DefaultModel)
		if modelID == "" || !containsEnabledModel(provider.Models, modelID) {
			modelID = firstEnabledModel(provider.Models)
		}
	}
	if modelID == "" {
		return Selection{}, fmt.Errorf("provider %q has no usable model", provider.ProviderID)
	}

	return Selection{
		ProviderID: provider.ProviderID,
		Model:      modelID,
	}, nil
}

func parseModelRef(modelRef string) (string, string) {
	parts := strings.SplitN(strings.TrimSpace(modelRef), "/", 2)
	if len(parts) == 2 {
		return strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])
	}
	return "", strings.TrimSpace(modelRef)
}

func findProvider(providers []models.ProviderConfig, providerID string) *models.ProviderConfig {
	for idx := range providers {
		if strings.EqualFold(strings.TrimSpace(providers[idx].ProviderID), strings.TrimSpace(providerID)) {
			return &providers[idx]
		}
	}
	return nil
}

func firstEnabledProvider(providers []models.ProviderConfig) *models.ProviderConfig {
	for idx := range providers {
		if providers[idx].Enabled {
			return &providers[idx]
		}
	}
	return nil
}

func containsModel(modelsList []models.ModelConfig, model string) bool {
	target := strings.TrimSpace(model)
	if target == "" {
		return false
	}
	for _, item := range modelsList {
		if strings.EqualFold(strings.TrimSpace(item.Name), target) {
			return true
		}
	}
	return false
}

func containsEnabledModel(modelsList []models.ModelConfig, model string) bool {
	target := strings.TrimSpace(model)
	if target == "" {
		return false
	}
	for _, item := range modelsList {
		if strings.EqualFold(strings.TrimSpace(item.Name), target) && item.Enabled {
			return true
		}
	}
	return false
}

func firstEnabledModel(modelsList []models.ModelConfig) string {
	for _, item := range modelsList {
		if item.Enabled {
			return strings.TrimSpace(item.Name)
		}
	}
	return ""
}
