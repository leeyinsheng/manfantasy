# 05 - Test Plan v4

## Test Scope

| Layer | Scope | Tests |
|-------|-------|-------|
| Unit | xv_spider.py URL building, HTML parsing, config, dedup, file I/O | 17 tests |
| Integration | HTML generation with xv tabs, embedded data, CSS selectors | 11 xv tests |
| Regression | All existing Telegram functionality | 62 tests |
| **Total** | | **90 tests** |

---

## Functional Test Cases

### T1 — Spider URL Building
- **category page 0**: `/c/Lingerie-83?s=uploaddate`
- **category page N**: `/c/Lingerie-83/2?s=uploaddate`
- **search page 0**: `/?k=%E6%97%A5%E6%9C%AC&sort=uploaddate`
- **search page N**: `/?k=%E6%97%A5%E6%9C%AC&p=3&sort=uploaddate`
- **Chinese keyword encoding**: `/%E4%B8%AD%E5%9C%8B` for 中國

### T2 — HTML Parsing
- Parse single video block: extract eid, video_id, title, duration, quality (1080p), uploader, views, thumbnail
- Parse SD quality (360p)
- Parse no quality tag
- Parse views in millions (8.8M views)
- Parse multiple blocks in single HTML
- Parse empty HTML returns []

### T3 — Config Loading
- Valid config returns sources list
- Missing config returns []
- Missing xvideos.json returns []

### T4 — Eid Deduplication
- Empty videos.jsonl returns empty set
- Existing eids loaded into set
- Duplicate eids not re-added

### T5 — File Appending
- First append creates file
- Second append preserves existing entries
- Corrupted lines skipped in load

### T6 — HTML Generation (xvideos)
- "衝啊, 弟兄們" tab present with badge count
- `__XV_DATA__` embedded in HTML
- Video data (eid, title, tags) present in JSON
- Tag bar with correct tag buttons
- xv-embed container and data-eid attribute
- xv tab has no search bar (unlike TG tabs)
- xv pagination container present

### T7 — Regression (Telegram)
- All existing TG tabs present
- Search bar and time presets present
- Lightbox HTML present
- Pagination present
- Card structure in JSON valid
- Grouped channels merge correctly
- Media paths include channel_id prefix
- HTML is valid structure (DOCTYPE, html, style, script)

---

## Edge Cases & Error Paths

| Case | Expected | Test |
|------|----------|------|
| Empty xvideos.json | `load_sources()` returns `[]`, crawl prints "No xvideos sources" | Covered |
| Corrupted JSON in videos.jsonl | `load_existing_eids()` skips line | Covered |
| Parse page with no video blocks | Returns `[]` | Covered |
| Single page crawl (pages=1) | Only fetches page 0 | Covered |
| HTML with `data-is-channel` attr | Parser skips non-video attributes | Covered via real xvideos HTML |
| Tag filter with unknown tag | No cards shown | JS logic covered in prototype |

---

## Integration Points

| Integration | Verified | How |
|-------------|----------|-----|
| xv_spider → videos.jsonl | Yes | TestAppendVideos |
| videos.jsonl → generate_html | Yes | TestXvHtml creates videos.jsonl then calls generate() |
| generate_html → `__XV_DATA__` | Yes | TestXvHtml.test_xv_data_content |
| CSS → JS interaction | Yes | CSS selectors (`.tag-btn`, `.xv-expand`, `.page-btn`) verified by HTML structure tests |

---

## Regression Test Scope

All files unchanged except `generate_html.py` additions:

- `tg_core.py`: No code changes, all state/load/save functions tested — **12 tests pass**
- `test_filename.py`: **29 tests pass**
- `test_media.py`: No new media tests, existing **7 tests pass**
- `test_state.py`: **17 tests pass**
- Existing Telegram HTML rendering: **13 tests pass**

---

## Test Execution

```
python -m unittest discover tests -v
Ran 90 tests in 0.456s — OK
```
