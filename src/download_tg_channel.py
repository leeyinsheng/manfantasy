import os
import asyncio
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


async def download_media_message(message, channel_id, client):
    media = message.media
    is_photo = isinstance(media, MessageMediaPhoto)
    is_document = isinstance(media, MessageMediaDocument)
    mime_type = media.document.mime_type if is_document else ""
    media_type, _ = classify_media(is_photo, is_document, mime_type)

    photo_dir = get_photo_dir(channel_id)
    video_dir = get_video_dir(channel_id)
    media_files = []

    if media_type == "photo":
        filename = generate_photo_filename(message.date, message.id)
        filepath = photo_dir / filename
        try:
            photo_dir.mkdir(parents=True, exist_ok=True)
            await client.download_media(message, file=str(filepath))
            kb = os.path.getsize(filepath) / 1024
            print(f"  [OK] 圖片: {filename} ({kb:.0f}KB)")
            media_files.append({"type": "photo", "path": f"photo/{filename}", "size_kb": round(kb)})
        except Exception as e:
            print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

    elif media_type == "document":
        original_name = get_original_filename(message.media.document.attributes)
        filename = generate_document_filename(message.date, message.id, original_name, mime_type)

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
            print(f"  [OK] {label}: {filename} ({size_mb:.1f}MB)")
            media_files.append({"type": "video" if is_video else "photo", "path": f"{subdir}/{filename}", "size_mb": round(size_mb, 1)})
        except Exception as e:
            print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

    elif media_type == "unknown":
        print(f"  [SKIP] 未知媒體類型 msg#{message.id}")

    return media_files


async def process_channel(channel, client):
    channel_id = channel["id"]
    channel_username = channel["username"]
    channel_mode = channel.get("mode", "media")
    fetch_limit = channel.get("fetch_limit", 50)

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

    async for message in client.iter_messages(entity, limit=fetch_limit):
        if message.id <= max_downloaded:
            break
        if message.id in downloaded:
            continue

        media_files = []
        if message.media:
            media_files = await download_media_message(message, channel_id, client)
        elif channel_mode == "text" and not message.text and not message.caption:
            continue

        downloaded.add(message.id)
        save_state(channel_id, downloaded)
        new_count += 1

        if channel_mode == "text":
            record = message_to_record(message, channel_id, media_files)
            append_message_record(channel_id, record)
            text_preview = message.text or message.caption or ""
            if text_preview:
                preview = text_preview[:50].replace("\n", " ")
                print(f"  [OK] 訊息: {preview}...")
            else:
                print(f"  [OK] 媒體訊息 msg#{message.id}")

    print(f"完成！新增: {new_count} 個，總計: {len(downloaded)} 個")


async def main():
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")

    client = TelegramClient(str(Path.home() / ".tg_downloader_session"), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("NEEDS_AUTH")
        return

    me = await client.get_me()
    print(f"已登入: {me.first_name}")

    channels = load_channels()
    if not channels:
        print("無頻道設定，請檢查 src/channels.json")
        return

    for channel in channels:
        await process_channel(channel, client)

    await client.disconnect()

    try:
        import generate_html
        generate_html.generate()
    except ImportError:
        print("[WARN] 無法載入 generate_html 模組，跳過網頁生成")


if __name__ == "__main__":
    asyncio.run(main())
