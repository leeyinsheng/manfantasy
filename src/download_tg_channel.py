import os
import subprocess
import asyncio
import tempfile
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from tg_core import (
    load_config,
    load_channels,
    load_state,
    save_state,
    load_messages,
    get_channel_dir,
    get_photo_dir,
    get_video_dir,
    generate_photo_filename,
    get_original_filename,
    is_video_mime,
    generate_document_filename,
    classify_media,
    append_id_to_filename,
    message_to_record,
    append_message_record,
)
import oss_uploader

TMP_DIR = Path(tempfile.gettempdir()) / "adult_dream"
OSS_CONFIG = oss_uploader.load_oss_config()
USE_OSS = bool(OSS_CONFIG)


async def download_media_message(message, channel_id, client, video_only=False):
    media = message.media
    is_photo = isinstance(media, MessageMediaPhoto)
    is_document = isinstance(media, MessageMediaDocument)
    mime_type = media.document.mime_type if is_document else ""
    media_type, _ = classify_media(is_photo, is_document, mime_type)

    photo_dir = get_photo_dir(channel_id)
    video_dir = get_video_dir(channel_id)
    media_files = []

    if media_type == "photo":
        if video_only:
            return []
        filename = generate_photo_filename(message.date, message.id)
        if USE_OSS:
            return await _download_to_oss(message, channel_id, filename, "photo", client)
        filepath = photo_dir / filename
        try:
            photo_dir.mkdir(parents=True, exist_ok=True)
            await client.download_media(message, file=str(filepath))
            kb = os.path.getsize(filepath) / 1024
            print(f"  [OK] 圖片: {filename} ({kb:.0f}KB)")
            media_files.append({"type": "photo", "path": f"{channel_id}/photo/{filename}", "size_kb": round(kb)})
        except Exception as e:
            print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

    elif media_type == "document":
        original_name = get_original_filename(message.media.document.attributes)
        filename = generate_document_filename(message.date, message.id, original_name, mime_type)

        if USE_OSS:
            target_dir = video_dir if is_video_mime(mime_type) else photo_dir
            subdir = "video" if is_video_mime(mime_type) else "photo"
            return await _download_to_oss(message, channel_id, filename, subdir, client)

        target_dir = video_dir if is_video_mime(mime_type) else photo_dir
        filepath = target_dir / filename
        if filepath.exists():
            filename = append_id_to_filename(filename, message.id)
            filepath = target_dir / filename

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            await client.download_media(message, file=str(filepath))
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            is_video = is_video_mime(mime_type)
            label = "影片" if is_video else "圖片" if mime_type.startswith("image/") else "檔案"
            subdir = "video" if is_video else "photo"
            thumb = ""
            if is_video:
                thumb_dir = video_dir / ".thumb"
                raw_name = Path(filename).stem
                thumb_name = f".thumb_{raw_name}.jpg"
                thumb_path = _generate_thumbnail_video(filepath, thumb_dir, thumb_name)
                if thumb_path:
                    thumb = f"{channel_id}/video/.thumb/{thumb_name}"
            print(f"  [OK] {label}: {filename} ({size_mb:.1f}MB)")
            record = {"type": "video" if is_video else "photo", "path": f"{channel_id}/{subdir}/{filename}", "size_mb": round(size_mb, 1)}
            if thumb:
                record["thumb"] = thumb
            media_files.append(record)
        except Exception as e:
            print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

    elif media_type == "unknown":
        print(f"  [SKIP] 未知媒體類型 msg#{message.id}")

    return media_files


async def _download_to_oss(message, channel_id, filename, subdir, client):
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = TMP_DIR / f"{channel_id}_{filename}"
    try:
        await client.download_media(message, file=str(tmp_path))
        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        oss_key = f"{channel_id}/{subdir}/{filename}"
        oss_url = oss_uploader.upload_file(OSS_CONFIG, str(tmp_path), oss_key)
        tmp_path.unlink()

        label = "影片" if subdir == "video" else "圖片"
        print(f"  [OK] {label}: {filename} ({size_mb:.1f}MB) → OSS")

        record = {
            "type": "video" if subdir == "video" else "photo",
            "path": oss_url,
            "size_mb": round(size_mb, 1),
        }
        if subdir == "video":
            thumb_url = _generate_thumbnail_oss(str(tmp_path), channel_id, filename)
            if thumb_url:
                record["thumb"] = thumb_url
        return [record]
    except Exception as e:
        print(f"  [ERR] OSS 上傳失敗 msg#{message.id}: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return []


def _generate_thumbnail_video(video_path, thumb_dir, thumb_name):
    thumb_path = thumb_dir / thumb_name
    if thumb_path.exists():
        return str(thumb_path)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", "1", "-i", str(video_path),
            "-vf", "thumbnail=15", "-vframes", "1",
            str(thumb_path)
        ], check=True, timeout=30)
        if thumb_path.exists():
            return str(thumb_path)
    except Exception:
        pass
    return None


def _generate_thumbnail_oss(video_path, channel_id, filename):
    try:
        thumb_name = f".thumb_{Path(filename).stem}.jpg"
        thumb_path = TMP_DIR / thumb_name
        result = subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", "1", "-i", str(video_path),
            "-vf", "thumbnail=15", "-vframes", "1",
            str(thumb_path)
        ], check=False, timeout=30)
        if result.returncode == 0 and thumb_path.exists():
            oss_key = f"{channel_id}/video/.thumb/{thumb_name}"
            thumb_url = oss_uploader.upload_file(OSS_CONFIG, str(thumb_path), oss_key)
            thumb_path.unlink()
            return thumb_url
    except Exception:
        pass
    return None


