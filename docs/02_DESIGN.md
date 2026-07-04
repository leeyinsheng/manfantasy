# 02 - Design v6：APP Mode (Telegram only)

## Layout

```
        body (dark bg, center app-shell)
   ┌─────────────────────────────────┐
   │ .app-shell (430px, phone frame)  │
   │  ┌──────────────────────────┐   │
   │  │ MAN'S FANTASY     update │   │
   │  ├──────────────────────────┤   │
   │  │ [search] [全部/今日/..] │   │
   │  │ cards...                │   │
   │  │ pagination              │   │
   │  ├──────────────────────────┤   │
   │  │ 🏠     📰     🔥     🎬  │   │
   │  │異想   大事件  吃瓜   AI短│   │
   │  └──────────────────────────┘   │
   └─────────────────────────────────┘
```

## Color System

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0a0c12` | Page bg |
| `--accent` | `#c9a24e` | Gold |
| `--accent-hover` | `#e0c878` | Light gold |
| `--app-w` | `430px` | Phone width |

## Bottom Nav

4 tabs with emoji icons, gold accent on active.

## Cards, Search, Pagination

Keep existing v3 component styles, just recolor to gold theme.

## What Changes

Only CSS block in `generate_html.py`. HTML structure and JS unchanged.
