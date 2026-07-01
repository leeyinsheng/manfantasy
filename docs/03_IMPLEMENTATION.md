# 03 - 實作摘要

## 模組結構

```
src/
├── tg_core.py                  ← 純邏輯函式（無外部依賴）
└── download_tg_channel.py      ← 主流程（依賴 telethon、tg_core）

tests/
├── test_filename.py            ← 檔案命名 + MIME 工具函式測試
├── test_media.py               ← 媒體分類邏輯測試
└── test_state.py               ← 設定檔與狀態檔 I/O 測試
```

## 重構重點

將原始 `download_tg_channel.py` 中的內聯邏輯抽取為 `tg_core.py` 的獨立函式：

| 函式 | 職責 | 可測試性 |
|------|------|----------|
| `generate_photo_filename()` | 產生圖片檔名 | 純函式，無副作用 |
| `generate_document_filename()` | 產生文件檔名（含原始名稱/備用命名） | 純函式 |
| `get_original_filename()` | 從文件屬性中提取原始檔名 | 純函式 |
| `mime_to_extension()` | MIME 類型對應副檔名 | 純函式 |
| `is_video_mime()` | 判斷是否為影片 MIME | 純函式 |
| `classify_media()` | 媒體類型分類 | 純函式 |
| `append_id_to_filename()` | 檔名衝突時附加訊息 ID | 純函式 |
| `load_config()` | 讀取 API 設定檔 | 檔案 I/O |
| `load_state()` | 讀取下載狀態檔 | 檔案 I/O |
| `save_state()` | 寫入下載狀態檔 | 檔案 I/O |

## 測試覆蓋

共 **32 個測試案例**，分布如下：

| 測試檔案 | 類別 | 案例數 |
|----------|------|--------|
| `test_filename.py` | `TestPhotoFilename` | 2 |
| | `TestDocumentFilename` | 5 |
| | `TestGetOriginalFilename` | 4 |
| | `TestMimeToExtension` | 3 |
| | `TestIsVideoMime` | 2 |
| | `TestAppendIdToFilename` | 3 |
| `test_media.py` | `TestClassifyMedia` | 6 |
| `test_state.py` | `TestLoadConfig` | 2 |
| | `TestLoadState` | 3 |
| | `TestSaveState` | 2 |

## 設計取捨

- **未做整合測試**：`main()` 依賴 Telethon API 連線，需要真實 Telegram 憑證。整合測試成本高，實務上透過排程日誌進行驗證。
- **未引入 mock 框架**：僅使用 `unittest` 標準庫，避免增加依賴。
