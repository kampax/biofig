/* BioFig — visor 3D de estructuras del PDB (3Dmol.js): rotar, colorear e insertar en la figura */
'use strict';

const PDB_EXAMPLES = [
  ['1JFF', 'Tubulina αβ'], ['6A69', 'PMCA1'], ['4F5S', 'BSA'], ['1HHO', 'Hemoglobina'],
  ['1EMA', 'GFP'], ['1BNA', 'ADN B'], ['1RUZ', 'Rubisco'], ['2RH1', 'Receptor β2'],
];
const PDB_PRESETS = { // colores como en las figuras de ejemplo
  '1JFF': { chains: ['A', 'B'], color: 'chain', colors: { A: '#e2582f', B: '#2a9d8f' } },
  '6A69': { chains: ['A'], color: 'chain', colors: { A: '#2a9d8f' }, nterm: ['#e4572e', 0.07] },
  '4F5S': { chains: ['A'], color: 'spectrum' },
};
const CHAIN_COLORS = ['#e2582f', '#2a9d8f', '#3a6ea5', '#9b5de5', '#e9c46a', '#6a994e', '#d62f6b', '#8d6e63'];
const RAINBOW3D = ['#d62828', '#f77f00', '#fcbf49', '#8ac926', '#2a9d8f', '#1982c4', '#4361ee'];
const SS_COLORS = { h: '#e63946', s: '#f4c430', c: '#9aa5b1' };

let p3 = null; // estado del visor abierto

const mix3 = (c1, c2, t) => '#' + [1, 3, 5].map((i) => Math.round(parseInt(c1.slice(i, i + 2), 16) * (1 - t) + parseInt(c2.slice(i, i + 2), 16) * t).toString(16).padStart(2, '0')).join('');
const rainbow3 = (f) => { const x = Math.min(Math.max(f, 0), 0.9999) * (RAINBOW3D.length - 1), i = Math.floor(x); return mix3(RAINBOW3D[i], RAINBOW3D[i + 1], x - i); };

