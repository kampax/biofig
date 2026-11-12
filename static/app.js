/* BioFig — editor de figuras científicas (Konva) */
'use strict';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const uid = () => 'n' + Math.random().toString(36).slice(2, 10);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = (s) => String(s || '').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '');

const state = {
  doc: { w: 1600, h: 1000, bg: '#ffffff' },
  projectId: null,
  dirty: false,
  selected: [],
  tool: null,
  snap: true,
  showGrid: false,
  history: [],
  future: [],
  clipboard: null,
};

/* =================================================================== stage */
const wrap = $('#stage-wrap');
const stage = new Konva.Stage({ container: 'stage', width: wrap.clientWidth, height: wrap.clientHeight });
const layer = new Konva.Layer();
const ui = new Konva.Layer();
stage.add(layer, ui);

const page = new Konva.Rect({ name: 'page', x: 0, y: 0, width: state.doc.w, height: state.doc.h, fill: '#fff', shadowColor: 'rgba(0,0,0,.18)', shadowBlur: 24, shadowOffsetY: 4 });
const grid = new Konva.Shape({
  name: 'grid', listening: false, visible: false,
  sceneFunc(ctx) {
    ctx.beginPath();
    for (let x = 0; x <= state.doc.w; x += 20) { ctx.moveTo(x, 0); ctx.lineTo(x, state.doc.h); }
    for (let y = 0; y <= state.doc.h; y += 20) { ctx.moveTo(0, y); ctx.lineTo(state.doc.w, y); }
    ctx.setAttr('strokeStyle', 'rgba(47,128,237,.08)'); ctx.setAttr('lineWidth', 1); ctx.stroke();
  },
});
layer.add(page, grid);

const tr = new Konva.Transformer({
  rotateEnabled: true, anchorSize: 9, anchorCornerRadius: 2, borderStroke: '#2f80ed', anchorStroke: '#2f80ed',
  rotationSnaps: [0, 45, 90, 135, 180, 225, 270, 315], rotationSnapTolerance: 6, ignoreStroke: true,
  boundBoxFunc: (o, n) => (Math.abs(n.width) < 8 || Math.abs(n.height) < 8 ? o : n),
});
ui.add(tr);
const selRect = new Konva.Rect({ fill: 'rgba(47,128,237,.08)', stroke: '#2f80ed', strokeWidth: 1, dash: [4, 4], visible: false, listening: false });
ui.add(selRect);
let anchors = [];

const items = () => layer.getChildren((n) => n.hasName('item'));
const kind = (n) => n.getAttr('kind');
const pointer = () => layer.getRelativePointerPosition();

function resize() {
  stage.size({ width: wrap.clientWidth, height: wrap.clientHeight });
}
let firstFit = true;
new ResizeObserver(() => {
  if (!wrap.clientWidth || !wrap.clientHeight) return;
  resize();
  if (firstFit) { firstFit = false; fitPage(); }
}).observe(wrap);

function setZoom(z, center) {
  z = Math.max(0.1, Math.min(6, z));
  const old = stage.scaleX();
  center = center || { x: stage.width() / 2, y: stage.height() / 2 };
  const p = { x: (center.x - stage.x()) / old, y: (center.y - stage.y()) / old };
  stage.scale({ x: z, y: z });
  stage.position({ x: center.x - p.x * z, y: center.y - p.y * z });
  $('#zoomLabel').textContent = Math.round(z * 100) + '%';
  refreshAnchors();
}
function fitPage() {
  const z = Math.max(0.05, Math.min((stage.width() - 60) / state.doc.w, (stage.height() - 60) / state.doc.h));
  stage.scale({ x: z, y: z });
  stage.position({ x: (stage.width() - state.doc.w * z) / 2, y: (stage.height() - state.doc.h * z) / 2 });
  $('#zoomLabel').textContent = Math.round(z * 100) + '%';
  refreshAnchors();
}

