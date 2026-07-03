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
  .time-presets{display:flex;gap:4px;flex-wrap:wrap}
  .preset-btn{padding:0.35rem 0.6rem;font-size:0.75rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--border);border-radius:4px;transition:all .15s}
  .preset-btn:hover{color:var(--fg-secondary);border-color:var(--muted)}
  .preset-btn.active{color:var(--fg);background:var(--accent-bg);border-color:var(--accent)}
  .search-bar .result-count{font-size:0.8rem;color:var(--muted);margin-left:auto}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin-bottom:0.75rem;transition:border-color .2s}
  .card:hover{border-color:var(--muted)}
  .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;font-size:0.78rem;color:var(--muted)}
  .card-source{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;background:var(--surface-2);border-radius:4px;color:var(--fg-secondary);font-size:0.75rem}
  .card-source::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent)}
  .card-date{font-family:var(--font-display);font-size:0.75rem;color:var(--muted)}
  .card-text{font-size:0.9rem;line-height:1.65;margin-bottom:0.5rem;word-wrap:break-word;white-space:pre-wrap;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical}
  .card-text.full{-webkit-line-clamp:unset;display:block}
  .card-thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:4px;margin-top:0.5rem}
  .card-thumbs.expanded{grid-template-columns:repeat(auto-fill,minmax(120px,1fr))}
  .thumb{position:relative;aspect-ratio:1;overflow:hidden;border-radius:4px;background:var(--surface-2);cursor:pointer}
  .thumb img{width:100%;height:100%;object-fit:cover}
  .thumb .vid-icon{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:24px;height:24px;background:rgba(0,0,0,0.6);border-radius:50%;display:flex;align-items:center;justify-content:center;pointer-events:none}
  .thumb .vid-icon::after{content:'';border-left:8px solid #fff;border-top:5px solid transparent;border-bottom:5px solid transparent;margin-left:2px}
  .card-expand{text-align:center;font-size:0.8rem;color:var(--muted);margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid var(--border);cursor:pointer;user-select:none}
  .card-expand:hover{color:var(--fg-secondary)}
  .load-more-wrap{padding:1rem 0;text-align:center}
  .pagination{display:flex;justify-content:center;align-items:center;gap:4px;padding:1rem 0;flex-wrap:wrap}
  .page-btn{min-width:36px;height:36px;display:flex;align-items:center;justify-content:center;padding:0 8px;font-size:0.82rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--border);border-radius:4px;cursor:pointer;transition:all .15s;user-select:none}
  .page-btn:hover{color:var(--fg);border-color:var(--muted)}
  .page-btn.active{color:var(--fg);background:var(--accent-bg);border-color:var(--accent)}
  .page-btn.disabled{color:var(--muted);opacity:0.4;cursor:default;pointer-events:none}
  .page-info{font-size:0.8rem;color:var(--muted);padding:0 12px}
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
  /* xv tag bar */
  .tag-bar{display:flex;gap:6px;margin-bottom:1rem;flex-wrap:wrap}
  .tag-btn{padding:0.35rem 0.7rem;font-size:0.78rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--border);border-radius:4px;cursor:pointer;transition:all .15s;user-select:none}
  .tag-btn:hover{color:var(--fg-secondary);border-color:var(--muted)}
  .tag-btn.active{color:var(--fg);background:var(--accent-bg);border-color:var(--accent)}
  .tag-count{font-size:0.7rem;color:var(--muted);margin-left:3px}
  /* xv source */
  .card-source.xv::before{background:#a070e0}
  /* xv embed */
  .xv-embed{margin-top:0.5rem;border-radius:6px;overflow:hidden;background:#000}
  .xv-embed iframe{display:block;border:none;width:100%;min-height:420px}
  /* xv tag badge */
  .tag-badge{display:inline-block;font-size:0.65rem;padding:1px 6px;border-radius:3px;background:rgba(160,112,224,0.15);color:#b8a0e0;margin-left:4px;vertical-align:middle}
  @media(max-width:600px){
    .xv-embed iframe{min-height:240px}
    .header{padding:1.2rem 0.8rem 0.8rem}
    main{padding:0 0.6rem}
    .card{padding:0.8rem}
    .search-bar{flex-direction:column;align-items:stretch}
    .result-count{margin-left:0;text-align:right}
    .tab-btn{font-size:0.82rem;padding:0.7rem 0.5rem}
    .card-thumbs{grid-template-columns:repeat(auto-fill,minmax(64px,1fr))}
    .card-thumbs.expanded{grid-template-columns:repeat(auto-fill,minmax(90px,1fr))}
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
  if(tabId === 'xvideos'){
    var xvData = window.__XV_DATA__;
    if(xvData && !xvData.page) renderXvCards(1);
  } else {
    var data = tabsData[tabId];
    if(data && !data.page) renderCards(tabId, 1);
  }
  applySearch(tabId);
}

function applySearch(tabId){
  var container = document.getElementById('cards-' + tabId);
  var searchInput = document.querySelector('#tab-' + tabId + ' .search-input');
  var resultEl = document.getElementById('result-count-' + tabId);
  if(!container || !searchInput) return;

  var kw = searchInput.value.trim().toLowerCase();
  var activePreset = document.querySelector('#tab-' + tabId + ' .preset-btn.active');
  var range = activePreset ? activePreset.getAttribute('data-range') : 'all';
  var isSearching = kw !== '' || range !== 'all';

  var now = new Date();
  var cutoff = null;
  if(range==='today'){ cutoff = new Date(now.getFullYear(),now.getMonth(),now.getDate()); }
  else if(range==='3d'){ cutoff = new Date(now.getTime() - 3*86400000); }
  else if(range==='7d'){ cutoff = new Date(now.getTime() - 7*86400000); }
  else if(range==='month'){ cutoff = new Date(now.getFullYear(),now.getMonth(),1); }
  else if(range==='halfyear'){ cutoff = new Date(now.getTime() - 180*86400000); }

  var cards = container.querySelectorAll('.card');
  var matched = 0;
  for(var i=0;i<cards.length;i++){
    var card = cards[i];
    var textEl = card.querySelector('.card-text');
    var dateEl = card.querySelector('.card-date');
    var text = textEl ? textEl.textContent.toLowerCase() : '';
    var show = true;
    if(kw && text.indexOf(kw) === -1) show = false;
    if(cutoff){
      var d = dateEl ? dateEl.textContent.trim().slice(0,10) : '';
      if(d < cutoff.toISOString().slice(0,10)) show = false;
    }
    if(show) matched++;
    card.classList.toggle('hidden', !show);
  }

  if(isSearching){
    resultEl.textContent = matched + ' 筆結果';
    var pagWrap = document.getElementById('pagination-' + tabId);
    if(pagWrap) pagWrap.innerHTML = '';
  } else {
    resultEl.textContent = '';
    renderPagination(tabId);
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
function filterXvTags(btn){
  var tag = btn.getAttribute('data-tag');
  var container = btn.closest('.tab-content');
  if(!container) return;
  btn.parentElement.querySelectorAll('.tag-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  container.querySelectorAll('.card[data-tags]').forEach(function(card){
    if(tag === 'all'){
      card.classList.remove('hidden');
    } else {
      var tags = card.getAttribute('data-tags').split(',');
      card.classList.toggle('hidden', tags.indexOf(tag) === -1);
    }
  });
}

/* xv cards render */
function renderXvCards(pageNum){
  var data = window.__XV_DATA__;
  if(!data || !data.videos) return;
  var container = document.getElementById('cards-xvideos');
  if(!container) return;
  var videos = data.videos;
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
    html += '<div class="card" data-tags="' + tagsStr + '">';
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
  document.querySelectorAll('.tab-btn').forEach(function(btn){
    var id = btn.getAttribute('data-tab');
    tabIds.push(id);
    btn.addEventListener('click', function(){ switchTab(id); });
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
    try{
    var loadBtn = e.target.closest('.page-btn:not(.disabled)');
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

    var tagBtn = e.target.closest('.tag-btn');
    if(tagBtn){ filterXvTags(tagBtn); return; }

    var xvExpand = e.target.closest('.xv-expand');
    if(xvExpand){ toggleXvEmbed(xvExpand); return; }

    var thumb = e.target.closest('.thumb');
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

    var preset = e.target.closest('.preset-btn');
    if(preset){
      var bar = preset.closest('.search-bar');
      bar.querySelectorAll('.preset-btn').forEach(function(b){ b.classList.remove('active'); });
      preset.classList.add('active');
      var panel = preset.closest('.tab-content');
      if(panel){ applySearch(panel.id.replace('tab-','')); }
      return;
    }

    var card = e.target.closest('.card');
    if(card){
      var onThumb = e.target.closest('.thumb');
      var onPageBtn = e.target.closest('.page-btn');
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

  document.querySelectorAll('.tab-content').forEach(function(panel){
    var si = panel.querySelector('.search-input');
    if(si) si.addEventListener('input', function(){
      applySearch(panel.id.replace('tab-',''));
    });
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
      <div class="time-presets">
        <button class="preset-btn active" data-range="all">全部</button>
        <button class="preset-btn" data-range="today">今日</button>
        <button class="preset-btn" data-range="3d">近3日</button>
        <button class="preset-btn" data-range="7d">近7日</button>
        <button class="preset-btn" data-range="month">本月</button>
        <button class="preset-btn" data-range="halfyear">近半年</button>
      </div>
      <span class="result-count" id="result-count-{tab_id}"></span>
    </div>
    <div class="cards-container" id="cards-{tab_id}"></div>
    <div class="pagination" id="pagination-{tab_id}"></div>
  </div>'''

    # xvideos tab
    xv_count = len(xv_videos)
    xv_tag_counts = _build_xv_tag_counts(xv_videos)
    xv_active_cls = "" if tabs else " active"
    if not first_id:
        first_id = "xvideos"

    tabs_nav += (
        f'<button class="tab-btn{xv_active_cls}" role="tab" '
        f'aria-selected="{str(not tabs).lower()}" '
        f'data-tab="xvideos">衝啊, 弟兄們 '
        f'<span class="badge">{xv_count}</span></button>'
    )

    tag_bar = '<div class="tag-bar">'
    tag_bar += f'<button class="tag-btn active" data-tag="all">全部 <span class="tag-count">{xv_count}</span></button>'
    for tag, count in sorted(xv_tag_counts.items()):
        tag_bar += f'<button class="tag-btn" data-tag="{tag}">{tag} <span class="tag-count">{count}</span></button>'
    tag_bar += '</div>'

    tabs_content += f'''<div class="tab-content{xv_active_cls}" id="tab-xvideos" role="tabpanel">
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
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Man's Fantasy</title>
<style>{CSS}</style>
</head>
<body>

<header class="header">
  <h1>Man's Fantasy</h1>
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
