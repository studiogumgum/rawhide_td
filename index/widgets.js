/* ═══════════════════════════════════════════════════════════
   widgets.js — Widget factories for BUSKER

   Depends on core.js (log, sendValue) being loaded first.

   Widget types:
     knob        — rotary knob, drag vertical or scroll wheel
     slider      — horizontal fader
     vfader      — vertical fader
     vxfader     — vertical fader with center line marker
     button      — exclusive selector button (radio style)
     toggle      — on/off switch
     bang        — momentary trigger
     xypad       — 2D XY position pad
     colorpicker — hue/saturation picker with RGB output
     executor    — combined vertical slider and blackout/flash/solo buttons

   All values are 0.0–1.0. Re-range in TouchDesigner.

   MIDI INDICATORS
   ───────────────
   midi.js calls setMidiMapped(channel, true/false) after
   building its map. Each widget that has a label element
   receives a .midi-mapped class on that label when mapped,
   which shows a colored dot via CSS ::after.

   TABLE DAT COLUMNS (add to existing list)
   ─────────────────
     type — add: vfader | vxfader
     height — vertical fader height in px (default 160)
═══════════════════════════════════════════════════════════ */


/* ── MIDI INDICATOR ─────────────────────────────────────── */

// Called by midi.js after map rebuild.
// Finds widget elements by channel and sets/clears .midi-mapped
// on their label child element.
function setMidiMapped(channel, mapped) {
  document.querySelectorAll(`[data-channel="${channel}"]`).forEach(el => {
    const tag = el.tagName.toLowerCase();
    if (tag === 'td-knob') {
      // knob label is SVG text — toggle class on the element itself
      // CSS handles the indicator via a positioned ::after on td-knob
      el.classList.toggle('midi-mapped', mapped);
      const svgLbl = el.querySelector('.knob-label-svg');
      if (svgLbl) svgLbl.setAttribute('fill', mapped ? '#e0943a' : '#b8b8cc');
    } else {
      const lbl = el.querySelector(
        '.slider-label, .vfader-label, .btn-inner, .pad-label, .hsp-label'
      );
      if (lbl) lbl.classList.toggle('midi-mapped', mapped);
    }
  });
}

// Clears all MIDI mapped indicators in the DOM.
// Called before a map rebuild on view switch.
function clearAllMidiIndicators() {
  document.querySelectorAll('.midi-mapped').forEach(el => {
    el.classList.remove('midi-mapped');
  });
  // reset knob SVG label fills — these are set via attribute not CSS class
  document.querySelectorAll('td-knob.midi-mapped, td-knob').forEach(el => {
    el.classList.remove('midi-mapped');
    const svgLbl = el.querySelector('.knob-label-svg');
    if (svgLbl) svgLbl.setAttribute('fill', '#b8b8cc');
  });
}


/* ── HSV → RGB ──────────────────────────────────────────── */

function hsvToRgb(h, s, v) {
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  switch (i % 6) {
    case 0: return [v, t, p];
    case 1: return [q, v, p];
    case 2: return [p, v, t];
    case 3: return [p, q, v];
    case 4: return [t, p, v];
    case 5: return [v, p, q];
  }
}

