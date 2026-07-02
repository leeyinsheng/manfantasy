# 02 - 設計文件 v3

## 版本變更摘要

v2 → v3 核心變動：平行下載、頻道合併顯示、四個新 UI 元件。

| 模組 | 狀態 | 說明 |
|------|------|------|
| `tg_core.py` | 不變 | 無需修改 |
| `download_tg_channel.py` | 重構 | 多頻道 `asyncio.gather()` 平行處理 |
| `generate_html.py` | 重構 | 新增燈箱/搜尋/分頁/合併邏輯 |
| `channels.json` | 擴充 | 新增 `group` 欄位，擴充至 4 頻道 |

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

## 2. 頻道組態設計 v3

### 2.1 設定檔（`src/channels.json`）

新增 `group` 欄位，表示頻道所屬的合併群組。

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

## 3. 平行下載設計

### 3.1 並行策略

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

### 3.2 競爭條件分析

| 資源 | 是否共享 | 風險 |
|------|----------|------|
| 頻道狀態檔 (`.downloaded_state.json`) | 各頻道獨立 | 無 |
| 訊息記錄檔 (`messages.jsonl`) | 各頻道獨立 | 無 |
| 媒體下載目錄 | 各頻道獨立 | 無 |
| TelegramClient | 共享 | Telethon 內建連線池管理 |

**結論：** 各頻道完全隔離，無競爭條件。

### 3.3 錯誤處理

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
for channel, result in zip(channels, results):
    if isinstance(result, Exception):
        print(f"頻道 {channel['name']} 錯誤: {result}")
```

單一頻道連線失敗、被踢出、被ban — 其他頻道正常繼續。

---

## 4. 頻道合併顯示設計

### 4.1 合併邏輯

`generate_html.py` 的 `_build_channel_data()` 處理合併：

```python
def _build_channel_data():
    channels = tg_core.load_channels()
    groups = {}  # group_name → [channel_entry, ...]
    standalone = []

    for ch in channels:
        grp = ch.get("group")
        if grp:
            groups.setdefault(grp, []).append(ch)
        else:
            standalone.append(ch)

    tabs = []
    # 合併群組：一個 tab
    for grp_name, members in groups.items():
        merged = {
            "id": grp_name,
            "name": members[0]["name"],
            "mode": "text",
            "messages": [],  # 合併所有成員的訊息
            "photos": [],
            "videos": [],
        }
        for m in members:
            merged["messages"].extend(tg_core.load_messages(m["id"]))
            merged["photos"].extend(_scan_media_files(m["id"], "photo"))
            merged["videos"].extend(_scan_media_files(m["id"], "video"))
        merged["messages"].sort(key=lambda x: x.get("id", 0), reverse=True)
        tabs.append(merged)

    # 獨立頻道：各自一個 tab
    for ch in standalone:
        tabs.append({...})  # 原有邏輯

    return tabs
```

### 4.2 訊息卡片來源標註

每張訊息卡片顯示來源頻道標籤：

```html
<div class="card">
  <div class="card-date">2025-07-01T14:30:22</div>
  <div class="card-source">AIguoman18</div>   ← 新增
  <div class="card-text">訊息內文...</div>
  <div class="card-media">...</div>
</div>
```

來源標籤從 `messages.jsonl` 的 `channel` 欄位取得，再透過 `channels.json` 對應到 `username` 顯示。

---

## 5. UI 元件設計

### 5.1 燈箱 (Lightbox)

```
┌─────────────────────────────────────────────┐
│                                       [✕]   │  ← 關閉按鈕（固定右上）
│                                             │
│              ┌──────────────┐               │
│   [‹]        │              │        [›]    │  ← 左右導航箭頭
│              │   圖片/影片   │               │
│              │              │               │
│              └──────────────┘               │
│                                             │
│                  2 / 15                      │  ← 計數器（固定底部）
└─────────────────────────────────────────────┘
```

**HTML 結構：**
```html
<div id="lightbox" class="lightbox">
  <span id="lb-close" class="lb-close">&times;</span>
  <span id="lb-prev" class="lb-prev">&lsaquo;</span>
  <span id="lb-next" class="lb-next">&rsaquo;</span>
  <span class="lb-counter"></span>
  <div class="lb-content">
    <img id="lb-img" src="" alt="">
    <video id="lb-video" src="" controls></video>
  </div>