/* ============================================================ SVG loading */
const imgCache = new Map();
function loadSvg(src) {
  if (imgCache.has(src)) return imgCache.get(src);
  if (/^data:image\/(png|jpe?g|gif|webp)/i.test(src) || /\.(png|jpe?g|gif|webp)(\?.*)?$/i.test(src)) { // imagen raster
    const pr = new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
    imgCache.set(src, pr);
    return pr;
  }
  const p = fetch(src).then((r) => { if (!r.ok) throw new Error('No se pudo cargar ' + src); return r.text(); }).then((txt) => {
    // Rasterizar siempre en alta resolución (~1024 px), con la proporción real: muchos iconos declaran
    // width="32" y se verían borrosos al agrandarlos en el lienzo.
    const head = txt.match(/<svg[^>]*>/i);
    if (head) {
      let tag = head[0];
      const num = (re) => { const m = tag.match(re); return m ? parseFloat(m[1]) : null; };
      let vb = tag.match(/viewBox\s*=\s*["']\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i);
      const w0 = num(/\swidth\s*=\s*["']\s*([\d.]+)/i), h0 = num(/\sheight\s*=\s*["']\s*([\d.]+)/i);
      if (!vb && w0 && h0) { tag = tag.replace(/<svg/i, `<svg viewBox="0 0 ${w0} ${h0}"`); vb = [null, 0, 0, w0, h0]; }
      if (vb) {
        const vw = parseFloat(vb[3]), vh = parseFloat(vb[4]), k = 1024 / Math.max(vw, vh);
        tag = tag.replace(/\s(width|height)\s*=\s*["'][^"']*["']/gi, '').replace(/<svg/i, `<svg width="${(vw * k).toFixed(1)}" height="${(vh * k).toFixed(1)}"`);
        txt = txt.replace(head[0], tag);
      }
    }
    const url = URL.createObjectURL(new Blob([txt], { type: 'image/svg+xml' }));
    return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = url; });
  });
  imgCache.set(src, p);
  return p;
}

/* Filtro "tinte": recolorea conservando sombras y luces */
function TintFilter(imageData) {
  const hex = this.getAttr('tint');
  if (!hex) return;
  const t = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const d = imageData.data;
  if (['PhyloPic', 'Health Icons'].includes((this.getAttr('meta') || {}).source)) { // silueta: relleno plano
    for (let i = 0; i < d.length; i += 4) if (d[i + 3]) { d[i] = t[0]; d[i + 1] = t[1]; d[i + 2] = t[2]; }
    return;
  }
  for (let i = 0; i < d.length; i += 4) {
    if (!d[i + 3]) continue;
    const l = (0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]) / 255;
    for (let c = 0; c < 3; c++) d[i + c] = l < 0.5 ? t[c] * 2 * l : t[c] + (255 - t[c]) * (2 * l - 1);
  }
}
function applyTint(n) {
  if (kind(n) !== 'icon') return;
  if (n.getAttr('tint')) { n.filters([TintFilter]); n.cache({ pixelRatio: 2 }); }
  else { n.filters([]); n.clearCache(); }
}

/* ================================================================ connectors */
function bezierCtrl(p) { // control point so that the curve passes through the middle point
  return { x: 2 * p[2] - (p[0] + p[4]) / 2, y: 2 * p[3] - (p[1] + p[5]) / 2 };
}
function drawHead(ctx, type, x, y, ang, sw, color) {
  if (!type || type === 'none') return;
  ctx.setLineDash([]);
  ctx.setAttr('fillStyle', color); ctx.setAttr('strokeStyle', color);
  const s = Math.max(9, sw * 3.6);
  ctx.beginPath();
  if (type === 'arrow') {
    ctx.moveTo(x, y);
    ctx.lineTo(x - s * Math.cos(ang - 0.42), y - s * Math.sin(ang - 0.42));
    ctx.lineTo(x - s * Math.cos(ang + 0.42), y - s * Math.sin(ang + 0.42));
    ctx.closePath(); ctx.fill();
  } else if (type === 'tbar') {
    const L = Math.max(10, sw * 4);
    ctx.setAttr('lineWidth', Math.max(3, sw * 1.4));
    ctx.moveTo(x + L * Math.cos(ang + Math.PI / 2), y + L * Math.sin(ang + Math.PI / 2));
    ctx.lineTo(x - L * Math.cos(ang + Math.PI / 2), y - L * Math.sin(ang + Math.PI / 2));
    ctx.stroke();
  } else if (type === 'circle') {
    ctx.arc(x, y, Math.max(5, sw * 2.2), 0, Math.PI * 2); ctx.fill();
  }
}
function makeConnector(o) {
  const n = new Konva.Shape({
    name: 'item', kind: 'connector', id: o.id || uid(), x: 0, y: 0,
    pts: o.pts, stroke: o.stroke || '#34495e', strokeWidth: o.strokeWidth || 3,
    head: o.head ?? 'arrow', tail: o.tail ?? 'none', dashed: !!o.dashed, curved: !!o.curved, from: o.from || null, to: o.to || null,
    opacity: o.opacity ?? 1, locked: !!o.locked, draggable: !o.locked, hitStrokeWidth: 18, lineCap: 'round',
    sceneFunc(ctx, shape) {
      const p = shape.getAttr('pts'), c = bezierCtrl(p), sw = shape.strokeWidth(), col = shape.stroke();
      const gap = (t) => (t === 'arrow' ? Math.max(9, sw * 3.6) * 0.6 : 0);
      const a2 = Math.atan2(p[5] - c.y, p[4] - c.x), a1 = Math.atan2(p[1] - c.y, p[0] - c.x);
      const e = { x: p[4] - gap(shape.getAttr('head')) * Math.cos(a2), y: p[5] - gap(shape.getAttr('head')) * Math.sin(a2) };
      const s = { x: p[0] - gap(shape.getAttr('tail')) * Math.cos(a1), y: p[1] - gap(shape.getAttr('tail')) * Math.sin(a1) };
      ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.quadraticCurveTo(c.x, c.y, e.x, e.y);
      ctx.setLineDash(shape.getAttr('dashed') ? [sw * 3, sw * 2.2] : []);
      ctx.setAttr('strokeStyle', col); ctx.setAttr('lineWidth', sw); ctx.setAttr('lineCap', 'round');
      ctx.stroke();
      drawHead(ctx, shape.getAttr('head'), p[4], p[5], a2, sw, col);
      ctx.setAttr('lineWidth', sw);
      drawHead(ctx, shape.getAttr('tail'), p[0], p[1], a1, sw, col);
    },
    hitFunc(ctx, shape) {
      const p = shape.getAttr('pts'), c = bezierCtrl(p);
      ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.quadraticCurveTo(c.x, c.y, p[4], p[5]);
      ctx.fillStrokeShape(shape);
    },
  });
  n.getSelfRect = function () {
    const p = this.getAttr('pts'), c = bezierCtrl(p), pad = this.strokeWidth() * 4;
    const xs = [p[0], p[4], c.x, p[2]], ys = [p[1], p[5], c.y, p[3]];
    const x0 = Math.min(...xs) - pad, y0 = Math.min(...ys) - pad;
    return { x: x0, y: y0, width: Math.max(...xs) + pad - x0, height: Math.max(...ys) + pad - y0 };
  };
  return n;
}
/* Conectores pegados a iconos: recalcular extremos cuando los iconos se mueven */
function boxOf(node) {
  const r = node.getClientRect({ relativeTo: layer });
  return { cx: r.x + r.width / 2, cy: r.y + r.height / 2, w: r.width + 14, h: r.height + 14 };
}
function updateAttached() {
  items().forEach((c) => {
    if (kind(c) !== 'connector' || (!c.getAttr('from') && !c.getAttr('to'))) return;
    bakeConnector(c);
    const p = c.getAttr('pts');
    const A = c.getAttr('from') && layer.findOne('#' + c.getAttr('from'));
    const B = c.getAttr('to') && layer.findOne('#' + c.getAttr('to'));
    const a = A ? boxOf(A) : { cx: p[0], cy: p[1], w: 0, h: 0 };
    const b = B ? boxOf(B) : { cx: p[4], cy: p[5], w: 0, h: 0 };
    const p1 = A ? clipToBox(a, b) : { x: p[0], y: p[1] };
    const p2 = B ? clipToBox(b, a) : { x: p[4], y: p[5] };
    let mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
    if (c.getAttr('curved')) { // conservar la curvatura relativa
      mx += p[2] - (p[0] + p[4]) / 2; my += p[3] - (p[1] + p[5]) / 2;
    }
    c.setAttr('pts', [p1.x, p1.y, mx, my, p2.x, p2.y]);
  });
  items().forEach((c) => kind(c) === 'connector' && placeConnLabels(c));
  layer.batchDraw();
}
/* Etiquetas de conectores: siguen el punto medio de su flecha con un desplazamiento fijo */
function placeConnLabels(c) {
  const p = c.getAttr('pts');
  items().forEach((t) => {
    if (t.getAttr('labelOf') !== c.id()) return;
    t.position({ x: p[2] + c.x() + (t.getAttr('labelDx') || 0), y: p[3] + c.y() + (t.getAttr('labelDy') || 0) });
  });
}
function rememberLabelOffset(t) {
  const c = t.getAttr('labelOf') && layer.findOne('#' + t.getAttr('labelOf'));
  if (!c) return;
  const p = c.getAttr('pts');
  t.setAttr('labelDx', t.x() - p[2] - c.x()); t.setAttr('labelDy', t.y() - p[3] - c.y());
}
function iconAt(x, y, except) {
  return items().reverse().find((n) => kind(n) === 'icon' && n !== except && Konva.Util.haveIntersection({ x, y, width: 1, height: 1 }, n.getClientRect({ relativeTo: layer })));
}
function attachEnds(c) {
  const p = c.getAttr('pts');
  const a = iconAt(p[0], p[1]), b = iconAt(p[4], p[5], a);
  c.setAttr('from', a ? a.id() : null); c.setAttr('to', b ? b.id() : null);
  updateAttached();
}
const followersOf = (nodes) => {
  const ids = new Set(nodes.map((n) => n.id()));
  return items().filter((t) => ((t.getAttr('anchorTo') && ids.has(t.getAttr('anchorTo'))) || (t.getAttr('labelOf') && ids.has(t.getAttr('labelOf')))) && !nodes.includes(t));
};

function bakeConnector(n) {
  const dx = n.x(), dy = n.y();
  if (!dx && !dy) return;
  n.setAttr('pts', n.getAttr('pts').map((v, i) => v + (i % 2 ? dy : dx)));
  n.position({ x: 0, y: 0 });
}
const TOOL_PRESETS = {
  arrow: { head: 'arrow', tail: 'none' }, inhibit: { head: 'tbar', tail: 'none' },
  dashed: { head: 'arrow', tail: 'none', dashed: true }, double: { head: 'arrow', tail: 'arrow' },
  catalysis: { head: 'circle', tail: 'none' }, line: { head: 'none', tail: 'none' },
};

function clearAnchors() { anchors.forEach((a) => a.destroy()); anchors = []; }
function refreshAnchors() {
  clearAnchors();
  if (state.selected.length !== 1 || kind(state.selected[0]) !== 'connector' || state.selected[0].getAttr('locked')) { ui.batchDraw(); return; }
  const n = state.selected[0];
  const r = 7 / stage.scaleX();
  [0, 1, 2].forEach((k) => {
    const p = n.getAttr('pts');
    const a = new Konva.Circle({ x: p[k * 2] + n.x(), y: p[k * 2 + 1] + n.y(), radius: k === 1 ? r * 0.85 : r, fill: k === 1 ? '#fff' : '#2f80ed', stroke: '#2f80ed', strokeWidth: 2 / stage.scaleX(), draggable: true });
    a.on('dragmove', () => {
      const pts = [...n.getAttr('pts')];
      pts[k * 2] = a.x() - n.x(); pts[k * 2 + 1] = a.y() - n.y();
      if (k === 1) n.setAttr('curved', true);
      else if (!n.getAttr('curved')) { pts[2] = (pts[0] + pts[4]) / 2; pts[3] = (pts[1] + pts[5]) / 2; anchors[1].position({ x: pts[2] + n.x(), y: pts[3] + n.y() }); }
      n.setAttr('pts', pts); placeConnLabels(n); layer.batchDraw();
    });
    a.on('dragend', () => {
      if (k !== 1) { // soltar un extremo sobre un icono lo pega a ese icono
        const pts = n.getAttr('pts'), hit = iconAt(pts[k * 2], pts[k * 2 + 1]);
        n.setAttr(k === 0 ? 'from' : 'to', hit ? hit.id() : null);
        updateAttached(); refreshAnchors();
      }
      commit();
    });
    a.on('mouseenter', () => (stage.container().style.cursor = 'move'));
    a.on('mouseleave', () => (stage.container().style.cursor = ''));
    ui.add(a); anchors.push(a);
  });
  ui.batchDraw();
}

/* ================================================================ node factory */
async function createNode(o) {
  let n;
  const base = { id: o.id || uid(), name: 'item', kind: o.kind, x: o.x || 0, y: o.y || 0, rotation: o.rotation || 0, opacity: o.opacity ?? 1, locked: !!o.locked, draggable: !o.locked };
  switch (o.kind) {
    case 'icon': {
      let img;
      try { img = await loadSvg(o.src); } catch (e) { console.warn(e); return null; }
      n = new Konva.Image({ ...base, image: img, width: o.width, height: o.height, offsetX: o.width / 2, offsetY: o.height / 2, scaleX: o.flip ? -1 : 1, src: o.src, iconId: o.iconId, meta: o.meta, tint: o.tint || null, alts: o.alts || [], pdb: o.pdb || null, realW: o.realW || null });
      break;
    }
    case 'rect':
      n = new Konva.Rect({ ...base, width: o.width, height: o.height, fill: o.fill, stroke: o.stroke, strokeWidth: o.strokeWidth ?? 2, cornerRadius: o.cornerRadius ?? 0, dash: o.dashed ? [10, 6] : [], dashed: !!o.dashed, strokeScaleEnabled: false });
      break;
    case 'ellipse':
      n = new Konva.Ellipse({ ...base, radiusX: o.radiusX, radiusY: o.radiusY, fill: o.fill, stroke: o.stroke, strokeWidth: o.strokeWidth ?? 2, dash: o.dashed ? [10, 6] : [], dashed: !!o.dashed, strokeScaleEnabled: false });
      break;
    case 'text':
      n = new Konva.Text({ ...base, text: o.text, fontSize: o.fontSize || 24, fontFamily: o.fontFamily || 'Arial', fontStyle: o.fontStyle || 'normal', fill: o.fill || '#1f2933', align: o.align || 'left', width: o.width || undefined, fixedWidth: !!o.width, lineHeight: 1.2, padding: 2, anchorTo: o.anchorTo || null, labelOf: o.labelOf || null, labelDx: o.labelDx || 0, labelDy: o.labelDy || 0, ...haloAttrs(!!o.halo) });
      break;
    case 'connector':
      n = makeConnector(o);
      break;
    default: return null;
  }
  layer.add(n);
  if (o.kind === 'icon' && o.tint) applyTint(n);
  return n;
}

function serializeNode(n) {
  const k = kind(n);
  const o = { kind: k, id: n.id(), x: round(n.x()), y: round(n.y()), rotation: round(n.rotation()), opacity: n.opacity(), locked: !!n.getAttr('locked') };
  if (k === 'icon') Object.assign(o, { src: n.getAttr('src'), iconId: n.getAttr('iconId'), meta: n.getAttr('meta'), width: round(n.width()), height: round(n.height()), flip: n.scaleX() < 0, tint: n.getAttr('tint') || null, alts: n.getAttr('alts') || [], pdb: n.getAttr('pdb') || null, realW: n.getAttr('realW') || null });
  if (k === 'rect') Object.assign(o, { width: round(n.width()), height: round(n.height()), fill: n.fill(), stroke: n.stroke(), strokeWidth: n.strokeWidth(), cornerRadius: n.cornerRadius(), dashed: !!n.getAttr('dashed') });
  if (k === 'ellipse') Object.assign(o, { radiusX: round(n.radiusX()), radiusY: round(n.radiusY()), fill: n.fill(), stroke: n.stroke(), strokeWidth: n.strokeWidth(), dashed: !!n.getAttr('dashed') });
  if (k === 'text') Object.assign(o, { text: n.text(), fontSize: round(n.fontSize()), fontFamily: n.fontFamily(), fontStyle: n.fontStyle(), fill: n.fill(), align: n.align(), width: n.getAttr('fixedWidth') ? Math.ceil(n.width()) : undefined, anchorTo: n.getAttr('anchorTo') || null, labelOf: n.getAttr('labelOf') || null, labelDx: round(n.getAttr('labelDx') || 0), labelDy: round(n.getAttr('labelDy') || 0), halo: !!n.getAttr('halo') });
  if (k === 'connector') { bakeConnector(n); Object.assign(o, { x: 0, y: 0, pts: n.getAttr('pts').map(round), stroke: n.stroke(), strokeWidth: n.strokeWidth(), head: n.getAttr('head'), tail: n.getAttr('tail'), dashed: !!n.getAttr('dashed'), curved: !!n.getAttr('curved'), from: n.getAttr('from') || null, to: n.getAttr('to') || null }); }
  return o;
}
function haloAttrs(on) { // contorno blanco para que el texto se lea sobre lineas
  return on ? { halo: true, stroke: '#ffffff', strokeWidth: 5, fillAfterStrokeEnabled: true, lineJoin: 'round' } : { halo: false, strokeWidth: 0, stroke: null };
}
const round = (v) => Math.round(v * 100) / 100;
const serialize = () => ({ ...state.doc, items: items().map(serializeNode) });

async function loadDoc(doc, { keepHistory = false } = {}) {
  select([]);
  items().forEach((n) => n.destroy());
  state.doc = { w: doc.w || 1600, h: doc.h || 1000, bg: doc.bg || '#ffffff' };
  page.size({ width: state.doc.w, height: state.doc.h }); page.fill(state.doc.bg);
  const nodes = await Promise.all((doc.items || []).map(createNode));
  // createNode es asíncrono: reordenar según el orden del documento
  nodes.forEach((n) => n && n.moveToTop());
  layer.batchDraw();
  if (!keepHistory) { state.history = [JSON.stringify(serialize())]; state.future = []; }
  renderProps();
}

/* =================================================================== history */
function commit() {
  const snap = JSON.stringify(serialize());
  if (state.history[state.history.length - 1] === snap) return;
  state.history.push(snap);
  if (state.history.length > 120) state.history.shift();
  state.future = [];
  setDirty(true);
  renderProps();
}
async function undo() {
  if (state.history.length < 2) return;
  state.future.push(state.history.pop());
  await loadDoc(JSON.parse(state.history[state.history.length - 1]), { keepHistory: true });
  setDirty(true);
}
async function redo() {
  if (!state.future.length) return;
  const s = state.future.pop();
  state.history.push(s);
  await loadDoc(JSON.parse(s), { keepHistory: true });
  setDirty(true);
}
function setDirty(v) { state.dirty = v; $('#dirtyMark').classList.toggle('on', v); }

/* ================================================================= selection */
function select(nodes) {
  state.selected = nodes.filter(Boolean);
  const transformable = state.selected.filter((n) => kind(n) !== 'connector' && !n.getAttr('locked'));
  tr.nodes(transformable);
  const onlyIcons = transformable.length && transformable.every((n) => kind(n) === 'icon');
  tr.keepRatio(!!onlyIcons);
  const onlyText = transformable.length === 1 && kind(transformable[0]) === 'text';
  tr.enabledAnchors(onlyText ? ['middle-left', 'middle-right', 'top-left', 'top-right', 'bottom-left', 'bottom-right'] : ['top-left', 'top-center', 'top-right', 'middle-right', 'middle-left', 'bottom-left', 'bottom-center', 'bottom-right']);
  refreshAnchors();
  renderProps();
  ui.batchDraw();
}
const itemOf = (t) => (t && t.hasName && t.hasName('item') ? t : null);

/* ===================================================================== mouse */
let panning = null, spaceDown = false, rubber = null, drawing = null, dragStart = null;

stage.on('wheel', (e) => {
  e.evt.preventDefault();
  const factor = e.evt.deltaY > 0 ? 1 / 1.1 : 1.1;
  setZoom(stage.scaleX() * factor, stage.getPointerPosition());
});

stage.on('mousedown touchstart', (e) => {
  const evt = e.evt;
  if (evt.button === 1 || spaceDown) {
    panning = { x: evt.clientX, y: evt.clientY, sx: stage.x(), sy: stage.y() };
    wrap.classList.add('panning'); evt.preventDefault(); return;
  }
  if (evt.button === 2) return;
  if (state.tool) {
    const p = pointer();
    const preset = TOOL_PRESETS[state.tool];
    drawing = makeConnector({ pts: [p.x, p.y, p.x, p.y, p.x, p.y], ...preset });
    layer.add(drawing); return;
  }
  if (e.target === stage || e.target === page) {
    const p = ui.getRelativePointerPosition();
    rubber = { x: p.x, y: p.y, add: evt.shiftKey };
    selRect.setAttrs({ x: p.x, y: p.y, width: 0, height: 0, visible: true, strokeWidth: 1 / stage.scaleX() });
  }
});

stage.on('mousemove touchmove', (e) => {
  if (panning) {
    stage.position({ x: panning.sx + e.evt.clientX - panning.x, y: panning.sy + e.evt.clientY - panning.y });
    stage.batchDraw(); return;
  }
  if (drawing) {
    const p = pointer(), pts = drawing.getAttr('pts');
    let x = p.x, y = p.y;
    if (e.evt.shiftKey) { // ángulos de 45°
      const a = Math.round(Math.atan2(y - pts[1], x - pts[0]) / (Math.PI / 4)) * (Math.PI / 4), d = Math.hypot(x - pts[0], y - pts[1]);
      x = pts[0] + d * Math.cos(a); y = pts[1] + d * Math.sin(a);
    }
    drawing.setAttr('pts', [pts[0], pts[1], (pts[0] + x) / 2, (pts[1] + y) / 2, x, y]);
    layer.batchDraw(); return;
  }
  if (rubber) {
    const p = ui.getRelativePointerPosition();
    selRect.setAttrs({ x: Math.min(p.x, rubber.x), y: Math.min(p.y, rubber.y), width: Math.abs(p.x - rubber.x), height: Math.abs(p.y - rubber.y) });
    ui.batchDraw();
  }
});

stage.on('mouseup touchend', () => {
  if (panning) { panning = null; wrap.classList.remove('panning'); refreshAnchors(); return; }
  if (drawing) {
    const p = drawing.getAttr('pts');
    if (Math.hypot(p[4] - p[0], p[5] - p[1]) < 8) { // clic sin arrastrar: flecha por defecto
      drawing.setAttr('pts', [p[0], p[1], p[0] + 80, p[1], p[0] + 160, p[1]]);
    }
    const n = drawing; drawing = null;
    attachEnds(n);
    setTool(null); commit(); select([n]); return;
  }
  if (rubber) {
    const box = selRect.getClientRect();
    selRect.visible(false);
    const wasClick = box.width < 4 && box.height < 4;
    const hits = wasClick ? [] : items().filter((n) => Konva.Util.haveIntersection(box, n.getClientRect()));
    select(rubber.add ? [...new Set([...state.selected, ...hits])] : hits);
    rubber = null;
  }
});

stage.on('click tap', (e) => {
  const n = itemOf(e.target);
  if (!n) return;
  if (e.evt.shiftKey || e.evt.ctrlKey || e.evt.metaKey) {
    select(state.selected.includes(n) ? state.selected.filter((x) => x !== n) : [...state.selected, n]);
  } else if (!state.selected.includes(n) || state.selected.length > 1 && !dragStart) {
    select([n]);
  }
});
stage.on('mousedown', (e) => {
  const n = itemOf(e.target);
  if (n && !state.selected.includes(n) && !e.evt.shiftKey && !state.tool) select([n]);
});

layer.on('dragstart', (e) => {
  const n = itemOf(e.target); if (!n) return;
  if (!state.selected.includes(n)) select([n]);
  dragStart = { node: n, x: n.x(), y: n.y(), others: state.selected.filter((o) => o !== n).map((o) => ({ o, x: o.x(), y: o.y() })),
    followers: followersOf(state.selected).map((o) => ({ o, x: o.x(), y: o.y() })) };
  clearAnchors();
});
layer.on('dragmove', (e) => {
  const n = itemOf(e.target); if (!n || !dragStart || dragStart.node !== n) return;
  if (state.snap && state.selected.length === 1 && kind(n) !== 'connector' && !e.evt?.altKey) {
    if (kind(n) === 'icon') { n.x(Math.round(n.x() / 5) * 5); n.y(Math.round(n.y() / 5) * 5); }
    else { n.x(Math.round(n.x() / 10) * 10); n.y(Math.round(n.y() / 10) * 10); }
  }
  const dx = n.x() - dragStart.x, dy = n.y() - dragStart.y;
  const nIsConn = kind(n) === 'connector';
  dragStart.others.forEach(({ o, x, y }) => {
    if (kind(o) === 'connector' || nIsConn || o.getAttr('locked')) { if (!o.getAttr('locked')) o.position({ x: x + dx, y: y + dy }); }
  });
  dragStart.followers.forEach(({ o, x, y }) => o.position({ x: x + dx, y: y + dy }));
  if (!nIsConn) updateAttached();
});
layer.on('dragend', () => {
  items().filter((n) => kind(n) === 'connector').forEach(bakeConnector);
  if (dragStart && kind(dragStart.node) === 'connector') attachEnds(dragStart.node);
  state.selected.forEach((t) => { if (t.getAttr('labelOf') && !state.selected.some((c) => c.id() === t.getAttr('labelOf'))) rememberLabelOffset(t); });
  dragStart = null;
  refreshAnchors(); commit();
});

tr.on('transformend', () => {
  tr.nodes().forEach((n) => {
    const sx = n.scaleX(), sy = n.scaleY(), k = kind(n);
    if (k === 'icon') {
      n.width(n.width() * Math.abs(sx)); n.height(n.height() * Math.abs(sy));
      n.offset({ x: n.width() / 2, y: n.height() / 2 }); n.scale({ x: Math.sign(sx), y: 1 });
      if (n.getAttr('tint')) applyTint(n);
    } else if (k === 'rect') {
      n.width(n.width() * sx); n.height(n.height() * sy); n.scale({ x: 1, y: 1 });
    } else if (k === 'ellipse') {
      n.radiusX(n.radiusX() * sx); n.radiusY(n.radiusY() * sy); n.scale({ x: 1, y: 1 });
    } else if (k === 'text') {
      const corner = Math.abs(sx - sy) < 0.01;
      if (corner) n.fontSize(Math.max(6, n.fontSize() * sy));
      n.width(n.width() * sx); n.scale({ x: 1, y: 1 }); n.setAttr('fixedWidth', true);
    }
  });
  updateAttached();
  commit();
});
tr.on('transform', () => { // texto: ancho variable sin deformar
  updateAttached();
  const n = tr.nodes()[0];
  if (tr.nodes().length === 1 && kind(n) === 'text' && ['middle-left', 'middle-right'].includes(tr.getActiveAnchor())) {
    n.width(Math.max(30, n.width() * n.scaleX())); n.scaleX(1); n.setAttr('fixedWidth', true);
  }
});

stage.on('dblclick dbltap', (e) => {
  const n = itemOf(e.target);
  if (n && kind(n) === 'text' && !n.getAttr('locked')) editText(n);
});

wrap.addEventListener('contextmenu', (e) => e.preventDefault());

function editText(n) {
  select([]);
  n.hide(); layer.batchDraw();
  const pos = n.absolutePosition(), z = stage.scaleX();
  const ta = document.createElement('textarea');
  ta.className = 'text-editor';
  ta.value = n.text();
  Object.assign(ta.style, {
    left: pos.x + 'px', top: pos.y + 'px', width: Math.max(80, (n.getAttr('fixedWidth') ? n.width() : n.width() + 40) * z) + 'px',
    fontSize: n.fontSize() * z + 'px', fontFamily: n.fontFamily(), color: n.fill(), textAlign: n.align(),
    fontWeight: n.fontStyle().includes('bold') ? 'bold' : 'normal', fontStyle: n.fontStyle().includes('italic') ? 'italic' : 'normal',
    transform: `rotate(${n.rotation()}deg)`, transformOrigin: 'top left',
  });
  const fit = () => { ta.style.height = 'auto'; ta.style.height = ta.scrollHeight + 4 + 'px'; };
  wrap.appendChild(ta); fit(); ta.focus(); ta.select();
  ta.addEventListener('input', fit);
  const done = () => {
    if (!ta.isConnected) return;
    n.text(ta.value || ' '); ta.remove(); n.show(); layer.batchDraw(); commit(); select([n]);
  };
  ta.addEventListener('blur', done);
  ta.addEventListener('keydown', (ev) => { ev.stopPropagation(); if (ev.key === 'Escape' || (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey))) ta.blur(); });
}