async function ensure3Dmol() {
  if (window.$3Dmol) return;
  await new Promise((res, rej) => { const s = document.createElement('script'); s.src = '/static/vendor/3Dmol-min.js'; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
}

/* ---------- orientación automática: eje principal en horizontal, cara más ancha hacia el observador */
function jacobiEigen(A) {
  const a = A.map((r) => [...r]), v = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let sweep = 0; sweep < 50; sweep++) {
    let off = 0;
    for (let p = 0; p < 3; p++) for (let q = p + 1; q < 3; q++) off += a[p][q] ** 2;
    if (off < 1e-12) break;
    for (let p = 0; p < 3; p++) for (let q = p + 1; q < 3; q++) {
      if (Math.abs(a[p][q]) < 1e-15) continue;
      const th = (a[q][q] - a[p][p]) / (2 * a[p][q]);
      const t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1)), c = 1 / Math.sqrt(t * t + 1), s = t * c;
      for (let k = 0; k < 3; k++) { const akp = a[k][p], akq = a[k][q]; a[k][p] = c * akp - s * akq; a[k][q] = s * akp + c * akq; }
      for (let k = 0; k < 3; k++) { const apk = a[p][k], aqk = a[q][k]; a[p][k] = c * apk - s * aqk; a[q][k] = s * apk + c * aqk; }
      for (let k = 0; k < 3; k++) { const vkp = v[k][p], vkq = v[k][q]; v[k][p] = c * vkp - s * vkq; v[k][q] = s * vkp + c * vkq; }
    }
  }
  return [0, 1, 2].map((i) => ({ val: a[i][i], vec: [v[0][i], v[1][i], v[2][i]] })).sort((x, y) => y.val - x.val);
}
function orientPdbText(txt, chains) {
  const lines = txt.split(/\r?\n/);
  const isAtom = (l) => l.startsWith('ATOM') || l.startsWith('HETATM');
  const ca = lines.filter((l) => l.startsWith('ATOM') && l.slice(12, 16).trim() === 'CA' && (!chains || chains.includes(l[21])))
    .map((l) => ({ p: [+l.slice(30, 38), +l.slice(38, 46), +l.slice(46, 54)], ch: l[21] }));
  if (ca.length < 3) return txt;
  const c = [0, 1, 2].map((k) => ca.reduce((s, a) => s + a.p[k], 0) / ca.length);
  const C = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  ca.forEach(({ p }) => { for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i][j] += (p[i] - c[i]) * (p[j] - c[j]); });
  const R = jacobiEigen(C).map((e) => e.vec);
  const det = R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1]) - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0]) + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]);
  if (det < 0) R[2] = R[2].map((x) => -x);
  const tf = (p) => R.map((r) => r[0] * (p[0] - c[0]) + r[1] * (p[1] - c[1]) + r[2] * (p[2] - c[2]));
  // extremo N (o primera cadena) a la izquierda
  const xs = ca.map((a) => tf(a.p)[0]), n10 = Math.max(1, Math.floor(ca.length / 10));
  const chs = [...new Set(ca.map((a) => a.ch))];
  let flip;
  if (chs.length > 1) {
    const mean = (ch) => { const v = ca.map((a, i) => (a.ch === ch ? xs[i] : null)).filter((x) => x !== null); return v.reduce((s, x) => s + x, 0) / v.length; };
    flip = mean(chs[0]) > mean(chs[1]);
  } else {
    const avg = (arr) => arr.reduce((s, x) => s + x, 0) / arr.length;
    flip = avg(xs.slice(0, n10)) > avg(xs.slice(-n10));
  }
  return lines.map((l) => {
    if (!isAtom(l) || l.length < 54) return l;
    let [x, y, z] = tf([+l.slice(30, 38), +l.slice(38, 46), +l.slice(46, 54)]);
    if (flip) { x = -x; z = -z; }
    const f = (v) => v.toFixed(3).padStart(8);
    return l.slice(0, 30) + f(x) + f(y) + f(z) + l.slice(54);
  }).join('\n');
}
function pdbInfo(txt) { // nombre de cada cadena (COMPND) y título
  const names = {}; let mol = null;
  txt.split(/\r?\n/).filter((l) => l.startsWith('COMPND')).forEach((l) => {
    const s = l.slice(10).trim();
    const m1 = s.match(/MOLECULE:\s*(.+?);?$/); if (m1) mol = m1[1].replace(/;$/, '').trim();
    const m2 = s.match(/CHAIN:\s*(.+?);?$/); if (m2 && mol) m2[1].split(',').forEach((c) => (names[c.trim()] = mol));
  });
  const title = txt.split(/\r?\n/).filter((l) => l.startsWith('TITLE')).map((l) => l.slice(10).trim()).join(' ').replace(/\s+/g, ' ');
  return { names, title };
}

