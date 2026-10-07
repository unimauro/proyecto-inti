#!/usr/bin/env python3
"""Genera data/regiones.json y una carátula estática por región en region/<slug>/index.html.

Fuentes (todas en data/fuentes/, ver README de cada una):
  - endes2025_departamentos.json   INEI ENDES 2025 (Indicadores de Programas Presupuestales)
  - enaho2025_pobreza_departamentos.json  INEI ENAHO 2016-2025 (Evolución de la pobreza monetaria)
  - censo2025_departamentos.json   INEI Censos Nacionales 2025 (notas de prensa departamentales)
  - cusco_extra.json               Censo 2025 Cusco (detalle) + turismo
  - ../indicadores.json / ../territorio.json  datos distritales (Censo 2017, IDH 2019, pobreza)

Uso: python3 scripts/build_regiones.py
"""
import json, os, re, unicodedata, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)
SITE = 'https://unimauro.github.io/proyecto-inti/'

def load(p): return json.load(open(D(p), encoding='utf-8'))
def norm(x): return ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn').upper().strip()
def slug(x): return re.sub(r'[^a-z0-9]+', '-', norm(x).lower()).strip('-')
def esc(x): return html.escape(str(x))
def fmt(n): return f'{n:,.0f}'.replace(',', ' ')
def f1(x): return ('—' if x is None else f'{x:.1f}'.replace('.', ','))
def fidh(x): return ('—' if x is None else f'{x / 100:.3f}'.replace('.', ','))  # IDH guardado ×100

TER = load('data/territorio.json')
IND = load('data/indicadores.json')
ENDES = load('data/fuentes/endes2025_departamentos.json')
ENAHO = load('data/fuentes/enaho2025_pobreza_departamentos.json')
CENSO = load('data/fuentes/censo2025_departamentos.json')
CUSCO = load('data/fuentes/cusco_extra.json')

NOMBRE = {'Ancash': 'Áncash', 'Apurimac': 'Apurímac', 'Huanuco': 'Huánuco', 'Junin': 'Junín',
          'Madre De Dios': 'Madre de Dios', 'San Martin': 'San Martín', 'Callao': 'Callao'}
NAT = {'TUMBES': 'costa', 'PIURA': 'costa', 'LAMBAYEQUE': 'costa', 'LA LIBERTAD': 'costa', 'LIMA': 'costa', 'CALLAO': 'costa',
       'ICA': 'costa', 'AREQUIPA': 'costa', 'MOQUEGUA': 'costa', 'TACNA': 'costa', 'CAJAMARCA': 'sierra', 'ANCASH': 'sierra',
       'HUANUCO': 'sierra', 'PASCO': 'sierra', 'JUNIN': 'sierra', 'HUANCAVELICA': 'sierra', 'AYACUCHO': 'sierra',
       'APURIMAC': 'sierra', 'CUSCO': 'sierra', 'PUNO': 'sierra', 'AMAZONAS': 'selva', 'LORETO': 'selva', 'UCAYALI': 'selva',
       'MADRE DE DIOS': 'selva', 'SAN MARTIN': 'selva'}
EMOJI = {'costa': '🌊', 'sierra': '⛰️', 'selva': '🌿'}
CAPITAL = {'Amazonas': 'Chachapoyas', 'Ancash': 'Huaraz', 'Apurimac': 'Abancay', 'Arequipa': 'Arequipa', 'Ayacucho': 'Ayacucho',
           'Cajamarca': 'Cajamarca', 'Callao': 'Callao', 'Cusco': 'Cusco', 'Huancavelica': 'Huancavelica', 'Huanuco': 'Huánuco',
           'Ica': 'Ica', 'Junin': 'Huancayo', 'La Libertad': 'Trujillo', 'Lambayeque': 'Chiclayo', 'Lima': 'Lima',
           'Loreto': 'Iquitos', 'Madre De Dios': 'Puerto Maldonado', 'Moquegua': 'Moquegua', 'Pasco': 'Cerro de Pasco',
           'Piura': 'Piura', 'Puno': 'Puno', 'San Martin': 'Moyobamba', 'Tacna': 'Tacna', 'Tumbes': 'Tumbes', 'Ucayali': 'Pucallpa'}

def endes_key(dep):
    if dep == 'Callao': return 'Prov. Const. del Callao'
    if dep == 'Lima': return 'Lima Metropolitana'
    return NOMBRE.get(dep, dep)

def enaho_key(dep):
    if dep == 'Callao': return 'Prov. Const. del Callao'
    if dep == 'Lima': return 'Lima Metropolitana'
    return NOMBRE.get(dep, dep)

def wavg(items, key, wkey='p'):
    num = den = 0
    for it in items:
        v, w = it.get(key), it.get(wkey)
        if v is not None and w: num += v * w; den += w
    return round(num / den, 1) if den else None

ENDES_IND = [  # clave, etiqueta, unidad, más es mejor?
    ('anemia', 'Anemia en niñas/os de 6-35 meses', '%', False),
    ('dci', 'Desnutrición crónica en menores de 5 años', '%', False),
    ('vacunas12m', 'Vacunas básicas completas (< 12 meses)', '%', True),
    ('cred', 'Controles CRED completos (< 36 meses)', '%', True),
    ('hierro', 'Suplemento de hierro (6-35 meses)', '%', True),
    ('lactancia', 'Lactancia materna exclusiva (< 6 meses)', '%', True),
    ('agua', 'Hogares con acceso a agua tratada', '%', True),
    ('saneamiento', 'Hogares con saneamiento básico', '%', True),
    ('violencia', 'Mujeres que sufrieron violencia de pareja (alguna vez)', '%', False),
    ('tgf', 'Tasa global de fecundidad', 'hijos', None),
]

