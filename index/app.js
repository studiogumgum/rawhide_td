/* ═══════════════════════════════════════════════════════════
   BUSKER — app.js

   Widget config is fetched from /config, which the Web Server
   DAT generates from a Table DAT called table_config.

   Table DAT columns:
     panel       — group label (e.g. "master", "fx chain")
     type        — knob | slider | toggle | button | bang | xypad | colorpicker
     label       — display name
     channel     — CHOP channel name (e.g. "fx/blur")
     default     — initial value 0.0–1.0
     width       — optional px width (sliders, colorpicker)
     size        — optional px diameter (knobs)
     value       — optional fixed value for buttons
     channel_x   — xypad x channel
     channel_y   — xypad y channel
     default_x   — xypad x default (0–1)
     default_y   — xypad y default (0–1)

   All widget values are 0.0–1.0. Re-range inside TD.


/* ── WEBSOCKET ─────────────────────────────────────────── */

let ws = null;
// auto-populate WS URL from the hostname the page was served from
//
document.getElementById('ws-url-input').value = `ws://${window.location.hostname}:9980`;

const wsDot  = document.getElementById('ws-dot');
const wsText = document.getElementById('ws-status-text');
const wsBtn  = document.getElementById('ws-connect-btn');

// Send the current value of every widget to TD.
// Called on WebSocket reconnect so TD stays in sync with the UI.
// Value reading is handled by readAllValues() in widgets.js.
function flushAllValues() {
  const values = readAllValues();
  Object.entries(values).forEach(([channel, value]) => sendValue(channel, value));
  log('info', `ws: flushed ${Object.keys(values).length} values to TD`);
}


function wsConnect() {
  if (ws) { ws.close(); ws = null; }
  const url = document.getElementById('ws-url-input').value.trim();
  setWsStatus('connecting');
  try {
    ws = new WebSocket(url);
    ws.onopen    = () => {
      setWsStatus('connected');
      log('info', `ws connected → ${url}`);
      flushAllValues();
    };
    ws.onclose   = () => { setWsStatus('disconnected'); };
    ws.onerror   = () => setWsStatus('error');
    ws.onmessage = e => onWsMessage(e.data);
  } catch(err) { setWsStatus('error'); log('err', err.message); }
}

function setWsStatus(s) {
  wsDot.className = 'status-dot'
    + (s==='connected'   ? ' connected'
      : s==='error'       ? ' error'
        : s==='connecting'  ? ' connecting' : '');
  wsText.textContent = s;
  wsBtn.textContent  = s === 'connected' ? 'disconnect' : 'connect';
  wsBtn.className    = 'btn' + (s === 'connected' ? ' active' : '');
}

wsBtn.onclick = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close(); setWsStatus('disconnected');
  } else {
    wsConnect();
  }
};

window.addEventListener('beforeunload', () => {
  if (ws) { ws.onclose = null; ws.close(); }
});

function onWsMessage(raw) {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch(e) {
    log('err', `ws: invalid JSON — ${raw.slice(0, 80)}`);
    return;
  }

  if (onWsHandlers[msg.type]) {
    try {
      onWsHandlers[msg.type](msg);
    } catch(e) {
      log('err', `ws: handler error [${msg.type}] — ${e.message}`);
    }
  }
}


/* ── WEBRTC ────────────────────────────────────────────── */

let pc = null;
let pendingIceCandidates = [];
let rtcReconnectTimer = null;
let rtcRetryCount     = 0;
const RTC_MAX_RETRIES = 5;

const videoEl     = document.getElementById('video-feed');
const placeholder = document.getElementById('video-placeholder');
const rtcDot      = document.getElementById('rtc-dot');
const rtcText     = document.getElementById('rtc-status-text');

function setRtcStatus(s) {
  const cls = s==='connected'           ? ' connected'
    : s==='failed'||s==='error' ? ' error'
      : s==='connecting'          ? ' connecting' : '';
  rtcDot.className    = 'status-dot' + cls;
  rtcText.textContent = s;
}

