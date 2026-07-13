"""Upload media files to Alibaba Cloud OSS."""
import json
import os
from pathlib import Path
from urllib.parse import quote

try:
    import oss2
except ImportError:
    oss2 = None

PROJECT_DIR = Path(__file__).parent.parent
OSS_CONFIG_FILE = Path(__file__).parent / "oss_config.json"


def load_oss_config():
    if not OSS_CONFIG_FILE.exists():
        return {}
    try:
        config = json.loads(OSS_CONFIG_FILE.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, ValueError):
        return {}

    access_key_id = os.environ.get("OSS_KEY_ID", config.get("access_key_id", ""))
    access_key_secret = os.environ.get("OSS_KEY_SECRET", config.get("access_key_secret", ""))
    config["access_key_id"] = access_key_id
    config["access_key_secret"] = access_key_secret

    if "public_url" not in config:
        endpoint = config.get("endpoint", "")
        bucket = config.get("bucket", "")
        if endpoint.startswith("https://"):
            host = endpoint[8:]
            config["public_url"] = f"https://{bucket}.{host}"
        else:
            config["public_url"] = f"https://{bucket}.{endpoint}"
    return config


def get_oss_url(config, oss_key):
    public_url = config.get("public_url", "")
    key = oss_key.lstrip("/")
    safe_key = quote(key, safe="/")
    return f"{public_url}/{safe_key}"


def _get_bucket(config):
    if oss2 is None:
        raise ImportError("oss2 is not installed. Run: pip install oss2")
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    return oss2.Bucket(auth, config["endpoint"], config["bucket"])


def upload_file(config, local_path, oss_key):
    bucket = _get_bucket(config)
    bucket.put_object_from_file(oss_key, local_path)
    return get_oss_url(config, oss_key)


def upload_media(config, local_path, channel_id, filename, subdir):
    oss_key = f"{channel_id}/{subdir}/{filename}"
    return upload_file(config, local_path, oss_key)
