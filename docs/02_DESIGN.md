# 02 - 設計文件 v3

## 版本變更摘要

v2 → v3 核心變動：平行下載、頻道合併顯示、四個新 UI 元件。

| 模組 | 狀態 | 說明 |
|------|------|------|
| `tg_core.py` | 不變 | 無需修改 |
| `download_tg_channel.py` | 重構 | 多頻道 `asyncio.gather()` 平行處理 |
| `generate_html.py` | 重構 | 新增燈箱/搜尋/分頁/合併邏輯，依 `design_20260702.html` 原型 |
| `channels.json` | 擴充 | 新增 `group` 欄位，擴充至 4 頻道 |

**原型參考：** `docs/prototype/design_20260702.html`

---

## 1. 系統架構 v3

```
┌──────────────────────────────────────────────────────┐
│                    排程層                              │
│       cron / 工作排程器                                  │
│            │                                           │
│            ▼                                           │
│     run_downloader.sh / .ps1                            │
│            │                                           │
│            ▼                                           │
│     download_tg_channel.py                              │
│            │                                           │
│     ┌──────┼──────┬──────┐                             │
│     ▼      ▼      ▼      ▼                             │
│  AIguoman ciyuanb llcosfc dashijian                    │
│  (text)  (text)  (text)  (text)                        │
│     │      │      │      │                             │
│     └──────┴──────┘      │   ← asyncio.gather() 平行    │
│            │             │                             │
│     group: mens_fantasy  │                             │
│            │             │                             │
│            ▼             ▼                             │
│     generate_html.py                                   │
│            │                                           │
│     ┌──────┴──────┐                                    │
│     ▼             ▼                                    │
│  合併頁籤      獨立頁籤                                  │
│  "男人的幻想"  "東南亞大事件"                             │
│     │             │                                    │
│     └──────┬──────┘                                    │
│            ▼                                           │
│     download/index.html                                │
│     (燈箱 + 搜尋 + 分頁 + 懶加載)                        │
└──────────────────────────────────────────────────────┘
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
  ├─ header (Adult Dream + 更新時間)
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

### 7.2 搜尋列 (Search Bar)

```html
<div class="search-bar">
  <input type="text" placeholder="搜尋訊息…">
  <div class="date-group">
    <label>從</label> <input type="date">
    <label>至</label> <input type="date">
  </div>
  <span class="result-count">12 筆結果</span>
</div>
```

| 特性 | 規格 |
|------|------|
| 佈局 | flexbox，`gap: 0.5rem` |
| 背景 | `--surface` + border |
| 搜尋框 | `flex: 1`，聚焦時邊框變 `--accent` |
| 日期群組 | 水平排列，手機版標籤隱藏 |
| 結果計數 | `margin-left: auto` 靠右對齊 |
| 搜尋時 | 結果計數顯示「N 筆結果」，隱藏載入按鈕 |

### 7.3 訊息卡片 (Card)

```html
<div class="card">
  <div class="card-header">
    <span class="card-source">AIguoman18</span>
    <span class="card-date">2026-06-28 14:30</span>
  </div>
  <div class="card-text">訊息內文...</div>
  <div class="card-media">
    <img src="" alt="" loading="lazy">
    <!-- 或影片 -->
    <video preload="none" src="" muted playsinline>
    <div class="vid-overlay"></div>
  </div>
</div>
```

| 特性 | 規格 |
|------|------|
| 背景 | `--surface` + border |
| hover | 邊框變亮 |
| card-header | `display: flex; justify-content: space-between` |
| card-source | `::before` 紅點 + 灰底圓角標籤 |
| card-date | 襯線字體 `--font-display` |
| 影片覆蓋層 | `.vid-overlay` — 半透明圓形 + CSS 三角形播放圖示 |

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
