# 02 - 設計文件 v5：APP 模式 + 博彩風格

## 圖示映射

```
🏠 → 異想空間    (mens_fantasy)
📰 → 大事件      (news)
🔥 → 吃瓜        (guaba_bl)
🎬 → AI短劇       (ai_drama)
👊 → 弟兄們      (xvideos)
```

---

## 1. 整體佈局

```
┌─────────────────────────────────────────────┐
│  background: #0a0c12 (fill viewport)         │
│                                              │
│   ┌─────────────────────────────────┐       │
│   │ .app-shell (max 430px, 居中)     │       │
│   │  ┌──────────────────────────┐   │       │
│   │  │ .app-header              │   │       │
│   │  │  MAN'S FANTASY    23:34 │   │       │
│   │  ├──────────────────────────┤   │       │
│   │  │ .app-content (scroll)    │   │       │
│   │  │   cards, pagination      │   │       │
│   │  │                          │   │       │
│   │  ├──────────────────────────┤   │       │
│   │  │ .bottom-nav              │   │       │
│   │  │  🏠  📰  🔥  🎬  👊    │   │       │
│   │  └──────────────────────────┘   │       │
│   └─────────────────────────────────┘       │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 2. CSS 變數 (Casino + App)

```css
:root {
  --bg: #0a0c12;
  --bg-card: rgba(16,18,26,0.85);
  --bg-card-hover: rgba(20,22,32,0.9);
  --gold: #c9a24e;
  --gold-light: #e0c878;
  --gold-glow: rgba(201,162,78,0.15);
  --gold-dim: rgba(201,162,78,0.3);
  --fg: #e4e1db;
  --fg-dim: #908d86;
  --muted: #524f4a;
  --border: rgba(201,162,78,0.08);
  --border-gold: rgba(201,162,78,0.18);
  --nav-bg: rgba(8,10,16,0.96);
  --radius: 8px;
  --app-w: 430px;
}
```

---

## 3. 元件規格

### 3.1 App Shell

```css
body {
  background: var(--bg);
  display: flex; justify-content: center;
  padding: 0; min-height: 100dvh;
}
.app-shell {
  width: 100%; max-width: var(--app-w);
  min-height: 100dvh;
  display: flex; flex-direction: column;
  background: var(--bg);
  position: relative;
  overflow-x: hidden;
  border-left: 1px solid rgba(255,255,255,0.02);
  border-right: 1px solid rgba(255,255,255,0.02);
}
```

### 3.2 App Header

手機頂欄：左側 APP 名（小字），右側更新時間。

```css
.app-header {
  padding: 0.8rem 1rem;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10;
  background: rgba(10,12,18,0.94); backdrop-filter: blur(8px);
}
.app-header .title {
  font-family: 'Cinzel', Georgia, serif;
  font-size: 0.85rem; font-weight: 600; color: var(--gold);
  letter-spacing: 0.06em; text-shadow: 0 0 12px var(--gold-glow);
}
.app-header .time { font-size: 0.68rem; color: var(--muted); }
```

### 3.3 App Content (滾動區)

```css
.app-content {
  flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch;
  padding: 0.75rem 0.75rem 5rem;
}
```

### 3.4 Bottom Nav (底部導航)

固定在底部，5 個圖示按鈕，選中時金色。

```css
.bottom-nav {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: var(--app-w);
  display: flex; justify-content: space-around;
  background: var(--nav-bg); backdrop-filter: blur(16px);
  border-top: 1px solid var(--border);
  padding: 0.3rem 0 env(safe-area-inset-bottom, 0.3rem);
  z-index: 20;
}
.nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 0.35rem 0.5rem; min-width: 52px;
  font-size: 0.6rem; color: var(--muted);
  cursor: pointer; user-select: none; transition: color .15s;
  -webkit-tap-highlight-color: transparent;
}
.nav-item .icon { font-size: 1.2rem; line-height: 1; }
.nav-item.active { color: var(--gold); }
.nav-item.active .icon { text-shadow: 0 0 10px var(--gold-glow); }
```

```html
<nav class="bottom-nav">
  <div class="nav-item active" data-tab="mens_fantasy">
    <span class="icon">🏠</span><span>異想空間</span>
  </div>
  <div class="nav-item" data-tab="news">
    <span class="icon">📰</span><span>大事件</span>
  </div>
  <div class="nav-item" data-tab="guaba_bl">
    <span class="icon">🔥</span><span>吃瓜</span>
  </div>
  <div class="nav-item" data-tab="ai_drama">
    <span class="icon">🎬</span><span>AI短劇</span>
  </div>
  <div class="nav-item" data-tab="xvideos">
    <span class="icon">👊</span><span>弟兄們</span>
  </div>
