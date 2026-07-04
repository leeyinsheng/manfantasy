# 05 - QA Report v7

## Execution Summary

| Item | Result |
|------|--------|
| Date | 2026-07-04 |
| Test runner | `python3 -m unittest discover tests` |
| Total tests | 88 |
| Passed | 88 |
| Failed | 0 |

## Test Breakdown

| Test File | Tests | Pass | Fail |
|-----------|-------|------|------|
| `test_filename.py` | 29 | 29 | 0 |
| `test_html.py` | 20 | 20 | 0 |
| `test_media.py` | 7 | 7 | 0 |
| `test_state.py` | 12 | 12 | 0 |
| `test_xv_spider.py` | 19 | 19 | 0 |
| **Total** | **88** | **88** | **0** |

## Browser-Verified Edge Cases (fixture with real varying-size images, run via Playwright)

| Case | Result |
|------|--------|
| XSS payload in card text (`<script>alert('xss')</script>`, `&`, `"`, `'`, `<b>`) | Renders as literal escaped text in both the waterfall card and the detail sheet — no execution |
| XSS payload in text-only card | Same — literal escaped text |
| Grouped multi-photo message (`grouped_id`, 3 photos) | Merges into a single waterfall card with correct "📷 3" badge |
| Zero-message tab | Sentinel shows "已無更多內容" (Phase 4 fix confirmed working) |
| Search filter (keyword) | Correctly scans the full per-tab dataset, not just the loaded batch; result count accurate |
| Desktop-width viewport (1200px) | Same narrow centered mobile layout as 390px viewport — confirms mobile-only requirement |
| Lightbox (image + video), prev/next, Escape/ArrowKey | All work |
| Detail sheet open/close, bottom-nav tab switch, search-toggle active-state sync | All work |

## Critical Finding During Regression Testing (Fixed)

**Stored XSS via inline `<script>` data embed** — `window.__DATA__ = {tabs_json};` embedded the raw JSON
directly into an inline `<script>` block. A Telegram channel post containing the literal text
`</script><script>...` would prematurely close the script block during HTML parsing (which happens
before JS parsing) and execute the injected script in every visitor's browser — confirmed via a real
`alert()` firing during Playwright testing before the fix.

This vulnerability was **inherited from v3** (same embedding pattern existed before this cycle), not
introduced by the v7 rewrite, but since this app renders arbitrary user-controlled Telegram channel
content, it was fixed immediately: `tabs_json` now has `</` replaced with `<\/` before embedding
(`src/generate_html.py`), which is valid, semantically-identical JS/JSON and prevents the HTML tokenizer
from ever seeing a literal `</script` sequence. Re-verified with the same payload post-fix: renders as
inert text, no dialog fires.

## Regression Check

| Component | Status |
|-----------|--------|
| Telegram channel downloading / data layer | Untouched, all 48 pre-existing tests pass |
| xv_spider.py / xvideos (out of scope) | Untouched, all 19 tests pass |
| Grouped message merge (`_merge_grouped_messages`) | Confirmed working via browser fixture |
| Media path normalization | Covered by `test_media_paths_in_json_start_with_channel_id` |

## Gate Decision

**Verdict**: Phase 5 GATE — **PASS**. 88/88 tests pass, all designed edge cases verified in a real
browser, one pre-existing security issue found and fixed.
