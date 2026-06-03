/* ═══════════════════════════════════════════════════════════
   core.js — Shared globals for BUSKER

   Load order: core.js → widgets.js → app.js → midi.js → presets.js

   Defines:
     log(type, text)          — append to #log
     wsSend(obj)              — send JSON over WebSocket (ws defined in app.js)
     sendValue(channel, val)  — send a control value over WebSocket
     onConfigLoaded[]         — hooks run ONCE on first page load
     onViewChanged[]          — hooks run on every view switch
     onWsHandlers{}           — registry for incoming WS message types
═══════════════════════════════════════════════════════════ */


/* ── THEME ──────────────────────────────────────────────── */

// knobSensitivity is used by createKnob in widgets.js
// higher value = less sensitive (more px needed to traverse full range)
let knobSensitivity = 150;

function applyTheme(theme) {
  const root = document.documentElement;

  // colour and font size variables — map directly to CSS custom properties
  const cssVars = {
    'bg': '--bg', 'bg2': '--bg2', 'bg3': '--bg3', 'bg4': '--bg4',
    'border': '--border', 'border2': '--border2',
    'text': '--text', 'text2': '--text2', 'text3': '--text3',
    'accent': '--accent', 'accent2': '--accent2', 'accent_glow': '--accent-glow',
    'green': '--green', 'red': '--red', 'amber': '--amber',
    'font_size_label': '--fs-label', 'font_size_value': '--fs-value',
    'font_size_ui':    '--fs-ui',    'font_size_micro':  '--fs-micro',
  };

  Object.entries(cssVars).forEach(([key, cssVar]) => {
    if (theme[key] !== undefined) {
      // font sizes need px suffix if bare number
      let val = theme[key];
      if (['font_size_label','font_size_value','font_size_ui','font_size_micro']
          .includes(key) && /^\d+$/.test(String(val))) {
        val = val + 'px';
      }
      root.style.setProperty(cssVar, val);
    }
  });

  // font families — update --mono and --sans
  if (theme.font_sans) root.style.setProperty('--sans', `'${theme.font_sans}', sans-serif`);
  if (theme.font_mono) root.style.setProperty('--mono', `'${theme.font_mono}', monospace`);

  // custom fonts served from TD — inject @font-face rules
  const fontFaces = [];
  if (theme.font_file_sans && theme.font_sans) {
    fontFaces.push(`@font-face {
  font-family: '${theme.font_sans}';
  src: url('/fonts/${theme.font_file_sans}') format('woff2');
  font-weight: 100 900;
  font-style: normal;
}`);
  }
  if (theme.font_file_mono && theme.font_mono) {
    fontFaces.push(`@font-face {
  font-family: '${theme.font_mono}';
  src: url('/fonts/${theme.font_file_mono}') format('woff2');
  font-weight: 100 900;
  font-style: normal;
}`);
  }
  if (fontFaces.length) {
    const style = document.createElement('style');
    style.id = 'busker-theme-fonts';
    style.textContent = fontFaces.join('\n');
    // replace if already present
    const existing = document.getElementById('busker-theme-fonts');
    if (existing) existing.remove();
    document.head.appendChild(style);
  }

  // JS parameters — not CSS
  if (theme.knob_sensitivity) knobSensitivity = parseFloat(theme.knob_sensitivity);
}

// fetch theme before anything renders
// fall back silently to CSS defaults if endpoint not present
fetch('/theme')
  .then(r => r.json())
  .then(applyTheme)
  .catch(() => {});

/* ── MODULE HOOKS ──────────────────────────────────────── */

// Runs ONCE on first page load — use for module init (e.g. building preset bar UI)
const onConfigLoaded = [];

// Runs on EVERY view switch including the first load
// Use for anything that depends on which widgets are in the DOM (e.g. MIDI remap)
const onViewChanged = [];

// Incoming WebSocket message handlers registered by other modules
// e.g. onWsHandlers['preset_list'] = msg => { ... }
const onWsHandlers = {};


/* ── LOG ───────────────────────────────────────────────── */
//
//const logEl = document.getElementById('log');
//
//function log(type, text) {
//  const d = document.createElement('div');
//  d.className = 'entry ' + type;
//  d.textContent = text;
//  logEl.appendChild(d);
//  if (logEl.children.length > 120) logEl.removeChild(logEl.firstChild);
//  logEl.scrollTop = logEl.scrollHeight;
//}


