# Model Service Config Plan

## Tasks

1. Add backend schemas for model detection request/response and persisted per-model detection status.
2. Add a DataAgent admin route for `POST /api/v1/nl2sql-admin/model-detections`.
3. Extend provider settings normalization to carry provider enable state and `model_detections` without adding database tables.
4. Refactor the Vue settings page into a simplified model service console, remove runtime details from the UI, drop the outer page header layer, and move save into the current provider title bar.
5. Update the configuration tab label from `智能问数` to `模型服务`.
6. Change provider save scope from whole-page save to current-provider save with per-provider dirty state and switch-away confirmation.
7. Keep model detection as a real check, but return the detection result without persisting provider draft changes until the current provider is explicitly saved.
8. Add targeted backend and frontend tests for detection state, enablement rules, dirty-state behavior, and API contract.

## Verification

- Run DataAgent pytest for admin routes and settings service tests.
- Run frontend tests for the model service settings page, including current-provider save and discard-on-switch behavior.
- Run `nvm use` and `npm --prefix frontend run build`.
- Use local mock data to visually check `/settings?tab=dataagent` on desktop and narrow viewports.

## Rollout

This is an admin UI and DataAgent API change. No migration is needed because detection data is stored in existing JSON settings. Existing saved provider settings remain readable; models without detection state will appear as not detected and cannot be newly enabled until detection succeeds. Detection remains a separate API call, but draft edits only become persistent when the current provider is saved.

## Backout

Revert the frontend page and admin route changes. Existing extra JSON fields under `provider_settings.model_detections` are ignored if not read.
