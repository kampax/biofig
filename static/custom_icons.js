/* BioFig — iconos personalizados (imagen o SVG) con opción de quitar el fondo (rembg, local) */
'use strict';

let ci = null; // estado de la ventana: { name, kind, original, result }

const fileToDataURL = (file) => new Promise((res, rej) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file); });
const imgSize = (src) => new Promise((res) => { const im = new Image(); im.onload = () => res([im.naturalWidth, im.naturalHeight]); im.onerror = () => res([1, 1]); im.src = src; });

async function openCustomIconModal({ data = null, name = '', node = null } = {}) {
  const st = await fetch('/api/remove-bg/status').then((r) => r.json()).catch(() => ({ installed: false, models: {} }));
  const firstReady = Object.entries(st.models || {}).find(([, m]) => m.ready)?.[0] || 'alta';
  const opts = Object.entries(st.models || {}).map(([k, m]) =>
    `<option value="${k}" ${k === firstReady ? 'selected' : ''}>${esc(m.label)}${m.ready ? ' ✓' : ` — descarga ~${m.sizeMB} MB la 1.ª vez`}</option>`).join('');
  openModal(node ? 'Quitar fondo' : 'Icono personalizado', `
    <div class="ci">
      <div class="ci-side">
        <label class="ci-drop" id="ciDrop">
          <input type="file" id="ciFile" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml" hidden>
          <b>Elegí o arrastrá una imagen</b><br><small>PNG, JPG, WebP, GIF o SVG · también podés pegar con Ctrl+V</small>
        </label>
        <label class="lbl" for="ciName">Nombre</label>
        <input id="ciName" placeholder="Ej: Mi equipo de muestreo" value="${esc(name)}">
        <div class="ci-bg ${st.installed ? '' : 'off'}">
          <div class="row"><b>Quitar el fondo</b><small class="muted">rembg · local</small></div>
          ${st.installed ? `
            <label>Calidad <select id="ciQuality">${opts}</select></label>
            <label class="chk"><input type="checkbox" id="ciSoft" checked> Suavizar bordes</label>
            <button id="ciRemove" class="wide" disabled>✂ Quitar fondo</button>
            <button id="ciUndo" class="wide" hidden>↶ Volver al original</button>`
    : '<p class="muted">rembg no está instalado. En la carpeta biofig ejecutá:<br><code>.venv\\Scripts\\python -m pip install "rembg[cpu]"</code></p>'}
        </div>
        <div id="ciMsg" class="ai-msg"></div>
        ${node
    ? '<button id="ciApply" class="primary wide" disabled>Aplicar a la imagen de la figura</button>'
    : `<button id="ciSaveInsert" class="primary wide" disabled>Guardar en Mis iconos e insertar</button>
       <button id="ciSave" class="wide" disabled>Solo guardar en Mis iconos</button>`}
      </div>
      <div class="ci-prev">
        <div><span>Original</span><div class="ci-box" id="ciOrig"><em>Sin imagen</em></div></div>
        <div><span>Resultado</span><div class="ci-box checker" id="ciRes"><em>—</em></div></div>
      </div>
    </div>`, 'wide');
  ci = { name, kind: null, original: null, result: null, node };
  const drop = $('#ciDrop');
  $('#ciFile').onchange = (e) => e.target.files[0] && loadCustomFile(e.target.files[0]);
  drop.ondragover = (e) => { e.preventDefault(); drop.classList.add('over'); };
  drop.ondragleave = () => drop.classList.remove('over');
  drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove('over'); const f = e.dataTransfer.files[0]; if (f) loadCustomFile(f); };
  $('#ciName').onkeydown = (e) => e.stopPropagation();
  if ($('#ciRemove')) $('#ciRemove').onclick = runRemoveBg;
  if ($('#ciUndo')) $('#ciUndo').onclick = () => { ci.result = null; showCustomPreview(); };
  if ($('#ciSaveInsert')) $('#ciSaveInsert').onclick = () => saveCustomIcon(true);
  if ($('#ciSave')) $('#ciSave').onclick = () => saveCustomIcon(false);
  if ($('#ciApply')) $('#ciApply').onclick = applyToNode;
  if (data) setCustomData(data, name);
}

async function loadCustomFile(file) {
  if (!/^image\/(png|jpe?g|webp|gif|svg\+xml)$/i.test(file.type)) { toast('Formato no soportado'); return; }
  setCustomData(await fileToDataURL(file), file.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' '));
}

function setCustomData(data, name) {
  ci.original = data; ci.result = null;
  ci.kind = data.startsWith('data:image/svg') ? 'svg' : 'raster';
  if (!$('#ciName').value && name) $('#ciName').value = name;
  showCustomPreview();
}

function showCustomPreview() {
  $('#ciOrig').innerHTML = ci.original ? `<img src="${ci.original}" alt="">` : '<em>Sin imagen</em>';
  $('#ciRes').innerHTML = ci.result ? `<img src="${ci.result}" alt="">` : (ci.original ? `<img src="${ci.original}" alt="" class="dim">` : '<em>—</em>');
  const has = !!ci.original;
  ['ciSaveInsert', 'ciSave', 'ciApply'].forEach((id) => { if ($('#' + id)) $('#' + id).disabled = !has || (id === 'ciApply' && !ci.result); });
  if ($('#ciRemove')) {
    $('#ciRemove').disabled = !has || ci.kind === 'svg';
    $('#ciRemove').title = ci.kind === 'svg' ? 'Los SVG son vectoriales: ya no tienen fondo de píxeles' : '';
  }
  if ($('#ciUndo')) $('#ciUndo').hidden = !ci.result;
  $('#ciMsg').className = 'ai-msg';
  $('#ciMsg').textContent = ci.kind === 'svg' ? 'SVG vectorial: se guarda tal cual (escala sin perder calidad).' : '';
}