function rgbToHsv(r, g, b) {
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const d = max - min;
  let h = 0, s = max === 0 ? 0 : d / max, v = max;
  if (d !== 0) {
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return [h, s, v];
}

/* ── KNOB ───────────────────────────────────────────────── */

function createKnob(cfg) {
  const el = document.createElement('td-knob');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
  const size = cfg.size || 120, R = size / 2, trackR = R - 10;
  const GAP = 0.3, startA = Math.PI/2 + GAP, endA = 2.5*Math.PI - GAP;
  let val = Math.max(0, Math.min(1, cfg.default ?? 0));

  function polar(a, r) { return [R + r*Math.cos(a), R + r*Math.sin(a)]; }
  function arc(r, f, t) {
    const [sx,sy] = polar(f,r), [ex,ey] = polar(t,r);
    return `M ${sx} ${sy} A ${r} ${r} 0 ${(t-f)>Math.PI?1:0} 1 ${ex} ${ey}`;
  }

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  // viewBox stays at the design size; CSS scales the SVG to fill its container
  // up to the max size (cfg.size or 80px default)
  svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
  svg.style.width  = '100%';
  svg.style.height = '100%';
  // knobs fill their container unless a size is provided
  if (cfg.size) {
    svg.style.maxWidth  = size + 'px';
    svg.style.maxHeight = size + 'px';
  }

  const trackP = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  trackP.setAttribute('fill', 'none');
  trackP.setAttribute('stroke', '#1f1f2a');
  trackP.setAttribute('stroke-width', '8');
  trackP.setAttribute('stroke-linecap', 'round');

  const fillP = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  fillP.setAttribute('fill', 'none');
  fillP.setAttribute('stroke', '#7c6af5');
  fillP.setAttribute('stroke-width', '8');
  fillP.setAttribute('stroke-linecap', 'round');

  const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  dot.setAttribute('r', '6');
  dot.setAttribute('fill', '#e8e8f0');

  // label centred inside the arc hole
  const labelSvg = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  labelSvg.setAttribute('x', R);
  labelSvg.setAttribute('y', R + 3);
  labelSvg.setAttribute('text-anchor', 'middle');
  labelSvg.setAttribute('dominant-baseline', 'middle');
  labelSvg.setAttribute('fill', '#b8b8cc');
  labelSvg.setAttribute('font-family', "'IBM Plex Mono', monospace");
  labelSvg.setAttribute('font-size', Math.max(size * 0.12, 6));
  labelSvg.setAttribute('letter-spacing', '0.5');
  labelSvg.setAttribute('pointer-events', 'none');
  labelSvg.classList.add('knob-label-svg');
  labelSvg.textContent = (cfg.label || '').toUpperCase();

  svg.appendChild(trackP);
  svg.appendChild(fillP);
  svg.appendChild(dot);
  svg.appendChild(labelSvg);

  const valueEl = document.createElement('div');
  valueEl.className = 'knob-value';

  el.appendChild(svg);
  el.appendChild(valueEl);

  function draw(v) {
    v = Math.max(0, Math.min(1, v));
    el.dataset.value = v;
    const a = startA + v * (endA - startA);
    trackP.setAttribute('d', arc(trackR, startA, endA));
    fillP.setAttribute('d',  arc(trackR, startA, a));
    const [dx,dy] = polar(a, trackR);
    dot.setAttribute('cx', dx);
    dot.setAttribute('cy', dy);
    valueEl.textContent = v.toFixed(2);
  }
  draw(val);

  let y0, v0;
  el.addEventListener('pointerdown', e => {
    y0 = e.clientY; v0 = val; e.preventDefault();
    el.setPointerCapture(e.pointerId);
    const mv = e2 => {
      val = Math.max(0, Math.min(1, v0 + (y0 - e2.clientY) / knobSensitivity));
      draw(val); sendValue(cfg.channel, val);
    };
    const up = () => {
      el.removeEventListener('pointermove', mv);
      el.removeEventListener('pointerup', up);
    };
    el.addEventListener('pointermove', mv);
    el.addEventListener('pointerup', up);
  });

  el.addEventListener('wheel', e => {
    e.preventDefault();
    val = Math.max(0, Math.min(1, val - Math.sign(e.deltaY) * 0.01));
    draw(val); sendValue(cfg.channel, val);
  }, { passive: false });

  el.setValue = v => { val = Math.max(0, Math.min(1, v)); draw(val); };
  return el;
}


/* ── HORIZONTAL SLIDER ──────────────────────────────────── */

function createSlider(cfg) {
  const el = document.createElement('td-slider');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
  // only apply fixed width if explicitly set; otherwise fills container via CSS
  if (cfg.width) el.style.maxWidth = cfg.width + 'px';
  let val = Math.max(0, Math.min(1, cfg.default ?? 0));

  const lbl   = document.createElement('div'); lbl.className   = 'slider-label'; lbl.textContent = cfg.label || '';
  const track = document.createElement('div'); track.className = 'track';
  const fill  = document.createElement('div'); fill.className  = 'fill';
  const thumb = document.createElement('div'); thumb.className = 'thumb';
  const vEl   = document.createElement('div'); vEl.className   = 'slider-value';
  track.appendChild(fill); track.appendChild(thumb);
  el.appendChild(lbl); el.appendChild(track); el.appendChild(vEl);

  function draw(v) {
    v = Math.max(0, Math.min(1, v));
    el.dataset.value = v;
    vEl.textContent = v.toFixed(2);
    fill.style.width = thumb.style.left = (v * 100) + '%';
  }
  draw(val);

  function fromEvent(e) {
    const r = track.getBoundingClientRect();
    return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
  }

  track.addEventListener('pointerdown', e => {
    val = fromEvent(e); draw(val); sendValue(cfg.channel, val); e.preventDefault();
    track.setPointerCapture(e.pointerId);
    const mv = e2 => { val = fromEvent(e2); draw(val); sendValue(cfg.channel, val); };
    const up = () => {
      track.removeEventListener('pointermove', mv);
      track.removeEventListener('pointerup', up);
    };
    track.addEventListener('pointermove', mv);
    track.addEventListener('pointerup', up);
  });

  el.setValue = v => { val = Math.max(0, Math.min(1, v)); draw(val); };
  return el;
}


/* ── VERTICAL FADER (shared logic) ─────────────────────── */

function _buildVFader(cfg, tagName, showCenterLine) {
  const el = document.createElement(tagName);
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
  const h = cfg.height || 160;
  const w = cfg.width  || 32;

  // label row: label span + value span side by side
  const head = document.createElement('div');
  head.className = 'vfader-head';

  const lbl = document.createElement('span');
  lbl.className = 'vfader-label';
  lbl.textContent = cfg.label || '';

  const vEl = document.createElement('span');
  vEl.className = 'vfader-value';

  head.appendChild(lbl);
  head.appendChild(vEl);

  // track
  const track = document.createElement('div');
  track.className = 'vfader-track';
  // fixed size only if explicitly provided
  if (cfg.height) track.style.maxHeight = h + 'px';
  if (cfg.width)  track.style.maxWidth  = w + 'px';

  const fill = document.createElement('div');
  fill.className = 'vfader-fill';

  const thumb = document.createElement('div');
  thumb.className = 'vfader-thumb';

  // center line marker for crossfader
  if (showCenterLine) {
    const center = document.createElement('div');
    center.className = 'vfader-center';
    track.appendChild(center);
  }

  track.appendChild(fill);
  track.appendChild(thumb);

  el.appendChild(lbl);
  el.appendChild(track);
  el.appendChild(vEl);

  let val = Math.max(0, Math.min(1, cfg.default ?? 0.5));

  function draw(v) {
    v = Math.max(0, Math.min(1, v));
    el.dataset.value = v;
    // fill grows from bottom
    fill.style.height = (v * 100) + '%';
    // thumb: 0 = bottom, 1 = top
    thumb.style.bottom = `calc(${v * 100}% - 7px)`;
    vEl.textContent = v.toFixed(2);
  }
  draw(val);

  function fromEvent(e) {
    const r = track.getBoundingClientRect();
    // invert Y: top of track = 1, bottom = 0
    return Math.max(0, Math.min(1, 1 - (e.clientY - r.top) / r.height));
  }

  track.addEventListener('pointerdown', e => {
    val = fromEvent(e); draw(val); sendValue(cfg.channel, val); e.preventDefault();
    track.setPointerCapture(e.pointerId);
    const mv = e2 => { val = fromEvent(e2); draw(val); sendValue(cfg.channel, val); };
    const up = () => {
      track.removeEventListener('pointermove', mv);
      track.removeEventListener('pointerup', up);
    };
    track.addEventListener('pointermove', mv);
    track.addEventListener('pointerup', up);
  });

  el.addEventListener('wheel', e => {
    e.preventDefault();
    val = Math.max(0, Math.min(1, val - Math.sign(e.deltaY) * 0.01));
    draw(val); sendValue(cfg.channel, val);
  }, { passive: false });

  el.setValue = v => { val = Math.max(0, Math.min(1, v)); draw(val); };
  return el;
}

function createVFader(cfg) {
  return _buildVFader(cfg, 'td-vfader', false);
}

function createVXFader(cfg) {
  return _buildVFader(cfg, 'td-vxfader', true);
}


/* ── BUTTON / TOGGLE / BANG ─────────────────────────────── */

function createButton(cfg) {
  const el = document.createElement('td-button');
  el.setAttribute('type', cfg.type || 'button');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;

  const inner = document.createElement('div');
  inner.className = 'btn-inner';
  inner.textContent = cfg.label || '';
  el.appendChild(inner);

  if (cfg.type === 'toggle') {
    let on = !!(cfg.default);
    el.dataset.value = on ? 1 : 0;
    if (on) el.classList.add('on');
    el.addEventListener('click', () => {
      on = !on;
      el.dataset.value = on ? 1 : 0;
      el.classList.toggle('on', on);
      sendValue(cfg.channel, on ? 1 : 0);
    });
  } else if (cfg.type === 'bang') {
    el.addEventListener('click', () => sendValue(cfg.channel, 1));
  } else {
    el.addEventListener('click', () => {
      // scope deselection to the same panel body so multiple
      // independent button groups can coexist on the same page
      const scope = el.closest('.panel-body') || document;
      scope.querySelectorAll('td-button[type="button"]').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      sendValue(cfg.channel, cfg.value ?? 1);
    });
  }
  return el;
}


/* ── XY PAD ─────────────────────────────────────────────── */

function createXYPad(cfg) {
  const el   = document.createElement('td-xypad');
  const w    = cfg.width  || 120;
  const h    = cfg.height || 120;
  if (cfg.channel_x) el.dataset.channelX = cfg.channel_x;
  if (cfg.channel_y) el.dataset.channelY = cfg.channel_y;
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
  // for xypad, store both channels as the data-channel for tooltip lookup
  el.dataset.channel = [cfg.channel_x, cfg.channel_y].filter(Boolean).join(' / ');

  const surf = document.createElement('div'); surf.className = 'pad-surface';
  if (cfg.width)  surf.style.maxWidth  = w + 'px';
  if (cfg.height) surf.style.maxHeight = h + 'px';

  const curs = document.createElement('div'); curs.className = 'pad-cursor'; surf.appendChild(curs);

  // label centred inside the grid
  const lbl  = document.createElement('div'); lbl.className  = 'pad-label'; lbl.textContent = cfg.label || '';
  surf.appendChild(lbl);

  // x value centred at bottom edge, y value rotated on left edge
  const xv = document.createElement('div'); xv.className = 'pad-val-x';
  const yv = document.createElement('div'); yv.className = 'pad-val-y';
  surf.appendChild(xv);
  surf.appendChild(yv);

  el.appendChild(surf);

  let px = cfg.default_x ?? 0.5, py = cfg.default_y ?? 0.5;

  function draw() {
    el.dataset.valueX = px;
    el.dataset.valueY = py;
    curs.style.left = (px * 100) + '%';
    curs.style.top  = ((1 - py) * 100) + '%';
    xv.textContent  = px.toFixed(2);
    yv.textContent  = py.toFixed(2);
  }
  draw();

  function update(e) {
    const r = surf.getBoundingClientRect();
    px = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    py = Math.max(0, Math.min(1, 1 - (e.clientY - r.top) / r.height));
    draw();
    sendValue(cfg.channel_x, px);
    sendValue(cfg.channel_y, py);
  }

  el.setValue = (x, y) => {
    if (x !== null && x !== undefined) {
      px = Math.max(0, Math.min(1, x));
    }
    if (y !== null && y !== undefined) {
      py = Math.max(0, Math.min(1, y));
    }
    draw();
  };

  surf.addEventListener('pointerdown', e => {
    update(e); e.preventDefault();
    surf.setPointerCapture(e.pointerId);
    const mv = e2 => update(e2);
    const up = () => {
      surf.removeEventListener('pointermove', mv);
      surf.removeEventListener('pointerup', up);
    };
    surf.addEventListener('pointermove', mv);
    surf.addEventListener('pointerup', up);
  });

  return el;
}


/* ── HS COLOR PICKER ─────────────────────────────────────── */

function createColorPicker(cfg) {
  const el   = document.createElement('td-hspicker');
  const w    = cfg.width  || 120;
  const h    = cfg.height || 80;
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;

  const lbl  = document.createElement('div');
  lbl.className = 'hsp-label';
  lbl.textContent = cfg.label || '';

  const surf = document.createElement('div');
  surf.className = 'hsp-surface';
  // fixed size only if explicitly provided
  if (cfg.width)  surf.style.maxWidth  = w + 'px';
  if (cfg.height) surf.style.maxHeight = h + 'px';

  const canvas = document.createElement('canvas');
  canvas.width  = w;
  canvas.height = h;

  const grid = document.createElement('div');
  grid.className = 'hsp-grid';

  const curs = document.createElement('div');
  curs.className = 'hsp-cursor';

  surf.appendChild(canvas);
  surf.appendChild(grid);
  surf.appendChild(curs);

  const vals = document.createElement('div');
  vals.className = 'hsp-vals';
  const hv = document.createElement('span');
  const sv = document.createElement('span');
  vals.appendChild(hv);
  vals.appendChild(sv);

  const swatch = document.createElement('div');
  swatch.className = 'hsp-swatch';

  el.appendChild(lbl);
  el.appendChild(surf);
  el.appendChild(vals);
  el.appendChild(swatch);

  function drawCanvas() {
    const ctx = canvas.getContext('2d');
    const hueGrad = ctx.createLinearGradient(0, 0, w, 0);
    for (let i = 0; i <= 12; i++) {
      hueGrad.addColorStop(i / 12, `hsl(${i * 30}, 100%, 50%)`);
    }
    ctx.fillStyle = hueGrad;
    ctx.fillRect(0, 0, w, h);
    const satGrad = ctx.createLinearGradient(0, 0, 0, h);
    satGrad.addColorStop(0, 'rgba(255,255,255,0)');
    satGrad.addColorStop(1, 'rgba(255,255,255,1)');
    ctx.fillStyle = satGrad;
    ctx.fillRect(0, 0, w, h);
  }
  drawCanvas();

  let px = cfg.default_x ?? 0.0;
  let py = cfg.default_y ?? 1.0;

  function draw() {
    
    el.dataset.valueH = px;
    el.dataset.valueS = py;

    curs.style.left = (px * 100) + '%';
    curs.style.top  = ((1 - py) * 100) + '%';
    hv.textContent  = 'h:' + px.toFixed(2);
    sv.textContent  = 's:' + py.toFixed(2);
    const hDeg = px * 360;
    const sPct = py * 100;
    swatch.style.background = `hsl(${hDeg}, ${sPct}%, ${50 + (1 - py) * 25}%)`;
    curs.style.borderColor = py > 0.3 ? '#fff' : '#333';
  }
  draw();

  function update(e) {
    const r = surf.getBoundingClientRect();
    px = Math.max(0, Math.min(1, (e.clientX - r.left)  / r.width));
    py = Math.max(0, Math.min(1, 1 - (e.clientY - r.top) / r.height));
    draw();
    const [rv, gv, bv] = hsvToRgb(px, py, 1.0);
    sendValue(cfg.channel + '/r', rv);
    sendValue(cfg.channel + '/g', gv);
    sendValue(cfg.channel + '/b', bv);
  }

  surf.addEventListener('pointerdown', e => {
    update(e); e.preventDefault();
    surf.setPointerCapture(e.pointerId);
    const mv = e2 => update(e2);
    const up = () => {
      surf.removeEventListener('pointermove', mv);
      surf.removeEventListener('pointerup', up);
    };
    surf.addEventListener('pointermove', mv);
    surf.addEventListener('pointerup', up);
  });

  el.setValue = (hOrRgb, s) => {
    if (hOrRgb !== null && typeof hOrRgb === 'object') {
      const [h2, s2] = rgbToHsv(hOrRgb.r, hOrRgb.g, hOrRgb.b);
      px = Math.max(0, Math.min(1, h2));
      py = Math.max(0, Math.min(1, s2));
    } else {
      px = Math.max(0, Math.min(1, hOrRgb));
      py = Math.max(0, Math.min(1, s));
    }
    draw();
  };

  return el;
}

/* ── COLOR PRESET GRID ─────────────────────────────────────────── */
 
// Grid of solid-color square buttons for recalling color presets.
// Output is an integer index (0..n-1), same as radio — no RGB sent.
// cfg.label is comma-delimited CSS colors; defaults to a 9-color set.
 
const COLOR_GRID_DEFAULT = 'red,orange,yellow,lime,cyan,blue,darkviolet,magenta,white';
 
function createColorGrid(cfg) {
  const el = document.createElement('td-colorgrid');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
 
  const colors = (cfg.label || COLOR_GRID_DEFAULT)
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
 
  if (!colors.length) return el;
 
  const n = colors.length;
  const values = colors.map((_, i) => i);
 
  // snap default to nearest integer index
  const def = cfg.default ?? 0;
  let activeIdx = Math.max(0, Math.min(n - 1, Math.round(def)));
 
  const grid = document.createElement('div');
  grid.className = 'colorgrid-grid';
 
  colors.forEach((color, i) => {
    const swatch = document.createElement('div');
    swatch.className = 'colorgrid-swatch';
    swatch.style.background = color;
    swatch.dataset.idx = i;
 
    if (i === activeIdx) swatch.classList.add('active');
 
    swatch.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.preventDefault();
      activeIdx = i;
      grid.querySelectorAll('.colorgrid-swatch').forEach((s, j) => {
        s.classList.toggle('active', j === i);
      });
      el.dataset.value = values[i];
      sendValue(cfg.channel, values[i]);
    });
 
    grid.appendChild(swatch);
  });
 
  el.dataset.value = values[activeIdx];
  el.appendChild(grid);
 
  el.setValue = v => {
    const val = Math.round(parseFloat(v));
    const idx = Math.max(0, Math.min(n - 1, val));
    activeIdx = idx;
    grid.querySelectorAll('.colorgrid-swatch').forEach((s, j) => {
      s.classList.toggle('active', j === idx);
    });
    el.dataset.value = values[idx];
  };
 
  return el;
}