/* ================================================================= keyboard */
const typing = () => ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
window.addEventListener('keydown', async (e) => {
  if (!$('#modal').hidden) { if (e.key === 'Escape') closeModal(); return; } // con un cuadro abierto, no tocar el lienzo
  if (e.code === 'Space' && !typing()) { spaceDown = true; wrap.classList.add('panning'); e.preventDefault(); return; }
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key.toLowerCase() === 's') { e.preventDefault(); saveProject(); return; }
  if (typing()) return;
  const k = e.key.toLowerCase();
  if (mod && k === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
  else if (mod && (k === 'y' || (k === 'z' && e.shiftKey))) { e.preventDefault(); redo(); }
  else if (mod && k === 'c') copySel();
  else if (mod && k === 'd') { e.preventDefault(); copySel(); paste(); }
  else if (mod && k === 'a') { e.preventDefault(); select(items()); }
  else if (k === 'delete' || k === 'backspace') deleteSel();
  else if (k === 'escape') { setTool(null); select([]); }
  else if (k.startsWith('arrow') && state.selected.length) {
    e.preventDefault();
    const d = e.shiftKey ? 10 : 1;
    const [dx, dy] = { arrowleft: [-d, 0], arrowright: [d, 0], arrowup: [0, -d], arrowdown: [0, d] }[k];
    const moving = state.selected.filter((n) => !n.getAttr('locked'));
    [...moving, ...followersOf(moving)].forEach((n) => moveBy(n, dx, dy));
    updateAttached(); refreshAnchors(); clearTimeout(window._nudge); window._nudge = setTimeout(commit, 300);
  }
});
window.addEventListener('keyup', (e) => { if (e.code === 'Space') { spaceDown = false; wrap.classList.remove('panning'); } });

function moveBy(n, dx, dy) {
  if (kind(n) === 'connector') n.setAttr('pts', n.getAttr('pts').map((v, i) => v + (i % 2 ? dy : dx)));
  else n.position({ x: n.x() + dx, y: n.y() + dy });
}
function deleteSel() {
  if (!state.selected.length) return;
  const gone = [...state.selected, ...followersOf(state.selected)];
  const ids = new Set(gone.map((n) => n.id()));
  gone.forEach((n) => n.destroy());
  items().forEach((c) => { if (ids.has(c.getAttr('from'))) c.setAttr('from', null); if (ids.has(c.getAttr('to'))) c.setAttr('to', null); });
  select([]); layer.batchDraw(); commit();
}
function copySel() {
  if (!state.selected.length) return;
  state.clipboard = state.selected.map(serializeNode);
  toast(`${state.clipboard.length} elemento(s) copiado(s)`);
}
async function paste() {
  if (!state.clipboard) return;
  const idMap = Object.fromEntries(state.clipboard.map((o) => [o.id, uid()]));
  const remap = (id) => (id && idMap[id]) || null;
  const nodes = await Promise.all(state.clipboard.map((o) => {
    const c = { ...o, id: idMap[o.id], anchorTo: remap(o.anchorTo), labelOf: remap(o.labelOf), from: remap(o.from), to: remap(o.to) };
    if (c.kind === 'connector') c.pts = c.pts.map((v) => v + 24); else { c.x += 24; c.y += 24; }
    return createNode(c);
  }));
  state.clipboard = nodes.filter(Boolean).map(serializeNode);
  layer.batchDraw(); commit(); select(nodes.filter(Boolean));
}

