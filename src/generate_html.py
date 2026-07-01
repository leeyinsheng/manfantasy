import json
from pathlib import Path

import tg_core


def _scan_media_files(channel_id, subdir):
    d = tg_core.DOWNLOAD_DIR / channel_id / subdir
    files = []
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.is_file():
                is_video = f.suffix.lower() in (".mp4", ".webm", ".mov")
                files.append({
                    "type": "video" if is_video else "photo",
                    "path": f"{subdir}/{f.name}",
                    "name": f.name,
                })
    return files


def _build_channel_data():
    channels = tg_core.load_channels()
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
            msgs = tg_core.load_messages(ch_id)
            msgs.sort(key=lambda m: m.get("id", 0), reverse=True)
            entry["messages"] = msgs
        else:
            entry["photos"] = _scan_media_files(ch_id, "photo")
            entry["videos"] = _scan_media_files(ch_id, "video")
        data.append(entry)
    return data


def _build_media_gallery(files, base_dir):
    if not files:
        return '<div class="empty">尚無內容</div>'
    items = []
    for f in files:
        path = f"{base_dir}/{f['path']}"
        if f["type"] == "video":
            items.append(f'<a href="{path}" target="_blank"><video src="{path}" preload="metadata" controls></video></a>')
        else:
            items.append(f'<a href="{path}" target="_blank"><img src="{path}" alt="{f["name"]}" loading="lazy"></a>')
    return '<div class="gallery">' + "".join(items) + "</div>"


def _build_split_gallery(photos, videos, base_dir):
    return f"""<div class="media-split">
    <div class="media-col">
      <div class="section-label">影片</div>
      {_build_media_gallery(videos, base_dir)}
    </div>
    <div class="media-col">
      <div class="section-label">圖片</div>
      {_build_media_gallery(photos, base_dir)}
    </div>
  </div>"""


def _build_messages(msgs, base_dir):
    if not msgs:
        return '<div class="empty">尚無內容</div>'
    cards = []
    for m in msgs:
        date_str = m.get("date", "")
        text = m.get("text", "")
        media_html = ""
        media_list = m.get("media", [])
        if media_list:
            items = []
            for media in media_list:
                path = f"{base_dir}/{media['path']}"
                items.append(f'<a href="{path}" target="_blank"><img src="{path}" alt="" loading="lazy"></a>')
            media_html = '<div class="card-media">' + "".join(items) + "</div>"

        cards.append(f"""<div class="card">
      <div class="card-date">{date_str}</div>
      {f'<div class="card-text">{text}</div>' if text else ''}
      {media_html}
    </div>""")
    return "".join(cards)


CSS = """
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
  .tabs { display:flex; margin-bottom:24px; border-bottom:2px solid var(--border); }
  .tab { padding:10px 24px; font-size:14px; font-weight:500; cursor:pointer; color:var(--text-dim); border-bottom:2px solid transparent; margin-bottom:-2px; transition:all .15s; user-select:none; }
  .tab:hover { color:var(--text); }
  .tab.active { color:var(--accent2); border-bottom-color:var(--accent2); }
  .tab-content { display:none; }
  .tab-content.active { display:block; }
  .section-label { font-size:12px; font-weight:600; text-transform:uppercase; color:var(--text-dim); padding:8px 4px 10px; border-bottom:1px solid var(--border); margin-bottom:10px; letter-spacing:.5px; }
  .card { background:var(--surface); border-radius:var(--radius); border:1px solid var(--border); margin-bottom:16px; overflow:hidden; }
  .card-date { font-size:12px; color:var(--accent); padding:14px 16px 0; font-weight:500; }
  .card-text { padding:8px 16px 14px; font-size:14px; line-height:1.7; color:var(--text); white-space:pre-wrap; }
  .card-media { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:2px; padding:0; }
  .card-media img,.card-media video { width:100%; height:150px; object-fit:cover; cursor:pointer; display:block; }
  .card-media a { display:block; }
  .gallery { display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:4px; }
  .gallery img,.gallery video { width:100%; height:200px; object-fit:cover; border-radius:4px; cursor:pointer; transition:opacity .15s; }
  .gallery img:hover,.gallery video:hover { opacity:.8; }
  .gallery a { display:block; }
  .media-split { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .media-col { min-width:0; }
  .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); }
  .media-col .gallery img,.media-col .gallery video { height:180px; }
  .empty { text-align:center; padding:60px 20px; color:var(--text-dim); font-size:14px; }
  @media (max-width:768px) {
    .media-split { grid-template-columns:1fr; }
    .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .media-col .gallery img,.media-col .gallery video { height:140px; }
  }
  @media (max-width:640px) {
    .gallery { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .gallery img,.gallery video { height:140px; }
    .card-media { grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); }
    .card-media img,.card-media video { height:140px; }
    .media-col .gallery { grid-template-columns:repeat(auto-fill, minmax(130px, 1fr)); }
    .media-col .gallery img,.media-col .gallery video { height:130px; }
  }
"""


def generate():
    output_path = tg_core.DOWNLOAD_DIR / "index.html"
    channels = _build_channel_data()

    tabs_html = ""
    contents_html = ""
    for i, ch in enumerate(channels):
        ch_id = ch["id"]
        tab_class = "tab active" if i == 0 else "tab"
        content_class = "tab-content active" if i == 0 else "tab-content"
        tabs_html += f'<div class="{tab_class}" onclick="switchTab(\'{ch_id}\')">{ch["name"]}</div>'

        if ch["mode"] == "text":
            inner = _build_messages(ch["messages"], ch_id)
        else:
            inner = _build_split_gallery(ch["photos"], ch["videos"], ch_id)

        contents_html += f'<div id="tab-{ch_id}" class="{content_class}">{inner}</div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adult Dream</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Adult Dream</h1>
    <p>更新時間: {_now_str()}</p>
  </header>
  <div class="tabs">{tabs_html}</div>
  <div id="contents">{contents_html}</div>
</div>
<script>
function switchTab(chId) {{
  document.querySelectorAll('.tab').forEach(function(t){{t.classList.remove('active')}});
  document.querySelectorAll('.tab-content').forEach(function(c){{c.classList.remove('active')}});
  var tabs=document.querySelectorAll('.tab');
  var els=document.querySelectorAll('.tab-content');
  for(var i=0;i<tabs.length;i++){{
    if(tabs[i].getAttribute('onclick')&&tabs[i].getAttribute('onclick').indexOf(chId)>-1)tabs[i].classList.add('active');
  }}
  var el=document.getElementById('tab-'+chId);
  if(el)el.classList.add('active');
}}
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML generated: {output_path}")
    return str(output_path)


def _now_str():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    generate()
