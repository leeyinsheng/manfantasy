# 01 - PRD v4：xvideos 影片來源整合

## 版本變更

v3 → v4 核心變動：新增 xvideos 影片來源，以 iframe/embed 播放，零儲存成本。v3 既有 Telegram 功能保持不變。

---

## 核心理念

xvideos 影片量巨大（單一類別即 20,000+ 部），完整下載不切實際。採用 **metadata 目錄 + embed iframe 播放** 模式：

- **爬取**：僅影片 metadata（標題、縮圖、時長、觀看數、eid）
- **播放**：點擊卡片 → `<iframe>` 嵌入 xvideos 官方 embed 頁面 `/embedframe/{VIDEO_EID}`
- **成本**：零影片儲存、零頻寬消耗（僅縮圖約 10KB/張）

---

## 來源清單（v4 初始）

4 個 xvideos 來源合併為 **單一頁籤**「衝啊, 弟兄們」，影片按上傳時間排序（最新在上）。

| # | type | id | 標籤 | URL |
|---|------|-----|------|-----|
| 1 | `category` | `Lingerie-83` | 內衣絲襪 | `/c/Lingerie-83` |
| 2 | `search` | `日本` | 日本 | `/?k=%E6%97%A5%E6%9C%AC&top` |
| 3 | `search` | `中國` | 中國 | `/?k=%E4%B8%AD%E5%9C%8B&top` |
| 4 | `category` | `Creampie-40` | 內射 | `/c/Creampie-40` |

> 每個影片自動掛上對應來源的標籤（如「內衣絲襪」）。用戶可在頁面上點擊標籤篩選。

### URL 規則差異

| 類型 | 範例 URL | 分頁規則 | 排序參數 |
|------|----------|----------|----------|
| `category` | `/c/Lingerie-83` | `/c/Lingerie-83/{N}` | `?s=uploaddate` |
| `search` | `/?k=%E6%97%A5%E6%9C%AC&top` | `/?k=KEYWORD&p={N}` | `&sort=uploaddate` |

> 後續可透過設定檔擴充更多類別或關鍵字搜尋。

---

## 功能需求

### F20 xvideos 爬蟲（支援類別頁 + 關鍵字搜尋頁）

- 爬取指定 xvideos 頁面（類別或搜尋），提取影片清單
- 每部影片蒐集：`data-id`, `data-eid`, 標題, 縮圖 URL, 時長, 觀看數, 上傳者, 畫質標記
- 兩種類型使用相同 HTML 解析邏輯，僅 URL 組合不同
- 支援分頁爬取（每頁約 30 部，預設爬 5 頁 = 150 部）
- 支援排序（最新/最熱門/最多觀看）
- 儲存為 `videos.jsonl`

### F21 Embed 播放整合

- 卡片點擊 → 展開內嵌 `<iframe src="https://www.xvideos.com/embedframe/{eid}">`
- xvideos 官方 embed 頁面自帶完整播放器（240p/360p + HLS）
- 手機/桌機皆可播放
- 不離開當前頁面（inline expand 或燈箱模式）

### F22 混合頁籤展示

- 現有 Telegram 頁籤（異想空間、東南亞大事件、AI短劇、吃瓜爆料）保持不變
- 新增 **1 個** xvideos 頁籤「**衝啊, 弟兄們**」，合併 4 個來源的所有影片
- xvideos 卡片與 Telegram 卡片共用 `.card` 結構，來源標記紫色圓點區分

### F24 標籤篩選

- xvideos 頁籤上方顯示標籤列（內衣絲襪 / 日本 / 中國 / 內射）
- 每個標籤顯示該標籤的影片數量
- 點擊標籤 → 只顯示帶有該標籤的影片（其他卡片隱藏）
- 再點一次 → 取消篩選，顯示全部
- 支援多選（同時點擊多個標籤，顯示 OR 聯集）

### F23 定期更新

- `xv_spider.py` 定時執行（排程/cron），增量爬取新影片
- 重複影片（相同 eid）自動跳過，不重複寫入
- 爬取完自動觸發 `generate_html.py` 重新生成頁面

---

## 設定檔設計（`src/xvideos.json`）

```json
{
  "sources": [
    {
      "type": "category",
      "id": "Lingerie-83",
      "tag": "內衣絲襪",
      "sort": "uploaddate",
      "pages": 5
    },
    {
      "type": "search",
      "id": "日本",
      "keyword": "日本",
      "tag": "日本",
      "sort": "uploaddate",
      "pages": 5
    },
    {
      "type": "search",
      "id": "中國",
      "keyword": "中國",
      "tag": "中國",
      "sort": "uploaddate",
      "pages": 5
    },
    {
      "type": "category",
      "id": "Creampie-40",
      "tag": "內射",
      "sort": "uploaddate",
      "pages": 5
    }
  ]
}
```

