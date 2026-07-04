# 02 - Design v7：Waterfall 卡片 + 手機直向專屬版型

## Layout

```
        body (深色底, 內容置中, 手機版寬度)
   ┌─────────────────────────────────┐
   │ .app (max-width: 560px, 置中)     │
   │  ┌──────────────────────────┐   │
   │  │ MAN'S FANTASY   🔍  更新..│   │ ← compact header
   │  ├──────────────────────────┤   │
   │  │ [搜尋/時間篩選面板]        │   │ ← 預設收合, 點🔍展開
   │  ├──────────────────────────┤   │
   │  │ ┌───────┐ ┌───────┐      │   │
   │  │ │ 圖卡A  │ │ 圖卡B  │      │   │ ← 雙欄 waterfall
   │  │ │(高)    │ └───────┘      │   │   （左右欄各自堆疊，
   │  │ │        │ ┌───────┐      │   │    高度依圖片比例）
   │  │ └───────┘ │ 圖卡C  │      │   │
   │  │ [純文字卡：全寬]           │   │ ← 無圖貼文，全寬
   │  │ ┌───────┐ ┌───────┐      │   │
   │  │ │ 圖卡D  │ │ 圖卡E  │      │   │
   │  │ └───────┘ └───────┘      │   │
   │  │        （捲動載入更多）    │   │
   │  ├──────────────────────────┤   │
   │  │  🏠     📰     🔥     🎬  │   │ ← 底部導覽 (fixed)
   │  │ 異想   大事件  吃瓜   AI短│   │
   │  └──────────────────────────┘   │
   └─────────────────────────────────┘
```

- 桌面瀏覽器開啟時套用同一份版型：`.app` 維持 `max-width:560px` 置中，不做寬螢幕多欄排版。
- 底部導覽以 `position:fixed` 貼齊視窗底部（含 `env(safe-area-inset-bottom)`），內容區底部保留 padding 避免被遮擋。

## Color System（延續 v3 深色主題，不重新配色）

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0a0a0a` | 頁面底色 |
| `--surface` | `#161616` | 卡片/面板底色 |
| `--surface-2` | `#1e1e1e` | 輸入框/次要底色 |
| `--fg` / `--fg-secondary` / `--muted` | `#e5e5e5` / `#a0a0a0` / `#6a6a6a` | 文字階層 |
| `--border` | `#2a2a2a` | 分隔線 |
| `--accent` / `--accent-hover` | `#d14334` / `#e05545` | 沿用既有品牌紅，用於底部導覽 active、多圖徽章、來源圓點 |
| `--radius` | `10px` | 卡片圓角（比 v3 略大，貼近 App 質感） |

沿用既有色票，避免無理由改品牌識別；本次調整重點在**版型與互動**，不在配色。

## Header

- 移除 v3 的大標題置中版面，改為緊湊單行 header：左側站名（縮小字級），右側 🔍 搜尋圖示 + 更新時間。
- 點擊 🔍 → 展開/收合搜尋面板（含關鍵字輸入 + 時間篩選按鈕，沿用現有 `time-presets` 邏輯），預設收合以節省手機直向垂直空間。

## Waterfall 卡片區

### 有圖貼文（waterfall 雙欄）
- JS 依訊息陣列順序，交替分配到左/右兩個獨立欄位容器（`i % 2`），非 CSS multi-column（避免 CSS columns 打亂閱讀順序、breaking-inside 問題，且交替分配容易單元測試）。
- 卡片結構：封面圖（取第一張 media，`width:100%;height:auto` 依原始比例顯示，不裁切成正方形，形成高低錯落的 waterfall 效果）→ 2 行文字摘要（`-webkit-line-clamp:2`）→ 來源圓點 + 相對時間小字。
- 若 media 超過 1 張，封面右上角疊加「📷 N」徽章；若首張為影片，疊加播放圖示（沿用 v3 `.vid-icon`）。
- 點擊卡片 → 開啟全螢幕詳情覆蓋層（sheet），顯示完整文字 + 所有圖片/影片縮圖；點縮圖沿用現有 lightbox 大圖/影片瀏覽邏輯（`openLightbox`/`lb-prev`/`lb-next`/`Esc` 關閉，功能不變，僅重新掛載到新的 DOM 結構）。

### 純文字貼文（無圖）
- 不進入雙欄 waterfall 計算，改為全寬卡片，插入在當前 waterfall 兩欄之後（不強制對齊左右欄高度）。
- 維持 v3 的行內展開/收合（`toggleCard`）行為：點擊全文預覽 → 展開完整文字，不開全螢幕 sheet（沒有圖片可看，沒必要）。

## 底部導覽（取代頂部 tab bar）

- `position:fixed`，4 個既有頻道分類（異想空間/大事件/吃瓜/AI短劇），圖示 + 文字兩行，active 狀態用 `--accent` 上色。
- 切換 tab 時：套用現有 `switchTab()` 邏輯（顯示/隱藏對應 `.tab-content`），waterfall 容器需重新分配欄位（切換 tab 後重算 i%2 分配，因為每個 tab 的訊息數量獨立）。

## 捲動載入更多（取代頁碼分頁）

- 移除 `.pagination` 頁碼元件，改用 `IntersectionObserver` 監看列表底部的 sentinel 元素，進入可視範圍時載入下一批（`PAGE_SIZE` 沿用 50 筆/批，累加渲染而非替換）。
- 搜尋/時間篩選啟用時：暫停無限捲動，直接在前端已渲染的卡片中做顯示/隱藏過濾（沿用現有 `applySearch` 邏輯），與 v3 行為一致。

## 保留不變

- 資料結構（`__DATA__`、`message.channel/date/text/media`）、頻道分類邏輯、搜尋關鍵字/時間篩選演算法、lightbox 大圖瀏覽（含鍵盤左右/Esc）— 皆只換外觀與掛載位置，邏輯本體沿用。

## What Changes

| 檔案 | 變更 |
|------|------|
| `src/generate_html.py` | CSS 全部重寫；HTML 模板改為 header+搜尋面板+雙欄 waterfall 容器+底部導覽；JS 新增 waterfall 分配、詳情 sheet、IntersectionObserver 捲動載入，移除 pagination 渲染 |
| `tests/test_html.py` | 同步改寫，涵蓋 waterfall 分配、無限捲動、詳情 sheet、底部導覽 |
| `docs/prototype/design.html` | 靜態視覺 + 基本互動 prototype，供本階段確認 |
