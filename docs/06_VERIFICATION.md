# 06 - Feature Verification v4

## Verification Checklist

### F20 — xvideos Spider
- [x] `src/xvideos.json` loads 4 sources (categories + searches)
- [x] `_build_url` produces correct URLs for both page types
- [x] `_build_url` URL-encodes keyword parameters
- [x] `_parse_video_blocks` extracts all 8 fields from HTML
- [x] `_parse_video_blocks` handles quality (HD/SD/none)
- [x] `_parse_video_blocks` handles views in "k" and "M" formats
- [x] `crawl_source` iterates pages until `pages` limit or no new eids
- [x] Duplicate eids skipped per `load_existing_eids`
- [x] Each video tagged with source tag
- [x] `_append_videos` appends to single `download/xvideos/videos.jsonl`

### F21 — Embed Playback
- [x] xvideos card renders `.card` with `.card-source.xv` (purple dot)
- [x] `.xv-embed` container with `data-eid` present
- [x] `toggleXvEmbed()` creates `<iframe src="embedframe/{eid}">` on expand
- [x] `toggleXvEmbed()` clears innerHTML on collapse
- [x] xv tab has no search bar (`.search-bar` absent)

### F22 — Mixed Tab Display
- [x] "衝啊, 弟兄們" tab appended after existing Telegram tabs
- [x] Badge count reflects total videos
- [x] `__XV_DATA__` separate from `__DATA__`
- [x] Existing Telegram tabs/cards/search/lightbox unchanged
- [x] `referrerpolicy="no-referrer"` on xv thumbnail images

### F23 — Periodic Update
- [x] `crawl()` can be called from cron/script
- [x] `load_existing_eids()` handles empty file (first run)
- [x] Duplicate prevention by eid

### F24 — Tag Filtering
- [x] `.tag-bar` rendered with correct tag buttons + counts
- [x] Tags sorted alphabetically in output
- [x] `filterXvTags()` toggles `.hidden` on non-matching cards
- [x] "全部" button shows all cards
- [x] Tag badges rendered in card headers

---

## Structure Verification

| File | Lines | Purpose | Verified |
|------|-------|---------|----------|
| `src/xvideos.json` | 34 | Source configuration | Correct JSON schema |
| `src/xv_spider.py` | 191 | Crawler + parser | 17 tests pass |
| `src/generate_html.py` | ~811 | HTML generation | 24 tests pass (11 xv + 13 TG) |
| `tests/test_xv_spider.py` | 211 | Spider unit tests | 17 tests pass |
| `tests/test_html.py` | ~344 | HTML integration tests | 24 tests pass |

---

## Final Sanity Check

```
$ python -m unittest discover tests
Ran 89 tests in 0.401s — OK
```

All v4 features verified against PRD and DESIGN specifications.

**Verdict**: Phase 6 — **PASS**. All features implemented as designed, no deviations.