/* ============================================================== adding things */
function viewCenter() {
  const t = layer.getAbsoluteTransform().copy().invert();
  const c = t.point({ x: stage.width() / 2, y: stage.height() / 2 });
  return { x: Math.max(60, Math.min(state.doc.w - 60, c.x)), y: Math.max(60, Math.min(state.doc.h - 60, c.y)) };
}

async function addIcon(icon, at, width = 160) {
  const aspect = icon.aspect || 1;
  const w = aspect >= 1 ? width : width * aspect, h = w / aspect;
  const p = at || viewCenter();
  const n = await createNode({ kind: 'icon', src: icon.src, iconId: icon.id, meta: { name: icon.name, author: icon.author, license: icon.license, source: icon.source }, x: p.x, y: p.y, width: w, height: h });
  if (!n) { toast('No se pudo cargar el icono'); return null; }
  layer.batchDraw(); commit(); select([n]);
  return n;
}

async function addShape(type) {
  const c = viewCenter();
  const presets = {
    rect: { kind: 'rect', x: c.x - 120, y: c.y - 70, width: 240, height: 140, fill: '#dbe8f5', stroke: '#5b7ea4', strokeWidth: 2, cornerRadius: 8 },
    ellipse: { kind: 'ellipse', x: c.x, y: c.y, radiusX: 220, radiusY: 140, fill: '#e9f6ea', stroke: '#3f9b4a', strokeWidth: 4 },
    nucleus: { kind: 'ellipse', x: c.x, y: c.y, radiusX: 90, radiusY: 65, fill: '#e7dcf3', stroke: '#7d5ba6', strokeWidth: 3, dashed: true },
    region: { kind: 'rect', x: c.x - 250, y: c.y - 150, width: 500, height: 300, fill: '#fdf5e4', stroke: '#d9b45a', strokeWidth: 2, cornerRadius: 18, dashed: true },
    text: { kind: 'text', x: c.x - 60, y: c.y - 14, text: 'Texto', fontSize: 24 },
    title: { kind: 'text', x: c.x - 150, y: c.y - 22, text: 'Título de la figura', fontSize: 40, fontStyle: 'bold', fill: '#1d3f72' },
  };
  const n = await createNode(presets[type]);
  if (['rect', 'ellipse', 'nucleus', 'region'].includes(type)) n.zIndex(2); // las formas van atrás
  layer.batchDraw(); commit(); select([n]);
  if (type === 'text' || type === 'title') editText(n);
}

function setTool(t) {
  state.tool = t;
  $$('.shape-btn[data-tool]').forEach((b) => b.classList.toggle('active', b.dataset.tool === t));
  wrap.classList.toggle('tool-active', !!t);
  if (t) select([]);
}

/* drag & drop from library */
wrap.addEventListener('dragover', (e) => e.preventDefault());
/* Imágenes propias (blots, fotos, microscopía): se incrustan en la figura */
function readImageFile(file) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => {
      const im = new Image();
      im.onload = () => {
        const MAX = 2400; // limitar tamaño para que el proyecto no pese demasiado
        let url = fr.result, w = im.naturalWidth, h = im.naturalHeight;
        if (Math.max(w, h) > MAX) {
          const k = MAX / Math.max(w, h); w = Math.round(w * k); h = Math.round(h * k);
          const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
          cv.getContext('2d').drawImage(im, 0, 0, w, h);
          url = cv.toDataURL(file.type === 'image/png' ? 'image/png' : 'image/jpeg', 0.92);
        }
        res({ url, w, h });
      };
      im.onerror = rej; im.src = fr.result;
    };
    fr.onerror = rej; fr.readAsDataURL(file);
  });
}
async function addImageFile(file, at) {
  if (!file || !/^image\/(png|jpe?g|gif|webp)$/i.test(file.type)) { toast('Formato no soportado (usá PNG, JPG, GIF o WebP)'); return; }
  const { url, w, h } = await readImageFile(file);
  const name = file.name && file.name !== 'image.png' ? file.name : 'Imagen pegada';
  const n = await addIcon({ id: 'img:' + uid(), name, src: url, author: '—', license: 'Propia', source: 'Imagen propia', aspect: w / h }, at, Math.min(420, w));
  if (n) toast('Imagen agregada');
}
$('#imgFile').addEventListener('change', async (e) => { for (const f of e.target.files) await addImageFile(f); e.target.value = ''; });
window.addEventListener('paste', async (e) => {
  if (typing() || !$('#modal').hidden) return;
  const file = [...(e.clipboardData?.items || [])].find((it) => it.kind === 'file' && it.type.startsWith('image/'))?.getAsFile();
  if (file) { e.preventDefault(); await addImageFile(file); }
  else if (state.clipboard) paste();
});

wrap.addEventListener('drop', async (e) => {
  e.preventDefault();
  if (e.dataTransfer.files?.length) {
    stage.setPointersPositions(e);
    const at = pointer();
    for (const f of e.dataTransfer.files) await addImageFile(f, at);
    return;
  }
  const id = e.dataTransfer.getData('text/icon-id');
  const icon = ICON_BY_ID.get(id);
  if (!icon) return;
  stage.setPointersPositions(e);
  addIcon(icon, pointer());
});

/* ================================================================= icon library */
let ICONS = [], ICON_BY_ID = new Map();
const lib = { group: 'ecologia', cat: '', q: '', shown: 0, results: [] };
const ES_EN = {
  arbol: 'tree', arboles: 'tree', bosque: 'forest tree', planta: 'plant', plantas: 'plant', hoja: 'leaf', flor: 'flower', raiz: 'root', semilla: 'seed', alga: 'algae alga', algas: 'algae',
  hongo: 'fungus fungi mushroom', hongos: 'fungi fungus', seta: 'mushroom', bacteria: 'bacteria bacterium', bacterias: 'bacteria', virus: 'virus', pez: 'fish', peces: 'fish', ave: 'bird', aves: 'bird', pajaro: 'bird',
  aguila: 'eagle', halcon: 'falcon hawk', buho: 'owl', lechuza: 'owl', lobo: 'wolf', zorro: 'fox', conejo: 'rabbit', liebre: 'hare', raton: 'mouse', rata: 'rat', oso: 'bear', ciervo: 'deer', venado: 'deer',
  vaca: 'cow cattle', oveja: 'sheep', cabra: 'goat', caballo: 'horse', cerdo: 'pig', jabali: 'boar', gato: 'cat', perro: 'dog', insecto: 'insect', insectos: 'insect', abeja: 'bee', mariposa: 'butterfly',
  hormiga: 'ant', mosca: 'fly', mosquito: 'mosquito', arana: 'spider', gusano: 'worm', lombriz: 'earthworm worm', serpiente: 'snake', rana: 'frog', sapo: 'toad', tortuga: 'turtle', lagarto: 'lizard',
  ballena: 'whale', delfin: 'dolphin', tiburon: 'shark', cangrejo: 'crab', camaron: 'shrimp', coral: 'coral', medusa: 'jellyfish', plancton: 'plankton', zooplancton: 'zooplankton', fitoplancton: 'phytoplankton',
  humano: 'human', persona: 'person human', murcielago: 'bat', mono: 'monkey', primate: 'primate', elefante: 'elephant', leon: 'lion', tigre: 'tiger', pato: 'duck', gallina: 'chicken', pinguino: 'penguin',
  celula: 'cell', celulas: 'cell', nucleo: 'nucleus', mitocondria: 'mitochondria mitochondrion', cloroplasto: 'chloroplast', ribosoma: 'ribosome', membrana: 'membrane', golgi: 'golgi', reticulo: 'reticulum',
  proteina: 'protein', proteinas: 'protein', enzima: 'enzyme', anticuerpo: 'antibody', receptor: 'receptor', canal: 'channel', adn: 'dna', arn: 'rna', gen: 'gene', genes: 'gene', cromosoma: 'chromosome',
  plasmido: 'plasmid', aminoacido: 'amino acid', molecula: 'molecule', lipido: 'lipid', azucar: 'sugar glucose', glucosa: 'glucose', agua: 'water', suelo: 'soil', sol: 'sun', nube: 'cloud', lluvia: 'rain',
  montana: 'mountain', rio: 'river', lago: 'lake', mar: 'sea ocean', oceano: 'ocean', tubo: 'tube', microscopio: 'microscope', pipeta: 'pipette', placa: 'plate petri', sangre: 'blood', hueso: 'bone',
  corazon: 'heart', cerebro: 'brain', pulmon: 'lung', higado: 'liver', rinon: 'kidney', neurona: 'neuron', parasito: 'parasite', levadura: 'yeast', grafico: 'graph chart', flecha: 'arrow', huevo: 'egg',
  satelite: 'satellite satelite', dron: 'drone dron uav', teledeteccion: 'satellite remote sensing teledeteccion', orbita: 'orbit orbita', antena: 'antenna antena', tractor: 'tractor', granja: 'farm granja barn', vaca: 'cow cattle vaca', fruta: 'fruit fruta', verdura: 'vegetable verdura', semilla: 'seed seedling semilla', membrana: 'membrane membrana bicapa bilayer', bicapa: 'bilayer bicapa', vesicula: 'vesicle vesicula liposoma', micela: 'micelle micela', liposoma: 'liposome liposoma', grafico: 'chart graph grafico', barras: 'bar barras', torta: 'pie torta', dispersion: 'scatter dispersion', flecha: 'arrow flecha', jeringa: 'syringe jeringa', centrifuga: 'centrifuge centrifuga', balanza: 'scale balance balanza', guantes: 'gloves guantes', lluvia: 'rain lluvia pluviometro', estacion: 'station estacion', clima: 'weather climate clima', suelo: 'soil suelo barreno', larva: 'larva', tejido: 'tissue', linfocito: 'lymphocyte', macrofago: 'macrophage', polen: 'pollen', musgo: 'moss', helecho: 'fern', pasto: 'grass', hierba: 'grass herb', cultivo: 'crop culture', trigo: 'wheat', maiz: 'maize corn',
};
const libTokens = (s) => norm(s).split(/[^a-z0-9]+/).filter((t) => t.length > 1);

function iconScore(ic, terms) {
  let s = 0;
  for (const alts of terms) {
    let best = 0;
    for (const t of alts) {
      if (ic._n.includes(t)) best = Math.max(best, 3);
      else if (t.length > 2 && ic._n.some((w) => w.startsWith(t))) best = Math.max(best, 2);
      else if (ic._c.includes(t)) best = Math.max(best, 1);
    }
    if (!best) return 0; // todos los términos deben aparecer
    s += best;
  }
  return s + (ic.source === 'BioFig' ? 0.3 : 0);
}

