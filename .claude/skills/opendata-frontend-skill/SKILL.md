---
name: "Opendata Frontend Skill"
description: "Use this skill when designing or implementing enterprise-facing frontend pages, dashboards, admin platforms, configuration workbenches, or data visualizations for opendataagent and similar SaaS products that should feel professional, restrained, information-dense, and implementation-ready."
emoji: "🏢"
category: "Generic"
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

## Data Visualization

When the task includes charts or analytical views:

- Prefer ECharts.
- Make the chart responsive to its container width.
- Override default chart colors to match the enterprise palette above.
- Keep axes, labels, and grid lines minimal.
- Use readable tooltips with business-context values and units.