# Indicadores comparables entre las 25 regiones (cuadros, rankings y memoria del chatbot)
def _endes(k): return lambda r: (r['endes'].get(k) or {}).get('y2025')
RANK_IND = [  # clave, etiqueta corta, getter, ¿más es mejor?, unidad, fuente
    ('pobreza', 'Pobreza monetaria', lambda r: (r['pobreza_serie'] or [None])[-1], False, '%', 'ENAHO 2025'),
    ('anemia', 'Anemia 6-35 meses', _endes('anemia'), False, '%', 'ENDES 2025'),
    ('dci', 'Desnutrición crónica <5', _endes('dci'), False, '%', 'ENDES 2025'),
    ('vacunas12m', 'Vacunas completas <12m', _endes('vacunas12m'), True, '%', 'ENDES 2025'),
    ('cred', 'Controles CRED <36m', _endes('cred'), True, '%', 'ENDES 2025'),
    ('hierro', 'Suplemento de hierro', _endes('hierro'), True, '%', 'ENDES 2025'),
    ('lactancia', 'Lactancia exclusiva', _endes('lactancia'), True, '%', 'ENDES 2025'),
    ('saneamiento', 'Saneamiento básico', _endes('saneamiento'), True, '%', 'ENDES 2025'),
    ('violencia', 'Violencia de pareja (alguna vez)', _endes('violencia'), False, '%', 'ENDES 2025'),
    ('ingreso', 'Ingreso real per cápita', lambda r: (r['ingreso_real'] or [None])[-1], True, 'S/', 'ENAHO 2025'),
    ('c_agua', 'Agua red pública en vivienda', lambda r: (r['censo2025'] or {}).get('agua'), True, '%', 'Censo 2025'),
    ('c_desague', 'Desagüe red pública', lambda r: (r['censo2025'] or {}).get('desague'), True, '%', 'Censo 2025'),
    ('c_internet', 'Hogares con Internet', lambda r: (r['censo2025'] or {}).get('internet'), True, '%', 'Censo 2025'),
]

def rankings(regiones):
    """{clave: [(dep, valor), ...] ordenado de MEJOR a PEOR}"""
    out = {}
    for key, _, get, up, *_ in RANK_IND:
        vals = [(d, get(r)) for d, r in regiones.items() if get(r) is not None]
        out[key] = sorted(vals, key=lambda x: -x[1] if up else x[1])
    return out

def build():
    regiones = {}
    ranking_pob = sorted([(k, v[-1]) for k, v in ENAHO['pobreza'].items() if k not in ('Nacional',)], key=lambda x: -x[1])
    for dep, provs in TER.items():
        nombre = NOMBRE.get(dep, dep)
        dists = []
        provinces = []
        for prov, arr in provs.items():
            pd = []
            for o in arr:
                r = IND.get(o['u'], {})
                it = {'u': o['u'], 'd': o['d'], 'prov': prov, 'p': r.get('p'), 'p25': r.get('p25'), 'i': r.get('i'),
                      't': r.get('t'), 'e': r.get('e'), 'va': r.get('va')}
                pd.append(it); dists.append(it)
            provinces.append({'prov': prov, 'n': len(pd), 'p': sum(x['p'] or 0 for x in pd),
                              'p25': sum(x['p25'] or x['p'] or 0 for x in pd),
                              'i': wavg(pd, 'i'), 't': wavg(pd, 't'), 'e': wavg(pd, 'e')})
        ek, nk = endes_key(dep), enaho_key(dep)
        endes = {k: ENDES[k]['v'].get(ek) for k, *_ in ENDES_IND}
        pob_series = ENAHO['pobreza'].get(nk)
        reg = {
            'dep': dep, 'nombre': nombre, 'slug': slug(nombre), 'natural': NAT.get(norm(dep)), 'capital': CAPITAL.get(dep),
            'n_prov': len(provs), 'n_dist': len(dists),
            'pob2017': sum(x['p'] or 0 for x in dists), 'pob25_est': sum(x['p25'] or x['p'] or 0 for x in dists),
            'idh2019': wavg(dists, 'i'), 'pobreza_distr': wavg(dists, 't'), 'pobreza_ext_distr': wavg(dists, 'e'),
            'endes': endes, 'endes_ref': ek,
            'pobreza_serie': pob_series, 'gasto_real': ENAHO['gasto_real'].get(nk), 'ingreso_real': ENAHO['ingreso_real'].get(nk),
            'enaho_ref': nk,
            'censo2025': CENSO.get(dep),
            'provincias': sorted(provinces, key=lambda x: -x['p25']),
            'criticos': sorted([x for x in dists if x['t'] is not None], key=lambda x: -x['t'])[:8],
            'mejores': sorted([x for x in dists if x['i'] is not None], key=lambda x: -x['i'])[:5],
            'distritos': sorted(dists, key=lambda x: (x['prov'], x['d'])),
        }
        if dep == 'Lima':
            reg['endes_lima_prov'] = {k: ENDES[k]['v'].get('Departamento de Lima') for k, *_ in ENDES_IND}
            reg['pobreza_lima_prov'] = ENAHO['pobreza'].get('Lima')
        rk = [i for i, (k, _) in enumerate(ranking_pob) if k == nk]
        reg['rank_pobreza'] = (rk[0] + 1, len(ranking_pob)) if rk else None
        regiones[dep] = reg
    nac = {'endes': {k: ENDES[k]['v'].get('Total') for k, *_ in ENDES_IND}, 'pobreza_serie': ENAHO['pobreza']['Nacional'],
           'gasto_real': ENAHO['gasto_real']['Nacional'], 'ingreso_real': ENAHO['ingreso_real']['Nacional'],
           'censo2025': CENSO['_meta']['nacional']}
    return regiones, nac

