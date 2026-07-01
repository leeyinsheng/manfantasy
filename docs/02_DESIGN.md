# 02 - 設計文件 v2

## 版本變更摘要

v1 → v2 新增三個模組、重構一個既有模組：

| 模組 | 狀態 | 說明 |
|------|------|------|
| `tg_core.py` | 擴充 | 新增訊息文字擷取、頻道組態 |
| `download_tg_channel.py` | 重構 | 從單頻道改為多頻道迴圈 |
| `generate_html.py` | 新增 | 靜態網頁生成器 |
| `channels.json` | 新增 | 頻道定義設定檔 |

---

## 1. 系統架構 v2

```
┌──────────────────────────────────────────────────┐
│                 排程層                             │
│    cron / 工作排程器                                │
│         │                                          │
│         ▼                                          │
│  run_downloader.sh / .ps1                          │
│         │                                          │
│         ▼                                          │
│  download_tg_channel.py（多頻道迴圈）               │
│         │                                          │
│         ├─ channel: AIguoman18                     │
│         │   └─ 媒體模式：圖片/影片 → photo/video/   │
│         │                                          │
│         └─ channel: dashijian                      │
│             └─ 文字模式：文字 → messages.json       │
│                         媒體 → photo/video/        │
│         │                                          │
│         ▼                                          │
│  generate_html.py                                  │
│         │                                          │
│         ├─ 讀取各頻道 messages.json                 │
│         ├─ 讀取各頻道媒體檔案清單                    │
│         └─ 輸出 download/index.html                 │
└──────────────────────────────────────────────────┘
```

---

## 2. 頻道組態設計

### 2.1 設定檔（`src/channels.json`）

```json
{
  "channels": [
    {
      "id": "ai_guoman",
      "username": "AIguoman18",
      "name": "AIguoman18",
      "mode": "media",
      "fetch_limit": 50
    },
    {
      "id": "dashijian",
      "username": "dashijian",
      "name": "華人大事件",
      "mode": "text",
      "fetch_limit": 50
    }
  ]
}
```

**欄位說明：**

| 欄位 | 用途 |
|------|------|
| `id` | 內部識別碼，對應 `download/{id}/` 目錄名稱 |
| `username` | Telegram 頻道 username（`@` 後面的部分） |
| `name` | 顯示名稱，用於網頁頁籤標題 |
| `mode` | `"media"` 僅下載媒體 / `"text"` 同時擷取文字 |
| `fetch_limit` | 每次拉取訊息上限 |

**設計取捨：** 使用 JSON 設定檔而非寫死在程式碼中，讓新增頻道只需編輯設定檔，不需改程式碼。

### 2.2 既有設定檔

`~/.tg_downloader_config.json` 維持不變，僅存放 API 憑證。頻道清單與 API 憑證分離。

---

## 3. 訊息資料模型

### 3.1 messages.json 結構

```json
[
  {
    "id": 12345,
    "date": "2025-07-01T14:30:22",
    "text": "今天東南亞發生重大事件...",
    "channel": "dashijian",
    "media": [
      {
        "type": "photo",
        "path": "photo/20250701_143022_photo_12345.jpg",
        "size_kb": 245
      }
    ]
  }
]
```

**欄位說明：**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | int | Telegram 訊息 ID |
| `date` | str | ISO 8601 時間字串 |
| `text` | str | 訊息文字內文（無文字時為空字串） |
| `channel` | str | 所屬頻道 ID |
| `media` | array | 附帶的媒體檔案清單 |

### 3.2 增量寫入策略

- 每下載完一條新訊息，將其 JSON 物件附加到 `messages.json` 陣列尾端
- 不重寫整個檔案 — 透過 `json.dumps` 的逐條序列化實現
- 網頁端讀取時按 `id` 降冪排列（最新在上）

**實作方式：** 採用 JSON Lines 風格（`.jsonl`），每行一個 JSON 物件，方便逐條附加而不需解析整個檔案：

```
{"id":12345,"date":"...","text":"...","channel":"dashijian","media":[...]}
{"id":12346,"date":"...","text":"...","channel":"dashijian","media":[...]}
```

讀取時逐行解析，寫入時 `open(..., "a")` 附加一行。

---

## 4. 核心模組變更（`tg_core.py`）

### 4.1 新增函式

