# 03 - Implementation Summary v4

## Files Changed

| File | Status | Lines |
|------|--------|-------|
| `src/xvideos.json` | **New** | 30 |
| `src/xv_spider.py` | **New** | 170 |
| `src/generate_html.py` | Modified | +120 |
| `tests/test_xv_spider.py` | **New** | 220 |
| `tests/test_html.py` | Modified | +90 |

## What Was Built

### xv_spider.py

Crawls xvideos category and search result pages to extract video metadata.

**Key functions:**
- `load_sources()` — reads `src/xvideos.json`
- `_build_url(source, page)` — constructs category or search URL with pagination
- `_fetch_html(url)` — HTTP GET with User-Agent header
- `_parse_video_blocks(html)` — regex-based HTML parser extracting: `eid`, `video_id`, title, duration, thumbnail, uploader, quality, views
- `crawl_source(source, existing_eids)` — iterates pages, deduplicates by eid, tags each video with source tag
- `_append_videos(videos)` — appends to `download/xvideos/videos.jsonl`
- `crawl()` — main entry, iterates all sources, merges results

**Supports two page types:**
- Category: `/c/{id}?s={sort}`, pagination: `/c/{id}/{N}?s={sort}`
- Search: `/?k={keyword}&sort={sort}`, pagination: `/?k={keyword}&p={N}&sort={sort}`

### generate_html.py (changes)

Added xvideos tab support alongside existing Telegram tabs:

- `_load_xvideos()` — reads `videos.jsonl`, sorts by `fetched_at` descending
- `_build_xv_tag_counts(videos)` — counts videos per tag
- **New CSS**: `.tag-bar`, `.tag-btn`, `.tag-count`, `.card-source.xv`, `.xv-embed`, `.tag-badge`, responsive styles
- **New JS functions**: `toggleXvEmbed()`, `filterXvTags()`, `renderXvCards()`, `renderXvPagination()`
- **Modified JS**: `switchTab()` handles `xvideos` tab, click handler handles tag buttons, xv expand, xv pagination
- **Added to HTML**: "衝啊, 弟兄們" tab with tag filter bar, `__XV_DATA__` embedded JSON

**Design:**
- xvideos tab reuses `.card` class; source indicator uses purple dot via `.card-source.xv::before`
- Embed iframe created on expand, removed on collapse (`innerHTML = ''`)
- Tag bar: click tag → filter cards by `data-tags` attribute

### xvideos.json

Configuration for 4 xvideos sources merged into one tab:

| Source | Type | Tag |
|--------|------|-----|
| Lingerie-83 | category | 內衣絲襪 |
| 日本 | search | 日本 |
| 中國 | search | 中國 |
| Creampie-40 | category | 內射 |

## Test Results

```
Ran 89 tests in 0.456s — OK
```

- 17 new xv_spider tests (URL building, HTML parsing, config, dedup, file I/O)
- 10 new xv_html tests (tab presence, data embedding, tag bar, embed container, existing tabs unaffected)
- 62 existing tests unchanged, all pass

## Architecture

```
src/
├── channels.json          (unchanged)
├── xvideos.json           ★ NEW
├── xv_spider.py           ★ NEW
├── tg_core.py             (unchanged)
├── download_tg_channel.py (unchanged)
└── generate_html.py       ★ MODIFIED

download/
├── {tg channels}/         (unchanged)
├── xvideos/
│   └── videos.jsonl       ★ NEW merged output
└── index.html             ★ includes xvideos tab

tests/
├── test_filename.py       (unchanged)
├── test_media.py          (unchanged)
├── test_state.py          (unchanged)
├── test_html.py           ★ MODIFIED
└── test_xv_spider.py      ★ NEW
```
