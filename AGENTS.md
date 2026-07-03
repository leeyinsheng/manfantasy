# AI Collaborative Development Workflow

## Phases

7 sequential phases — must be executed in order, no skipping.

| Phase | Name | Performer | Output |
|-------|------|-----------|--------|
| 1 | Product Ideation | Me | `docs/01_PRD.md` |
| 2 | Product Design | Me + AI | `docs/02_DESIGN.md` + `docs/prototype/design.html` |
| 3 | Feature Dev + Unit Tests | AI | `src/` + `tests/` (unit tests, all must pass) |
| 4 | Code Review | AI | `docs/04_REVIEW.md` |
| 5 | Regression Testing | AI | `docs/05_TEST_PLAN.md` + `docs/05_QA_REPORT.md` |
| 6 | Feature Verification | AI | `docs/06_VERIFICATION.md` |
| 7 | User Acceptance | Me | Sign-off / Rework |

## Startup Rules

Every time AI starts:

1. Read `docs/STATUS.md` to determine current phase
2. For the phase marked `⏳` (in progress), run `git log --oneline` to confirm all preceding docs have commits
3. If preceding docs are outdated → block and say "Preceding docs not updated. Please complete Phase N first."
4. If preceding docs are updated → read all preceding docs sequentially before execution

## Phase Transition Rules

| Transition | Prev Performer | Trigger |
|-----------|----------------|---------|
| Phase 1 → 2 | Me | I say "start phase 2" |
| Phase 2 → 3 | Me + AI | I say "start phase 3" |
| Phase 3 → 4 | AI | **AI auto-triggers** |
| Phase 4 → 5 | AI | **AI auto-triggers** |
| Phase 5 → 6 | AI | **AI auto-triggers** |
| Phase 6 → 7 | AI | AI updates STATUS.md, waits for me to say "UAT" |

## Completion Actions

When each phase completes, AI must:

1. **Commit** all outputs to git
2. **Update** `docs/STATUS.md`: set current phase to ✅, next phase to ⏳
3. **Notify** me that the phase is done and name the next phase

## Phase 5 Test Gate

Phase 5 is a hard gate — no feature gets to Phase 6 without a complete test cycle.

### Step 1 — Design test plan

AI reads `02_DESIGN.md` (design spec) and `src/` + `tests/` (implementation), then writes `docs/05_TEST_PLAN.md` covering:

- Functional test cases derived from DESIGN.md
- Edge cases, error paths, boundary conditions
- Integration points between components
- Regression test scope

### Step 2 — Execute

AI runs all tests:
- Unit tests from Phase 3
- Integration tests designed in Step 1
- End-to-end flows

### Gate

- **All pass** → update STATUS.md, proceed to Phase 6
- **Any fail** → AI updates STATUS.md marking Phase 3 as ⏳ with failed tests, blocks progression. I say "start phase 3" to fix, then re-run Phase 4 → 5.

## Rollback & Fix

When any phase finds issues:

1. AI updates STATUS.md: mark the affected phase as ⏳ with reason
2. AI tells me which phases need re-execution
3. I confirm by saying "start phase N". AI reads all preceding docs + review/report/test plan docs, then fixes
4. Fix complete → commit → update STATUS.md ✅
5. Re-run downstream phases (Phase 4 → 5 → 6)

**Phase 5 test failures** always roll back to Phase 3 (implementation must be fixed). Phase 5 regression tests and the test plan gate re-run after the fix.

## Directory Structure

```
docs/
├── STATUS.md               ← Phase status tracker
├── 01_PRD.md               ← Phase 1 output
├── 02_DESIGN.md            ← Phase 2 output
├── prototype/
│   └── design.html         ← Phase 2 HTML prototype
├── 03_IMPLEMENTATION.md    ← Phase 3 AI summary
├── 04_REVIEW.md            ← Phase 4 output
├── 05_TEST_PLAN.md         ← Phase 5 test design
├── 05_QA_REPORT.md         ← Phase 5 test results
└── 06_VERIFICATION.md     ← Phase 6 output
src/                        ← Phase 3 output
tests/                      ← Phase 3 output
```

## Flow Diagram

```
[Me] Phase 1 ──I say──→ [Me+AI] Phase 2 ──I say──→ [AI] Phase 3
                                                          │ auto
                                                          v
                                                  [AI] Phase 4
                                                          │ auto
                                                          v
                                              ┌── [AI] Phase 5 ──┐
                                              │ test design gate  │
                                              └─── all pass? ─────┘
                                               yes│        │no (→ P3)
                                                  v
                                          [AI] Phase 6
                                                  │ AI notifies done
                                                  v
                                          [Me] Phase 7 ──sign-off──→ Ship
                                                  │
                                                  └──rework→ Rollback Phase N
```

## gstack Skill Mapping

| Phase | Name | Performer | gstack Skill |
|-------|------|-----------|-------------|
| 1 | Product Ideation | Me | `/office-hours` (optional, AI challenges ideas) |
| 2 | Product Design | Me + AI | `/design-consultation` → `/design-html` |
| 3 | Feature Dev + UT | AI | `/spec` + TDD |
| 4 | Code Review | AI | `/review` |
| 5 | Regression Testing | AI | `/qa` + `/benchmark` (test design → execution) |
| 6 | Feature Verification | AI | `/browse` |
| 7 | User Acceptance | Me | `/ship` (optional, deploy after sign-off) |

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
