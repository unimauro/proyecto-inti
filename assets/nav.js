/* Proyecto INTI — menú lateral de secciones (escritorio) + cajón "☰ Secciones" (móvil).
   Lee los <h2> de las secciones, les asigna id, agrupa por tema y resalta la sección visible. */
(function () {
  const GRUPOS = [
    ['Resumen', /salud, nutrici|pobreza|anemia|carátula|las 25|preguntas/i],
    ['Dinero público', /recauda|regresa|gasto|canon|presupuesto|financiamiento|camisea|ruta del dinero|en qué se gasta|quién recibe|presupuesto/i],
    ['Salud y vida', /salud y vida|camas|nacimiento|esperanza/i],
    ['Educación', /lectura|matemática|educa/i],
    ['Territorio', /censo|vivienda|provincia|distrito|cusco a fondo|mapa|territorio/i],
    ['Comparar', /ubica|ranking|cuadro|compar|benchmark|correlaci|similares/i],
    ['Distrito', /resumen|diagn|familia|prospectiva|simulador|clima|conflict|seguridad|oportunidad|proyectos prioritarios|corredor|interconex|motor|consultas/i],
    ['Planes y ayuda', /roadmap|hoja de ruta|descarga|planes|qué es|fuentes/i],
  ];
  // En el dashboard (tiene selector de distrito) se usa otra agrupación
  const DASH = [
    ['Tu distrito', /resumen|diagn|familia|prospectiva|simulador|seguridad|clima|conflict|oportunidad|proyectos prioritarios/i],
    ['Territorio y regiones', /mapa|comparador|benchmark|cuadro de indicadores|correlaci|corredor|interconex/i],
    ['IA y planes', /motor|consultas|roadmap|hoja de ruta|descarga|planes|qué es/i],
  ];
  const slug = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
  const limpia = (t) => t.replace(/^[^\p{L}\p{N}¿]+/u, '').replace(/\s*\(.*?\)\s*$/, '').trim();
  const ico = (h) => { const m = h.textContent.trim().match(/^(\p{Extended_Pictographic}\uFE0F?)/u); if (m) return m[1];
    const sib = h.parentElement && h.parentElement.querySelector('.ico'); return sib ? sib.textContent.trim() : '•'; };

  function build() {
    const G = document.getElementById('selRegion') ? DASH : GRUPOS;
    const hs = [...document.querySelectorAll('section h2, header.cover h1')].filter((h) => h.offsetParent !== null || h.closest('section'));
    if (hs.length < 4) return;
    const items = hs.map((h) => {
      const sec = h.closest('section') || h.closest('header');
      if (!sec.id) sec.id = slug(limpia(h.textContent)) || ('s' + Math.random().toString(36).slice(2, 7));
      const txt = h.tagName === 'H1' ? 'Inicio' : limpia(h.textContent);
      const g = h.tagName === 'H1' ? 'Inicio' : ((G.find(([, re]) => re.test(h.textContent)) || ['Más'])[0]);
      return { id: sec.id, txt, ico: h.tagName === 'H1' ? '🏠' : ico(h), g, el: sec };
    });
    const orden = ['Inicio', ...G.map((g) => g[0]), 'Más'];
    const html = orden.map((g) => {
      const its = items.filter((i) => i.g === g); if (!its.length) return '';
      return `<div class="inav-g">${g === 'Inicio' ? '' : `<div class="inav-gt">${g}</div>`}${its.map((i) => `<a href="#${i.id}" data-id="${i.id}"><span class="inav-i">${i.ico}</span><span>${i.txt}</span></a>`).join('')}</div>`;
    }).join('');
    const css = `
.inav{position:fixed;top:0;left:0;bottom:0;width:250px;background:rgba(10,15,30,.96);border-right:1px solid var(--line,#243156);overflow-y:auto;z-index:60;padding:16px 10px 30px;backdrop-filter:blur(10px);transition:transform .25s;font-family:Inter,system-ui,sans-serif}
.inav .inav-h{font-weight:800;font-size:.95rem;color:#e8edf7;padding:4px 10px 12px;display:flex;justify-content:space-between;align-items:center}
.inav .inav-h a{color:#ffcf5c;text-decoration:none}
.inav-gt{font-size:.66rem;text-transform:uppercase;letter-spacing:1.2px;color:#5f6f99;font-weight:800;margin:14px 10px 4px}
.inav a[data-id]{display:flex;gap:8px;align-items:flex-start;padding:6px 10px;border-radius:9px;color:#8b9bc4;font-size:.82rem;line-height:1.3;text-decoration:none;border-left:3px solid transparent}
.inav a[data-id]:hover{background:rgba(255,255,255,.05);color:#e8edf7}
.inav a.on{background:rgba(245,166,35,.12);color:#ffcf5c;border-left-color:#f5a623;font-weight:700}
.inav-i{width:18px;flex-shrink:0;text-align:center}
.inav-x{display:none;background:none;border:0;color:#8b9bc4;font-size:1.3rem;cursor:pointer}
.inav-btn{display:none;position:fixed;right:14px;bottom:14px;z-index:61;background:linear-gradient(90deg,#f5a623,#ff7a18);color:#1a1206;border:0;border-radius:999px;padding:11px 16px;font-weight:800;font-size:.9rem;box-shadow:0 10px 30px rgba(0,0,0,.4);cursor:pointer;font-family:inherit}
.inav-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:59}
@media(min-width:1200px){body.has-inav{padding-left:250px}}
@media(max-width:1199px){.inav{transform:translateX(-100%);width:min(86vw,300px)}.inav.open{transform:none}.inav-btn{display:block}.inav-x{display:block}.inav.open~.inav-bg{display:block}}
body[data-theme="claro"] .inav{background:rgba(255,255,255,.97)}body[data-theme="claro"] .inav a[data-id]{color:#475569}body[data-theme="claro"] .inav .inav-h{color:#0f172a}
@media print{.inav,.inav-btn,.inav-bg{display:none!important}body.has-inav{padding-left:0}}`;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const home = document.querySelector('nav.top a.brand, a.brand');
    const nav = document.createElement('nav'); nav.className = 'inav'; nav.setAttribute('aria-label', 'Secciones');
    nav.innerHTML = `<div class="inav-h"><a href="${home ? home.getAttribute('href') : './'}">🌞 Proyecto INTI</a><button class="inav-x" aria-label="Cerrar">✕</button></div>${html}`;
    const bg = document.createElement('div'); bg.className = 'inav-bg';
    const btn = document.createElement('button'); btn.className = 'inav-btn'; btn.textContent = '☰ Secciones'; btn.setAttribute('aria-label', 'Abrir menú de secciones');
    document.body.prepend(bg); document.body.prepend(nav); document.body.appendChild(btn); document.body.classList.add('has-inav');
    const close = () => nav.classList.remove('open');
    btn.onclick = () => nav.classList.add('open'); bg.onclick = close; nav.querySelector('.inav-x').onclick = close;
    nav.querySelectorAll('a[data-id]').forEach((a) => a.addEventListener('click', () => { if (innerWidth < 1200) close(); }));
    // resaltar la sección visible
    const links = Object.fromEntries([...nav.querySelectorAll('a[data-id]')].map((a) => [a.dataset.id, a]));
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => { if (e.isIntersecting) { Object.values(links).forEach((a) => a.classList.remove('on')); const a = links[e.target.id]; if (a) { a.classList.add('on'); a.scrollIntoView({ block: 'nearest' }); } } });
    }, { rootMargin: '-30% 0px -60% 0px' });
    items.forEach((i) => io.observe(i.el));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
