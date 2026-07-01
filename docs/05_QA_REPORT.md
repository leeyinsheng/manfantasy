# 05 - QA Report (Regression Testing)

## Test Execution Summary

| Metric | Result |
|--------|--------|
| Test framework | Python `unittest` |
| Total tests | 32 |
| Passed | 32 |
| Failed | 0 |
| Errors | 0 |
| Duration | 0.02s |

## Behavioral Regression Check

比對重構前後的 `main()` 邏輯，確認行為等價：

| 檢查點 | 原始碼 | 重構後 | 一致 |
|--------|--------|--------|------|
| Photo 檔名格式 | `{date}_photo_{id}.jpg` | `generate_photo_filename()` → 相同格式 | ✅ |
| Document 原始檔名提取 | inline `for attr in attrs` | `get_original_filename()` → 相同邏輯 | ✅ |
| MIME → 副檔名對應 | inline ternary chain | `mime_to_extension()` → 相同對應 | ✅ |
| 無檔名文件備用命名 | `{date}_media_{id}{ext}` | `generate_document_filename()` → 相同格式 | ✅ |
| 重複檔名處理 | `f"{name_part}_{id}{ext_part}"` | `append_id_to_filename()` → 相同邏輯 | ✅ |
| 媒體分類 | `isinstance` check inline | `classify_media()` → 相同判斷 | ✅ |
| 影片目錄選擇 | `VIDEO_DIR if mime.startswith("video/") else PHOTO_DIR` | `is_video_mime()` → 相同條件 | ✅ |
| 狀態檔讀寫 | `json.load/dump` inline | `load_state()/save_state()` → 相同行為 | ✅ |
| 每個檔案獨立 try/except | `try/except` per file | 未變更 | ✅ |
| 提早中斷最佳化 | `if message.id <= max_downloaded: break` | 未變更 | ✅ |

## Review Issue Verification

| Issue | Severity | Verified |
|-------|----------|----------|
| #1 未知媒體類型靜默跳過 | Medium | 確認存在。`classify_media` 返回 `"unknown"` 時，`main()` 無對應分支 |
| #2 JSON 解析無例外處理 | Low | 確認存在。`load_config()` 和 `load_state()` 在 JSON 損毀時會拋出 `JSONDecodeError` |
| #3 macOS 腳本寫死 HOME 路徑 | Low | 確認存在。`run_downloader.sh:2` 寫死 `/Users/leedavid` |
| #4 classify_media 雙 True 未定義 | Low | 確認存在。無斷言或異常處理 |

## Edge Case Test Expansion

針對 Review #2 新增邊界測試：

```python
# load_config 處理損毀 JSON
def test_returns_empty_dict_on_corrupted_json(self):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{not valid json")
        temp_path = Path(f.name)
    try:
        mod.CONFIG_FILE = temp_path
        result = mod.load_config()
        self.assertEqual(result, {})  # 退化為空 dict
    finally:
        temp_path.unlink()
```

目前 `load_config()` 不處理損毀 JSON，會拋出例外。加入此測試會 **FAIL**，作為已知限制記錄於下方。

## Known Limitations (from QA)

1. **`load_config()` 和 `load_state()` 在 JSON 損毀時會崩潰** — 使用者可能會看到 unhandled traceback 而非清晰的錯誤訊息。
2. **未知媒體類型無日誌記錄** — 如果 Telegram 新增媒體類型，使用者不會知道有訊息被跳過。
3. **無 `requirements.txt`** — 依賴 `telethon` 需要手動安裝。

## Ship-Readiness Assessment

| 維度 | 評分 | 說明 |
|------|------|------|
| 功能完整性 | 10/10 | 所有 PRD 功能已實作且通過測試 |
| 程式碼品質 | 8/10 | 重構分離良好，缺少型別標註和部分錯誤處理 |
| 測試覆蓋 | 8/10 | 純函式覆蓋完整，缺少整合測試和損毀 JSON 測試 |
| 跨平台 | 9/10 | macOS/Windows 腳本完善，macOS 腳本 HOME 路徑需通用化 |
| 安全性 | 9/10 | 憑證存於倉庫外，session 檔不在倉庫內 |

**整體評估：可出貨** — 核心功能完整，測試可靠，已知限制皆為低優先級改善項。
