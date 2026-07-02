# 06 - Feature Verification v3

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| F14 | 平行頻道下載 | ✅ | `download_tg_channel.py:200` — `asyncio.gather(*tasks, return_exceptions=True)` |
| F15 | 圖片燈箱檢視 | ✅ | `generate_html.py` — `.lightbox` CSS + `lbState` JS + 鍵盤事件 |
| F16 | 訊息搜尋與日期篩選 | ✅ | `generate_html.py` — `.search-bar` HTML + `applySearch()` JS |
| F17 | 分頁載入 | ✅ | `generate_html.py` — `PAGE_SIZE=50`, `renderCards()`, `.load-more-btn` |
| F18 | 媒體載入效能優化 | ✅ | `generate_html.py` — `<img loading="lazy">` + `<video preload="none">` |
| F19 | 文字回溯擷取 | ✅ | `download_tg_channel.py:28` — `_get_existing_media_records()` + `backfill` flag |

## Detailed Verification

### F14: Parallel Download
- Code: `asyncio.gather()` replaces sequential `for` loop
- Each channel has independent state file and download directory — no race conditions
- `return_exceptions=True` ensures one channel failure doesn't block others
- **Verified:** Code review confirmed no shared mutable state between channels

### F15: Lightbox
- CSS: `.lightbox.open` → fullscreen overlay with `rgba(0,0,0,0.92)`
- Navigation: click ‹/› buttons, ←/→ keys, ESC to close, click backdrop to close
- Counter: `.lb-counter` shows "N / M"
- Grouping: All media in same tab share lightbox navigation
- Video support: Autoplay on open, native `<video>` controls
- **Verified:** 7 integration tests confirm HTML structure. Component present in `design_20260702.html` prototype.

### F16: Search + Date Filter
- Search bar HTML generated per text-mode tab
- `applySearch()`: keyword match on `.card-text` textContent, date range on `.card-date`
- Result count updates: "N 筆結果"
- Load-more button hidden during search, restored on clear
- **Verified:** Search bar HTML tests pass. JS logic mirrors prototype.

### F17: Pagination
- `PAGE_SIZE = 50` items per batch
- `renderCards(tabId, count)`: renders first batch initially
- Click "載入更多 (N)" → renders next batch
- Final state: "已全部載入" with `.done` class
- **Verified:** `test_load_more_present` confirms HTML. Load-more logic mirrors prototype.

### F18: Media Performance
- All `<img>` elements include `loading="lazy"` attribute
- All `<video>` elements include `preload="none"` attribute
- Video overlay: `.vid-overlay` with CSS triangle play button
- **Verified:** Code inspection. Attributes generated in `mediaHtml()` JS function.

### F19: Backfill
- `channels.json`: ai_guoman has `"backfill": true`
- `_get_existing_media_records()`: checks filesystem for photo/video files matching message date+ID
- Handles both photo messages and document messages (with original name or fallback naming)
- `process_channel()`: three-way branch — normal / backfill-new / backfill-existing
- Existing media not re-downloaded; new media downloaded normally
- Text records appended to `messages.jsonl` for backfilled messages
- **Verified:** Code review confirms no duplicate download. Backfill count reported in output.

## Channel Config Verification

```json
{
  "channels": [
    {"id": "ai_guoman", "mode": "text", "group": "mens_fantasy", "backfill": true},  // was "media"
    {"id": "ciyuanb",   "mode": "text", "group": "mens_fantasy"},                     // NEW
    {"id": "llcosfc",   "mode": "text", "group": "mens_fantasy"},                     // NEW
    {"id": "dashijian", "mode": "text"}                                               // unchanged
  ]
}
```

- 3 channels grouped → 1 "男人的幻想" tab (verified: `test_channel_group_produces_merged_tab`)
- dashijian standalone → 1 "東南亞大事件" tab (verified: `test_html_has_tab_content_v3`)

## Test Evidence

64/64 tests pass. 14 integration tests validate HTML structure, JSON data, and new UI components.

## Design Fidelity

`generate_html.py` output matches `design_20260702.html` prototype:
- Same CSS color system (`#d14334` accent, `#0a0a0a` background)
- Same font stack (serif display + system sans-serif)
- Same HTML structure (sticky tabs, search bar, cards-container, lightbox)
- Same JS architecture (IIFE, `renderCards()`, `applySearch()`, `lbState`)

**ALL VERIFIED PASS**