```python
def load_channels():
    """從 channels.json 讀取頻道清單"""
    # 讀取 src/channels.json，回傳頻道定義列表

def extract_message_text(message):
    """從 Telegram Message 物件擷取純文字"""
    # 回傳 message.text 或 message.caption 或 ""

def message_to_record(message, channel_id, media_files):
    """將訊息轉為 messages.jsonl 的一行記錄"""
    # 回傳 dict: {id, date, text, channel, media}
    # 轉為 JSON 字串

def append_message_record(channel_dir, record):
    """附加一筆訊息記錄到 messages.jsonl"""
    # open(channel_dir / "messages.jsonl", "a")
    # 寫入一行 JSON + 換行

def get_channel_dir(channel_id):
    """取得頻道的下載目錄路徑"""
    # return download_dir / channel_id
```

### 4.2 既有函式相容性

- `generate_photo_filename`、`generate_document_filename`、`classify_media` 等保持不變
- `load_state` / `save_state` 增加 `channel_id` 參數，指向不同頻道的狀態檔
- `PHOTO_DIR` / `VIDEO_DIR` / `STATE_FILE` 改為動態（依頻道）

---

## 5. HTML 生成器設計（`generate_html.py`）

### 5.1 架構

```
generate_html.py
  │
  ├─ load_all_messages()     ← 讀取所有頻道的 messages.jsonl
  ├─ load_all_media()        ← 掃描媒體頻道的 photo/video 目錄
  ├─ build_channel_data()    ← 組裝頻道資料結構
  └─ render_html()           ← 用模板生成 index.html
```

### 5.2 網頁結構

```
index.html
  ├─ header (標題: TG Archive)
  ├─ nav (頻道頁籤)
  │   ├─ [AIguoman18]  [華人大事件]
  │   └─ 點擊切換顯示內容
  ├─ content
  │   ├─ 媒體模式（AIguoman18）：
  │   │   └─ 圖片瀑布流 + 影片播放器
  │   └─ 文字模式（華人大事件）：
  │       └─ 訊息卡片（日期 → 文字 → 圖片縮圖，點擊放大）
  └─ footer (更新時間)
```

### 5.3 資料傳遞方式

採用內嵌 JSON 資料到 `<script>` 標籤中，不需額外的 HTTP 請求：

```html
<script>
  window.CHANNEL_DATA = [
    {
      "id": "ai_guoman", "name": "AIguoman18", "mode": "media",
      "media": [{"type":"photo","path":"photo/xxx.jpg"}, ...]
    },
    {
      "id": "dashijian", "name": "華人大事件", "mode": "text",
      "messages": [{"id":123,"date":"...","text":"...","media":[...]}, ...]
    }
  ];
</script>
```

### 5.4 視覺設計

- 深色背景 + 卡片式佈局
- 新聞卡片：日期標籤 → 文字段落 → 圖片縮圖網格
- 媒體展示：CSS Grid 瀑布流
- 圖片點擊放大（純 CSS/JS lightbox，無外部依賴）
- 影片使用 HTML5 `<video>` 標籤
- 響應式：桌面 3 欄 → 平板 2 欄 → 手機 1 欄

---

## 6. 目錄遷移策略

v1 的 `download/photo/` `download/video/` 遷移至 `download/ai_guoman/` 下：

```
download/photo/*.jpg  →  download/ai_guoman/photo/*.jpg
download/video/*.mp4  →  download/ai_guoman/video/*.mp4
download/.downloaded_state.json  →  download/ai_guoman/.downloaded_state.json
```

提供一次性遷移腳本 `src/migrate_v1_to_v2.py`。

---

## 7. 關鍵設計取捨

| 決策 | 理由 |
|------|------|
| JSONL 而非 JSON 陣列 | 逐行附加無需讀取整個檔案再寫回，適合增量寫入 |
| 內嵌資料而非 fetch | 靜態 HTML 無法發起 fetch 請求（`file://` 協定的 CORS 限制） |
| 頻道設定檔與 API 憑證分離 | `channels.json` 可提交到 git，`~/.tg_downloader_config.json` 不可 |
| 每個頻道獨立目錄 | 避免媒體檔案檔名衝突，方便手動管理 |
| 無前端框架 | 純 HTML/CSS/JS，零依賴，雙擊即開 |
