import json as _json
from datetime import datetime
from pathlib import Path

import tg_core

XV_VIDEOS_FILE = tg_core.DOWNLOAD_DIR / "xvideos" / "videos.jsonl"


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
            thumb = media.get("thumb", "")
            if thumb and not thumb.startswith(f"{channel_id}/"):
                media["thumb"] = f"{channel_id}/{thumb}"


def _merge_grouped_messages(messages):
    groups = {}
    result = []
    for msg in messages:
        gid = msg.get("grouped_id")
        if gid:
            if gid not in groups:
                groups[gid] = msg
                result.append(msg)
            else:
                groups[gid]["media"].extend(msg.get("media", []))
        else:
            result.append(msg)
    return result


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
        messages = _merge_grouped_messages(messages)
        messages.sort(key=lambda x: x.get("date", ""), reverse=True)

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
        msgs = _merge_grouped_messages(msgs)
        msgs.sort(key=lambda x: x.get("date", ""), reverse=True)
        tabs[ch["id"]] = {
            "name": ch["name"],
            "messages": msgs,
            "total": len(msgs),
        }

    return tabs


def _load_xvideos():
    videos = []
    if XV_VIDEOS_FILE.exists():
        with open(XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        videos.append(_json.loads(line))
                    except (_json.JSONDecodeError, ValueError):
                        pass
    videos.sort(key=lambda v: v.get("fetched_at", ""), reverse=True)
    return videos


def _build_xv_tag_counts(videos):
    counts = {}
    for v in videos:
        for tag in v.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


CSS = r"""
  :root {
    --bg: #0a0c12; --surface: rgba(16,18,26,0.92); --surface-2: #141720;
    --fg: #e4e1db; --fg-secondary: #908d86; --muted: #524f4a;
    --border: rgba(201,162,78,0.10); --accent: #c9a24e; --accent-hover: #e0c878;
    --accent-bg: rgba(201,162,78,0.10); --radius: 8px;
    --nav-bg: rgba(8,10,16,0.96); --app-w: 430px;
    --font-display: Georgia,'Times New Roman',serif;
    --font-body: -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{font-size:15px}
  body{font-family:var(--font-body);background:#06070a;display:flex;justify-content:center;min-height:100dvh;color:var(--fg);line-height:1.6;-webkit-tap-highlight-color:transparent}
  a{color:var(--accent);text-decoration:none}
  button{cursor:pointer;font:inherit;border:none;background:none;color:inherit}
  input{font:inherit;color:inherit}
  .app-shell{width:100%;max-width:var(--app-w);min-height:100dvh;display:flex;flex-direction:column;background:var(--bg);position:relative;overflow-x:hidden;border-left:1px solid rgba(255,255,255,0.02);border-right:1px solid rgba(255,255,255,0.02)}
  .app-header{padding:0.8rem 1rem;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10;background:rgba(10,12,18,0.96)}
  .app-header .title{font-family:var(--font-display);font-size:0.85rem;font-weight:600;color:var(--accent);letter-spacing:0.06em;text-shadow:0 0 12px rgba(201,162,78,0.15)}
  .app-header .time{font-size:0.68rem;color:var(--muted)}
  .app-content{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:0.75rem 0.75rem 5rem}
  .tab-content{display:none}
  .tab-content.active{display:block}
  .search-bar{display:flex;flex-wrap:wrap;gap:0.5rem;padding:0.75rem;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:1rem;align-items:center}
  .search-bar input[type="text"]{flex:1;min-width:120px;padding:0.5rem 0.75rem;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;font-size:0.82rem;color:var(--fg);outline:none}
  .search-bar input[type="text"]:focus{border-color:var(--accent)}
  .time-presets{display:flex;gap:4px;flex-wrap:wrap}
  .preset-btn{padding:0.3rem 0.5rem;font-size:0.72rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--border);border-radius:4px}
  .preset-btn:hover{color:var(--fg-secondary)}
  .preset-btn.active{color:var(--fg);background:var(--accent-bg);border-color:var(--accent)}
  .search-bar .result-count{font-size:0.75rem;color:var(--muted);margin-left:auto}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:0.8rem 0.8rem 0;margin-bottom:0.5rem}
  .card:hover{border-color:var(--muted)}
  .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;font-size:0.72rem}
  .card-source{display:inline-flex;align-items:center;gap:4px;padding:2px 6px;background:var(--surface-2);border-radius:3px;color:var(--fg-secondary);font-size:0.68rem}
  .card-source::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--accent)}
  .card-source.xv::before{background:var(--accent)}
  .card-date{font-family:var(--font-display);font-size:0.66rem;color:var(--muted)}
  .card-text{font-size:0.84rem;line-height:1.6;margin-bottom:0.4rem;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;white-space:pre-wrap;word-wrap:break-word}
  .card-text.full{-webkit-line-clamp:unset;display:block}
  .card-thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:3px;margin-top:0.4rem}
  .thumb{position:relative;aspect-ratio:1;overflow:hidden;border-radius:3px;background:var(--surface-2);cursor:pointer}
  .thumb img{width:100%;height:100%;object-fit:cover}
  .thumb .vid-icon{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:24px;height:24px;background:rgba(0,0,0,0.65);border-radius:50%;display:flex;align-items:center;justify-content:center;pointer-events:none}
  .thumb .vid-icon::after{content:'';border-left:7px solid var(--accent);border-top:4px solid transparent;border-bottom:4px solid transparent;margin-left:1px}
  .card-expand{text-align:center;font-size:0.72rem;color:var(--muted);padding:0.5rem 0;margin:0 -0.8rem;margin-top:0.4rem;border-top:1px solid var(--border);cursor:pointer;user-select:none}
  .card-expand:hover{color:var(--fg-secondary)}
  .pagination{display:flex;justify-content:center;align-items:center;gap:4px;padding:0.75rem 0 0.5rem;flex-wrap:wrap}
  .page-btn{min-width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:0.75rem;color:var(--muted);background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:4px;cursor:pointer;user-select:none}
  .page-btn:hover{color:var(--fg-secondary);border-color:var(--muted)}
  .page-btn.active{color:var(--fg);background:var(--accent-bg);border-color:var(--accent)}
  .page-btn.disabled{opacity:0.25;pointer-events:none}
  .page-info{font-size:0.72rem;color:var(--muted);padding:0 8px}
  .tag-bar{display:flex;gap:5px;margin-bottom:0.75rem;flex-wrap:wrap;padding:0 0.25rem}
  .tag-btn{padding:0.3rem 0.65rem;font-size:0.72rem;color:var(--muted);background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:16px;cursor:pointer;user-select:none}
  .tag-btn.active{color:var(--bg);background:linear-gradient(135deg,var(--accent),var(--accent-hover));border-color:transparent;font-weight:600}
  .tag-count{font-size:0.65rem;opacity:0.7;margin-left:2px}
  .tag-badge{display:inline-block;font-size:0.6rem;padding:1px 5px;border-radius:2px;background:var(--accent-bg);color:var(--accent);margin-left:4px;vertical-align:middle}
  .xv-embed{margin:0.4rem -0.8rem 0;overflow:hidden;background:#000;border-top:1px solid var(--border)}
  .xv-embed iframe{display:block;border:none;width:100%;min-height:420px}
  @media(max-width:430px){.xv-embed iframe{min-height:240px}}
  .bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:var(--app-w);display:flex;justify-content:space-around;background:var(--nav-bg);border-top:1px solid var(--border);z-index:20;padding:0.3rem 0 max(0.3rem,env(safe-area-inset-bottom))}
  .nav-item{display:flex;flex-direction:column;align-items:center;gap:1px;padding:0.35rem 0.3rem;min-width:52px;font-size:0.58rem;color:var(--muted);cursor:pointer;user-select:none;transition:color .15s}
  .nav-item .icon{font-size:1.15rem;line-height:1}
  .nav-item.active{color:var(--accent)}
  .nav-item.active .icon{text-shadow:0 0 10px rgba(201,162,78,0.2)}
  .lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,0.96)}
  .lightbox.open{display:flex;align-items:center;justify-content:center}
  .lb-close{position:absolute;top:1rem;right:1rem;width:38px;height:38px;border-radius:50%;font-size:1.3rem;color:var(--accent);border:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2}
  .lb-prev,.lb-next{position:absolute;top:50%;transform:translateY(-50%);width:40px;height:40px;font-size:1.8rem;color:var(--accent);cursor:pointer;z-index:2;display:flex;align-items:center;justify-content:center}
  .lb-prev{left:0.5rem}.lb-next{right:0.5rem}
  .lb-counter{position:absolute;bottom:1rem;left:50%;transform:translateX(-50%);color:var(--fg-secondary);font-size:0.78rem;z-index:2;font-family:var(--font-display)}
  .lb-content{max-width:96vw;max-height:80vh;display:flex;align-items:center;justify-content:center}
  .lb-content img,.lb-content video{max-width:100%;max-height:80vh;object-fit:contain;border-radius:4px}
  .hidden{display:none!important}
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

function mediaHtml(media){
  if(!media || media.length===0) return '';
  var html = '<div class="card-thumbs">';
  for(var i=0;i<media.length;i++){
    var m = media[i];
    var src = m.thumb || m.path;
    html += '<div class="thumb' + (m.type==='video'?' video':'') + '"';
    if(m.type==='video') html += ' data-video="' + m.path + '"';
    html += '>';
    html += '<img src="' + src + '" alt="" loading="lazy">';
    if(m.type==='video') html += '<div class="vid-icon"></div>';
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function renderCards(tabId, pageNum){
  var data = tabsData[tabId];
  if(!data) return;
  var container = document.getElementById('cards-' + tabId);
  if(!container) return;
  var msgs = data.messages;
  var totalPages = Math.ceil(msgs.length / PAGE_SIZE) || 1;
  var p = Math.max(1, Math.min(pageNum, totalPages));
  var start = (p - 1) * PAGE_SIZE;
  var end = Math.min(start + PAGE_SIZE, msgs.length);
  var html = '';
  for(var i=start;i<end;i++){
    var m = msgs[i];
    html += '<div class="card" data-idx="' + i + '">';
    html += '<div class="card-header">';
    html += '<span class="card-source">' + escHtml(m.channel||'') + '</span>';
    html += '<span class="card-date">' + formatDate(m.date) + '</span>';
    html += '</div>';
    html += '<div class="card-text">' + escHtml(m.text||'') + '</div>';
    html += mediaHtml(m.media);
    if(m.media && m.media.length) html += '<div class="card-expand">展開詳情 ▾</div>';
    html += '</div>';
  }
  container.innerHTML = html;
  data.page = p;
  data.totalPages = totalPages;
  renderPagination(tabId);
}

function renderPagination(tabId){
  var data = tabsData[tabId];
  var wrap = document.getElementById('pagination-' + tabId);
  if(!wrap || !data || !data.messages) return;
  var total = data.totalPages || Math.ceil(data.messages.length / PAGE_SIZE) || 1;
  var cur = data.page || 1;
  if(total <= 1){
    wrap.innerHTML = '<span class="page-info">共 ' + data.messages.length + ' 筆</span>';
    return;
  }
  var html = '';
  html += '<button class="page-btn' + (cur===1?' disabled':'') + '" data-page="' + (cur-1) + '" data-tab="'+tabId+'">← 上一頁</button>';
  for(var i=1;i<=total;i++){
    if(total>7 && i>2 && i<total-1 && Math.abs(i-cur)>1){
      if(i===3 || i===total-2) html += '<span class="page-info">…</span>';
      continue;
    }
    html += '<button class="page-btn' + (i===cur?' active':'') + '" data-page="'+i+'" data-tab="'+tabId+'">'+i+'</button>';
  }
  html += '<button class="page-btn' + (cur===total?' disabled':'') + '" data-page="' + (cur+1) + '" data-tab="'+tabId+'">下一頁 →</button>';
  html += '<span class="page-info">共 ' + data.messages.length + ' 筆</span>';
  wrap.innerHTML = html;
}

function toggleCard(card){
  if(!card) return;
  var txt = card.querySelector('.card-text');
  var thumbs = card.querySelector('.card-thumbs');
  var exp = card.querySelector('.card-expand');
  if(!txt) return;
  if(card.hasAttribute('data-expanded')){
    card.removeAttribute('data-expanded');
    txt.classList.remove('full');
    if(thumbs) thumbs.classList.remove('expanded');
    if(exp) exp.innerHTML = '展開詳情 ▾';
  } else {
    card.setAttribute('data-expanded','');
    txt.classList.add('full');
    if(thumbs) thumbs.classList.add('expanded');
    if(exp) exp.innerHTML = '收合 ▴';
  }
}

function switchTab(tabId){
  if(tabId === currentTab) return;
  document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active');});
  document.querySelectorAll('.tab-content').forEach(function(c){c.classList.remove('active');});
  var nav = document.querySelector('.nav-item[data-tab="'+tabId+'"]');
  if(nav) nav.classList.add('active');
  var panel = document.getElementById('content-' + tabId);
  if(panel) panel.classList.add('active');
  currentTab = tabId;
  if(tabId === 'xvideos'){
    var xvData = window.__XV_DATA__;
    if(xvData && !xvData.page) renderXvCards(1);
  } else {
    var data = tabsData[tabId];
    if(data && !data.page) renderCards(tabId, 1);
  }
}

/* lightbox */
var lbState = { tabId:'', items:[], current:0 };

function openLightbox(tabId, startIndex){
  var container = document.getElementById('cards-' + tabId);
  if(!container) return;
  var wraps = container.querySelectorAll('.thumb');
  var items = [];
  wraps.forEach(function(w,i){
    var img = w.querySelector('img');
    var isVid = w.classList.contains('video');
    var src = isVid ? (w.getAttribute('data-video') || '') : (img ? img.getAttribute('src') : '');
    items.push({ index:i, isVideo:isVid, src: src });
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

/* xv embed toggle */
function toggleXvEmbed(btn){
  var card = btn.closest('.card');
  var embedDiv = btn.parentElement.querySelector('.xv-embed');
  if(!embedDiv) return;
  var eid = embedDiv.getAttribute('data-eid');
  if(card.classList.contains('expanded')){
    embedDiv.innerHTML = '';
    card.classList.remove('expanded');
    btn.textContent = '▶ 播放影片';
  } else {
    embedDiv.innerHTML = '<iframe src="https://www.xvideos.com/embedframe/'
      + eid + '" allowfullscreen frameborder="0" width="100%" height="420" loading="lazy"></iframe>';
    card.classList.add('expanded');
    btn.textContent = '▲ 收合';
  }
}

/* xv tag filter */
var xvActiveTag = 'all';
function filterXvTags(btn){
  var tag = btn.getAttribute('data-tag');
  xvActiveTag = tag;
  btn.parentElement.querySelectorAll('.tag-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderXvCards(1);
}

/* xv cards render */
function renderXvCards(pageNum){
  var data = window.__XV_DATA__;
  if(!data || !data.videos) return;
  var container = document.getElementById('cards-xvideos');
  if(!container) return;
  var videos = data.videos;
  if(xvActiveTag !== 'all'){
    videos = videos.filter(function(v){
      return (v.tags||[]).indexOf(xvActiveTag) !== -1;
    });
  }
  var totalPages = Math.ceil(videos.length / PAGE_SIZE) || 1;
  var p = Math.max(1, Math.min(pageNum, totalPages));
  var start = (p - 1) * PAGE_SIZE;
  var end = Math.min(start + PAGE_SIZE, videos.length);
  var html = '';
  for(var i=start;i<end;i++){
    var v = videos[i];
    var tagsStr = (v.tags||[]).join(',');
    var tagBadges = '';
    for(var t=0;t<(v.tags||[]).length;t++){
      tagBadges += '<span class="tag-badge">' + escHtml(v.tags[t]) + '</span>';
    }
    html += '<div class="card">';
    html += '<div class="card-header">';
    html += '<span class="card-source xv">xv · ' + escHtml(v.uploader||'') + tagBadges + '</span>';
    html += '<span class="card-date">' + escHtml(v.duration||'') + ' · ' + escHtml(v.quality||'') + ' · ' + escHtml(v.views||'') + '</span>';
    html += '</div>';
    html += '<div class="card-text full">' + escHtml(v.title||'') + '</div>';
    if(v.thumbnail){
      html += '<div class="card-thumbs"><div class="thumb video"><img src="' + v.thumbnail + '" alt="" loading="lazy" referrerpolicy="no-referrer"><div class="vid-icon"></div></div></div>';
    }
    html += '<div class="xv-embed" data-eid="' + escHtml(v.eid||'') + '"></div>';
    html += '<div class="card-expand xv-expand">▶ 播放影片</div>';
    html += '</div>';
  }
  container.innerHTML = html;
  data.page = p;
  data.totalPages = totalPages;
  renderXvPagination();
}

function renderXvPagination(){
  var data = window.__XV_DATA__;
  var wrap = document.getElementById('pagination-xvideos');
  if(!wrap || !data || !data.videos) return;
  var total = data.totalPages || Math.ceil(data.videos.length / PAGE_SIZE) || 1;
  var cur = data.page || 1;
  if(total <= 1){
    wrap.innerHTML = '<span class="page-info">共 ' + data.videos.length + ' 部</span>';
    return;
  }
  var html = '';
  html += '<button class="page-btn' + (cur===1?' disabled':'') + '" data-xv-page="' + (cur-1) + '">← 上一頁</button>';
  for(var i=1;i<=total;i++){
    if(total>7 && i>2 && i<total-1 && Math.abs(i-cur)>1){
      if(i===3 || i===total-2) html += '<span class="page-info">…</span>';
      continue;
    }
    html += '<button class="page-btn' + (i===cur?' active':'') + '" data-xv-page="'+i+'">'+i+'</button>';
  }
  html += '<button class="page-btn' + (cur===total?' disabled':'') + '" data-xv-page="' + (cur+1) + '">下一頁 →</button>';
  html += '<span class="page-info">共 ' + data.videos.length + ' 部</span>';
  wrap.innerHTML = html;
}

/* init */
function init(){
  var tabIds = [];
  document.querySelectorAll('.nav-item').forEach(function(item){
    var id = item.getAttribute('data-tab');
    tabIds.push(id);
    item.addEventListener('click', function(){ switchTab(id); });
  });

    if(tabIds.length > 0){
      tabIds.forEach(function(id){
        if(id === 'xvideos'){
          renderXvCards(1);
        } else {
          renderCards(id, 1);
        }
      });
      currentTab = tabIds[0];
    }

  document.addEventListener('click', function(e){
    var t = e.target;
    if(t.nodeType === 3) t = t.parentElement;
    if(!t) return;
    try{
    var loadBtn = t.closest('.page-btn:not(.disabled)');
    if(loadBtn){
      var tabId = loadBtn.getAttribute('data-tab');
      if(tabId){
        var page = parseInt(loadBtn.getAttribute('data-page'));
        if(tabId && page) renderCards(tabId, page);
      } else {
        var xvPage = loadBtn.getAttribute('data-xv-page');
        if(xvPage) renderXvCards(parseInt(xvPage));
      }
      return;
    }

    var tagBtn = t.closest('.tag-btn');
    if(tagBtn){ filterXvTags(tagBtn); return; }

    var xvExpand = t.closest('.xv-expand');
    if(xvExpand){ toggleXvEmbed(xvExpand); return; }

    var thumb = t.closest('.thumb');
    if(thumb){
      var card2 = thumb.closest('.card');
      if(card2){
        var container2 = card2.closest('.cards-container');
        if(container2){
          var tabId2 = container2.id.replace('cards-','');
          var allThumbs = container2.querySelectorAll('.thumb');
          var idx2 = -1;
          allThumbs.forEach(function(el,i){ if(el === thumb) idx2 = i; });
          if(idx2 >= 0) openLightbox(tabId2, idx2);
        }
      }
      return;
    }

    var card = t.closest('.card');
    if(card){
      var onThumb = t.closest('.thumb');
      var onPageBtn = t.closest('.page-btn');
      if(!onThumb && !onPageBtn){
        toggleCard(card);
      }
    }
    }catch(ex){}
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
    xv_videos = _load_xvideos()

    bottom_nav = ""
    tabs_content = ""
    first_id = None

    nav_items = [
        ("mens_fantasy", "異想空間", "🏠"),
        ("news", "大事件", "📰"),
        ("guaba_bl", "吃瓜", "🔥"),
        ("ai_drama", "AI短劇", "🎬"),
    ]

    for tab_id, name, icon in nav_items:
        tab = tabs.get(tab_id)
        if not tab:
            continue
        if first_id is None:
            first_id = tab_id
        active = " active" if tab_id == first_id else ""
        bottom_nav += (
            f'<div class="nav-item{active}" data-tab="{tab_id}">'
            f'<span class="icon">{icon}</span><span>{name}</span></div>'
        )
        tabs_content += f'''<div class="tab-content{active}" id="content-{tab_id}">
    <div class="cards-container" id="cards-{tab_id}"></div>
    <div class="pagination" id="pagination-{tab_id}"></div>
  </div>'''

    xv_count = len(xv_videos)
    xv_active = "" if tabs else " active"
    if not first_id:
        first_id = "xvideos"

    bottom_nav += (
        f'<div class="nav-item{xv_active}" data-tab="xvideos">'
        f'<span class="icon">👊</span><span>弟兄們</span></div>'
    )

    xv_tag_counts = _build_xv_tag_counts(xv_videos)
    tag_bar = '<div class="tag-bar">'
    tag_bar += f'<button class="tag-btn active" data-tag="all">全部 <span class="tag-count">{xv_count}</span></button>'
    for tag, count in sorted(xv_tag_counts.items()):
        tag_bar += f'<button class="tag-btn" data-tag="{tag}">{tag} <span class="tag-count">{count}</span></button>'
    tag_bar += '</div>'

    tabs_content += f'''<div class="tab-content{xv_active}" id="content-xvideos">
    {tag_bar}
    <div class="cards-container" id="cards-xvideos"></div>
    <div class="pagination" id="pagination-xvideos"></div>
  </div>'''

    if first_id is None:
        first_id = "xvideos"

    tabs_json = _json.dumps(tabs, ensure_ascii=False, default=str)
    xv_json = _json.dumps({"videos": xv_videos, "total": xv_count}, ensure_ascii=False, default=str)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Man's Fantasy</title>
<style>{CSS}</style>
</head>
<body>

<div class="app-shell">

<header class="app-header">
  <span class="title">MAN'S FANTASY</span>
  <span class="time">更新 {_now_str()}</span>
</header>

<main class="app-content">
  {tabs_content}
</main>

<nav class="bottom-nav">
  {bottom_nav}
</nav>

</div>

<div class="lightbox" id="lightbox" role="dialog" aria-label="圖片檢視">
  <span class="lb-close" id="lb-close">&times;</span>
  <span class="lb-prev" id="lb-prev">&lsaquo;</span>
  <span class="lb-next" id="lb-next">&rsaquo;</span>
  <div class="lb-content" id="lb-content"></div>
  <span class="lb-counter" id="lb-counter"></span>
</div>

<script>
window.__DATA__ = {tabs_json};
window.__XV_DATA__ = {xv_json};
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
