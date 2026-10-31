// ===== Teseracto 4D — proyección 4D → 3D → 2D sobre canvas =====

const canvas = document.getElementById('scene');
const ctx = canvas.getContext('2d');
const $ = (id) => document.getElementById(id);

let W = 0, H = 0, DPR = 1;
function resize() {
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = window.innerWidth;
  H = window.innerHeight;
  canvas.width = W * DPR;
  canvas.height = H * DPR;
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
window.addEventListener('resize', resize);
resize();

// ---------- Geometría ----------

function normalize(verts) {
  const r = Math.max(...verts.map((v) => Math.hypot(...v)));
  return verts.map((v) => v.map((c) => c / r));
}

function edgesByMinDistance(verts) {
  let min = Infinity;
  const d = (a, b) => Math.hypot(...a.map((c, i) => c - b[i]));
  for (let i = 0; i < verts.length; i++)
    for (let j = i + 1; j < verts.length; j++) min = Math.min(min, d(verts[i], verts[j]));
  const edges = [];
  for (let i = 0; i < verts.length; i++)
    for (let j = i + 1; j < verts.length; j++)
      if (Math.abs(d(verts[i], verts[j]) - min) < 1e-4) edges.push([i, j]);
  return edges;
}

function trianglesFromEdges(n, edges) {
  const adj = Array.from({ length: n }, () => new Set());
  edges.forEach(([a, b]) => { adj[a].add(b); adj[b].add(a); });
  const tris = [];
  edges.forEach(([a, b]) => {
    for (let c = b + 1; c < n; c++) if (adj[a].has(c) && adj[b].has(c)) tris.push([a, b, c]);
  });
  return tris;
}

function buildTesseract() {
  const verts = [];
  for (let i = 0; i < 16; i++) verts.push([0, 1, 2, 3].map((b) => (i >> b & 1 ? 1 : -1)));
  const edges = [];
  for (let i = 0; i < 16; i++)
    for (let b = 0; b < 4; b++) {
      const j = i ^ (1 << b);
      if (j > i) edges.push([i, j]);
    }
  const faces = [];
  for (let a = 0; a < 4; a++)
    for (let b = a + 1; b < 4; b++)
      for (let base = 0; base < 16; base++) {
        if (base & (1 << a) || base & (1 << b)) continue;
        faces.push([base, base | (1 << a), base | (1 << a) | (1 << b), base | (1 << b)]);
      }
  return { verts: normalize(verts), edges, faces, cells: 8 };
}

function buildSimplicial(rawVerts, cells) {
  const verts = normalize(rawVerts);
  const edges = edgesByMinDistance(verts);
  const faces = trianglesFromEdges(verts.length, edges);
  return { verts, edges, faces, cells };
}

function build16Cell() {
  const v = [];
  for (let i = 0; i < 4; i++)
    for (const s of [1, -1]) { const p = [0, 0, 0, 0]; p[i] = s; v.push(p); }
  return buildSimplicial(v, 16);
}

function build24Cell() {
  const v = [];
  for (let i = 0; i < 4; i++)
    for (let j = i + 1; j < 4; j++)
      for (const si of [1, -1])
        for (const sj of [1, -1]) { const p = [0, 0, 0, 0]; p[i] = si; p[j] = sj; v.push(p); }
  return buildSimplicial(v, 24);
}

function build5Cell() {
  const k = 1 / Math.sqrt(5);
  return buildSimplicial([
    [1, 1, 1, -k], [1, -1, -1, -k], [-1, 1, -1, -k], [-1, -1, 1, -k], [0, 0, 0, 4 * k],
  ], 5);
}

const SHAPES = {
  tesseract: {
    build: buildTesseract,
    name: 'Teseracto',
    sub: 'Hipercubo · sombra 3D de un objeto 4D',
    info: 'El análogo 4D del cubo: 8 cubos unidos de forma que cada cara cuadrada es compartida por dos. La imagen clásica de "un cubo dentro de otro cubo" es su proyección en perspectiva: el cubo pequeño está simplemente más lejos en la dirección W.',
  },
  cell16: {
    build: build16Cell,
    name: '16-celdas',
    sub: 'Hiperoctaedro · dual del teseracto',
    info: 'El análogo 4D del octaedro, formado por 16 tetraedros. Sus vértices son los centros de las 8 celdas del teseracto: es su figura dual.',
  },
  cell24: {
    build: build24Cell,
    name: '24-celdas',
    sub: 'Icositetracoron · sin equivalente en 3D',
    info: 'Formado por 24 octaedros. Es autodual y no tiene análogo en ninguna otra dimensión: es el único politopo regular convexo exclusivo del espacio 4D.',
  },
  cell5: {
    build: build5Cell,
    name: '5-celdas',
    sub: 'Pentácoron · el símplex 4D',
    info: 'El análogo 4D del tetraedro: 5 vértices todos conectados entre sí, que delimitan 5 tetraedros. Es el politopo 4D más simple posible.',
  },
};

// ---------- Estado ----------

const PLANES = [
  { id: 'XY', a: 0, b: 1 }, { id: 'XZ', a: 0, b: 2 }, { id: 'YZ', a: 1, b: 2 },
  { id: 'XW', a: 0, b: 3 }, { id: 'YW', a: 1, b: 3 }, { id: 'ZW', a: 2, b: 3 },
];

const PRESETS = {
  clasico: { XY: 0, XZ: 0, YZ: 0, XW: 0.6, YW: 0, ZW: 0 },
  clifford: { XY: 0.5, XZ: 0, YZ: 0, XW: 0, YW: 0, ZW: 0.5 },
  solo3d: { XY: 0.2, XZ: 0.4, YZ: 0.15, XW: 0, YW: 0, ZW: 0 },
  quieto: { XY: 0, XZ: 0, YZ: 0, XW: 0, YW: 0, ZW: 0 },
};
const DEFAULT_SPEEDS = { XY: 0, XZ: 0, YZ: 0.1, XW: 0.5, YW: 0, ZW: 0.3 };

const state = {
  shapeKey: 'tesseract',
  shape: null,
  speeds: { ...DEFAULT_SPEEDS },
  angles: { XY: 0, XZ: 0, YZ: 0, XW: 0, YW: 0, ZW: 0 },
  yaw: 0.6, pitch: -0.35, yawVel: 0, pitchVel: 0,
  paused: false,
  hover: -1, selected: -1,
  time: 0,
};

const opt = {}; // valores de controles, rellenados por bindControls()

// ---------- Panel: deslizadores de rotación ----------

const rotWrap = $('rotSliders');
PLANES.forEach((p) => {
  const row = document.createElement('div');
  row.className = 'rot-row' + (p.id.includes('W') ? ' w4' : '');
  row.innerHTML = `<span>${p.id}</span><input type="range" min="-2" max="2" step="0.05" id="rot${p.id}"><output id="rot${p.id}Val"></output>`;
  rotWrap.appendChild(row);
  const input = row.querySelector('input');
  input.addEventListener('input', () => {
    state.speeds[p.id] = parseFloat(input.value);
    syncRotSliders();
  });
});

function syncRotSliders() {
  PLANES.forEach((p) => {
    $('rot' + p.id).value = state.speeds[p.id];
    $('rot' + p.id + 'Val').textContent = state.speeds[p.id].toFixed(2);
  });
}

function applyPreset(name) {
  if (name === 'caos') {
    PLANES.forEach((p) => { state.speeds[p.id] = Math.round((Math.random() * 2.4 - 1.2) * 20) / 20; });
  } else {
    Object.assign(state.speeds, PRESETS[name]);
  }
  syncRotSliders();
}

document.querySelectorAll('[data-preset]').forEach((b) =>
  b.addEventListener('click', () => applyPreset(b.dataset.preset)));

// ---------- Panel: controles generales ----------

const SLIDERS = { d4: 2, d3: 1, zoom: 2, sliceW: 2, hue: 0, lineWidth: 1 };
const OUTPUTS = { d4: 'd4Val', d3: 'd3Val', zoom: 'zoomVal', sliceW: 'sliceVal', hue: 'hueVal', lineWidth: 'widthVal' };
const CHECKS = ['pulse', 'slice', 'sliceSweep', 'sliceOnly', 'showVerts', 'showEdges', 'showFaces', 'glow', 'trails', 'anaglyph', 'autoCam'];

function bindControls() {
  Object.entries(SLIDERS).forEach(([id, dec]) => {
    const el = $(id);
    const update = () => {
      opt[id] = parseFloat(el.value);
      $(OUTPUTS[id]).textContent = id === 'hue' ? opt[id] + '°' : opt[id].toFixed(dec);
    };
    el.addEventListener('input', update);
    update();
  });
  CHECKS.forEach((id) => {
    const el = $(id);
    const update = () => { opt[id] = el.checked; };
    el.addEventListener('change', update);
    update();
  });
  const cm = $('colorMode');
  cm.addEventListener('change', () => { opt.colorMode = cm.value; });
  opt.colorMode = cm.value;
}
bindControls();

function setControl(id, value) {
  const el = $(id);
  if (el.type === 'checkbox') el.checked = value; else el.value = value;
  el.dispatchEvent(new Event(el.type === 'checkbox' ? 'change' : 'input'));
}

function setShape(key) {
  state.shapeKey = key;
  state.shape = SHAPES[key].build();
  state.selected = -1;
  state.hover = -1;
  const s = state.shape;
  $('statV').textContent = s.verts.length;
  $('statE').textContent = s.edges.length;
  $('statF').textContent = s.faces.length;
  $('statC').textContent = s.cells;
  $('shapeInfo').textContent = SHAPES[key].info;
  $('subtitle').textContent = SHAPES[key].sub;
  document.querySelectorAll('[data-shape]').forEach((b) =>
    b.classList.toggle('active', b.dataset.shape === key));
}

document.querySelectorAll('[data-shape]').forEach((b) =>
  b.addEventListener('click', () => setShape(b.dataset.shape)));

function reset() {
  Object.keys(state.angles).forEach((k) => (state.angles[k] = 0));
  Object.assign(state.speeds, DEFAULT_SPEEDS);
  state.yaw = 0.6; state.pitch = -0.35; state.yawVel = state.pitchVel = 0;
  state.selected = -1;
  syncRotSliders();
  setControl('d4', 2.4); setControl('d3', 5); setControl('zoom', 1);
}

function togglePause() {
  state.paused = !state.paused;
  $('pauseBtn').textContent = state.paused ? '▶ Seguir' : '⏸ Pausa';
  $('pauseBtn').classList.toggle('active', state.paused);
}

function screenshot() {
  const out = document.createElement('canvas');
  out.width = canvas.width; out.height = canvas.height;
  const o = out.getContext('2d');
  o.fillStyle = '#04050d';
  o.fillRect(0, 0, out.width, out.height);
  o.drawImage(canvas, 0, 0);
  const a = document.createElement('a');
  a.download = `${state.shapeKey}-${Date.now()}.png`;
  a.href = out.toDataURL('image/png');
  a.click();
}

function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
}

