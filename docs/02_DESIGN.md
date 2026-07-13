# 02 - Design v12：小紅書卡片 + 分類標籤

## Layout

```
┌──────────────────────────────┐
│ 🔍 搜尋小紅書筆記…      ⏳ ⚙ │ ← 頂部搜尋列（常駐）
├──────────────────────────────┤
│ [異想] [大事件] [吃瓜] [AI短]│ ← 分類標籤（水平滾動）
│ [xv]                         │
├──────────────────────────────┤
│ ┌────────┐ ┌────────┐       │
│ │        │ │        │       │ ← 雙欄 waterfall
│ │  圖片   │ │  圖片   │       │   卡片 3:4 比例
│ │  3:4   │ │  3:4   │       │
│ │        │ │        │       │
│ │標題兩行 │ │標題兩行 │       │
│ │👤 頻道  │ │👤 頻道  │       │   ← 頭像 + 名稱
│ │♥ 1.2k  │ │♥ 856   │       │   ← 愛心數 + 留言數
│ └────────┘ └────────┘       │
├──────────────────────────────┤
│ 🏠      📰     🔥     🎬   ❌│ ← 底部導覽
│ 異想    大事件  吃瓜   AI短  xv│   （圖示 + 文字）
└──────────────────────────────┘
```

## 卡片設計

```
┌─────────────────┐
│                 │
│                 │
│   Cover Image   │  ← aspect-ratio: 3/4
│                 │
│                 │
├─────────────────┤
│ 標題文字最多三行  │  ← font-size: 0.82rem, -webkit-line-clamp: 3
│ 第二行…          │
├─────────────────┤
│ 👤 頻道名        │  ← 左側 18px 圓形頭像 + 來源名稱
│ ♥ 1.2k  💬 89  │  ← 右側互動數據
└─────────────────┘
```

### CSS 關鍵值

```css
.card { background: var(--surface); border-radius: 8px; overflow: hidden; }
.card-cover { position: relative; aspect-ratio: 3 / 4; }
.card-cover img { width: 100%; height: 100%; object-fit: cover; }
.card-body { padding: 0.5rem 0.6rem; }
.card-title { font-size: 0.82rem; line-height: 1.4; -webkit-line-clamp: 3; }
.card-footer { display: flex; align-items: center; justify-content: space-between; padding: 0 0.6rem 0.5rem; }
.card-author { display: flex; align-items: center; gap: 0.35rem; font-size: 0.68rem; }
.card-author-avatar { width: 18px; height: 18px; border-radius: 50%; background: var(--accent); }
.card-stats { display: flex; gap: 0.6rem; font-size: 0.68rem; color: var(--muted); }
```

## 分類標籤列

```html
<div class="chip-bar">
  <button class="chip active">異想空間</button>
  <button class="chip">大事件</button>
  <button class="chip">吃瓜爆料</button>
  <button class="chip">AI短劇</button>
  <button class="chip">xvideo</button>
</div>
```

```css
.chip-bar { display: flex; gap: 0.5rem; padding: 0.6rem 0.75rem; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.chip-bar::-webkit-scrollbar { display: none; }
.chip { flex-shrink: 0; padding: 0.35rem 0.8rem; border-radius: 20px; font-size: 0.78rem; background: var(--surface-2); color: var(--muted); border: none; }
.chip.active { background: var(--accent); color: #fff; }
```

## 搜尋列

```html
<div class="search-bar">
  <div class="search-input-wrapper">
    <span class="search-icon">🔍</span>
    <input placeholder="搜尋筆記…">
  </div>
</div>
```

## 互動數據

```javascript
function fakeStats() {
  return {
    likes: Math.floor(Math.random() * 9000) + 100,
    comments: Math.floor(Math.random() * 200)
  };
}
function formatNum(n) {
  return n >= 1000 ? (n/1000).toFixed(1).replace('.0','') + 'k' : n;
}
```

## 底部導覽（恢復文字）

恢復 icon + label 雙行顯示，5 tab 等寬：

```css
.nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 0.3rem 0; color: var(--muted); }
.nav-item .icon { font-size: 1.35rem; }
.nav-item .label { font-size: 0.55rem; }
```

## What Changes

| 檔案 | 變更 |
|------|------|
| `src/generate_html.py` | CSS 全部重寫、HTML 新增 chip-bar + search-bar、JS 更新卡片渲染 + 假數據 + chip 切換 |
| `tests/test_html.py` | 新增 chip-bar、search-bar、card 結構測試 |