/* ── WEBSOCKET SEND ────────────────────────────────────── */

// ws is defined in app.js which loads after core.js.
// These functions reference it at call time, not at definition time,
// so the forward reference is safe.

function wsSend(obj) {
  if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}

function sendValue(channel, value) {
  wsSend({ type: 'control', channel, value });
  log('tx', `→ ${channel} = ${value.toFixed(3)}`);
}

/* ── WIDGET TOOLTIPS ─────────────────────────────────────── */

// midi.js overrides this to provide MIDI mapping info
let getMidiInfo = () => null;

let tooltipHoverEnabled = false;
let altHeld             = false;
let tooltipHoverTimer   = null;
// tooltip element looked up lazily so it's always found after DOM is ready
let _tooltipEl = null;
function getTooltipEl() {
  if (!_tooltipEl) _tooltipEl = document.getElementById('widget-tooltip');
  return _tooltipEl;
}

document.addEventListener('keydown', e => {
  if (e.key === 'Alt') { altHeld = true; e.preventDefault(); }
});
document.addEventListener('keyup', e => {
  if (e.key === 'Alt') { altHeld = false; hideTooltip(); }
});

function showTooltip(el, x, y) {
  const channel = el.dataset.channel || '';
  const desc    = el.dataset.tooltip  || '';
  const midi    = getMidiInfo(channel);

  let lines = [];
  if (desc)    lines.push(desc);
  if (channel) lines.push(`ch    ${channel}`);
  if (midi)    lines.push(`midi  ${midi}`);
  if (!channel && !desc) return;  // nothing useful to show

  const tooltipEl = getTooltipEl();
  if (!tooltipEl) return;
  tooltipEl.textContent = lines.join('\n');

  // position near cursor, keeping within viewport
  const rect = tooltipEl.getBoundingClientRect();
  const tw = Math.max(rect.width, 180);
  const tx = Math.min(x + 14, window.innerWidth  - tw - 8);
  const ty = Math.min(y + 14, window.innerHeight - 80  - 8);
  tooltipEl.style.left = tx + 'px';
  tooltipEl.style.top  = ty + 'px';
  tooltipEl.classList.add('visible');
}

function hideTooltip() {
  const te = getTooltipEl();
  if (te) te.classList.remove('visible');
  clearTimeout(tooltipHoverTimer);
}

document.addEventListener('mousemove', e => {
  if (!altHeld && !tooltipHoverEnabled) { return; }
  const widget = e.target.closest('[data-channel]');
  if (!widget) { hideTooltip(); return; }
  if (altHeld) {
    clearTimeout(tooltipHoverTimer);
    showTooltip(widget, e.clientX, e.clientY);
  } else {
    clearTimeout(tooltipHoverTimer);
    hideTooltip();
    tooltipHoverTimer = setTimeout(() => {
      showTooltip(widget, e.clientX, e.clientY);
    }, 600);
  }
});

document.addEventListener('mouseleave', () => hideTooltip());

// settings toggle
const tooltipToggleBtn = document.getElementById('tooltip-toggle-btn');
if (tooltipToggleBtn) {
  tooltipToggleBtn.onclick = () => {
    tooltipHoverEnabled = !tooltipHoverEnabled;
    tooltipToggleBtn.classList.toggle('active', tooltipHoverEnabled);
    tooltipToggleBtn.textContent = tooltipHoverEnabled ? 'disable hover tips' : 'enable hover tips';
  };
}

/* ── FULLSCREEN BUTTON ────────────────────────────── */

const fsBtn = document.getElementById('fullscreen-btn');

fsBtn.onclick = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
};

document.addEventListener('fullscreenchange', () => {
  const icon = document.getElementById('fullscreen-icon');
  if (icon) icon.textContent = document.fullscreenElement ? 'fullscreen_exit' : 'fullscreen';
  fsBtn.classList.toggle('active', !!document.fullscreenElement);
});

// Fullscreen shortcut F
document.addEventListener('keydown', e => {
  if (e.key === 'f' && !e.target.matches('input')) fsBtn.click();
});

/* ── LOG ───────────────────────────────────────────────── */

const logEl = document.getElementById('log');
const logContainer = document.getElementById('log');

