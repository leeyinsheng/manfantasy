# 02 - Design Document

## Design Philosophy

**Simplicity over flexibility.** Single-channel, single-user, single-run. No daemon, no web server, no database. The tool is a stateless CLI script that runs, downloads, and exits. Complexity lives only where it prevents data loss: incremental state tracking and error resilience.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────┐
│              Scheduler Layer                 │
│  cron (macOS) / Task Scheduler (Windows)     │
│         │                  │                 │
│         ▼                  ▼                 │
│  run_downloader.sh    run_downloader.ps1     │
│         │                  │                 │
│         └──────┬───────────┘                 │
│                ▼                              │
│     download_tg_channel.py (core)            │
│                │                              │
│     ┌──────────┼──────────┐                   │
│     ▼          ▼          ▼                   │
│  Config    Telethon    State                  │
│  (~/.json)  (API)    (.json)                  │
│                │                              │
│        ┌───────┴───────┐                       │
│        ▼               ▼                       │
│   download/photo/  download/video/             │
└─────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Files |
|-------|---------------|-------|
| Scheduler | OS-level periodic invocation | `run_downloader.sh`, `run_downloader.ps1` |
| Core | API connection, message iteration, media download, state management | `download_tg_channel.py` |
| Config | Credential storage outside repo | `~/.tg_downloader_config.json` |
| State | Incremental download tracking | `download/.downloaded_state.json` |
| Storage | Media file organization | `download/photo/`, `download/video/` |
| Logging | Execution output and error capture | `download/download.log` |

---

## 2. Core Module Design (`download_tg_channel.py`)

### 2.1 Entry Point

```python
if __name__ == "__main__":
    asyncio.run(main())
```

Single async entry. No argument parsing needed -- all configuration is file-based.

### 2.2 Main Flow

```
main()
  │
  ├─ 1. load_config()         → read ~/.tg_downloader_config.json
  ├─ 2. client.connect()      → establish Telegram session
  ├─ 3. is_user_authorized()  → gate: exit if NEEDS_AUTH
  ├─ 4. get_entity(channel)   → resolve channel username
  ├─ 5. load_state()          → read .downloaded_state.json
  ├─ 6. iter_messages()       → loop: fetch up to FETCH_LIMIT messages
  │     ├─ skip: no media
  │     ├─ skip: already downloaded (by message ID)
  │     ├─ skip: id ≤ max_downloaded (early break optimization)
  │     ├─ is_photo → download_photo()
  │     └─ is_document → download_document()
  └─ 7. client.disconnect()
```

### 2.3 Message Processing Decision Tree

```
message.media?
  ├─ None          → skip (text-only message)
  ├─ MessageMediaPhoto
  │   └─ download as: {YYYYMMDD_HHMMSS}_photo_{msg_id}.jpg
  └─ MessageMediaDocument
      ├─ Has original file_name? → use original name
      ├─ No file_name?
      │   ├─ video/* MIME → {date}_media_{id}.mp4
      │   ├─ image/* MIME → {date}_media_{id}.jpg
      │   └─ other       → {date}_media_{id}.bin
      └─ File exists? → append _{msg_id} to stem
```

### 2.4 State Management

```json
// .downloaded_state.json
[1001, 1002, 1003, 1005, 1010]
```

- **Data structure:** Sorted JSON array of downloaded message IDs
- **Persistence:** Saved immediately after each successful download (not batched at end)
- **Rationale:** If the script crashes mid-run, re-download is minimal (at most 1 file)
- **Early break optimization:** `max(downloaded)` compared to incoming message IDs; since Telegram returns messages in descending ID order, once we hit an ID ≤ max_downloaded, all remaining messages are known to be downloaded

### 2.5 File Naming Convention

| Media Type | Pattern | Example |
|-----------|---------|---------|
| Photo | `{date}_photo_{msg_id}.jpg` | `20250201_143022_photo_1234.jpg` |
| Document (named) | `{original_name}` | `my_video.mp4` |
| Document (unnamed, video) | `{date}_media_{msg_id}.mp4` | `20250201_143022_media_1234.mp4` |
| Duplicate filename | `{stem}_{msg_id}{ext}` | `my_video_1234.mp4` |

---

## 3. Configuration Design

### 3.1 Credentials (`~/.tg_downloader_config.json`)

```json
{
  "api_id": 123456,
  "api_hash": "abcdef1234567890abcdef1234567890",
  "phone": "+886912345678"
}
```

**Security design:**
- Stored in `$HOME`, outside the project directory
- Excluded from git via `.gitignore`
- Session file (`~/.tg_downloader_session.session`) created by Telethon, also outside repo

