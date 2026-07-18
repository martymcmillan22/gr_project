# Deterministic Vite Hygiene Audit Statement (for VS Code AI)

> Run a full Vite hygiene audit now.
>
> 1. Check the repository for any tracked files under frontend_homepage/node_modules/.vite/ including _metadata.json.
> 2. If any Vite artifacts are tracked, untrack them using a scoped hygiene commit:
>
> - remove the tracked .vite files from the Git index
> - ensure .gitignore covers .vite/ and _metadata.json
> - commit only the hygiene fix with no logic, routing, gating, or determinism changes
>
> 3. Confirm the local .vite cache still exists on disk but is no longer tracked by Git.
> 4. After cleanup, run the full determinism suite (unit, integration, E2E, visual, CSS) to verify zero drift across all four tiers: Novice, Intermediate, Studio, Enterprise.
>
> This audit must be isolated, intentional, and follow the established governance pattern.