# ---------------------------------------------------------------- HTML
CSS = """
:root{--bg:#0a0f1e;--bg2:#0f1730;--card:#131d3a;--card2:#18244a;--line:#243156;--txt:#e8edf7;--muted:#8b9bc4;--muted2:#5f6f99;
--inti:#f5a623;--inti2:#ffcf5c;--sol:#ff7a18;--verde:#22c55e;--ambar:#f59e0b;--rojo:#ef4444;--azul:#3b82f6;--h1:#f5a623;--h2:#ff7a18}
*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}html,body{overflow-x:hidden}.grid2>*,.kpis>*{min-width:0}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--txt);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--inti2);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
nav.top{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:12px 0;font-size:.86rem}
nav.top .brand{font-weight:800;color:var(--txt)}nav.top select{max-width:46vw;background:var(--card);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:7px 10px;font:inherit;max-width:100%}
.cover{position:relative;overflow:hidden;border-radius:26px;margin:6px 0 26px;padding:clamp(28px,6vw,64px) clamp(20px,5vw,56px);
 background:linear-gradient(135deg,var(--h1),var(--h2));color:#fff;min-height:340px;display:flex;flex-direction:column;justify-content:flex-end;box-shadow:0 30px 80px -30px rgba(0,0,0,.6)}
.cover::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 85% 15%,rgba(255,255,255,.28),transparent 45%),linear-gradient(180deg,transparent 30%,rgba(0,0,0,.38));pointer-events:none}
.cover .pattern{position:absolute;inset:0;opacity:.13;pointer-events:none}
.cover .emb{position:absolute;right:clamp(14px,4vw,48px);top:clamp(14px,4vw,40px);font-size:clamp(3rem,10vw,6.5rem);filter:drop-shadow(0 6px 20px rgba(0,0,0,.3))}
.cover .kicker{position:relative;font-size:.78rem;letter-spacing:2.5px;text-transform:uppercase;font-weight:700;opacity:.92}
.cover h1{position:relative;font-size:clamp(2.6rem,9vw,5.6rem);font-weight:900;letter-spacing:-2px;line-height:1;margin:8px 0 10px;text-shadow:0 4px 30px rgba(0,0,0,.25)}
.cover .lead{position:relative;max-width:720px;font-size:clamp(1rem,2.4vw,1.2rem);font-weight:500;opacity:.96}
.cover .meta{position:relative;display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.cover .meta span{background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.25);padding:5px 12px;border-radius:999px;font-size:.8rem;font-weight:600;backdrop-filter:blur(4px)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:-56px 0 28px;position:relative;z-index:2;padding:0 clamp(0px,2vw,24px)}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 16px 40px -20px rgba(0,0,0,.7)}
.kpi .l{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700}
.kpi .v{font-size:clamp(1.3rem,2.6vw,1.65rem);white-space:nowrap;font-weight:900;margin:2px 0;font-variant-numeric:tabular-nums}
.kpi .s{font-size:.75rem;color:var(--muted)}
.up{color:var(--verde)}.down{color:var(--rojo)}.flat{color:var(--muted)}
section{margin:0 0 30px}h2{font-size:1.35rem;font-weight:800;margin-bottom:6px}.desc{color:var(--muted);font-size:.9rem;margin-bottom:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:14px}
.tbl{width:100%;border-collapse:collapse;font-size:.88rem}.tbl th,.tbl td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.tbl th{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.4px}.tbl td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.7rem;font-weight:700}
.p-real{background:rgba(34,197,94,.15);color:#86efac}.p-reg{background:rgba(59,130,246,.15);color:#93c5fd}.p-ref{background:rgba(245,158,11,.15);color:#fcd34d}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin-top:6px}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--h1),var(--h2))}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chips a{background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:.8rem;color:var(--txt)}
.cta{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(90deg,var(--inti),var(--sol));color:#1a1206;font-weight:800;padding:11px 18px;border-radius:999px}
.cta:hover{text-decoration:none;filter:brightness(1.08)}
.src{font-size:.78rem;color:var(--muted2)}.src a{color:var(--muted)}
.special{border:1px solid rgba(245,166,35,.45);background:linear-gradient(180deg,rgba(245,166,35,.08),transparent)}
details summary{cursor:pointer;font-weight:700}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--muted);font-size:.82rem}
.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,250px),1fr));gap:14px}
.rcard{border-radius:20px;overflow:hidden;background:var(--card);border:1px solid var(--line);color:var(--txt);display:block;transition:transform .15s}
.rcard:hover{transform:translateY(-3px);text-decoration:none}
.rcard .top{padding:22px 16px 16px;color:#fff;min-height:110px;position:relative}.rcard .top b{font-size:1.5rem;font-weight:900;display:block}
.rcard .top em{position:absolute;right:12px;top:10px;font-style:normal;font-size:2rem}
.rcard .bot{padding:12px 16px;font-size:.8rem;color:var(--muted);display:grid;grid-template-columns:1fr 1fr;gap:4px}
.rkgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px}
.rk{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--muted2);border-radius:14px;padding:12px 14px}
.rk.top{border-left-color:var(--verde)}.rk.mid{border-left-color:var(--ambar)}.rk.low{border-left-color:var(--rojo)}
.rk-h{display:flex;justify-content:space-between;gap:8px;font-size:.86rem}.rk-h b{font-size:1.05rem}
.rk-pos{font-size:.78rem;color:var(--muted);margin:2px 0 10px}.rk-pos small{color:var(--muted2)}
.strip{position:relative;height:18px;border-radius:99px;background:linear-gradient(90deg,rgba(139,155,196,.12),rgba(139,155,196,.22))}
.strip i{position:absolute;top:5px;width:8px;height:8px;margin-left:-4px;border-radius:50%;background:rgba(139,155,196,.7)}
.strip i.me{top:1px;width:16px;height:16px;margin-left:-8px;background:var(--h1);border:2px solid #fff;box-shadow:0 0 0 3px rgba(0,0,0,.3);z-index:2}
.rk-ax{display:flex;justify-content:space-between;font-size:.68rem;color:var(--muted2);margin-top:4px}
@media print{nav.top,.cta,footer .no-print{display:none}body{background:#fff;color:#111}.card,.kpi{background:#fff;border-color:#ddd}}
"""

HUES = {'costa': ('#0ea5e9', '#f59e0b'), 'sierra': ('#b45309', '#7c3aed'), 'selva': ('#059669', '#0d9488')}
SPECIAL_HUES = {'Cusco': ('#c2410c', '#7e22ce'), 'Puno': ('#1d4ed8', '#0891b2'), 'Lima': ('#be123c', '#f59e0b'),
                'Arequipa': ('#64748b', '#0ea5e9'), 'Loreto': ('#15803d', '#a16207'), 'Callao': ('#0369a1', '#dc2626')}

INCA = ('<svg class="pattern" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
        '<defs><pattern id="tk" width="24" height="24" patternUnits="userSpaceOnUse">'
        '<path d="M0 12h6V6h6v6h6v6h-6v6H6v-6H0z" fill="#fff"/><rect x="15" y="1" width="6" height="6" fill="none" stroke="#fff" stroke-width="1.4"/>'
        '</pattern></defs><rect width="120" height="120" fill="url(#tk)"/></svg>')
WAVES = ('<svg class="pattern" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs>'
         '<pattern id="wv" width="30" height="14" patternUnits="userSpaceOnUse"><path d="M0 7q7.5-7 15 0t15 0" fill="none" stroke="#fff" stroke-width="1.6"/></pattern>'
         '</defs><rect width="120" height="120" fill="url(#wv)"/></svg>')

def delta(v25, v24, better_up):
    if v25 is None or v24 is None: return ''
    d = round(v25 - v24, 1)
    if d == 0 or better_up is None: cls = 'flat'
    else: cls = 'up' if (d > 0) == better_up else 'down'
    return f'<span class="{cls}">{"+" if d > 0 else ""}{f1(d)} pp vs 2024</span>'

def head(title, desc, url, extra=''):
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-CQY8SYKRG1"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CQY8SYKRG1');</script>
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:url" content="{url}"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{SITE}og-image.jpg"><meta property="og:locale" content="es_PE">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{SITE}og-image.jpg">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌞</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>{CSS}{extra}</style></head><body>"""