/* ---------- modal */
async function openPdbModal(node = null) {
  const cfg = node ? (node.getAttr('pdb') || null) : null;
  const presetId = node && !cfg && /^pdb:/.test(node.getAttr('iconId') || '') ? node.getAttr('iconId').slice(4) : null;
  openModal('Estructura 3D del Protein Data Bank', `
    <div class="p3">
      <div class="p3-side">
        <div class="p3-row"><input id="p3Id" maxlength="4" placeholder="Código PDB (ej. 1JFF)" autocomplete="off"><button id="p3Load" class="primary">Cargar</button></div>
        <div class="p3-ex">${PDB_EXAMPLES.map(([id, n]) => `<button data-id="${id}" title="${esc(n)}">${id} · ${esc(n)}</button>`).join('')}</div>
        <div id="p3Title" class="meta" hidden></div>
        <div id="p3Opts" hidden>
          <label>Representación <select id="p3Rep"><option value="cartoon">Cintas</option><option value="both">Cintas + superficie</option><option value="surface">Superficie</option><option value="sphere">Esferas</option><option value="stick">Varillas</option></select></label>
          <label>Color <select id="p3Color"><option value="chain">Por cadena</option><option value="spectrum">Arcoíris N→C</option><option value="ss">Estructura secundaria</option></select></label>
          <div id="p3Chains" class="p3-chains"></div>
          <div class="p3-checks"><label><input type="checkbox" id="p3Het"> Ligandos</label><label><input type="checkbox" id="p3Outline" checked> Contorno</label></div>
          <div class="p3-rot">
            <span>Rotar</span>
            <button data-rot="x:-15">X−</button><button data-rot="x:15">X+</button>
            <button data-rot="y:-15">Y−</button><button data-rot="y:15">Y+</button>
            <button data-rot="z:-15">Z−</button><button data-rot="z:15">Z+</button>
          </div>
          <div class="p3-row"><button id="p3Orient" title="Eje principal en horizontal">Orientar automático</button><button id="p3Center">Centrar</button></div>
          <button id="p3Insert" class="primary wide">${node ? 'Actualizar en la figura' : 'Insertar en la figura'}</button>
        </div>
        <p class="hint">Arrastrá para rotar · rueda para zoom · botón derecho o Ctrl+arrastrar para desplazar.</p>
      </div>
      <div class="p3-view-wrap"><div id="p3View"></div><div id="p3Msg" class="p3-msg">Elegí un ejemplo o escribí un código PDB.</div></div>
    </div>`, 'wide');
  await ensure3Dmol();
  p3 = { node, viewer: $3Dmol.createViewer($('#p3View'), { backgroundColor: 'white', backgroundAlpha: 0, antialias: true }), cfg };
  $('#p3Load').onclick = () => loadPdb($('#p3Id').value.trim());
  $('#p3Id').onkeydown = (e) => { e.stopPropagation(); if (e.key === 'Enter') loadPdb($('#p3Id').value.trim()); };
  $$('.p3-ex button').forEach((b) => (b.onclick = () => { $('#p3Id').value = b.dataset.id; loadPdb(b.dataset.id); }));
  ['p3Rep', 'p3Color', 'p3Het', 'p3Outline'].forEach((id) => ($('#' + id).onchange = applyP3Style));
  $$('.p3-rot button').forEach((b) => (b.onclick = () => { const [ax, deg] = b.dataset.rot.split(':'); p3.viewer.rotate(+deg, ax); p3.viewer.render(); }));
  $('#p3Center').onclick = () => { p3Center(); p3.viewer.render(); };
  $('#p3Orient').onclick = () => loadPdb(p3.id, { keepStyle: true });
  $('#p3Insert').onclick = insertP3;
  const startId = cfg?.id || presetId;
  if (startId) { $('#p3Id').value = startId; loadPdb(startId, { cfg }); }
}

