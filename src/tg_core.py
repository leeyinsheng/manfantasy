import json
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CONFIG_FILE = Path.home() / ".tg_downloader_config.json"
PHOTO_DIR = PROJECT_DIR / "download" / "photo"
VIDEO_DIR = PROJECT_DIR / "download" / "video"
STATE_FILE = PROJECT_DIR / "download" / ".downloaded_state.json"


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def load_state():
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            if isinstance(data, list):
                return set(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return set()


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(state), indent=2))


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
