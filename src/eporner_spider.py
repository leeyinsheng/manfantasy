import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "download"
XV_DIR = DOWNLOAD_DIR / "xvideos"
XV_VIDEOS_FILE = XV_DIR / "videos.jsonl"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
REQUEST_DELAY = 1
DEFAULT_PAGES = 3
DEFAULT_CATEGORY = "amateur"


def _build_url(category, page):
    if page <= 1:
        return f"https://www.eporner.com/cat/{category}/"
    return f"https://www.eporner.com/cat/{category}/page-{page}/"


def _fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_video_blocks(html):
    block_re = re.compile(
        r'<div class="mb"[^>]*data-id="(\d+)"[^>]*>',
        re.DOTALL,
    )
    url_re = re.compile(r'href="(/video-([^"/]+)/[^"]*)"')
    title_re = re.compile(r'alt="([^"]*)"')
    thumb_re = re.compile(r'src="([^"]*)"')
    duration_re = re.compile(r'<span class="mbtim"[^>]*>([^<]+)</span>')
    quality_re = re.compile(r'<div class="mvhdico"[^>]*><span>([^<]+)</span></div>')
    views_re = re.compile(r'<span class="mbvie"[^>]*>([^<]+)</span>')
    uploader_re = re.compile(
        r'<span class="mb-uploader"><a[^>]*title="Uploader"[^>]*>([^<]+)</a></span>'
    )

    videos = []
    for match in block_re.finditer(html):
        video_id = int(match.group(1))
        chunk_end = min(len(html), match.end() + 2000)
        chunk = html[match.start():chunk_end]

        url_match = url_re.search(chunk)
        if not url_match:
            continue
        page_url = url_match.group(1)
        eid = url_match.group(2)

        title_match = title_re.search(chunk)
        title = title_match.group(1) if title_match else ""

        thumb_match = thumb_re.search(chunk)
        thumbnail = thumb_match.group(1) if thumb_match else ""

        duration_match = duration_re.search(chunk)
        duration = duration_match.group(1) if duration_match else ""

        quality_match = quality_re.search(chunk)
        quality = quality_match.group(1) if quality_match else ""

        views_match = views_re.search(chunk)
        views = views_match.group(1) if views_match else ""

        uploader_match = uploader_re.search(chunk)
        uploader = uploader_match.group(1) if uploader_match else ""

        videos.append({
            "eid": eid,
            "video_id": video_id,
            "title": title,
            "duration": duration,
            "views": views,
            "uploader": uploader,
            "thumbnail": thumbnail,
            "quality": quality,
            "page_url": page_url,
            "source": "eporner",
        })

    return videos


def load_existing_eids():
    eids = set()
    if XV_VIDEOS_FILE.exists():
        with open(XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        vid = json.loads(line)
                        eids.add(vid.get("eid", ""))
                    except (json.JSONDecodeError, ValueError):
                        pass
    return eids


def _append_videos(videos):
    XV_DIR.mkdir(parents=True, exist_ok=True)
    with open(XV_VIDEOS_FILE, "a", encoding="utf-8") as f:
        for v in videos:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


def crawl(category=DEFAULT_CATEGORY, pages=DEFAULT_PAGES):
    existing_eids = load_existing_eids()
    total_new = 0

    for page in range(1, pages + 1):
        url = _build_url(category, page)
        try:
            html = _fetch_html(url)
        except Exception as e:
            print(f"  [SKIP] {url}: {e}")
            break

        videos = _parse_video_blocks(html)
        new_videos = []
        for v in videos:
            if v["eid"] and v["eid"] not in existing_eids:
                v["tags"] = [f"eporner_{category}"]
                v["fetched_at"] = datetime.now(timezone.utc).isoformat()
                existing_eids.add(v["eid"])
                new_videos.append(v)

        if new_videos:
            _append_videos(new_videos)
        total_new += len(new_videos)
        print(f"  page {page}: {len(videos)} found, {len(new_videos)} new")

        if page < pages:
            time.sleep(REQUEST_DELAY)

    print(f"[eporner] Done. {total_new} new videos added.")
    return total_new


if __name__ == "__main__":
    crawl()