function togglePanel() { $('panel').classList.toggle('closed'); }

$('pauseBtn').addEventListener('click', togglePause);
$('resetBtn').addEventListener('click', reset);
$('shotBtn').addEventListener('click', screenshot);
$('fullBtn').addEventListener('click', toggleFullscreen);
$('togglePanel').addEventListener('click', togglePanel);

window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' && e.target.type !== 'range' && e.target.type !== 'checkbox') return;
  const k = e.key.toLowerCase();
  if (k === ' ') { e.preventDefault(); togglePause(); }
  else if (k === 'r') reset();
  else if (k === 's') screenshot();
  else if (k === 'f') toggleFullscreen();
  else if (k === 'h') togglePanel();
  else if (k === 'c') setControl('slice', !opt.slice);
  else if (['1', '2', '3', '4'].includes(k)) setShape(Object.keys(SHAPES)[+k - 1]);
});

// ---------- Interacción con el ratón ----------

let drag = null;

canvas.addEventListener('pointerdown', (e) => {
  canvas.setPointerCapture(e.pointerId);
  drag = { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY, shift: e.shiftKey, moved: false };
  state.yawVel = state.pitchVel = 0;
  canvas.classList.add('dragging');
});

canvas.addEventListener('pointermove', (e) => {
  if (drag) {
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (Math.hypot(e.clientX - drag.sx, e.clientY - drag.sy) > 4) drag.moved = true;
    if (drag.shift || e.shiftKey) {
      state.angles.XW += dx * 0.01;
      state.angles.YW += dy * 0.01;
    } else {
      state.yaw += dx * 0.008;
      state.pitch = clamp(state.pitch + dy * 0.008, -1.5, 1.5);
      state.yawVel = dx * 0.008;
      state.pitchVel = dy * 0.008;
    }
    hideTooltip();
  } else {
    updateHover(e.clientX, e.clientY);
  }
});