</div>
```

**互動行為：**
| 操作 | 行為 |
|------|------|
| 點擊圖片/影片 | 開啟燈箱，定位到該項目 |
| 點擊 ‹ / › | 前後切換 |
| 按 ← / → 鍵 | 前後切換 |
| 按 ESC | 關閉 |
| 點擊遮罩背景 | 關閉 |
| 點擊 ✕ | 關閉 |

**JS 實作要點：**
- 全頁事件委派：監聽 `a[data-lightbox]` 點擊
- `data-lightbox` 值 = 頁籤 ID，同一頁籤的所有媒體共用同一個燈箱導航群組
- 影片不自動播放，使用者手動點擊播放

### 5.2 搜尋與日期篩選

```
┌──────────────────────────────────────────────────────┐
│  [🔍 搜尋訊息...              ] [📅 起始] [📅 結束]  │
│  3 筆結果                                            │
├──────────────────────────────────────────────────────┤
│  (訊息卡片列表 — 僅顯示符合條件的卡片)                  │
└──────────────────────────────────────────────────────┘
```

**元件規格：**
| 元件 | 型別 | 行為 |
|------|------|------|
| 搜尋輸入框 | `<input type="text">` | `input` 事件即時觸發篩選 |
| 起始日期 | `<input type="date">` | `change` 事件觸發篩選 |
| 結束日期 | `<input type="date">` | `change` 事件觸發篩選 |
| 結果計數 | `<div>` | 顯示 "N 筆結果" |

**篩選邏輯：**
- 關鍵字：比對 `.card-text` 的文字內容（不分大小寫）
- 日期範圍：比對 `.card-date` 的前 10 字元（yyyy-mm-dd）
- 兩個條件同時成立才顯示
- 篩選時隱藏分頁「載入更多」按鈕，顯示所有符合結果
- 清空搜尋條件時還原分頁狀態

**顯示位置：** 僅在文字模式（`mode: "text"`）的頁籤顯示搜尋列。

### 5.3 分頁載入 (Load More)

```
┌──────────────────────────────┐
│  (前 50 筆內容)              │
│                              │
├──────────────────────────────┤
│     載入更多 (120)           │  ← 點擊展開次頁
└──────────────────────────────┘
         │ 點擊後
         ▼
┌──────────────────────────────┐
│  (展開後 100 筆內容)         │
│                              │
├──────────────────────────────┤
│     載入更多 (70)            │
└──────────────────────────────┘
         │ ...重複直到全部載入
         ▼
┌──────────────────────────────┤
│     已全部載入               │  ← disabled 狀態
└──────────────────────────────┘
```

**規格：**

| 參數 | 值 |
|------|-----|
| 每頁筆數 | 50 |
| 初始顯示 | 前 50 筆 |
| 載入按鈕文字 | 「載入更多 (N)」→「已全部載入」 |
| 適用範圍 | `.gallery` 和 `.cards-container` 的直接子元素 |

**JS 實作：**
- DOM 載入後，掃描所有 `.gallery` 和 `.cards-container`
- 隱藏超過 50 筆的子元素（添加 `.hidden` class）
- 動態插入 `<div class="load-more">` 按鈕
- 點擊後移除下一批 `.hidden` class
- 全部展開後按鈕變為 `.done` 狀態

### 5.4 媒體效能優化

| 媒體 | 屬性 | 效果 |
|------|------|------|
| `<img>` | `loading="lazy"` | 瀏覽器僅載入可視範圍圖片 |
| `<video>` | `preload="none"` | 不預載影片，點擊播放才載入 |

`loading="lazy"` 為 HTML 原生屬性，無需 JS。在 `_build_media_gallery()` 和 `_build_messages()` 中直接輸出。

---

## 6. 文字回溯擷取設計 (F19)

### 6.1 問題

AIguoman18 在 v2 是 `mode: "media"`，只下載媒體不擷取文字。切換到 `mode: "text"` 後需回溯擷取歷史訊息文字，但不應重複下載已存在的媒體。

### 6.2 方案：檔案存在檢查

```python
async def process_channel(channel, client):
    # ... existing setup ...
    async for message in client.iter_messages(entity, limit=fetch_limit):
        # 不再提前 break，因為需要回溯處理已下載的訊息
        if channel_mode == "text" and message.id in downloaded:
            # 已處理過但需要文字：檢查是否已有文字記錄
            # 若無 → 擷取文字但不重複下載媒體
            ...
