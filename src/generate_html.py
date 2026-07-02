import json as _json
from datetime import datetime
from pathlib import Path

import tg_core


CHANNEL_USERNAME_MAP = {}

def _build_channel_map():
    global CHANNEL_USERNAME_MAP
    CHANNEL_USERNAME_MAP = {}
    for ch in tg_core.load_channels():
        CHANNEL_USERNAME_MAP[ch["id"]] = ch["username"]

def _username_for(channel_id):
    return CHANNEL_USERNAME_MAP.get(channel_id, channel_id)


def _scan_media_files(channel_id, subdir):
    d = tg_core.DOWNLOAD_DIR / channel_id / subdir
    files = []
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": f"{subdir}/{f.name}",
                })
    return files


def _normalize_media_paths(messages, channel_id):
    for msg in messages:
        for media in msg.get("media", []):
            p = media.get("path", "")
            if not p.startswith(f"{channel_id}/"):
                media["path"] = f"{channel_id}/{p}"


def _build_tab_data():
    _build_channel_map()
    channels = tg_core.load_channels()
    groups = {}
    standalone = []

    for ch in channels:
        grp = ch.get("group")
        if grp:
            groups.setdefault(grp, []).append(ch)
        else:
            standalone.append(ch)

    tabs = {}

    for grp_name, members in groups.items():
        messages = []
        for m in members:
            msgs = tg_core.load_messages(m["id"])
            for msg in msgs:
                if "channel" not in msg or not msg["channel"]:
                    msg["channel"] = _username_for(m["id"])
            _normalize_media_paths(msgs, m["id"])
            messages.extend(msgs)
        messages.sort(key=lambda x: x.get("id", 0), reverse=True)

        tabs[grp_name] = {
            "name": members[0]["name"],
            "messages": messages,
            "total": len(messages),
        }

    for ch in standalone:
        msgs = tg_core.load_messages(ch["id"])
        for msg in msgs:
            if "channel" not in msg or not msg["channel"]:
                msg["channel"] = _username_for(ch["id"])
        _normalize_media_paths(msgs, ch["id"])
        msgs.sort(key=lambda x: x.get("id", 0), reverse=True)
        tabs[ch["id"]] = {
            "name": ch["name"],
            "messages": msgs,
            "total": len(msgs),
        }

    return tabs


