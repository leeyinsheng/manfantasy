# 02 - Design v10：xvideos 影片下載到 OSS

## 架構

```
xv_spider.py (metadata only)
    │  outputs: eid, video_id, title, duration, thumbnail, url
    v
videos.jsonl (每行一筆，含完整 video URL)
    │
    v
xv_downloader.py (每日執行，下載最新 50 部)
    │  yt-dlp → /tmp/ → oss_uploader → OSS
    v
videos.jsonl (更新 media path = OSS mp4 URL)
    │
    v
generate_html.py → index.html
    │  xvideo tab: card with thumbnail, click → <video> lightbox
    v
使用者瀏覽器 <video src="https://dream20260711.oss-ap-southeast-7...">
```

## 檔案變更

### 新增：`src/xv_downloader.py`

```python
def load_videos():         # 讀取 videos.jsonl
def save_videos():         # 寫回 videos.jsonl
def download_video():      # yt-dlp 下載單一影片
def download_pending():    # 遍歷未下載的影片，下載並上傳 OSS
```

下載流程：
1. 讀取 `videos.jsonl`，找出 `media_uploaded != true` 的影片
2. 取最新 50 筆
3. 逐筆 yt-dlp 下載到 `/tmp/xv_{video_id}.mp4`
4. `oss_uploader.upload_media()` 上傳 OSS
5. 更新 record: `media_path = oss_url, media_uploaded = true`
6. 刪除 `/tmp/` 暫存

### 變更：`src/xv_spider.py`

- 改寫 `_parse_video_blocks()`：新增擷取完整 video URL
- 改寫 `_build_url()`：user 型態 URL 改用 `/maderotic`（頁碼從 0 開始）
- 影片記錄新增 `url` 欄位

影片 URL 格式：`https://www.xvideos.com/video.{eid}/{video_id}/0/{title}`

### 變更：`src/generate_html.py`

- `_load_xvideos()`：新增 `media` 陣列（當 `media_uploaded == true` 時）
- `cardXvHtml()`：不變，卡片外觀相同
- 點擊處理：檢查 `media` 是否存在，有的話用 `<video>` 播放，沒有的話用舊邏輯
- `openLbEmbed()`：改為 `openLbVideo(videoUrl)` → `<video src>` 播放

## OSS Key 格式

```
xvideos/{video_id}.mp4
```

完整 OSS URL：
```
https://dream20260711.oss-ap-southeast-7.aliyuncs.com/xvideos/49709194.mp4
```

## videos.jsonl 格式變更

```json
{
  "eid": "oplmapafe9c",
  "video_id": "49709194",
  "title": "video title",
  "duration": "12:34",
  "thumbnail": "https://...",
  "uploader": "maderotic",
  "url": "https://www.xvideos.com/video.oplmapafe9c/49709194/0/title",
  "media_path": "https://dream20260711.oss.../xvideos/49709194.mp4",
  "media_uploaded": true,
  "tags": ["maderotic"],
  "fetched_at": "2026-07-13T..."
}
```

## 排程

- xv_spider：每小時一次（更新 metadata）
- xv_downloader：每天一次（下載最新 50 部到 OSS）
- generate_html：每 30 分鐘一次（與 Telegram 同步）

## What Changes

| 檔案 | 變更 |
|------|------|
| `src/xv_downloader.py` | **新增** — yt-dlp 下載 + OSS 上傳 |
| `src/xv_spider.py` | 修正 URL 格式，新增完整 video URL |
| `src/xvideos.json` | 新增 `download_latest: 50` 設定 |
| `src/generate_html.py` | 燈箱 `<video>` 播放 OSS mp4 |
| `tests/` | 新增 xv_downloader 測試 |
