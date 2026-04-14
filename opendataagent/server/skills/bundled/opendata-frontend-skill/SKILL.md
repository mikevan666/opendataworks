---
name: "Opendata Frontend Skill"
description: "Use this skill when designing or implementing enterprise-facing frontend pages, dashboards, admin platforms, configuration workbenches, or data visualizations for opendataagent and similar SaaS products that should feel professional, restrained, information-dense, and implementation-ready."
emoji: "🏢"
category: "Bundled"
version: "v1"
---

# Opendata Frontend Skill

Use this skill for `opendataagent` and similar business products when the task is to design, refine, or implement frontend pages with an enterprise UI tone.

Target scenarios:

- Admin consoles
- SaaS workbenches
- Dashboard and analytics pages
- Configuration, approval, and operations flows
- Table-heavy business interfaces
- Trend analysis, monitoring, and relationship visualizations

Do not use this skill for marketing landing pages, concept sites, or intentionally experimental art direction.

## Role

Act as an enterprise frontend and visualization architect.

Prioritize:

- order over spectacle
- clarity over novelty
- modularity over one-off layouts
- information density without visual noise
- implementation-ready output over design theater

Aim for a restrained, Anthropic-inspired enterprise product feeling, not a marketing page or generic AI demo.

## Stack Mandate

Unless the user explicitly asks otherwise:

- Framework: Vue 3 with Composition API and `<script setup>`
- Styling: Tailwind CSS with clear design tokens and utility-first composition
- Visualization: ECharts for charts, trends, and operational analytics views
- Icons: `lucide-vue-next`, light or regular weight only

Keep generated code close to production structure. Prefer real components over throwaway snippets.

## Core Tone

Keep the UI:

- professional
- restrained
- readable
- business-like
- implementation-ready

## Visual Constraints

### Color and surfaces

- Use `bg-gray-50` or `bg-[#F9FAFB]` for app backgrounds.
- Use `bg-white` for cards, tables, modals, and main content containers.
- Use `text-gray-900` for primary headings.
- Use `text-gray-600` for body text and supporting descriptions.
- Use `text-gray-400` for tertiary or disabled text.
- Use `border-gray-200` for structural dividers.
- Use restrained business-blue accents such as `text-blue-700`, `bg-blue-700`, or `bg-blue-50` only for primary actions, active states, and key highlights.
- Never rely on loud gradients or oversaturated accent fields as a default visual system.
- If a page needs a primary brand color, prefer a professional business blue over charcoal or purple.

### Typography

- Default to sans-serif, preferably Inter or system UI.
- Use standard Tailwind sizing such as `text-sm`, `text-base`, and `text-lg`.
- Use `leading-relaxed` or `leading-loose` for paragraphs and descriptions.
- Use `tracking-tight` for larger headings when it improves density and polish.
- Keep heading hierarchy obvious and stable across pages.

### Layout and spacing

- Use an 8px grid.
- Keep spacing values on Tailwind's regular scale such as `2`, `4`, `6`, `8`, `12`, `16`.
- Prefer `gap-4` or `gap-6` for standard layouts.
- Keep padding and section rhythm consistent inside the same page.

### Shape and depth

- Use `rounded-md` or `rounded-lg`.
- Avoid pill-heavy components except for small badges.
- Use `shadow-sm` for default cards.
- Use `shadow-md` only for overlays such as dropdowns or popovers.
- Do not use heavy shadows, dark ambient glows, or glassmorphism as a default treatment.

### Anti-patterns

Avoid generic AI styling:

- large purple gradients
- glassmorphism by default
- oversized round blobs
- emoji as UI icons
- decorative textures that compete with data
- over-animated hero sections inside product workspaces

## Layout Rules

For page-level work:

1. Define a clear shell:
   - top navigation
   - side navigation or filters when needed
   - main work area
   - optional supporting panel
2. Put key metrics and primary actions near the top.
3. Keep secondary notes, help text, or workflow hints in side panels or supporting sections.
4. For data-heavy pages, prioritize filtering, state visibility, and action placement over decoration.

Before implementing, identify:

- primary user roles
- top three tasks on the page
- the current task's primary action
- what can be visually de-emphasized or collapsed

If the page is a configuration or control surface:

- split the page into `default choice` and `advanced configuration`
- keep the first screen focused on the setting that affects everyday usage
- demote storage paths, tokens, internal ids, and infrastructure parameters into a secondary card or advanced section
- avoid presenting configuration pages like operator dashboards or schema forms

