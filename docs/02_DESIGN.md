# 02 - 設計文件 v4

## 版本變更摘要

v3 → v4 核心變動：新增 xvideos 影片來源，以 metadata 目錄 + embed iframe 播放模式整合。

| 模組 | 狀態 | 說明 |
|------|------|------|
| `tg_core.py` | 不變 | 無需修改 |
| `download_tg_channel.py` | 不變 | 無需修改 |
| `generate_html.py` | 擴充 | 新增 xvideos 頁籤與 embed 卡片渲染 |
| `channels.json` | 不變 | 無需修改 |
| `xv_spider.py` | **新增** | xvideos 類別/搜尋頁爬蟲 |
| `xvideos.json` | **新增** | xvideos 來源設定檔 |

**原型參考：** `docs/prototype/design.html`

---

## 1. 系統架構 v4

```
┌──────────────────────────────────────────────────────────────┐
│                       排程層                                   │
│          cron / 工作排程器                                       │
│               │                                                │
│               ▼                                                │
│        run_downloader.sh / .ps1                                 │
│               │                                                │
│     ┌─────────┴──────────┐                                    │
│     ▼                    ▼                                    │
│  download_tg_channel  xv_spider.py                             │
│  (Telegram)            (xvideos HTML 爬蟲)                      │
│     │                    │                                     │
│     │  Telegram 頻道     │  xvideos 類別/搜尋                    │
│     │                    │                                     │
│     ▼                    ▼                                     │
│  download/{ch}/       download/xvideos/{src}/                  │
│  messages.jsonl        videos.jsonl                            │
│     │                    │                                     │
│     └─────────┬──────────┘                                    │
│               ▼                                                │
│        generate_html.py                                         │
│               │                                                │
│     ┌─────────┼──────────┬──────────┬──────────┐              │
│     ▼         ▼          ▼          ▼          ▼              │
│  Telegram   Telegram   xvideos    xvideos    xvideos          │
│  頁籤       頁籤       頁籤        頁籤        頁籤             │
│  (既有)     (既有)     (new)      (new)      (new)            │
│     │         │          │          │          │              │
│     └─────────┴──────────┴──────────┴──────────┘              │
│                         │                                      │
│                         ▼                                      │
│                  download/index.html                            │
│            (Telegram 卡片 + xvideos embed 卡片)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 視覺設計系統

依 `design_20260702.html` 原型定義。

### 2.1 色彩

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#0a0a0a` | 頁面背景 |
| `--surface` | `#161616` | 卡片、搜尋列背景 |
| `--surface-2` | `#1e1e1e` | 次要表面（輸入框、載入按鈕） |
| `--fg` | `#e5e5e5` | 主要文字 |
| `--fg-secondary` | `#a0a0a0` | 次要文字 |
| `--muted` | `#6a6a6a` | 禁用/輔助文字 |
| `--border` | `#2a2a2a` | 邊框 |
| `--accent` | `#d14334` | 主色調（紅色） |
| `--accent-hover` | `#e05545` | hover 加深 |
| `--accent-bg` | `rgba(209,67,52,0.08)` | 主色淡化背景 |

### 2.2 字體

| Token | 值 | 用途 |
|-------|-----|------|
| `--font-display` | `'Iowan Old Style', 'Charter', Georgia, serif` | 標題、日期、計數器 |
| `--font-body` | `-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif` | 內文、介面元件 |