// levels in ascending verbosity — earlier = more severe = always shown
const LOG_LEVELS = ['err', 'warn', 'rtc', 'tx', 'rx', 'tdlog', 'info', 'debug'];
let logLevel = 'info'; // default: show everything

function shouldShowLog(type) {
  const typeIdx  = LOG_LEVELS.indexOf(type);
  const levelIdx = LOG_LEVELS.indexOf(logLevel);
  // unknown types always show; known types show if at or below current level
  return typeIdx === -1 || typeIdx <= levelIdx;
}

function log(type, text) {
  const d = document.createElement('div');
  d.className = 'entry ' + type;
  d.textContent = text;
  d.style.display = shouldShowLog(type) ? '' : 'none';
  logEl.appendChild(d);
  if (logEl.children.length > 120) logEl.removeChild(logEl.firstChild);
  logEl.scrollTop = logEl.scrollHeight;
}

function setLogLevel(level) {
  if (!LOG_LEVELS.includes(level)) return;
  logLevel = level;
  // re-filter all existing entries to match new level
  Array.from(logEl.children).forEach(el => {
    const type = el.className.replace('entry ', '').trim();
    el.style.display = shouldShowLog(type) ? '' : 'none';
  });
  log('info', `log level set to: ${level}`);
}

function setLogVisible(visible) {
  logEl.style.display = visible ? '' : 'none';
}
onWsHandlers['control'] = msg => {
  document.querySelectorAll('[data-channel]').forEach(el => {
    if (el.dataset.channel === msg.channel && typeof el.setValue === 'function')
      el.setValue(parseFloat(msg.value));
  });
  log('rx', `← ${msg.channel} = ${msg.value}`);
};

onWsHandlers['control_batch'] = msg => {
  if (!msg.values) return;
  Object.entries(msg.values).forEach(([channel, value]) => {
    document.querySelectorAll(`[data-channel="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(parseFloat(value));
    });
    // xypad axes
    document.querySelectorAll(`[data-channel-x="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(parseFloat(value), null);
    });
    document.querySelectorAll(`[data-channel-y="${channel}"]`).forEach(el => {
      if (typeof el.setValue === 'function') el.setValue(null, parseFloat(value));
    });
  });
  log('rx', `← batch update: ${Object.keys(msg.values).length} channels`);
};

onWsHandlers['rtc_answer'] = msg => {
  log('rtc', 'rtc: received answer');
  rtcHandleAnswer(msg.sdp);
};

onWsHandlers['rtc_ice'] = msg => {
  log('rtc', 'rtc: received ice candidate');
  rtcHandleRemoteIce(msg.candidate);
};

onWsHandlers['log_config'] = msg => {
  if (msg.level   !== undefined) setLogLevel(msg.level);
  if (msg.visible !== undefined) setLogVisible(msg.visible);
};

onWsHandlers['command'] = msg => {
  if (msg.action === 'refresh') {
    // refresh webpage
    location.reload();
  }
}

/* ── LOG FROM TD ────────────────────────────── */

onWsHandlers['tdlog'] = msg => {
  log(msg.level || 'info', `td-${msg.source}: ${msg.message}`);
};
/* ── PERFORMANCE STATUS BAR ────────────────────────────── */

onWsHandlers['perf'] = msg => {
  const set = (id, text, val, warnAt, critAt) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    let value_tag = ''
    if (id !== 'val-fps') {
      value_tag = (val >= critAt ? ' crit' : val >= warnAt ? ' warn': '');
    } else {
      value_tag = (val <= critAt ? ' crit' : val <= warnAt ? ' warn': '');
    };

    el.className = 'stat-value' + value_tag
      //+ (val >= critAt ? ' crit' : val >= warnAt ? ' warn' : '');
  };
  // first number is the warning thresh, second is the critical thresh
  set('val-fps',  msg.fps           ,    msg.fps,       58, 55);
  set('val-ram',  msg.ram      + '%',    msg.ram,       40, 75);
  set('val-vram', msg.vram     + '%',    msg.vram,      70, 90);
  set('val-gpu',  msg.gpu_temp + '°c',   msg.gpu_temp,  70, 80);
};

/* ── SETTINGS DROPDOWN ──────────────────────────────────── */

const settingsBtn  = document.getElementById('settings-btn');
const settingsMenu = document.getElementById('settings-menu');