async function rtcStart() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    log('err', 'connect websocket first');
    return;
  }
  rtcStop();
  log('rtc', 'rtc: creating peer connection');
  setRtcStatus('connecting');
  pendingIceCandidates = [];

  pc = new RTCPeerConnection({ iceServers: [] });
  const thisPc = pc;
  pc.addTransceiver('video', { direction: 'recvonly' });

  pc.onconnectionstatechange = () => {
    console.log('connectionState:', pc.connectionState);
  };

  pc.onsignalingstatechange = () => {
    console.log('signalingState:', pc.signalingState);
  };

  pc.onicegatheringstatechange = () => {
    console.log('iceGatheringState:', pc.iceGatheringState);
  };

  pc.oniceconnectionstatechange = () => {
    console.log('iceConnectionState:', pc.iceConnectionState);
  };

  pc.ontrack = e => {
    console.log('ontrack fired:', e.track.kind);
  };

  pc.onicecandidate = e => {
    console.log('local ice candidate:', e.candidate?.candidate?.substring(0, 60));
  };
  pc.ontrack = e => {
    if (e.track.kind === 'video') {
      log('rtc', 'rtc: video track received');
      console.log('rtc: video track received', e.track.kind);
      videoEl.srcObject = e.streams[0] || new MediaStream([e.track]);
      placeholder.classList.add('hidden');
      setRtcStatus('connected');
      videoEl.play().catch(err => log('err', 'play: ' + err.message));
      // successful connection — reset retry counter
      rtcRetryCount = 0;
    }
  };

  pc.onicecandidate = e => {
    if (e.candidate) {
      log('rtc', 'rtc: sending ice candidate');
      console.log('rtc: local ice candidate:', e.candidate?.candidate?.substring(0,60));
      wsSend({ type: 'rtc_ice', candidate: e.candidate.toJSON() });
    }
  };

  pc.onconnectionstatechange = () => {
    console.log('connectionState:', pc.connectionState);
    if (pc !== thisPc) return; // stale connection, ignore
    log('rtc', `rtc: state → ${pc.connectionState}`);
    if (pc.connectionState === 'connected') {
      setRtcStatus('connected');
    }
    if (pc.connectionState === 'failed') {
      log('err', 'rtc: connection failed');
      placeholder.classList.remove('hidden');
      setRtcStatus('failed');
      scheduleRtcReconnect();
    }
    if (pc.connectionState === 'disconnected') {
      placeholder.classList.remove('hidden');
      setRtcStatus('disconnected');
      scheduleRtcReconnect();
    }
  };

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  log('rtc', 'rtc: sending offer');
  wsSend({ type: 'rtc_offer', sdp: pc.localDescription.sdp });
}

async function rtcHandleAnswer(sdp) {
  if (!pc) return;
  try {
    await pc.setRemoteDescription({ type: 'answer', sdp });
    log('rtc', 'rtc: remote description set');
    for (const c of pendingIceCandidates) {
      try { await pc.addIceCandidate(c); }
      catch(e) { log('err', 'rtc queued ice: ' + e.message); }
    }
    pendingIceCandidates = [];
  } catch(e) {
    log('err', 'rtc setRemoteDescription: ' + e.message);
  }
}

async function rtcHandleRemoteIce(candidate) {
  if (!pc) return;
  const init = (typeof candidate === 'string')
    ? { candidate, sdpMLineIndex: 0, sdpMid: '0' }
    : candidate;
  if (!init.candidate || init.candidate === '') {
    try { await pc.addIceCandidate(null); } catch(e) {}
    return;
  }
  if (!pc.remoteDescription) {
    pendingIceCandidates.push(init);
    return;
  }
  try { await pc.addIceCandidate(init); }
  catch(e) { log('err', 'rtc ice: ' + e.message); }
}