async function runRemoveBg() {
  const btn = $('#ciRemove'), msg = $('#ciMsg');
  const q = $('#ciQuality').value, label = $('#ciQuality').selectedOptions[0].textContent;
  btn.disabled = true;
  msg.className = 'ai-msg';
  msg.innerHTML = `<span class="spinner"></span>Quitando el fondo… ${/descarga/.test(label) ? '(la primera vez descarga el modelo, puede tardar un par de minutos)' : ''}`;
  const t0 = performance.now();
  try {
    const r = await fetch('/api/remove-bg', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data: ci.original, quality: q, soft: $('#ciSoft').checked }) });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Error');
    ci.result = d.data;
    showCustomPreview();
    msg.textContent = `Listo en ${((performance.now() - t0) / 1000).toFixed(1)} s (${d.w}×${d.h} px). Si recortó de más, probá otra calidad.`;
    const opt = $('#ciQuality').selectedOptions[0]; opt.textContent = opt.textContent.replace(/ — descarga.*$/, ' ✓');
  } catch (e) {
    msg.className = 'ai-msg err'; msg.textContent = '✗ ' + e.message;
  } finally { btn.disabled = false; }
}

async function saveCustomIcon(insert) {
  const name = $('#ciName').value.trim() || 'Mi icono';
  const r = await fetch('/api/custom-icons', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, data: ci.result || ci.original }) });
  const ic = await r.json();
  if (!r.ok) { toast(ic.detail || 'No se pudo guardar'); return; }
  ICONS.unshift(ic); ICON_BY_ID.set(ic.id, ic);
  ic._n = libTokens(ic.name + ' ' + (ic.tags || '')); ic._c = libTokens(ic.category);
  closeModal();
  if (insert) await addIcon(ic);
  if (lib.group === 'mis' || !lib.q) { fillCategories(); filterIcons(); }
  toast(`"${name}" guardado en Mis iconos`);
}

async function applyToNode() { // reemplaza la imagen de la figura por la versión sin fondo
  const n = ci.node, src = ci.result;
  const img = await loadSvg(src);
  const [w0, h0] = await imgSize(src);
  const w = n.width(), h = w * h0 / w0;
  n.setAttrs({ image: img, src, width: w, height: h, offsetX: w / 2, offsetY: h / 2 });
  if (n.getAttr('tint')) applyTint(n);
  layer.batchDraw(); updateAttached(); commit(); closeModal(); select([n]);
  toast('Fondo quitado');
}

/* quitar el fondo a una imagen que ya está en la figura */
async function removeBgFromNode(n) {
  const src = n.getAttr('src');
  const data = src.startsWith('data:') ? src : await fetch(src).then((r) => r.blob()).then((b) => fileToDataURL(b));
  openCustomIconModal({ data, name: (n.getAttr('meta') || {}).name || '', node: n });
}

/* guardar en Mis iconos una imagen que ya está en la figura */
async function saveNodeAsCustom(n) {
  const src = n.getAttr('src');
  const data = src.startsWith('data:') ? src : await fetch(src).then((r) => r.blob()).then((b) => fileToDataURL(b));
  const name = prompt('Nombre para Mis iconos:', (n.getAttr('meta') || {}).name || 'Mi icono');
  if (name === null) return;
  const r = await fetch('/api/custom-icons', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, data }) });
  const ic = await r.json();
  if (!r.ok) { toast(ic.detail || 'No se pudo guardar'); return; }
  ICONS.unshift(ic); ICON_BY_ID.set(ic.id, ic); ic._n = libTokens(ic.name); ic._c = libTokens(ic.category);
  toast(`"${name}" guardado en Mis iconos`);
}

async function deleteCustomIcon(ic) {
  if (!confirm(`¿Eliminar "${ic.name}" de Mis iconos? Las figuras que ya lo usan pueden quedar sin esa imagen.`)) return;
  await fetch('/api/custom-icons/' + encodeURIComponent(ic.id), { method: 'DELETE' });
  const i = ICONS.indexOf(ic); if (i >= 0) ICONS.splice(i, 1);
  ICON_BY_ID.delete(ic.id);
  filterIcons(); toast('Eliminado de Mis iconos');
}

$('#btnCustomIcon').addEventListener('click', () => openCustomIconModal());
// pegar una imagen con el cuadro abierto la carga en el cuadro (en lugar de en el lienzo)
window.addEventListener('paste', (e) => {
  if ($('#modal').hidden || !$('#ciDrop')) return;
  const f = [...(e.clipboardData?.items || [])].find((it) => it.kind === 'file' && it.type.startsWith('image/'))?.getAsFile();
  if (f) { e.preventDefault(); e.stopImmediatePropagation(); loadCustomFile(f); }
}, true);