```

**簡化策略：**
- 為 AIguoman18 新增 `backfill: true` 設定
- 當 `backfill: true` 時：重新遍歷歷史訊息，已存在的媒體跳過不重複下載，僅補充文字記錄
- 下載狀態檔不變，避免重複爬取

**實作方式：**
- 在 `download_tg_channel.py` 中增加 `backfill` 模式的判斷
- 判斷媒體檔案是否已存在於磁碟：`filepath.exists()` → 跳過下載
- 仍寫入 `messages.jsonl`

### 6.3 設定

```json
{
  "id": "ai_guoman",
  "username": "AIguoman18",
  "name": "男人的幻想",
  "mode": "text",
  "group": "mens_fantasy",
  "fetch_limit": 50,
  "backfill": true
}
```

`backfill: true` 值僅在首次回溯時需要，完成後可移除或設為 `false`。

---

## 7. TOC 結構設計

### 7.1 HTML 生成架構 v3

```
generate_html.py
  │
  ├─ _scan_media_files(channel_id, subdir)
  ├─ _build_channel_data()           ← 新增合併邏輯
  │    ├─ 讀取 channels.json
  │    ├─ 依 group 分組
  │    ├─ 合併同組頻道的 messages + media
  │    └─ 回傳 tabs 陣列
  │
  ├─ _build_media_gallery()          ← 新增 data-lightbox 屬性
  ├─ _build_split_gallery()
  ├─ _build_messages()               ← 新增 channel 標籤 + data-lightbox
  │
  └─ generate()
       ├─ 生成頁籤 HTML
       ├─ 生成內容 HTML（含搜尋列 + 燈箱骨架）
       ├─ 輸出 CSS（既有 + 燈箱 + 搜尋 + 分頁樣式）
       └─ 輸出 JS（燈箱 + 搜尋 + 分頁）
```

### 7.2 網頁結構 v3

```
index.html
  ├─ header (標題: Adult Dream + 更新時間)
  ├─ nav (頻道頁籤)
  │   ├─ [男人的幻想]    ← 合併 ai_guoman + ciyuanb + llcosfc
  │   └─ [東南亞大事件]  ← dashijian 獨立
  ├─ content
  │   ├─ 男人的幻想頁籤
  │   │   ├─ 搜尋列（文字+日期）
  │   │   ├─ 訊息卡片列表（按時間降冪，標註來源頻道）
  │   │   └─ 媒體合併圖庫
  │   └─ 東南亞大事件頁籤
  │       ├─ 搜尋列（文字+日期）
  │       └─ 訊息卡片列表
  └─ 燈箱骨架 (display:none)
```

---

## 8. 關鍵設計取捨 v3

| 決策 | 理由 |
|------|------|
| group 欄位而非巢狀結構 | 向後相容 v2 設定檔，無 group 即為獨立頻道 |
| 合併時訊息交錯排列 | 讓使用者看到按時間排序的統一時間線 |
| 卡片標註來源頻道 | 合併後仍能追溯原始出處 |
| ES5 JS（無箭頭函式/const/let） | 確保舊瀏覽器相容，靜態 HTML 無法控管使用者環境 |
| 燈箱共用 data-lightbox 群組 | 同一頁籤內所有媒體可連續瀏覽，不需切換群組 |
| 搜尋時隱藏分頁按鈕 | 使用者搜尋時期看到所有符合結果，不分頁干擾 |
| 分頁 50 筆 | 平衡初始載入速度與每次展開的內容量 |
| backfill 而非重置狀態 | 不重複下載已存在媒體，僅補充文字 |
| 檔案存在檢查跳過重複下載 | 避免浪費頻寬和儲存空間 |
| 純 HTML/CSS/JS 無外部依賴 | 保持靜態網站零依賴原則 |
