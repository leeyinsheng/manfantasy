# 02 - Design v9：OSS 儲存層架構

## 資料流

```
Telegram API
    │
    v
download_tg_channel.py
    │
    ├── client.download_media() → 下載到本地暫存
    ├── oss.upload() → 上傳到 OSS
    ├── 記錄 OSS URL 到 messages.jsonl
    └── os.unlink() → 刪除本地暫存
    │
    v
messages.jsonl (media.path = OSS URL)
    │
    v
generate_html.py
    │
    ├── _normalize_media_paths() → 不需修改 (path 已是完整 URL)
    └── HTML 中 img/video src 直接使用 OSS URL
    │
    v
download/index.html
    │
    v
Nginx 只服務 HTML，媒體流量走 OSS
```

## 檔案變更

### 新增：`src/oss_config.json`

```json
{
  "endpoint": "https://oss-ap-southeast-7.aliyuncs.com",
  "bucket": "dream20260711",
  "access_key_id": "FROM_ENV_OSS_KEY_ID",
  "access_key_secret": "FROM_ENV_OSS_KEY_SECRET",
  "public_url": "https://dream20260711.oss-ap-southeast-7.aliyuncs.com"
}
```

### 新增：`src/oss_uploader.py`

```python
def load_oss_config():        # 讀取 oss_config.json
def upload_file(local_path, oss_key):  # 單檔上傳
def upload_media(channel_id, filename, subdir):  # 上傳並回傳 OSS URL
def get_oss_url(oss_key):     # 構建完整 OSS URL
```

### 變更：`src/download_tg_channel.py`

`download_media_message()` 函數改造：

```
Before:
  await client.download_media(message, file=str(filepath))
  media_files.append({"type": "photo", "path": f"{channel_id}/photo/{filename}"})

After:
  await client.download_media(message, file=str(tmp_path))
  oss_url = upload_media(channel_id, filename, "photo")
  os.unlink(tmp_path)
  media_files.append({"type": "photo", "path": oss_url})
```

同樣改造 `_generate_thumbnail()`（縮圖也上傳 OSS）。

### 變更：`src/generate_html.py`

不需改動 URL 邏輯。`_normalize_media_paths()` 目前檢查 `path.startswith(f"{channel_id}/")` 並加前綴 — 當 path 已是完整 OSS URL（以 `https://` 開頭）時，不會觸發前綴邏輯，無需修改。

唯一確認：卡片渲染 `cardImageHtml` 使用 `src = cover.thumb || cover.path`，直接作為 `<img src>` — OSS URL 可直接使用。

### 移除或簡化：`src/cleanup_old.py`

OSS 無容量限制，不需要定期清理。可移除或保留為 no-op。

## OSS 上傳流程

```python
# download_media_message 中的媒體處理流程

tmp_dir = Path("/tmp/adult_dream")
tmp_dir.mkdir(parents=True, exist_ok=True)
tmp_path = tmp_dir / filename

await client.download_media(message, file=str(tmp_path))  # 下載

oss_key = f"{channel_id}/{subdir}/{filename}"              # OSS key
oss_url = upload_file(str(tmp_path), oss_key)              # 上傳 OSS

tmp_path.unlink()                                          # 清理暫存

media_files.append({"type": ..., "path": oss_url})         # 記錄 OSS URL
```

縮圖同樣流程：

```python
thumb_path = ffmpeg_generate(video_path)
oss_thumb_url = upload_file(str(thumb_path), f"{channel_id}/video/.thumb/{thumb_name}")
thumb_path.unlink()
```

## messages.jsonl 格式變更

```
Before:
{"path": "ai_guoman/photo/2025-07-01_test.jpg"}

After:
{"path": "https://dream20260711.oss-ap-southeast-7.aliyuncs.com/ai_guoman/photo/2025-07-01_test.jpg"}
```

## 測試策略

| 測試項目 | 說明 |
|---------|------|
| `test_oss_config_loading` | 驗證 oss_config.json 讀取 |
| `test_oss_url_building` | `get_oss_url("ai_guoman/photo/test.jpg")` → 完整 URL |
| `test_normalize_skips_oss_url` | _normalize_media_paths 不修改 https:// 開頭的 path |
| `test_upload_media` | Mock OSS client，驗證上傳後回傳正確 URL |
| 既有測試 | 確保 _normalize_media_paths 行為對 OSS URL 正確 |

## What Changes

| 檔案 | 變更 |
|------|------|
| `src/oss_config.json` | **新增** — OSS 連線設定 |
| `src/oss_uploader.py` | **新增** — OSS 上傳模組 |
| `src/download_tg_channel.py` | 下載後上傳 OSS → 記錄 OSS URL → 清理暫存 |
| `src/generate_html.py` | 不變（OSS URL 直接可用） |
| `src/cleanup_old.py` | 移除或 no-op |
| `tests/` | 新增 OSS 相關測試 |
