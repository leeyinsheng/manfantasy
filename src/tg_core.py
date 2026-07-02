import json
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CONFIG_FILE = Path.home() / ".tg_downloader_config.json"
DOWNLOAD_DIR = PROJECT_DIR / "download"
CHANNELS_FILE = Path(__file__).parent / "channels.json"


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def load_channels():
    if CHANNELS_FILE.exists():
        try:
            data = json.loads(CHANNELS_FILE.read_text(encoding="utf-8-sig"))
            return data.get("channels", [])
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def get_channel_dir(channel_id):
    return DOWNLOAD_DIR / channel_id


def get_photo_dir(channel_id):
    return get_channel_dir(channel_id) / "photo"


def get_video_dir(channel_id):
    return get_channel_dir(channel_id) / "video"


def get_state_file(channel_id):
    return get_channel_dir(channel_id) / ".downloaded_state.json"


def get_messages_file(channel_id):
    return get_channel_dir(channel_id) / "messages.jsonl"


def load_state(channel_id):
    state_file = get_state_file(channel_id)
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return set()


def save_state(channel_id, state):
    state_file = get_state_file(channel_id)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(sorted(state), indent=2))


def extract_message_text(message):
    text = getattr(message, "text", None) or getattr(message, "caption", None) or ""
    return text.strip()


def message_to_record(message, channel_id, media_files):
    return {
        "id": message.id,
        "date": message.date.isoformat(),
        "text": extract_message_text(message),
        "channel": channel_id,
        "media": media_files,
    }


def append_message_record(channel_id, record):
    messages_file = get_messages_file(channel_id)
    messages_file.parent.mkdir(parents=True, exist_ok=True)
    with open(messages_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_messages(channel_id):
    messages_file = get_messages_file(channel_id)
    records = []
    if messages_file.exists():
        with open(messages_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
    return records


def generate_photo_filename(message_date, message_id):
    date_prefix = message_date.strftime("%Y%m%d_%H%M%S")
    return f"{date_prefix}_photo_{message_id}.jpg"


def get_original_filename(attributes):
    for attr in attributes:
        if hasattr(attr, 'file_name') and attr.file_name:
            return attr.file_name
    return ""


def mime_to_extension(mime_type):
    if mime_type.startswith("video/"):
        return ".mp4"
    if mime_type.startswith("image/"):
        return ".jpg"
    return ".bin"


def is_video_mime(mime_type):
    return mime_type.startswith("video/")


def generate_document_filename(message_date, message_id, original_name, mime_type):
    if original_name:
        return original_name.strip()
    ext = mime_to_extension(mime_type)
    date_prefix = message_date.strftime("%Y%m%d_%H%M%S")
    return f"{date_prefix}_media_{message_id}{ext}"


def classify_media(is_photo, is_document, mime_type=""):
    if is_photo and is_document:
        raise ValueError("Media cannot be both photo and document")
    if is_photo:
        return ("photo", None)
    if is_document:
        return ("document", mime_type or "")
    return ("unknown", None)


def append_id_to_filename(filename, message_id):
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    return f"{stem}_{message_id}{suffix}"