def nav(regiones, current=None, depth=2):
    up = '../' * depth
    opts = ''.join(f'<option value="{up}region/{r["slug"]}/"{" selected" if r["dep"] == current else ""}>{esc(r["nombre"])}</option>'
                   for r in sorted(regiones.values(), key=lambda r: r['nombre']))
    return (f'<div class="wrap"><nav class="top"><a class="brand" href="{up}">🌞 Proyecto INTI</a>'
            f'<span><a href="{up}region/">Todas las regiones</a> · <select aria-label="Ir a región" onchange="location.href=this.value">'
            f'<option value="{up}region/">Elegir región…</option>{opts}</select></span></nav>')

def footer(depth=2):
    up = '../' * depth
    return f"""<footer><div>Proyecto INTI — Gemelo Digital del Perú 2075 · <a href="{up}">Dashboard</a> · <a href="{up}region/">Regiones</a> ·
<a href="https://github.com/unimauro/proyecto-inti">Código y datos</a></div>
<div class="src" style="margin-top:8px">Regla del proyecto: <b>no inventamos cifras</b>. Cada dato indica fuente y año; los datos departamentales de encuestas (ENDES/ENAHO) son estimaciones muestrales con intervalo de confianza.
Generado el {date.today().isoformat()}.</div></footer></div></body></html>"""