/* ── TOGGLE SWITCH ──────────────────────────────────────── */

function createToggle(cfg) {
  const el = document.createElement('td-toggle');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;

  const track  = document.createElement('div'); track.className  = 'toggle-track';
  const handle = document.createElement('div'); handle.className = 'toggle-handle';
  track.appendChild(handle);
  el.appendChild(track);

  let on = !!(cfg.default);
  el.dataset.value = on ? 1 : 0;

  function draw() {
    el.classList.toggle('on', on);
    el.dataset.value = on ? 1 : 0;
  }
  draw();

  el.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    e.preventDefault();
    on = !on;
    draw();
    sendValue(cfg.channel, on ? 1 : 0);
  });

  el.setValue = v => {
    on = parseFloat(v) >= 0.5;
    draw();
  };

  return el;
}


/* ── RADIO GROUP ────────────────────────────────────────── */

function createRadio(cfg) {
  const el = document.createElement('td-radio');
  el.dataset.channel = cfg.channel || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;

  // parse comma-delimited labels
  const labels = (cfg.label || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  if (!labels.length) return el;

  const n = labels.length;
  // evenly distribute values 0..1 across n buttons
  // n=1 → [0], n=2 → [0, 1], n>2 → evenly spaced
  //const values = labels.map((_, i) => n === 1 ? 0 : i / (n - 1));
  //
  // evenly distribute values 0..n across n buttons
  const values = labels.map((_, i) => i);
  let activeIdx = null;

  // find which button matches the default value
  const def = cfg.default ?? 0;
  let closest = 0, closestDist = Infinity;
  values.forEach((v, i) => {
    const d = Math.abs(v - def);
    if (d < closestDist) { closestDist = d; closest = i; }
  });
  activeIdx = closest;

  const buttons = labels.map((lbl, i) => {
    const btn = document.createElement('div');
    const btnLabel = document.createElement('span');
    btn.className = 'radio-btn';
    btnLabel.className = 'radio-btn-label';
    if (cfg.width) el.style.maxWidth = cfg.width + 'px';
    if (cfg.height) el.style.maxHeight = cfg.height + 'px';

    // border radius: round outer edges only
    if      (i === 0)         btn.classList.add('radio-first');
    else if (i === n - 1)    btn.classList.add('radio-last');

    btnLabel.textContent = lbl;
    btn.dataset.idx = i;

    if (i === activeIdx) btn.classList.add('active');

    btn.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.preventDefault();
      activeIdx = i;
      el.querySelectorAll('.radio-btn').forEach((b, j) => {
        b.classList.toggle('active', j === i);
      });
      el.dataset.value = values[i];
      sendValue(cfg.channel, values[i]);
    });

    btn.appendChild(btnLabel);
    return btn;
  });

  el.dataset.value = values[activeIdx];

  const row = document.createElement('div');
  row.className = 'radio-row';
  buttons.forEach(b => row.appendChild(b));
  el.appendChild(row);

  el.setValue = v => {
    const val = parseFloat(v);
    let closest = 0, closestDist = Infinity;
    values.forEach((bv, i) => {
      const d = Math.abs(bv - val);
      if (d < closestDist) { closestDist = d; closest = i; }
    });
    activeIdx = closest;
    el.querySelectorAll('.radio-btn').forEach((b, j) => {
      b.classList.toggle('active', j === closest);
    });
    el.dataset.value = values[closest];
  };

  return el;
}