canvas.addEventListener('pointerup', (e) => {
  if (drag && !drag.moved) {
    updateHover(e.clientX, e.clientY);
    state.selected = state.hover === state.selected ? -1 : state.hover;
  }
  drag = null;
  canvas.classList.remove('dragging');
});

canvas.addEventListener('pointerleave', () => { if (!drag) { state.hover = -1; hideTooltip(); } });

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  setControl('zoom', clamp(opt.zoom * Math.exp(-e.deltaY * 0.001), 0.3, 3));
}, { passive: false });

const tooltip = $('tooltip');
let lastScreen = [];
let lastRot4 = [];

function updateHover(x, y) {
  let best = -1, bestD = 14;
  lastScreen.forEach((p, i) => {
    const d = Math.hypot(p.sx - x, p.sy - y);
    if (d < bestD) { bestD = d; best = i; }
  });
  state.hover = best;
  canvas.classList.toggle('hovering', best >= 0);
  if (best < 0) return hideTooltip();
  const v = lastRot4[best];
  const n = state.shape.edges.filter(([a, b]) => a === best || b === best).length;
  tooltip.textContent =
    `vértice #${best}\n` +
    `x ${fmt(v[0])}   y ${fmt(v[1])}\n` +
    `z ${fmt(v[2])}   w ${fmt(v[3])}\n` +
    `${n} aristas conectadas`;
  tooltip.style.left = x + 16 + 'px';
  tooltip.style.top = y + 16 + 'px';
  tooltip.classList.remove('hidden');
}

