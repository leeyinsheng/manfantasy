"""Download xvideos videos via yt-dlp and upload to OSS."""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "download"
XV_DIR = DOWNLOAD_DIR / "xvideos"
XV_VIDEOS_FILE = XV_DIR / "videos.jsonl"
XV_URLS_FILE = Path(__file__).parent / "xv_video_urls.json"

TMP_DIR = Path("/tmp/adult_dream_xv")

import oss_uploader
OSS_CONFIG = oss_uploader.load_oss_config()
USE_OSS = bool(OSS_CONFIG)


def load_urls():
    if XV_URLS_FILE.exists():
        try:
            data = json.loads(XV_URLS_FILE.read_text(encoding="utf-8-sig"))
            return data.get("urls", [])
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def load_videos():
    videos = []
    if XV_VIDEOS_FILE.exists():
        with open(XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        videos.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
    return videos


def save_videos(videos):
    XV_DIR.mkdir(parents=True, exist_ok=True)
    with open(XV_VIDEOS_FILE, "w", encoding="utf-8") as f:
        for v in videos:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


def download_video(url):
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        meta_result = subprocess.run([
            "python3", "-m", "yt_dlp",
            "--dump-json", "--no-download",
            url,
        ], capture_output=True, text=True, timeout=60)
        if meta_result.returncode != 0 or not meta_result.stdout.strip():
            print(f"  [ERR] yt-dlp metadata failed")
            return None
        meta = json.loads(meta_result.stdout.strip().split("\n")[-1])
        video_id = meta.get("id", "")

        out_path = TMP_DIR / f"{video_id}.mp4"
        subprocess.run([
            "python3", "-m", "yt_dlp",
            "-f", "best[height<=720]",
            "-o", str(out_path),
            url,
        ], capture_output=True, check=True, timeout=300)

        return meta
    except Exception as e:
        print(f"  [ERR] yt-dlp failed: {e}")
        return None


def process_downloads():
    urls = load_urls()
    if not urls:
        print("[xv] No video URLs configured.")
        return

    videos = load_videos()
    existing_urls = {v.get("url", "") for v in videos}

    new_count = 0
    for url_info in urls:
        url = url_info.get("url", "")
        tag = url_info.get("tag", "")
        if url in existing_urls:
            continue

        print(f"[xv] Downloading: {url}")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        meta = download_video(url)
        if not meta:
            continue

        video_id = meta.get("id", "")
        title = meta.get("title", "")
        duration = meta.get("duration", 0)
        thumbnail = meta.get("thumbnail", "")

        local_file = TMP_DIR / f"{video_id}.mp4"
        if not local_file.exists():
            print(f"  [WARN] File not found: {local_file}")
            continue

        size_mb = local_file.stat().st_size / (1024 * 1024)

        if USE_OSS:
            oss_key = f"xvideos/{video_id}.mp4"
            try:
                oss_url = oss_uploader.upload_file(OSS_CONFIG, str(local_file), oss_key)
                local_file.unlink()
                print(f"  [OK] {title[:40]} ({size_mb:.1f}MB) → OSS")
            except Exception as e:
                print(f"  [ERR] OSS upload failed: {e}")
                local_file.unlink()
                continue
        else:
            xv_dir = XV_DIR / "media"
            xv_dir.mkdir(parents=True, exist_ok=True)
            dest = xv_dir / f"{video_id}.mp4"
            local_file.rename(dest)
            oss_url = f"xvideos/media/{video_id}.{ext}"
            print(f"  [OK] {title[:40]} ({size_mb:.1f}MB) → local")

        mins = duration // 60
        secs = duration % 60
        duration_str = f"{mins}:{secs:02d}"

        record = {
            "eid": video_id,
            "video_id": meta.get("display_id", video_id),
            "title": title,
            "duration": duration_str,
            "thumbnail": thumbnail,
            "uploader": tag,
            "url": url,
            "media_path": oss_url,
            "media_uploaded": True,
            "tags": [tag],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        videos.append(record)
        new_count += 1

    if new_count:
        save_videos(videos)
    print(f"[xv] Done. {new_count} new videos downloaded.")


if __name__ == "__main__":
    process_downloads()
