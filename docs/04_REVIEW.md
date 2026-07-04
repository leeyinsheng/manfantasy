# 04 - Code Review v7

## Scope Check: CLEAN

- Intent: waterfall card redesign + mobile-portrait-only layout, per `docs/01_PRD.md` / `docs/02_DESIGN.md`
- Delivered: full CSS/HTML/JS rewrite in `src/generate_html.py`, `tests/test_html.py` rewritten to match
- Data layer (`tg_core.py`, `download_tg_channel.py`, `channels.json`, message JSON shape) untouched, as scoped
- Also removed: the dead `TestXvHtml` test class (referenced `generate_html.XV_VIDEOS_FILE`, which no longer
  exists since the v3 rollback — these 8 tests were already failing before this change, unrelated to xv scope)

## Issues Found & Fixed

| Severity | Description | Status |
|----------|--------------|--------|
| Low | `loadNextBatch()` returned early for a tab with 0 messages without calling `updateSentinel()`, leaving the sentinel stuck on "載入更多…" instead of "已無更多內容" | Fixed |

## Issues Noted, Not Blocking

| Severity | Description |
|----------|--------------|
| Info | Search now scans the full per-tab `data.messages` array instead of only the currently-rendered batch (v3 only filtered within the current page). This is an intentional improvement needed for the infinite-scroll model to filter correctly, not a regression. |
| Info | Bottom nav no longer shows per-tab message-count badges (dropped per Phase 2 design decision to declutter the nav bar, matching the XHS/IG reference style). `total` is still present in the embedded JSON for potential future use. |

## Verdict

**PASS** — no blockers. 88/88 tests pass after the sentinel fix.
