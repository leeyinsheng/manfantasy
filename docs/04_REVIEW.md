# 04 - Code Review Report

## Review Summary

| Metric | Value |
|--------|-------|
| Files reviewed | 6 (`tg_core.py`, `download_tg_channel.py`, 3 test files, `run_downloader.sh`) |
| Tests | 32, all passing |
| Issues found | 4 (1 medium, 3 low) |
| Verdict | **APPROVED with recommendations** |

---

## Issue 1 (Medium): Unknown media types silently skipped

**File:** `src/download_tg_channel.py:67-68`

```python
media_type, _ = classify_media(is_photo, is_document, mime_type)

if media_type == "photo":
    ...
elif media_type == "document":
    ...
# no elif media_type == "unknown": — silently dropped
```

When Telegram introduces a new media type (e.g. `MessageMediaPoll`, `MessageMediaDice`), `classify_media()` returns `("unknown", None)`. The main loop has no handler for this — the message is silently skipped with no log entry. User has no way to know media was missed.

**Recommendation:** Add an `else` branch that logs skipped messages:

```python
else:
    print(f"  [SKIP] 未知媒體類型 msg#{message.id}")
```

---

## Issue 2 (Low): No JSON error handling in config/state loaders

**File:** `src/tg_core.py:11-14, 17-20`

```python
def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}
```

If `~/.tg_downloader_config.json` exists but contains malformed JSON (e.g., truncated by a crash), `json.JSONDecodeError` crashes the script with an unhelpful traceback instead of a clear error message.

**Recommendation:** Wrap in try/except:

```python
def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            print(f"[ERR] 設定檔格式錯誤: {CONFIG_FILE}")
            return {}
    return {}
```

Same pattern applies to `load_state()`.

---

## Issue 3 (Low): Hardcoded HOME path in macOS script

**File:** `src/run_downloader.sh:2`

```bash
export HOME=/Users/leedavid
```

This path is specific to one macOS user. On any other machine, `cron` will not find the Telethon session file.

**Recommendation:** Use `$HOME` from the environment or compute it:

```bash
export HOME="${HOME:-/Users/leedavid}"
```

---

## Issue 4 (Low): `classify_media` double-true case undefined

**File:** `src/tg_core.py:60-65`

```python
def classify_media(is_photo, is_document, mime_type=""):
    if is_photo:
        return ("photo", None)
```

If both `is_photo=True` and `is_document=True` (should never happen with current Telegram API, but defensive coding pays off), the function silently returns `"photo"`. No assertion or warning.

**Recommendation:** Add an early assertion or return a warning:

```python
def classify_media(is_photo, is_document, mime_type=""):
    if is_photo and is_document:
        raise ValueError("Media cannot be both photo and document")
```

---

## Code Quality Observations

| Aspect | Assessment |
|--------|-----------|
| Module separation (`tg_core.py` / `download_tg_channel.py`) | Clean. Pure logic is testable without Telethon import. |
| Function naming | Descriptive and consistent (`generate_photo_filename`, `is_video_mime`). |
| Test coverage | 32 tests covering all pure functions. Edge cases for filename generation, MIME mapping, and state I/O are well covered. |
| Error isolation | Per-file try/except in the download loop ensures one failure doesn't block the rest. |
| No type hints | Missing on all functions. Low priority for a personal tool but would improve IDE support. |
| Test design | Uses `tempfile` for I/O tests and `setUp/tearDown` to restore module constants. Clean. |

## Missing Test Coverage

| Scenario | Priority |
|----------|----------|
| Corrupted JSON in `load_config` / `load_state` | Low |
| `classify_media(is_photo=True, is_document=True)` ambiguous case | Low |
| `load_state` with non-list JSON root (e.g., `{"ids": [1,2,3]}`) | Low |

---

## Scope Drift Check

**Intent:** Refactor existing code for testability + add unit tests.

**Delivered:** Extracted 10 pure functions to `tg_core.py`, rewrote main flow to use them, added 32 unit tests covering all extracted functions. No additional features added.

**Verdict:** CLEAN — no scope drift detected.

---

## Review Verdict

**APPROVED** — 32 tests pass, code is clean and well-structured. The 4 issues noted are all low severity, with one medium (silent skip of unknown media). Recommended to fix Issue 1 before production use.