function hideTooltip() { tooltip.classList.add('hidden'); }

// ---------- Matemáticas ----------

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const fmt = (n) => (n >= 0 ? ' ' : '') + n.toFixed(3);

function rotate4(v) {
  const p = v.slice();
  for (const pl of PLANES) {
    const t = state.angles[pl.id];
    if (!t) continue;
    const c = Math.cos(t), s = Math.sin(t);
    const x = p[pl.a], y = p[pl.b];
    p[pl.a] = c * x - s * y;
    p[pl.b] = s * x + c * y;
  }
  return p;
}

// 4D → 3D (perspectiva en W) → cámara → 2D
function project(p4, yawOffset) {
  const k = opt.d4Eff / (opt.d4Eff - p4[3]);
  let x = p4[0] * k, y = p4[1] * k, z = p4[2] * k;

  const cy = Math.cos(state.yaw + yawOffset), sy = Math.sin(state.yaw + yawOffset);
  [x, z] = [cy * x + sy * z, -sy * x + cy * z];
  const cp = Math.cos(state.pitch), sp = Math.sin(state.pitch);
  [y, z] = [cp * y - sp * z, sp * y + cp * z];

  const d3 = opt.d3;
  const s = d3 / Math.max(d3 - z, 0.2);
  const scale = Math.min(W, H) * 0.22 * opt.zoom;
  return { sx: W / 2 + x * s * scale, sy: H / 2 - y * s * scale, z, s, w: p4[3] };
}

function colorFor(i, p, l = 62, a = 1) {
  let h = opt.hue, sat = 90;
  switch (opt.colorMode) {
    case 'w': h = opt.hue + p.w * 90; break;
    case 'depth': h = opt.hue + p.z * 50; break;
    case 'rainbow': h = opt.hue + (i / state.shape.verts.length) * 360 + state.time * 30; break;
    case 'mono': sat = 70; l += (p.s - 1) * 20; break;
  }
  return `hsla(${h}, ${sat}%, ${clamp(l, 20, 90)}%, ${a})`;
}

