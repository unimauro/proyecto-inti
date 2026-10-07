/* Proyecto INTI — chat flotante "Pregúntale a INTI" para carátulas regionales y provinciales.
   Responde con la memoria de datos oficiales (data/memoria_chat.json + data/regiones.json).
   Si config.js define gateway + token (ai.tunky.net), usa el LLM con esa misma memoria como contexto. */
(function () {
  const ROOT = window.INTI_ROOT || './';
  const DEP = window.INTI_DEP || null;
  let MEM = null, R = null, CFG = null;
  const norm = (x) => String(x || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase();
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const KW = [['pobreza', /POBRE/], ['anemia', /ANEMI/], ['dci', /DESNUTRI/], ['vacunas12m', /VACUN/], ['cred', /CRED|CONTROL/], ['hierro', /HIERRO/],
    ['lactancia', /LACTAN/], ['saneamiento', /SANEAMIENTO/], ['violencia', /VIOLEN/], ['ingreso', /INGRESO|SUELDO/], ['c_agua', /\bAGUA\b/], ['c_desague', /DESAG/],
    ['c_internet', /INTERNET/], ['lectura', /LECTUR|LEER/], ['matematica', /MATEMAT/], ['empresas_1k', /EMPRESA/], ['camas_10k', /CAMA/], ['hab_medico', /MEDICO/],
    ['evn', /ESPERANZA DE VIDA/], ['tmi', /MORTALIDAD INFANTIL/], ['canon_pc', /CANON|REGALIA|CAMISEA|FOCAM/], ['tax_pc', /IMPUEST|RECAUD|SUNAT/],
    ['gasto_pc', /GASTO|PRESUPUESTO/], ['retorno', /REGRESA|RETORN/]];
  const fmt = (v, u) => v == null ? '—' : (u === 'S/' ? 'S/ ' + Math.round(v).toLocaleString('es-PE') : (String((+v).toFixed(u === 'x' ? 2 : 1)).replace('.', ',') + (u === '%' ? '%' : (u ? ' ' + u : ''))));
  const val = (r, k) => (r && r.vals) ? r.vals[k] : null;
  const regs = (Q) => { const out = []; if (!MEM) return out; const QQ = ' ' + Q.replace(/[^A-Z ]/g, ' ') + ' ';
    for (const d in MEM.regiones) { const n = norm(MEM.regiones[d].nombre); if (QQ.includes(' ' + n + ' ') || (n === 'CUSCO' && QQ.includes(' CUZCO '))) out.push(d); }
    if (!out.length && DEP && /ESTA REGION|AQUI|ACA|MI REGION|LA REGION|ESTA PROVINCIA/.test(Q)) out.push(DEP); return out; };
  const inds = (Q) => KW.filter(([, re]) => re.test(Q)).map(([k]) => k);
  function contexto(q) {
    const Q = norm(q); let rs = regs(Q); if (DEP && !rs.includes(DEP)) rs.unshift(DEP);
    let t = 'MEMORIA INTI (datos OFICIALES, usa solo estos):\nReglas: ' + MEM.reglas.join(' ') + '\n' + MEM.nacional + '\n';
    rs.slice(0, 3).forEach((d) => { t += MEM.regiones[d].texto + '\n'; });
    inds(Q).slice(0, 3).forEach((k) => { const r = MEM.rankings[k]; if (r) t += `Ranking ${r.etiqueta} (${r.fuente}), de mejor a peor: ${r.orden_mejor_a_peor.join(', ')}.\n`; });
    return t;
  }
  function local(q) {
    const Q = norm(q), rs = regs(Q), ks = inds(Q), I = R.indicadores;
    const li = (a) => '<ul>' + a.map((x) => `<li>${x}</li>`).join('') + '</ul>';
    const rank = /RANKING|MAYOR|MENOR|MENOS|MAS |PEOR|MEJOR|QUE REGION|CUAL|DONDE|TOP/.test(Q);
    if (rs.length >= 2) {
      const rr = rs.slice(0, 3).map((d) => R.regiones[d]);
      return `<b>${rr.map((r) => r.nombre).join(' vs ')}</b><table>${I.map((i) => `<tr><td>${esc(i.l)}</td>${rr.map((r) => `<td><b>${fmt(val(r, i.k), i.u)}</b></td>`).join('')}</tr>`).join('')}</table>`;
    }
    if (rank && ks.length && !rs.length) {
      const i = I.find((x) => x.k === ks[0]); const rows = Object.values(R.regiones).map((r) => [r.nombre, val(r, i.k)]).filter((x) => x[1] != null).sort((a, b) => b[1] - a[1]);
      const menos = /MENOS|MENOR|MAS BAJ/.test(Q); const l = menos ? rows.slice(-5).reverse() : rows.slice(0, 5);
      return `<b>${esc(i.l)} (${esc(i.f)}) — ${menos ? 'valores más bajos' : 'valores más altos'}</b>` + li(l.map((x) => `${esc(x[0])}: <b>${fmt(x[1], i.u)}</b>`)) + `Perú: ${fmt(R.nacional.vals[i.k], i.u)}`;
    }
    const d = rs[0] || DEP;
    if (d && R.regiones[d]) {
      const r = R.regiones[d];
      if (ks.length) return `<b>${esc(r.nombre)}</b>` + li(ks.slice(0, 4).map((k) => { const i = I.find((x) => x.k === k); return i ? `${esc(i.l)}: <b>${fmt(val(r, k), i.u)}</b> · Perú ${fmt(R.nacional.vals[k], i.u)} · puesto ${(r.ranks || {})[k] || '—'} de 25 (${esc(i.f)})` : ''; }));
      return `<b>${esc(r.nombre)} en cifras</b>` + li(MEM.regiones[d].texto.split(/; /).slice(0, 12).map(esc));
    }
    return 'Puedo responder sobre las 25 regiones: rankings (“¿dónde hay más anemia?”), comparaciones (“Compara Cusco y Puno”) o un indicador (“canon en Arequipa”).';
  }
  async function ask(q) {
    if (CFG && CFG.gateway && CFG.token) {
      try {
        const res = await fetch(CFG.gateway, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Client-Token': CFG.token },
          body: JSON.stringify({ messages: [{ role: 'user', content: contexto(q) + '\n\nPregunta: ' + q }] }) });
        const j = await res.json(); if (res.ok && j.reply) return esc(j.reply).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
      } catch (e) { /* cae a modo memoria */ }
    }
    return local(q);
  }
  function ui() {
    const css = `.ichat-btn{position:fixed;left:14px;bottom:14px;z-index:62;background:#131d3a;color:#ffcf5c;border:1px solid #f5a623;border-radius:999px;padding:11px 16px;font-weight:800;font-family:Inter,system-ui,sans-serif;cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.4)}
@media(min-width:1200px){.ichat-btn{left:264px}}
.ichat{position:fixed;left:14px;bottom:70px;z-index:63;width:min(92vw,400px);max-height:70vh;display:none;flex-direction:column;background:#0f1730;border:1px solid #243156;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.5);font-family:Inter,system-ui,sans-serif;color:#e8edf7}
@media(min-width:1200px){.ichat{left:264px}}
.ichat.open{display:flex}.ichat-h{padding:12px 14px;border-bottom:1px solid #243156;font-weight:800;display:flex;justify-content:space-between}.ichat-h button{background:none;border:0;color:#8b9bc4;cursor:pointer;font-size:1.1rem}
.ichat-b{padding:12px 14px;overflow-y:auto;flex:1;font-size:.88rem;line-height:1.45}.ichat-b .m{margin:8px 0;padding:9px 11px;border-radius:12px;background:#18244a}.ichat-b .u{background:rgba(245,166,35,.15);margin-left:30px}
.ichat-b table{font-size:.78rem;width:100%;border-collapse:collapse}.ichat-b td{border-bottom:1px solid #243156;padding:3px 4px}.ichat-b ul{margin-left:16px}
.ichat-c{display:flex;gap:6px;flex-wrap:wrap;padding:0 14px 8px}.ichat-c button{background:#18244a;color:#8b9bc4;border:1px solid #243156;border-radius:999px;padding:4px 9px;font-size:.74rem;cursor:pointer}
.ichat-f{display:flex;gap:6px;padding:10px;border-top:1px solid #243156}.ichat-f input{flex:1;background:#131d3a;color:#e8edf7;border:1px solid #243156;border-radius:10px;padding:9px;font:inherit}.ichat-f button{background:linear-gradient(90deg,#f5a623,#ff7a18);border:0;border-radius:10px;padding:0 14px;font-weight:800;cursor:pointer}
.ichat-n{font-size:.68rem;color:#5f6f99;padding:0 14px 8px}@media print{.ichat,.ichat-btn{display:none!important}}`;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const nombre = DEP && R && R.regiones[DEP] ? R.regiones[DEP].nombre : 'el Perú';
    const btn = document.createElement('button'); btn.className = 'ichat-btn'; btn.textContent = '💬 Pregúntale a INTI';
    const box = document.createElement('div'); box.className = 'ichat';
    const chips = [`¿Cómo está ${nombre}?`, `Canon en ${nombre}`, '¿Dónde hay más anemia?', `Compara ${nombre === 'el Perú' ? 'Cusco' : nombre} y Puno`];
    box.innerHTML = `<div class="ichat-h">💬 Pregúntale a INTI <button aria-label="Cerrar">✕</button></div><div class="ichat-b"><div class="m">Hola. Respondo con datos oficiales 2025-2026 de las 25 regiones (INEI, MEF, SUNAT, MINSA, MINEDU). Si un dato no está, te lo digo.</div></div>
<div class="ichat-c">${chips.map((c) => `<button>${esc(c)}</button>`).join('')}</div><form class="ichat-f"><input placeholder="Escribe tu pregunta…" aria-label="Pregunta"><button>➤</button></form>
<div class="ichat-n">${CFG && CFG.token ? 'IA conectada (ai.tunky.net) con memoria de datos oficiales.' : 'Modo memoria: respuestas directas desde los datos oficiales.'}</div>`;
    document.body.appendChild(btn); document.body.appendChild(box);
    const body = box.querySelector('.ichat-b'), inp = box.querySelector('input');
    const add = (h, u) => { const d = document.createElement('div'); d.className = 'm' + (u ? ' u' : ''); d.innerHTML = h; body.appendChild(d); body.scrollTop = body.scrollHeight; return d; };
    const go = async (q) => { if (!q) return; add(esc(q), true); const w = add('…'); w.innerHTML = await ask(q); body.scrollTop = body.scrollHeight; };
    btn.onclick = () => { box.classList.toggle('open'); if (box.classList.contains('open')) inp.focus(); };
    box.querySelector('.ichat-h button').onclick = () => box.classList.remove('open');
    box.querySelectorAll('.ichat-c button').forEach((b) => b.onclick = () => go(b.textContent));
    box.querySelector('form').onsubmit = (e) => { e.preventDefault(); const q = inp.value.trim(); inp.value = ''; go(q); };
  }
  Promise.all([fetch(ROOT + 'data/memoria_chat.json').then((r) => r.json()), fetch(ROOT + 'data/regiones.json').then((r) => r.json()),
    new Promise((res) => { const s = document.createElement('script'); s.src = ROOT + 'config.js'; s.onload = () => res(window.INTI_IA || null); s.onerror = () => res(null); document.head.appendChild(s); })])
    .then(([m, r, c]) => { MEM = m; R = r; CFG = c; ui(); }).catch(() => {});
})();