def page_region(r, nac, regiones):
    dep, nombre = r['dep'], r['nombre']
    h1, h2 = SPECIAL_HUES.get(dep, HUES.get(r['natural'], ('#f5a623', '#ff7a18')))
    emb = '☀️' if dep == 'Cusco' else EMOJI.get(r['natural'], '🌞')
    pattern = INCA if r['natural'] == 'sierra' else WAVES
    c = r['censo2025'] or {}
    e = r['endes']; en = nac['endes']
    ps = r['pobreza_serie'] or []
    pob_txt = (f'{fmt(c["pob"])}' if c.get('pob') else (f'{fmt(c["pob_lima_metropolitana"])}' if c.get('pob_lima_metropolitana') else fmt(r['pob25_est'])))
    pob_sub = ('Censo 2025 (INEI)' if c.get('pob') else ('Lima Metropolitana · Censo 2025' if c.get('pob_lima_metropolitana') else 'estimación 2025 (suma distrital, no oficial)'))
    pob_pill = 'p-real' if (c.get('pob') or c.get('pob_lima_metropolitana')) else 'p-ref'
    an = e.get('anemia') or {}; dci = e.get('dci') or {}
    url = f'{SITE}region/{r["slug"]}/'
    title = f'{nombre} 2025 — indicadores regionales | Proyecto INTI'
    desc = (f'{nombre}: pobreza {f1(ps[-1]) if ps else "—"}% (ENAHO 2025), anemia infantil {f1(an.get("y2025"))}% (ENDES 2025), '
            f'{r["n_prov"]} provincias y {r["n_dist"]} distritos con IDH, pobreza y brechas. Datos oficiales INEI.')
    extra = f':root{{--h1:{h1};--h2:{h2}}}'
    out = [head(title, desc, url, extra), nav(regiones, dep)]
    lead = {
        'Cusco': 'Capital histórica del Perú y corazón del Tawantinsuyu. Su reto: que el auge turístico se traduzca en agua, saneamiento y nutrición para las 13 provincias.',
    }.get(dep, f'Carátula regional con los indicadores oficiales más recientes de {nombre}: pobreza, salud infantil, servicios y brechas por provincia y distrito.')
    out.append(f"""<header class="cover">{pattern}<div class="emb">{emb}</div>
<div class="kicker">Región {esc(r['natural'] or '')} · Carátula regional 2025</div>
<h1>{esc(nombre)}</h1><p class="lead">{esc(lead)}</p>
<div class="meta"><span>🏛️ Capital: {esc(r['capital'] or '—')}</span><span>{r['n_prov']} provincia{'s' if r['n_prov'] != 1 else ''}</span><span>{r['n_dist']} distritos</span>
{f'<span>📉 Puesto {r["rank_pobreza"][0]} de {r["rank_pobreza"][1]} en pobreza (1 = más pobre)</span>' if r['rank_pobreza'] else ''}</div></header>""")
    k = []
    k.append(f'<div class="kpi"><div class="l">Población</div><div class="v">{pob_txt}</div><div class="s"><span class="pill {pob_pill}">{pob_sub}</span></div></div>')
    if ps:
        k.append(f'<div class="kpi"><div class="l">Pobreza monetaria 2025</div><div class="v">{f1(ps[-1])}%</div><div class="s">{delta(ps[-1], ps[-2], False)} · Perú {f1(nac["pobreza_serie"][-1])}%</div></div>')
    if an:
        k.append(f'<div class="kpi"><div class="l">Anemia 6-35 meses 2025</div><div class="v">{f1(an["y2025"])}%</div><div class="s">{delta(an["y2025"], an["y2024"], False)} · Perú {f1(en["anemia"]["y2025"])}%</div></div>')
    if dci:
        k.append(f'<div class="kpi"><div class="l">Desnutrición crónica 2025</div><div class="v">{f1(dci["y2025"])}%</div><div class="s">{delta(dci["y2025"], dci["y2024"], False)} · Perú {f1(en["dci"]["y2025"])}%</div></div>')
    if r['ingreso_real']:
        k.append(f'<div class="kpi"><div class="l">Ingreso real per cápita</div><div class="v">S/ {fmt(r["ingreso_real"][-1])}</div><div class="s">mensual 2025 · Perú S/ {fmt(nac["ingreso_real"][-1])}</div></div>')
    k.append(f'<div class="kpi"><div class="l">IDH (ponderado)</div><div class="v">{fidh(r["idh2019"])}</div><div class="s">PNUD 2019 · promedio de distritos</div></div>')
    out.append(f'<div class="kpis">{"".join(k)}</div>')
    out.append(f'<p style="margin:-8px 0 26px"><a class="cta" href="../../?region={r["slug"]}">Abrir {esc(nombre)} en el gemelo digital →</a></p>')

    # Indicadores ENDES 2025
    rows = []
    for key, lab, uni, up in ENDES_IND:
        v = e.get(key)
        if not v: continue
        nv = en.get(key) or {}
        ref = ' <span class="pill p-ref">referencial</span>' if v.get('ref') else ''
        rows.append(f'<tr><td>{esc(lab)}{ref}</td><td class="n"><b>{f1(v["y2025"])}</b> {uni if uni != "%" else "%"}</td>'
                    f'<td class="n">{delta(v["y2025"], v["y2024"], up)}</td><td class="n">{f1(v["y2021"])}</td><td class="n">{f1(nv.get("y2025"))}</td></tr>')
    lima_note = ('<p class="src" style="margin-top:8px">En Lima se muestra <b>Lima Metropolitana</b> (43 distritos). Lima Provincias (9 provincias): anemia '
                 f'{f1((r.get("endes_lima_prov") or {}).get("anemia", {}).get("y2025"))}%, pobreza {f1((r.get("pobreza_lima_prov") or [None])[-1])}%.</p>') if dep == 'Lima' else ''
    out.append(f"""<section><h2>🩺 Salud, nutrición y servicios — ENDES 2025</h2>
<p class="desc">Indicadores de resultado de los Programas Presupuestales (INEI, publicado mayo 2026). Dato <span class="pill p-reg">departamental</span>: aplica a toda la región, no a cada distrito. Anemia según la nueva directriz OMS 2024 (RM 251-2024-MINSA), la que usa INEI en su titular.</p>
<div class="card scroll"><table class="tbl"><thead><tr><th>Indicador</th><th>{esc(nombre)} 2025</th><th>Cambio</th><th>2021</th><th>Perú 2025</th></tr></thead><tbody>{''.join(rows)}</tbody></table>{lima_note}
<p class="src" style="margin-top:8px">Fuente: <a href="https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf">INEI — Perú: Indicadores de Resultados de los Programas Presupuestales, ENDES 2025</a> (cuadros 01A–36A).</p></div></section>""")

    # Charts
    out.append(f"""<section class="grid2"><div class="card"><h2>📉 Pobreza monetaria 2016–2025</h2><p class="desc">% de la población (ENAHO, INEI). La pandemia disparó la pobreza en 2020.</p><canvas id="chPob" height="220"></canvas>
<p class="src">Fuente: <a href="https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025">INEI — Evolución de la Pobreza Monetaria 2016-2025</a>, cuadro III.1.</p></div>
<div class="card"><h2>🩸 Anemia infantil 2021–2025</h2><p class="desc">% de niñas y niños de 6 a 35 meses (ENDES, directriz OMS 2024).</p><canvas id="chAn" height="220"></canvas>
<p class="src">Fuente: INEI — ENDES 2025, cuadro 06.1A.</p></div></section>""")

    # Censo 2025
    if c and any(c.get(x) for x in ('agua', 'desague', 'luz', 'internet')):
        bars = ''
        for kk, lab in (('agua', '💧 Agua por red pública dentro de la vivienda'), ('desague', '🚽 Desagüe por red pública'), ('luz', '💡 Alumbrado eléctrico por red pública'), ('internet', '🌐 Hogares con Internet')):
            if c.get(kk) is not None:
                bars += f'<div style="margin:10px 0"><div style="display:flex;justify-content:space-between"><span>{lab}</span><b>{f1(c[kk])}%</b></div><div class="bar"><i style="width:{c[kk]}%"></i></div></div>'
        gap = f'<p class="desc" style="margin-top:10px">Brecha: <b>{f1(100 - c["desague"])}%</b> de las viviendas aún sin desagüe por red pública.</p>' if c.get('desague') else ''
        out.append(f"""<section><h2>🏠 Censos Nacionales 2025 — viviendas</h2><p class="desc">Resultados oficiales presentados por INEI en la región{f' · crecimiento anual 2017–2025: <b>{f1(c["crec"])}%</b>' if c.get('crec') is not None else ''}.</p>
<div class="card">{bars}{gap}<p class="src">Fuente: <a href="{c['url']}">INEI — nota de prensa Censos Nacionales 2025 ({esc(nombre)})</a>.</p></div></section>""")

    if dep == 'Cusco':
        out.append(cusco_section())

    # Provincias
    prow = ''.join(f'<tr><td>{esc(p["prov"])}</td><td class="n">{p["n"]}</td><td class="n">{fmt(p["p"])}</td><td class="n">{fmt(p["p25"])}</td>'
                   f'<td class="n">{fidh(p["i"])}</td><td class="n">{f1(p["t"])}%</td><td class="n">{f1(p["e"])}%</td></tr>' for p in r['provincias'])
    out.append(f"""<section><h2>🗺️ Provincias</h2><p class="desc">Agregado desde los datos distritales de INTI (promedios ponderados por población). Pobreza distrital = mapa de pobreza INEI (no comparable con ENAHO 2025).</p>
<div class="card scroll"><table class="tbl"><thead><tr><th>Provincia</th><th>Distritos</th><th>Pob. 2017</th><th>Pob. 2025 est.</th><th>IDH 2019</th><th>Pobreza</th><th>Pob. extrema</th></tr></thead><tbody>{prow}</tbody></table>
<p class="src">Fuentes: INEI Censo 2017; PNUD IDH 2019; INEI mapa de pobreza distrital (vía ubigeo-peru-aumentado). Población 2025 por distrito = estimación, no Censo 2025.</p></div>
<div class="card" style="margin-top:14px"><h2>📊 Pobreza e IDH por provincia</h2><p class="desc">Barras: pobreza (%) · línea: IDH 2019 (×100). Ordenado de mayor a menor pobreza.</p><div style="position:relative;height:{max(260, 34 * len(r['provincias']))}px"><canvas id="chProv"></canvas></div></div></section>""")

    crit = ''.join(f'<tr><td><a href="../../?u={x["u"]}">{esc(x["d"])}</a></td><td>{esc(x["prov"])}</td><td class="n">{f1(x["t"])}%</td><td class="n">{f1(x["e"])}%</td><td class="n">{fidh(x["i"])}</td></tr>' for x in r['criticos'])
    best = ''.join(f'<tr><td><a href="../../?u={x["u"]}">{esc(x["d"])}</a></td><td>{esc(x["prov"])}</td><td class="n">{fidh(x["i"])}</td><td class="n">{f1(x["t"])}%</td></tr>' for x in r['mejores'])
    out.append(f"""<section class="grid2"><div class="card scroll"><h2>🚨 Distritos con mayor pobreza</h2><table class="tbl"><thead><tr><th>Distrito</th><th>Provincia</th><th>Pobreza</th><th>Extrema</th><th>IDH</th></tr></thead><tbody>{crit}</tbody></table></div>
<div class="card scroll"><h2>🏅 Distritos con mayor IDH</h2><table class="tbl"><thead><tr><th>Distrito</th><th>Provincia</th><th>IDH</th><th>Pobreza</th></tr></thead><tbody>{best}</tbody></table></div></section>""")

    # Todos los distritos
    by = {}
    for x in r['distritos']: by.setdefault(x['prov'], []).append(x)
    lst = ''.join(f'<details style="margin:8px 0"><summary>{esc(p)} ({len(v)})</summary><div class="chips" style="margin-top:8px">'
                  + ''.join(f'<a href="../../?u={x["u"]}">{esc(x["d"])}</a>' for x in v) + '</div></details>' for p, v in by.items())
    out.append(ranking_section(r, regiones))
    out.append(f'<section><h2>📍 Todos los distritos</h2><p class="desc">Abre cualquier distrito en el gemelo digital (diagnóstico, prospectiva 2075 y planes descargables).</p><div class="card">{lst}</div></section>')

    data = {'years': ENAHO['years'], 'pob': ps, 'pobNac': nac['pobreza_serie'],
            'an': [an.get(f'y{y}') for y in range(2021, 2026)] if an else [],
            'anNac': [en['anemia'].get(f'y{y}') for y in range(2021, 2026)],
            'prov': [[p['prov'], p['t'], p['i']] for p in sorted(r['provincias'], key=lambda p: -(p['t'] or 0))]}
    out.append(f"""<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script><script>
const D={json.dumps(data)},css=getComputedStyle(document.documentElement),c1=css.getPropertyValue('--h1').trim(),mut='#8b9bc4',grid='rgba(139,155,196,.15)';
Chart.defaults.color=mut;Chart.defaults.font.family='Inter,system-ui,sans-serif';
const opt={{responsive:true,plugins:{{legend:{{position:'bottom'}}}},scales:{{y:{{grid:{{color:grid}},ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}},spanGaps:true}};
if(D.pob&&D.pob.length)new Chart(document.getElementById('chPob'),{{type:'line',data:{{labels:D.years,datasets:[{{label:{json.dumps(nombre)},data:D.pob,borderColor:c1,backgroundColor:c1,borderWidth:3,tension:.3}},{{label:'Perú',data:D.pobNac,borderColor:mut,borderDash:[5,4],borderWidth:2,pointRadius:0,tension:.3}}]}},options:opt}});
if(D.prov&&D.prov.length)new Chart(document.getElementById('chProv'),{{data:{{labels:D.prov.map(p=>p[0]),datasets:[{{type:'bar',label:'Pobreza %',data:D.prov.map(p=>p[1]),backgroundColor:c1,borderRadius:5,xAxisID:'x',order:2}},{{type:'line',label:'IDH ×100',data:D.prov.map(p=>p[2]),borderColor:'#93c5fd',backgroundColor:'#93c5fd',showLine:false,pointRadius:6,pointBorderColor:'#0a0f1e',pointBorderWidth:2,xAxisID:'x',order:1}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},scales:{{x:{{grid:{{color:grid}},beginAtZero:true}},y:{{grid:{{display:false}}}}}}}}}});
if(D.an&&D.an.length)new Chart(document.getElementById('chAn'),{{type:'bar',data:{{labels:['2021','2022','2023','2024','2025'],datasets:[{{label:{json.dumps(nombre)},data:D.an,backgroundColor:c1,borderRadius:6}},{{label:'Perú',data:D.anNac,backgroundColor:'rgba(139,155,196,.45)',borderRadius:6}}]}},options:opt}});
</script>""")
    out.append(footer())
    return '\n'.join(out), desc

