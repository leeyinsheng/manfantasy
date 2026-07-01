# 01 - Product Requirements Document (PRD)

## Product Name

**Telegram Channel Media Archiver** (TG-Downloader)

## Elevator Pitch

一個輕量級的命令列工具，自動將指定 Telegram 頻道中的所有媒體內容（圖片、影片、文件）增量下載到本地儲存，支援 macOS / Windows 雙平台排程執行。

## Problem Statement

Telegram 頻道內的媒體檔案沒有官方提供的批次下載功能，使用者若想長期保存頻道內容，只能手動逐條下載，效率極低且容易遺漏。

## Target Users

- 需要備份 Telegram 頻道媒體內容的一般使用者
- 單一使用者，單一頻道場景（非多租戶）

## Core Features (Functional Requirements)

| ID | Feature | Description |
|----|---------|-------------|
| F1 | Telegram 登入 | 透過 Telegram API 以使用者帳號登入，支援 session 持久化，首次使用後不需重複驗證 |
| F2 | 頻道媒體擷取 | 從指定頻道拉取最新 N 條訊息（預設 50），過濾出含有媒體的訊息 |
| F3 | 圖片下載 | 自動下載訊息中的圖片，以「時間戳_photo_訊息ID.jpg」命名 |
| F4 | 影片下載 | 自動下載訊息中的影片文件，優先使用原始檔名，以「時間戳_media_訊息ID.mp4」為備用 |
| F5 | 其他文件下載 | 支援下載非圖片/影片的文檔，依 MIME 類型智能分類存放目錄 |
| F6 | 增量下載 | 基於本地狀態檔（`.downloaded_state.json`）記錄已下載訊息 ID，每次僅下載新內容 |
| F7 | 自動分類儲存 | 圖片 → `download/photo/`，影片 → `download/video/`，其他文件按類型歸類 |
| F8 | 排程執行 | 提供 macOS shell 腳本和 Windows PowerShell 腳本，可配合 cron / 工作排程器定時觸發 |
| F9 | 日誌記錄 | 將執行輸出和錯誤寫入 `download/download.log`，方便排查問題 |

## Non-Functional Requirements

| ID | Requirement | Detail |
|----|-------------|--------|
| NF1 | 跨平台 | 支援 macOS 和 Windows 雙平台 |
| NF2 | 無狀態斷點續傳 | 即使中途失敗，下次執行從上次成功處繼續 |
| NF3 | 最小依賴 | 僅依賴 Python 3 + Telethon 套件 |
| NF4 | 憑證安全 | API 憑證存放在使用者家目錄的 JSON 設定檔，不提交到程式碼倉庫 |
| NF5 | 輕量級 | 非服務型應用，作為一次性腳本執行後即退出 |

## User Flow

```
首次使用:
  1. 申請 Telegram API 憑證 (api_id, api_hash)
  2. 建立 ~/.tg_downloader_config.json 設定檔
  3. 手動執行腳本完成首次 Telegram 登入驗證（輸入手機號碼 + 驗證碼）

日常使用:
  1. 排程工具定時觸發 run_downloader.sh / run_downloader.ps1
  2. 腳本自動連接 Telegram，拉取最新訊息
  3. 比較本地狀態檔，僅下載新媒體
  4. 依類型分類存放到對應目錄
  5. 更新狀態檔，輸出執行日誌
```

## Architecture Overview

```
run_downloader.{sh,ps1}     ← 排程觸發入口
        │
        ▼
download_tg_channel.py      ← 核心邏輯
        │
        ├── Telethon ──── Telegram API ──── 指定頻道
        │
        ├── ~/.tg_downloader_config.json     ← API 憑證
        │
        └── download/
            ├── photo/                       ← 圖片輸出
            ├── video/                       ← 影片輸出
            ├── .downloaded_state.json       ← 增量狀態
            └── download.log                 ← 執行日誌
```

## Out of Scope

- 不支援多頻道同時下載
- 不提供 GUI 介面
- 不做訊息文字內容備份（僅媒體檔案）
- 不支援 Telegram Bot 模式（僅使用者帳號模式）
- 不支援 Docker 部署
- 不做雲端同步 / 上傳

## Success Metrics

- 每次執行下載成功率 ≥ 95%
- 重複執行無檔案重複下載
- 無需人工介入即可排程自動運轉
