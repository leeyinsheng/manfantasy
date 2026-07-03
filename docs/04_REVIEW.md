# 04 - Code Review v4

## Scope Check: CLEAN

- **Intent**: Add xvideos embed integration with spider, single tab, tag filtering
- **Delivered**: `xv_spider.py`, `xvideos.json`, updated `generate_html.py`, unit + integration tests (89 pass)
- **Drift**: None. All changes trace to v4 PRD requirements
- **Missing**: None. All PRD features covered (F20-F24)

---

## Review Findings

### Strengths

| Area | Notes |
|------|-------|
| Test coverage | 17 spider + 10 HTML = 27 new tests, all 89 pass |
| Backward compat | Existing Telegram tabs/cards/lightbox untouched; `__XV_DATA__` separate from `__DATA__` |
| CSS extension | xv-specific CSS is additive only (`.xv-embed`, `.tag-bar`, `.card-source.xv`), no existing selectors changed |
| Dedup | `load_existing_eids()` prevents duplicate video entries by eid |
| Regex parsing | `_parse_video_blocks` uses `finditer` for efficient chunk extraction, avoids full-HTML greediness |
| Iframe lifecycle | `toggleXvEmbed()` clears `innerHTML = ''` on collapse, preventing background playback |

### Issues

**ISSUE 1 (Medium) — CSS has duplicate `@media(max-width:600px)` blocks**

`src/generate_html.py:220-225` adds xv-iframes responsive rule before existing `@media(max-width:600px)` block at line 226. Both use the same query. Not a functional bug (CSS cascade handles it), but adds ~5 lines of dead code.

**Recommendation**: Merge both `@media(max-width:600px)` blocks into one.

---

**ISSUE 2 (Low) — `xv_spider.py` uses `urllib` without TLS certificate verification risk**

`urllib.request.urlopen()` on Windows with default context trusts system CA store, which is fine. However, `_fetch_html` does not set a timeout for the connection phase, only for the read phase via `timeout=30`. Slow DNS could hang.

**Recommendation**: Consider wrapping in a connection timeout or adding retry logic. Not blocking for v4.

---

**ISSUE 3 (Low) — `crawl_source()` breaks on first page failure, losing subsequent pages**

```python
try:
    html = _fetch_html(url)
except Exception as e:
    print(f"  [SKIP] {url}: {e}")
    break  # exits entire page loop for this source
```

If page 2 fails with a transient error, pages 3-5 are never fetched. Using `continue` instead of `break` would try remaining pages.

---

**ISSUE 4 (Medium) — `_append_videos` opens/closes file for every source call**

Each source's results are appended in a separate `open()` call. For 4 sources with 5 pages each, that's 4 file opens. Not a correctness issue but could interleave data if called concurrently.

**Recommendation**: Acceptable for sequential single-threaded use. If parallelism is added in v5, use a lock.

---

**ISSUE 5 (Info) — `generate_html.py` uses `_json` (global) for `import json as _json` but `json` is referenced elsewhere**

The file imports `json as _json` at top, then uses `_json.dumps()`, `_json.loads()`, `_json.JSONDecodeError`. All references are consistent. The `json` name is shadowed — any code path using bare `json.` would raise `NameError`. Current code is clean.

---

**ISSUE 6 (Low) — `_build_xv_tag_counts` returns unsorted dict**

Python 3.7+ dicts preserve insertion order, so tag buttons appear in the order videos with those tags were first encountered. This is unpredictable for the user. The `generate()` function calls `sorted(xv_tag_counts.items())` when rendering, so the HTML output is sorted. Fine for now.

---

**ISSUE 7 (Info) — No rate-limiting user-agent rotation in spider**

Single `USER_AGENT` string for all requests. xvideos may eventually rate-limit based on this. Not blocking for v4 (5 pages * 4 sources = 20 requests with 2s delays = harmless).

---

## Summary

| Metric | Value |
|--------|-------|
| New files | 4 (spider, config, 2 test files) |
| Modified files | 2 (generate_html, test_html) |
| New tests | 27 |
| Issues found | 2 Medium, 3 Low, 2 Info |
| Blockers | 0 |

**Verdict**: Phase 4 PASS. No blocking issues. Recommendation: fix ISSUE 1 (duplicate media query) before deployment for cleanliness.

---

*Review completed 2026-07-03*