RANKS = None
def ranking_section(r, regiones):
    cards = []
    for key, lab, get, up, uni, fuente in RANK_IND:
        lst = RANKS[key]
        pos = next((i for i, (d, _) in enumerate(lst) if d == r['dep']), None)
        if pos is None: continue
        v = lst[pos][1]; n = len(lst)
        lo, hi = min(x[1] for x in lst), max(x[1] for x in lst)
        dots = ''.join(f'<i title="{esc(regiones[d]["nombre"])}: {f1(val)}" style="left:{(val - lo) / (hi - lo or 1) * 100:.1f}%"{" class=me" if d == r["dep"] else ""}></i>' for d, val in lst)
        tercio = 'top' if pos < n / 3 else ('mid' if pos < 2 * n / 3 else 'low')
        val = f'S/ {fmt(v)}' if uni == 'S/' else f'{f1(v)}%'
        cards.append(f'<div class="rk {tercio}"><div class="rk-h"><span>{esc(lab)}</span><b>{val}</b></div>'
                     f'<div class="rk-pos">Puesto <b>{pos + 1}</b> de {n} <small>({"1 = mejor" if True else ""} · {fuente})</small></div>'
                     f'<div class="strip">{dots}</div><div class="rk-ax"><span>{f1(lo) if uni != "S/" else fmt(lo)}</span><span>{"mejor →" if up else "← mejor"}</span><span>{f1(hi) if uni != "S/" else fmt(hi)}</span></div></div>')
    return (f'<section><h2>🏆 ¿Cómo se ubica {esc(r["nombre"])} entre las regiones?</h2><p class="desc">Cada punto es una región; el punto grande es {esc(r["nombre"])}. '
            f'Puesto 1 = mejor situación. Verde: tercio superior · ámbar: medio · rojo: tercio inferior. Lima = Lima Metropolitana.</p>'
            f'<div class="rkgrid">{"".join(cards)}</div></section>')

