# GrassRoots Version Control System

This document defines the required Git workflow for this repository.

## Goals
- Keep history clean and reviewable.
- Ship small, reversible changes.
- Prevent accidental regressions in production.

## 1) Branch Model

## Long-lived branches
- `main`: stable production-ready code only.
- `develop` (optional): integration branch if release batching is needed.

If your team does not use `develop`, merge feature branches directly into `main` via PR.

## Short-lived branches
- `feature/<scope>-<short-name>`
- `fix/<scope>-<short-name>`
- `hotfix/<scope>-<short-name>`
- `chore/<scope>-<short-name>`
- `release/<yyyy-mm-dd-or-version>`

Examples:
- `feature/semantic-ops-heatmap-deltas`
- `fix/admin-css-compat`
- `hotfix/story-save-regression`

## 2) Commit Rules

## Commit frequency
- Commit every logical unit (typically every 20-90 minutes).
- Never mix unrelated changes in one commit.

## Commit format
Use Conventional Commit style:
- `feat: ...`
- `fix: ...`
- `chore: ...`
- `refactor: ...`
- `docs: ...`
- `test: ...`

Optional scope:
- `feat(semantic-ops): add transitional delta strip`
- `fix(css): remove unsupported color-mix usage`

## Commit quality requirements
- Message explains "what changed" and "why".
- Code compiles/tests for affected area.
- No generated build artifacts unless intentional for release packaging.

## 3) Pull Request Rules

- All changes merge through Pull Requests.
- Minimum 1 reviewer approval.
- PR must pass required checks.
- PR should be under ~500 changed lines when possible.

## PR checklist (required)
- [ ] Scope is single-purpose.
- [ ] Tests/checks run for affected areas.
- [ ] Migration risk reviewed (if DB touched).
- [ ] Backward compatibility reviewed.
- [ ] Rollback approach noted.

## 4) Protected Branch Settings (recommended)

Apply to `main` (and `develop` if used):
- Require pull request before merging.
- Require status checks to pass.
- Require up-to-date branch before merge.
- Require at least 1 approval.
- Block force pushes and branch deletion.

## 5) Merge Strategy

Default: **Squash merge** for feature/fix branches.
Use **Merge commit** only when preserving branch history is important.
Avoid rebasing shared branches after publishing.

## 6) Release and Tagging

- Create release branch when preparing production rollout.
- Final validation uses docs/operations/production_readiness_checklist.md.
- Tag production releases using SemVer:
  - `v0.1.0`, `v0.2.0`, `v1.0.0`

## Release steps
1. Freeze scope.
2. Run readiness checklist.
3. Merge release PR.
4. Tag commit.
5. Deploy.
6. Post-deploy verification.

## 7) Hotfix Workflow

1. Branch from `main`: `hotfix/<scope>-<name>`.
2. Implement minimal fix.
3. Fast-track PR with focused review.
4. Tag patch release (`vX.Y.Z+1`).
5. Back-merge to `develop` if used.

## 8) Database Safety Rules

- Any destructive DB operation requires explicit human approval.
- Always create backup/snapshot before production migrations.
- Include migration rollback notes in PR description.

## 9) Ignore and Artifact Policy

- Keep generated artifacts out of Git unless required.
- Keep OS metadata files ignored (`.DS_Store`).
- If a tracked generated file must be ignored later, run one-time untrack with:
  - `git rm --cached <path>`

## 10) Day-to-Day Command Flow

1. `git checkout -b feature/<scope>-<name>`
2. Make small changes.
3. `git add -p`
4. `git commit -m "type(scope): message"`
5. `git push -u origin <branch>`
6. Open PR and complete checklist.

## 11) Ownership

- Engineering owner keeps this workflow current.
- Changes to this file require team agreement.
