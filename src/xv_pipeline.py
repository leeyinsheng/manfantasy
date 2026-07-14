"""Pipeline: spider crawl → download pending videos → OSS upload."""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "download"
XV_DIR = DOWNLOAD_DIR / "xvideos"
XV_VIDEOS_FILE = XV_DIR / "videos.jsonl"

TMP_DIR = Path("/tmp/adult_dream_xv")
VENV_PYTHON = str(PROJECT_DIR / ".venv" / "bin" / "python3")
if not Path(VENV_PYTHON).exists():
    VENV_PYTHON = "python3"

import oss_uploader
OSS_CONFIG = oss_uploader.load_oss_config()
USE_OSS = bool(OSS_CONFIG)

import xv_spider


def get_pending_entries():
    if not XV_VIDEOS_FILE.exists():
        return []
    entries = []
    with open(XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not entry.get("media_path"):
                entries.append(entry)
    return entries


def build_video_url(entry):
    eid = entry.get("eid", "")
    video_id = entry.get("video_id", "")
    path = f"video.{eid}"
    if video_id:
        path += f"/{video_id}"
    return f"https://www.xvideos.com/{path}/"


def _download_single(url, tag=""):
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        meta_result = subprocess.run([
            VENV_PYTHON, "-m", "yt_dlp",
            "--dump-json", "--no-download",
            url,
        ], capture_output=True, text=True, timeout=60)
        if meta_result.returncode != 0 or not meta_result.stdout.strip():
            print(f"  [ERR] yt-dlp metadata failed: {url}")
            return None
        meta = json.loads(meta_result.stdout.strip().split("\n")[-1])
        video_id = meta.get("id", "")

        out_path = TMP_DIR / f"{video_id}.mp4"
        subprocess.run([
            VENV_PYTHON, "-m", "yt_dlp",
            "-f", "best[height<=720]",
            "-o", str(out_path),
            url,
        ], capture_output=True, check=True, timeout=300)

        return meta
    except Exception as e:
        print(f"  [ERR] yt-dlp failed: {e}")
        return None


def _upload_to_oss(local_path, oss_key):
    try:
        oss_url = oss_uploader.upload_file(OSS_CONFIG, str(local_path), oss_key)
        local_path.unlink(missing_ok=True)
        return oss_url
    except Exception as e:
        print(f"  [ERR] OSS upload failed: {e}")
        local_path.unlink(missing_ok=True)
        return None


def download_entry(entry):
    eid = entry.get("eid", "")
    if not eid:
        return None
    url = build_video_url(entry)
    tag = (entry.get("tags") or ["unknown"])[0]

    print(f"[pipeline] Downloading: {url}")
    meta = _download_single(url, tag)
    if not meta:
        return None

    video_id = meta.get("id", "")
    local_file = TMP_DIR / f"{video_id}.mp4"
    if not local_file.exists():
        print(f"  [WARN] File not found: {local_file}")
        return None

    size_mb = local_file.stat().st_size / (1024 * 1024)
    title = meta.get("title", "")
    duration = meta.get("duration", 0)
    mins = duration // 60
    secs = duration % 60
    duration_str = f"{mins}:{secs:02d}"

    oss_url = None
    if USE_OSS:
        oss_key = f"xvideos/{video_id}.mp4"
        oss_url = _upload_to_oss(local_file, oss_key)
    else:
        local_dest = XV_DIR / "media" / f"{video_id}.mp4"
        local_dest.parent.mkdir(parents=True, exist_ok=True)
        local_file.rename(local_dest)
        oss_url = f"xvideos/media/{video_id}.mp4"
        print(f"  [OK] {title[:40]} ({size_mb:.1f}MB) → local")

    if not oss_url:
        return None

    print(f"  [OK] {title[:40]} ({size_mb:.1f}MB) → OSS")

    return {
        "media_path": oss_url,
        "title": title,
        "duration": duration_str,
        "thumbnail": meta.get("thumbnail", entry.get("thumbnail", "")),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def update_entry(eid, **fields):
    if not XV_VIDEOS_FILE.exists():
        return
    entries = []
    with open(XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("eid") == eid:
                entry.update(fields)
            entries.append(entry)
    with open(XV_VIDEOS_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def download_pending(max_downloads=5):
    pending = get_pending_entries()
    if not pending:
        print("[pipeline] No pending videos to download.")
        return 0

    print(f"[pipeline] {len(pending)} videos pending, downloading up to {max_downloads}")
    count = 0
    for entry in pending[:max_downloads]:
        result = download_entry(entry)
        if result:
            update_entry(entry["eid"],
                         media_path=result["media_path"],
                         title=result.get("title", entry.get("title", "")),
                         duration=result.get("duration", entry.get("duration", "")),
                         thumbnail=result.get("thumbnail", entry.get("thumbnail", "")),
                         fetched_at=result["fetched_at"])
            count += 1
            time.sleep(2)

    print(f"[pipeline] Done. {count} videos downloaded.")
    return count


def run_pipeline(max_downloads=5):
    print("=" * 50)
    print("[pipeline] Phase 1: Spider crawl")
    print("=" * 50)
    new_meta = xv_spider.crawl()
    print(f"[pipeline] Spider found {new_meta} new entries")

    print("=" * 50)
    print("[pipeline] Phase 2: Download pending")
    print("=" * 50)
    downloaded = download_pending(max_downloads=max_downloads)

    print("=" * 50)
    print(f"[pipeline] Complete. {new_meta} new metadata, {downloaded} downloaded.")
    print("=" * 50)
    return downloaded


if __name__ == "__main__":
    max_dl = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_pipeline(max_downloads=max_dl)
