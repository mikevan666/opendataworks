# Compose Project Isolation Implementation Plan

## Goal

Prevent OpenDataWorks and `opendataagent` from being treated as the same Compose project when both are deployed on one machine.

## Scope

- Fix only `opendataagent` project naming.
- Keep OpenDataWorks root Compose files, fixed container names, and existing volume behavior unchanged.
- Do not add `COMPOSE_IGNORE_ORPHANS`; the warning should be prevented by correct project labels.

## Implementation Steps

1. Add `COMPOSE_PROJECT_NAME=opendataagent` to `opendataagent/deploy/.env.example`.
2. Update `opendataagent/scripts/start.sh` to resolve the project name from shell env, `.env`, or default, then pass `-p "$COMPOSE_PROJECT_NAME"` to `up` and `ps`.
3. Update `opendataagent/scripts/stop.sh` with the same resolution order and pass `-p "$COMPOSE_PROJECT_NAME"` to `down`.
4. Leave `opendataagent/scripts/restart.sh` as stop-then-start.
5. Update `opendataagent` deployment docs to prefer `bash ../scripts/start.sh` and show the manual `--project-name opendataagent` command.
6. Add a migration note warning against one-sided `--remove-orphans` cleanup when old containers may share project `deploy`.

## Verification

- Run `bash -n opendataagent/scripts/start.sh`.
- Run `bash -n opendataagent/scripts/stop.sh`.
- Run `bash -n opendataagent/scripts/restart.sh`.
- Search docs for bare `docker compose up -d --build` in `opendataagent` deployment instructions.
- If Docker or Podman is available, run Compose config with project name and env file.
- If no container runtime is available, report that runtime Compose verification was skipped.

## Backout

Revert the `opendataagent` script, env-template, and documentation changes.
This restores the previous default Compose project behavior without changing OpenDataWorks data volumes.