/* ── EXECUTOR ───────────────────────────────────────────── */
 
function createExecutor(cfg) {
  const el = document.createElement('td-executor');
  el.dataset.channel = cfg.channel  || '';
  if (cfg.tooltip) el.dataset.tooltip = cfg.tooltip;
 
  // ── fader section (75% height) ──────────────────────────
  const faderWrap = document.createElement('div');
  faderWrap.className = 'executor-fader';
 
  const lbl = document.createElement('div');
  lbl.className = 'vfader-label';
  lbl.textContent = cfg.label || '';
 
  const track = document.createElement('div');
  track.className = 'vfader-track';
 
  const fill  = document.createElement('div'); fill.className  = 'vfader-fill';
  const thumb = document.createElement('div'); thumb.className = 'vfader-thumb';
  track.appendChild(fill);
  track.appendChild(thumb);
 
  const vEl = document.createElement('div');
  vEl.className = 'vfader-value';
 
  faderWrap.appendChild(lbl);
  faderWrap.appendChild(track);
  faderWrap.appendChild(vEl);
 
  // ── button section (25% height) ─────────────────────────
  const btnWrap = document.createElement('div');
  btnWrap.className = 'executor-btns';
 
  const BTNS = [
    { label: 'BLACK', suffix: 'black' },
    { label: 'FLASH', suffix: 'flash' },
    { label: 'SOLO',  suffix: 'solo'  },
  ];
 
  BTNS.forEach(({ label, suffix }) => {
    const btn = document.createElement('div');
    btn.className = `executor-btn executor-btn--${suffix}`;
    btn.textContent = label;
 
    btn.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      btn.classList.add('pressed');
      sendValue(`${cfg.channel}/${suffix}`, 1);
    });
 
    btn.addEventListener('pointerup', () => {
      btn.classList.remove('pressed');
      sendValue(`${cfg.channel}/${suffix}`, 0);
    });
 
    btn.addEventListener('pointercancel', () => {
      btn.classList.remove('pressed');
      sendValue(`${cfg.channel}/${suffix}`, 0);
    });
 
    btnWrap.appendChild(btn);
  });
 
  el.appendChild(faderWrap);
  el.appendChild(btnWrap);
 
  // ── fader interaction (shared with vfader) ───────────────
  let val = Math.max(0, Math.min(1, cfg.default ?? 0));
  el.dataset.value = val;
 
  function draw(v) {
    v = Math.max(0, Math.min(1, v));
    fill.style.height  = (v * 100) + '%';
    thumb.style.bottom = `calc(${v * 100}% - 7px)`;
    vEl.textContent    = v.toFixed(2);
    el.dataset.value   = v;
  }
  draw(val);
 
  function fromEvent(e) {
    const r = track.getBoundingClientRect();
    return Math.max(0, Math.min(1, 1 - (e.clientY - r.top) / r.height));
  }
 
  track.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    val = fromEvent(e); draw(val); sendValue(cfg.channel, val); e.preventDefault();
    track.setPointerCapture(e.pointerId);
    const mv = e2 => { val = fromEvent(e2); draw(val); sendValue(cfg.channel, val); };
    const up = () => {
      track.removeEventListener('pointermove', mv);
      track.removeEventListener('pointerup',   up);
    };
    track.addEventListener('pointermove', mv);
    track.addEventListener('pointerup',   up);
  });
 
  el.addEventListener('wheel', e => {
    e.preventDefault();
    val = Math.max(0, Math.min(1, val - Math.sign(e.deltaY) * 0.01));
    draw(val); sendValue(cfg.channel, val);
  }, { passive: false });
 
  el.setValue = v => { val = Math.max(0, Math.min(1, v)); draw(val); };
 
  return el;
}
/* ── PANEL BUILDER ──────────────────────────────────────── */

