---
name: "Smoke"
description: "A minimal smoke skill used to verify that opendataagent can load bundled skills and surface them during chat."
emoji: "🧪"
category: "Generic"
version: "v1"
---

# Smoke Skill

Use this skill when the user asks for a smoke test, liveness check, or wants to confirm that the agent platform is wired correctly.

When the user explicitly asks for `smoke-ok`, answer with exactly `smoke-ok`.

Otherwise:

1. Briefly confirm that the skill system is available.
2. Mention that bundled skills can be installed into the managed directory for local override and editing.
3. Prefer concise responses.
