# Compose Project Isolation Design

## Summary

OpenDataWorks and `opendataagent` are separate deployment units, but both can be started from a directory named `deploy`.
When Compose is run without an explicit project name, it may assign both stacks the same project label, which can make containers from one stack appear as orphan containers in the other.

This change makes `opendataagent` use the explicit Compose project name `opendataagent`.
OpenDataWorks root deployment keeps its current project behavior, fixed container names, and existing volumes.

## Current State

- OpenDataWorks root scripts run Compose from `deploy/` and keep existing `opendataworks-*` container names.
- `opendataagent` scripts also run Compose from `opendataagent/deploy/`.
- Manual `docker compose up` from either `deploy` directory can default the project name to `deploy`.
- `opendataagent` already uses distinct host ports by default: web `18080`, server `18900`, MySQL `13306`.

## Problem

The main issue is not a shared service name alone; it is shared Compose project identity.
If both deployments are labeled as project `deploy`, Compose can treat containers from the other stack as orphans.
Using `--remove-orphans` in that state is risky because the two stacks may share the same project label.

## Solution

- Add `COMPOSE_PROJECT_NAME=opendataagent` to `opendataagent/deploy/.env.example`.
- Update `opendataagent` start and stop scripts to pass `-p "$COMPOSE_PROJECT_NAME"` on every Compose call.
- Resolve the project name in this order:
  1. caller-provided `COMPOSE_PROJECT_NAME`
  2. `opendataagent/deploy/.env`
  3. default `opendataagent`
- Keep `restart.sh` as stop-then-start so it inherits the same project resolution.
- Update docs to recommend `bash ../scripts/start.sh` and document manual `docker compose --project-name opendataagent --env-file .env up -d --build`.

## Tradeoffs

- This does not add multi-instance support for multiple `opendataagent` deployments on one host.
- This does not rename or migrate existing OpenDataWorks volumes, avoiding avoidable production data risk.
- Existing `opendataagent` deployments previously created under project `deploy` may need a one-time maintenance restart.

## Migration Note

If both stacks were previously started with the default project `deploy`, stop and restart them in a maintenance window.
Avoid running `--remove-orphans` against only one stack until old containers are understood, because containers from both products may share the same project label.
