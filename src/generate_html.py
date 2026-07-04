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


ICON_MAP = {
    "mens_fantasy": "🏠",
    "news": "📰",
    "guaba_bl": "🔥",
    "ai_drama": "🎬",
}
DEFAULT_ICON = "📌"


CSS = r"""
  :root {
    --bg: #0a0a0a; --surface: #161616; --surface-2: #1e1e1e;
    --fg: #e5e5e5; --fg-secondary: #a0a0a0; --muted: #6a6a6a;
    --border: #2a2a2a; --accent: #d14334; --accent-hover: #e05545;
    --accent-bg: rgba(209,67,52,0.08); --radius: 10px; --app-w: 560px;
    --font-body: -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{font-size:15px}
  body{font-family:var(--font-body);background:#000;color:var(--fg);line-height:1.5;display:flex;justify-content:center;min-height:100dvh;-webkit-tap-highlight-color:transparent}
  button{cursor:pointer;font:inherit;border:none;background:none;color:inherit}
  input{font:inherit;color:inherit}
  img{max-width:100%;display:block}

  .app{width:100%;max-width:var(--app-w);min-height:100dvh;background:var(--bg);display:flex;flex-direction:column}

  .app-header{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;padding:0.7rem 0.9rem;border-bottom:1px solid var(--border);background:rgba(10,10,10,0.96)}
  .app-title{font-size:0.95rem;font-weight:600;letter-spacing:0.03em}
  .header-right{display:flex;align-items:center;gap:0.6rem}
  .header-right .time{font-size:0.68rem;color:var(--muted)}
  .search-toggle{width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:1rem;border-radius:50%;color:var(--fg-secondary)}
  .search-toggle.active{color:var(--accent);background:var(--accent-bg)}

  .search-panel{max-height:0;overflow:hidden;transition:max-height .2s ease;border-bottom:1px solid transparent}
  .search-panel.open{max-height:140px;border-bottom-color:var(--border)}
  .search-panel-inner{display:flex;flex-wrap:wrap;gap:0.5rem;padding:0.75rem 0.9rem;align-items:center}
  .search-panel input[type="text"]{flex:1;min-width:120px;padding:0.5rem 0.7rem;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;font-size:0.82rem;color:var(--fg);outline:none}
  .search-panel input[type="text"]:focus{border-color:var(--accent)}
  .time-presets{display:flex;gap:4px;flex-wrap:wrap}
  .preset-btn{padding:0.35rem 0.6rem;font-size:0.72rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--border);border-radius:6px}
  .preset-btn.active{color:var(--fg);border-color:var(--accent);background:var(--accent-bg)}
  .result-count{font-size:0.72rem;color:var(--muted);width:100%}

  .app-content{flex:1;padding:0.75rem 0.75rem 5rem}
  .tab-content{display:none}
  .tab-content.active{display:block}

  .waterfall{display:flex;gap:0.6rem}
  .wf-col{flex:1;display:flex;flex-direction:column;gap:0.6rem;min-width:0}

  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
  .card-cover{position:relative}
  .card-cover img{width:100%;object-fit:cover}
  .badge-count{position:absolute;top:6px;right:6px;background:rgba(0,0,0,0.6);color:#fff;font-size:0.66rem;padding:2px 6px;border-radius:10px}
  .badge-play{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:34px;height:34px;background:rgba(0,0,0,0.55);border-radius:50%;display:flex;align-items:center;justify-content:center}
  .badge-play::after{content:'';border-left:11px solid #fff;border-top:7px solid transparent;border-bottom:7px solid transparent;margin-left:3px}
  .card-body{padding:0.6rem 0.65rem}
  .card-text{font-size:0.82rem;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;margin-bottom:0.4rem;white-space:pre-wrap}
  .card-foot{display:flex;justify-content:space-between;align-items:center;font-size:0.68rem;color:var(--muted)}
  .card-source{display:inline-flex;align-items:center;gap:4px}
  .card-source::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent)}

  .textonly-list .card{width:100%;margin-bottom:0.6rem}
  .card.text-only .card-body{padding:0.75rem 0.8rem}
  .card.text-only .card-text{-webkit-line-clamp:3;font-size:0.86rem}
  .card.text-only .card-text.full{-webkit-line-clamp:unset}
  .card.text-only .card-expand{font-size:0.7rem;color:var(--muted);text-align:center;padding-top:0.4rem;margin-top:0.4rem;border-top:1px solid var(--border);cursor:pointer;user-select:none}

  .sentinel{text-align:center;font-size:0.72rem;color:var(--muted);padding:1rem 0}

  .sheet-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:50}
  .sheet-backdrop.open{display:block}
  .sheet{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:100%;max-width:var(--app-w);max-height:85vh;background:var(--surface);border-radius:16px 16px 0 0;z-index:51;display:flex;flex-direction:column;overflow:hidden}
  .sheet-header{display:flex;justify-content:space-between;align-items:center;padding:0.8rem 1rem;border-bottom:1px solid var(--border)}
  .sheet-close{font-size:1.3rem;color:var(--fg-secondary)}
  .sheet-body{overflow-y:auto;padding:0.9rem 1rem}
  .full-text{font-size:0.88rem;line-height:1.7;margin-bottom:0.8rem;white-space:pre-wrap}
  .sheet-thumbs{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
  .sheet-thumbs .thumb{position:relative;aspect-ratio:1;border-radius:8px;overflow:hidden;cursor:pointer}
  .sheet-thumbs .thumb img{width:100%;height:100%;object-fit:cover}

  .lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,0.94)}
  .lightbox.open{display:flex;align-items:center;justify-content:center}
  .lb-close{position:absolute;top:1rem;right:1rem;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.1)}
  .lb-prev,.lb-next{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.06)}
  .lb-prev{left:0.5rem}
  .lb-next{right:0.5rem}
  .lb-counter{position:absolute;bottom:1.5rem;left:50%;transform:translateX(-50%);color:rgba(255,255,255,0.6);font-size:0.85rem;z-index:2}
  .lb-content{max-width:92vw;max-height:85vh;display:flex;align-items:center;justify-content:center}
  .lb-content img,.lb-content video{max-width:100%;max-height:85vh;object-fit:contain;border-radius:4px}

  .bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:var(--app-w);display:flex;justify-content:space-around;background:rgba(10,10,10,0.97);border-top:1px solid var(--border);z-index:20;padding:0.35rem 0 max(0.35rem,env(safe-area-inset-bottom))}
  .nav-item{display:flex;flex-direction:column;align-items:center;gap:2px;padding:0.3rem;min-width:56px;font-size:0.62rem;color:var(--muted)}
  .nav-item .icon{font-size:1.25rem;line-height:1}
  .nav-item.active{color:var(--accent)}
"""

