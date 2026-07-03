# 02 - 設計文件 v5：博彩風格系統

## 版本變更摘要

v4 → v5：純前端 CSS 重設計，套用 2026 博彩網站設計語言。功能、資料結構、後端程式全部不動。

| 模組 | 狀態 | 說明 |
|------|------|------|
| `generate_html.py` CSS | **完全重寫** | 玻璃擬態、金色主調、動效 |
| `generate_html.py` JS | 微調 | 動效 class 名調整 |
| 其餘全部 | 不變 | — |

---

## 1. 色彩系統

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#06080d` | 頁面背景（極深灰藍） |
| `--bg-2` | `#0c0f16` | 次要背景 |
| `--surface` | `rgba(20,24,34,0.85)` | 卡片底（玻璃擬態） |
| `--surface-hover` | `rgba(26,30,42,0.92)` | 卡片 hover |
| `--gold` | `#c9a24e` | 主金色（琥珀金） |
| `--gold-light` | `#e8c96a` | 亮金 hover |
| `--gold-glow` | `rgba(201,162,78,0.20)` | 發光 |
| `--gold-dim` | `rgba(201,162,78,0.35)` | 半透明金 |
| `--fg` | `#e6e3dd` | 主要文字 |
| `--fg-secondary` | `#9a9790` | 次要文字 |
| `--muted` | `#5a5752` | 輔助文字 |
| `--border` | `rgba(201,162,78,0.10)` | 卡片邊框 |
| `--border-active` | `rgba(201,162,78,0.30)` | 作用中邊框 |
| `--badge-bg` | `rgba(201,162,78,0.12)` | badge 背景 |
| `--radius` | `6px` | 圓角 |
| `--max-w` | `880px` | 內容最大寬度 |

CSS 變數定義：
```css
:root {
  --bg: #06080d;
  --bg-2: #0c0f16;
  --surface: rgba(20,24,34,0.85);
  --surface-hover: rgba(26,30,42,0.92);
  --gold: #c9a24e;
  --gold-light: #e8c96a;
  --gold-glow: rgba(201,162,78,0.20);
  --gold-dim: rgba(201,162,78,0.35);
  --fg: #e6e3dd;
  --fg-secondary: #9a9790;
  --muted: #5a5752;
  --border: rgba(201,162,78,0.10);
  --border-active: rgba(201,162,78,0.30);
  --badge-bg: rgba(201,162,78,0.12);
  --radius: 6px;
  --max-w: 880px;
}
```

---

## 2. 字體

| Token | 值 | 用途 |
|-------|-----|------|
| `--font-display` | `'Cinzel', Georgia, 'Times New Roman', serif` | 標題、日期、計數 |
| `--font-body` | `-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif` | 內文、介面 |

引入 Google Fonts：`@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap');`

---

## 3. Header 設計

```html
<header class="header">
  <div class="header-deco">◆</div>
  <h1>MAN'S FANTASY</h1>
  <div class="header-deco">◆</div>
  <div class="time">最後更新：<span>2026-07-03 23:34</span></div>
</header>
```

```css
.header { padding: 2.5rem 1rem 1.5rem; border-bottom: 1px solid var(--border); text-align: center; }
.header h1 {
  font-family: var(--font-display); font-size: clamp(1.5rem, 4vw, 2.2rem);
  font-weight: 600; letter-spacing: 0.12em; color: var(--gold);
  text-shadow: 0 0 30px var(--gold-glow);
}
.header-deco { color: var(--gold-dim); font-size: 0.6rem; margin: 0.4rem 0; }
```

---

## 4. 頁籤 (Tab Navigation)

```html
<nav class="tab-nav">
  <button class="tab-btn active" data-tab="news">東南亞大事件 <span class="badge">1019</span></button>
  <button class="tab-btn" data-tab="xvideos">衝啊, 弟兄們 <span class="badge">465</span></button>
</nav>
```

```css
.tab-nav { display: flex; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; background: rgba(6,8,13,0.92); backdrop-filter: blur(8px); }
.tab-btn {
  flex: 1; padding: 0.75rem 0.5rem; text-align: center; font-size: 0.82rem;
  font-weight: 500; color: var(--muted);
  position: relative; transition: color .2s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.tab-btn:hover { color: var(--fg-secondary); }
.tab-btn.active {
  color: var(--gold);
  text-shadow: 0 0 12px var(--gold-glow);
}
.tab-btn.active::after {
  content: ''; position: absolute; bottom: -1px; left: 15%; width: 70%; height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), var(--gold-light), var(--gold), transparent);
  border-radius: 1px;
}
.tab-btn .badge {
  display: inline-block; font-size: 0.65rem;
  background: var(--badge-bg); color: var(--gold-dim);
  padding: 1px 7px; border-radius: 10px; margin-left: 4px; vertical-align: middle;
}
.tab-btn.active .badge { background: var(--gold-dim); color: var(--bg); }
```

---

## 5. 卡片 (Card)

```html
<div class="card">
  <div class="card-header">
    <span class="card-source">xv · Amoulsolo <span class="tag-badge">內衣絲襪</span></span>
    <span class="card-date">48 min · 1080p</span>
  </div>
  <div class="card-text">Sexy O2, T&A XRed 392...</div>
  <div class="card-thumbs">...</div>
  <div class="card-expand">▶ 播放影片</div>
</div>
```

