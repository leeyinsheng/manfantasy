import os
import json
import asyncio
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

PROJECT_DIR = Path(__file__).parent.parent
CONFIG_FILE = Path.home() / ".tg_downloader_config.json"
PHOTO_DIR = PROJECT_DIR / "download" / "photo"
VIDEO_DIR = PROJECT_DIR / "download" / "video"
STATE_FILE = PROJECT_DIR / "download" / ".downloaded_state.json"
CHANNEL_USERNAME = "AIguoman18"
FETCH_LIMIT = 50

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def load_state():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(state), indent=2))

async def main():
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    phone = config.get("phone")

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

        if is_photo:
            date_prefix = message.date.strftime("%Y%m%d_%H%M%S")
            filename = f"{date_prefix}_photo_{message.id}.jpg"
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

        elif is_document:
            mime = media.document.mime_type or ""
            attrs = media.document.attributes
            original_name = ""
            for attr in attrs:
                if hasattr(attr, 'file_name') and attr.file_name:
                    original_name = attr.file_name
                    break

            if original_name:
                name_clean = original_name.strip()
            else:
                ext = ".mp4" if mime.startswith("video/") else ".jpg" if mime.startswith("image/") else ".bin"
                date_prefix = message.date.strftime("%Y%m%d_%H%M%S")
                name_clean = f"{date_prefix}_media_{message.id}{ext}"

            is_video = mime.startswith("video/")
            target_dir = VIDEO_DIR if is_video else PHOTO_DIR
            filepath = target_dir / name_clean
            if filepath.exists():
                name_part = filepath.stem
                ext_part = filepath.suffix
                filepath = target_dir / f"{name_part}_{message.id}{ext_part}"

            try:
                await client.download_media(message, file=str(filepath))
                downloaded.add(message.id)
                save_state(downloaded)
                new_count += 1
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                label = "影片" if is_video else "圖片" if mime.startswith("image/") else "檔案"
                print(f"  [OK] {label}: {name_clean} ({size_mb:.1f}MB)")
            except Exception as e:
                print(f"  [ERR] 下載失敗 msg#{message.id}: {e}")

    print(f"\n完成！新增: {new_count} 個檔案，總計: {len(downloaded)} 個")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