function scheduleRtcReconnect() {
  if (rtcReconnectTimer) return;  // already scheduled
  if (rtcRetryCount >= RTC_MAX_RETRIES) {
    log('err', `rtc: gave up after ${RTC_MAX_RETRIES} attempts — click start stream to retry`);
    rtcRetryCount = 0;
    return;
  }
  // exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
  const delay = Math.min(1000 * Math.pow(2, rtcRetryCount), 30000);
  rtcRetryCount++;
  log('rtc', `rtc: reconnecting in ${delay / 1000}s (attempt ${rtcRetryCount}/${RTC_MAX_RETRIES})`);
  rtcReconnectTimer = setTimeout(() => {
    rtcReconnectTimer = null;
    if (ws && ws.readyState === WebSocket.OPEN) {
      rtcStart();
    } else {
      log('rtc', 'rtc: websocket not open, skipping reconnect');
    }
  }, delay);
}

function rtcStop() {
  // cancel any pending reconnect so manual stop is respected
  if (rtcReconnectTimer) { clearTimeout(rtcReconnectTimer); rtcReconnectTimer = null; }
  rtcRetryCount = 0;
  if (pc) { pc.close(); pc = null; }
  pendingIceCandidates = [];
  videoEl.srcObject = null;
  placeholder.classList.remove('hidden');
  setRtcStatus('idle');
  log('rtc', 'rtc: stopped');
}

function rtcSnapshot() {
  if (!videoEl.srcObject) { log('err', 'no video to snapshot'); return; }
  const c = document.createElement('canvas');
  c.width  = videoEl.videoWidth  || 1920;
  c.height = videoEl.videoHeight || 1080;
  c.getContext('2d').drawImage(videoEl, 0, 0);
  const a = document.createElement('a');
  a.download = 'td-' + Date.now() + '.jpg';
  a.href = c.toDataURL('image/jpeg', 0.95);
  a.click();
}

document.getElementById('rtc-start-btn').onclick    = rtcStart;
document.getElementById('rtc-stop-btn').onclick     = rtcStop;


/* ── RENDER ────────────────────────────────────────────── */

// Accepts two config formats:
//
// New layout format (from Views COMP with table_layout):
//   [{ row, row_flex, cols: [{ col, col_flex, panel, widgets }] }]
//
// Legacy flat format (from plain /config without table_layout):
//   [{ label, widgets: [...] }]
//
// The legacy format is normalised into a single-column layout so
// renderControls only needs one rendering path.
function normaliseConfig(config) {
  if (!config || config.length === 0) return [];
  // detect legacy format by presence of 'label' key instead of 'row'
  if (config[0].label !== undefined && config[0].row === undefined) {
    return config.map((panelCfg, i) => ({
      row:      i + 1,
      row_flex: 1,
      cols: [{
        col:      1,
        col_flex: 1,
        panel:    panelCfg.label,
        widgets:  panelCfg.widgets || [],
      }],
    }));
  }
  return config;
}

function renderControls(config, targetEl) {
  const area = targetEl || document.getElementById('controls-area');
  area.innerHTML = '';

  normaliseConfig(config).forEach(rowCfg => {
    const rowEl = document.createElement('div');
    rowEl.className = 'layout-row';
    rowEl.style.flex = rowCfg.row_flex ?? 1;

    (rowCfg.cols || []).forEach(colCfg => {
      const colEl = document.createElement('div');
      colEl.className = 'layout-col';
      colEl.style.flex = colCfg.col_flex ?? 1;
      colEl.appendChild(buildPanel(colCfg));
      rowEl.appendChild(colEl);
    });

    area.appendChild(rowEl);
  });
}


/* ── KEYBOARD SHORTCUTS ────────────────────────────────── */

document.addEventListener('keydown', e => {
  if (e.target.matches('input')) return;
  if (e.key === 'b') {
    const b = document.querySelector('td-button[type="bang"]');
    if (b) b.click();
  }
  if (e.key === ' ') {
    e.preventDefault();
    const t = document.querySelector('td-button[type="toggle"]');
    if (t) t.click();
  }
});