function filterIcons() {
  const terms = libTokens(lib.q).map((t) => [t, ...(ES_EN[t] ? libTokens(ES_EN[t]) : [])]);
  let res;
  if (terms.length) { // con texto: buscar en todo, el grupo elegido solo prioriza
    res = ICONS.filter((ic) => !lib.cat || ic.category === lib.cat)
      .map((ic) => { const sc = iconScore(ic, terms); return [sc && sc + (lib.group && ic.groups.includes(lib.group) ? 0.5 : 0), ic]; })
      .filter((x) => x[0] > 0).sort((a, b) => b[0] - a[0]).map((x) => x[1]);
  } else {
    res = ICONS.filter((ic) => (!lib.group || ic.groups.includes(lib.group)) && (!lib.cat || ic.category === lib.cat));
    res = [...res].sort((a, b) => (a.source === 'BioFig' ? -1 : 0) - (b.source === 'BioFig' ? -1 : 0) || a.category.localeCompare(b.category) || a.name.localeCompare(b.name));
  }
  lib.results = res; lib.shown = 0;
  $('#iconGrid').innerHTML = '';
  $('#resultCount').textContent = `${res.length} iconos en la biblioteca local`;
  showMore();
  searchPhylopic();
}
let ppToken = 0;
async function searchPhylopic() {
  const sec = $('#ppSection'), q = lib.q.trim(), token = ++ppToken;
  if (q.length < 3 || ['laboratorio', 'graficos', 'membranas', 'satelite'].includes(lib.group)) { sec.hidden = true; return; }
  sec.hidden = false; $('#ppGrid').innerHTML = ''; $('#ppCount').innerHTML = '<span class="spinner"></span>Buscando siluetas en PhyloPic…';
  try {
    const r = await fetch('/api/phylopic/search?limit=12&q=' + encodeURIComponent(q));
    const list = r.ok ? await r.json() : [];
    if (token !== ppToken) return;
    if (!list.length) { sec.hidden = true; return; }
    list.forEach((ic) => ICON_BY_ID.set(ic.id, ic));
    $('#ppCount').textContent = `🐾 ${list.length} siluetas de organismos · PhyloPic`;
    const frag = document.createDocumentFragment();
    list.forEach((ic) => frag.appendChild(makeCell(ic)));
    $('#ppGrid').appendChild(frag);
  } catch (e) { if (token === ppToken) sec.hidden = true; }
}
function makeCell(ic) {
  const d = document.createElement('div');
  d.className = 'icon-cell'; d.draggable = true;
  d.title = `${ic.name}\n${ic.category} · ${ic.author} · ${ic.license}`;
  d.innerHTML = `<img loading="lazy" src="${esc(ic.src)}" alt=""><span>${esc(ic.name)}</span>${ic.source === 'BioFig' ? '<i class="own">●</i>' : ''}${ic.source === 'PhyloPic' ? `<i class="pp">${esc(ic.license)}</i>` : ''}`;
  d.addEventListener('click', () => addIcon(ic));
  d.addEventListener('dragstart', (e) => e.dataTransfer.setData('text/icon-id', ic.id));
  if (ic.source === 'Mis iconos') {
    const del = document.createElement('button');
    del.className = 'cell-del'; del.title = 'Eliminar de Mis iconos'; del.textContent = '×';
    del.addEventListener('click', (e) => { e.stopPropagation(); deleteCustomIcon(ic); });
    d.appendChild(del);
  }
  return d;
}
function showMore() {
  const grid = $('#iconGrid');
  const next = lib.results.slice(lib.shown, lib.shown + 120);
  const frag = document.createDocumentFragment();
  next.forEach((ic) => frag.appendChild(makeCell(ic)));
  grid.appendChild(frag);
  lib.shown += next.length;
  $('#btnMore').hidden = lib.shown >= lib.results.length;
}
function fillCategories() {
  const cats = [...new Set(ICONS.filter((ic) => !lib.group || ic.groups.includes(lib.group)).map((ic) => ic.category))].sort();
  $('#catSelect').innerHTML = '<option value="">Todas las categorías</option>' + cats.map((c) => `<option>${esc(c)}</option>`).join('');
  lib.cat = '';
}
async function initLibrary() {
  ICONS = await (await fetch('/api/icons')).json();
  const mine = await fetch('/api/custom-icons').then((r) => (r.ok ? r.json() : [])).catch(() => []);
  ICONS = [...mine, ...ICONS];
  ICONS.forEach((ic) => { ic._n = libTokens(ic.name + ' ' + (ic.tags || '')); ic._c = libTokens(ic.category); ICON_BY_ID.set(ic.id, ic); });
  fillCategories(); filterIcons();
}
let searchT;
$('#iconSearch').addEventListener('input', (e) => { clearTimeout(searchT); searchT = setTimeout(() => { lib.q = e.target.value; filterIcons(); }, 160); });
$('#groupChips').addEventListener('click', (e) => {
  const b = e.target.closest('.chip'); if (!b) return;
  $$('.chip').forEach((c) => c.classList.toggle('active', c === b));
  lib.group = b.dataset.group; fillCategories(); filterIcons();
});
$('#catSelect').addEventListener('change', (e) => { lib.cat = e.target.value; filterIcons(); });
$('#btnMore').addEventListener('click', showMore);

/* ==================================================================== tabs */
$$('.tab').forEach((t) => t.addEventListener('click', () => {
  $$('.tab').forEach((x) => x.classList.toggle('active', x === t));
  $$('.tab-panel').forEach((p) => p.classList.toggle('active', p.id === 'tab-' + t.dataset.tab));
  if (t.dataset.tab === 'ai') refreshAIStatus();
}));
$$('.shape-btn[data-tool]').forEach((b) => b.addEventListener('click', () => setTool(state.tool === b.dataset.tool ? null : b.dataset.tool)));
$$('.shape-btn[data-add]').forEach((b) => b.addEventListener('click', () => addShape(b.dataset.add)));

