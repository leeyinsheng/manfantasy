# 01 - PRD v9：多媒體檔案遷移至阿里雲 OSS

## 背景

v7 上線後，Telegram 爬蟲下載的圖片與影片全部存在伺服器本地磁碟，已達到 100% 容量。雖然有 3 天自動清理機制，但隨著頻道數量增加和使用者瀏覽，本地儲存始終是瓶頸。

本輪目標：將媒體檔案的儲存層從本地磁碟遷移到阿里雲 OSS，一勞永逸解決儲存問題。

## 版本變更

v7 → v9。僅改動儲存層和 URL 生成層，不改 UI。

## 目標

1. Telegram 爬蟲下載媒體後，立即上傳到阿里雲 OSS，不長期保留在本地
2. `messages.jsonl` 中 `media[].path` 從本地相對路徑改為完整 OSS URL
3. 前端 HTML 中的 `<img>` / `<video>` 直接引用 OSS URL
4. 不需要 3 天自動清理機制（OSS 低成本，可長期保留）

## 範圍

### In Scope
- `src/tg_core.py`：新增 OSS 上傳函數、OSS URL 構建函數
- `src/download_tg_channel.py`：下載後立即上傳 OSS → 記錄 OSS URL → 清理本地暫存
- `src/generate_html.py`：確認 OSS URL 格式已包含完整路徑，不需額外前綴
- `src/cleanup_old.py`：移除或簡化（OSS 不需定期清理）
- 伺服器端：安裝 `oss2` Python 套件、建立 `/root/.oss_credentials.json`

### Out of Scope
- 不改 UI 或前端互動邏輯
- 不改 Telegram 爬取邏輯（rate limiting、頻道設定）
- 不修改 `messages.jsonl` 的欄位結構（只改 `path`/`thumb` 的值）
- 不遷移 xvideos 資料（xvideos 本身就只儲存 metadata，不儲存影片）

## 技術方案

### OSS URL 格式

檔案在 OSS 上的 key 與目前本地路徑結構一致：
```
{channel_id}/photo/2025-07-01_1234567890.jpg
{channel_id}/video/2025-07-01_1234567890.mp4
{channel_id}/video/.thumb/.thumb_2025-07-01_1234567890.jpg
```

完整 OSS URL：
```
https://dream20260711.oss-ap-southeast-7.aliyuncs.com/{channel_id}/photo/2025-07-01_1234567890.jpg
```

### 上傳流程

```
Telegram API
    │
    v
download_tg_channel.py
    │
    ├── 下載到本地暫存 (/tmp/)
    ├── 上傳到 OSS (oss2 SDK)
    ├── 記錄 OSS URL 到 messages.jsonl
    └── 刪除本地暫存檔案
```

### 認證管理

認證資訊直接寫入 `src/channels.json` 的頂層（與現有 `channels` 陣列同級），不入獨立檔案：
```json
{
  "oss": {
    "endpoint": "https://oss-ap-southeast-7.aliyuncs.com",
    "bucket": "dream20260711",
    "access_key_id": "***",
    "access_key_secret": "***"
  },
  "channels": [...]
}
```

或新增獨立設定檔 `src/oss_config.json`（也入版控）。

### OSS Bucket 設定需求

Phase 3 實作前需確認：
- Bucket ACL 設為 public-read（或對 media 目錄設公開）
- CORS 設定（允許前端跨域請求）

## 部署計畫

1. 在伺服器安裝 `oss2`：`pip install oss2`
2. 建立 `/root/.oss_credentials.json`
3. 清空 `download/` 中所有媒體檔案和 messages.jsonl
4. 更新 `src/` 中的程式碼
5. 手動執行一次下載，確認媒體上傳到 OSS 且前端可載入
6. Cron 自動執行（沿用既有排程 `*/30 * * * *`）

## 成功標準

- [ ] Telegram 下載的圖片和影片成功上傳到 OSS
- [ ] `messages.jsonl` 中 media path 為完整 OSS URL
- [ ] `generate_html.py` 產生的 HTML 中圖片/影片 URL 可正常載入
- [ ] 本地 `download/` 目錄不累積媒體檔案
- [ ] 所有既有單元測試通過（或合理修改）
- [ ] UAT 環境部署驗收通過