def memoria(regiones, nac):
    """Memoria del chatbot: hechos verificados en texto compacto, por región + nacional + rankings."""
    def line(r):
        e = r['endes']; c = r['censo2025'] or {}; ps = r['pobreza_serie'] or []
        g = lambda k: (e.get(k) or {}).get('y2025')
        parts = [f"{r['nombre']} ({r['natural']}, capital {r['capital']}, {r['n_prov']} provincias, {r['n_dist']} distritos)"]
        if c.get('pob'): parts.append(f"población Censo 2025 {fmt(c['pob'])}" + (f" (crec. {f1(c['crec'])}%/año 2017-2025)" if c.get('crec') is not None else ''))
        elif c.get('pob_lima_metropolitana'): parts.append(f"Lima Metropolitana Censo 2025 {fmt(c['pob_lima_metropolitana'])}")
        if ps: parts.append(f"pobreza monetaria 2025 {f1(ps[-1])}% (2024 {f1(ps[-2])}%, 2019 {f1(ps[3])}%, 2020 {f1(ps[4])}%)")
        if r['ingreso_real']: parts.append(f"ingreso real per cápita 2025 S/ {fmt(r['ingreso_real'][-1])}/mes")
        for k, lab in (('anemia', 'anemia 6-35m'), ('dci', 'desnutrición crónica <5'), ('vacunas12m', 'vacunas completas <12m'),
                       ('cred', 'CRED <36m'), ('hierro', 'hierro 6-35m'), ('lactancia', 'lactancia exclusiva'), ('saneamiento', 'saneamiento básico'),
                       ('violencia', 'violencia de pareja alguna vez'), ('tgf', 'fecundidad (hijos/mujer)')):
            v = e.get(k)
            if v: parts.append(f"{lab} {f1(v['y2025'])}{'' if k == 'tgf' else '%'} (2024 {f1(v['y2024'])})")
        for k, lab in (('agua', 'agua red pública en vivienda'), ('desague', 'desagüe red pública'), ('luz', 'electricidad'), ('internet', 'internet')):
            if c.get(k) is not None: parts.append(f"Censo 2025 {lab} {f1(c[k])}%")
        parts.append(f"IDH 2019 ponderado {fidh(r['idh2019'])}")
        if r['criticos']: parts.append('distritos con mayor pobreza: ' + ', '.join(f"{x['d']} ({f1(x['t'])}%)" for x in r['criticos'][:3]))
        return '; '.join(parts) + '.'
    reg = {r['dep']: {'nombre': r['nombre'], 'slug': r['slug'], 'texto': line(r)} for r in regiones.values()}
    reg['Cusco']['texto'] += (' Detalle Censo 2025 Cusco: 639 942 viviendas, 55,1% paredes de adobe; cocinan con leña 213 mil hogares y bosta 78 mil; '
                              'internet 52,8%; esperanza de vida 75,0 años; La Convención crece 3,5%/año y Acomayo -0,6%; San Sebastián (124 mil) y Cusco (97 mil) son los distritos más poblados; '
                              'emigran sobre todo a Arequipa (36,3%). Machu Picchu: >1,17 millones de visitantes ene-sep 2025; aforo 5 600/día en temporada alta.')
    rk = {}
    for key, lab, get, up, uni, fuente in RANK_IND:
        lst = RANKS[key]
        rk[key] = {'etiqueta': lab, 'fuente': fuente, 'mejor_es': 'mayor' if up else 'menor',
                   'orden_mejor_a_peor': [f"{regiones[d]['nombre']} {('S/ ' + fmt(v)) if uni == 'S/' else f1(v) + '%'}" for d, v in lst]}
    ne = nac['endes']
    nac_txt = (f"Perú: población Censo 2025 {fmt(nac['censo2025']['pob'])} (crec. 1,11%/año); pobreza monetaria 2025 {f1(nac['pobreza_serie'][-1])}% "
               f"(2024 {f1(nac['pobreza_serie'][-2])}%); pobreza extrema 2025 4,7%; ingreso real {fmt(nac['ingreso_real'][-1])} S/ al mes; anemia 6-35m {f1(ne['anemia']['y2025'])}%; "
               f"desnutrición crónica {f1(ne['dci']['y2025'])}%; vacunas <12m {f1(ne['vacunas12m']['y2025'])}%; CRED {f1(ne['cred']['y2025'])}%; hierro {f1(ne['hierro']['y2025'])}%; "
               f"violencia de pareja {f1(ne['violencia']['y2025'])}%.")
    return {'generado': date.today().isoformat(), 'nacional': nac_txt, 'regiones': reg, 'rankings': rk,
            'reglas': ['Usa SOLO estas cifras como datos reales; si no está, di que no hay dato oficial.',
                       'ENDES/ENAHO son estimaciones departamentales (no distritales).',
                       'Anemia según directriz OMS 2024 (RM 251-2024-MINSA).',
                       'Lima en ENDES/ENAHO = Lima Metropolitana.',
                       'Índices de seguridad, educación, etc. del distrito son ILUSTRATIVOS.'],
            'fuentes': ['INEI ENDES 2025 (Programas Presupuestales)', 'INEI Evolución de la Pobreza Monetaria 2016-2025',
                        'INEI Censos Nacionales 2025 (notas departamentales)', 'PNUD IDH 2019', 'INEI Censo 2017']}

def cusco_section():
    x = CUSCO['censo2025']
    def bars(dct, unit='%'):
        mx = max(dct.values())
        return ''.join(f'<div style="margin:8px 0"><div style="display:flex;justify-content:space-between"><span>{esc(k)}</span><b>{f1(v) if unit == "%" else fmt(v) + " mil"}{unit if unit == "%" else ""}</b></div>'
                       f'<div class="bar"><i style="width:{v / mx * 100:.0f}%"></i></div></div>' for k, v in dct.items())
    tur = ''.join(f'<li style="margin:6px 0">{esc(t["dato"])} — <a href="{t["url"]}">{esc(t["fuente"])}</a></li>' for t in CUSCO['turismo'])
    ed = x['educ']
    return f"""<section class="card special"><h2>☀️ Cusco a fondo — Censo 2025</h2>
<p class="desc">Detalle oficial presentado por INEI en Cusco el 4 de agosto de 2026. Esta sección amplía la carátula con vivienda, energía, migración y educación.</p>
<div class="kpis" style="margin:10px 0 18px;padding:0">
<div class="kpi"><div class="l">Viviendas particulares</div><div class="v">{fmt(x['viviendas'])}</div><div class="s">{f1(x['viv_ocupadas'])}% ocupadas · {f1(x['viv_ocasional'])}% uso ocasional</div></div>
<div class="kpi"><div class="l">Paredes de adobe</div><div class="v">{f1(x['paredes_adobe'])}%</div><div class="s">ladrillo {f1(x['paredes_ladrillo'])}% · riesgo sísmico</div></div>
<div class="kpi"><div class="l">Adultos mayores (60+)</div><div class="v">{f1(x['edad_60mas'])}%</div><div class="s">0-14 años: {f1(x['edad_0_14'])}% · índice envejec. 62,7</div></div>
<div class="kpi"><div class="l">Esperanza de vida</div><div class="v">75,0</div><div class="s">años al nacer</div></div>
<div class="kpi"><div class="l">Hogares con computadora</div><div class="v">{f1(x['computadora'])}%</div><div class="s">celular {f1(x['celular'])}% · Internet 52,8%</div></div></div>
<div class="grid2">
<div><h3 style="margin-bottom:6px">🔥 ¿Con qué cocinan los hogares? (miles)</h3>{bars(x['cocina_hogares_miles'], 'mil')}
<p class="desc" style="margin-top:8px">Más de <b>290 mil hogares</b> aún cocinan con leña, bosta o carbón: humo intradomiciliario, salud respiratoria y anemia van de la mano.</p></div>
<div><h3 style="margin-bottom:6px">🎓 Nivel educativo según edad</h3>{bars({'Inicial (3-5 años)': ed['inicial_3_5'], 'Primaria (6-11)': ed['primaria_6_11'], 'Secundaria (12-17)': ed['secundaria_12_17'], 'Superior universitaria (18-26)': ed['sup_univ_18_26'], 'Superior no universitaria (18-26)': ed['sup_no_univ_18_26']})}</div>
<div><h3 style="margin-bottom:6px">🧭 ¿De dónde llegan? (inmigrantes 2020-2025)</h3>{bars(x['inmigrantes_origen'])}</div>
<div><h3 style="margin-bottom:6px">🚌 ¿A dónde se van? (emigrantes 2020-2025)</h3>{bars(x['emigrantes_destino'])}</div></div>
<div class="grid2" style="margin-top:14px">
<div><h3>📈 Dinámica territorial</h3><ul style="margin:8px 0 0 18px"><li><b>La Convención</b> ({fmt(x['prov_mayor_crec']['pob'])} hab.) es la provincia que más crece: {f1(x['prov_mayor_crec']['crec'])}% anual.</li>
<li><b>Acomayo</b> pierde población: {f1(x['prov_decrec']['crec'])}% anual.</li><li>Distritos más poblados: <b>San Sebastián</b> (124 mil) y <b>Cusco</b> (97 mil).</li></ul></div>
<div><h3>🏔️ Turismo — Machu Picchu</h3><ul style="margin:8px 0 0 18px">{tur}</ul></div></div>
<p class="src" style="margin-top:12px">Fuente principal: <a href="{x['url']}">INEI — Población de Cusco registró 1 millón 379 mil habitantes según los Censos Nacionales 2025</a>.</p></section>"""