CSS = r"""
  :root {
    --bg: #0a0a0a; --surface: #161616; --surface-2: #1e1e1e;
    --fg: #e5e5e5; --fg-secondary: #a0a0a0; --muted: #6a6a6a;
    --border: #2a2a2a; --accent: #d14334; --accent-hover: #e05545;
    --accent-bg: rgba(209,67,52,0.08); --radius: 8px;
    --font-display: 'Iowan Old Style','Charter',Georgia,serif;
    --font-body: -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
    --max-w: 840px;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{font-size:clamp(14px,1vw + 10px,17px)}
  body{font-family:var(--font-body);background:var(--bg);color:var(--fg);line-height:1.6;min-height:100dvh;overflow-x:hidden}
  a{color:var(--accent);text-decoration:none}
  a:hover{color:var(--accent-hover)}
  img{max-width:100%;height:auto;display:block}
  button{cursor:pointer;font:inherit;border:none;background:none;color:inherit}
  input{font:inherit;color:inherit}
  .header{padding:2rem 1rem 1rem;border-bottom:1px solid var(--border);text-align:center}
  .header h1{font-family:var(--font-display);font-size:clamp(1.6rem,3.5vw,2.4rem);font-weight:400;letter-spacing:0.04em}
  .header .time{font-size:0.8rem;color:var(--muted);margin-top:0.4rem}
  .header .time span{color:var(--fg-secondary)}
  .tab-nav{display:flex;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10;background:var(--bg)}
  .tab-btn{flex:1;padding:0.8rem 1rem;text-align:center;font-size:0.9rem;font-weight:500;color:var(--muted);transition:color .2s,background .2s;position:relative}
  .tab-btn:hover{color:var(--fg-secondary);background:var(--surface)}
  .tab-btn.active{color:var(--fg)}
  .tab-btn.active::after{content:'';position:absolute;bottom:0;left:10%;width:80%;height:2px;background:var(--accent);border-radius:1px 1px 0 0}
  .tab-btn .badge{display:inline-block;font-size:0.7rem;background:var(--surface-2);color:var(--muted);padding:1px 6px;border-radius:8px;margin-left:4px;vertical-align:middle}
  .tab-btn.active .badge{color:var(--fg-secondary)}
  main{padding:0 1rem;max-width:var(--max-w);margin:0 auto}
  .tab-content{display:none;padding:1rem 0}
  .tab-content.active{display:block}
  .search-bar{display:flex;flex-wrap:wrap;gap:0.5rem;padding:0.75rem;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:1.5rem;align-items:center}
  .search-bar input[type="text"]{flex:1;min-width:160px;padding:0.5rem 0.75rem;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;font-size:0.85rem;color:var(--fg)}
  .search-bar input[type="text"]::placeholder{color:var(--muted)}
  .search-bar input[type="text"]:focus{border-color:var(--accent);outline:none}
  .search-bar .date-group{display:flex;gap:0.4rem;align-items:center}
  .search-bar .date-group label{font-size:0.8rem;color:var(--muted)}
  .search-bar input[type="date"]{padding:0.4rem 0.5rem;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;font-size:0.8rem;color:var(--fg)}
  .search-bar input[type="date"]:focus{border-color:var(--accent);outline:none}
  .search-bar .result-count{font-size:0.8rem;color:var(--muted);margin-left:auto}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin-bottom:0.75rem;transition:border-color .2s}
  .card:hover{border-color:var(--muted)}
  .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;font-size:0.78rem;color:var(--muted)}
  .card-source{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;background:var(--surface-2);border-radius:4px;color:var(--fg-secondary);font-size:0.75rem}
  .card-source::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent)}
  .card-date{font-family:var(--font-display);font-size:0.75rem;color:var(--muted)}
  .card-text{font-size:0.9rem;line-height:1.65;margin-bottom:0.5rem;word-wrap:break-word;white-space:pre-wrap}
  .card-text:empty{display:none}
  .card-media{margin-top:0.5rem;border-radius:6px;overflow:hidden;background:var(--surface-2);position:relative}
  .card-media img,.card-media video{width:100%;display:block;cursor:pointer;transition:opacity .2s}
  .card-media img:hover,.card-media video:hover{opacity:0.95}
  .card-media .vid-overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:48px;height:48px;background:rgba(0,0,0,0.6);border-radius:50%;display:flex;align-items:center;justify-content:center;pointer-events:none}
  .card-media .vid-overlay::after{content:'';border-left:14px solid #fff;border-top:8px solid transparent;border-bottom:8px solid transparent;margin-left:3px}
  .load-more-wrap{padding:1rem 0;text-align:center}
  .load-more-btn{display:inline-block;padding:0.65rem 2rem;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius);font-size:0.85rem;color:var(--fg-secondary);transition:background .2s}
  .load-more-btn:hover{background:var(--surface);color:var(--fg)}
  .load-more-btn.done{color:var(--muted);cursor:default;background:var(--surface)}
  .load-more-btn.done:hover{background:var(--surface);color:var(--muted)}
  .lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,0.92)}
  .lightbox.open{display:flex;align-items:center;justify-content:center}
  .lb-close{position:absolute;top:1rem;right:1rem;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.1)}
  .lb-close:hover{background:rgba(255,255,255,0.2)}
  .lb-prev,.lb-next{position:absolute;top:50%;transform:translateY(-50%);width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:2.2rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.06)}
  .lb-prev:hover,.lb-next:hover{background:rgba(255,255,255,0.15)}
  .lb-prev{left:1rem}
  .lb-next{right:1rem}
  .lb-counter{position:absolute;bottom:1.5rem;left:50%;transform:translateX(-50%);color:rgba(255,255,255,0.6);font-size:0.85rem;z-index:2;font-family:var(--font-display)}
  .lb-content{max-width:90vw;max-height:85vh;display:flex;align-items:center;justify-content:center}
  .lb-content img,.lb-content video{max-width:100%;max-height:85vh;object-fit:contain;border-radius:4px}
  .lb-content video{width:auto;height:auto}
  .hidden{display:none!important}
  @media(max-width:600px){
    .header{padding:1.2rem 0.8rem 0.8rem}
    main{padding:0 0.6rem}
    .card{padding:0.8rem}
    .search-bar{flex-direction:column;align-items:stretch}
    .search-bar .date-group{justify-content:space-between}
    .search-bar .result-count{margin-left:0;text-align:right}
    .tab-btn{font-size:0.82rem;padding:0.7rem 0.5rem}
    .lb-prev{left:0.5rem;width:36px;height:36px;font-size:1.6rem}
    .lb-next{right:0.5rem;width:36px;height:36px;font-size:1.6rem}
    .lb-content{max-width:96vw}
  }
  @media(min-width:601px)and (max-width:1023px){
    .search-bar .date-group label{display:none}
  }
"""

