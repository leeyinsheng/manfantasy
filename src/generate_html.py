import json
import os
from datetime import datetime
from pathlib import Path

from tg_core import load_channels, load_messages, DOWNLOAD_DIR, get_photo_dir, get_video_dir

OUTPUT_PATH = DOWNLOAD_DIR / "index.html"


def _scan_media_files(channel_id, subdir):
    d = get_photo_dir(channel_id) if subdir == "photo" else get_video_dir(channel_id)
    files = []
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.is_file():
                files.append({
                    "type": "video" if f.suffix.lower() in (".mp4", ".webm", ".mov") else "photo",
                    "path": f"{subdir}/{f.name}",
                    "name": f.name,
                })
    return files


def build_channel_data():
    channels = load_channels()
    data = []

    for ch in channels:
        ch_id = ch["id"]
        entry = {
            "id": ch_id,
            "name": ch["name"],
            "mode": ch.get("mode", "media"),
            "messages": [],
            "photos": [],
            "videos": [],
        }

        if ch.get("mode") == "text":
            msgs = load_messages(ch_id)
            msgs.sort(key=lambda m: m.get("id", 0), reverse=True)
            entry["messages"] = msgs
        else:
            entry["photos"] = _scan_media_files(ch_id, "photo")
            entry["videos"] = _scan_media_files(ch_id, "video")

        data.append(entry)

    return data


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adult Dream</title>
<style>
  :root {
    --bg: #0f0f14; --surface: #1a1a24; --surface2: #22223a;
    --accent: #f0a050; --accent2: #50b0e0; --text: #e4e4ec;
    --text-dim: #8888a0; --border: #2a2a3a; --radius: 10px;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
    background:var(--bg); color:var(--text); min-height:100vh;
  }
  .container { max-width:960px; margin:0 auto; padding:20px 16px; }
  header { text-align:center; padding:32px 0 20px; border-bottom:1px solid var(--border); margin-bottom:20px; }
  header h1 { font-size:22px; font-weight:700; }
  header p { color:var(--text-dim); font-size:13px; margin-top:4px; }

  .tabs { display:flex; gap:0; margin-bottom:24px; border-bottom:2px solid var(--border); }
  .tab { padding:10px 24px; font-size:14px; font-weight:500; cursor:pointer; color:var(--text-dim); border-bottom:2px solid transparent; margin-bottom:-2px; transition:all .15s; }
  .tab:hover { color:var(--text); }
  .tab.active { color:var(--accent2); border-bottom-color:var(--accent2); }
  .tab-content { display:none; }
  .tab-content.active { display:block; }

  .section-label { font-size:12px; font-weight:600; text-transform:uppercase; color:var(--text-dim); padding:8px 4px 10px; border-bottom:1px solid var(--border); margin-bottom:10px; letter-spacing:.5px; }

  .card { background:var(--surface); border-radius:var(--radius); border:1px solid var(--border); margin-bottom:16px; overflow:hidden; }
  .card-date { font-size:12px; color:var(--accent); padding:14px 16px 0; font-weight:500; }
  .card-text { padding:8px 16px 14px; font-size:14px; line-height:1.7; color:var(--text); white-space:pre-wrap; }
  .card-media { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:2px; padding:0; }
  .card-media a { display:block; }
  .card-media img,.card-media video { width:100%; height:150px; object-fit:cover; cursor:pointer; display:block; }

  .gallery { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:4px; }
  .gallery img,.gallery video { width:100%; height:200px; object-fit:cover; border-radius:4px; cursor:pointer; transition:opacity .15s; }
  .gallery img:hover,.gallery video:hover { opacity:.8; }
  .gallery a { display:block; }

  .media-split { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .media-col { min-width:0; }
  .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); }
  .media-col .gallery img,.media-col .gallery video { height:180px; }

  .empty { text-align:center; padding:60px 20px; color:var(--text-dim); font-size:14px; }

  .media-placeholder {
    background: var(--surface2); border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    color: var(--text-dim); font-size: 12px; text-align: center;
    padding: 8px; word-break: break-all; min-height: 80px;
  }
  .gallery .media-placeholder { height: 200px; }
  .card-media .media-placeholder { height: 150px; }
  .media-col .gallery .media-placeholder { height: 180px; }
  .video-placeholder::before { content: '\\25b6 '; font-size: 16px; }

  @media (max-width:768px) {
    .media-split { grid-template-columns:1fr; }
    .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .media-col .gallery img,.media-col .gallery video { height:140px; }
    .media-col .gallery .media-placeholder { height:140px; }
  }
  @media (max-width:640px) {
    .gallery { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .gallery img,.gallery video { height:140px; }
    .card-media { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .card-media img,.card-media video { height:140px; }
    .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(130px, 1fr)); }
    .media-col .gallery img,.media-col .gallery video { height:130px; }
    .gallery .media-placeholder { height:140px; }
    .card-media .media-placeholder { height:140px; }
    .media-col .gallery .media-placeholder { height:130px; }
  }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Adult Dream</h1>
    <p id="update-time"></p>
  </header>

  <div class="tabs" id="tabs"></div>

  <div id="contents"></div>