def page_index(regiones, nac):
    url = f'{SITE}region/'
    title = 'Las 25 regiones del Perú en 2025 | Proyecto INTI'
    desc = 'Carátula de cada región del Perú con datos oficiales 2025: pobreza (ENAHO), anemia y desnutrición (ENDES), Censo 2025 y brechas por provincia y distrito.'
    out = [head(title, desc, url), nav(regiones, None, depth=1)]
    out.append(f"""<header class="cover" style="min-height:260px">{INCA}<div class="emb">🇵🇪</div><div class="kicker">Proyecto INTI · Regiones</div><h1>Las 25 regiones</h1>
<p class="lead">Una carátula por región con los indicadores oficiales más recientes. Perú 2025: pobreza {f1(nac['pobreza_serie'][-1])}% · anemia infantil {f1(nac['endes']['anemia']['y2025'])}% · {fmt(nac['censo2025']['pob'])} habitantes (Censo 2025).</p></header>""")
    cards = []
    for r in sorted(regiones.values(), key=lambda r: (r['dep'] != 'Cusco', r['nombre'])):
        h1, h2 = SPECIAL_HUES.get(r['dep'], HUES.get(r['natural'], ('#f5a623', '#ff7a18')))
        ps = r['pobreza_serie'] or [None]; an = (r['endes'].get('anemia') or {}).get('y2025')
        star = ' ★ destacada' if r['dep'] == 'Cusco' else ''
        cards.append(f'<a class="rcard" href="{r["slug"]}/"><div class="top" style="background:linear-gradient(135deg,{h1},{h2})"><em>{"☀️" if r["dep"] == "Cusco" else EMOJI.get(r["natural"], "🌞")}</em>'
                     f'<small style="opacity:.85;font-weight:700;text-transform:uppercase;font-size:.68rem;letter-spacing:1.5px">{esc(r["natural"] or "")}{star}</small><b>{esc(r["nombre"])}</b></div>'
                     f'<div class="bot"><span>Pobreza <b style="color:var(--txt)">{f1(ps[-1])}%</b></span><span>Anemia <b style="color:var(--txt)">{f1(an)}%</b></span>'
                     f'<span>{r["n_prov"]} provincia{"s" if r["n_prov"] != 1 else ""}</span><span>{r["n_dist"]} distritos</span></div></a>')
    out.append(f'<section><div class="rgrid">{"".join(cards)}</div></section>')
    out.append('<p class="src">Pobreza: INEI ENAHO 2025 (Lima = Lima Metropolitana). Anemia 6-35 meses: INEI ENDES 2025 (directriz OMS 2024).</p>')
    out.append(footer(depth=1))
    return '\n'.join(out)

def main():
    global RANKS
    regiones, nac = build()
    RANKS = rankings(regiones)
    for r in regiones.values():
        r['ranks'] = {k: next((i + 1 for i, (d, _) in enumerate(lst) if d == r['dep']), None) for k, lst in RANKS.items()}
    json.dump(memoria(regiones, nac), open(D('data/memoria_chat.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # JSON consumido por el dashboard (sin listas pesadas)
    slim = {k: {kk: vv for kk, vv in v.items() if kk not in ('distritos',)} for k, v in regiones.items()}
    json.dump({'generado': date.today().isoformat(), 'nacional': nac, 'regiones': slim, 'indicadores': [{'k': k, 'l': l, 'up': up, 'u': u, 'f': f} for k, l, _, up, u, f in RANK_IND],
               'fuentes': {'endes': 'INEI ENDES 2025 — Indicadores de Resultados de los Programas Presupuestales',
                           'enaho': 'INEI — Perú: Evolución de la Pobreza Monetaria 2016-2025',
                           'censo': CENSO['_meta']['fuente']}},
              open(D('data/regiones.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    urls = [SITE, SITE + 'region/']
    os.makedirs(D('region'), exist_ok=True)
    open(D('region/index.html'), 'w', encoding='utf-8').write(page_index(regiones, nac))
    for r in regiones.values():
        os.makedirs(D('region', r['slug']), exist_ok=True)
        html_, _ = page_region(r, nac, regiones)
        open(D('region', r['slug'], 'index.html'), 'w', encoding='utf-8').write(html_)
        urls.append(f'{SITE}region/{r["slug"]}/')
    today = date.today().isoformat()
    sm = ''.join(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>{"1.0" if u == SITE else ("0.9" if "cusco" in u else "0.8")}</priority></url>\n' for u in urls)
    open(D('sitemap.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n')
    print(f'OK: {len(regiones)} regiones → region/*/index.html + data/regiones.json + sitemap ({len(urls)} URLs)')

if __name__ == '__main__':
    main()
