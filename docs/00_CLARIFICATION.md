# 00 - Clarification v10：xvideo 影片線上播放方案

## 我對目標的理解

目前 v8 xvideo 頁籤只能在點擊後開啟 xvideos 原始頁面（新分頁），不能在本站內播放。你希望在站內燈箱中直接播放 xvideos 影片。

最終結果：點擊 xvideo 卡片 → 燈箱內播放影片（不需離開本站）

## 研究結論

| 方案 | 狀態 |
|------|------|
| iframe embed (`embedframe/{id}`) | ❌ 404，端點已失效 |
| iframe 嵌入 xvideos 原始頁面 | ❌ `X-Frame-Options: SAMEORIGIN`，禁止嵌入 |
| 直接連結新分頁 | ✅ 目前方案，但不算"播放" |

## 可行方案

### 方案 A：下載影片到 OSS，本站直接播放

用 `yt-dlp` 從 xvideos 下載影片 → 上傳 OSS → HTML 中直接引用 OSS 的 mp4 URL → `<video>` 標籤播放。

- ✅ 完全可控，播放體驗最佳
- ✅ OSS 已就緒，儲存不是問題
- ❌ OSS 流量費用（預估：每 1GB 下載約 NT$2-3）
- ❌ 下載耗時（每個影片可能 50-500MB）

### 方案 B：爬取原始 mp4 URL，直接引用播放

從 xvideos 頁面解析出實際影片 URL（通常是 CDN 上的 mp4 或 m3u8），直接作為 `<video src>`。

- ✅ 不需儲存/下載
- ❌ URL 會過期（通常幾小時）
- ❌ 需要動態解析，而非靜態 HTML（需要後端 proxy）
- ❌ xvideos 會輪換 CDN 域名，維護成本高

## 我的假設

1. **方案 A 優先**：下載到 OSS + 本地 `<video>` 播放。OSS 流量費用可接受。

2. **實作方式**：
   - 新增 `src/xv_downloader.py`：用 `yt-dlp` 從 xvideos 下載影片
   - 修改 `xv_spider.py`：爬取 metadata 後，可選下載影片
   - 下載到 `/tmp/`，上傳 OSS，清理暫存
   - `messages.jsonl` 中的 `media.path` 指向 OSS 上的 mp4 URL
   - 前端直接用 `<video src="...oss-url...">` 播放

3. **範圍**：只限 maderotic 頻道，每個影片下載一次。

4. **隱含假設**：你接受 OSS 流量費用。xvideo 內容體積較大（影片 50-500MB），觀看次數多的話流量費用可觀。

## 盲點 / 模糊點

1. **OSS 流量費用是否在預算內？** 一個 200MB 影片被觀看 100 次 = 20GB 流量 ≈ NT$40-60。若每天上千次觀看，費用會可觀。

2. **要不要限制下載數量？** 只下載最新 N 個影片，還是全部 maderotic 影片？

3. **下載後清理策略？** OSS 容量無限且便宜，要保留多久？

4. **yt-dlp 合規性？** xvideos ToS 可能禁止自動下載。風險自負。