### 2.3 基礎尺寸

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius` | `8px` | 圓角 |
| `--max-w` | `840px` | 內容最大寬度 |
| `html font-size` | `clamp(14px, 1vw + 10px, 17px)` | 流體字級 |

---

## 3. 頻道組態設計 v3

### 3.1 設定檔（`src/channels.json`）

```json
{
  "channels": [
    {
      "id": "ai_guoman",
      "username": "AIguoman18",
      "name": "男人的幻想",
      "mode": "text",
      "group": "mens_fantasy",
      "fetch_limit": 50
    },
    {
      "id": "ciyuanb",
      "username": "ciyuanb",
      "name": "男人的幻想",
      "mode": "text",
      "group": "mens_fantasy",
      "fetch_limit": 50
    },
    {
      "id": "llcosfc",
      "username": "llcosfc",
      "name": "男人的幻想",
      "mode": "text",
      "group": "mens_fantasy",
      "fetch_limit": 50
    },
    {
      "id": "dashijian",
      "username": "dashijian",
      "name": "東南亞大事件",
      "mode": "text",
      "fetch_limit": 50
    }
  ]
}
```

| 欄位 | 用途 | v3 變更 |
|------|------|---------|
| `id` | 內部識別碼 | 不變 |
| `username` | Telegram 頻道 username | 不變 |
| `name` | 顯示名稱 | 不變 |
| `mode` | `"media"` / `"text"` | AIguoman18: media → text |
| `group` | **新增**。相同 group 合併為單一頁籤 | 無 group = 獨立頁籤 |
| `fetch_limit` | 每次拉取訊息上限 | 不變 |

---

## 4. 平行下載設計

### 4.1 並行策略

```
download_tg_channel.py::main()
  │
  ├─ 建立 TelegramClient（單一連線，多路複用）
  ├─ 載入頻道清單
  ├─ asyncio.gather(*tasks, return_exceptions=True)
  │   ├─ task_1: process_channel(ai_guoman, client)
  │   ├─ task_2: process_channel(ciyuanb, client)
  │   ├─ task_3: process_channel(llcosfc, client)
  │   └─ task_4: process_channel(dashijian, client)
  │
  ├─ 檢查例外：單一頻道失敗不影響其他
  └─ 觸發 generate_html.generate()
```

### 4.2 競爭條件分析

| 資源 | 是否共享 | 風險 |
|------|----------|------|
| 頻道狀態檔 | 各頻道獨立 | 無 |
| 訊息記錄檔 | 各頻道獨立 | 無 |
| 媒體下載目錄 | 各頻道獨立 | 無 |
| TelegramClient | 共享 | Telethon 內建連線池管理 |

### 4.3 錯誤處理

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
for channel, result in zip(channels, results):
    if isinstance(result, Exception):
        print(f"頻道 {channel['name']} 錯誤: {result}")
```

---

## 5. 頻道合併顯示設計

### 5.1 合併邏輯

`_build_channel_data()` 依 `group` 欄位合併同組頻道：

```python
def _build_channel_data():
    channels = tg_core.load_channels()
    groups = {}
    standalone = []

    for ch in channels:
        grp = ch.get("group")
        if grp:
            groups.setdefault(grp, []).append(ch)
        else:
            standalone.append(ch)

    tabs = []
    for grp_name, members in groups.items():
        merged = {
            "id": grp_name,
            "name": members[0]["name"],
            "mode": "text",
            "messages": [],
            "photos": [],
            "videos": [],
        }
        for m in members:
            merged["messages"].extend(tg_core.load_messages(m["id"]))
            merged["photos"].extend(_scan_media_files(m["id"], "photo"))
            merged["videos"].extend(_scan_media_files(m["id"], "video"))
        merged["messages"].sort(key=lambda x: x.get("id", 0), reverse=True)
        tabs.append(merged)

    for ch in standalone:
        tabs.append({...})  # 原有邏輯

    return tabs
```

### 5.2 訊息卡片來源標註

卡片 header 左右對齊：左側頻道來源（紅點 + username），右側日期。

```html
<div class="card">
  <div class="card-header">
    <span class="card-source">AIguoman18</span>
    <span class="card-date">2026-06-28 14:30</span>
  </div>
  <div class="card-text">訊息內文...</div>
  <div class="card-media">...</div>
</div>
```

**來源標記樣式：**
```css
.card-source::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
}
```

---

## 6. HTML 生成架構

### 6.1 渲染策略

依原型採用 **JS 端動態渲染**，而非 v2 的伺服器端 HTML 生成：

```
generate_html.py
  │
  ├─ 產生頁面骨架（header / tabs / 空白 tab-content）
  ├─ 內嵌 JSON 資料：messages + media 陣列
  ├─ 內嵌 CSS（依原型色系與字體）
  └─ 內嵌 JS（renderCards / 燈箱 / 搜尋 / 分頁）
```