async function loadPdb(id, { cfg = null, keepStyle = false } = {}) {
  id = (id || '').toUpperCase();
  if (!/^[0-9][A-Z0-9]{3}$/.test(id)) { toast('Código PDB inválido (4 caracteres, ej. 1JFF)'); return; }
  const msg = $('#p3Msg'); msg.hidden = false; msg.innerHTML = `<span class="spinner"></span>Descargando ${id} del PDB…`;
  const r = await fetch('/api/pdb/' + id);
  if (!r.ok) {
    const detail = (await r.json().catch(() => ({}))).detail || 'No se pudo cargar';
    const stale = r.status === 404 && detail === 'Not Found' && !(await fetch('/api/version').then((x) => x.ok).catch(() => false));
    msg.textContent = stale
      ? 'El servidor de BioFig está desactualizado: cerrá la ventana de iniciar.bat y abrilo de nuevo.'
      : detail;
    return;
  }
  const fmt = r.headers.get('X-Format') || 'pdb';
  const raw = await r.text();
  const prev = keepStyle ? p3State() : null;
  const info = fmt === 'pdb' ? pdbInfo(raw) : { names: {}, title: '' };
  const v = p3.viewer; v.clear(); v.removeAllSurfaces();
  // cadenas de proteína/ácido nucleico presentes
  const tmp = v.addModel(raw, fmt);
  const chains = [...new Set(tmp.selectedAtoms({ hetflag: false }).map((a) => a.chain))];
  v.clear();
  const preset = PDB_PRESETS[id] || {};
  const use = cfg?.chains || prev?.chains || preset.chains || chains.slice(0, chains.length > 8 ? 2 : chains.length);
  const text = fmt === 'pdb' ? orientPdbText(raw, use) : raw;
  p3.model = v.addModel(text, fmt);
  p3.id = id; p3.fmt = fmt; p3.chains = chains; p3.info = info;
  p3.colors = cfg?.colors || prev?.colors || Object.fromEntries(chains.map((c, i) => [c, (preset.colors || {})[c] || CHAIN_COLORS[i % CHAIN_COLORS.length]]));
  p3.nterm = cfg ? cfg.nterm || null : (preset.nterm || null);
  $('#p3Title').hidden = false;
  $('#p3Title').innerHTML = `<b>${id}</b>${info.title ? ' — ' + esc(info.title.toLowerCase()) : ''}`;
  $('#p3Chains').innerHTML = '<span class="lbl">Cadenas</span>' + chains.map((c) => `
    <label class="p3-chain"><input type="checkbox" data-ch="${c}" ${use.includes(c) ? 'checked' : ''}>
    <input type="color" data-col="${c}" value="${p3.colors[c]}"> <b>${c}</b> <small>${esc((info.names[c] || '').toLowerCase())}</small></label>`).join('');
  $$('#p3Chains input').forEach((el) => (el.onchange = () => {
    if (el.dataset.col) { p3.colors[el.dataset.col] = el.value; p3.nterm = null; }
    applyP3Style();
  }));
  const st = cfg || prev || {};
  $('#p3Rep').value = st.rep || 'cartoon';
  $('#p3Color').value = st.color || preset.color || 'chain';
  $('#p3Het').checked = !!st.het;
  $('#p3Outline').checked = st.outline !== false;
  $('#p3Opts').hidden = false;
  applyP3Style();
  if (cfg?.view) { p3Center(); v.setView(cfg.view); } // reabrir con la orientación guardada
  else p3Center({ resetRotation: true });            // orientación automática: eje principal horizontal
  v.render();
  msg.hidden = true;
}

/* Centrar: anula el desplazamiento de la cámara (3Dmol lo guarda en lookingAt y zoomTo no lo restablece)
   y reencuadra lo visible. Con resetRotation también vuelve a la orientación de las coordenadas. */
function p3Center({ resetRotation = false } = {}) {
  const v = p3.viewer;
  if (resetRotation) { const vw = v.getView(); vw[4] = 0; vw[5] = 0; vw[6] = 0; vw[7] = 1; v.setView(vw); }
  if (v.lookingAt && v.camera) { v.lookingAt.x = 0; v.lookingAt.y = 0; v.lookingAt.z = 0; v.camera.lookAt(v.lookingAt); }
  v.zoomTo(p3Selected().length ? p3Sel() : {});
}

