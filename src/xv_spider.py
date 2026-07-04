import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "download"
XV_CONFIG_FILE = Path(__file__).parent / "xvideos.json"
XV_DIR = DOWNLOAD_DIR / "xvideos"
XV_VIDEOS_FILE = XV_DIR / "videos.jsonl"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
REQUEST_DELAY = 2


def load_sources():
    if XV_CONFIG_FILE.exists():
        try:
            data = json.loads(XV_CONFIG_FILE.read_text(encoding="utf-8-sig"))
            return data.get("sources", [])
        except (json.JSONDecodeError, ValueError):
            return []
    return []


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


def _build_url(source, page):
    base = "https://www.xvideos.com"
    if source["type"] == "category":
        sort = source.get("sort", "uploaddate")
        if page == 0:
            return f"{base}/c/{source['id']}?s={sort}"
        return f"{base}/c/{source['id']}/{page}?s={sort}"
    elif source["type"] == "user":
        return f"{base}/{source['id']}/videos/{page}"
    else:
        keyword = urllib.parse.quote(source.get("keyword", source["id"]))
        sort = source.get("sort", "uploaddate")
        if page == 0:
            return f"{base}/?k={keyword}&sort={sort}"
        return f"{base}/?k={keyword}&p={page}&sort={sort}"


def _fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_video_blocks(html):
    block_re = re.compile(
        r'<div[^>]*\bdata-id="(\d+)"[^>]*\bdata-eid="([^"]*)"[^>]*\bclass="[^"]*\bframe-block\b[^"]*\bthumb-block\b[^"]*"[^>]*>',
        re.DOTALL,
    )
    title_re = re.compile(
        r'<p class="title">\s*<a[^>]*title="([^"]*)"[^>]*>.*?'
        r'<span class="duration">([^<]*)</span>.*?</a>',
        re.DOTALL,
    )
    thumb_re = re.compile(r'data-src="([^"]*)"')
    name_re = re.compile(r'<span class="name">([^<]+)</span>')
    hd_re = re.compile(r'<span class="video-hd-mark">\s*(\S+)\s*</span>')
    sd_re = re.compile(r'<span class="video-sd-mark">\s*(\S+)\s*</span>')
    views_re = re.compile(r'(\d[\d.,]*[kKmM]?)\s*Views?', re.IGNORECASE)

    videos = []
    for match in block_re.finditer(html):
        video_id = match.group(1)
        eid = match.group(2)
        start = max(0, match.start() - 200)
        end = min(len(html), match.end() + 3000)
        chunk = html[start:end]

        title_match = title_re.search(chunk)
        title = title_match.group(1) if title_match else ""
        duration = title_match.group(2).strip() if title_match else ""

        thumb_match = thumb_re.search(chunk)
        thumbnail = thumb_match.group(1) if thumb_match else ""

        name_match = name_re.search(chunk)
        uploader = name_match.group(1).strip() if name_match else ""

        quality = ""
        hd_match = hd_re.search(chunk)
        if hd_match:
            quality = hd_match.group(1)
        else:
            sd_match = sd_re.search(chunk)
            if sd_match:
                quality = sd_match.group(1)

        views = ""
        views_match = views_re.search(chunk)
        if views_match:
            views = views_match.group(1) + " views"

        videos.append({
            "eid": eid,
            "video_id": int(video_id),
            "title": title,
            "duration": duration,
            "views": views,
            "uploader": uploader,
            "thumbnail": thumbnail,
            "quality": quality,
        })

    return videos


def crawl_source(source, existing_eids):
    tag = source.get("tag", source["id"])
    pages = source.get("pages", 5)
    new_videos = []

    for page in range(pages):
        url = _build_url(source, page)
        try:
            html = _fetch_html(url)
        except Exception as e:
            print(f"  [SKIP] {url}: {e}")
            break

        videos = _parse_video_blocks(html)
        added = 0
        for v in videos:
            if v["eid"] and v["eid"] not in existing_eids:
                v["tags"] = [tag]
                v["fetched_at"] = datetime.now(timezone.utc).isoformat()
                existing_eids.add(v["eid"])
                new_videos.append(v)
                added += 1

        print(f"  page {page + 1}: {len(videos)} found, {added} new")
        if added == 0:
            break
        if page < pages - 1:
            time.sleep(REQUEST_DELAY)

    return new_videos


def _append_videos(videos):
    XV_DIR.mkdir(parents=True, exist_ok=True)
    with open(XV_VIDEOS_FILE, "a", encoding="utf-8") as f:
        for v in videos:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


def crawl():
    sources = load_sources()
    if not sources:
        print("No xvideos sources configured.")
        return 0

    existing_eids = load_existing_eids()
    total_new = 0

    for src in sources:
        label = src.get("tag", src["id"])
        print(f"[xv] {label} ({src['type']})")
        new_videos = crawl_source(src, existing_eids)
        _append_videos(new_videos)
        total_new += len(new_videos)
        print(f"  total new: {len(new_videos)}")

    print(f"\n[xv] Done. {total_new} new videos added.")
    return total_new


if __name__ == "__main__":
    crawl()
