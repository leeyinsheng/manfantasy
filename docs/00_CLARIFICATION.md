# 00 - Clarification v9：多媒體檔案遷移至 OSS

## 我對目標的理解

目前從 Telegram 下載的圖片與影片全部存在伺服器本地磁碟（`/opt/adult-dream/download/`），已經遇過磁碟滿載（99G/99G）且需要手動清理的問題。你希望把媒體檔案搬到 OSS（物件儲存服務），徹底解決儲存空間問題。

最終結果：
- Telegram 爬蟲下載檔案後，上傳到 OSS，不長期存放在伺服器本地
- 前端 HTML 中的圖片/影片 URL 指向 OSS（而非本地相對路徑）
- 不需要 3 天自動清理機制（OSS 儲存成本低，可長期保留）

## 我的假設

1. **OSS 提供商**：阿里雲 OSS ✅ 已確認

2. **連線資訊（已確認）**：
   - Endpoint: `https://oss-ap-southeast-7.aliyuncs.com`
   - Bucket: `dream20260711`
   - Region: `ap-southeast-7`
   - 公開 URL: `https://dream20260711.oss-ap-southeast-7.aliyuncs.com/`

3. **公開讀取**：OSS bucket 設為公開讀取（public-read），前端直接用 `<img src="https://dream20260711.oss-ap-southeast-7.aliyuncs.com/...">` 載入，不經由伺服器轉發。

4. **儲存路徑不變**：OSS 上的目錄結構與目前本地一致：`{channel_id}/photo/filename.jpg`、`{channel_id}/video/filename.mp4`。messages.jsonl 中的 path 格式改為完整 OSS URL。

5. **上傳流程**：Telegram 下載到本地暫存 → 立即上傳 OSS → 記錄 OSS URL 到 messages.jsonl → 清理本地暫存。

6. **縮圖**：影片縮圖一同上傳 OSS，保持現有 `.thumb/` 目錄結構。

7. **現有檔案處理**：清空現有媒體，之後重新下載的才上傳 OSS ✅ 已確認

9. **Python SDK**：使用阿里雲官方 `oss2` 套件。認證資訊將存放在 `src/oss_config.json`，納入版控。

10. **Bucket 公開讀取**：需要確保 bucket 讀取權限設為 public-read（或對特定目錄設為 public），否則前端圖片無法載入。若尚未設定，Phase 3 實作時提醒你設定。

11. **CORS**：若 bucket 需要 CORS 設定（瀏覽器跨域請求），Phase 3 時一併處理。

## 確認狀態

| 項目 | 狀態 |
|------|------|
| OSS 提供商 | ✅ 阿里雲 OSS |
| Endpoint / Bucket / Region | ✅ 已提供 |
| AccessKey | ✅ 已提供 |
| 現有檔案處理 | ✅ 清空重新開始 |
| 優先順序 | ✅ OSS 遷移優先於 xvideo |
| 確認開始 | ⏳ 等你說「確認」或「進 phase 1」 |