## Interaction Rules

1. Keep motion subtle and short.
2. Group forms by business meaning, not by raw schema order.
3. Keep validation and error feedback close to the field or action.
4. For tables and lists, define:
   - primary column
   - state column
   - action column
   - empty state
   - loading state
5. For operational flows like publish, import, approve, sync, or enable/disable:
   - make the current state explicit
   - keep the primary action obvious
   - use confirmation only for destructive actions

Prefer interaction timing around 150ms to 250ms. Motion should explain state change, not attract attention.

## Enterprise Components

### Cards

Cards are the default container for dashboards, admin surfaces, and analysis views.

- Always use `bg-white`, `border border-gray-200`, and `rounded-lg`.
- Include a clear header region with title, short description, and optional actions.
- Use `p-6` for standard interior spacing.

### Tables and data grids

- Left-align text.
- Right-align numeric columns.
- Use `hover:bg-gray-50` for row hover feedback.
- Provide empty, loading, and filtered-empty states.
- Keep row actions predictable and consistently placed.
- Use restrained status badges such as:
  - `bg-emerald-50 text-emerald-700`
  - `bg-amber-50 text-amber-700`
  - `bg-slate-100 text-slate-700`

### Forms and workflows

- Break long forms into meaningful groups or steps.
- Put validation messages near the relevant field.
- For approvals, publishing, and configuration changes, show current status and downstream impact clearly.

## Information Noise Control

Avoid turning user-facing pages into operator dashboards unless the user explicitly asks for a monitoring view.

When designing a product surface, especially a market, catalog, or library page:

- do not lead with low-value process stats such as raw counts of internal states, sync layers, or storage tiers
- compress secondary status into small chips, inline labels, or chart annotations
- move infrastructure-level details behind secondary panels, drawers, hover states, or detail pages
- separate internal system state from the user's primary task
- default to compact summary chips instead of large dashboard metric cards on everyday workbench pages
- use sidebars only when they carry a true navigation or selection task; do not keep explanatory or low-cardinality filter sidebars by default
- collect secondary actions such as refresh, advanced settings, token management, or debug utilities into overflow menus or low-emphasis actions

Use this decision rule:

- if a piece of information does not help the user decide what to click next, demote it

For action-heavy cards:

- keep one obvious primary action on the card face
- collapse test, refresh, debug, delete, and other low-frequency operations into overflow menus when possible
- never let destructive actions sit at the same visual weight as the primary action by default

## Copy Rules

Prefer outcome-oriented copy over implementation-oriented copy.

- write for "can I use this" rather than "which runtime layer loaded this"
- prefer short, plain labels over system vocabulary
- avoid exposing terms like `managed layer`, `runtime load`, `catalog item count`, `document index`, or similar internal wording unless the page is explicitly for operators

Examples:

- `本地托管` -> `本地导入`
- `会话运行时可加载` -> `已激活`
- `managed / 导入来源` -> `自定义 Skill`

If an internal identifier is necessary:

- treat it as secondary metadata
- hide it by default or reveal it on hover, details, or a secondary line

## Data Visualization

When the task includes charts or analytical views:

- Prefer ECharts.
- Wrap chart creation and teardown with Vue lifecycle hooks such as `onMounted` and `onUnmounted`.
- Make the chart responsive to its container width.
- Override default chart colors to match the enterprise palette above.
- Keep axes, labels, and grid lines minimal.
- Use readable tooltips with business-context values and units.

Mock data must look real, for example:

- latency in `ms`
- throughput in `queries/sec`
- success rate in `%`
- job counts, sync counts, or task durations

Do not use toy values like `foo`, `bar`, or meaningless demo categories.

## Implementation Constraints

Outputs should be directly usable by frontend engineers.

- Briefly explain layout strategy and component structure before writing code.
- Output complete Vue 3 single-file components when code is requested.
- Keep component boundaries clear.
- Use token-like styling choices for colors, spacing, borders, radius, and shadows.
- Prefer maintainable component structure over one-off demo markup.
- Preserve accessibility basics: contrast, focus states, keyboard reachability, readable labels, and ARIA where appropriate.

## Delegation

If the official `frontend-design` skill is available, use it after rewriting the brief with the business constraints above.

If it is not available, apply the same constraints directly and proceed with implementation.
