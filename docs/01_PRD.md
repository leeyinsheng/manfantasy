# 01 - PRD v3：多頻道合併 + 平行下載 + UI 強化

## 版本變更

v2 → v3 核心變動：新增3個頻道並合併顯示、平行下載加速、靜態網頁互動強化（燈箱/搜尋/分頁）。

---

## 頻道清單（v3）

| # | id | username | 模式 | 顯示名稱 | group | 備註 |
|---|-----|----------|------|----------|-------|------|
| 1 | ai_guoman | AIguoman18 | text | 男人的幻想 | mens_fantasy | 既有 |
| 2 | ciyuanb | ciyuanb | text | 男人的幻想 | mens_fantasy | 既有 |
| 3 | llcosfc | llcosfc | text | 男人的幻想 | mens_fantasy | 既有 |
| 4 | guoman18 | guoman18 | text | 男人的幻想 | mens_fantasy | 既有 |
| 5 | OnlyfansChannels | OnlyfansChannels | text | 男人的幻想 | mens_fantasy | **新增** |
| 6 | dashijian | dashijian | text | 東南亞大事件 | news | 既有 |
| 6 | ll111 | ll111 | text | 東南亞大事件 | news | 既有 |
| 7 | yuanqubot | yuanqubot | text | 東南亞大事件 | news | **新增** |

---

## 功能需求

### F14 平行頻道下載

- 使用 `asyncio.gather()` 同時對多個頻道進行下載
- 單一頻道失敗不影響其他頻道（`return_exceptions=True`）
- 各頻道擁有獨立目錄與狀態檔，無競爭條件

### F15 圖片燈箱檢視

- 點擊圖片/影片 → 全螢幕深色遮罩檢視（純 CSS/JS，無外部依賴）
- 支援左右箭頭切換前後張、ESC 關閉、點擊遮罩關閉
- 顯示當前位置計數（N / M）
- 影片在燈箱內使用 HTML5 `<video>` 播放
- 同一頁籤內所有媒體共用一個燈箱群組

### F16 訊息搜尋與日期篩選

- 文字模式頻道頁籤上方出現搜尋列 + 時間快捷按鈕組（全部/今日/近3日/近7日/本月/近半年）
- 關鍵字即時比對訊息卡片內文
- 顯示符合結果筆數

### F17 分頁載入

- 每頁 50 筆（圖片/影片/訊息卡片）
- 初始僅顯示第一頁，底部顯示「載入更多 (N)」
- 點擊展開下一頁，直到全部載入後顯示「已全部載入」
- 搜尋模式下暫停分頁，顯示所有符合結果

### F18 媒體載入效能優化

- 所有 `<img>` 加入 `loading="lazy"`（瀏覽器原生懶加載）
- 所有 `<video>` 使用 `preload="none"`（不預載影片節省頻寬）

### F19 文字回溯擷取

- AIguoman18 從 v2 的 media 模式切換為 text+media 模式
- 首次執行時回溯拉取歷史訊息，擷取文字內容寫入 `messages.jsonl`
- 已存在於磁碟的媒體檔案不重複下載
- 透過檢查檔案是否已存在來跳過重複下載

---

## 頻道設定檔設計（v3 `channels.json`）

新增 `group` 欄位：相同 `group` 值的頻道在網頁合併為一個頁籤。

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
      "group": "news",
      "fetch_limit": 50
    },
    {
      "id": "ll111",
      "username": "ll111",
      "name": "東南亞大事件",
      "mode": "text",
      "group": "news",
      "fetch_limit": 50
    }
  ]
}
```

| 欄位 | 用途 |
|------|------|
| `group` | 可選。相同 group 的頻道合併為單一頁籤；無 group 則獨立頁籤 |

---

## 網頁合併邏輯

```
頁籤: [男人的幻想]  [東南亞大事件]
         │               │
         │               └─ 合併 dashijian + ll111 (news group)
         │                    ├─ 所有訊息按時間降冪交錯排列
         │                    └─ 每張訊息卡片標註來源頻道
         │
         └─ 合併 ai_guoman + ciyuanb + llcosfc (mens_fantasy group)
              ├─ 所有訊息按時間降冪交錯排列
              ├─ 每張訊息卡片標註來源頻道
              └─ 媒體圖庫合併顯示
```

---

## 使用者流程（v3）

```
排程觸發
  │
  ├─ 1. 平行連接五個頻道 (asyncio.gather)
  │     ├─ AIguoman18: 回溯擷取文字 + 新媒體
  │     ├─ ciyuanb: 擷取文字 + 下載媒體
  │     ├─ llcosfc: 擷取文字 + 下載媒體
  │     ├─ dashijian: 擷取文字 + 下載媒體
  │     └─ ll111: 擷取文字 + 下載媒體
  │
  ├─ 2. 更新各頻道狀態檔
  │
  └─ 3. 觸發 generate_html.py
        ├─ 合併 mens_fantasy group → 男人的幻想頁籤
        ├─ 合併 news group → 東南亞大事件頁籤
        └─ 產出 index.html（燈箱 / 搜尋 / 分頁）
```

---

## 目錄結構（v3）

```
download/
├── ai_guoman/                  ← AIguoman18（既有）
│   ├── photo/
│   ├── video/
│   ├── messages.jsonl          ← 新增：文字記錄
│   └── .downloaded_state.json
├── ciyuanb/                    ← 新增
│   ├── photo/
│   ├── video/
│   ├── messages.jsonl
│   └── .downloaded_state.json
├── llcosfc/                    ← 新增
│   ├── photo/
│   ├── video/
│   ├── messages.jsonl
│   └── .downloaded_state.json
├── dashijian/                  ← 既有，改為 news group
│   ├── photo/
│   ├── video/
│   ├── messages.jsonl
│   └── .downloaded_state.json
├── ll111/                       ← 新增
│   ├── photo/
│   ├── video/
│   ├── messages.jsonl
│   └── .downloaded_state.json
└── index.html                  ← 靜態展示網頁（兩頁籤）
```

---

## Out of Scope（v3）

- 不支援 Telegram Bot 模式
- 不做全文搜尋引擎（留待 v4）
- 不做資料庫儲存
- 不做動態網站或後端服務
- 不做自動翻譯或內容過濾
- 不做使用者認證 / 多用戶
