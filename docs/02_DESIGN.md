# 02 - Design v5：Casino Gold Theme

CSS-only redesign. v4 JS/HTML structure unchanged. Only colors, fonts, visual polish.

## Color System

| Token | v4 (Red) | v5 (Gold) |
|-------|----------|-----------|
| `--bg` | `#0a0a0a` | `#0a0c12` |
| `--accent` | `#d14334` | `#c9a24e` |
| `--accent-hover` | `#e05545` | `#e0c878` |
| `--surface` | `#161616` | `rgba(16,18,26,0.92)` |
| `--border` | `#2a2a2a` | `rgba(201,162,78,0.10)` |

## Key Visual Changes

| Element | v4 | v5 |
|---------|-----|-----|
| Header title | White text | Gold text with glow |
| Tab active | Red underline | Gold gradient underline + glow |
| Tab badge active | Gray | Gold |
| Tag buttons | Square | Capsule (16px radius) |
| Tag active | Red bg | Gold gradient bg, dark text |
| Tag badge | Purple | Gold |
| xv source dot | Purple | Gold (unified) |
| Lightbox close | White semi-transparent | Gold color |
| Vid icon play arrow | White | Gold |

## What Doesn't Change

- HTML structure (tab-nav, cards, search-bar, lightbox)
- JS logic (click handlers, rendering, toggleXvEmbed)
- Data flow
- Spider
- All Python code outside CSS block
