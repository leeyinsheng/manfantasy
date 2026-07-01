# 04 - Code Review Report (Updated)

## Review Summary

| Metric | Value |
|--------|-------|
| Files reviewed | 6 |
| Tests | 36, all passing |
| Issues found (initial) | 4 (1 medium, 3 low) |
| Issues resolved | 4/4 |

---

## Resolved Issues

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | Medium | 未知媒體類型靜默跳過 | `download_tg_channel.py:103` — 加入 `else: print("[SKIP] ...")` |
| 2 | Low | JSON 損毀時無例外處理 | `tg_core.py:13-14` — `try/except json.JSONDecodeError` |
| 3 | Low | macOS 腳本寫死 HOME | `run_downloader.sh:2` — 改用 `$HOME` 環境變數 |
| 4 | Low | classify_media 雙 True 無防禦 | `tg_core.py:62` — `raise ValueError` |

## Updated Test Coverage

| Test File | New Tests | Reason |
|-----------|-----------|--------|
| `test_media.py` | `test_both_photo_and_document_raises_error` | Verify Issue #4 fix |
| `test_state.py` | `test_returns_empty_dict_on_corrupted_json` | Verify Issue #2 fix (config) |
| `test_state.py` | `test_returns_empty_set_on_corrupted_json` | Verify Issue #2 fix (state) |
| `test_state.py` | `test_returns_empty_set_on_non_list_json` | Verify defensive type check |

## Verdict

**APPROVED** — all 4 issues resolved, 36/36 tests pass, no regressions.