</nav>
```

### 3.5 卡片

```css
.card {
  background: var(--bg-card); backdrop-filter: blur(10px);
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0.8rem 0.8rem 0; margin-bottom: 0.5rem;
  transition: border-color .15s;
  -webkit-tap-highlight-color: transparent;
}
.card:active { border-color: var(--border-gold); }
.card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.4rem; font-size: 0.72rem;
}
.card-source {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 6px; background: rgba(201,162,78,0.08);
  border-radius: 3px; color: var(--fg-dim); font-size: 0.68rem;
}
.card-source::before {
  content: ''; width: 5px; height: 5px; border-radius: 50%;
  background: var(--gold); box-shadow: 0 0 4px var(--gold-glow);
}
.card-date {
  font-family: 'Cinzel', Georgia, serif;
  font-size: 0.66rem; color: var(--muted);
}
.card-text {
  font-size: 0.84rem; line-height: 1.6; margin-bottom: 0.4rem;
  overflow: hidden; display: -webkit-box;
  -webkit-line-clamp: 3; -webkit-box-orient: vertical;
}
.card-text.full { -webkit-line-clamp: unset; display: block; }
.card-thumbs {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 3px; margin-top: 0.4rem;
}
.thumb {
  position: relative; aspect-ratio: 1; overflow: hidden;
  border-radius: 3px; background: var(--bg);
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb .vid-icon {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  width: 24px; height: 24px; background: rgba(0,0,0,0.65);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.thumb .vid-icon::after {
  content: ''; border-left: 7px solid var(--gold);
  border-top: 4px solid transparent; border-bottom: 4px solid transparent;
  margin-left: 1px;
}
.card-expand {
  text-align: center; font-size: 0.72rem; color: var(--gold-dim);
  padding: 0.5rem 0; margin: 0 -0.8rem; margin-top: 0.4rem;
  border-top: 1px solid var(--border); cursor: pointer; user-select: none;
  transition: color .15s;
  -webkit-tap-highlight-color: transparent;
}
.card-expand:active { color: var(--gold); }
```

### 3.6 標籤列 (xv)

```css
.tag-bar {
  display: flex; gap: 5px; margin-bottom: 0.75rem; flex-wrap: wrap;
  padding: 0 0.25rem;
}
.tag-btn {
  padding: 0.3rem 0.7rem; font-size: 0.72rem;
  color: var(--muted); background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); border-radius: 16px;
  cursor: pointer; user-select: none; transition: all .15s;
  -webkit-tap-highlight-color: transparent;
}
.tag-btn:active { color: var(--gold-dim); border-color: var(--gold-dim); }
.tag-btn.active {
  color: var(--bg); background: linear-gradient(135deg, var(--gold), var(--gold-light));
  border-color: transparent; font-weight: 600;
}
```

### 3.7 分頁

```css
.pagination {
  display: flex; justify-content: center; gap: 4px;
  padding: 0.75rem 0 0.5rem; flex-wrap: wrap;
}
.page-btn {
  min-width: 32px; height: 32px; font-size: 0.75rem;
  color: var(--muted); background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); border-radius: 4px;
  cursor: pointer; transition: all .15s;
  display: flex; align-items: center; justify-content: center;
  -webkit-tap-highlight-color: transparent;
}
.page-btn:active { color: var(--gold-dim); border-color: var(--gold-dim); }
.page-btn.active {
  color: var(--bg); background: linear-gradient(135deg, var(--gold), var(--gold-light));
  border-color: transparent; font-weight: 600;
}
```

### 3.8 xv Embed

```css
.xv-embed {
  margin: 0.4rem -0.8rem 0; overflow: hidden;
  background: #000; border-top: 1px solid var(--border);
}
.xv-embed iframe {
  display: block; border: none; width: 100%;
  min-height: 260px;
}
```

### 3.9 Lightbox

```css
.lightbox {
  display: none; position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.96);
}
.lightbox.open { display: flex; align-items: center; justify-content: center; }
.lb-close {
  position: absolute; top: 1rem; right: 1rem;
  width: 38px; height: 38px; border-radius: 50%;
  font-size: 1.3rem; color: var(--gold-dim);
  border: 1px solid var(--border-gold);
  background: var(--bg-card);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 2;
}
.lb-prev,.lb-next {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 40px; height: 40px; font-size: 1.8rem;
  color: var(--gold-dim); cursor: pointer; z-index: 2;
  display: flex; align-items: center; justify-content: center;
}
.lb-prev { left: 0.5rem; } .lb-next { right: 0.5rem; }
.lb-counter {
  position: absolute; bottom: 1rem; left: 50%; transform: translateX(-50%);
  color: var(--fg-dim); font-size: 0.78rem; z-index: 2;
}
.lb-content {
  max-width: 96vw; max-height: 80vh;
  display: flex; align-items: center; justify-content: center;
}
.lb-content img,.lb-content video {
  max-width: 100%; max-height: 80vh; object-fit: contain; border-radius: 4px;
}
```

---

## 4. HTML 結構 v5

```html
<body>
  <div class="app-shell">
    <header class="app-header">...</header>
    <main class="app-content">
      <div class="tab-content active" id="content-mens_fantasy">...</div>
      <div class="tab-content" id="content-news">...</div>
      ...
    </main>
    <nav class="bottom-nav">...</nav>
  </div>
  <div class="lightbox">...</div>
  <script>...</script>
</body>
```

---

## 5. 設計取捨

| 決策 | 理由 |
|------|------|
| 底部導航取代頂部 tab | APP 標準 UX，拇指熱區 |
| max-w: 430px | iPhone 14 Pro Max 尺寸 |
| 無 hover，改用 :active | 手機端無 hover，桌面點擊也有回饋 |
| 不留搜尋列 | APP 瀏覽模式，不適合文字輸入 |
| Cinzel 字體僅用於標題/日期 | 內文用系統字體確保可讀性 |
| backdrop-filter + 半透明卡片 | 博彩高端感 |
| 卡片點擊展開（非 hover） | 觸控友善 |