**伺服器端僅輸出：**
- `<!DOCTYPE html>` 結構
- `<style>` 完整 CSS
- 頁籤按鈕 + 空白內容容器
- 搜尋列 HTML（每個文字頁籤）
- 燈箱骨架
- `<script>window.__DATA__ = {...}</script>`
- `<script>` 完整 JS

### 6.2 網頁結構

```
index.html
  ├─ header (Man's Fantasy + 更新時間)
  ├─ nav.tab-nav (sticky)
  │   ├─ [男人的幻想 65]    ← badge 顯示訊息總數
  │   └─ [東南亞大事件 35]
  ├─ main
  │   ├─ #tab-mens_fantasy
  │   │   ├─ .search-bar (搜尋輸入 + 日期範圍 + 結果計數)
  │   │   ├─ .cards-container (JS 渲染)
  │   │   └─ .load-more-wrap (載入按鈕)
  │   └─ #tab-dashijian
  │       ├─ .search-bar
  │       ├─ .cards-container (JS 渲染)
  │       └─ .load-more-wrap
  └─ #lightbox (燈箱骨架)
```

### 6.3 內嵌資料格式

```javascript
window.__DATA__ = {
  tabs: {
    mens_fantasy: {
      name: "男人的幻想",
      messages: [ /* 合併後依時間排序 */ ],
      total: 65
    },
    dashijian: {
      name: "東南亞大事件",
      messages: [ /* 獨立頻道訊息 */ ],
      total: 35
    }
  },
  channels: { /* username → name 對照 */ },
  updated: "2026-07-02 14:30"
};
```

---

## 7. UI 元件設計

### 7.1 頁籤 (Tab)

```html
<nav class="tab-nav" role="tablist">
  <button class="tab-btn active" data-tab="mens_fantasy">
    男人的幻想 <span class="badge">65</span>
  </button>
  <button class="tab-btn" data-tab="dashijian">
    東南亞大事件 <span class="badge">35</span>
  </button>
</nav>
```

| 特性 | 規格 |
|------|------|
| 定位 | `position: sticky; top: 0` |
| 寬度 | `flex: 1` 均分 |
| 作用中指示 | `::after` 偽元素 2px 紅線 |
| badge | 灰底圓角，顯示該頁籤訊息總數 |

### 7.2 搜尋列 (Search Bar) v3.1

```html
<div class="search-bar">
  <input type="text" placeholder="搜尋訊息…">
  <div class="time-presets">
    <button class="preset-btn active">全部</button>
    <button class="preset-btn">今日</button>
    <button class="preset-btn">近3日</button>
    <button class="preset-btn">近7日</button>
    <button class="preset-btn">本月</button>
    <button class="preset-btn">近半年</button>
  </div>
  <span class="result-count">12 筆結果</span>
</div>
```

| 特性 | 規格 |
|------|------|
| 佈局 | flexbox，`gap: 0.5rem`，手機直排 |
| 搜尋框 | `flex: 1`，聚焦時邊框變 `--accent` |
| 時間快捷 | 6 個預設按鈕：全部/今日/近3日/近7日/本月/近半年 |
| 作用中 | 已選取按鈕高亮 |
| 結果計數 | `margin-left: auto` 靠右對齊 |
| 搜尋時 | 計數顯示「N 筆結果」，隱藏載入按鈕 |

### 7.3 訊息卡片 (Card) v3.1

每張卡片代表一條 TG 貼文。文字超過 3 行截斷，媒體以縮圖網格顯示。點擊卡片展開完整內容。

```html
<div class="card" data-expanded="false">
  <div class="card-header">
    <span class="card-source">AIguoman18</span>
    <span class="card-date">2026-06-28 14:30</span>
  </div>
  <div class="card-text">訊息內文截斷至3行，超過則顯示「...」</div>
  <div class="card-thumbs">
    <div class="thumb"><img src="..." loading="lazy"></div>
    <div class="thumb"><img src="..." loading="lazy"></div>
    <div class="thumb video"><img src="thumb.jpg"><div class="vid-icon"></div></div>
  </div>
  <div class="card-expand">展開詳情 ▾</div>
</div>
```

**展開後（點擊卡片）：**
```html
<div class="card" data-expanded="true">
  <div class="card-header">...</div>
  <div class="card-text full">完整訊息內文，不限行數</div>
  <div class="card-thumbs expanded">
    <!-- 所有媒體以較大縮圖顯示 -->
  </div>
  <div class="card-expand">收合 ▴</div>
</div>
```