/* ============================================================= properties */
const PALETTE = ['#1f2933', '#ffffff', '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60', '#1abc9c', '#3498db', '#2f80ed', '#9b59b6', '#8e5a2b', '#95a5a6', '#fdf5e4', '#e9f6ea', '#dbe8f5', '#f6e3ea', '#e7dcf3'];
function renderProps() {
  const el = $('#props');
  const sel = state.selected;
  if (!sel.length) {
    el.innerHTML = `<h3>Lienzo</h3>
      <div class="row"><label>Ancho</label><input type="number" id="pW" value="${state.doc.w}" min="200" max="8000" step="10"></div>
      <div class="row"><label>Alto</label><input type="number" id="pH" value="${state.doc.h}" min="200" max="8000" step="10"></div>
      <div class="row"><label>Tamaño</label><select id="pPreset"><option value="">Personalizado</option><option value="1600x1000">Figura 16:10</option><option value="1920x1080">Diapositiva 16:9</option><option value="2480x3508">A4 vertical</option><option value="3508x2480">A4 horizontal</option><option value="1500x1500">Cuadrado / abstract gráfico</option></select></div>
      <div class="row"><label>Fondo</label><input type="color" id="pBg" value="${state.doc.bg}"></div>
      <div class="row"><label>Imantar a la cuadrícula</label><input type="checkbox" id="pSnap" ${state.snap ? 'checked' : ''}></div>
      <div class="row"><label>Mostrar cuadrícula</label><input type="checkbox" id="pGrid" ${state.showGrid ? 'checked' : ''}></div>
      ${realSizeHtml(null)}
      <hr><p class="meta">Elementos: ${items().length}<br>Seleccioná algo para editarlo. Arrastrá en un área vacía para seleccionar varios.</p>`;
    if ($('#pReal')) $('#pReal').onclick = () => fitRealSize(null);
    $('#pW').onchange = (e) => { state.doc.w = +e.target.value; page.width(state.doc.w); layer.batchDraw(); commit(); };
    $('#pH').onchange = (e) => { state.doc.h = +e.target.value; page.height(state.doc.h); layer.batchDraw(); commit(); };
    $('#pPreset').onchange = (e) => { if (!e.target.value) return; const [w, h] = e.target.value.split('x').map(Number); Object.assign(state.doc, { w, h }); page.size({ width: w, height: h }); fitPage(); layer.batchDraw(); commit(); };
    $('#pBg').oninput = (e) => { state.doc.bg = e.target.value; page.fill(e.target.value); layer.batchDraw(); };
    $('#pBg').onchange = () => commit();
    $('#pSnap').onchange = (e) => (state.snap = e.target.checked);
    $('#pGrid').onchange = (e) => { state.showGrid = e.target.checked; grid.visible(state.showGrid); layer.batchDraw(); };
    return;
  }
  const n = sel[0], k = kind(n), multi = sel.length > 1;
  const names = { icon: 'Icono', rect: 'Rectángulo', ellipse: 'Elipse', text: 'Texto', connector: 'Conector' };
  let h = `<h3>${multi ? sel.length + ' elementos' : names[k]}</h3>`;
  const color = (id, label, val) => `<div class="row"><label>${label}</label><input type="color" id="${id}" value="${toHex(val)}"></div>`;
  if (!multi && k === 'icon') {
    const m = n.getAttr('meta') || {};
    h += `<div class="row"><label>Tinte</label><span><input type="color" id="pTint" value="${n.getAttr('tint') || '#3498db'}"> <button id="pTintOff" ${n.getAttr('tint') ? '' : 'disabled'}>Quitar</button></span></div>
      <div class="swatches" id="pSw">${PALETTE.map((c) => `<span style="background:${c}" data-c="${c}"></span>`).join('')}</div>
      <div class="btns"><button id="pFlip">⇋ Espejar</button></div>
      <div class="meta" style="margin-top:8px"><b>${esc(m.name)}</b><br>${esc(m.author)} · ${esc(m.license)} · ${esc(m.source)}</div>`;
    const alts = altIcons(n);
    if (alts.length) h += `<div class="row" style="margin-top:10px"><label>Alternativas sugeridas</label></div><div class="alts">${alts.map((a) => `<img src="${esc(a.src)}" data-id="${esc(a.id)}" title="${esc(a.name)} · ${esc(a.source)}">`).join('')}</div>`;
    const is3d = n.getAttr('pdb') || /^pdb:/.test(n.getAttr('iconId') || '');
    const isRaster = /^data:image\/(png|jpe?g|webp|gif)|\.(png|jpe?g|webp|gif)(\?|$)/i.test(n.getAttr('src') || '');
    if (!is3d && isRaster && ['Imagen propia', 'Mis iconos'].includes(m.source)) {
      h += `<div class="btns"><button id="pRemoveBg" class="primary">✂ Quitar fondo</button>${m.source === 'Imagen propia' ? '<button id="pSaveMine">★ Guardar en Mis iconos</button>' : ''}</div>`;
    }
    h += is3d
      ? `<div class="btns"><button id="p3Edit" class="primary">🧬 Reorientar en 3D</button></div>${realSizeHtml(n)}`
      : `<div class="btns"><button id="pFindPP" title="Buscar siluetas en PhyloPic con este nombre">Buscar organismo similar</button></div>`;
  }
  if (!multi && (k === 'rect' || k === 'ellipse')) {
    h += color('pFill', 'Relleno', n.fill()) + `<div class="swatches" id="pSw">${PALETTE.map((c) => `<span style="background:${c}" data-c="${c}"></span>`).join('')}</div>`;
    h += `<div class="row"><label>Sin relleno</label><input type="checkbox" id="pNoFill" ${!n.fill() ? 'checked' : ''}></div>`;
    h += color('pStroke', 'Borde', n.stroke()) + `<div class="row"><label>Grosor</label><input type="number" id="pSW" value="${n.strokeWidth()}" min="0" max="40"></div>`;
    h += `<div class="row"><label>Discontinuo</label><input type="checkbox" id="pDash" ${n.getAttr('dashed') ? 'checked' : ''}></div>`;
    if (k === 'rect') h += `<div class="row"><label>Esquinas</label><input type="number" id="pRad" value="${n.cornerRadius()}" min="0" max="300"></div>`;
  }
  if (!multi && k === 'text') {
    h += `<textarea id="pText" rows="3">${esc(n.text())}</textarea>
      <div class="row"><label>Tamaño</label><input type="number" id="pFS" value="${Math.round(n.fontSize())}" min="6" max="300"></div>
      ${color('pFill', 'Color', n.fill())}
      <div class="row"><label>Contorno blanco</label><input type="checkbox" id="pHalo" ${n.getAttr('halo') ? 'checked' : ''}></div>
      <div class="row"><label>Fuente</label><select id="pFont">${['Arial', 'Helvetica', 'Verdana', 'Georgia', 'Times New Roman', 'Courier New', 'Segoe UI'].map((f) => `<option ${f === n.fontFamily() ? 'selected' : ''}>${f}</option>`).join('')}</select></div>
      <div class="btns"><button id="pBold" class="${n.fontStyle().includes('bold') ? 'primary' : ''}"><b>N</b></button><button id="pItal" class="${n.fontStyle().includes('italic') ? 'primary' : ''}"><i>K</i></button>
      ${['left', 'center', 'right'].map((a) => `<button data-align="${a}" class="${n.align() === a ? 'primary' : ''}">${{ left: '⯇ Izq', center: 'Centro', right: 'Der ⯈' }[a]}</button>`).join('')}</div>`;
  }
  if (!multi && k === 'connector') {
    const heads = { arrow: 'Flecha', tbar: 'Inhibición (T)', circle: 'Círculo', none: 'Ninguno' };
    const opt = (v) => Object.entries(heads).map(([key, l]) => `<option value="${key}" ${key === v ? 'selected' : ''}>${l}</option>`).join('');
    h += color('pStroke', 'Color', n.stroke()) + `<div class="swatches" id="pSw">${PALETTE.map((c) => `<span style="background:${c}" data-c="${c}"></span>`).join('')}</div>
      <div class="row"><label>Grosor</label><input type="number" id="pSW" value="${n.strokeWidth()}" min="1" max="30"></div>
      <div class="row"><label>Final</label><select id="pHead">${opt(n.getAttr('head'))}</select></div>
      <div class="row"><label>Inicio</label><select id="pTail">${opt(n.getAttr('tail'))}</select></div>
      <div class="row"><label>Discontinuo</label><input type="checkbox" id="pDash" ${n.getAttr('dashed') ? 'checked' : ''}></div>
      <div class="btns"><button id="pStraight">Enderezar</button><button id="pReverse">Invertir sentido</button><button id="pLabel">+ Etiqueta</button></div>
      <p class="meta" style="margin-top:8px">Arrastrá los puntos azules para mover los extremos y el blanco para curvar.</p>`;
  }
  if (multi) {
    h += `<div class="row"><label>Alinear</label></div><div class="btns">
      <button data-al="left">⇤ Izq</button><button data-al="hcenter">↔ Centro</button><button data-al="right">Der ⇥</button>
      <button data-al="top">⤒ Arriba</button><button data-al="vcenter">↕ Medio</button><button data-al="bottom">Abajo ⤓</button>
      <button data-al="hdist">Distribuir ↔</button><button data-al="vdist">Distribuir ↕</button></div>`;
  }
  h += `<hr><div class="row"><label>Opacidad</label><input type="range" id="pOp" min="0.05" max="1" step="0.05" value="${n.opacity()}"></div>`;
  if (!multi && k !== 'connector') h += `<div class="row"><label>Rotación</label><input type="number" id="pRot" value="${Math.round(n.rotation())}" step="5"></div>`;
  h += `<div class="btns"><button id="pFront">Al frente</button><button id="pBack">Al fondo</button><button id="pUp">Subir</button><button id="pDown">Bajar</button></div>
    <div class="btns"><button id="pDup">Duplicar</button><button id="pLock">${n.getAttr('locked') ? '🔓 Desbloquear' : '🔒 Bloquear'}</button><button id="pDel" class="danger">Eliminar</button></div>`;
  el.innerHTML = h;

  const set = (fn, live = false) => (e) => { sel.forEach((x) => fn(x, e)); layer.batchDraw(); if (!live) commit(); else refreshAnchors(); };
  const on = (id, ev, fn) => { const x = $('#' + id); if (x) x.addEventListener(ev, fn); };

  on('pTint', 'input', (e) => { n.setAttr('tint', e.target.value); applyTint(n); layer.batchDraw(); });
  on('pTint', 'change', () => commit());
  on('pTintOff', 'click', () => { n.setAttr('tint', null); applyTint(n); layer.batchDraw(); commit(); });
  on('pFlip', 'click', () => { n.scaleX(-n.scaleX()); layer.batchDraw(); commit(); });
  $$('#props .alts img').forEach((img) => img.addEventListener('click', () => swapIcon(n, altIcons(n).find((a) => a.id === img.dataset.id))));
  on('p3Edit', 'click', () => openPdbModal(n));
  on('pRemoveBg', 'click', () => removeBgFromNode(n));
  on('pSaveMine', 'click', () => saveNodeAsCustom(n));
  on('pReal', 'click', () => fitRealSize(n));
  on('pFindPP', 'click', () => {
    const name = (n.getAttr('meta') || {}).name || '';
    $$('.tab').find((t) => t.dataset.tab === 'icons').click();
    $('#iconSearch').value = name; lib.q = name; filterIcons();
  });
  on('pSw', 'click', (e) => {
    const c = e.target.dataset.c; if (!c) return;
    if (k === 'icon') { n.setAttr('tint', c); applyTint(n); } else if (k === 'connector') n.stroke(c); else n.fill(c);
    layer.batchDraw(); commit();
  });
  on('pFill', 'input', set((x, e) => x.fill(e.target.value), true)); on('pFill', 'change', () => commit());
  on('pNoFill', 'change', set((x, e) => x.fill(e.target.checked ? null : '#ffffff')));
  on('pStroke', 'input', set((x, e) => x.stroke(e.target.value), true)); on('pStroke', 'change', () => commit());
  on('pSW', 'change', set((x, e) => x.strokeWidth(+e.target.value)));
  on('pDash', 'change', set((x, e) => { x.setAttr('dashed', e.target.checked); if (kind(x) !== 'connector') x.dash(e.target.checked ? [10, 6] : []); }));
  on('pRad', 'change', set((x, e) => x.cornerRadius(+e.target.value)));
  on('pText', 'input', set((x, e) => x.text(e.target.value), true)); on('pText', 'change', () => commit());
  on('pFS', 'change', set((x, e) => x.fontSize(+e.target.value)));
  on('pFont', 'change', set((x, e) => x.fontFamily(e.target.value)));
  on('pHalo', 'change', set((x, e) => x.setAttrs(haloAttrs(e.target.checked))));
  const toggleStyle = (st) => () => { const cur = n.fontStyle(); const parts = new Set(cur.split(' ').filter((p) => p && p !== 'normal')); parts.has(st) ? parts.delete(st) : parts.add(st); n.fontStyle([...parts].join(' ') || 'normal'); layer.batchDraw(); commit(); };
  on('pBold', 'click', toggleStyle('bold')); on('pItal', 'click', toggleStyle('italic'));
  $$('#props [data-align]').forEach((b) => b.addEventListener('click', () => { n.setAttr('fixedWidth', true); n.width(n.width()); n.align(b.dataset.align); layer.batchDraw(); commit(); }));
  on('pHead', 'change', set((x, e) => x.setAttr('head', e.target.value)));
  on('pTail', 'change', set((x, e) => x.setAttr('tail', e.target.value)));
  on('pStraight', 'click', set((x) => { const p = x.getAttr('pts'); x.setAttr('pts', [p[0], p[1], (p[0] + p[4]) / 2, (p[1] + p[5]) / 2, p[4], p[5]]); x.setAttr('curved', false); }));
  on('pReverse', 'click', set((x) => { const p = x.getAttr('pts'); x.setAttr('pts', [p[4], p[5], p[2], p[3], p[0], p[1]]); }));
  on('pLabel', 'click', async () => {
    const p = n.getAttr('pts');
    const t = await createNode({ kind: 'text', x: p[2] - 70, y: p[3] - 30, width: 140, align: 'center', text: 'etiqueta', fontSize: 16, fontStyle: 'italic', fill: '#4a5663', labelOf: n.id() });
    rememberLabelOffset(t); layer.batchDraw(); commit(); editText(t);
  });
  on('pOp', 'input', set((x, e) => x.opacity(+e.target.value), true)); on('pOp', 'change', () => commit());
  on('pRot', 'change', set((x, e) => x.rotation(+e.target.value)));
  on('pFront', 'click', set((x) => x.moveToTop()));
  on('pBack', 'click', set((x) => x.zIndex(2)));
  on('pUp', 'click', set((x) => x.moveUp()));
  on('pDown', 'click', set((x) => { if (x.zIndex() > 2) x.moveDown(); }));
  on('pDup', 'click', () => { copySel(); paste(); });
  on('pLock', 'click', () => { const v = !n.getAttr('locked'); sel.forEach((x) => { x.setAttr('locked', v); x.draggable(!v); }); commit(); select(sel); });
  on('pDel', 'click', deleteSel);
  $$('#props [data-al]').forEach((b) => b.addEventListener('click', () => alignSel(b.dataset.al)));
}
/* ---------- tamaño real de las estructuras 3D (opcional) */
const structures = () => items().filter((n) => kind(n) === 'icon' && n.getAttr('realW'));
const pxPerA = (n) => n.width() / n.getAttr('realW');
function realSizeHtml(n) {
  const st = structures();
  if (st.length < 2 || (n && !n.getAttr('realW'))) return '';
  const r = st.map(pxPerA), same = Math.max(...r) / Math.min(...r) < 1.02;
  const info = n ? `Esta estructura mide ~${Math.round(n.getAttr('realW'))} Å de ancho.` : `${st.length} estructuras 3D en la figura.`;
  return `<hr><div class="row"><label>Tamaño de las proteínas</label></div>
    <div class="btns"><button id="pReal" title="Escala todas las estructuras 3D a la misma escala en Å${n ? ', tomando esta como referencia' : ''}">📏 Ajustar a tamaño real</button></div>
    <p class="meta">${info} ${same ? '✓ Ya están a escala real entre sí.' : 'Ahora no están a la misma escala (es opcional).'}</p>`;
}
function fitRealSize(ref) {
  const st = structures();
  if (st.length < 2) { toast('Hace falta más de una estructura 3D en la figura'); return; }
  let k;
  if (ref && ref.getAttr('realW')) k = pxPerA(ref);
  else { const r = st.map(pxPerA).sort((a, b) => a - b); k = r[Math.floor(r.length / 2)]; } // mediana: el tamaño general no cambia
  st.forEach((n) => {
    const w = n.getAttr('realW') * k, h = w * n.height() / n.width();
    n.setAttrs({ width: w, height: h, offsetX: w / 2, offsetY: h / 2 }); // el centro queda en su lugar
    if (n.getAttr('tint')) applyTint(n);
  });
  layer.batchDraw(); tr.forceUpdate(); updateAttached(); commit();
  toast(`Proteínas a escala real (1 nm ≈ ${Math.round(k * 10)} px). Ctrl+Z para deshacer.`);
}
function toHex(c) {
  if (!c) return '#ffffff';
  if (/^#[0-9a-f]{6}$/i.test(c)) return c;
  const ctx = document.createElement('canvas').getContext('2d'); ctx.fillStyle = c; return ctx.fillStyle.startsWith('#') ? ctx.fillStyle : '#000000';
}
function altIcons(n) { // alternativas: objetos completos (o ids de la biblioteca local, formato viejo)
  return (n.getAttr('alts') || []).map((a) => (typeof a === 'string' ? ICON_BY_ID.get(a) : a)).filter(Boolean);
}
const slimIcon = (ic) => ({ id: ic.id, name: ic.name, src: ic.src, author: ic.author, license: ic.license, source: ic.source, aspect: ic.aspect });
async function swapIcon(n, icon) {
  if (!icon) return;
  const img = await loadSvg(icon.src);
  const area = n.width() * n.height(), a = icon.aspect || 1;
  const h = Math.sqrt(area / a), w = h * a;
  const m = n.getAttr('meta') || {};
  const old = { id: n.getAttr('iconId'), src: n.getAttr('src'), name: m.name, author: m.author, license: m.license, source: m.source, aspect: n.width() / n.height() };
  n.setAttrs({ image: img, src: icon.src, iconId: icon.id, width: w, height: h, offsetX: w / 2, offsetY: h / 2, meta: { name: icon.name, author: icon.author, license: icon.license, source: icon.source }, alts: [old, ...altIcons(n).filter((x) => x.id !== icon.id)].map(slimIcon) });
  applyTint(n); layer.batchDraw(); commit(); select([n]);
}
function alignSel(mode) {
  const sel = state.selected.filter((n) => !n.getAttr('locked'));
  const R = sel.map((n) => ({ n, r: n.getClientRect({ relativeTo: layer }) }));
  const minX = Math.min(...R.map((x) => x.r.x)), maxX = Math.max(...R.map((x) => x.r.x + x.r.width));
  const minY = Math.min(...R.map((x) => x.r.y)), maxY = Math.max(...R.map((x) => x.r.y + x.r.height));
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  if (mode === 'hdist' || mode === 'vdist') {
    const horiz = mode === 'hdist';
    R.sort((a, b) => (horiz ? a.r.x + a.r.width / 2 - b.r.x - b.r.width / 2 : a.r.y + a.r.height / 2 - b.r.y - b.r.height / 2));
    const c0 = horiz ? R[0].r.x + R[0].r.width / 2 : R[0].r.y + R[0].r.height / 2;
    const L = R[R.length - 1], c1 = horiz ? L.r.x + L.r.width / 2 : L.r.y + L.r.height / 2;
    R.forEach(({ n, r }, i) => {
      const target = c0 + ((c1 - c0) * i) / (R.length - 1);
      horiz ? moveBy(n, target - (r.x + r.width / 2), 0) : moveBy(n, 0, target - (r.y + r.height / 2));
    });
  } else {
    R.forEach(({ n, r }) => {
      const d = { left: [minX - r.x, 0], right: [maxX - r.x - r.width, 0], hcenter: [cx - r.x - r.width / 2, 0], top: [0, minY - r.y], bottom: [0, maxY - r.y - r.height], vcenter: [0, cy - r.y - r.height / 2] }[mode];
      moveBy(n, d[0], d[1]);
    });
  }
  updateAttached(); tr.forceUpdate(); commit();
}

/* ================================================================= export */
function renderPage({ scale = 3, transparent = false, mime = 'image/png', quality = 0.92 } = {}) {
  const sel = state.selected; select([]);
  grid.visible(false);
  if (transparent) page.visible(false);
  else page.shadowEnabled(false);
  const z = stage.scaleX();
  const r = { x: stage.x(), y: stage.y(), width: state.doc.w * z, height: state.doc.h * z };
  const url = stage.toDataURL({ ...r, pixelRatio: scale / z, mimeType: mime, quality });
  page.visible(true); page.shadowEnabled(true); grid.visible(state.showGrid);
  select(sel);
  return url;
}
function download(url, name) {
  const a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
}
const fileBase = () => (norm($('#projName').value).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'figura');
$('#btnExport').addEventListener('click', (e) => { e.stopPropagation(); $('#exportMenu').classList.toggle('open'); });
document.addEventListener('click', () => $('#exportMenu').classList.remove('open'));
$('#exportMenu').addEventListener('click', (e) => {
  const t = e.target.dataset.export; if (!t) return;
  if (t === 'png3') download(renderPage({ scale: 3 }), fileBase() + '.png');
  if (t === 'png1') download(renderPage({ scale: 1 }), fileBase() + '.png');
  if (t === 'pngT') download(renderPage({ scale: 3, transparent: true }), fileBase() + '-transparente.png');
  if (t === 'jpg') download(renderPage({ scale: 3, mime: 'image/jpeg' }), fileBase() + '.jpg');
  if (t === 'json') download(URL.createObjectURL(new Blob([JSON.stringify({ app: 'BioFig', name: $('#projName').value, doc: serialize() }, null, 1)], { type: 'application/json' })), fileBase() + '.biofig.json');
  if (t === 'import') $('#importFile').click();
});
$('#importFile').addEventListener('change', async (e) => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const data = JSON.parse(await f.text());
    await loadDoc(data.doc || data); $('#projName').value = data.name || f.name.replace(/\.biofig\.json$|\.json$/, '');
    state.projectId = null; setDirty(true); fitPage(); toast('Figura importada');
  } catch (err) { toast('Archivo inválido'); }
  e.target.value = '';
});