function closeSettings() {
  settingsMenu.classList.remove('open');
  settingsBtn.classList.remove('open');
  const arrow = document.getElementById('settings-arrow');
  if (arrow) arrow.style.transform = '';
}

settingsBtn.onclick = e => {
  e.stopPropagation();
  const isOpen = settingsMenu.classList.contains('open');
  if (isOpen) {
    closeSettings();
  } else {
    settingsMenu.classList.add('open');
    settingsBtn.classList.add('open');
    const arrow = document.getElementById('settings-arrow');
    if (arrow) arrow.style.transform = 'rotate(180deg)';
  }
};

// close when clicking outside
document.addEventListener('click', e => {
  if (!settingsMenu.contains(e.target) && e.target !== settingsBtn) {
    closeSettings();
  }
});

// close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeSettings();
});


/* ── HELP OVERLAY (touch devices only) ────────────────────────────── */
let helpOverlayActive = false;
const helpBtn = document.getElementById('help-overlay-btn');

if (helpBtn) {
  if (navigator.maxTouchPoints > 0) {
    helpBtn.style.display = '';

    helpBtn.onclick = () => {
      helpOverlayActive = !helpOverlayActive;
      helpBtn.classList.toggle('help-overlay-active', helpOverlayActive);
    };
  }
  else {
    helpBtn.style.display = 'none';
  }
}

document.addEventListener('pointerdown', e => {
  if (!helpOverlayActive) return;

  const widget = e.target.closest('[data-channel]');
  if (!widget) return;

  // disable widget interaction
  e.stopImmediatePropagation();
  e.preventDefault();

  showHelpOverlay(widget);
}, true);


function showHelpOverlay(el) {
  // remove any existing overlay
  const existing = document.getElementById('help-overlay-modal');
  if (existing) existing.remove();
 
  const channel = el.dataset.channel || '';
  const desc    = el.dataset.tooltip  || '';
  const midi    = getMidiInfo(channel);
 
  if (!channel && !desc) return;
 
  const modal = document.createElement('div');
  modal.id = 'help-overlay-modal';
 
  if (desc) {
    const descEl = document.createElement('div');
    descEl.className = 'help-overlay-desc';
    descEl.textContent = desc;
    modal.appendChild(descEl);
  }
 
  if (channel) {
    const chEl = document.createElement('div');
    chEl.className = 'help-overlay-channel';
    chEl.textContent = channel;
    modal.appendChild(chEl);
  }
 
  if (midi) {
    const midiEl = document.createElement('div');
    midiEl.className = 'help-overlay-midi';
    midiEl.textContent = midi;
    modal.appendChild(midiEl);
  }
 
  // close on tap anywhere
  modal.addEventListener('pointerdown', e => {
    e.stopImmediatePropagation();
    modal.remove();
  });
 
  document.body.appendChild(modal);
 
  // auto-dismiss after 4 seconds
  setTimeout(() => { if (modal.parentNode) modal.remove(); }, 4000);
}


/* ── VALUE VISIBILITY TOGGLE ────────────────────────────── */

let valuesVisible = true;

const valuesBtn = document.getElementById('values-btn');
if (valuesBtn) {
  valuesBtn.onclick = () => {
    valuesVisible = !valuesVisible;
    document.getElementById('controls-area').classList.toggle('hide-values', !valuesVisible);
    valuesBtn.classList.toggle('active', !valuesVisible);
    valuesBtn.textContent = valuesVisible ? 'hide values' : 'show values';
  };
  valuesBtn.click();
}

/* ── LOG / QUICK-ACCESS VISIBILITY TOGGLE ──────────────────────────────── */

let logVisible = true;

const logToggleBtn = document.getElementById('log-toggle-btn');
const logEl2 = document.getElementById('log');
const quickAccessEl = document.getElementById('quick-access');

function setLogVisible(show) {
  logVisible = show;
  if (logEl2)        logEl2.classList.toggle('hidden', !show);
  if (quickAccessEl) quickAccessEl.classList.toggle('hidden', show);
  if (logToggleBtn) {
    logToggleBtn.classList.toggle('active', show);
    logToggleBtn.textContent = show ? 'hide log' : 'show log';
  }
}
 
if (logToggleBtn) {
  logToggleBtn.onclick = () => setLogVisible(!logVisible);
}
 
// initialise — quick access visible, log hidden
setLogVisible(false);
