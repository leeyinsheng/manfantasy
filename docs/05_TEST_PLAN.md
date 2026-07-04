# 05 - Test Plan v7

Derived from `docs/02_DESIGN.md` and the Phase 3 implementation in `src/generate_html.py` / `tests/test_html.py`.

## Functional (covered by `tests/test_html.py`, 88 tests total)

- App shell / header / bottom-nav / no-top-tab-bar markup present
- Waterfall column containers + textonly-list container present per tab
- Sentinel present, pagination markup fully removed
- Search panel, search-toggle, time-presets markup present
- Detail sheet + lightbox markup present
- `__DATA__` JSON structure unchanged (id/date/text/channel/media), media paths channel-prefixed
- Channel grouping → merged tab (`mens_fantasy` group name/messages/total)
- Text-only message (empty `media`) round-trips through JSON correctly
- Unmapped channel group falls back to `DEFAULT_ICON`

## Edge Cases / Error Paths (need a real browser — not visible in static-HTML unit tests)

| Case | Why it matters | Method |
|------|-----------------|--------|
| XSS-unsafe characters in post text (`<`, `&`, `"`, `'`) | Card/sheet text is built via string concatenation in JS; must confirm `escHtml`/`escAttr` actually neutralize it at runtime | Browser render + accessibility snapshot |
| Zero-message tab | Phase 4 fix for sentinel getting stuck on "載入更多…" | Browser render |
| Grouped multi-photo message (`grouped_id`) | `_merge_grouped_messages` merge logic is unchanged, but must confirm the merged media list still renders as one waterfall card with correct multi-image badge | Browser render |
| Search with zero matches | Result count + empty waterfall, no stale cards left over from before search | Browser interaction |
| Infinite scroll past first batch | `PAGE_SIZE=20` batching + column balance across batches | Browser render (already spot-checked in Phase 3, re-verified here) |

## Integration Points

- `window.__DATA__` schema is the only contract between Python and JS — unchanged, verified above
- Bottom-nav tab order follows `channels.json` group insertion order — unchanged from v3 behavior
- Media path resolution (`{channel_id}/{subdir}/{filename}`) — untouched, covered by existing `test_media_paths_in_json_start_with_channel_id`

## Regression Scope

- Data layer (`tg_core.py`, `download_tg_channel.py`, `channels.json`) not touched this cycle — covered by pre-existing `test_state.py` (12 tests), `test_media.py` (7 tests), `test_filename.py` (29 tests), all still passing
- `xv_spider.py` / xvideos integration is out of scope (already removed pre-v7) — `test_xv_spider.py` (19 tests) still passing, confirms no accidental interference

## Gate

All unit tests pass **and** all edge cases above execute correctly in a real browser → proceed to Phase 6.