function buildPanel(colCfg) {
  const panel = document.createElement('div');
  panel.className = 'panel';

  // if header exists in the config table, add one
  if (colCfg.panel_label) {
    const header = document.createElement('div');
    header.className = 'panel-header';
    const label = document.createElement('span');
    label.className = 'panel-label';
    label.textContent = colCfg.panel_label;
    header.appendChild(label);
    panel.appendChild(header);
  }


  const body = document.createElement('div');
  body.className = 'panel-body';

  // direction: 'row' (default) or 'column'
  // max_per: if set, children get flex-basis: calc(100% / N) so exactly
  //          N fit per row before wrapping
  const direction = colCfg.direction || 'row';
  const maxPer    = colCfg.max_per   || null;

  body.dataset.direction = direction;
  if (direction === 'column') body.classList.add('panel-body--column');

  const widgets = [];
  (colCfg.widgets || []).forEach(cfg => {
    let w;
    switch (cfg.type) {
      case 'knob':        w = createKnob(cfg);        break;
      case 'slider':      w = createSlider(cfg);      break;
      case 'vfader':      w = createVFader(cfg);      break;
      case 'executor':    w = createExecutor(cfg);    break;
      case 'vxfader':     w = createVXFader(cfg);     break;
      case 'button':      w = createButton(cfg);      break;
      case 'bang':        w = createButton(cfg);      break;
      case 'toggle':      w = createToggle(cfg);      break;
      case 'xypad':       w = createXYPad(cfg);       break;
      case 'colorpicker': w = createColorPicker(cfg); break;
      case 'colorgrid':   w = createColorGrid(cfg); break;
      case 'toggle':      w = createToggle(cfg);      break;
      case 'radio':       w = createRadio(cfg);       break;
    }
    if (w) {
      // every cell takes an equal share — CSS handles the rest
      const cell = document.createElement('div');
      cell.className = 'widget-cell';
      cell.appendChild(w);
      body.appendChild(cell);
      widgets.push(w);
    }
  });

  panel.appendChild(body);
  return panel;
}


