# Human UI/UX Design Principles

## Purpose

This document defines the human-facing UI/UX principles for the Grassroots dual-UI system. The human surface is optimized for calm visual clarity, low resistance, and gradual increases in structure as the user moves from idea capture to governed delivery.

The human UI is for people. The agent UI is for Copilot, VS Code AI, and other orchestrators. Both surfaces read from the same deterministic backend and narrative model, but they present different interaction densities.

## Core Split

- UI is aesthetics.
- UX is flow.
- Human UI should be visually attractive, simple, and reassuring.
- Human UX should minimize resistance and cognitive load.
- Agent UI may be dense, structural, and orchestration-heavy.

## Design Principles

### 1. Start with creative freedom

Idea capture must feel painless. In the creative phase, the user should not be interrupted by structure, validation pressure, or heavy form behavior. The first interaction should support fast capture, not analysis.

### 2. Increase structure gradually

The flow should move from low structure to higher structure over time. Structure should appear only when the user has entered a more governed phase and is ready for it.

### 3. Keep the visible surface calm

Human-facing screens should use clear hierarchy, restrained density, and obvious next steps. The screen should feel attractive and composed, not crowded.

### 4. Reduce resistance at every step

Every action should have a clear affordance. Default states should be usable without configuration. The user should always know what to do next.

### 5. Use Veil as progressive disclosure

Veil means complexity is present, but not fully exposed at once. The interface should reveal more depth only when the user moves into a deeper phase or requests it. This preserves confidence while still supporting advanced workflows.

### 6. Separate creation from governance

Creation happens in lightweight surfaces. Governance appears later, after the user has already captured the idea or intent. The human UI should avoid forcing governance into the earliest creative moment.

### 7. Respect energy state

Creative states are high energy. Structured states are lower energy. The UI should match that rhythm:

- high-energy phases: minimal prompts, fast capture, low friction
- lower-energy phases: more review, more structure, more guided validation

### 8. Make the path legible

The human user should always be able to see where they are in the journey: Idea, Seed, Project, MVP, Studio, Enterprise. The current phase should be easy to recognize and easy to advance.

## Human UX Rules

- Prefer one primary action per screen.
- Prefer short labels and plain language.
- Prefer guided defaults over empty forms.
- Prefer progressive disclosure over full-density dashboards.
- Prefer readable summaries over technical controls.
- Prefer quick capture over deep configuration in early phases.

## Human UI Rules

- Use visually attractive composition with clear spacing and hierarchy.
- Keep panels calm and purposeful.
- Use strong section titles, but avoid overwhelming users with too many simultaneous controls.
- Keep the display narrative-first, not system-first.
- Let the interface feel like a companion, not a control room.

## Phase Guidance

### Idea

The Idea surface should feel the most open. It should prioritize capture, not structure. This is the lowest-friction entry point.

### Seed

The Seed surface should add only enough structure to validate direction. It should support thesis shaping and gentle review.

### Project

The Project surface should begin to introduce workflow and timeline detail. Structure can increase here because the user is moving into execution.

### MVP

The MVP surface should support review, packaging, and readiness checks. It can be more governed, but still human-readable.

### Studio

The Studio surface should support publishing and creator-tier synthesis without becoming visually heavy.

### Enterprise

The Enterprise surface should support orchestration and coordination while remaining understandable to humans.

## Office Model

The human UI can be organized by office and access context:

- Corporation / Twist: fast idea capture
- Museum / QC office: seed review and approval
- Garden: project execution and launch
- Meta Interface: enterprise-only governance and read-only meta compartments

The office model should never increase friction unnecessarily. It should help users understand where they are and why the surface looks different.

## Read-Only Compartments

Subject compartments should be read-only views of generated artifacts. CRUD belongs in the governing interfaces, not inside the artifact viewers.

This preserves clarity:

- interfaces create and manage
- compartments display and reflect

## Acceptance Criteria

A human-facing surface is correct when:

- it feels simple on first use
- it supports fast idea capture
- it introduces structure gradually
- it keeps complexity hidden until needed
- it stays visually calm and attractive
- it remains consistent with the deterministic narrative model

## Dual-UI Alignment

This human design model intentionally differs from the agent UI model:

- humans get calm, guided, low-resistance surfaces
- agents get dense, orchestrated, high-context surfaces

Both are valid. They serve different users and different cognitive modes.