| 特性 | 規格 |
|------|------|
| 文字截斷 | 未展開時 `line-clamp: 3`（3行），超出顯示省略 |
| 縮圖網格 | `.card-thumbs` 以 grid 排列，每張 80×80px |
| 影片標記 | 影片縮圖上覆蓋 ▶ 播放圖示 |
| 點擊展開 | 點擊卡片（非媒體區域）切換展開/收合 |
| 展開後 | 文字不限行，縮圖尺寸變大（120px），全覽 |
| 媒體點擊 | 點擊縮圖 → 開啟燈箱 |
| 卡片間距 | `margin-bottom: 0.75rem` |

### 7.4 燈箱 (Lightbox)
```html
<div class="lightbox" id="lightbox" role="dialog">
  <span class="lb-close">&times;</span>
  <span class="lb-prev">&lsaquo;</span>
  <span class="lb-next">&rsaquo;</span>
  <div class="lb-content"></div>
  <span class="lb-counter">2 / 15</span>
</div>
```

| 特性 | 規格 |
|------|------|
| 開啟 | `.open` class → `display: flex` |
| 關閉 | 點擊 ✕ / 背景 / ESC |
| 導航 | ‹ › 箭頭 / ← → 鍵 |
| 按鈕樣式 | 半透明白底圓形，hover 加深 |
| 計數器 | `--font-display`，底部置中 |
| JS 資料 | `lbState = { tabId, items[], current }` |
| 內容生成 | `showLightboxItem()` 動態插入 `<img>` 或 `<video>` |

### 7.5 分頁載入 (Load More)

```html
<div class="load-more-wrap">
  <button class="load-more-btn">載入更多 (15)</button>
</div>
```

| 特性 | 規格 |
|------|------|
| 每頁筆數 | `PAGE_SIZE = 50` |
| 初始 | `renderCards(tabId, PAGE_SIZE)` |
| 展開 | 重新呼叫 `renderCards(tabId, rendered + PAGE_SIZE)` |
| 完成 | `.done` class → 文字變「已全部載入」 |
| 搜尋時 | 隱藏整個 `.load-more-wrap` |

### 7.6 媒體效能

| 媒體 | 屬性 | 效果 |
|------|------|------|
| `<img>` | `loading="lazy"` | 瀏覽器僅載入可視範圍 |
| `<video>` | `preload="none"` | 不預載 |

---

## 8. 文字回溯擷取設計 (F19)

AIguoman18 從 v2 `mode: "media"` 切換為 `mode: "text"`。回溯擷取文字但不下載已存在媒體。

**方案：`backfill` 設定 + 檔案存在檢查**

```json
{
  "id": "ai_guoman",
  "backfill": true
}
```

- `backfill: true` 時：重新遍歷歷史訊息，`filepath.exists()` → 跳過下載，僅寫入 `messages.jsonl`
- 下載狀態檔不變
- 回溯完成後可將 `backfill` 改為 `false` 或移除

---

## 9. 關鍵設計取捨

| 決策 | 理由 |
|------|------|
| JS 端動態渲染卡片（非 Python 端 HTML） | 分頁、搜尋、合併邏輯在 JS 端更靈活，renderCards 可直接操控 DOM |
| 內嵌 JSON 資料（非 fetch） | `file://` 協定不支援 fetch，靜態 HTML 必須內嵌 |
| 紅色主調 `#d14334` | 用戶原型設計選擇，更強烈的視覺識別 |
| 襯線展示體 + 無襯線內文體 | 編輯感排版，區分標題性與功能性文字 |
| sticky 頁籤 | 長頁面捲動時頁籤不消失，切換更方便 |
| badge 訊息計數 | 頁籤上直接可見各頻道內容量 |
| group 欄位 | 向後相容 v2 設定檔 |
| backfill 而非重置狀態 | 不重複下載已有媒體，只補文字 |
| 純 HTML/CSS/JS 無外部依賴 | 雙擊即開，零安裝 |

---

## 10. xvideos 資料模型

### 10.1 來源設定檔（`src/xvideos.json`）