/* ── READ ALL VALUES ────────────────────────────────────── */

// Returns a flat { channel: value } dict for every widget
// that has a persistent scalar state, read from data-value
// attributes set by each widget's draw() function.
// Used by flushAllValues() in app.js and captureValues()
// in presets.js — add new widget types here, not there.

function readAllValues() {
  const values = {};

  document.querySelectorAll('[data-channel]').forEach(el => {
    const channel = el.dataset.channel;
    if (!channel) return;

    const tag = el.tagName.toLowerCase();

    switch (tag) {
      // scalar widgets — value stored directly on element
      case 'td-knob':
      case 'td-slider':
      case 'td-vfader':
      case 'td-vxfader': {
        const v = parseFloat(el.dataset.value);
        if (!isNaN(v)) values[channel] = v;
        break;
      }

      // toggle — stored as 0 or 1 on element
      case 'td-button': {
        if (el.getAttribute('type') === 'toggle') {
          const v = parseFloat(el.dataset.value);
          if (!isNaN(v)) values[channel] = v;
        }
        // bangs and scene buttons have no persistent state
        break;
      }

      // toggle switch
      case 'td-toggle': {
        const v = parseFloat(el.dataset.value);
        if (!isNaN(v)) values[channel] = v;
        break;
      }

      // radio group
      case 'td-radio': {
        const v = parseFloat(el.dataset.value);
        if (!isNaN(v)) values[channel] = v;
        break;
      }

      // xypad — two channels stored as valueX / valueY
      case 'td-xypad': {
        if (el.dataset.channelX) {
          const vx = parseFloat(el.dataset.valueX);
          if (!isNaN(vx)) values[el.dataset.channelX] = vx;
        }
        if (el.dataset.channelY) {
          const vy = parseFloat(el.dataset.valueY);
          if (!isNaN(vy)) values[el.dataset.channelY] = vy;
        }
        break;
      }

      // hspicker — stored as valueH / valueS, convert to r/g/b
      case 'td-hspicker': {
        const h = parseFloat(el.dataset.valueH);
        const s = parseFloat(el.dataset.valueS);
        if (!isNaN(h) && !isNaN(s)) {
          const [r, g, b] = hsvToRgb(h, s, 1.0);
          values[channel + '/r'] = r;
          values[channel + '/g'] = g;
          values[channel + '/b'] = b;
        }
        break;
      }
    }
  });

  return values;
}