### 3.2 Hardcoded Constants (in-code config)

| Constant | Value | Purpose |
|----------|-------|---------|
| `CHANNEL_USERNAME` | `"AIguoman18"` | Target channel |
| `FETCH_LIMIT` | `50` | Max messages per run |

**Design decision:** Channel username is hardcoded rather than configurable. Rationale: single-channel scope, keeping the tool as a zero-config daemon after initial setup. If multi-channel support is ever needed (explicitly out of scope per PRD), this becomes a config file parameter.

---

## 4. Scheduler Script Design

### 4.1 macOS (`run_downloader.sh`)

```bash
#!/bin/bash
export HOME=/Users/leedavid
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
cd "/Users/leedavid/Documents/Project/Adult Dream"
/usr/bin/python3 src/download_tg_channel.py >> download/download.log 2>&1
```

**Design notes:**
- Explicit `HOME` export: `cron` runs with a minimal environment; Telethon looks for session/config files under `$HOME`
- Explicit `PATH`: ensures `python3` is found even in `cron`'s restricted environment
- Absolute paths: no ambiguity regardless of `cron`'s working directory
- `2>&1` redirect: captures both stdout and stderr to the log

### 4.2 Windows (`run_downloader.ps1`)

```powershell
$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectDir "download\download.log"
$Script = Join-Path $PSScriptRoot "download_tg_channel.py"

Set-Location -LiteralPath $ProjectDir
cmd /c "python `"$Script`" 2>&1" | Out-File -FilePath $LogFile -Append -Encoding utf8
```

**Design notes:**
- `$PSScriptRoot`: PowerShell auto-variable, resolves to script location regardless of working directory
- `cmd /c` wrapper: prevents PowerShell from wrapping stderr output in error record noise (`CategoryInfo`, `FullyQualifiedErrorId`)
- `Out-File -Encoding utf8`: avoids PowerShell's default UTF-16 which produces mojibake
- `-Append`: preserves log history across runs

---

## 5. Error Handling Strategy

| Scenario | Behavior |
|----------|----------|
| Config file missing | `load_config()` returns `{}`; Telethon raises auth error → `"NEEDS_AUTH"` |
| Network failure | Telethon exception → `[ERR]` log, script exits |
| Channel not found | `get_entity()` exception → log and exit |
| Single file download fails | `try/except` per file → `[ERR]` log, **continue** to next message |
| State file corrupted | `load_state()` returns empty set → re-downloads all (safe) |
| File already exists | Append `_msg_id` to filename to avoid collision |

**Key design decision:** Per-file error isolation. A single failed download does not abort the entire run. The state file is only updated on success, so failed downloads are retried next run.

---

## 6. Directory Layout

```
Adult Dream/
├── src/
│   ├── download_tg_channel.py    # Core logic
│   ├── run_downloader.sh         # macOS scheduler entry
│   └── run_downloader.ps1        # Windows scheduler entry
├── download/                     # Runtime data (gitignored)
│   ├── photo/                    # Downloaded photos
│   ├── video/                    # Downloaded videos
│   ├── .downloaded_state.json    # Incremental state
│   └── download.log              # Execution log
├── docs/                         # Workflow documents
├── tests/                        # Test suite
└── .gitignore
```

**Separation principle:** `src/` for code (versioned), `download/` for runtime artifacts (gitignored). No config files in the repo.

---

## 7. Cross-Platform Compatibility

| Concern | macOS | Windows |
|---------|-------|---------|
| Path separator | `/` (native) | `\` handled by `pathlib.Path` |
| Home directory | `/Users/leedavid` | `C:\Users\davidlee` resolved by `Path.home()` |
| Python invocation | `/usr/bin/python3` | `python` (PATH) |
| Scheduler | `cron` | Task Scheduler |
| Log encoding | UTF-8 (native) | UTF-8 via `-Encoding utf8` |
| Line endings | LF | CRLF (git `core.autocrlf`) |

`pathlib.Path` handles all path construction -- no manual string concatenation of paths anywhere in the core module.

---

## 8. Key Design Trade-offs

| Decision | Rationale |
|----------|-----------|
| Hardcoded channel name | Single-purpose tool; YAGNI. If multi-channel is needed, it's a v2 feature. |
| State as sorted JSON array | Human-readable, debuggable with any text editor. Set of 50 ints is trivial. |
| Save state after each file | Prevents data loss on crash. Cost: one extra `write()` per file (negligible). |
| `FETCH_LIMIT=50` | Balances API rate limits with covering gaps. Assumes <50 new media messages between runs. |
| No `pip` requirements file | Single dependency (`telethon`). Not worth the ceremony for one package. |