4 個來源合併為單一頁籤「衝啊, 弟兄們」，每個來源的影片掛上對應標籤。

```json
{
  "sources": [
    { "type": "category", "id": "Lingerie-83",  "tag": "內衣絲襪", "sort": "uploaddate", "pages": 5 },
    { "type": "search",   "id": "日本",          "keyword": "日本", "tag": "日本",   "sort": "uploaddate", "pages": 5 },
    { "type": "search",   "id": "中國",          "keyword": "中國", "tag": "中國",   "sort": "uploaddate", "pages": 5 },
    { "type": "category", "id": "Creampie-40",   "tag": "內射",    "sort": "uploaddate", "pages": 5 }
  ]
}
```

| 欄位 | 用途 |
|------|------|
| `type` | `"category"` = `/c/{id}`，`"search"` = `/?k={keyword}` |
| `id` | 類別 ID 或搜尋唯一識別名 |
| `keyword` | 僅 `search` 需要 |
| `tag` | 影片掛上的標籤名稱 |
| `sort` | 固定 `uploaddate`，最新在上 |
| `pages` | 每次爬取頁數 |

### 10.2 影片記錄格式（`videos.jsonl`）

4 個來源合併寫入單一檔案，依 `fetched_at` 降冪排序。

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

### 10.3 合併策略

- 4 個來源爬取完成後，合併入單一 `videos.jsonl`
- 相同 `eid`（跨來源重複）只保留首次出現的標籤
- 合併後 `sort(key= fetched_at, reverse=True)`（最新在上）

---

## 11. xvideos Embed 卡片元件（v4 擴充）

### 11.1 設計原則

xvideos 卡片完全復用現有 Telegram `.card` 基礎結構。**單一頁籤**「衝啊, 弟兄們」合併 4 來源，依上傳時間排序（最新在上），上方有標籤篩選列。

- **相同**：`.card` 外框、`.card-header` 左右對齊、`.card-text` 文字區、`.card-thumbs` 縮圖、`.card-expand` 展開按鈕
- **差異**：來源標記紫色圓點（`.card-source.xv`）、展開後內嵌 iframe
- **新增**：`.tag-bar` 標籤篩選列

### 11.2 標籤篩選列

```html
<div class="tag-bar">
  <button class="tag-btn active" data-tag="all">全部 <span class="tag-count">600</span></button>
  <button class="tag-btn" data-tag="內衣絲襪">內衣絲襪 <span class="tag-count">150</span></button>
  <button class="tag-btn" data-tag="日本">日本 <span class="tag-count">150</span></button>
  <button class="tag-btn" data-tag="中國">中國 <span class="tag-count">150</span></button>
  <button class="tag-btn" data-tag="內射">內射 <span class="tag-count">150</span></button>
</div>
```

```css
.tag-bar { display: flex; gap: 6px; margin-bottom: 1rem; flex-wrap: wrap; }
.tag-btn {
  padding: 0.35rem 0.7rem; font-size: 0.78rem;
  color: var(--muted); background: var(--surface-2);
  border: 1px solid var(--border); border-radius: 4px;
  cursor: pointer; transition: all .15s; user-select: none;
}
.tag-btn:hover { color: var(--fg-secondary); border-color: var(--muted); }
.tag-btn.active { color: var(--fg); background: var(--accent-bg); border-color: var(--accent); }
.tag-count { font-size: 0.7rem; color: var(--muted); margin-left: 3px; }
```

**邏輯**：點擊標籤 → 只顯示 `tags` 陣列包含該標籤的卡片；再點「全部」→ 顯示全部。

### 11.3 卡片結構（收合狀態）

```html
<div class="card">
  <div class="card-header">
    <span class="card-source xv">xv · Amoulsolo</span>
    <span class="card-date">48 min · 1080p · 68.1k views</span>
  </div>
  <div class="card-text full">Sexy O2, T&A XRed 392 - Dressed in Corset...</div>
  <div class="card-thumbs">
    <div class="thumb">
      <img src="thumbnail.jpg" loading="lazy" alt="">
      <div class="vid-icon"></div>
    </div>
  </div>
  <div class="xv-embed" id="embed-khluvuo33b8"></div>
  <div class="card-expand" onclick="toggleEmbed(this,'khluvuo33b8')">▶ 播放影片</div>
</div>
```

