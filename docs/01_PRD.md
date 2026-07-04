# 01 - PRD v8：xvideos 頻道整合 — 嵌入式播放

## 背景

目前網站內容全部來自 Telegram 頻道，透過 `download_tg_channel.py` 下載訊息與媒體後，由 `generate_html.py` 產生靜態 HTML。使用者要求新增 xvideos 影片內容，但直接下載影片到本機伺服器會產生大量儲存與頻寬成本。

xvideos 提供 iframe embed 功能，可以在不儲存影片檔案的情況下，直接在網站內嵌播放。

## 版本變更

v7 → v8。僅新增功能，不修改既有架構。

## 目標

1. **新增「xvideo」類別頁籤**：在底部導覽列新增一個 xvideo 分頁，展示來自 xvideos 的影片。
2. **不儲存影片檔案**：透過 xvideos iframe embed 播放，不用下載影片到伺服器。
3. **與現有 UI 一致**：卡片使用 waterfall 雙欄佈局，點擊播放時以燈箱嵌入 xvideos 播放器。
4. **僅爬取 metadata**：抓取影片標題、縮圖、時長、影片 ID，不下載實際影片內容。

## 範圍

### In Scope
- `src/xv_spider.py`：新增對 xvideos 頻道/使用者頁面 URL 的支援（`/maderotic` 格式）
- `src/xvideos.json`：加入 `maderotic` 新來源
- `src/generate_html.py`：
  - 載入 `download/xvideos/videos.jsonl` 資料
  - 新增 `xvideo` tab（包含在底部導覽、資料嵌入、卡片渲染）
  - 燈箱影片播放改為支援 xvideos iframe embed
- `tests/test_xv_spider.py`：新增對應的單元測試
- 圖示：為 xvideo tab 選用適當 emoji（如 🔞 或 🎥）

### Out of Scope
- 不下載 xvideos 影片檔案到 `download/`
- 不修改既有 Telegram 頻道的下載與顯示邏輯
- 不修改 `channels.json`（xvideos 是獨立資料源）
- 不處理反爬蟲機制（若被阻擋，使用者自行處理 proxy）

## 技術方案

### 資料流

```
xv_spider.py (爬取 metadata)
       │
       v
download/xvideos/videos.jsonl (每行一筆影片資料)
       │
       v
generate_html.py (讀取 xvideos 資料，嵌入 window.__DATA__)
       │
       v
download/index.html (客戶端渲染卡片 + iframe embed)
```

### xvideos 影片 Embed

xvideos 提供 embed 格式：
```
https://www.xvideos.com/embedframe/{video_id}
```

使用 `<iframe>` 嵌入燈箱播放：
```html
<iframe src="https://www.xvideos.com/embedframe/{video_id}"
        frameborder="0" scrolling="no"
        allowfullscreen="allowfullscreen"
        width="100%" height="100%">
</iframe>
```

資料格式（每筆影片）：
```json
{
  "source": "maderotic",
  "eid": "unique-id",
  "video_id": "12345678",
  "title": "影片標題",
  "duration": "12:34",
  "thumbnail": "https://img-thumbnail-url.jpg",
  "uploader": "maderotic",
  "quality": "HD"
}
```

### 爬蟲策略

- `xv_spider.py` 現已支援 category 與 search 兩種 URL 模式，需新增 `user/channel` 模式
- channel URL：`https://www.xvideos.com/{username}`
- 分頁：`https://www.xvideos.com/{username}/videos/{page}`
- 請求間隔：每次請求延遲 2-3 秒，避免被 ban

### 排程

xvideos 資料不需即時更新。建議：
- 手動執行 `python3 src/xv_spider.py` 更新
- 或與 Telegram 爬蟲分離，不加入 cron `*/30 * * * *`

## 分頁設計

底部導覽新增頁籤：

| Tab | 圖示 | 內容來源 |
|-----|------|---------|
| 異想空間 | 🏠 | Telegram mens_fantasy |
| 東南亞大事件 | 📰 | Telegram news |
| 吃瓜爆料 | 🔥 | Telegram guaba_bl |
| AI短劇 | 🎬 | Telegram ai_drama |
| **xvideo** | **🔞** | **xvideos.com/maderotic** |

## 成功標準

- [ ] `python3 src/xv_spider.py` 成功爬取 xvideos.com/maderotic 的影片列表
- [ ] `download/xvideos/videos.jsonl` 包含有效的影片 metadata
- [ ] `python3 src/generate_html.py` 成功產生包含 xvideo tab 的 index.html
- [ ] 底部導覽列顯示 xvideo 頁籤，點擊可切換
- [ ] xvideo 頁籤以 waterfall 雙欄顯示影片卡片（縮圖 + 標題 + 時長）
- [ ] 點擊影片卡片 → 燈箱以 iframe 嵌入播放 xvideos 影片
- [ ] 所有既有功能無回歸問題
- [ ] 所有單元測試通過（`python3 -m unittest discover tests`）

## 風險

| 風險 | 影響 | 緩解方式 |
|------|------|---------|
| xvideos 封鎖爬蟲 | 無法取得影片列表 | 增加請求間隔、輪換 User-Agent；引導使用者手動更新 |
| xvideos embed 被封鎖（X-Frame-Options） | 影片無法內嵌播放 | 備案：點擊後開新分頁連到 xvideos 原始頁面 |
| xvideos HTML 結構變更 | 爬蟲解析失敗 | 模組化 parser 函數，減少變更時的修復成本 |
| 版權或合規問題 | 法律風險 | 僅嵌入播放，不下載儲存；使用者自行確認合規性 |
