# 06 - Feature Verification

## Verification Method

由於本產品為 CLI 工具（無 Web UI），無法使用瀏覽器／截圖驗證。改以 PRD 功能需求逐條對照程式碼實作進行靜態驗證。

---

## Functional Requirements Verification

| ID | Requirement | Implementation | Status |
|----|-------------|---------------|--------|
| F1 | Telegram 登入（session 持久化） | `download_tg_channel.py:31` — `TelegramClient` with `.tg_downloader_session` | ✅ PASS |
| F2 | 頻道媒體擷取（最新 50 筆） | `download_tg_channel.py:54` — `iter_messages(entity, limit=FETCH_LIMIT)` | ✅ PASS |
| F3 | 圖片下載（`{date}_photo_{id}.jpg`） | `tg_core.py:28-30` — `generate_photo_filename()`, `download_tg_channel.py:69-80` | ✅ PASS |
| F4 | 影片下載（優先原始檔名、備用命名） | `tg_core.py:52-57` — `generate_document_filename()`, `tg_core.py:33-37` — `get_original_filename()` | ✅ PASS |
| F5 | 其他文件下載（依 MIME 分類） | `tg_core.py:40-45` — `mime_to_extension()`, `download_tg_channel.py:98` — label logic | ✅ PASS |
| F6 | 增量下載（`.downloaded_state.json`） | `tg_core.py:17-25` — `load_state()` / `save_state()`, `download_tg_channel.py:51,65` | ✅ PASS |
| F7 | 自動分類儲存（photo/ video/） | `tg_core.py:48-49` — `is_video_mime()`, `download_tg_channel.py:86` — target_dir | ✅ PASS |
| F8 | 排程執行（macOS sh + Windows ps1） | `src/run_downloader.sh`, `src/run_downloader.ps1` | ✅ PASS |
| F9 | 日誌記錄（`download/download.log`） | Both runner scripts redirect output to log | ✅ PASS |

## Non-Functional Requirements Verification

| ID | Requirement | Implementation | Status |
|----|-------------|---------------|--------|
| NF1 | 跨平台（macOS + Windows） | `run_downloader.sh` (bash/cron) + `run_downloader.ps1` (PowerShell/Task Scheduler) | ✅ PASS |
| NF2 | 無狀態斷點續傳 | `save_state()` called per-file after success; `load_state()` at start | ✅ PASS |
| NF3 | 最小依賴（Python 3 + Telethon） | Only `telethon` external dependency; stdlib-only `tg_core.py` | ✅ PASS |
| NF4 | 憑證安全（JSON 在 repo 外） | `~/.tg_downloader_config.json` stored in `Path.home()`, excluded via `.gitignore` | ✅ PASS |
| NF5 | 輕量級（腳本執行後即退出） | `main()` is async, runs and exits; no daemon, no server | ✅ PASS |

## Out of Scope Verification

| Scope Item | Verdict |
|------------|---------|
| 多頻道支援 | 未實作 — 符合 PRD |
| GUI 介面 | 未實作 — 符合 PRD |
| 文字訊息備份 | 未實作（`message.media` 為 None 時跳過）— 符合 PRD |
| Bot 模式 | 使用使用者帳號登入 — 符合 PRD |
| Docker 部署 | 未提供 — 符合 PRD |
| 雲端同步 | 僅本地儲存 — 符合 PRD |

## Test Verification (Last Run)

```
Ran 32 tests in 0.020s — OK
```

## File Inventory

| File | Purpose | Lines |
|------|---------|-------|
| `src/tg_core.py` | Pure logic: naming, MIME, state, config | 71 |
| `src/download_tg_channel.py` | Main flow with Telethon | 108 |
| `src/run_downloader.sh` | macOS cron entry | 9 |
| `src/run_downloader.ps1` | Windows Task Scheduler entry | 7 |
| `tests/test_filename.py` | Tests: filename + MIME | 132 |
| `tests/test_media.py` | Tests: media classification | 56 |
| `tests/test_state.py` | Tests: config + state I/O | 101 |

## Verification Summary

| Category | Result |
|----------|--------|
| F1-F9 Functional | 9/9 PASS |
| NF1-NF5 Non-functional | 5/5 PASS |
| Out of scope constraints | All respected |
| Unit tests | 32/32 PASS |
| Known issues (from QA) | 3 low-severity, documented in `05_QA_REPORT.md` |

**Overall: ALL REQUIREMENTS VERIFIED PASS**