### 11.4 展開狀態

```html
<div class="card expanded">
  ...同上 header + thumbs...
  <div class="xv-embed">
    <iframe src="https://www.xvideos.com/embedframe/khluvuo33b8"
            allowfullscreen frameborder="0" width="100%" height="420"
            loading="lazy"></iframe>
  </div>
  <div class="card-expand">▲ 收合</div>
</div>
```

### 11.5 CSS 擴充（僅新增，不修改既有樣式）

```css
/* xv source variant — purple dot instead of red */
.card-source.xv::before { background: #a070e0; }

/* embed container */
.xv-embed {
  margin-top: 0.5rem; border-radius: 6px;
  overflow: hidden; background: #000;
}
.xv-embed iframe {
  display: block; border: none; width: 100%;
  min-height: 420px;
}
@media (max-width: 600px) {
  .xv-embed iframe { min-height: 240px; }
}
```

### 11.6 JS 互動（追加）

```javascript
function toggleEmbed(btn, eid) {
  var card = btn.closest('.card');
  var embedDiv = document.getElementById('embed-' + eid);
  if (card.classList.contains('expanded')) {
    embedDiv.innerHTML = '';  // 移除 iframe，釋放資源
    card.classList.remove('expanded');
    btn.textContent = '▶ 播放影片';
  } else {
    embedDiv.innerHTML = '<iframe src="https://www.xvideos.com/embedframe/'
      + eid + '" allowfullscreen frameborder="0" width="100%" height="420"></iframe>';
    card.classList.add('expanded');
    btn.textContent = '▲ 收合';
  }
}
```

---

## 12. 頁籤結構 v4

```
index.html
  ├─ header (Man's Fantasy + 更新時間)
  ├─ nav.tab-nav (sticky, flex)
  │   ├─ [東南亞大事件 {1010}]   ← TG news group
  │   ├─ [吃瓜爆料 {340}]        ← TG guaba_bl
  │   ├─ [AI短劇 {65}]          ← TG ai_drama
  │   ├─ [異想空間 {518}]        ← TG mens_fantasy
  │   └─ [衝啊, 弟兄們 {600}]    ★ xv 合併頁 (4 source merged)
  ├─ main
  │   ├─ #tab-news            (.search-bar + time presets + .cards + .pagination)
  │   ├─ #tab-guaba_bl        (同上)
  │   ├─ #tab-ai_drama        (同上)
  │   ├─ #tab-mens_fantasy    (同上)
  │   └─ #tab-xvideos         (.tag-bar + .cards + .pagination) ★
  └─ #lightbox
```

---

## 13. xvideos 內嵌資料格式（合併單一來源）

```javascript
window.__XV_DATA__ = {
  videos: [
    { eid, title, duration, views, uploader, thumbnail, quality, tags:["內衣絲襪"], fetched_at },
    { eid, title, duration, views, uploader, thumbnail, quality, tags:["日本"],     fetched_at },
    ...
  ],
  total: 600
};
```

依 `fetched_at` 降冪排序（最新在上），JS 端直接渲染，無須額外排序。

---

## 14. v4 設計取捨

| 決策 | 理由 |
|------|------|
| 4 來源合併為單一頁籤 | 用戶要求統一分類，避免頁籤過多 |
| 排序固定 uploaddate 降冪 | 用戶想看最新影片 |
| 標籤來自來源類別（非爬影片頁 tags） | 爬 4 來源共 600 部，逐一爬影片頁成本過高；來源類別名稱即為有效標籤 |
| xv 卡片完全復用 `.card` 結構 | 與 TG 卡片無兩套 CSS，維護成本最低 |
| xv 來源紫色圓點（`.card-source.xv::before`） | 單行 CSS 區分 |
| 收合時 `innerHTML = ''` 移除 iframe | 停止播放、釋放記憶體 |
| 縮圖使用 xvideos CDN URL（不下載） | 零本地儲存 |
| 標籤篩選在前端 JS 實現 | 無後端，純 CSS `.hidden` 切換 |
| 純 HTML/CSS/JS 無外部依賴 | 雙擊即開，零安裝 |
