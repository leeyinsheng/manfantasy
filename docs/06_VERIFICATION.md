# 06 - Feature Verification v8

## Verification Summary

| Check | Result |
|-------|--------|
| `generate_html.py` runs without error | PASS |
| 5 tabs in generated HTML | PASS (news, guaba_bl, ai_drama, mens_fantasy, xvideo) |
| ❌ icon in xvideo nav tab | PASS |
| `openLbEmbed` JS function present | PASS |
| `xv-embed` CSS class present | PASS |
| `badge-duration` CSS class present | PASS |
| `data-xv` attribute rendering logic in JS | PASS |
| UAT server accessible (http://8.213.209.231/dream/) | PASS (HTTP 200) |

## Notes

- xvideo tab shows 0 messages on local build (no `xvideos.jsonl` data yet)
- `xv_spider.py` must be run on server to populate `download/xvideos/videos.jsonl` before xvideo tab shows content
- All 102 tests pass at unit level

## Deployment Notes (for Phase 7)

1. Run `python3 src/xv_spider.py` on server to scrape initial batch
2. Copy updated `src/generate_html.py`, `src/xv_spider.py`, `src/xvideos.json` to server
3. Run `python3 src/generate_html.py` to regenerate HTML with xvideo data
4. Cron continues auto-regeneration (`*/30 * * * *`)