// ---------- Corte con hiperplano w = c ----------

function computeSlice(rot4, c) {
  const crossing = (a, b) => {
    const wa = rot4[a][3] - c, wb = rot4[b][3] - c;
    if (wa * wb >= 0) return null;
    const t = wa / (wa - wb);
    return rot4[a].map((v, i) => v + (rot4[b][i] - v) * t);
  };
  const points = [];
  const segments = [];
  for (const f of state.shape.faces) {
    const hits = [];
    for (let i = 0; i < f.length; i++) {
      const p = crossing(f[i], f[(i + 1) % f.length]);
      if (p) hits.push(p);
    }
    if (hits.length === 2) segments.push(hits);
  }
  for (const [a, b] of state.shape.edges) {
    const p = crossing(a, b);
    if (p) points.push(p);
  }
  return { points, segments };
}

// ---------- Render ----------

function renderScene(rot4, yawOffset, tint) {
  const shape = state.shape;
  const pts = rot4.map((v) => project(v, yawOffset));
  if (yawOffset === 0 || tint === 'left') lastScreen = pts;

  const fade = opt.slice && opt.sliceOnly ? 0.18 : 1;
  const col = (i, p, l, a) => (tint ? tintColor(tint, a) : colorFor(i, p, l, a));
  const lw = opt.lineWidth;

  const neighbors = new Set();
  if (state.selected >= 0)
    shape.edges.forEach(([a, b]) => {
      if (a === state.selected) neighbors.add(b);
      if (b === state.selected) neighbors.add(a);
    });

  // Caras
  if (opt.showFaces) {
    const faces = shape.faces
      .map((f) => ({ f, z: f.reduce((s, i) => s + pts[i].z, 0) / f.length }))
      .sort((a, b) => a.z - b.z);
    for (const { f } of faces) {
      ctx.beginPath();
      f.forEach((i, n) => (n ? ctx.lineTo(pts[i].sx, pts[i].sy) : ctx.moveTo(pts[i].sx, pts[i].sy)));
      ctx.closePath();
      ctx.fillStyle = col(f[0], pts[f[0]], 55, 0.05 * fade);
      ctx.fill();
    }
  }

  // Aristas
  if (opt.showEdges) {
    const edges = shape.edges
      .map(([a, b]) => ({ a, b, z: (pts[a].z + pts[b].z) / 2 }))
      .sort((p, q) => p.z - q.z);
    for (const { a, b } of edges) {
      const pa = pts[a], pb = pts[b];
      const persp = (pa.s + pb.s) / 2;
      const highlighted = state.selected >= 0 && (a === state.selected || b === state.selected);
      const dim = state.selected >= 0 && !highlighted ? 0.25 : 1;
      let stroke;
      if (tint) stroke = tintColor(tint, 0.9 * fade);
      else {
        stroke = ctx.createLinearGradient(pa.sx, pa.sy, pb.sx, pb.sy);
        stroke.addColorStop(0, colorFor(a, pa, highlighted ? 75 : 62, 0.95 * dim * fade));
        stroke.addColorStop(1, colorFor(b, pb, highlighted ? 75 : 62, 0.95 * dim * fade));
      }
      if (opt.glow && !tint) {
        ctx.strokeStyle = colorFor(a, pa, 60, 0.12 * dim * fade);
        ctx.lineWidth = lw * persp * 4;
        line(pa, pb);
      }
      ctx.strokeStyle = stroke;
      ctx.lineWidth = lw * persp * (highlighted ? 1.8 : 1);
      line(pa, pb);
    }
  }

  // Vértices
  if (opt.showVerts) {
    pts.forEach((p, i) => {
      const special = i === state.selected || i === state.hover;
      const near = neighbors.has(i);
      const r = (lw * 1.6 + 1.5) * p.s * (special ? 1.8 : near ? 1.35 : 1);
      if (opt.glow && !tint) {
        const g = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, r * 4);
        g.addColorStop(0, colorFor(i, p, 70, 0.5 * fade));
        g.addColorStop(1, colorFor(i, p, 70, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.sx, p.sy, r * 4, 0, Math.PI * 2); ctx.fill();
      }
      ctx.fillStyle = special ? '#fff' : col(i, p, near ? 80 : 72, fade);
      ctx.beginPath(); ctx.arc(p.sx, p.sy, r, 0, Math.PI * 2); ctx.fill();
    });
  }

  // Sección del hiperplano
  if (opt.slice) {
    const { points, segments } = computeSlice(rot4, opt.sliceWEff);
    const sliceCol = tint ? tintColor(tint, 1) : '#ffd36b';
    ctx.lineWidth = lw * 1.5;
    for (const [a, b] of segments) {
      const pa = project(a, yawOffset), pb = project(b, yawOffset);
      if (opt.glow && !tint) {
        ctx.strokeStyle = 'rgba(255, 200, 90, 0.18)';
        ctx.lineWidth = lw * 6;
        line(pa, pb);
        ctx.lineWidth = lw * 1.5;
      }
      ctx.strokeStyle = sliceCol;
      line(pa, pb);
    }
    ctx.fillStyle = tint ? sliceCol : '#fff6d8';
    for (const p of points) {
      const q = project(p, yawOffset);
      ctx.beginPath(); ctx.arc(q.sx, q.sy, 2.5 * q.s, 0, Math.PI * 2); ctx.fill();
    }
  }
}