| 欄位 | 用途 |
|------|------|
| `type` | `"category"` 或 `"search"` |
| `id` | 類別 ID（如 `Lingerie-83`）或搜尋識別名（如 `日本`） |
| `keyword` | 僅 `search` 類型需要，搜尋關鍵字（URL 編碼由程式處理） |
| `tag` | 影片掛上的標籤名稱（如 `內衣絲襪`） |
| `sort` | 排序方式：`uploaddate`（固定，最新在上） |
| `pages` | 每次爬取頁數 |

---

## 爬蟲邏輯

```
xv_spider.py
  │
  ├─ 讀取 src/xvideos.json 的 4 個 sources
  ├─ for each source:
  │   ├─ 依 type 決定 URL 格式
  │   ├─ 解析 HTML，提取 .frame-block.thumb-block
  │   │   ├─ data-id → video_id
  │   │   ├─ data-eid → encoded_id
  │   │   ├─ .title → title + duration
  │   │   ├─ img data-src → thumbnail
  │   │   ├─ .name → uploader
  │   │   ├─ .video-hd-mark / .video-sd-mark → quality
  │   │   └─ 掛上 source.tag 作為 tags
  │   └─ 比對現有 eid，跳過重複
  │
  ├─ 4 個來源結果全部合併寫入 download/xvideos/videos.jsonl
  ├─ 依 fetched_at 降冪排序（最新在上）
  └─ 觸發 generate_html.py
```

---

## 目錄結構（v4 新增部分）

```
download/
├── ... (既有 Telegram 頻道目錄) ...
├── xvideos/                          ← 新增
│   └── videos.jsonl                 ← 合併 4 來源的影片 metadata
└── index.html
```

---

## 影片卡片資料格式

### videos.jsonl（每行一筆 JSON）

```json
{
  "eid": "khluvuo33b8",
  "video_id": 51923269,
  "title": "Sexy O2, T&A XRed 392 ...",
  "duration": "48 min",
  "views": "68.1k",
  "uploader": "Amoulsolo",
  "thumbnail": "https://thumb-cdn77.xvideos-cdn.com/.../xv_12_t.jpg",
  "quality": "1080p",
  "tags": ["內衣絲襪"],
  "url": "/video.khluvuo33b8/...",
  "fetched_at": "2026-07-03T12:00:00"
}
```

---

## UI 設計方向

xvideos 頁籤「衝啊, 弟兄們」結構：

```
tab: [衝啊, 弟兄們 {600}]

  tag bar:
  [內衣絲襪 150] [日本 150] [中國 150] [內射 150]

  cards: (依上傳時間降冪，最新在上)
  ┌──────────────────────────────────────────┐
  │ ●xv · Amoulsolo    48min · 1080p · 68.1k │
  │ Sexy O2, T&A XRed 392 ...               │
  │ [縮圖 ▶]                                │
  │ ▶ 播放影片                              │
  └──────────────────────────────────────────┘

  pagination: ← 1 2 3 ... 20 →  共 600 部
```

---

## Out of Scope（v4）

- 不下載完整 xvideos 影片檔案
- 不支援 xvideos 會員/付費內容 (RED)
- 不做跨來源合併顯示（Telegram + xvideos 分開頁籤）
- 不爬取 xvideos 頻道頁（`/channels-index`），僅爬類別頁 + 搜尋頁
- 不處理 xvideos 年齡驗證 / 地區限制（使用者自行解決）
- 不支援複合搜尋（多關鍵字、篩選器組合），僅單一關鍵字 + 排序
- 不提供網頁內搜尋 xvideos 功能（使用 xvideos 站內搜尋即可）

---

## 技術風險

| 風險 | 緩解 |
|------|------|
| xvideos 改版 HTML 結構變更 | 爬蟲使用 CSS class 選擇器，定期檢查 |
| embed 頁面被封鎖或修改 | 測試階段已驗證 `/embedframe/` 可用 |
| secure token 過期導致 mp4 無法直接存取 | 不使用直接 mp4 URL，依賴 embed iframe 自身 JS 更新 token |
| IP 被限速/封鎖 | 加入請求延遲（2-3 秒間隔），控制並行數 |