JS = r"""'use strict';
(function(){
var PAGE_SIZE = 20,
    tabsData = window.__DATA__,
    currentTab = '';

function escHtml(s){
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function escAttr(s){ return escHtml(s); }

function formatDate(iso){
  var d = new Date(iso);
  var m = String(d.getMonth()+1).padStart(2,'0');
  var day = String(d.getDate()).padStart(2,'0');
  var h = String(d.getHours()).padStart(2,'0');
  var min = String(d.getMinutes()).padStart(2,'0');
  return m + '-' + day + ' ' + h + ':' + min;
}

function cardImageHtml(tabId, idx, m){
  var cover = m.media[0];
  var src = cover.thumb || cover.path;
  var badge = m.media.length > 1 ? '<span class="badge-count">📷 ' + m.media.length + '</span>' : '';
  var play = cover.type === 'video' ? '<span class="badge-play"></span>' : '';
  return '<div class="card" data-tab="' + tabId + '" data-idx="' + idx + '">'
    + '<div class="card-cover"><img src="' + escAttr(src) + '" loading="lazy">' + badge + play + '</div>'
    + '<div class="card-body">'
    + '<div class="card-text">' + escHtml(m.text||'') + '</div>'
    + '<div class="card-foot"><span class="card-source">' + escHtml(m.channel||'') + '</span><span>' + formatDate(m.date) + '</span></div>'
    + '</div></div>';
}

function cardTextOnlyHtml(tabId, idx, m){
  return '<div class="card text-only" data-tab="' + tabId + '" data-idx="' + idx + '">'
    + '<div class="card-body">'
    + '<div class="card-text">' + escHtml(m.text||'') + '</div>'
    + '<div class="card-foot"><span class="card-source">' + escHtml(m.channel||'') + '</span><span>' + formatDate(m.date) + '</span></div>'
    + '<div class="card-expand">展開詳情 ▾</div>'
    + '</div></div>';
}

function appendItems(tabId, indices){
  var data = tabsData[tabId];
  var col0 = document.getElementById('wfcol-' + tabId + '-0');
  var col1 = document.getElementById('wfcol-' + tabId + '-1');
  var textWrap = document.getElementById('textonly-' + tabId);
  indices.forEach(function(i){
    var m = data.messages[i];
    if(m.media && m.media.length){
      var target = (data.wfCounter % 2 === 0) ? col0 : col1;
      target.insertAdjacentHTML('beforeend', cardImageHtml(tabId, i, m));
      data.wfCounter++;
    } else {
      textWrap.insertAdjacentHTML('beforeend', cardTextOnlyHtml(tabId, i, m));
    }
  });
}

function updateSentinel(tabId){
  var data = tabsData[tabId];
  var sentinel = document.getElementById('sentinel-' + tabId);
  if(!sentinel) return;
  sentinel.textContent = data.loaded >= data.messages.length ? '已無更多內容' : '載入更多…';
}

function loadNextBatch(tabId){
  var data = tabsData[tabId];
  if(!data || data.loaded >= data.messages.length) return;
  var start = data.loaded;
  var end = Math.min(start + PAGE_SIZE, data.messages.length);
  var indices = [];
  for(var i=start;i<end;i++) indices.push(i);
  appendItems(tabId, indices);
  data.loaded = end;
  updateSentinel(tabId);
}

function clearTabView(tabId){
  document.getElementById('wfcol-' + tabId + '-0').innerHTML = '';
  document.getElementById('wfcol-' + tabId + '-1').innerHTML = '';
  document.getElementById('textonly-' + tabId).innerHTML = '';
}

function resetTabView(tabId){
  var data = tabsData[tabId];
  data.loaded = 0;
  data.wfCounter = 0;
  clearTabView(tabId);
  loadNextBatch(tabId);
}

function computeCutoffIso(range){
  var now = new Date();
  if(range==='today') return new Date(now.getFullYear(),now.getMonth(),now.getDate()).toISOString();
  if(range==='3d') return new Date(now.getTime() - 3*86400000).toISOString();
  if(range==='7d') return new Date(now.getTime() - 7*86400000).toISOString();
  if(range==='month') return new Date(now.getFullYear(),now.getMonth(),1).toISOString();
  if(range==='halfyear') return new Date(now.getTime() - 180*86400000).toISOString();
  return null;
}

function applySearch(tabId){
  var data = tabsData[tabId];
  var panel = document.getElementById('search-panel-' + tabId);
  var input = panel.querySelector('.search-input');
  var resultEl = document.getElementById('result-count-' + tabId);
  var sentinel = document.getElementById('sentinel-' + tabId);
  var activePreset = panel.querySelector('.preset-btn.active');
  var range = activePreset ? activePreset.getAttribute('data-range') : 'all';
  var kw = input.value.trim().toLowerCase();
  var isSearching = kw !== '' || range !== 'all';

  if(!isSearching){
    resultEl.textContent = '';
    sentinel.style.display = '';
    resetTabView(tabId);
    return;
  }

  sentinel.style.display = 'none';
  var cutoff = computeCutoffIso(range);
  var matched = [];
  data.messages.forEach(function(m, i){
    var text = (m.text||'').toLowerCase();
    if(kw && text.indexOf(kw) === -1) return;
    if(cutoff && m.date < cutoff) return;
    matched.push(i);
  });
  resultEl.textContent = matched.length + ' 筆結果';
  clearTabView(tabId);
  data.wfCounter = 0;
  appendItems(tabId, matched);
}

/* detail sheet */
function openSheet(tabId, idx){
  var data = tabsData[tabId];
  var m = data.messages[idx];
  if(!m.media || !m.media.length) return;
  var body = document.getElementById('sheet-body');
  var thumbs = m.media.map(function(item){
    var src = item.thumb || item.path;
    var play = item.type === 'video' ? '<span class="badge-play"></span>' : '';
    return '<div class="thumb" data-src="' + escAttr(item.path) + '" data-type="' + item.type + '"><img src="' + escAttr(src) + '">' + play + '</div>';
  }).join('');
  body.innerHTML = '<div class="full-text">' + escHtml(m.text||'') + '</div><div class="sheet-thumbs">' + thumbs + '</div>';
  document.getElementById('sheet-backdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeSheet(){
  document.getElementById('sheet-backdrop').classList.remove('open');
  document.body.style.overflow = '';
}

function toggleTextCard(card){
  var txt = card.querySelector('.card-text');
  var exp = card.querySelector('.card-expand');
  if(card.hasAttribute('data-expanded')){
    card.removeAttribute('data-expanded');
    txt.classList.remove('full');
    if(exp) exp.textContent = '展開詳情 ▾';
  } else {
    card.setAttribute('data-expanded','');
    txt.classList.add('full');
    if(exp) exp.textContent = '收合 ▴';
  }
}

/* lightbox */
var lbState = { items:[], current:0 };

function openLightbox(items, startIndex){
  if(items.length===0) return;
  lbState.items = items;
  lbState.current = startIndex;
  showLightboxItem();
  document.getElementById('lightbox').classList.add('open');
}

function showLightboxItem(){
  var content = document.getElementById('lb-content');
  var counter = document.getElementById('lb-counter');
  var item = lbState.items[lbState.current];
  counter.textContent = (lbState.current+1) + ' / ' + lbState.items.length;
  if(item.isVideo){
    content.innerHTML = '<video src="'+item.src+'" controls autoplay></video>';
  } else {
    content.innerHTML = '<img src="'+item.src+'" alt="">';
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
}

function switchTab(tabId){
  if(tabId === currentTab) return;
  document.querySelectorAll('.nav-item').forEach(function(b){
    b.classList.remove('active'); b.setAttribute('aria-selected','false');
  });
  document.querySelectorAll('.tab-content').forEach(function(c){
    c.classList.remove('active');
  });
  var btn = document.querySelector('.nav-item[data-tab="'+tabId+'"]');
  if(btn){ btn.classList.add('active'); btn.setAttribute('aria-selected','true'); }
  var panel = document.getElementById('tab-' + tabId);
  if(panel) panel.classList.add('active');
  currentTab = tabId;

  var searchToggle = document.getElementById('search-toggle');
  var searchPanel = document.getElementById('search-panel-' + tabId);
  if(searchToggle && searchPanel){
    searchToggle.classList.toggle('active', searchPanel.classList.contains('open'));
  }
}

/* init */
function init(){
  var tabIds = [];
  document.querySelectorAll('.nav-item').forEach(function(btn){
    var id = btn.getAttribute('data-tab');
    tabIds.push(id);
    btn.addEventListener('click', function(){ switchTab(id); });
  });

  tabIds.forEach(function(id){
    tabsData[id].loaded = 0;
    tabsData[id].wfCounter = 0;
    loadNextBatch(id);
  });
  if(tabIds.length > 0) currentTab = tabIds[0];

  var searchToggle = document.getElementById('search-toggle');
  if(searchToggle) searchToggle.addEventListener('click', function(){
    var panel = document.querySelector('.tab-content.active .search-panel');
    if(!panel) return;
    panel.classList.toggle('open');
    searchToggle.classList.toggle('active');
  });

  document.querySelectorAll('.search-input').forEach(function(inp){
    inp.addEventListener('input', function(){
      var tabId = inp.closest('.tab-content').id.replace('tab-','');
      applySearch(tabId);
    });
  });

  document.addEventListener('click', function(e){
    try{
    var preset = e.target.closest('.preset-btn');
    if(preset){
      var bar = preset.closest('.time-presets');
      bar.querySelectorAll('.preset-btn').forEach(function(b){ b.classList.remove('active'); });
      preset.classList.add('active');
      var panel = preset.closest('.tab-content');
      if(panel){ applySearch(panel.id.replace('tab-','')); }
      return;
    }

    var sheetThumb = e.target.closest('.sheet-thumbs .thumb');
    if(sheetThumb){
      var allThumbs = Array.prototype.slice.call(document.querySelectorAll('.sheet-thumbs .thumb'));
      var idx = allThumbs.indexOf(sheetThumb);
      var items = allThumbs.map(function(t){
        return { isVideo: t.getAttribute('data-type') === 'video', src: t.getAttribute('data-src') };
      });
      if(idx >= 0) openLightbox(items, idx);
      return;
    }

    var textCard = e.target.closest('.card.text-only');
    if(textCard){
      toggleTextCard(textCard);
      return;
    }

    var card = e.target.closest('.card:not(.text-only)');
    if(card){
      var tabId2 = card.getAttribute('data-tab');
      var idx2 = parseInt(card.getAttribute('data-idx'), 10);
      openSheet(tabId2, idx2);
      return;
    }
    }catch(ex){}
  });

  document.getElementById('sheet-close').addEventListener('click', closeSheet);
  document.getElementById('sheet-backdrop').addEventListener('click', function(e){
    if(e.target === this) closeSheet();
  });

  document.getElementById('lb-close').addEventListener('click', closeLightbox);
  document.getElementById('lightbox').addEventListener('click', function(e){
    if(e.target === this) closeLightbox();
  });

  document.addEventListener('keydown', function(e){
    if(!document.getElementById('lightbox').classList.contains('open')) return;
    if(e.key === 'Escape'){ closeLightbox(); e.preventDefault(); }
    if(e.key === 'ArrowLeft'){ lbPrev(); e.preventDefault(); }
    if(e.key === 'ArrowRight'){ lbNext(); e.preventDefault(); }
  });

  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        loadNextBatch(entry.target.id.replace('sentinel-',''));
      }
    });
  }, { rootMargin: '200px' });
  document.querySelectorAll('.sentinel').forEach(function(s){ io.observe(s); });
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

    bottom_nav = ""
    tabs_content = ""
    first_id = None

    for tab_id, tab in tabs.items():
        if first_id is None:
            first_id = tab_id
        active_cls = " active" if tab_id == first_id else ""
        icon = ICON_MAP.get(tab_id, DEFAULT_ICON)
        bottom_nav += (
            f'<button class="nav-item{active_cls}" role="tab" '
            f'aria-selected="{str(tab_id == first_id).lower()}" '
            f'data-tab="{tab_id}">'
            f'<span class="icon">{icon}</span><span class="label">{tab["name"]}</span></button>'
        )

        tabs_content += f'''<div class="tab-content{active_cls}" id="tab-{tab_id}" role="tabpanel">
    <div class="search-panel" id="search-panel-{tab_id}">
      <div class="search-panel-inner">
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
    </div>
    <div class="waterfall" id="waterfall-{tab_id}">
      <div class="wf-col" id="wfcol-{tab_id}-0"></div>
      <div class="wf-col" id="wfcol-{tab_id}-1"></div>
    </div>
    <div class="textonly-list" id="textonly-{tab_id}"></div>
    <div class="sentinel" id="sentinel-{tab_id}">載入更多…</div>
  </div>'''

    tabs_json = _json.dumps(tabs, ensure_ascii=False, default=str)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Man's Fantasy</title>
<style>{CSS}</style>
</head>
<body>
<div class="app">

<header class="app-header">
  <span class="app-title">Man's Fantasy</span>
  <div class="header-right">
    <span class="time">更新：<span id="update-time">{_now_str()}</span></span>
    <button class="search-toggle" id="search-toggle" aria-label="搜尋">🔍</button>
  </div>
</header>

<main class="app-content" id="main-content">
  {tabs_content}
</main>

<nav class="bottom-nav" role="tablist">
  {bottom_nav}
</nav>

</div>

<div class="sheet-backdrop" id="sheet-backdrop">
  <div class="sheet" role="dialog" aria-label="貼文詳情">
    <div class="sheet-header">
      <span>貼文詳情</span>
      <span class="sheet-close" id="sheet-close">&times;</span>
    </div>
    <div class="sheet-body" id="sheet-body"></div>
  </div>
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
