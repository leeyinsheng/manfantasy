# 02 - 設計文件

## 設計理念

**簡潔優先於彈性。** 單一頻道、單一使用者、單次執行。沒有常駐服務、沒有網頁伺服器、沒有資料庫。此工具是一個無狀態的 CLI 腳本，執行、下載、結束。複雜度只存在於防止資料遺失的機制中：增量狀態追蹤和錯誤恢復能力。

---

## 1. 系統架構

```
┌─────────────────────────────────────────────┐
│               排程層                         │
│  cron (macOS) / 工作排程器 (Windows)         │
│         │                  │                 │
│         ▼                  ▼                 │
│  run_downloader.sh    run_downloader.ps1     │
│         │                  │                 │
│         └──────┬───────────┘                 │
│                ▼                              │
│     download_tg_channel.py（核心）           │
│                │                              │
│     ┌──────────┼──────────┐                   │
│     ▼          ▼          ▼                   │
│  設定檔     Telethon    狀態檔               │
│  (~/.json)  (API)      (.json)               │
│                │                              │
│        ┌───────┴───────┐                       │
│        ▼               ▼                       │
│   download/photo/  download/video/             │
└─────────────────────────────────────────────┘
```

### 各層職責

| 層級 | 職責 | 檔案 |
|------|------|------|
| 排程層 | 作業系統層級的定時觸發 | `run_downloader.sh`、`run_downloader.ps1` |
| 核心層 | API 連線、訊息迭代、媒體下載、狀態管理 | `download_tg_channel.py` |
| 設定層 | 將憑證存放於程式碼倉庫之外 | `~/.tg_downloader_config.json` |
| 狀態層 | 增量下載追蹤 | `download/.downloaded_state.json` |
| 儲存層 | 媒體檔案分類整理 | `download/photo/`、`download/video/` |
| 日誌層 | 執行輸出與錯誤擷取 | `download/download.log` |

---

## 2. 核心模組設計（`download_tg_channel.py`）

### 2.1 進入點

```python
if __name__ == "__main__":
    asyncio.run(main())
```

單一非同步進入點。無需命令列參數解析，所有組態皆以檔案為基礎。

### 2.2 主流程

```
main()
  │
  ├─ 1. load_config()         → 讀取 ~/.tg_downloader_config.json
  ├─ 2. client.connect()      → 建立 Telegram 連線階段（session）
  ├─ 3. is_user_authorized()  → 閘門：若未授權則輸出 NEEDS_AUTH 並離開
  ├─ 4. get_entity(channel)   → 解析頻道使用者名稱
  ├─ 5. load_state()          → 讀取 .downloaded_state.json
  ├─ 6. iter_messages()       → 迴圈：拉取最多 FETCH_LIMIT 筆訊息
  │     ├─ 跳過：無媒體
  │     ├─ 跳過：已下載（依訊息 ID 判斷）
  │     ├─ 跳過：id ≤ max_downloaded（提早中斷最佳化）
  │     ├─ 是圖片 → download_photo()
  │     └─ 是文件 → download_document()
  └─ 7. client.disconnect()
```

### 2.3 訊息處理決策樹

```
message.media？
  ├─ None               → 跳過（純文字訊息）
  ├─ MessageMediaPhoto
  │   └─ 下載為：{YYYYMMDD_HHMMSS}_photo_{訊息ID}.jpg
  └─ MessageMediaDocument
      ├─ 有原始檔名？ → 使用原始檔名
      ├─ 無檔名？
      │   ├─ video/* MIME → {日期}_media_{ID}.mp4
      │   ├─ image/* MIME → {日期}_media_{ID}.jpg
      │   └─ 其他         → {日期}_media_{ID}.bin
      └─ 檔案已存在？ → 在檔名主幹後附加 _{訊息ID}
```

### 2.4 狀態管理

```json
// .downloaded_state.json
[1001, 1002, 1003, 1005, 1010]
```

- **資料結構：** 已排序的 JSON 陣列，存放已下載的訊息 ID
- **持久化時機：** 每次下載成功後立即寫入（非批次結束時才寫入）
- **設計理由：** 若腳本執行中途崩潰，重新下載的範圍極小（最多 1 個檔案）
- **提早中斷最佳化：** 將 `max(downloaded)` 與接收到的訊息 ID 比對；因為 Telegram 回傳訊息時是依 ID 降冪排列，一旦遇到 ID ≤ max_downloaded，後續所有訊息即已知已下載完畢

### 2.5 檔案命名規範

| 媒體類型 | 命名模式 | 範例 |
|----------|----------|------|
| 圖片 | `{日期}_photo_{訊息ID}.jpg` | `20250201_143022_photo_1234.jpg` |
| 文件（有原始檔名） | `{原始檔名}` | `my_video.mp4` |
| 文件（無檔名，影片） | `{日期}_media_{訊息ID}.mp4` | `20250201_143022_media_1234.mp4` |
| 檔名重複時 | `{主幹}_{訊息ID}{副檔名}` | `my_video_1234.mp4` |

---

## 3. 組態設計

### 3.1 憑證設定（`~/.tg_downloader_config.json`）

```json
{
  "api_id": 123456,
  "api_hash": "abcdef1234567890abcdef1234567890",
  "phone": "+886912345678"
}
```

**安全性設計：**
- 存放於 `$HOME`（使用者家目錄），位於專案目錄之外
- 透過 `.gitignore` 排除於 git 追蹤之外
- 連線階段檔（`~/.tg_downloader_session.session`）由 Telethon 自動建立，同樣位於程式碼倉庫之外