```css
.card {
  background: var(--surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-left: 2px solid var(--gold-dim);
  border-radius: var(--radius);
  padding: 1rem 1rem 0;
  margin-bottom: 0.75rem;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 1px var(--gold-glow);
  border-color: var(--border-active);
}
.card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.5rem; font-size: 0.78rem;
}
.card-source {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 2px 8px; background: var(--badge-bg);
  border-radius: 4px; color: var(--fg-secondary); font-size: 0.73rem;
}
.card-source::before {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: var(--gold); box-shadow: 0 0 6px var(--gold-glow);
}
.card-date {
  font-family: var(--font-display); font-size: 0.7rem;
  color: var(--muted); letter-spacing: 0.02em;
}
.card-text {
  font-size: 0.88rem; line-height: 1.65; margin-bottom: 0.5rem; color: var(--fg);
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
}
.card-text.full { -webkit-line-clamp: unset; display: block; }
.card-expand {
  text-align: center; font-size: 0.78rem; color: var(--gold-dim);
  padding: 0.6rem 0; margin: 0 -1rem; margin-top: 0.5rem;
  border-top: 1px solid var(--border); cursor: pointer;
  transition: color .15s, background .15s; user-select: none;
}
.card-expand:hover { color: var(--gold); background: rgba(201,162,78,0.04); }
```

---

## 6. 搜尋列 / 標籤列

搜尋列和標籤列保持結構不變，僅換色：

```css
.search-bar {
  display: flex; flex-wrap: wrap; gap: 0.5rem; padding: 0.75rem;
  background: var(--surface); backdrop-filter: blur(12px);
  border: 1px solid var(--border); border-radius: var(--radius);
  margin-bottom: 1.5rem; align-items: center;
}
.search-bar input[type="text"] {
  flex: 1; min-width: 160px; padding: 0.5rem 0.75rem;
  background: var(--bg-2); border: 1px solid var(--border);
  border-radius: 4px; font-size: 0.82rem; color: var(--fg);
  transition: border-color .15s;
}
.search-bar input[type="text"]:focus {
  border-color: var(--gold-dim); outline: none;
  box-shadow: 0 0 0 2px rgba(201,162,78,0.08);
}

.tag-bar { display: flex; gap: 6px; margin-bottom: 1rem; flex-wrap: wrap; }
.tag-btn {
  padding: 0.35rem 0.8rem; font-size: 0.76rem;
  color: var(--muted); background: var(--bg-2);
  border: 1px solid var(--border); border-radius: 20px;
  cursor: pointer; transition: all .15s; user-select: none;
}
.tag-btn:hover { color: var(--gold-dim); border-color: var(--gold-dim); }
.tag-btn.active {
  color: var(--bg); background: linear-gradient(135deg, var(--gold), var(--gold-light));
  border-color: transparent; font-weight: 600;
}
```

---

## 7. 分頁按鈕

```css
.pagination { display: flex; justify-content: center; gap: 4px; padding: 1rem 0; flex-wrap: wrap; align-items: center; }
.page-btn {
  min-width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
  padding: 0 8px; font-size: 0.8rem; color: var(--muted);
  background: var(--bg-2); border: 1px solid var(--border);
  border-radius: 4px; cursor: pointer; transition: all .15s; user-select: none;
}
.page-btn:hover { color: var(--gold-dim); border-color: var(--gold-dim); }
.page-btn.active {
  color: var(--bg); background: linear-gradient(135deg, var(--gold), var(--gold-light));
  border-color: transparent; font-weight: 600;
  box-shadow: 0 2px 8px var(--gold-glow);
}
.page-btn.disabled { opacity: 0.3; pointer-events: none; }
```

---

## 8. Embed iframe

```css
.xv-embed {
  margin: 0.5rem -1rem 0; border-radius: 0; overflow: hidden;
  background: #000; border-top: 1px solid var(--border);
}
.xv-embed iframe { display: block; border: none; width: 100%; min-height: 420px; }
```

---

## 9. 燈箱 (Lightbox)

```css
.lightbox {
  display: none; position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.95); backdrop-filter: blur(4px);
}
.lightbox.open { display: flex; align-items: center; justify-content: center; animation: lbFadeIn .2s ease; }
@keyframes lbFadeIn { from { opacity: 0; } to { opacity: 1; } }
.lb-close {
  position: absolute; top: 1rem; right: 1rem; width: 42px; height: 42px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; color: var(--gold-dim); cursor: pointer; z-index: 2;
  border: 1px solid var(--border-active); border-radius: 50%;
  background: var(--bg-2); transition: all .15s;
}
.lb-close:hover { color: var(--gold-light); border-color: var(--gold); box-shadow: 0 0 12px var(--gold-glow); }
```

---

## 10. 設計取捨

| 決策 | 理由 |
|------|------|
| `backdrop-filter: blur()` 玻璃擬態 | 現代博彩網站標配，營造深度感 |
| `#c9a24e` 琥珀金而非純金色 | 沉穩奢華，避免刺眼 |
| `Cinzel` 襯線標題字體 | 高端博彩品牌感 |
| 卡片 hover 上浮 2px + 微發光 | 暗示可點擊，不喧賓奪主 |
| 漸層金按鈕僅用於 active 狀態 | 視覺階層：預設低調、選中高亮 |
| 保留 sticky tab-nav + 實色背景 | 滾動時須遮蓋背後內容，blur 不夠 |
