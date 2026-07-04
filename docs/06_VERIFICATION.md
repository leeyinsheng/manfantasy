# 06 - Feature Verification v7

## Verification Checklist (against `01_PRD.md` / `02_DESIGN.md`)

### Waterfall Card Layout
- [x] Image posts render as two-column waterfall cards, alternately assigned (`i % 2`), preserving chronological order within each column
- [x] Cover image keeps its natural aspect ratio (no forced crop) — irregular waterfall heights confirmed visually
- [x] Multi-image posts show a "📷 N" badge; single-image posts don't
- [x] Video-covered posts show a play-icon badge
- [x] Text-only posts (no media) render as full-width cards below the waterfall, not forced into the two-column grid

### Mobile-Portrait-Only Layout
- [x] `.app` container is a fixed narrow width, centered
- [x] Verified at 390px (mobile) and 1200px (wide desktop) viewports — identical centered layout at both, no responsive breakpoint changes the structure

### Bottom Navigation
- [x] Bottom nav replaces the old top tab bar (`tab-nav`/`tab-btn` markup fully removed)
- [x] 4 channel-group tabs with icon + label, active tab highlighted in accent color
- [x] Icon lookup falls back to a default icon for any unmapped channel group

### Search & Time Filter
- [x] Collapsible per-tab search panel, toggled by a single header search icon
- [x] Icon's active/highlighted state stays in sync with the currently active tab's panel state when switching tabs (fixed during Phase 3 browser testing)
- [x] Keyword + time-range presets (今日/近3日/近7日/本月/近半年) filter across the tab's **entire** dataset, not just the currently loaded batch
- [x] Result count displayed; clearing the search restores the normal infinite-scroll view

### Detail Sheet + Lightbox
- [x] Tapping an image/video card opens a bottom sheet with full text + all thumbnails
- [x] Tapping a thumbnail opens the lightbox (image or video), with prev/next, counter, Escape/Arrow-key navigation, and click-outside-to-close — reused from v3 with no loss of functionality
- [x] Tapping a text-only card expands/collapses inline instead (no sheet, since there's nothing to view)

### Infinite Scroll
- [x] Pagination markup (`pagination`, `page-btn`) fully removed
- [x] `IntersectionObserver` on a per-tab sentinel loads the next batch (`PAGE_SIZE=20`) as the user scrolls
- [x] Empty tab shows "已無更多內容" immediately (Phase 4 fix verified)

### Data Layer (Unchanged, Out of Scope)
- [x] `__DATA__` JSON schema unchanged (`id`/`date`/`text`/`channel`/`media`)
- [x] Grouped multi-photo messages (`grouped_id`) still merge into a single card with the correct image count
- [x] Media path channel-id prefixing unaffected
- [x] Telegram data layer (`tg_core.py`, `download_tg_channel.py`, `channels.json`) untouched

### Security (found during Phase 5, fixed)
- [x] `</script>` sequences in channel post text can no longer break out of the inline `__DATA__` script block — verified with a live XSS payload before and after the fix

## Final Sanity Check

```
$ python3 -m unittest discover tests
Ran 88 tests in 0.079s — OK
```

All v7 features verified against the PRD and DESIGN specifications, including edge cases beyond what
static-HTML unit tests can cover (verified interactively via Playwright against a real generated page).

**Verdict**: Phase 6 — **PASS**. Ready for Phase 7 (User Acceptance).
