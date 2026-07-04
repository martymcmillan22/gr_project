# Phase 2 Semantic Sprint Checklist

Purpose: Execute semantic intelligence work in small, verifiable steps while protecting current preset UX stability.

## Global Rules

- [ ] One change set at a time.
- [ ] Verify each step before moving to the next.
- [ ] No schema-breaking manifest changes without explicit gate approval.
- [ ] Preserve baseline preset UX behavior (built-in, custom, current filters).

## Daily Command Rhythm

### Start of day

- [ ] `./a_gr_venv/bin/python manage.py check`
- [ ] `./a_gr_venv/bin/python manage.py test`

### Before commit

- [ ] `cd frontend_homepage && npm run build`
- [ ] `./a_gr_venv/bin/python manage.py test`

### End of day

- [ ] Run semantic browser verification on `/homepage/`.
- [ ] Log pass/fail + blockers in sprint notes.

---

## Day 1 - Lock Semantic Contract

Outcome target: approved v1 semantic spec for 4 views.

Tasks
- [ ] Define `operations_health`.
- [ ] Define `customer_journey`.
- [ ] Define `delivery_risk`.
- [ ] Define `executive_snapshot`.
- [ ] For each view, define categories, required tag profiles, component/page signatures, default sort/group.
- [ ] Add explicit non-goals per view.

Verification
- [ ] Team review pass.
- [ ] No unresolved spec questions.

Stop/Go
- [ ] STOP if any view lacks deterministic inclusion rules.
- [ ] GO when spec is signed off.

## Day 2 - Build Mapping Skeleton

Outcome target: semantic view id resolves to concrete filter object.

Tasks
- [ ] Add semantic mapping module.
- [ ] Add invalid view fallback behavior.
- [ ] Keep existing preset behavior untouched.

Verification
- [ ] Manual call for each view id returns complete structure.

Stop/Go
- [ ] STOP if mapping output shape varies by caller.
- [ ] GO when outputs are stable and complete.

## Day 3 - Add Mapping Tests

Outcome target: mapping contract is test-protected.

Tasks
- [ ] Positive tests for all 4 views.
- [ ] Negative tests for unknown ids.
- [ ] Strict key assertions for output shape.

Verification
- [ ] `./a_gr_venv/bin/python manage.py test` passes.

Stop/Go
- [ ] STOP on ambiguous test expectations.
- [ ] GO when all mapping tests pass.

## Day 4 - Implement Deterministic Resolver

Outcome target: ranked slide results are predictable.

Tasks
- [ ] Add weighted scoring: category, tag profile, component/page signature.
- [ ] Add tie-break policy.
- [ ] Document score rationale in code comments.

Verification
- [ ] Repeated runs with same input produce same order.

Stop/Go
- [ ] STOP if ordering changes across runs.
- [ ] GO when determinism is confirmed.

## Day 5 - Resolver Fixture Matrix

Outcome target: resolver quality proven on controlled data.

Tasks
- [ ] Add fixtures for mixed-match scenarios.
- [ ] Add fixtures for tie scenarios.
- [ ] Add stress fixture with noisy metadata.
- [ ] Assert expected rank order per scenario.

Verification
- [ ] `./a_gr_venv/bin/python manage.py test` passes.

Stop/Go
- [ ] STOP if tie behavior is inconsistent.
- [ ] GO when matrix passes fully.

## Day 6 - Integrate Semantic Layer (Safe Path)

Outcome target: semantic presets wired without regressing existing presets.

Tasks
- [ ] Route semantic view selection through mapping + resolver.
- [ ] Preserve built-in/custom/current-filter behavior.
- [ ] Keep delete-button and active-badge logic unchanged.

Verification
- [ ] Existing preset flows pass manually.
- [ ] Semantic views apply expected filters/results.

Stop/Go
- [ ] STOP if existing preset UX regresses.
- [ ] GO when parity is maintained.

## Day 7 - Instrument Preset Behavior Metrics

Outcome target: measurable semantic usefulness.

Tasks
- [ ] Log semantic preset selected event.
- [ ] Log first override after selection.
- [ ] Log settled filter state after interaction pause.

Verification
- [ ] Events are visible from local run.
- [ ] Event payload includes view id and timestamp.

Stop/Go
- [ ] STOP if events are missing key fields.
- [ ] GO when event stream is complete.

## Day 8 - Add Semantic Coverage Linter

Outcome target: metadata gaps are detectable fast.

Tasks
- [ ] Build linter for required category/labels/tag profile/component signatures.
- [ ] Group findings by semantic view.
- [ ] Output actionable fix hints.

Verification
- [ ] `./a_gr_venv/bin/python manage.py check` passes.
- [ ] `./a_gr_venv/bin/python manage.py test` passes.

Stop/Go
- [ ] STOP if report is noisy/non-actionable.
- [ ] GO when report is clean and useful.

## Day 9 - Browser Regression and Scripted Validation

Outcome target: semantic views are stable in real UI.

Tasks
- [ ] Script E2E checks for all 4 semantic views.
- [ ] Verify expected slide sets.
- [ ] Verify active preset badge text and mode transitions.

Verification
- [ ] Desktop browser run passes.
- [ ] No control-state regressions.

Stop/Go
- [ ] STOP on expected vs actual slide-set mismatches.
- [ ] GO when scripted checks pass.

## Day 10 - Freeze and Release Gate

Outcome target: decision-ready Phase 2 closure.

Tasks
- [ ] Publish semantic spec v1 and resolver rules.
- [ ] Summarize metrics: override rate and metadata coverage.
- [ ] Record known gaps and next risks.
- [ ] Complete go/no-go review.

Verification
- [ ] Stakeholder review completed.

Stop/Go
- [ ] STOP if metrics are missing/inconclusive.
- [ ] GO to Phase 3 only with explicit approval.

---

## Hard Gates

- [ ] Gate A: No integration before mapping tests are green.
- [ ] Gate B: No semantic UI behavior before resolver determinism is proven.
- [ ] Gate C: No pilot expansion before preset regression tests pass.
- [ ] Gate D: No Phase 3 start without explicit go decision.