def _get_existing_media_records(message, channel_id):
    if USE_OSS:
        return []
    media = message.media
    if not media:
        return []
    is_photo = isinstance(media, MessageMediaPhoto)
    is_document = isinstance(media, MessageMediaDocument)
    mime_type = media.document.mime_type if is_document else ""
    media_type, _ = classify_media(is_photo, is_document, mime_type)
    photo_dir = get_photo_dir(channel_id)
    video_dir = get_video_dir(channel_id)

    if media_type == "photo":
        filename = generate_photo_filename(message.date, message.id)
        filepath = photo_dir / filename
        if filepath.exists():
            kb = os.path.getsize(filepath) / 1024
            return [{"type": "photo", "path": f"{channel_id}/photo/{filename}", "size_kb": round(kb)}]

    elif media_type == "document":
        original_name = get_original_filename(message.media.document.attributes)
        filename = generate_document_filename(message.date, message.id, original_name, mime_type)
        target_dir = video_dir if is_video_mime(mime_type) else photo_dir
        filepath = target_dir / filename
        if not filepath.exists():
            alt_name = append_id_to_filename(filename, message.id)
            alt_path = target_dir / alt_name
            if alt_path.exists():
                filepath = alt_path
                filename = alt_name
        if filepath.exists():
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            is_vid = is_video_mime(mime_type)
            subdir = "video" if is_vid else "photo"
            record = {
                "type": "video" if is_vid else "photo",
                "path": f"{channel_id}/{subdir}/{filename}",
                "size_mb": round(size_mb, 1)
            }
            if is_vid:
                thumb_dir = video_dir / ".thumb"
                raw_name = Path(filename).stem
                thumb_name = f".thumb_{raw_name}.jpg"
                thumb_path = _generate_thumbnail_video(filepath, thumb_dir, thumb_name)
                if thumb_path:
                    record["thumb"] = f"{channel_id}/video/.thumb/{thumb_name}"
            return [record]

    return []


async def process_channel(channel, client):
    channel_id = channel["id"]
    channel_username = channel["username"]
    channel_mode = channel.get("mode", "media")
    fetch_limit = channel.get("fetch_limit", 50)
    backfill = channel.get("backfill", False)

    print(f"\n=== {channel['name']} (@{channel_username}) ===")

    try:
        entity = await client.get_entity(channel_username)
    except Exception as e:
        print(f"無法存取頻道 {channel_username}: {e}")
        return

    get_channel_dir(channel_id).mkdir(parents=True, exist_ok=True)

    downloaded = load_state(channel_id)
    max_downloaded = max(downloaded) if downloaded else 0
    new_count = 0
    backfill_count = 0

    async for message in client.iter_messages(entity, limit=fetch_limit):
        if not backfill and message.id <= max_downloaded:
            break
        if not backfill and message.id in downloaded:
            continue

        is_backfill_msg = backfill and message.id in downloaded
        media_files = []

        if channel_mode == "video":
            if not message.media:
                continue
            has_video = hasattr(message.media, 'document') and hasattr(message.media.document, 'mime_type') and message.media.document.mime_type and message.media.document.mime_type.startswith('video/')
            if not has_video:
                continue

        if is_backfill_msg:
            media_files = _get_existing_media_records(message, channel_id)
        elif message.media:
            media_files = await download_media_message(message, channel_id, client, video_only=(channel_mode == "video"))
        elif channel_mode == "text" and not message.text and not getattr(message, "caption", None):
            continue

        if not is_backfill_msg:
            downloaded.add(message.id)
            save_state(channel_id, downloaded)
            new_count += 1

        if channel_mode == "text":
            record = message_to_record(message, channel_id, media_files)
            append_message_record(channel_id, record)
            if is_backfill_msg:
                backfill_count += 1
            text_preview = message.text or getattr(message, "caption", None) or ""
            if text_preview:
                preview = text_preview[:50].replace("\n", " ")
                label = "[BACKFILL] " if is_backfill_msg else ""
                print(f"  {label}[OK] 訊息: {preview}...")
            else:
                label = "[BACKFILL] " if is_backfill_msg else ""
                print(f"  {label}[OK] 媒體訊息 msg#{message.id}")

    if backfill_count:
        print(f"文字回溯完成: {backfill_count} 筆")
    print(f"完成！新增: {new_count} 個，總計: {len(downloaded)} 個")


async def main():
    import os
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    phone = config.get("phone")

    client = TelegramClient(str(Path.home() / ".tg_downloader_session"), api_id, api_hash)
    password = config.get("password", "")
    code = os.environ.get("TG_CODE")
    cb = (lambda: code) if code else None
    await client.start(phone=phone, password=password, code_callback=cb)

    me = await client.get_me()
    print(f"已登入: {me.first_name}")

    channels = load_channels()
    if not channels:
        print("無頻道設定，請檢查 src/channels.json")
        return

    tasks = [process_channel(channel, client) for channel in channels]
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for channel, result in zip(channels, results):
            if isinstance(result, Exception):
                print(f"頻道 {channel['name']} 錯誤: {result}")

    await client.disconnect()

    try:
        import generate_html
        generate_html.generate()
    except ImportError:
        print("[WARN] 無法載入 generate_html 模組，跳過網頁生成")


if __name__ == "__main__":
    asyncio.run(main())