/* ── QUICK ACCESS ───────────────────────────────────────── */

function loadQuickAccess() {
  loadView('quick_access',0, document.getElementById('quick-access'));
}
/* ── VIEWS ─────────────────────────────────────────────── */

let activeView = null;

function renderViewBar(views) {
  const bar = document.getElementById('view-bar');
  bar.innerHTML = '';

  views.forEach((view, index) => {
    const btn = document.createElement('div');
    btn.className = 'view-btn';
    btn.dataset.view = view.name;
    btn.textContent = view.label;
    btn.onclick = () => loadView(view.name, index);
    bar.appendChild(btn);
  });
}

function setActiveViewBtn(name) {
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === name);
  });
}
function applyViewState(state) {
  // group RGB channels for hspicker: { 'fx/color': {r, g, b} }
  const rgbGroups = {};
  Object.entries(state).forEach(([channel, value]) => {
    const rgbMatch = channel.match(/^(.+)\/(r|g|b)$/);
    if (rgbMatch) {
      const base = rgbMatch[1], comp = rgbMatch[2];
      if (!rgbGroups[base]) rgbGroups[base] = {};
      rgbGroups[base][comp] = value;
    }
  });

  Object.entries(state).forEach(([channel, value]) => {
    // skip RGB sub-channels — handled via rgbGroups below
    if (/\/(r|g|b)$/.test(channel)) return;

    // standard widgets
    document.querySelectorAll(`[data-channel="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(value);
    });
    // xypad x axis
    document.querySelectorAll(`[data-channel-x="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(value, null);
    });
    // xypad y axis
    document.querySelectorAll(`[data-channel-y="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(null, value);
    });
  });

  // restore hspickers via RGB groups
  Object.entries(rgbGroups).forEach(([base, rgb]) => {
    if (rgb.r === undefined || rgb.g === undefined || rgb.b === undefined) return;
    document.querySelectorAll(`[data-channel="${base}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(rgb);
    });
  });

  log('info', `view: state restored`);
}

function loadView(name, index, targetEl) {
  // render to the target element area, or the controls area by default
  render_area = targetEl || document.getElementById('controls-area');
  // targetEl acts as a flag to make sure we don't do viewbar specific stuff
  // when rendering to other areas

  const configUrl = name ? `/config?view=${encodeURIComponent(name)}` : '/config';
  const stateUrl = name ? `/state?view=${encodeURIComponent(name)}` : null;
  fetch(configUrl)
    .then(r => r.json())
    .then(config => {

      renderControls(config, render_area);

      if (!targetEl) {
        activeView = name
        setActiveViewBtn(name);
        onViewChanged.forEach(fn => fn(config));
      };

      if (stateUrl) {
        fetch(stateUrl)
          .then(r => r.json())
          .then(applyViewState)
          .catch(err => log('err', `view: failed to restore view state - ${err.message}`));
        // we now send the viewindex from the generator radio
        // but it's here if we want to change back to viewbutton triggers
        //if (!targetEl) {sendValue('ui/view/viewindex', index)};
      }
    })
    .catch(err => log('err', `view: failed to load "${name}" — ${err.message}`));
}


/* ── INIT ──────────────────────────────────────────────── */

// Other modules (midi.js, presets.js etc.) push functions here.
// Each is called with the parsed config after renderControls runs.

const AUTO_WS_ATTEMPTS  = 5;
const AUTO_RTC_ATTEMPTS = 3;
const AUTO_WS_DELAY_MS  = 1500;
const AUTO_RTC_DELAY_MS = 2000;