/* =============================================================== projects */
async function saveProject() {
  const body = { name: $('#projName').value || 'Figura', doc: serialize(), thumb: renderPage({ scale: 320 / state.doc.w, mime: 'image/jpeg', quality: 0.7 }) };
  const r = await fetch(state.projectId ? `/api/projects/${state.projectId}` : '/api/projects', { method: state.projectId ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) { toast('Error al guardar'); return; }
  state.projectId = (await r.json()).id;
  setDirty(false); toast('Guardado ✓');
  try { localStorage.setItem('biofig:last', state.projectId); } catch (e) { /* sin storage */ }
}
async function openProject(id) {
  const r = await fetch(`/api/projects/${id}`); if (!r.ok) { toast('No se pudo abrir'); return; }
  const d = await r.json();
  await loadDoc(d.doc); state.projectId = d.id; $('#projName').value = d.name; setDirty(false); fitPage(); closeModal();
  try { localStorage.setItem('biofig:last', d.id); } catch (e) { /* */ }
}
async function showOpen() {
  const list = await (await fetch('/api/projects')).json();
  openModal('Abrir figura', list.length ? `<div class="proj-grid">${list.map((p) => `<div class="proj-card" data-id="${esc(p.id)}">${p.thumb ? `<img src="${p.thumb}">` : '<img>'}<div><span><b>${esc(p.name)}</b><small>${new Date(p.updated * 1000).toLocaleString()}</small></span><button class="danger" data-del="${esc(p.id)}" title="Eliminar">🗑</button></div></div>`).join('')}</div>` : '<p>Todavía no hay figuras guardadas.</p>');
  $$('.proj-card').forEach((c) => c.addEventListener('click', async (e) => {
    const del = e.target.closest('[data-del]');
    if (del) {
      e.stopPropagation();
      if (!confirm('¿Eliminar esta figura de forma permanente?')) return;
      await fetch(`/api/projects/${del.dataset.del}`, { method: 'DELETE' });
      if (state.projectId === del.dataset.del) state.projectId = null;
      showOpen(); return;
    }
    if (state.dirty && !confirm('Hay cambios sin guardar. ¿Abrir igual?')) return;
    openProject(c.dataset.id);
  }));
}
$('#btnSave').addEventListener('click', saveProject);
$('#btnOpen').addEventListener('click', showOpen);
$('#btnNew').addEventListener('click', async () => {
  if (state.dirty && !confirm('Hay cambios sin guardar. ¿Empezar una figura nueva?')) return;
  await loadDoc({ w: 1600, h: 1000, items: [] }); state.projectId = null; $('#projName').value = 'Figura sin título'; setDirty(false); fitPage();
});
$('#projName').addEventListener('change', () => setDirty(true));
$('#btnUndo').addEventListener('click', undo);
$('#btnRedo').addEventListener('click', redo);
$('#btnZoomIn').addEventListener('click', () => setZoom(stage.scaleX() * 1.2));
$('#btnZoomOut').addEventListener('click', () => setZoom(stage.scaleX() / 1.2));
$('#btnFit').addEventListener('click', fitPage);
window.addEventListener('beforeunload', (e) => { if (state.dirty) { e.preventDefault(); e.returnValue = ''; } });

/* ================================================================ credits */
function creditsData() {
  const used = new Map();
  items().filter((n) => kind(n) === 'icon').forEach((n) => { const m = n.getAttr('meta') || {}; used.set(n.getAttr('iconId'), m); });
  return [...used.values()];
}
function creditsText(list) {
  const ext = list.filter((m) => m.source !== 'BioFig' && m.source !== 'Imagen propia' && !['CC0', 'Dominio público'].includes(m.license));
  if (!ext.length) return 'Figura creada con BioFig. Todos los iconos son de dominio público (CC0) o propios.';
  const sites = { Bioicons: 'Bioicons (bioicons.com)', PhyloPic: 'PhyloPic (phylopic.org)', 'RCSB PDB': 'estructuras del RCSB PDB (rcsb.org), renderizadas con 3Dmol.js', 'Fluent Emoji': 'Fluent Emoji de Microsoft (MIT)', 'Health Icons': 'Health Icons (healthicons.org)' };
  const bySrc = {};
  ext.forEach((m) => { const s = (bySrc[m.source] ||= {}); (s[m.license] ||= new Set()).add(m.author); });
  return 'Figura creada con BioFig. Iconos de ' + Object.entries(bySrc).map(([src, lics]) =>
    `${sites[src] || src}: ` + Object.entries(lics).map(([lic, a]) => `${[...a].join(', ')} (${lic})`).join('; ')).join('. ') + '.';
}
$('#btnCredits').addEventListener('click', () => {
  const list = creditsData();
  const txt = creditsText(list);
  openModal('Créditos y licencias', `
    <p>Los iconos CC BY requieren atribución cuando publicás la figura. Copiá este texto en la leyenda o en los agradecimientos:</p>
    <textarea class="credits-text" id="credTxt" readonly>${esc(txt)}</textarea>
    <div class="btns" style="margin:8px 0 14px;display:flex;gap:6px"><button class="primary" id="credCopy">Copiar</button><button id="credInsert">Insertar en la figura</button></div>
    <div class="credits-list">${list.length ? list.map((m) => `• <b>${esc(m.name)}</b> — ${esc(m.author)} · ${esc(m.license)} · ${esc(m.source)}`).join('<br>') : 'Todavía no hay iconos en la figura.'}</div>`);
  $('#credCopy').onclick = () => { navigator.clipboard.writeText(txt); toast('Copiado'); };
  $('#credInsert').onclick = async () => {
    const n = await createNode({ kind: 'text', x: 20, y: state.doc.h - 40, text: txt, fontSize: 13, fill: '#6b7785', width: state.doc.w - 40 });
    n.y(state.doc.h - n.height() - 12); layer.batchDraw(); commit(); closeModal(); select([n]);
  };
});

/* ================================================================== modal */
function openModal(title, html, cls = '') {
  $('#modalTitle').textContent = title; $('#modalBody').innerHTML = html;
  $('.modal-box').className = 'modal-box' + (cls ? ' ' + cls : ''); $('#modal').hidden = false;
}
function closeModal() { $('#modal').hidden = true; }
$('#modalClose').addEventListener('click', closeModal);
$('#modal').addEventListener('click', (e) => { if (e.target.id === 'modal') closeModal(); });
let toastT;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('show'), 2200); }

