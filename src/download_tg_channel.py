import os
import asyncio
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from tg_core import (
    load_config,
    load_state,
    save_state,
    generate_photo_filename,
    get_original_filename,
    is_video_mime,
    generate_document_filename,
    classify_media,
    append_id_to_filename,
    PHOTO_DIR,
    VIDEO_DIR,
)

CHANNEL_USERNAME = "AIguoman18"
FETCH_LIMIT = 50


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

    try:
        entity = await client.get_entity(CHANNEL_USERNAME)
    except Exception as e:
        print(f"無法存取頻道 {CHANNEL_USERNAME}: {e}")
        return

    downloaded = load_state()
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    max_downloaded = max(downloaded) if downloaded else 0
    new_count = 0

    async for message in client.iter_messages(entity, limit=FETCH_LIMIT):
        if message.id <= max_downloaded:
            break
        if not message.media:
            continue
        if message.id in downloaded:
            continue

        media = message.media
        is_photo = isinstance(media, MessageMediaPhoto)
        is_document = isinstance(media, MessageMediaDocument)
        mime_type = media.document.mime_type if is_document else ""

        media_type, _ = classify_media(is_photo, is_document, mime_type)

        if media_type == "photo":
            filename = generate_photo_filename(message.date, message.id)
            filepath = PHOTO_DIR / filename
            try:
                await client.download_media(message, file=str(filepath))
                downloaded.add(message.id)
                save_state(downloaded)
                new_count += 1
                kb = os.path.getsize(filepath) / 1024
                print(f"  [OK] 圖片: {filename} ({kb:.0f}KB)")
            except Exception as e:
                print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

        elif media_type == "document":
            original_name = get_original_filename(message.media.document.attributes)
            filename = generate_document_filename(message.date, message.id, original_name, mime_type)

            target_dir = VIDEO_DIR if is_video_mime(mime_type) else PHOTO_DIR
            filepath = target_dir / filename
            if filepath.exists():
                filename = append_id_to_filename(filename, message.id)
                filepath = target_dir / filename

            try:
                await client.download_media(message, file=str(filepath))
                downloaded.add(message.id)
                save_state(downloaded)
                new_count += 1
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                label = "影片" if is_video_mime(mime_type) else "圖片" if mime_type.startswith("image/") else "檔案"
                print(f"  [OK] {label}: {filename} ({size_mb:.1f}MB)")
            except Exception as e:
                print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

        else:
            print(f"  [SKIP] 未知媒體類型 msg#{message.id}")

    print(f"\n完成！新增: {new_count} 個檔案，總計: {len(downloaded)} 個")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
