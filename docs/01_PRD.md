# 01 - PRD v6：APP 模式前端設計 (Telegram only)

## 版本變更

v3 → v6：純 CSS 重新設計為 APP 模式。功能、JS、HTML 結構全部不動。Telegram 頻道專用（無 xvideos）。

## 設計目標

模擬手機 APP 外觀：
- 430px 手機框架置中
- 底部導航 (🏠📰🔥🎬)
- Compact header
- 金色博彩主題
- 51 項現有測試必須通過

## 變更範圍

| 檔案 | 變更 |
|------|------|
| `src/generate_html.py` CSS block | 完全重寫 |
| 其他全部 | 不變 |

## Out of Scope

- 不含 xvideos
- 不改 JS
- 不改 HTML 結構
- 不改 Telegram 功能