JS = r"""'use strict';
(function(){
var PAGE_SIZE = 50,
    tabsData = window.__DATA__,
    currentTab = '';

var CHANNELS = {};
for(var k in tabsData) CHANNELS[k] = tabsData[k];

function escHtml(s){
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function formatDate(iso){
  var d = new Date(iso);
  var y = d.getFullYear();
  var m = String(d.getMonth()+1).padStart(2,'0');
  var day = String(d.getDate()).padStart(2,'0');
  var h = String(d.getHours()).padStart(2,'0');
  var min = String(d.getMinutes()).padStart(2,'0');
  return y + '-' + m + '-' + day + ' ' + h + ':' + min;
}

function mediaHtml(media, basePath){
  if(!media || media.length===0) return '';
  var html = '';
  for(var i=0;i<media.length;i++){
    var m = media[i];
    var src = m.path;
    if(m.type === 'video'){
      html += '<div class="card-media" style="background:var(--surface-2);min-height:150px;display:flex;align-items:center;justify-content:center">';
      html += '<div class="vid-overlay"></div>';
      html += '<video preload="none" src="' + src + '" muted playsinline style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover"></video>';
      html += '</div>';
    } else {
      html += '<div class="card-media">';
      html += '<img src="' + src + '" alt="" loading="lazy">';
      html += '</div>';
    }
  }
  return html;
}

function renderCards(tabId, maxCount){
  var data = tabsData[tabId];
  if(!data) return;
  var container = document.getElementById('cards-' + tabId);
  if(!container) return;
  var msgs = data.messages;
  var count = maxCount || msgs.length;
  var showCount = Math.min(count, msgs.length);
  var html = '';
  for(var i=0;i<showCount;i++){
    var m = msgs[i];
    html += '<div class="card">';
    html += '<div class="card-header">';
    html += '<span class="card-source">' + escHtml(m.channel||'') + '</span>';
    html += '<span class="card-date">' + formatDate(m.date) + '</span>';
    html += '</div>';
    html += '<div class="card-text">' + escHtml(m.text||'') + '</div>';
    html += mediaHtml(m.media, tabId);
    html += '</div>';
  }
  container.innerHTML = html;
  data.rendered = showCount;
  updateLoadMore(tabId);
}

function updateLoadMore(tabId){
  var data = tabsData[tabId];
  var wrap = document.getElementById('loadmore-' + tabId);
  if(!wrap || !data) return;
  var remaining = data.messages.length - (data.rendered||0);
  if(remaining <= 0){
    if(data.messages.length > 0){
      wrap.innerHTML = '<button class="load-more-btn done">已全部載入</button>';
    } else {
      wrap.innerHTML = '';
    }
    return;
  }
  wrap.innerHTML = '<button class="load-more-btn" data-tab="'+tabId+'">載入更多 ('+remaining+')</button>';
}

function switchTab(tabId){
  if(tabId === currentTab) return;
  document.querySelectorAll('.tab-btn').forEach(function(b){
    b.classList.remove('active'); b.setAttribute('aria-selected','false');
  });
  document.querySelectorAll('.tab-content').forEach(function(c){
    c.classList.remove('active');
  });
  var btn = document.querySelector('.tab-btn[data-tab="'+tabId+'"]');
  if(btn){ btn.classList.add('active'); btn.setAttribute('aria-selected','true'); }
  var panel = document.getElementById('tab-' + tabId);
  if(panel) panel.classList.add('active');
  currentTab = tabId;
  var data = tabsData[tabId];
  if(data && !data.rendered){
    renderCards(tabId, PAGE_SIZE);
  }
  applySearch(tabId);
}

function applySearch(tabId){
  var container = document.getElementById('cards-' + tabId);
  var searchInput = document.querySelector('#tab-' + tabId + ' .search-input');
  var dateStart = document.querySelector('#tab-' + tabId + ' .search-date-start');
  var dateEnd = document.querySelector('#tab-' + tabId + ' .search-date-end');
  var resultEl = document.getElementById('result-count-' + tabId);
  if(!container || !searchInput) return;

  var kw = searchInput.value.trim().toLowerCase();
  var ds = dateStart ? dateStart.value : '';
  var de = dateEnd ? dateEnd.value : '';
  var isSearching = kw !== '' || ds !== '' || de !== '';

  var cards = container.querySelectorAll('.card');
  var matched = 0;

  for(var i=0;i<cards.length;i++){
    var card = cards[i];
    var textEl = card.querySelector('.card-text');
    var dateEl = card.querySelector('.card-date');
    var text = textEl ? textEl.textContent.toLowerCase() : '';
    var date = dateEl ? dateEl.textContent.trim().slice(0,10) : '';
    var show = true;
    if(kw && text.indexOf(kw) === -1) show = false;
    if(ds && date < ds) show = false;
    if(de && date > de) show = false;
    if(show) matched++;
    card.classList.toggle('hidden', !show);
  }

  if(isSearching){
    resultEl.textContent = matched + ' 筆結果';
    var loadWrap = document.getElementById('loadmore-' + tabId);
    if(loadWrap) loadWrap.innerHTML = '';
  } else {
    resultEl.textContent = '';
    updateLoadMore(tabId);
  }
}

/* lightbox */
var lbState = { tabId:'', items:[], current:0 };

function openLightbox(tabId, startIndex){
  var container = document.getElementById('cards-' + tabId);
  if(!container) return;
  var wraps = container.querySelectorAll('.card-media');
  var items = [];
  wraps.forEach(function(w,i){
    var img = w.querySelector('img');
    var vid = w.querySelector('video');
    items.push({ index:i, isVideo:!!vid, src: vid ? vid.getAttribute('src') : (img ? img.getAttribute('src') : '') });
  });
  if(items.length===0) return;
  lbState.tabId = tabId;
  lbState.items = items;
  lbState.current = startIndex;
  showLightboxItem();
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function showLightboxItem(){
  var content = document.getElementById('lb-content');
  var counter = document.getElementById('lb-counter');
  var items = lbState.items;
  var idx = lbState.current;
  if(!items || items.length===0) return;
  var item = items[idx];
  counter.textContent = (idx+1) + ' / ' + items.length;
  if(item.isVideo){
    content.innerHTML = '<video src="'+item.src+'" controls autoplay style="max-width:90vw;max-height:80vh;border-radius:4px"></video>';
  } else {
    content.innerHTML = '<img src="'+item.src+'" alt="" style="max-width:90vw;max-height:80vh;object-fit:contain;border-radius:4px">';
  }
}

function lbPrev(){
  if(lbState.items.length===0) return;
  lbState.current = (lbState.current - 1 + lbState.items.length) % lbState.items.length;
  showLightboxItem();
}
function lbNext(){
  if(lbState.items.length===0) return;
  lbState.current = (lbState.current + 1) % lbState.items.length;
  showLightboxItem();
}
function closeLightbox(){
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}

/* init */
function init(){
  var tabIds = [];
  document.querySelectorAll('.tab-btn').forEach(function(btn){
    var id = btn.getAttribute('data-tab');
    tabIds.push(id);
    btn.addEventListener('click', function(){ switchTab(id); });
  });

  if(tabIds.length > 0){
    tabIds.forEach(function(id){ renderCards(id, PAGE_SIZE); });
    currentTab = tabIds[0];
  }

  document.addEventListener('click', function(e){
    var loadBtn = e.target.closest('.load-more-btn:not(.done)');
    if(loadBtn){
      var tabId = loadBtn.getAttribute('data-tab');
      if(tabId && tabsData[tabId]){
        var next = (tabsData[tabId].rendered||0) + PAGE_SIZE;
        renderCards(tabId, next);
      }
      return;
    }

    var mediaWrap = e.target.closest('.card-media');
    if(mediaWrap){
      var card = mediaWrap.closest('.card');
      if(!card) return;
      var container = card.closest('.cards-container');
      if(!container) return;
      var tabId = container.id.replace('cards-','');
      var allMedia = container.querySelectorAll('.card-media');
      var idx = -1;
      allMedia.forEach(function(el,i){ if(el === mediaWrap) idx = i; });
      if(idx >= 0) openLightbox(tabId, idx);
      return;
    }
  });

  document.getElementById('lb-close').addEventListener('click', closeLightbox);
  document.getElementById('lb-prev').addEventListener('click', lbPrev);
  document.getElementById('lb-next').addEventListener('click', lbNext);
  document.getElementById('lightbox').addEventListener('click', function(e){
    if(e.target === this) closeLightbox();
  });

  document.addEventListener('keydown', function(e){
    if(!document.getElementById('lightbox').classList.contains('open')) return;
    if(e.key === 'Escape'){ closeLightbox(); e.preventDefault(); }
    if(e.key === 'ArrowLeft'){ lbPrev(); e.preventDefault(); }
    if(e.key === 'ArrowRight'){ lbNext(); e.preventDefault(); }
  });

  document.querySelectorAll('.tab-content').forEach(function(panel){
    var si = panel.querySelector('.search-input');
    var ds = panel.querySelector('.search-date-start');
    var de = panel.querySelector('.search-date-end');
    function onSearch(){
      var tabId = panel.id.replace('tab-','');
      applySearch(tabId);
    }
    if(si) si.addEventListener('input', onSearch);
    if(ds) ds.addEventListener('change', onSearch);
    if(de) de.addEventListener('change', onSearch);
  });
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
})();
"""