function line(a, b) {
  ctx.beginPath();
  ctx.moveTo(a.sx, a.sy);
  ctx.lineTo(b.sx, b.sy);
  ctx.stroke();
}

function tintColor(tint, a) {
  return tint === 'left' ? `rgba(255, 40, 40, ${a})` : `rgba(0, 220, 255, ${a})`;
}

// ---------- Bucle principal ----------

let last = performance.now();
let fpsSmooth = 60;

function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  fpsSmooth += (1 / Math.max(dt, 1e-3) - fpsSmooth) * 0.05;

  if (!state.paused) {
    state.time += dt;
    PLANES.forEach((p) => (state.angles[p.id] += state.speeds[p.id] * dt));
    if (opt.autoCam) state.yaw += dt * 0.25;
  }
  if (!drag) {
    state.yaw += state.yawVel;
    state.pitch = clamp(state.pitch + state.pitchVel, -1.5, 1.5);
    state.yawVel *= 0.93;
    state.pitchVel *= 0.93;
  }

  opt.d4Eff = opt.pulse ? opt.d4 + Math.sin(state.time * 1.3) * 0.6 : opt.d4;
  opt.d4Eff = Math.max(opt.d4Eff, 1.15);
  if (opt.sliceSweep && !state.paused) {
    const c = Math.sin(state.time * 0.7) * 0.95;
    $('sliceW').value = c;
    opt.sliceW = c;
    $('sliceVal').textContent = c.toFixed(2);
  }
  opt.sliceWEff = opt.sliceW;

  // Limpiar (o desvanecer para estelas)
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (opt.trails) {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = 'rgba(0, 0, 0, 0.14)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  ctx.restore();

  const rot4 = state.shape.verts.map(rotate4);
  lastRot4 = rot4;

  if (opt.anaglyph) {
    ctx.globalCompositeOperation = 'lighter';
    renderScene(rot4, -0.035, 'left');
    renderScene(rot4, 0.035, 'right');
    ctx.globalCompositeOperation = 'source-over';
  } else {
    ctx.globalCompositeOperation = opt.glow ? 'lighter' : 'source-over';
    renderScene(rot4, 0, null);
    ctx.globalCompositeOperation = 'source-over';
  }

  $('fps').textContent = `${Math.round(fpsSmooth)} fps`;
  $('angles').textContent = PLANES
    .filter((p) => p.id.includes('W'))
    .map((p) => `${p.id} ${((state.angles[p.id] * 180 / Math.PI) % 360).toFixed(0).padStart(4)}°`)
    .join('   ');

  requestAnimationFrame(frame);
}

// ---------- Inicio ----------

setShape('tesseract');
syncRotSliders();
if (window.innerWidth < 700) $('panel').classList.add('closed');
requestAnimationFrame(frame);