const p3Selected = () => $$('#p3Chains input[data-ch]').filter((x) => x.checked).map((x) => x.dataset.ch);
const p3Sel = () => ({ chain: p3Selected(), hetflag: false });
function p3State() {
  return { id: p3.id, chains: p3Selected(), rep: $('#p3Rep').value, color: $('#p3Color').value, colors: { ...p3.colors },
    nterm: p3.nterm, het: $('#p3Het').checked, outline: $('#p3Outline').checked, view: p3.viewer.getView() };
}
function applyP3Style() {
  const v = p3.viewer, mode = $('#p3Color').value, rep = $('#p3Rep').value, chains = p3Selected();
  const res = p3.model.selectedAtoms({ hetflag: false }).map((a) => a.resi);
  const ranges = {};
  p3.model.selectedAtoms({ hetflag: false }).forEach((a) => { const r = (ranges[a.chain] ||= [Infinity, -Infinity]); r[0] = Math.min(r[0], a.resi); r[1] = Math.max(r[1], a.resi); });
  const colorOf = (a) => {
    const rg = ranges[a.chain] || [Math.min(...res), Math.max(...res)];
    const f = (a.resi - rg[0]) / Math.max(1, rg[1] - rg[0]);
    if (mode === 'spectrum') return a.ss === 'h' ? rainbow3(f) : mix3(rainbow3(f), '#ffffff', 0.25);
    if (mode === 'ss') return SS_COLORS[a.ss] || SS_COLORS.c;
    if (p3.nterm && f < p3.nterm[1]) return a.ss === 'h' ? p3.nterm[0] : mix3(p3.nterm[0], '#ffffff', 0.3);
    const base = p3.colors[a.chain] || '#999999';
    return a.ss === 'h' ? base : mix3(base, '#ffffff', 0.35);
  };
  v.setStyle({}, {});
  v.removeAllSurfaces();
  if (!chains.length) { v.render(); return; }
  const sel = { chain: chains, hetflag: false };
  if (rep === 'cartoon' || rep === 'both') v.setStyle(sel, { cartoon: { colorfunc: colorOf, thickness: 0.6, arrows: true } });
  if (rep === 'sphere') v.setStyle(sel, { sphere: { colorfunc: colorOf } });
  if (rep === 'stick') v.setStyle(sel, { stick: { colorfunc: colorOf, radius: 0.2 } });
  if (rep === 'surface' || rep === 'both') {
    chains.forEach((c) => {
      const rg = ranges[c] || [0, 1];
      const style = mode === 'spectrum' ? { colorscheme: { prop: 'resi', gradient: 'roygb', min: rg[0], max: rg[1] } }
        : mode === 'ss' ? { colorscheme: 'ssJmol' } : { color: p3.colors[c] };
      const s = { chain: c, hetflag: false };
      // la superficie se calcula en segundo plano: volver a dibujar cuando termina
      v.addSurface($3Dmol.SurfaceType.VDW, { ...style, opacity: rep === 'both' ? 0.75 : 1 }, s, s, false, () => v.render());
    });
  }
  if ($('#p3Het').checked) v.setStyle({ chain: chains, hetflag: true, not: { resn: ['HOH', 'WAT', 'DOD'] } }, { stick: { colorscheme: 'grayCarbon', radius: 0.25 } });
  // el contorno no es compatible con superficies (las deja invisibles): solo para cintas, esferas y varillas
  const hasSurface = rep === 'surface' || rep === 'both';
  $('#p3Outline').disabled = hasSurface;
  v.setViewStyle($('#p3Outline').checked && !hasSurface ? { style: 'outline', color: 'black', width: 0.03 } : { style: 'outline', color: 'black', width: 0 });
  v.render();
}

/* captura en alta resolución con fondo transparente, recortada al contenido */
async function captureP3(scale = 3) {
  const div = $('#p3View'), v = p3.viewer;
  const w = div.clientWidth, h = div.clientHeight;
  Object.assign(div.style, { width: w * scale + 'px', height: h * scale + 'px', transform: `scale(${1 / scale})`, transformOrigin: 'top left' });
  v.resize(); v.render();
  await new Promise((r) => setTimeout(r, 80));
  const url = v.pngURI();
  Object.assign(div.style, { width: '', height: '', transform: '' });
  v.resize(); v.render();
  const im = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = url; });
  const cv = document.createElement('canvas'); cv.width = im.width; cv.height = im.height;
  const ctx = cv.getContext('2d'); ctx.drawImage(im, 0, 0);
  const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
  let x0 = cv.width, y0 = cv.height, x1 = -1, y1 = -1;
  for (let y = 0; y < cv.height; y++) for (let x = 0; x < cv.width; x++) {
    if (d[(y * cv.width + x) * 4 + 3] > 10) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 < 0) throw new Error('No hay nada visible para capturar');
  const pad = 8; x0 = Math.max(0, x0 - pad); y0 = Math.max(0, y0 - pad); x1 = Math.min(cv.width - 1, x1 + pad); y1 = Math.min(cv.height - 1, y1 + pad);
  const out = document.createElement('canvas'); out.width = x1 - x0 + 1; out.height = y1 - y0 + 1;
  out.getContext('2d').drawImage(cv, x0, y0, out.width, out.height, 0, 0, out.width, out.height);
  return { data: out.toDataURL('image/png'), w: out.width, h: out.height };
}