async function autoConnect() {
  for (let i = 0; i < AUTO_WS_ATTEMPTS; i++) {
    log('info', `ws: auto-connect attempt ${i + 1} of ${AUTO_WS_ATTEMPTS}`);
    wsConnect();
    const connected = await new Promise(resolve => {
      const timeout = setTimeout(() => resolve(false), AUTO_WS_DELAY_MS);
      const check = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          clearTimeout(timeout); clearInterval(check); resolve(true);
        } else if (ws && ws.readyState === WebSocket.CLOSED) {
          clearTimeout(timeout); clearInterval(check); resolve(false);
        }
      }, 100);
    });
    if (connected) {
      log('info', 'ws: connected — attempting rtc stream');
      await autoConnectRTC();
      return;
    }
    if (i < AUTO_WS_ATTEMPTS - 1) {
      log('info', `ws: retrying in ${AUTO_WS_DELAY_MS}ms...`);
      await new Promise(resolve => setTimeout(resolve, AUTO_WS_DELAY_MS));
    }
  }
  log('err', `ws: could not connect after ${AUTO_WS_ATTEMPTS} attempts`);
}

async function autoConnectRTC() {
  for (let i = 0; i < AUTO_RTC_ATTEMPTS; i++) {
    log('rtc', `rtc: auto-connect attempt ${i + 1} of ${AUTO_RTC_ATTEMPTS}`);
    await rtcStart();
    const connected = await new Promise(resolve => {
      const timeout = setTimeout(() => resolve(false), 5000);
      const check = setInterval(() => {
        if (videoEl.srcObject && videoEl.srcObject.active) {
          clearTimeout(timeout); clearInterval(check); resolve(true);
        }
        if (!pc || pc.connectionState === 'failed') {
          clearTimeout(timeout); clearInterval(check); resolve(false);
        }
      }, 200);
    });
    if (connected) { log('rtc', 'rtc: stream connected'); return; }
    if (i < AUTO_RTC_ATTEMPTS - 1) {
      log('rtc', `rtc: retrying in ${AUTO_RTC_DELAY_MS}ms...`);
      rtcStop();
      await new Promise(resolve => setTimeout(resolve, AUTO_RTC_DELAY_MS));
    }
  }
  log('err', `rtc: could not connect after ${AUTO_RTC_ATTEMPTS} attempts`);
}

// Fetch view list, render view bar, then load first view (or default config)
fetch('/views')
  .then(r => r.json())
  .then(views => {
    renderViewBar(views);
    loadQuickAccess();
    const first = views.length > 0 ? views[0].name : null;
    return first
      ? fetch(`/config?view=${encodeURIComponent(first)}`).then(r => r.json()).then(config => ({ config, view: first }))
      : fetch('/config').then(r => r.json()).then(config => ({ config, view: null }));
  })
  .then(({ config, view }) => {
    activeView = view;
    renderControls(config);
    onConfigLoaded.forEach(fn => fn(config));   // init hooks — run once
    onViewChanged.forEach(fn => fn(config));     // view hooks — run on first load too
    if (view) setActiveViewBtn(view);
    log('info', `loaded view: ${view ?? 'default'}`);
    log('info', 'kb: space = first toggle  |  b = first bang');
    autoConnect();
    // create texture select radio
    const textureSelect = document.getElementById('video-texture-select');
    if (textureSelect) {
      const widget = createRadio({
        label: 'MAIN,GENERATORS,FX,PREVIEW',
        channel: 'ui/view/viewindex',
        default: 0
      });
      const cell = document.createElement('div');
      cell.classname = 'widget-cell';
      cell.appendChild(widget);
      textureSelect.appendChild(cell);
    }
  })
  .catch(err => {
    // /views not available — fall back to flat config
    log('info', 'views: endpoint not found, loading default config');
    fetch('/config')
      .then(r => r.json())
      .then(config => {
        renderControls(config);
        onConfigLoaded.forEach(fn => fn(config));
        onViewChanged.forEach(fn => fn(config));
        log('info', 'loaded default config');
        autoConnect();
      })
      .catch(e => {
        log('err', 'failed to load config: ' + e.message);
        log('err', 'is the Web Server DAT running?');
      });
  });
