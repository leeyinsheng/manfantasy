"""Clean up messages and media older than 3 days."""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "download"
RETENTION_DAYS = 90


def _load_messages(file_path):
    messages = []
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
    return messages


def _save_messages(file_path, messages):
    with open(file_path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def _media_paths_from_message(msg, channel_id):
    paths = set()
    for media in msg.get("media", []):
        p = media.get("path", "")
        if not p:
            continue
        if not p.startswith(f"{channel_id}/"):
            p = f"{channel_id}/{p}"
        paths.add(DOWNLOAD_DIR / p)
        thumb = media.get("thumb", "")
        if thumb:
            if not thumb.startswith(f"{channel_id}/"):
                thumb = f"{channel_id}/{thumb}"
            paths.add(DOWNLOAD_DIR / thumb)
    return paths


def _delete_files(paths):
    deleted = 0
    for p in paths:
        if p.exists() and p.is_file():
            p.unlink()
            deleted += 1
    return deleted


def cleanup_channel(channel_id):
    msg_file = DOWNLOAD_DIR / channel_id / "messages.jsonl"
    if not msg_file.exists():
        return 0, 0

    messages = _load_messages(msg_file)
    if not messages:
        return 0, 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    cutoff_str = cutoff.isoformat()

    kept = []
    removed = 0
    deleted_files = 0

    for msg in messages:
        date = msg.get("date", "")
        if date and date > cutoff_str:
            kept.append(msg)
        else:
            paths = _media_paths_from_message(msg, channel_id)
            deleted_files += _delete_files(paths)
            removed += 1

    _save_messages(msg_file, kept)

    # also clean orphaned media files (not referenced by any kept message)
    referenced = set()
    for msg in kept:
        referenced |= _media_paths_from_message(msg, channel_id)

    for subdir in ("photo", "video"):
        d = DOWNLOAD_DIR / channel_id / subdir
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and f not in referenced:
                    f.unlink()
                    deleted_files += 1

    return removed, deleted_files


def cleanup_xvideos():
    xv_file = DOWNLOAD_DIR / "xvideos" / "videos.jsonl"
    if not xv_file.exists():
        return 0

    messages = _load_messages(xv_file)
    if not messages:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    cutoff_str = cutoff.isoformat()

    kept = [m for m in messages if m.get("fetched_at", "") and m["fetched_at"] > cutoff_str]
    removed = len(messages) - len(kept)

    _save_messages(xv_file, kept)
    return removed


def main():
    total_removed = 0
    total_files = 0

    for entry in DOWNLOAD_DIR.iterdir():
        if not entry.is_dir():
            continue
        msg_file = entry / "messages.jsonl"
        if msg_file.exists():
            removed, files = cleanup_channel(entry.name)
            if removed or files:
                print(f"[cleanup] {entry.name}: {removed} msgs, {files} files removed")
            total_removed += removed
            total_files += files

    xv_removed = cleanup_xvideos()
    if xv_removed:
        print(f"[cleanup] xvideos: {xv_removed} entries removed")
        total_removed += xv_removed

    print(f"[cleanup] total: {total_removed} messages, {total_files} files removed")


if __name__ == "__main__":
    main()