</div>

<script>
var CHANNELS = __CHANNELS__;
var gChannels = CHANNELS;

function switchTab(tab, contentId) {
  document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
  tab.classList.add('active');
  document.getElementById(contentId).classList.add('active');
}

function buildMediaFileHTML(f, base) {
  var path = base + f.path;
  if (f.type === 'video') {
    return '<a href="' + path + '" target="_blank"><video src="' + path + '" preload="metadata" controls onerror="this.style.display=\'none\';var d=document.createElement(\'div\');d.className=\'media-placeholder video-placeholder\';d.textContent=\'\\u25b6 \'+decodeURIComponent(\'' + encodeURIComponent(f.name || f.path.split('/').pop()) + '\');this.parentElement.appendChild(d);"></video></a>';
  }
  return '<a href="' + path + '" target="_blank"><img src="' + path + '" alt="" loading="lazy" onerror="this.style.display=\'none\';var d=document.createElement(\'div\');d.className=\'media-placeholder\';d.textContent=decodeURIComponent(\'' + encodeURIComponent(f.name || f.path.split('/').pop()) + '\');this.parentElement.appendChild(d);"></a>';
}

function buildMediaGallery(files, base) {
  if (!files.length) return '<div class="empty">尚無內容</div>';
  return '<div class="gallery">' + files.map(function(f) { return buildMediaFileHTML(f, base); }).join('') + '</div>';
}

function buildSplitGallery(photos, videos, base) {
  return '<div class="media-split">' +
    '<div class="media-col">' +
      '<div class="section-label">影片</div>' +
      buildMediaGallery(videos, base) +
    '</div>' +
    '<div class="media-col">' +
      '<div class="section-label">圖片</div>' +
      buildMediaGallery(photos, base) +
    '</div>' +
  '</div>';
}

function buildMessages(msgs, base) {
  if (!msgs.length) return '<div class="empty">尚無內容</div>';
  return msgs.map(function(m) {
    var date = new Date(m.date).toLocaleString('zh-TW', {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    var mediaHTML = '';
    if (m.media && m.media.length) {
      mediaHTML = '<div class="card-media">' + m.media.map(function(f) { return buildMediaFileHTML(f, base); }).join('') + '</div>';
    }
    return '<div class="card">' +
      '<div class="card-date">' + date + '</div>' +
      (m.text ? '<div class="card-text">' + m.text + '</div>' : '') +
      mediaHTML +
    '</div>';
  }).join('');
}

function render() {
  var tabsHTML = '';
  var contentsHTML = '';
  gChannels.forEach(function(ch, i) {
    var tabId = 'tab-' + ch.id;
    tabsHTML += '<div class="tab' + (i === 0 ? ' active' : '') + '" onclick="switchTab(this,\\'' + tabId + '\\')">' + ch.name + '</div>';

    var baseDir = ch.id + '/';
    var inner = '';
    if (ch.mode === 'text') {
      inner = buildMessages(ch.messages, baseDir);
    } else {
      inner = buildSplitGallery(ch.photos, ch.videos, baseDir);
    }
    contentsHTML += '<div id="' + tabId + '" class="tab-content' + (i === 0 ? ' active' : '') + '">' + inner + '</div>';
  });

  document.getElementById('tabs').innerHTML = tabsHTML;
  document.getElementById('contents').innerHTML = contentsHTML;
  document.getElementById('update-time').textContent = '更新時間: ' + new Date().toLocaleString('zh-TW');
}

render();
</script>
</body>
</html>"""


def generate():
    channels_data = build_channel_data()
    data_json = json.dumps(channels_data, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__CHANNELS__", data_json)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    print(f"\nHTML generated: {OUTPUT_PATH}")
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    generate()
