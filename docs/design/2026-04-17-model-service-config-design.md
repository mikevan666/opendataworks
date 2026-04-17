# Model Service Config Design

## Current State

The administrator settings page currently exposes DataAgent runtime details together with model provider settings. Provider validation is local: a provider is treated as verified when credentials, Base URL requirements, and at least one enabled model are present. The UI does not have a real model availability check.

## Problem

Users need a simpler model service configuration page that focuses on provider selection, API credentials, model detection, model enablement, and default model selection. Runtime internals such as Skill paths and DataAgent storage should not be exposed in this UI. Enabling a model should require a real service check so the saved configuration reflects usable provider/model pairs. The page should also avoid a separate top-level page header layer and make save scope match the visible provider.

## Scope

This change covers the DataAgent admin settings API, model detection state in existing provider settings JSON, and the Vue settings page under the `dataagent` configuration tab. It does not change the intelligent-query chat entrypoint or add new database tables.

## Solution

- Rename the settings tab label from `智能问数` to `模型服务` while keeping the existing `dataagent` tab key and route query.
- Replace the current settings page with a two-column model service console:
  - left provider list with provider name, status, and enabled model count
  - right provider header with provider name, save button, and provider enable switch
  - compact form for API Key or Token, Base URL, and streaming capability
  - model rows with detection status, a detection button, and an enable switch
  - default model selector limited to enabled models for the selected provider
- Remove the outer page card/header (`模型服务 / 刷新 / 保存配置`) so the page opens directly into the provider workbench.
- Keep a manual save button, but scope it to the currently visible provider. Unsaved changes are tracked per provider draft and surfaced through the current save button and provider-switch confirmation.
- Add `POST /api/v1/nl2sql-admin/model-detections` for real model checks using the same provider environment mapping as runtime DataAgent execution.
- Store model detection results inside `provider_settings` in `da_agent_settings.raw_json`, under each provider entry, when the current provider is saved. Detection itself returns a live result and does not directly persist draft credentials or detection state.
- A model can be enabled only after its detection status is `verified`. Provider usability still requires provider switch on, at least one enabled model, and locally valid credentials/base URL.

## Interfaces

`POST /api/v1/nl2sql-admin/model-detections`

Request fields:

- `provider_id`
- `model`
- `api_key`
- `auth_token`
- `base_url`
- `supports_partial_messages`

Response fields:

- `provider_id`
- `model`
- `status`: `verified` or `failed`
- `message`
- `checked_at`

The request may omit credentials. The backend resolves missing credentials from saved provider settings for that provider.

## Tradeoffs

The detection endpoint performs a real external model call, so it can be slower or fail because of provider/network conditions. This is intentional because the UI contract is “key plus model is usable,” not “form fields are non-empty.” The timeout is bounded at 30 seconds. Detection no longer persists provider drafts on its own; that keeps discard-and-switch behavior coherent at the cost of requiring an explicit save after a successful check.

## Rollback

Rollback can remove the detection endpoint usage from the UI and return to local validation. Persisted `model_detections` fields are additive JSON fields and can be ignored by older code.