def generate():
    output_path = tg_core.DOWNLOAD_DIR / "index.html"
    tabs = _build_tab_data()

    tabs_nav = ""
    tabs_content = ""
    first_id = None

    for tab_id, tab in tabs.items():
        if first_id is None:
            first_id = tab_id
        active_cls = " active" if tab_id == first_id else ""
        tabs_nav += (
            f'<button class="tab-btn{active_cls}" role="tab" '
            f'aria-selected="{str(tab_id == first_id).lower()}" '
            f'data-tab="{tab_id}">{tab["name"]} '
            f'<span class="badge">{tab["total"]}</span></button>'
        )

        tabs_content += f'''<div class="tab-content{active_cls}" id="tab-{tab_id}" role="tabpanel">
    <div class="search-bar">
      <input type="text" class="search-input" placeholder="搜尋訊息…" aria-label="搜尋關鍵字">
      <div class="date-group">
        <label>從</label>
        <input type="date" class="search-date-start">
        <label>至</label>
        <input type="date" class="search-date-end">
      </div>
      <span class="result-count" id="result-count-{tab_id}"></span>
    </div>
    <div class="cards-container" id="cards-{tab_id}"></div>
    <div class="load-more-wrap" id="loadmore-{tab_id}"></div>
  </div>'''

    tabs_json = _json.dumps(tabs, ensure_ascii=False, default=str)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Adult Dream</title>
<style>{CSS}</style>
</head>
<body>

<header class="header">
  <h1>Adult Dream</h1>
  <div class="time">最後更新：<span id="update-time">{_now_str()}</span></div>
</header>

<nav class="tab-nav" role="tablist">
  {tabs_nav}
</nav>

<main id="main-content">
  {tabs_content}
</main>

<div class="lightbox" id="lightbox" role="dialog" aria-label="圖片檢視">
  <span class="lb-close" id="lb-close">&times;</span>
  <span class="lb-prev" id="lb-prev">&lsaquo;</span>
  <span class="lb-next" id="lb-next">&rsaquo;</span>
  <div class="lb-content" id="lb-content"></div>
  <span class="lb-counter" id="lb-counter"></span>
</div>

<script>
window.__DATA__ = {tabs_json};
</script>
<script>{JS}</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML generated: {output_path}")
    return str(output_path)


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    generate()