/* ancho real (Å) de lo que se ve, con la rotación actual del visor */
function p3RealWidth(shotW, pad = 8) {
  const v = p3.viewer.getView(), [qx, qy, qz, qw] = v.slice(4, 8);
  let atoms = p3.model.selectedAtoms({ chain: p3Selected(), hetflag: false }).filter((a) => a.atom === 'CA' || a.atom === 'P');
  if (atoms.length < 3) atoms = p3.model.selectedAtoms({ chain: p3Selected() });
  const c = ['x', 'y', 'z'].map((k) => atoms.reduce((s, a) => s + a[k], 0) / atoms.length);
  const xs = atoms.map((a) => { // rotar (a - c) por el cuaternión de la vista
    const p = [a.x - c[0], a.y - c[1], a.z - c[2]];
    const t = [2 * (qy * p[2] - qz * p[1]), 2 * (qz * p[0] - qx * p[2]), 2 * (qx * p[1] - qy * p[0])];
    return p[0] + qw * t[0] + (qy * t[2] - qz * t[1]);
  });
  const rep = $('#p3Rep').value, extra = rep === 'surface' || rep === 'both' || rep === 'sphere' ? 6 : 3;
  return (Math.max(...xs) - Math.min(...xs) + extra) * shotW / Math.max(1, shotW - 2 * pad);
}

async function insertP3() {
  const btn = $('#p3Insert'); btn.disabled = true; const label = btn.textContent; btn.textContent = 'Renderizando…';
  try {
    const shot = await captureP3();
    const r = await fetch('/api/pdb/render', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: p3.id, data: shot.data }) });
    if (!r.ok) throw new Error('No se pudo guardar el render');
    const { src } = await r.json();
    const chainNames = p3Selected().map((c) => p3.info.names[c]).filter(Boolean);
    const name = `${chainNames.length ? [...new Set(chainNames)].join(' / ').toLowerCase() + ' ' : ''}(PDB ${p3.id})`;
    const meta = { name: name.charAt(0).toUpperCase() + name.slice(1), author: `PDB ${p3.id}`, license: 'Dominio público (PDB)', source: 'RCSB PDB' };
    const cfg = p3State();
    const aspect = shot.w / shot.h;
    const realW = Math.round(p3RealWidth(shot.w) * 10) / 10;
    const node = p3.node;
    if (node) { // reemplazar en el mismo lugar, conservando el ancho
      const img = await loadSvg(src);
      const w = node.width(), h = w / aspect;
      node.setAttrs({ image: img, src, iconId: 'pdb:' + p3.id, width: w, height: h, offsetX: w / 2, offsetY: h / 2, meta, pdb: cfg, alts: [], realW });
      applyTint(node); layer.batchDraw(); updateAttached(); commit(); select([node]);
    } else {
      const n = await addIcon({ id: 'pdb:' + p3.id, name: meta.name, src, author: meta.author, license: meta.license, source: meta.source, aspect }, null, 320);
      if (n) { n.setAttr('pdb', cfg); n.setAttr('realW', realW); commit(); renderProps(); }
    }
    closeModal(); toast(node ? 'Estructura actualizada' : 'Estructura insertada');
  } catch (e) {
    toast('✗ ' + e.message);
  } finally { btn.disabled = false; btn.textContent = label; }
}

$('#btnPdb').addEventListener('click', () => openPdbModal());
