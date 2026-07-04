# 02 - Design v8：xvideos 嵌入式播放整合

## 前提

v7 設計（waterfall 卡片、底部導覽、深色主題）全部保留。v8 僅在既有架構上新增一個 xvideo 頁籤，不修改既有 tab 的樣式或行為。

## Layout 變更

```
         body (深色底, 內容置中, 手機版寬度)
   ┌─────────────────────────────────┐
   │ .app (max-width: 560px, 置中)     │
   │  ┌──────────────────────────┐   │
   │  │ MAN'S FANTASY   🔍  更新..│   │ ← compact header（不變）
   │  ├──────────────────────────┤   │
   │  │ [搜尋/時間篩選面板]        │   │ ← 預設收合（不變）
   │  ├──────────────────────────┤   │
   │  │ ┌───────┐ ┌───────┐      │   │
   │  │ │卡片A(高)│ │卡片B   │      │   │ ← 雙欄 waterfall（不變）
   │  │ │        │ └───────┘      │   │
   │  │ │        │ ┌───────┐      │   │
   │  │ └───────┘ │卡片C   │      │   │
   │  │ ┌───────┐ ┌───────┐      │   │
   │  │ │卡片D   │ │卡片E   │      │   │
   │  │ └───────┘ └───────┘      │   │
   │  ├──────────────────────────┤   │
   │  │ 🏠  📰  🔥  🎬  ❌   │   │ ← 5 個 tab，字體縮小
   │  │異想 大事件 吃瓜 AI短 xv   │   │ ← 底部導覽（5 項）
   │  └──────────────────────────┘   │
   └─────────────────────────────────┘
```

## 底部導覽（變更）

原有 4 tab → 5 tab。**僅顯示圖示，不顯示文字標籤**，確保 5 個 tab 在手機窄螢幕上不擁擠。

| Tab | 圖示 | 寬度 |
|-----|------|------|
| 異想空間 | 🏠 | 20% |
| 東南亞大事件 | 📰 | 20% |
| 吃瓜爆料 | 🔥 | 20% |
| AI短劇 | 🎬 | 20% |
| xvideo | ❌ | 20% |

- `nav-item` 寬度 `flex: 1`（等分 20%）
- 圖示字體 `1.65rem`
- 移除 `.label` 文字元素
- active 狀態用 `--accent` 上色（不變）
- 保留 `aria-label` 屬性以維持無障礙瀏覽

## xvideo 卡片設計

與現有 waterfall 卡片一致，僅增加**時長徽章**：

```
┌──────────────────┐
│  ┌────────────┐   │
│  │            │   │
│  │  縮圖      │   │
│  │            │   │
│  │     ▶      │   │  ← play 圖示（與 v7 影片卡片相同）
│  │            │   │
│  └────────────┘   │
│  ⏱ 12:34          │  ← 時長徽章（右上角）
│                    │
│  影片標題兩行      │  ← -webkit-line-clamp:2
│  來源 · 3天前     │  ← 來源/時間小字
└──────────────────┘
```

### 資料格式 (`download/xvideos/videos.jsonl`)

```json
{
  "source": "maderotic",
  "eid": "maderotic_12345678",
  "video_id": "12345678",
  "title": "影片標題",
  "duration": "12:34",
  "thumbnail": "https://img-thumbnail-url.jpg",
  "uploader": "maderotic",
  "quality": "HD",
  "url": "https://www.xvideos.com/video12345678/",
  "ts": 1712345678
}
```

## 播放方式：iframe embed

不使用 `<video>` 標籤播放本地檔案，改以 iframe 嵌入 xvideos 播放器：

```html
<div class="xv-embed-container" style="position:relative;width:100%;padding-top:56.25%">
  <iframe src="https://www.xvideos.com/embedframe/{video_id}"
          style="position:absolute;inset:0;width:100%;height:100%"
          frameborder="0" scrolling="no" allowfullscreen>
  </iframe>
</div>
```

點擊流程：
1. 使用者點擊 xvideo 卡片 → 開啟詳情 sheet（顯示完整標題 + 縮圖）
2. 點擊縮圖或播放按鈕 → 開啟燈箱
3. 燈箱內以 iframe 取代原生的 `<video>` 標籤
4. 關閉燈箱 → iframe 從 DOM 移除（避免背景繼續播放）

## Color System

無變更。沿用 v7 深色主題色票。

## What Changes

| 檔案 | 變更 |
|------|------|
| `src/xv_spider.py` | 新增 `user/channel` URL 模式支援（`/maderotic` 格式） |
| `src/xvideos.json` | 加入 maderotic 來源設定 |
| `src/generate_html.py` | 新增 xvideos 資料載入函數（`_load_xvideos()`）；底部導覽改為 5 tab，`flex-basis: 20%`；燈箱播放邏輯新增 iframe embed 分支 |
| `tests/test_xv_spider.py` | 新增 channel 模式爬蟲測試 |
| `tests/test_html.py` | 新增 xvideo tab 渲染測試、iframe embed 測試 |

## 使用者體驗流程

```
開啟網站 → 底部導覽顯示 5 個 tab（包含 ❌ xv）
    ↓
點擊 ❌ xv → 切換到 xvideo tab
    ↓
顯示 xvideos 影片瀑布流卡片（雙欄）
    ↓
點擊卡片 → 詳情 sheet
    ↓
點擊播放 → 燈箱內以 iframe 播放 xvideos 影片
    ↓
關閉燈箱 → 回到瀑布流
```
