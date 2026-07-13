import json as _json
from datetime import datetime
from pathlib import Path

import tg_core


def _load_xvideos():
    xv_file = tg_core.DOWNLOAD_DIR / "xvideos" / "videos.jsonl"
    videos = []
    if xv_file.exists():
        with open(xv_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        v = _json.loads(line)
                        videos.append({
                            "id": f"xv_{v.get('eid', '')}",
                            "date": v.get("fetched_at", ""),
                            "text": v.get("title", ""),
                            "channel": "xvideos",
                            "media": [],
                            "_xv": True,
                            "video_id": str(v.get("video_id", "")),
                            "thumbnail": v.get("thumbnail", ""),
                            "duration": v.get("duration", ""),
                            "media_path": v.get("media_path", ""),
                        })
                    except (_json.JSONDecodeError, ValueError):
                        pass
    return videos


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
            if not p:
                continue
            if p.startswith("https://") or p.startswith("http://"):
                continue
            if not p.startswith(f"{channel_id}/"):
                media["path"] = f"{channel_id}/{p}"
            thumb = media.get("thumb", "")
            if thumb and (not thumb.startswith("https://")) and (not thumb.startswith("http://")):
                if not thumb.startswith(f"{channel_id}/"):
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

    xvideos = _load_xvideos()
    xvideos.sort(key=lambda x: x.get("date", ""), reverse=True)
    tabs["xvideo"] = {
        "name": "xvideo",
        "messages": xvideos,
        "total": len(xvideos),
    }

    return tabs


ICON_MAP = {
    "mens_fantasy": "🏠",
    "news": "📰",
    "guaba_bl": "🔥",
    "ai_drama": "🎬",
    "xvideo": "❌",
}
DEFAULT_ICON = "📌"


CSS = r"""
  :root {
    --bg: #0a0a0a; --surface: #161616; --surface-2: #1e1e1e;
    --fg: #e5e5e5; --fg-secondary: #a0a0a0; --muted: #6a6a6a;
    --border: #2a2a2a; --accent: #d14334; --accent-hover: #e05545;
    --radius: 8px; --app-w: 560px;
    --font-body: -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{font-size:15px}
  body{font-family:var(--font-body);background:#000;color:var(--fg);line-height:1.5;display:flex;justify-content:center;min-height:100dvh;-webkit-tap-highlight-color:transparent}
  button{cursor:pointer;font:inherit;border:none;background:none;color:inherit}
  input{font:inherit;color:inherit}
  img{max-width:100%;display:block}
  .app{width:100%;max-width:var(--app-w);min-height:100dvh;background:var(--bg)}

  .search-bar{position:sticky;top:0;z-index:10;padding:0.6rem 0.75rem;background:rgba(10,10,10,0.96);display:flex;align-items:center;gap:0.5rem}
  .search-input-wrap{flex:1;display:flex;align-items:center;gap:0.4rem;background:var(--surface-2);border-radius:20px;padding:0.4rem 0.8rem}
  .search-input-wrap .search-icon{font-size:0.9rem;color:var(--muted)}
  .search-input-wrap input{flex:1;border:none;background:none;color:var(--fg);font-size:0.82rem;outline:none;min-width:0}
  .search-input-wrap input::placeholder{color:var(--muted)}
  .search-bar .btn-time{width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;border-radius:50%;color:var(--fg-secondary)}
  .time-presets{display:none;gap:4px;flex-wrap:wrap;padding:0.4rem 0.75rem 0.5rem;overflow-x:auto}
  .time-presets.open{display:flex}
  .preset-btn{flex-shrink:0;padding:0.3rem 0.55rem;font-size:0.7rem;color:var(--muted);background:var(--surface-2);border-radius:14px}
  .preset-btn.active{color:var(--fg);background:var(--accent)}
  .result-count{font-size:0.68rem;color:var(--muted);padding:0 0.75rem 0.2rem}

  .chip-bar{display:flex;gap:0.5rem;padding:0 0.75rem 0.6rem;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .chip-bar::-webkit-scrollbar{display:none}
  .chip{flex-shrink:0;padding:0.35rem 0.85rem;border-radius:20px;font-size:0.78rem;background:var(--surface-2);color:var(--muted);white-space:nowrap}
  .chip.active{background:var(--accent);color:#fff}

  .app-content{flex:1;padding:0 0.5rem 5rem}
  .tab-content{display:none}
  .tab-content.active{display:block}

  .waterfall{display:flex;gap:0.4rem}
  .wf-col{flex:1;display:flex;flex-direction:column;gap:0.4rem;min-width:0}

  .card{background:var(--surface);border-radius:var(--radius);overflow:hidden}
  .card-cover{position:relative;aspect-ratio:3/4}
  .card-cover img{width:100%;height:100%;object-fit:cover}
  .badge-count{position:absolute;top:6px;right:6px;background:rgba(0,0,0,0.55);color:#fff;font-size:0.62rem;padding:2px 6px;border-radius:10px}
  .badge-play{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:30px;height:30px;background:rgba(0,0,0,0.55);border-radius:50%;display:flex;align-items:center;justify-content:center}
  .badge-play::after{content:'';border-left:10px solid #fff;border-top:6px solid transparent;border-bottom:6px solid transparent;margin-left:2px}
  .card-title{padding:0.5rem 0.55rem 0;font-size:0.8rem;line-height:1.4;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;white-space:pre-wrap}
  .card-footer{display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0.55rem 0.5rem}
  .card-author{display:flex;align-items:center;gap:0.3rem;min-width:0}
  .card-author-avatar{width:16px;height:16px;border-radius:50%;background:var(--accent);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:0.5rem;color:#fff}
  .card-author-name{font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .card-stats{display:flex;align-items:center;gap:0.5rem;font-size:0.65rem;color:var(--muted);flex-shrink:0}
  .card-stats span{display:flex;align-items:center;gap:2px}

  .textonly-list .card{margin-bottom:0.4rem}
  .card.text-only .card-title{padding:0.6rem 0.65rem 0;font-size:0.84rem;-webkit-line-clamp:4}
  .card.text-only.expanded .card-title{-webkit-line-clamp:unset}
  .card.text-only .card-expand{text-align:center;font-size:0.68rem;color:var(--muted);padding:0.35rem 0 0.5rem;border-top:1px solid var(--border);margin:0.4rem 0.65rem 0;cursor:pointer}
  .sentinel{text-align:center;font-size:0.7rem;color:var(--muted);padding:1rem 0}

  .lightbox{display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,0.94)}
  .lightbox.open{display:flex;align-items:center;justify-content:center}
  .lb-close{position:absolute;top:1rem;right:1rem;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.1)}
  .lb-prev,.lb-next{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#fff;cursor:pointer;z-index:2;border-radius:50%;background:rgba(255,255,255,0.06)}
  .lb-prev{left:0.5rem}
  .lb-next{right:0.5rem}
  .lb-counter{position:absolute;bottom:1.5rem;left:50%;transform:translateX(-50%);color:rgba(255,255,255,0.6);font-size:0.85rem;z-index:2}
  .lb-content{max-width:92vw;max-height:85vh;display:flex;align-items:center;justify-content:center}
  .lb-content img,.lb-content video{max-width:100%;max-height:85vh;object-fit:contain;border-radius:4px}

  .bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:var(--app-w);display:flex;background:rgba(10,10,10,0.97);border-top:1px solid var(--border);z-index:20;padding:0.3rem 0 max(0.3rem,env(safe-area-inset-bottom))}
  .nav-item{flex:1;display:flex;flex-direction:column;align-items:center;gap:1px;padding:0.25rem 0;color:var(--muted);position:relative;font-size:0.55rem;min-width:0}
  .nav-item .icon{font-size:1.25rem;line-height:1}
  .nav-item::after{content:'';position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:0;height:2px;border-radius:1px;background:var(--accent);transition:width .2s}
  .nav-item.active{color:var(--accent)}
  .nav-item.active::after{width:20px}
  .badge-duration{position:absolute;bottom:6px;right:6px;background:rgba(0,0,0,0.75);color:#fff;font-size:0.62rem;padding:2px 5px;border-radius:4px}
"""

JS = r"""'use strict';
(function(){
var PAGE_SIZE = 20,
    tabsData = window.__DATA__,
    currentTab = '',
    currentChip = '';

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

function fakeStats(){
  return {
    likes: Math.floor(Math.random()*9000)+100,
    comments: Math.floor(Math.random()*200)
  };
}
function fmtNum(n){
  if(n>=100000) return (n/1000).toFixed(0)+'k';
  if(n>=1000) return (n/1000).toFixed(1).replace('.0','')+'k';
  return String(n);
}

function cardImageHtml(tabId, idx, m){
  var cover = m.media[0];
  var src = cover.thumb || cover.path;
  var badge = m.media.length > 1 ? '<span class="badge-count">📷 ' + m.media.length + '</span>' : '';
  var play = cover.type === 'video' ? '<span class="badge-play"></span>' : '';
  var st = fakeStats();
  var name = (m.channel||'').replace(/^@/,'');
  return '<div class="card" data-tab="'+tabId+'" data-idx="'+idx+'">'
    + '<div class="card-cover"><img src="'+escAttr(src)+'" loading="lazy">'+badge+play+'</div>'
    + '<div class="card-title">'+escHtml(m.text||'')+'</div>'
    + '<div class="card-footer">'
    + '<div class="card-author"><div class="card-author-avatar">'+name[0]+'</div><span class="card-author-name">'+escHtml(name)+'</span></div>'
    + '<div class="card-stats"><span>♥ '+fmtNum(st.likes)+'</span><span>💬 '+st.comments+'</span></div>'
    + '</div></div>';
}

function cardXvHtml(tabId, idx, m){
  var st = fakeStats();
  return '<div class="card" data-tab="'+tabId+'" data-idx="'+idx+'" data-xv="1">'
    + '<div class="card-cover"><img src="'+escAttr(m.thumbnail)+'" loading="lazy">'
    + '<span class="badge-play"></span>'
    + '<span class="badge-duration">⏱ '+escHtml(m.duration)+'</span></div>'
    + '<div class="card-title">'+escHtml(m.text||'')+'</div>'
    + '<div class="card-footer">'
    + '<div class="card-author"><div class="card-author-avatar">M</div><span class="card-author-name">maderotic</span></div>'
    + '<div class="card-stats"><span>♥ '+fmtNum(st.likes)+'</span><span>💬 '+st.comments+'</span></div>'
    + '</div></div>';
}

function cardTextOnlyHtml(tabId, idx, m){
  var st = fakeStats();
  var name = (m.channel||'').replace(/^@/,'');
  return '<div class="card text-only" data-tab="'+tabId+'" data-idx="'+idx+'">'
    + '<div class="card-title">'+escHtml(m.text||'')+'</div>'
    + '<div class="card-footer">'
    + '<div class="card-author"><div class="card-author-avatar">'+name[0]+'</div><span class="card-author-name">'+escHtml(name)+'</span></div>'
    + '<div class="card-stats"><span>♥ '+fmtNum(st.likes)+'</span><span>💬 '+st.comments+'</span></div>'
    + '</div>'
    + '<div class="card-expand">展開詳情 ▾</div>'
    + '</div>';
}

function appendItems(tabId, indices){
  var data = tabsData[tabId];
  var col0 = document.getElementById('wfcol-'+tabId+'-0');
  var col1 = document.getElementById('wfcol-'+tabId+'-1');
  var textWrap = document.getElementById('textonly-'+tabId);
  indices.forEach(function(i){
    var m = data.messages[i];
    if(m._xv){
      var target = (data.wfCounter % 2 === 0) ? col0 : col1;
      target.insertAdjacentHTML('beforeend', cardXvHtml(tabId, i, m));
      data.wfCounter++;
    } else if(m.media && m.media.length){
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
  var sentinel = document.getElementById('sentinel-'+tabId);
  if(!sentinel) return;
  sentinel.textContent = data.loaded >= data.messages.length ? '已無更多內容' : '載入更多…';
}

function loadNextBatch(tabId){
  var data = tabsData[tabId];
  if(!data) return;
  if(data.loaded >= data.messages.length){ updateSentinel(tabId); return; }
  var start = data.loaded;
  var end = Math.min(start + PAGE_SIZE, data.messages.length);
  var indices = [];
  for(var i=start;i<end;i++) indices.push(i);
  appendItems(tabId, indices);
  data.loaded = end;
  updateSentinel(tabId);
}

function clearTabView(tabId){
  document.getElementById('wfcol-'+tabId+'-0').innerHTML = '';
  document.getElementById('wfcol-'+tabId+'-1').innerHTML = '';
  document.getElementById('textonly-'+tabId).innerHTML = '';
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

function applySearch(){
  var input = document.getElementById('search-input');
  var kw = input.value.trim().toLowerCase();
  var activePreset = document.querySelector('.preset-btn.active');
  var range = activePreset ? activePreset.getAttribute('data-range') : 'all';
  var resultEl = document.getElementById('result-count');

  if(!kw && range==='all'){
    resultEl.textContent = '';
    resetTabView(currentTab);
    return;
  }

  var data = tabsData[currentTab];
  var cutoff = computeCutoffIso(range);
  var matched = [];
  data.messages.forEach(function(m, i){
    var text = (m.text||'').toLowerCase();
    if(kw && text.indexOf(kw) === -1) return;
    if(cutoff && m.date < cutoff) return;
    matched.push(i);
  });
  resultEl.textContent = matched.length + ' 筆結果';
  clearTabView(currentTab);
  data.wfCounter = 0;
  appendItems(currentTab, matched);
}

function openLightbox(items, startIndex){
  if(items.length===0) return;
  lbState.items = items;
  lbState.current = startIndex;
  showLightboxItem();
  document.getElementById('lightbox').classList.add('open');
}

var lbState = { items:[], current:0 };

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
  document.getElementById('lb-content').innerHTML = '';
}

function openLbEmbed(videoId){
  var xvMsg = tabsData[currentTab].messages.find(function(m){ return m.video_id === videoId; });
  var mediaPath = xvMsg ? xvMsg.media_path : null;
  if(mediaPath){
    document.getElementById('lb-content').innerHTML = '<video src="'+escAttr(mediaPath)+'" controls autoplay style="max-width:92vw;max-height:85vh;border-radius:4px"></video>';
  } else {
    document.getElementById('lb-content').innerHTML = '<div style="text-align:center"><p style="color:var(--fg);margin-bottom:1rem">影片尚未下載</p><a href="https://www.xvideos.com/video'+videoId+'/" target="_blank" rel="noopener" style="display:inline-block;padding:0.8rem 2rem;background:var(--accent);color:#fff;border-radius:8px;text-decoration:none;font-size:1rem">在 xvideos 觀看</a></div>';
  }
  document.getElementById('lb-counter').textContent = '';
  document.getElementById('lightbox').classList.add('open');
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
  var panel = document.getElementById('tab-'+tabId);
  if(panel) panel.classList.add('active');
  currentTab = tabId;

  var chip = document.querySelector('.chip[data-chip="'+tabId+'"]');
  document.querySelectorAll('.chip').forEach(function(c){c.classList.remove('active');});
  if(chip) chip.classList.add('active');
}

function switchChip(tabId){
  document.querySelectorAll('.chip').forEach(function(c){c.classList.remove('active');});
  var chip = document.querySelector('.chip[data-chip="'+tabId+'"]');
  if(chip) chip.classList.add('active');
  switchTab(tabId);
}

function init(){
  var tabIds = [];
  document.querySelectorAll('.nav-item').forEach(function(btn){
    var id = btn.getAttribute('data-tab');
    tabIds.push(id);
    btn.addEventListener('click', function(){ switchTab(id); });
  });
  document.querySelectorAll('.chip').forEach(function(c){
    c.addEventListener('click', function(){
      switchChip(c.getAttribute('data-chip'));
    });
  });

  tabIds.forEach(function(id){
    tabsData[id].loaded = 0;
    tabsData[id].wfCounter = 0;
    loadNextBatch(id);
  });
  if(tabIds.length > 0) currentTab = tabIds[0];

  var searchInput = document.getElementById('search-input');
  if(searchInput) searchInput.addEventListener('input', function(){
    applySearch();
  });

  var btnTime = document.getElementById('btn-time');
  if(btnTime) btnTime.addEventListener('click', function(){
    document.getElementById('time-presets').classList.toggle('open');
  });

  document.addEventListener('click', function(e){
    try{
    var preset = e.target.closest('.preset-btn');
    if(preset){
      document.querySelectorAll('.preset-btn').forEach(function(b){b.classList.remove('active');});
      preset.classList.add('active');
      applySearch();
      return;
    }

    var card = e.target.closest('.card:not(.text-only)');
    if(card){
      var tabId2 = card.getAttribute('data-tab');
      var idx2 = parseInt(card.getAttribute('data-idx'), 10);
      if(card.getAttribute('data-xv') === '1'){
        var xvMsg = tabsData[tabId2].messages[idx2];
        openLbEmbed(xvMsg.video_id);
        return;
      }
      var m = tabsData[tabId2].messages[idx2];
      var items = m.media.map(function(item){
        return { isVideo: item.type === 'video', src: item.path };
      });
      if(items.length) openLightbox(items, 0);
      return;
    }

    var textCard = e.target.closest('.card.text-only');
    if(textCard){
      var txt = textCard.querySelector('.card-title');
      var exp = textCard.querySelector('.card-expand');
      if(textCard.hasAttribute('data-expanded')){
        textCard.removeAttribute('data-expanded');
        txt.style.webkitLineClamp = '';
        if(exp) exp.textContent = '展開詳情 ▾';
      } else {
        textCard.setAttribute('data-expanded','');
        txt.style.webkitLineClamp = 'unset';
        if(exp) exp.textContent = '收合 ▴';
      }
      return;
    }
    }catch(ex){}
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
    chip_bar = ""

    for tab_id, tab in tabs.items():
        if first_id is None:
            first_id = tab_id
        active_cls = " active" if tab_id == first_id else ""
        icon = ICON_MAP.get(tab_id, DEFAULT_ICON)
        label = tab["name"]
        if len(label) > 3:
            label = label[:2] if len(tab_id) > 3 else label[:3]
        bottom_nav += (
            f'<button class="nav-item{active_cls}" role="tab" '
            f'aria-selected="{str(tab_id == first_id).lower()}" '
            f'aria-label="{tab["name"]}" '
            f'data-tab="{tab_id}">'
            f'<span class="icon">{icon}</span><span class="label">{label}</span></button>'
        )
        chip_active = " active" if tab_id == first_id else ""
        chip_bar += f'<button class="chip{chip_active}" data-chip="{tab_id}">{tab["name"]}</button>'

        tabs_content += f'''<div class="tab-content{active_cls}" id="tab-{tab_id}" role="tabpanel">
    <div class="waterfall" id="waterfall-{tab_id}">
      <div class="wf-col" id="wfcol-{tab_id}-0"></div>
      <div class="wf-col" id="wfcol-{tab_id}-1"></div>
    </div>
    <div class="textonly-list" id="textonly-{tab_id}"></div>
    <div class="sentinel" id="sentinel-{tab_id}">載入更多…</div>
  </div>'''

    # Escape "</" so a message containing "</script>" can't break out of the
    # inline <script> block below (HTML parsing happens before JS parsing).
    tabs_json = _json.dumps(tabs, ensure_ascii=False, default=str).replace("</", "<\\/")

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

<div class="search-bar">
  <div class="search-input-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="search-input" placeholder="搜尋筆記…" aria-label="搜尋關鍵字">
  </div>
  <button class="btn-time" id="btn-time" aria-label="時間篩選">⏳</button>
</div>
<div class="time-presets" id="time-presets">
  <button class="preset-btn active" data-range="all">全部</button>
  <button class="preset-btn" data-range="today">今日</button>
  <button class="preset-btn" data-range="3d">近3日</button>
  <button class="preset-btn" data-range="7d">近7日</button>
  <button class="preset-btn" data-range="month">本月</button>
  <button class="preset-btn" data-range="halfyear">近半年</button>
</div>
<span class="result-count" id="result-count"></span>
<div class="chip-bar">
  {chip_bar}
</div>

<main class="app-content">
  {tabs_content}
</main>

<nav class="bottom-nav" role="tablist">
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
