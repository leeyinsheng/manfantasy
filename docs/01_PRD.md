# 01 - PRD v10：xvideo 影片下載到 OSS 播放

## 背景

v8 xvideo 整合嘗試用 iframe embed 播放 xvideos 影片，但 embedframe 端點已失效且 xvideos 設有 `X-Frame-Options: SAMEORIGIN`，無法嵌入。改用「在 xvideos 觀看」連結（開新分頁），不是真正的播放體驗。

本輪目標：用 yt-dlp 從 xvideos 下載影片 → 上傳 OSS → 站內 `<video>` 播放。

## 版本變更

v9 → v10。在既有 xvideo tab 基礎上，改進播放方式。

## 目標

1. xvideo 卡片點擊後，在燈箱中以 `<video>` 標籤直接播放影片
2. 影片儲存在 OSS（與 Telegram 媒體相同 bucket）
3. 不下載全部影片，只下載最新 N 個（節省流量）
4. 下載後記錄在 videos.jsonl 中，重複爬取時跳過已下載

## 範圍

### In Scope
- `src/xv_downloader.py` — **新增**：用 yt-dlp 下載 xvideos 影片，上傳 OSS
- `src/xv_spider.py` — 爬取 metadata 時記錄完整 video URL（含 eid/slug），供下載器使用
- `src/generate_html.py` — xvideo 卡片點擊改為 `<video>` 播放 OSS 上的 mp4
- `src/xvideos.json` — 新增下載設定（latest N，下載開關）

### Out of Scope
- 不修改 Telegram 下載邏輯
- 不修改 OSS 上傳模組（沿用 oss_uploader.py）
- 不下載歷史影片（只下載新爬取的）

## 技術方案

### 下載流程

```
xv_spider.py (爬取 metadata + video URL)
    │
    v
xv_videos.jsonl (含 video_id, title, url, thumbnail)
    │
    v
xv_downloader.py (逐筆處理)
    │
    ├── yt-dlp 下載影片到 /tmp/
    ├── 上傳到 OSS (xvideos/{video_id}.mp4)
    ├── 記錄 OSS URL 到 videos.jsonl
    └── 清理 /tmp/
    │
    v
generate_html.py (讀取 videos.jsonl)
    │
    ├── media.path = OSS mp4 URL
    └── cardImageHtml → <video src="oss_url"> 播放
```

### 播放方式

點擊 xvideo 卡片 → 燈箱以 `<video src="..." controls autoplay>` 播放：

```html
<video src="https://dream20260711.oss-ap-southeast-7.aliyuncs.com/xvideos/49709194.mp4"
       controls autoplay style="max-width:92vw;max-height:85vh">
</video>
```

### yt-dlp 命令

```bash
yt-dlp -f best -o /tmp/xv_{video_id}.mp4 "https://www.xvideos.com/video.{eid}/{video_id}/0/{slug}"
```

## 成功標準

- [ ] yt-dlp 成功從 xvideos 下載影片
- [ ] 影片上傳 OSS 成功
- [ ] 點擊 xvideo 卡片 → 燈箱內 `<video>` 播放
- [ ] 所有測試通過
- [ ] UAT 部署驗收通過
