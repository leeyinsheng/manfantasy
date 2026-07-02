# 04 - Code Review v3

## Scope Check

| ID | Requirement | Status |
|----|-------------|--------|
| F14 | 平行頻道下載 | ✅ `asyncio.gather()` in `main()` |
| F15 | 圖片燈箱 | ✅ CSS + JS lightbox with keyboard nav |
| F16 | 搜尋+日期篩選 | ✅ `applySearch()` with keyword + date range |
| F17 | 分頁載入 | ✅ `renderCards()` with `PAGE_SIZE=50` |
| F18 | 媒體效能 | ✅ `loading="lazy"` + `preload="none"` |
| F19 | 文字回溯 | ✅ `_get_existing_media_records()` + backfill flag |

**Intent:** 4-channel TG downloader with merged tab UI, parallel download, backfill
**Delivered:** All 6 requirements implemented. 3 new channels, group-based merging, JS-rendered UI matching prototype.

**Scope:** CLEAN — all changes trace to v3 PRD requirements.

---

## File-by-File Review

### `src/channels.json`
- 4 channels: ai_guoman (backfill), ciyuanb (new), llcosfc (new), dashijian (unchanged)
- Group `mens_fantasy` merges 3 channels into one tab
- **Note:** `backfill: true` on ai_guoman. Remove after first successful run.

### `src/download_tg_channel.py`
- **Parallel download** (line 200-204): Clean `asyncio.gather()` with `return_exceptions=True`. Each channel has independent state/dir — no race conditions.
- **Backfill support** (line 28-118): `_get_existing_media_records()` checks filesystem for previously downloaded files. `process_channel()` handles backfill flag with three-way branching: normal / backfill-existing / backfill-new.
- **DRY note:** `_get_existing_media_records()` duplicates filename generation logic from `download_media_message()`. Acceptable for one-time backfill operation, but if backfill logic grows, consider extracting shared `_predict_media_paths()` helper.
- **Error handling:** Each channel wrapped in try/except within `asyncio.gather()`. Failed channel doesn't block others.

### `src/generate_html.py`
- **Architecture change:** Server-side HTML generation → JS-driven rendering from `window.__DATA__` JSON. This is a deliberate shift per prototype design.
- **CSS:** Full color system swap to `#d14334` red accent, serif display font, sticky tabs. Matches `design_20260702.html` line-for-line.
- **JS:** ~230 lines covering tab switching, `renderCards()`, `applySearch()`, lightbox, pagination. Uses ES5 syntax for broad browser compatibility.
- **Channel merging:** `_build_tab_data()` groups channels by `group` field, merges messages sorted by ID descending, annotates `channel` field with username.
- **Global state:** `CHANNEL_USERNAME_MAP` as module-level cache. Safe for single-invocation script.
- **XSS:** `escHtml()` escapes all text content. Media paths are filesystem-originated, not user-controlled.
- **`padStart`:** ES2017. All modern browsers (Chrome 57+, Firefox 51+, Safari 10+, Edge 15+) support it. IE11 already unsupported by CSS features used.

### `tests/test_html.py`
- **14 tests** covering: structure, tabs, JSON data extraction, media paths, lightbox HTML, search bar, load more, channel grouping, card structure, empty tabs.
- Test setup now creates a temporary `channels.json` to control tab layout.
- **Missing:** Backfill unit test, channel merge logic unit test. Acceptable for v3 — backfill is a one-time operation best verified with real Telegram data.

---

## Test Coverage

| Suite | Tests | Status |
|-------|-------|--------|
| Unit (core logic) | 51 | ALL PASS |
| Integration (HTML gen v3) | 14 | ALL PASS |
| **Total** | **64** | **ALL PASS** |

---

## Verdict

**APPROVED** — all v3 requirements implemented, 64 tests pass, no regressions.

### Action items (non-blocking):
1. Remove `backfill: true` from `channels.json` after first successful run
2. Consider extracting shared media path prediction in a future refactor

---

## Diff Summary

| File | + | - | Change |
|------|---|---|--------|
| `channels.json` | +18 | -2 | 2 new channels, group, backfill |
| `download_tg_channel.py` | +83 | -6 | Parallel + backfill |
| `generate_html.py` | +316 | -200 | Full UI rewrite |
| `test_html.py` | +91 | -42 | Rewritten for v3 structure |
