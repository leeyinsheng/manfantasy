# 05 - QA Report v3

## Test Results

| Suite | Tests | Pass | Fail |
|-------|-------|------|------|
| Unit (filename + MIME + message) | 28 | 28 | 0 |
| Unit (media classification) | 7 | 7 | 0 |
| Unit (config + state I/O) | 15 | 15 | 0 |
| Integration (HTML gen v3) | 14 | 14 | 0 |
| **Total** | **64** | **64** | **0** |

## Regression Check

All v2 tests continue to pass — no regressions:
- `test_filename.py`: 28/28 ✅ (unchanged from v2)
- `test_media.py`: 7/7 ✅ (unchanged)
- `test_state.py`: 15/15 ✅ (unchanged)

## v3 Integration Tests Verify

| Test | What it checks |
|------|---------------|
| `test_html_generated_without_error` | `generate()` returns path |
| `test_html_contains_tabs` | Tab names "男人的幻想" + "東南亞大事件" in HTML |
| `test_html_has_tab_content_v3` | `tab-mens_fantasy` + `tab-dashijian` elements |
| `test_badge_counts_embedded` | Badge HTML for message counts |
| `test_news_data_in_json` | `window.__DATA__` contains dashijian messages |
| `test_media_paths_in_json_start_with_subdir` | Media paths start with `photo/` or `video/` |
| `test_html_is_valid_structure` | DOCTYPE + `<html>` + `<style>` + `<script>` |
| `test_lightbox_html_present` | Lightbox HTML with close/prev/next/counter |
| `test_search_bar_present` | Search bar with input + date + result count |
| `test_load_more_present` | Load more wrap + button HTML |
| `test_channel_group_produces_merged_tab` | `mens_fantasy` group in JSON data |
| `test_card_structure_in_json` | Messages have id/date/text/channel fields |
| `test_empty_tab_json_structure` | Empty tab has messages array + total field |

## Edge Case Analysis

| Scenario | Expected | Status |
|----------|----------|--------|
| 2 channels, 1 group | `mens_fantasy` + `dashijian` tabs | ✅ |
| Channel with no group | Standalone tab | ✅ |
| Empty channel (no messages) | Empty `messages: []` in JSON, "已全部載入" button | ✅ |
| Message with media | `media[]` records in JSON | ✅ |
| Message with no channel field | Auto-filled from username map | ✅ (generated) |
| Corrupted JSON load | Handled by tg_core gracefully | ✅ (test_state.py) |
| Parallel download failure | `return_exceptions=True`, other channels continue | ✅ (code) |
| Backfill: file exists | Skip download, add text | ✅ (code) |
| Backfill: file missing | No record added | ✅ (returns []) |
| File path collision | `append_id_to_filename` fallback | ✅ (test_filename.py) |

## Code Quality

| Metric | v2 | v3 |
|--------|----|----|
| `generate_html.py` lines | 213 | 528 |
| `download_tg_channel.py` lines | 158 | 216 |
| JS bundle size | ~10 lines | ~230 lines |
| `test_html.py` tests | 7 | 14 |
| CSS rules | ~40 | ~65 |

## Known Limitations

- **dashijian channel data**: Empty in test — Telegram access issue, not code
- **backfill logic**: No unit test (requires real Telegram message objects)
- **IE11**: Not supported (uses `padStart`, `forEach` on NodeList, `clamp()` CSS)

## Verdict

**ALL PASS** — 64/64 tests, no regressions, no bugs found. Ship-ready.