### 3.2 寫死的常數（程式碼內組態）

| 常數 | 值 | 用途 |
|------|-----|------|
| `CHANNEL_USERNAME` | `"AIguoman18"` | 目標頻道 |
| `FETCH_LIMIT` | `50` | 每次執行最多處理的訊息數 |

**設計決策：** 頻道名稱寫死在程式碼中，而非可設定。理由：此為單一頻道用途，完成初始設定後即為零組態的常駐工具。若未來需要多頻道支援（PRD 已明確排除於本次範圍），此參數將改為設定檔參數。

---

## 4. 排程腳本設計

### 4.1 macOS（`run_downloader.sh`）

```bash
#!/bin/bash
export HOME=/Users/leedavid
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
cd "/Users/leedavid/Documents/Project/Adult Dream"
/usr/bin/python3 src/download_tg_channel.py >> download/download.log 2>&1
```

**設計說明：**
- 明確匯出 `HOME`：`cron` 執行時環境變數極少，Telethon 需要在 `$HOME` 下尋找連線階段檔和設定檔
- 明確指定 `PATH`：確保在 `cron` 受限環境中仍能找到 `python3`
- 絕對路徑：無論 `cron` 的工作目錄為何都不會有歧義
- `2>&1` 重定向：將 stdout 和 stderr 同時擷取到日誌檔

### 4.2 Windows（`run_downloader.ps1`）

```powershell
$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectDir "download\download.log"
$Script = Join-Path $PSScriptRoot "download_tg_channel.py"

Set-Location -LiteralPath $ProjectDir
cmd /c "python `"$Script`" 2>&1" | Out-File -FilePath $LogFile -Append -Encoding utf8
```

**設計說明：**
- `$PSScriptRoot`：PowerShell 自動變數，無論當前工作目錄為何，都能解析為腳本所在目錄
- `cmd /c` 包裝：防止 PowerShell 將 stderr 輸出包裝成錯誤記錄雜訊（如 `CategoryInfo`、`FullyQualifiedErrorId`）
- `Out-File -Encoding utf8`：避免 PowerShell 預設的 UTF-16 編碼產生日誌亂碼
- `-Append`：保留跨次執行的日誌歷史

---

## 5. 錯誤處理策略

| 情境 | 處理方式 |
|------|----------|
| 設定檔不存在 | `load_config()` 回傳空 `{}`；Telethon 拋出認證錯誤 → `"NEEDS_AUTH"` |
| 網路中斷 | Telethon 例外 → `[ERR]` 記錄，腳本結束 |
| 頻道不存在 | `get_entity()` 例外 → 記錄並結束 |
| 單一檔案下載失敗 | 每個檔案獨立的 `try/except` → `[ERR]` 記錄，**繼續**處理下一則訊息 |
| 狀態檔損毀 | `load_state()` 回傳空集合 → 全部重新下載（安全的退化行為） |
| 檔案已存在 | 在檔名後附加 `_訊息ID` 以避免衝突 |

**關鍵設計決策：** 每個檔案獨立隔離錯誤。單一下載失敗不會中止整次執行。狀態檔僅在下載成功後才更新，因此失敗的下載會在下次執行時重新嘗試。

---

## 6. 目錄佈局

```
Adult Dream/
├── src/
│   ├── download_tg_channel.py    # 核心邏輯
│   ├── run_downloader.sh         # macOS 排程進入點
│   └── run_downloader.ps1        # Windows 排程進入點
├── download/                     # 執行期資料（gitignore 排除）
│   ├── photo/                    # 已下載圖片
│   ├── video/                    # 已下載影片
│   ├── .downloaded_state.json    # 增量狀態
│   └── download.log              # 執行日誌
├── docs/                         # 工作流程文件
├── tests/                        # 測試套件
└── .gitignore
```

**分離原則：** `src/` 存放程式碼（受版本控管），`download/` 存放執行期產物（gitignore 排除）。程式碼倉庫中不存放任何設定檔。

---

## 7. 跨平台相容性

| 關注點 | macOS | Windows |
|--------|-------|---------|
| 路徑分隔符 | `/`（原生） | `\`，由 `pathlib.Path` 處理 |
| 家目錄 | `/Users/leedavid` | `C:\Users\davidlee`，由 `Path.home()` 解析 |
| Python 呼叫方式 | `/usr/bin/python3` | `python`（透過 PATH） |
| 排程工具 | `cron` | 工作排程器 |
| 日誌編碼 | UTF-8（原生） | UTF-8，透過 `-Encoding utf8` |
| 換行符號 | LF | CRLF（git `core.autocrlf`） |

`pathlib.Path` 處理所有路徑建構，核心模組中沒有任何手動字串拼接路徑的程式碼。

---

## 8. 關鍵設計取捨

| 決策 | 理由 |
|------|------|
| 頻道名稱寫死在程式碼中 | 單一用途工具，遵循 YAGNI 原則。若需要多頻道支援，留待 v2 處理。 |
| 狀態以排序 JSON 陣列存放 | 人類可讀，用任何文字編輯器都能除錯。50 個整數的集合微不足道。 |
| 每個檔案下載後立即儲存狀態 | 防止崩潰時資料遺失。成本：每個檔案多一次 `write()`（可忽略不計）。 |
| `FETCH_LIMIT=50` | 在 API 速率限制和涵蓋缺口之間取得平衡。假設兩次執行之間的新媒體訊息少於 50 則。 |
| 不使用 `requirements.txt` | 單一依賴（`telethon`）。不值得為一個套件增加額外的儀式。 |