/* ===================================================================== AI */
const EXAMPLES = [
  ['ecologia', 'Red trófica de un bosque mediterráneo: encina, pasto, conejo, perdiz, saltamontes, zorro, águila, serpiente, y hongos y bacterias descomponedores en el suelo.'],
  ['ecologia', 'Ciclo del carbono: atmósfera con CO2, fotosíntesis de plantas, respiración de animales, descomposición en el suelo, intercambio con el océano y combustibles fósiles.'],
  ['ecologia', 'Ciclo del nitrógeno en un ecosistema terrestre: fijación por bacterias en nódulos de leguminosas, nitrificación, desnitrificación, absorción por plantas y herbívoros.'],
  ['ecologia', 'Pirámide de niveles tróficos de un lago: fitoplancton, zooplancton, peces pequeños, peces depredadores y garza, con la eficiencia del 10% entre niveles.'],
  ['molecular', 'Dogma central: ADN en el núcleo se transcribe a ARNm por la ARN polimerasa, el ARNm sale al citoplasma y el ribosoma lo traduce a proteína.'],
  ['molecular', 'Vía de señalización MAPK: factor de crecimiento se une a un receptor tirosina quinasa en la membrana, activa RAS, RAF, MEK y ERK, que entra al núcleo y activa factores de transcripción.'],
  ['molecular', 'Flujo de trabajo de PCR: extracción de ADN, mezcla con cebadores y polimerasa, termociclador, electroforesis en gel y análisis de bandas.'],
  ['molecular', 'Edición génica con CRISPR-Cas9: el ARN guía dirige a Cas9 al ADN diana, corte de doble cadena y reparación por NHEJ o HDR.'],
];
$('#aiExamples').innerHTML = EXAMPLES.map(([g, t], i) => `<button data-i="${i}">${g === 'ecologia' ? '🌿' : '🧬'} ${esc(t.slice(0, 80))}…</button>`).join('');
$('#aiExamples').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return;
  const [g, t] = EXAMPLES[+b.dataset.i];
  $('#aiPrompt').value = t; $('#aiGroup').value = g;
});
const AI_INFO = {
  deepseek: { label: 'DeepSeek', url: 'https://platform.deepseek.com/api_keys', site: 'platform.deepseek.com', ph: 'sk-...', model: 'deepseek-chat', base: 'https://api.deepseek.com' },
  gemini: { label: 'Gemini', url: 'https://aistudio.google.com/apikey', site: 'aistudio.google.com', ph: 'AIza...', model: 'automático (Flash más nuevo)', base: 'https://generativelanguage.googleapis.com' },
};
let aiView = null, aiState = null; // proveedor mostrado en el panel / estado del servidor
async function refreshAIStatus() {
  aiState = await (await fetch('/api/ai/status')).json();
  if (!aiView) aiView = aiState.provider;
  renderAIPanel();
}
function renderAIPanel() {
  const s = aiState, info = AI_INFO[aiView], pv = s.providers[aiView];
  $$('#aiProviders button').forEach((b) => {
    b.classList.toggle('active', b.dataset.p === aiView);
    b.querySelector('i').textContent = s.providers[b.dataset.p].configured ? (b.dataset.p === s.provider && s.configured ? ' ● en uso' : ' ✓') : '';
  });
  const el = $('#aiStatus');
  const inUse = s.configured && s.provider === aiView;
  el.className = 'ai-status ' + (pv.configured ? 'ok' : 'no');
  el.innerHTML = pv.configured
    ? `✓ ${info.label} configurado · modelo <b>${esc(pv.model)}</b>${inUse ? '' : ' · <a href="#" id="aiUse">usar este</a>'} · <a href="#" id="aiChange">cambiar clave</a>`
    : `⚠ Falta la clave de ${info.label}.`;
  $('#aiKeyHelp').innerHTML = `Pegá tu clave de <b>${info.label}</b> (<a href="${info.url}" target="_blank" rel="noopener">${info.site}</a>). Se guarda solo en <code>biofig/.env</code> de esta máquina.`;
  $('#aiKey').placeholder = info.ph; $('#aiModel').placeholder = info.model; $('#aiBase').placeholder = info.base;
  $('#aiKeyForm').hidden = pv.configured;
  $('#aiGo').disabled = !s.configured;
  $('#aiGo').textContent = s.configured ? `Generar figura con ${s.label}` : 'Generar figura';
  const ch = $('#aiChange'); if (ch) ch.onclick = (e) => { e.preventDefault(); $('#aiKeyForm').hidden = false; };
  const use = $('#aiUse'); if (use) use.onclick = (e) => { e.preventDefault(); setProvider(aiView); };
}
async function setProvider(p) {
  const r = await fetch('/api/ai/provider', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider: p }) });
  if (r.ok) { aiState = await r.json(); toast(`Ahora se usa ${AI_INFO[p].label}`); renderAIPanel(); }
}
$('#aiProviders').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b || !aiState) return;
  aiView = b.dataset.p;
  if (aiState.providers[aiView].configured && aiState.provider !== aiView) setProvider(aiView); else renderAIPanel();
});
$('#aiKeyForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = e.submitter || $('#aiKeyForm button[type=submit]');
  btn.disabled = true; btn.textContent = 'Verificando…';
  try {
    const r = await fetch('/api/ai/key', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider: aiView, api_key: $('#aiKey').value, model: $('#aiModel').value, base_url: $('#aiBase').value }) });
    const data = await r.json();
    if (!r.ok) { toast(data.detail || 'No se pudo guardar la clave'); return; }
    $('#aiKey').value = '';
    aiState = data; renderAIPanel();
    toast(data.note || `Clave de ${AI_INFO[aiView].label} guardada ✓`);
  } finally { btn.disabled = false; btn.textContent = 'Guardar clave'; }
});
$('#aiGo').addEventListener('click', async () => {
  const prompt = $('#aiPrompt').value.trim();
  if (!prompt) { toast('Escribí una descripción'); return; }
  const msg = $('#aiMsg'), btn = $('#aiGo');
  msg.className = 'ai-msg'; msg.innerHTML = `<span class="spinner"></span>${esc(aiState?.label || 'La IA')} está diseñando la figura… (puede tardar 20–60 s)`;
  btn.disabled = true;
  try {
    const r = await fetch('/api/ai/figure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt, group: $('#aiGroup').value || null }) });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Error');
    const stats = await buildFromSpec(data, $('#aiReplace').checked);
    msg.textContent = `Listo: ${stats.icons} iconos, ${stats.connectors} conectores${stats.missing ? `, ${stats.missing} sin icono (marcados con línea punteada)` : ''}. Hacé clic en un icono para ver alternativas.`;
  } catch (err) {
    msg.className = 'ai-msg err'; msg.textContent = '✗ ' + err.message;
  } finally { btn.disabled = false; }
});

async function buildFromSpec(spec, replace) {
  if (replace) { select([]); items().forEach((n) => n.destroy()); }
  const cw = spec.canvas?.w || 1400, ch = spec.canvas?.h || 900;
  const f = Math.min(state.doc.w / cw, state.doc.h / ch);
  const ox = (state.doc.w - cw * f) / 2, oy = (state.doc.h - ch * f) / 2;
  const X = (v) => ox + (+v || 0) * f, Y = (v) => oy + (+v || 0) * f;
  const boxes = {}; // id -> {cx, cy, w, h}
  const nodeOf = {}; // id del plan -> id del icono creado
  const stats = { icons: 0, connectors: 0, missing: 0 };
  const created = [];
  const els = spec.elements || [];
  const ordered = [...els.filter((e) => e.kind === 'region'), ...els.filter((e) => e.kind !== 'region')];
  for (const el of ordered) {
    if (el.kind === 'region') {
      const x = X(el.x), y = Y(el.y), w = (+el.w || 300) * f, h = (+el.h || 200) * f;
      const fill = /^#[0-9a-f]{6}$/i.test(el.fill || '') ? el.fill : '#f3f6fa';
      const stroke = shade(fill, -0.35);
      const n = await createNode(el.shape === 'ellipse'
        ? { kind: 'ellipse', x: x + w / 2, y: y + h / 2, radiusX: w / 2, radiusY: h / 2, fill, stroke, strokeWidth: 3 }
        : { kind: 'rect', x, y, width: w, height: h, fill, stroke, strokeWidth: 2, cornerRadius: 18 });
      created.push(n);
      boxes[el.id] = { cx: x + w / 2, cy: y + h / 2, w, h };
      if (el.label) created.push(await createNode({ kind: 'text', x: x + 14, y: y + 10, text: el.label, fontSize: Math.max(14, 20 * f), fontStyle: 'bold', fill: shade(fill, -0.6), halo: true }));
    } else if (el.kind === 'icon') {
      const cx = X(el.x), cy = Y(el.y);
      const ic = el.icon;
      let w = Math.max(50, Math.min(260, +el.w || 130)) * f, h = w;
      if (ic) {
        const a = ic.aspect || 1;
        if (a < 1) { h = w; w = h * a; } else h = w / a;
        const n = await createNode({ kind: 'icon', src: ic.src, iconId: ic.id, meta: { name: ic.name, author: ic.author, license: ic.license, source: ic.source }, x: cx, y: cy, width: w, height: h, alts: (el.alternatives || []).map(slimIcon) });
        if (n) { created.push(n); stats.icons++; nodeOf[el.id] = n.id(); }
      } else {
        stats.missing++;
        created.push(await createNode({ kind: 'rect', x: cx - w / 2, y: cy - h / 2, width: w, height: h, fill: '#fafafa', stroke: '#b0b8c2', strokeWidth: 2, dashed: true, cornerRadius: 10 }));
        created.push(await createNode({ kind: 'text', x: cx - w / 2, y: cy - 10, width: w, align: 'center', text: '? ' + (el.query || ''), fontSize: 14, fill: '#8a96a3' }));
      }
      boxes[el.id] = { cx, cy, w: w + 16, h: h + 16 };
      if (el.label) {
        const lw = Math.max(170, w + 40);
        created.push(await createNode({ kind: 'text', x: cx - lw / 2, y: cy + h / 2 + 6, width: lw, align: 'center', text: el.label, fontSize: Math.max(13, 18 * f), fill: '#1f2933', anchorTo: nodeOf[el.id] || null, halo: true }));
      }
    } else if (el.kind === 'text') {
      const size = Math.max(12, (+el.size || 22) * f);
      const n = await createNode({ kind: 'text', x: X(el.x), y: Y(el.y), text: el.text || '', fontSize: size, fontStyle: size >= 26 * f ? 'bold' : 'normal', fill: size >= 26 * f ? '#1d3f72' : '#1f2933' });
      created.push(n);
      boxes[el.id] = { cx: n.x() + n.width() / 2, cy: n.y() + n.height() / 2, w: n.width(), h: n.height() };
    }
  }
  const kinds = { arrow: { head: 'arrow' }, inhibit: { head: 'tbar' }, dashed: { head: 'arrow', dashed: true }, double: { head: 'arrow', tail: 'arrow' } };
  for (const c of spec.connectors || []) {
    const A = boxes[c.from], B = boxes[c.to];
    if (!A || !B) continue;
    const p1 = clipToBox(A, B), p2 = clipToBox(B, A);
    const n = await createNode({ kind: 'connector', pts: [p1.x, p1.y, (p1.x + p2.x) / 2, (p1.y + p2.y) / 2, p2.x, p2.y], strokeWidth: 3, stroke: c.kind === 'inhibit' ? '#c0392b' : '#34495e', from: nodeOf[c.from] || null, to: nodeOf[c.to] || null, ...(kinds[c.kind] || kinds.arrow) });
    created.push(n); stats.connectors++;
    if (c.label) {
      const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2, ang = Math.atan2(p2.y - p1.y, p2.x - p1.x);
      const t = await createNode({ kind: 'text', x: 0, y: 0, text: c.label, fontSize: Math.max(12, 15 * f), fontStyle: 'italic', fill: '#4a5663', align: 'center', width: 150, halo: true });
      t.position({ x: mx - 75 - 16 * Math.sin(ang), y: my - t.height() / 2 + 16 * Math.cos(ang) - (Math.abs(Math.cos(ang)) > 0.7 ? 12 : 0) });
      t.setAttr('labelOf', n.id()); rememberLabelOffset(t);
      created.push(t);
    }
  }
  // conectores debajo de los iconos, encima de las regiones
  const regionIdx = created.filter((n) => n && (kind(n) === 'rect' || kind(n) === 'ellipse') && !n.dash().length).map((n) => n.zIndex());
  const above = regionIdx.length ? Math.max(...regionIdx) : 1;
  created.filter((n) => n && kind(n) === 'connector').forEach((n) => n.zIndex(above + 1));
  layer.batchDraw(); commit(); fitPage();
  if (spec.title && $('#projName').value === 'Figura sin título') $('#projName').value = spec.title;
  return stats;
}
function clipToBox(A, B) {
  const dx = B.cx - A.cx, dy = B.cy - A.cy;
  if (!dx && !dy) return { x: A.cx, y: A.cy };
  const t = Math.min(dx ? (A.w / 2) / Math.abs(dx) : Infinity, dy ? (A.h / 2) / Math.abs(dy) : Infinity, 1);
  return { x: A.cx + dx * t, y: A.cy + dy * t };
}
function shade(hex, amt) {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const out = c.map((v) => Math.round(amt < 0 ? v * (1 + amt) : v + (255 - v) * amt));
  return '#' + out.map((v) => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('');
}

/* =================================================================== init */
(async function init() {
  fitPage();
  renderProps();
  await initLibrary();
  let last = null;
  try { last = localStorage.getItem('biofig:last'); } catch (e) { /* */ }
  if (last) { const r = await fetch(`/api/projects/${last}`); if (r.ok) await openProject(last); }
  if (!state.history.length) state.history = [JSON.stringify(serialize())];
  refreshAIStatus();
})();
