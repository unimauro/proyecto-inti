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
TAX = load('data/fuentes/sunat_recaudacion_departamentos.json')
EVN = load('data/fuentes/inei_evn_tmi_departamentos.json')
CNV = load('data/fuentes/cnv_nacimientos_2026.json')
SINADEF = load('data/fuentes/sinadef_defunciones_departamentos.json')
ENLA = load('data/fuentes/enla2024_regiones.json')
COMP = load('data/fuentes/compendio2025_salud_nacimientos.json')
CANON = load('data/fuentes/mef_canon_departamentos.json') if os.path.exists(D('data/fuentes/mef_canon_departamentos.json')) else None
EMP = load('data/fuentes/empresas_canon.json')
CANON_ENT = load('data/fuentes/mef_canon_departamentos_entidades.json') if os.path.exists(D('data/fuentes/mef_canon_departamentos_entidades.json')) else None
DET = load('data/fuentes/mef_gasto_detalle.json') if os.path.exists(D('data/fuentes/mef_gasto_detalle.json')) else None
PROV_BY4 = {o['u'][:4]: prov for dep, pv in TER.items() for prov, arr in pv.items() for o in arr}
UBI = {o['u']: (dep, prov, o['d']) for dep, pv in TER.items() for prov, arr in pv.items() for o in arr}
MEF = load('data/fuentes/mef_gasto_departamentos.json') if os.path.exists(D('data/fuentes/mef_gasto_departamentos.json')) else None

def pick(dct, dep, alias=None):
    """Busca el departamento en un dict de otra fuente (tolerante a tildes/mayúsculas/alias)."""
    want = {norm(dep), norm(NOMBRE.get(dep, dep))} | {norm(a) for a in (alias or [])}
    for k, v in dct.items():
        if norm(k) in want: return v
    return None
CALLAO_AL = ['Prov. Const. del Callao', 'Prov. Constitucional del Callao', 'Provincia Constitucional del Callao', 'Callao']

def extra(dep, pob):
    """Indicadores de fuentes adicionales: impuestos, gasto público, salud, nacimientos, defunciones, lectura, EVN."""
    al = CALLAO_AL if dep == 'Callao' else None
    x = {}
    # Recaudación SUNAT (millones S/, por domicilio fiscal). Lima = Lima Metropolitana + Lima provincias.
    ta = TAX['anual']
    if dep == 'Lima':
        a, b = ta.get('Lima Metropolitana', {}), ta.get('Lima provincias', {})
        x['tax'] = {y: round(a.get(y, 0) + b.get(y, 0), 1) for y in a}
    else:
        x['tax'] = pick(ta, dep, al)
    if MEF:
        g = pick(MEF['departamentos'], dep, al)
        if g: x['gasto'] = g
    if CANON:
        cn = pick(CANON['departamentos'], dep, al)
        if cn:
            x['canon'] = cn
            if pob and cn.get('2025'): x['canon_pc'] = round(cn['2025']['total_canon'] / pob)
    ev = EVN['esperanza_vida']; tm = EVN['mortalidad_infantil_x1000']
    x['evn'] = pick(ev, dep, al); x['tmi'] = pick(tm, dep, al)
    x['cnv2026'] = pick(CNV['v'], dep, al)
    x['def'] = {y: pick(v, dep, al) for y, v in SINADEF['v'].items()}
    x['tasa_def'] = {y: pick(v, dep, al) for y, v in SINADEF['tasa_x100mil'].items() if v}
    en = ENLA['v']
    x['enla'] = pick(en, 'LIMA METROPOLITANA' if dep == 'Lima' else dep, al)
    cv = COMP
    x['camas'] = pick(cv['camas']['v'], dep, al); x['medicos'] = pick(cv['medicos']['v'], dep, al)
    x['hab_medico'] = pick(cv['hab_por_medico']['v'], dep, al); x['nac_insc'] = pick(cv['nacimientos_inscritos']['v'], dep, al)
    if x['camas'] and pob: x['camas_10k'] = round(x['camas'][-1] / pob * 10000, 1)
    if x['tax'] and pob: x['tax_pc'] = round(x['tax'].get('2025', 0) * 1e6 / pob)
    if x.get('gasto') and pob and x['gasto'].get('2025'): x['gasto_pc'] = round(x['gasto']['2025']['dev'] / pob)
    if x.get('gasto') and x['tax'] and x['tax'].get('2025'):
        x['retorno'] = round(x['gasto']['2025']['dev'] / (x['tax']['2025'] * 1e6), 2)
    return x

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
    ('lectura', 'Lectura satisfactoria (4.° prim.)', lambda r: ((r['x'].get('enla') or {}).get('lectura') or {}).get('satisfactorio'), True, '%', 'ENLA 2024'),
    ('matematica', 'Matemática satisfactoria (4.° prim.)', lambda r: ((r['x'].get('enla') or {}).get('matematica') or {}).get('satisfactorio'), True, '%', 'ENLA 2024'),
    ('camas_10k', 'Camas hospitalarias x 10 mil hab.', lambda r: r['x'].get('camas_10k'), True, '', 'MINSA 2024'),
    ('hab_medico', 'Habitantes por médico', lambda r: (r['x'].get('hab_medico') or [None])[-1], False, '', 'CMP/INEI 2024'),
    ('evn', 'Esperanza de vida al nacer', lambda r: (r['x'].get('evn') or [None])[0], True, 'años', 'INEI 2020-25'),
    ('tmi', 'Mortalidad infantil (x mil)', lambda r: (r['x'].get('tmi') or [None])[0], False, '', 'INEI 2020-25'),
    ('canon_pc', 'Canon y regalías por habitante', lambda r: r['x'].get('canon_pc'), None, 'S/', 'MEF 2025'),
    ('tax_pc', 'Recaudación SUNAT por habitante', lambda r: r['x'].get('tax_pc'), None, 'S/', 'SUNAT/BCRP 2025'),
    ('gasto_pc', 'Gasto público por habitante', lambda r: r['x'].get('gasto_pc'), None, 'S/', 'MEF 2025'),
    ('retorno', 'Gasto público / recaudación', lambda r: r['x'].get('retorno'), None, 'x', 'MEF y SUNAT 2025'),
]

def rankings(regiones):
    """{clave: [(dep, valor), ...] ordenado de MEJOR a PEOR}"""
    out = {}
    for key, _, get, up, *_ in RANK_IND:
        vals = [(d, get(r)) for d, r in regiones.items() if get(r) is not None]
        out[key] = sorted(vals, key=lambda x: -x[1] if up in (True, None) else x[1])
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
        c25 = CENSO.get(dep) or {}
        reg['pob_ref'] = c25.get('pob') or reg['pob25_est']
        reg['pob_ref_fuente'] = 'Censo 2025' if c25.get('pob') else 'estimación 2025'
        reg['x'] = extra(dep, reg['pob_ref'])
        if dep == 'Lima':
            reg['endes_lima_prov'] = {k: ENDES[k]['v'].get('Departamento de Lima') for k, *_ in ENDES_IND}
            reg['pobreza_lima_prov'] = ENAHO['pobreza'].get('Lima')
        rk = [i for i, (k, _) in enumerate(ranking_pob) if k == nk]
        reg['rank_pobreza'] = (rk[0] + 1, len(ranking_pob)) if rk else None
        regiones[dep] = reg
    nac = {'endes': {k: ENDES[k]['v'].get('Total') for k, *_ in ENDES_IND}, 'pobreza_serie': ENAHO['pobreza']['Nacional'],
           'gasto_real': ENAHO['gasto_real']['Nacional'], 'ingreso_real': ENAHO['ingreso_real']['Nacional'],
           'censo2025': CENSO['_meta']['nacional']}
    npob = CENSO['_meta']['nacional']['pob']
    nx = {'tax': TAX['anual']['Total'], 'evn': pick(EVN['esperanza_vida'], 'Perú'), 'tmi': pick(EVN['mortalidad_infantil_x1000'], 'Perú'),
          'enla': ENLA['v'].get('NACIONAL'), 'camas': COMP['camas']['v'].get('Total'), 'medicos': COMP['medicos']['v'].get('Total'),
          'hab_medico': COMP['hab_por_medico']['v'].get('Total'), 'nac_insc': COMP['nacimientos_inscritos']['v'].get('Total'),
          'cnv2026': sum(CNV['v'].values()), 'def': {y: sum(v.values()) for y, v in SINADEF['v'].items()}}
    nx['camas_10k'] = round(nx['camas'][-1] / npob * 10000, 1)
    nx['tax_pc'] = round(nx['tax']['2025'] * 1e6 / npob)
    if MEF:
        nx['gasto'] = MEF['total']; nx['gasto_pc'] = round(MEF['total']['2025']['dev'] / npob) if MEF['total'].get('2025') else None
        nx['retorno'] = round(MEF['total']['2025']['dev'] / (nx['tax']['2025'] * 1e6), 2) if MEF['total'].get('2025') else None
    if CANON:
        nx['canon'] = CANON['total']; nx['canon_pc'] = round(CANON['total']['2025']['total_canon'] / npob)
    nac['x'] = nx
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
.stack{display:flex;height:16px;border-radius:99px;overflow:hidden;margin-top:6px}.stack i{display:block;height:100%}
.apoyo{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:linear-gradient(135deg,rgba(245,166,35,.12),rgba(255,122,24,.06));border:1px solid rgba(245,166,35,.35);border-radius:16px;padding:14px 16px;margin-bottom:16px;color:var(--txt)}
.apoyo span{color:var(--muted);font-size:.84rem}.apoyo-btns{display:flex;gap:8px;flex-wrap:wrap}
.ab{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;font-weight:700;font-size:.84rem;border:1px solid var(--line);background:var(--card2);color:var(--txt)}
.ab.cafe{background:#ffdd00;color:#1a1206;border-color:#ffdd00}.ab.paypal{background:#0070ba;color:#fff;border-color:#0070ba}.ab.yape{background:#742284;color:#fff;border-color:#742284}
.faq details{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:10px 0}.faq details p,.faq details ul{margin-top:8px;color:var(--muted)}.faq li{margin:4px 0 4px 18px}
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
            f'<span><a href="{up}region/">Todas las regiones</a> · <a href="{up}fuentes/">FAQ</a> · <select aria-label="Ir a región" onchange="location.href=this.value">'
            f'<option value="{up}region/">Elegir región…</option>{opts}</select></span></nav>')

APOYO = {'yape': '940584307', 'plin': '940584307', 'paypal': 'https://www.paypal.com/paypalme/unimauro', 'cafe': 'https://buymeacoffee.com/unimauro'}

def apoyo_html():
    return f"""<div class="apoyo"><div><b>💛 Apoya este proyecto</b><br><span>Proyecto abierto y sin fines de lucro. Tu apoyo cubre hosting, datos y el tiempo de mantenerlo vivo.</span></div>
<div class="apoyo-btns"><a class="ab cafe" href="{APOYO['cafe']}" target="_blank" rel="noopener">☕ Invítame un café</a>
<a class="ab paypal" href="{APOYO['paypal']}" target="_blank" rel="noopener">💳 PayPal</a>
<span class="ab yape" title="Yape / Plin">📱 Yape / Plin: <b>{APOYO['yape']}</b></span></div></div>"""

def footer(depth=2):
    up = '../' * depth
    return f"""<footer>{apoyo_html()}<div>Proyecto INTI — Gemelo Digital del Perú 2075 · <a href="{up}">Dashboard</a> · <a href="{up}region/">Regiones</a> ·
<a href="{up}fuentes/">❓ FAQ y fuentes de datos</a> · <a href="https://github.com/unimauro/proyecto-inti">Código y datos</a> · Carlos Cárdenas Fernández (dirección, tecnología y datos)</div>
<div class="src" style="margin-top:8px">Regla del proyecto: <b>no inventamos cifras</b>. Cada dato indica fuente y año; los datos departamentales de encuestas (ENDES/ENAHO) son estimaciones muestrales con intervalo de confianza.
Generado el {date.today().isoformat()}.</div></footer></div><script src="{up}assets/nav.js"></script></body></html>"""

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
    out.append(fiscal_section(r, nac))
    out.append(fuentes_fin_section(r, nac))
    out.append(canon_section(r, nac))
    out.append(camisea_section(r, nac, regiones))
    out.append(empresas_section(r))
    out.append(canon_receptores_section(r))
    out.append(flujo_canon_section(r))
    out.append(gasto_en_que_section(r))
    out.append(salud_vida_section(r, nac))
    out.append(lectura_section(r, nac))
    out.append(ranking_section(r, regiones))
    out.append(f'<section><h2>📍 Todos los distritos</h2><p class="desc">Abre cualquier distrito en el gemelo digital (diagnóstico, prospectiva 2075 y planes descargables).</p><div class="card">{lst}</div></section>')

    X = r['x']; TY = [str(y) for y in range(2015, 2027)]
    data = {'years': ENAHO['years'], 'pob': ps, 'pobNac': nac['pobreza_serie'],
            'ty': TY, 'tax': [(X.get('tax') or {}).get(y) for y in TY],
            'gas': [round(((X.get('gasto') or {}).get(y) or {}).get('dev', 0) / 1e6, 1) or None for y in TY] if X.get('gasto') else [],
            'camY': COMP['camas']['years'], 'cam': X.get('camas') or [],
            'defY': sorted(X['def']), 'def': [X['def'][y] for y in sorted(X['def'])],
            'nacY': COMP['nacimientos_inscritos']['years'], 'nac': X.get('nac_insc') or [],
            'enlaY': ['2016', '2018', '2019', '2022', '2023', '2024'],
            'lec': [(((X.get('enla') or {}).get('lectura') or {}).get('historico') or {}).get(y) for y in ['2016', '2018', '2019', '2022', '2023', '2024']],
            'mat': [(((X.get('enla') or {}).get('matematica') or {}).get('historico') or {}).get(y) for y in ['2016', '2018', '2019', '2022', '2023', '2024']],
            'an': [an.get(f'y{y}') for y in range(2021, 2026)] if an else [],
            'anNac': [en['anemia'].get(f'y{y}') for y in range(2021, 2026)],
            'prov': [[p['prov'], p['t'], p['i']] for p in sorted(r['provincias'], key=lambda p: -(p['t'] or 0))]}
    out.append(f"""<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script><script src="https://cdn.jsdelivr.net/npm/chartjs-chart-sankey@0.14.0/dist/chartjs-chart-sankey.min.js"></script><script>
const D={json.dumps(data)},css=getComputedStyle(document.documentElement),c1=css.getPropertyValue('--h1').trim(),mut='#8b9bc4',grid='rgba(139,155,196,.15)';
Chart.defaults.color=mut;Chart.defaults.font.family='Inter,system-ui,sans-serif';
const opt={{responsive:true,plugins:{{legend:{{position:'bottom'}}}},scales:{{y:{{grid:{{color:grid}},ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}},spanGaps:true}};
if(D.pob&&D.pob.length)new Chart(document.getElementById('chPob'),{{type:'line',data:{{labels:D.years,datasets:[{{label:{json.dumps(nombre)},data:D.pob,borderColor:c1,backgroundColor:c1,borderWidth:3,tension:.3}},{{label:'Perú',data:D.pobNac,borderColor:mut,borderDash:[5,4],borderWidth:2,pointRadius:0,tension:.3}}]}},options:opt}});
if(D.prov&&D.prov.length)new Chart(document.getElementById('chProv'),{{data:{{labels:D.prov.map(p=>p[0]),datasets:[{{type:'bar',label:'Pobreza %',data:D.prov.map(p=>p[1]),backgroundColor:c1,borderRadius:5,xAxisID:'x',order:2}},{{type:'line',label:'IDH ×100',data:D.prov.map(p=>p[2]),borderColor:'#93c5fd',backgroundColor:'#93c5fd',showLine:false,pointRadius:6,pointBorderColor:'#0a0f1e',pointBorderWidth:2,xAxisID:'x',order:1}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},scales:{{x:{{grid:{{color:grid}},beginAtZero:true}},y:{{grid:{{display:false}}}}}}}}}});
const ax=(cb)=>({{responsive:true,plugins:{{legend:{{position:'bottom'}}}},scales:{{y:{{grid:{{color:grid}},beginAtZero:true,ticks:{{callback:cb||(v=>v)}}}},x:{{grid:{{display:false}}}}}},spanGaps:true}});
const el=id=>document.getElementById(id);
if(el('chTax'))new Chart(el('chTax'),{{type:'bar',data:{{labels:D.ty.map(y=>y==='2026'?'2026*':y),datasets:[{{type:'bar',label:'Recaudación SUNAT (S/ millones)',data:D.tax,backgroundColor:c1,borderRadius:5,order:2}}].concat(D.gas.length?[{{type:'line',label:'Gasto público ejecutado en la región (S/ millones)',data:D.gas,borderColor:'#22c55e',backgroundColor:'#22c55e',borderWidth:3,tension:.25,order:1}}]:[])}},options:ax(v=>v.toLocaleString('es-PE'))}});
if(el('chCanon')&&window.__CANON)new Chart(el('chCanon'),{{type:'bar',data:{{labels:__CANON.y.map(y=>y==='2026'?'2026*':y),datasets:__CANON.ds.map(d=>Object.assign({{stack:'c',borderRadius:2}},d))}},options:{{responsive:true,plugins:{{legend:{{position:'bottom',labels:{{boxWidth:12}}}}}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,grid:{{color:grid}},ticks:{{callback:v=>v.toLocaleString('es-PE')}}}}}}}}}});
const SKC={{'T':'#f59e0b','R':'#3b82f6','F':'#a855f7','E':'#22c55e'}};const skCol=id=>id==='E:Sin gastar'?'#ef4444':(SKC[id[0]]||'#8b9bc4');
function skDraw(id,links){{if(!el(id)||!links||!links.length)return;const labels={{}};links.forEach(l=>{{labels[l.from]=l.from.slice(2);labels[l.to]=l.to.slice(2);}});
new Chart(el(id),{{type:'sankey',data:{{datasets:[{{data:links,labels,colorFrom:c=>skCol(c.raw.from),colorTo:c=>skCol(c.raw.to),colorMode:'gradient',color:'#e8edf7',size:'max',padding:10,font:{{size:11}}}}]}},
options:{{maintainAspectRatio:false,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+labels[c.raw.from]+' → '+labels[c.raw.to]+': S/ '+c.raw.flow.toLocaleString('es-PE')+' M'}}}}}}}}}});}}
if(window.__SK&&window.Chart&&Chart.registry.controllers.get('sankey')){{skDraw('skA',__SK.L1);skDraw('skB',__SK.L2);}}
if(el('chFF')&&window.__FF)new Chart(el('chFF'),{{type:'bar',data:{{labels:__FF.y.map(y=>y==='2026'?'2026*':y),datasets:__FF.ds.map(d=>Object.assign({{stack:'f'}},d))}},options:{{responsive:true,plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,font:{{size:10}}}}}}}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,grid:{{color:grid}},ticks:{{callback:v=>v.toLocaleString('es-PE')}}}}}}}}}});
if(el('chCamisea')&&window.__CAMISEA)new Chart(el('chCamisea'),{{type:'bar',data:{{labels:__CAMISEA.y.map(y=>y==='2026'?'2026*':y),datasets:[{{label:'Canon gasífero',data:__CAMISEA.gas,backgroundColor:'#ef4444',stack:'c',borderRadius:3}},{{label:'FOCAM',data:__CAMISEA.foc,backgroundColor:'#ec4899',stack:'c',borderRadius:3}}]}},options:{{responsive:true,plugins:{{legend:{{position:'bottom'}}}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,grid:{{color:grid}},ticks:{{callback:v=>v.toLocaleString('es-PE')+' M'}}}}}}}}}});
if(el('chCam')&&D.cam.length)new Chart(el('chCam'),{{type:'bar',data:{{labels:D.camY,datasets:[{{label:'Camas hospitalarias',data:D.cam,backgroundColor:'#3b82f6',borderRadius:4}}]}},options:ax()}});
if(el('chVit'))new Chart(el('chVit'),{{type:'line',data:{{labels:D.defY,datasets:[{{label:'Defunciones (SINADEF)',data:D.def,borderColor:'#ef4444',backgroundColor:'#ef4444',tension:.25}},{{label:'Nacimientos inscritos (RENIEC/INEI)',data:D.defY.map(y=>{{const i=D.nacY.indexOf(+y);return i>=0?D.nac[i]:null;}}),borderColor:'#22c55e',backgroundColor:'#22c55e',tension:.25}}]}},options:ax(v=>v.toLocaleString('es-PE'))}});
if(el('chEnla'))new Chart(el('chEnla'),{{type:'line',data:{{labels:D.enlaY,datasets:[{{label:'Lectura',data:D.lec,borderColor:c1,backgroundColor:c1,borderWidth:3,tension:.25}},{{label:'Matemática',data:D.mat,borderColor:'#93c5fd',backgroundColor:'#93c5fd',borderWidth:3,tension:.25}}]}},options:ax(v=>v+'%')}});
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
        tercio = '' if up is None else ('top' if pos < n / 3 else ('mid' if pos < 2 * n / 3 else 'low'))
        val = f'S/ {fmt(v)}' if uni == 'S/' else (f'{f1(v)}%' if uni == '%' else f'{f1(v)} {uni}'.strip())
        cards.append(f'<div class="rk {tercio}"><div class="rk-h"><span>{esc(lab)}</span><b>{val}</b></div>'
                     f'<div class="rk-pos">Puesto <b>{pos + 1}</b> de {n} <small>({"1 = mejor" if up is not None else "1 = mayor valor"} · {fuente})</small></div>'
                     f'<div class="strip">{dots}</div><div class="rk-ax"><span>{f1(lo) if uni != "S/" else fmt(lo)}</span><span>{"mejor →" if up else ("" if up is None else "← mejor")}</span><span>{f1(hi) if uni != "S/" else fmt(hi)}</span></div></div>')
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
        X = r['x']; t = X.get('tax') or {}
        if t: parts.append(f"recaudación SUNAT tributos internos 2025 S/ {fmt(t.get('2025', 0))} millones (S/ {fmt(X.get('tax_pc') or 0)} por habitante; 2024 S/ {fmt(t.get('2024', 0))} M; 2026 ene-{TAX['corte'].split('.')[0].lower()} S/ {fmt(t.get('2026', 0))} M; registrada por domicilio fiscal)")
        g = X.get('gasto') or {}
        if g.get('2025'): parts.append(f"gasto público ejecutado en la región 2025 S/ {fmt(g['2025']['dev'] / 1e6)} millones (S/ {f1(X['retorno'])} gastados por cada S/ 1 recaudado; canon/regalías S/ {fmt((g['2025'].get('canon') or 0) / 1e6)} M)")
        if g.get('2025') and g['2025'].get('rub_18') is not None:
            gg = g['2025']; parts.append(f"el gasto 2025 SÍ incluye canon: {f1(gg['rub_18'] / gg['dev'] * 100)}% financiado con canon/regalías, {f1(gg.get('rub_00', 0) / gg['dev'] * 100)}% con recursos ordinarios del Tesoro")
        if g.get('2026'): parts.append(f"gasto 2026 a {MEF['corte_2026']} S/ {fmt(g['2026']['dev'] / 1e6)} M de un PIM de S/ {fmt(g['2026']['pim'] / 1e6)} M")
        cn = (X.get('canon') or {}).get('2025') or {}
        if cn.get('total_canon'):
            det = ', '.join(f"{t['l']} S/ {fmt(cn[t['k']] / 1e6)} M" for t in CANON['tipos'] if t['k'] not in ('foncomun',) and cn.get(t['k'], 0) > 1e6)
            parts.append(f"canon, sobrecanon y regalías recibidos 2025 S/ {fmt(cn['total_canon'] / 1e6)} millones (S/ {fmt(X.get('canon_pc') or 0)} por habitante): {det}; Foncomun S/ {fmt((cn.get('foncomun') or 0) / 1e6)} M")
            tops = [e for e in _entidades(r) if e['y'].get('2025', 0) > 0][:3]
            if tops: parts.append('principales receptores de canon 2025: ' + ', '.join(f"{e['n'].title()} S/ {fmt(e['y']['2025'] / 1e6)} M" for e in tops))
            gas_f = (cn.get('gasifero') or 0) + (cn.get('focam') or 0)
            if gas_f > 1e6: parts.append(f"dinero de Camisea 2025 (canon gasífero + FOCAM) S/ {fmt(gas_f / 1e6)} M")
            c26 = (X['canon'].get('2026') or {}).get('total_canon')
            if c26: parts.append(f"canon y regalías 2026 a {CANON['corte_2026']} S/ {fmt(c26 / 1e6)} M")
        for e in [e for e in EMP['empresas'] if norm(r['dep']) in {norm(x) for x in e['regiones']}]:
            parts.append(f"empresa {e['nombre']}: " + '; '.join(f"{d['k']} {d['v']} ({d['f']})" for d in e['datos'][:3]))
        if X.get('camas'): parts.append(f"camas hospitalarias 2024 {fmt(X['camas'][-1])} ({f1(X.get('camas_10k'))} por 10 mil hab.)")
        if X.get('medicos'): parts.append(f"médicos colegiados 2024 {fmt(X['medicos'][-1])} ({fmt((X.get('hab_medico') or [0])[-1])} hab. por médico)")
        if X.get('evn'): parts.append(f"esperanza de vida 2020-25 {f1(X['evn'][0])} años (INEI proyección)")
        if X.get('tmi'): parts.append(f"mortalidad infantil 2020-25 {f1(X['tmi'][0])} por mil")
        if X.get('cnv2026'): parts.append(f"nacimientos 2026 (CNV, a {CNV['corte']}) {fmt(X['cnv2026'])}")
        if X['def'].get('2025'): parts.append(f"defunciones SINADEF 2025 {fmt(X['def']['2025'])}, 2026 ene-sep {fmt(X['def'].get('2026') or 0)}")
        en = X.get('enla') or {}
        if en: parts.append(f"ENLA 2024 4.° primaria: lectura satisfactoria {f1((en.get('lectura') or {}).get('satisfactorio'))}%, matemática {f1((en.get('matematica') or {}).get('satisfactorio'))}%")
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
        rk[key] = {'etiqueta': lab, 'fuente': fuente, 'mejor_es': 'mayor' if up else ('no aplica (orden de mayor a menor)' if up is None else 'menor'),
                   'orden_mejor_a_peor': [f"{regiones[d]['nombre']} {('S/ ' + fmt(v)) if uni == 'S/' else (f1(v) + ('%' if uni == '%' else (' ' + uni if uni else '')))}" for d, v in lst]}
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

def _kpi(l, v, s=''):
    return f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s">{s}</div></div>'

def fiscal_section(r, nac):
    X = r['x']; t = X.get('tax') or {}; nx = nac['x']
    if not t: return ''
    g = X.get('gasto') or {}
    m26 = TAX['meses_ultimo_anio']; corte = TAX['corte'].replace('.', ' ')
    k = [_kpi('Recaudación SUNAT 2025', f'S/ {fmt(t.get("2025", 0))} M', f'{f1(t["2025"] / nx["tax"]["2025"] * 100)}% del total nacional'),
         _kpi('Por habitante 2025', f'S/ {fmt(X.get("tax_pc") or 0)}', f'Perú S/ {fmt(nx["tax_pc"])} · pob. {r["pob_ref_fuente"]}'),
         _kpi(f'Recaudación 2026 (ene–{corte.split()[0].lower()})', f'S/ {fmt(t.get("2026", 0))} M', f'{m26} meses · corte {corte}')]
    if g.get('2025'):
        k.append(_kpi('Gasto público ejecutado 2025', f'S/ {fmt(g["2025"]["dev"] / 1e6)} M', 'Gobierno nacional + regional + locales'))
        k.append(_kpi('Gasto público por persona', f'S/ {fmt(X.get("gasto_pc") or 0)}', f'2025 · Perú S/ {fmt(nac["x"].get("gasto_pc") or 0)} · puesto {r.get("ranks", {}).get("gasto_pc", "—")} de 25'))
        k.append(_kpi('Por cada S/ 1 recaudado', f'S/ {f1(X["retorno"]).replace(",0", "")}', 'se gastó en la región (2025)'))
        if g.get('2026'):
            k.append(_kpi(f'Gasto 2026 (a {MEF["corte_2026"]})', f'S/ {fmt(g["2026"]["dev"] / 1e6)} M', f'PIM 2026: S/ {fmt(g["2026"]["pim"] / 1e6)} M'))
    rows = ''
    for y in [str(v) for v in range(2015, 2027)]:
        if y not in t: continue
        gy = g.get(y) or {}
        ratio = f'{f1(gy["dev"] / (t[y] * 1e6))}' if gy.get('dev') and t[y] else '—'
        cyr = (gy.get('canon') or 0) / 1e6
        rows += (f'<tr><td>{y}{"*" if y == "2026" else ""}</td><td class="n">{fmt(t[y])}</td><td class="n">{fmt(gy["dev"] / 1e6) if gy.get("dev") else "—"}</td>'
                 f'<td class="n">{fmt(cyr) if gy else "—"}</td><td class="n">{fmt((gy.get("foncomun") or 0) / 1e6) if gy else "—"}</td><td class="n">{ratio}</td></tr>')
    lima_note = ' En Lima se suman Lima Metropolitana y Lima Provincias.' if r['dep'] == 'Lima' else ''
    gasto_src = (f' Gasto: <a href="https://datosabiertos.mef.gob.pe/">MEF — Datos Abiertos, Gasto Devengado</a> (devengado por departamento donde se ejecuta la meta, 3 niveles de gobierno, '
                 f'sin transferencias entre entidades ni servicio de la deuda; 2026 a {MEF["corte_2026"]}).') if MEF else ' Gasto MEF: en proceso de carga.'
    return f"""<section><h2>💰 ¿Cuánto recauda {esc(r['nombre'])} y cuánto regresa?</h2>
<p class="desc">Barras: tributos internos recaudados por SUNAT en la región. Línea: gasto público total ejecutado en la región (todos los niveles de gobierno). Montos en millones de soles corrientes.</p>
<div class="kpis" style="margin:0 0 14px;padding:0">{''.join(k)}</div>
<div class="grid2"><div class="card"><canvas id="chTax" height="240"></canvas></div>
<div class="card scroll"><table class="tbl"><thead><tr><th>Año</th><th>Recaudado</th><th>Gasto ejecutado</th><th>de canon/regalías</th><th>de Foncomun</th><th>Gasto ÷ recaudado</th></tr></thead><tbody>{rows}</tbody></table>
<p class="src" style="margin-top:6px">* 2026 parcial.</p></div></div>
<p class="src" style="margin-top:8px">⚠️ SUNAT registra la recaudación según el <b>domicilio fiscal</b>: una minera o banco con sede en Lima tributa en Lima aunque opere en {esc(r['nombre'])}, por eso la recaudación regional subestima lo que la región genera.{lima_note}
Fuente: <a href="{TAX['url']}">BCRP — Ingresos tributarios recaudados por SUNAT según departamento</a> (corte {TAX['corte']}).{gasto_src}</p></section>"""

CANON_COL = {'minero': '#f59e0b', 'gasifero': '#ef4444', 'regalias': '#a16207', 'petrolero': '#7c3aed', 'sobrecanon': '#a855f7', 'focam': '#ec4899',
             'hidro': '#06b6d4', 'pesquero': '#3b82f6', 'forestal': '#22c55e', 'aduanas': '#64748b', 'participaciones': '#94a3b8'}

RUB_LAB = [('00', 'Recursos ordinarios (Tesoro público)', '#3b82f6'), ('18', 'Canon, sobrecanon y regalías', '#f59e0b'),
           ('07', 'Foncomun', '#22c55e'), ('08', 'Impuestos municipales', '#14b8a6'), ('09', 'Recursos directamente recaudados', '#a855f7'),
           ('19', 'Endeudamiento (operaciones de crédito)', '#ef4444'), ('13', 'Donaciones y transferencias', '#ec4899'),
           ('04', 'Contribuciones a fondos', '#64748b'), ('15', 'Foncor', '#94a3b8')]

def fuentes_fin_section(r, nac):
    g = r['x'].get('gasto') or {}
    if not g.get('2025'): return ''
    ys = [y for y in [str(v) for v in range(2019, 2027)] if y in g]
    g25 = g['2025']; tot = g25['dev'] or 1; can = g25.get('rub_18', 0)
    ds = [{'label': l, 'data': [round((g[y].get('rub_' + c, 0)) / 1e6, 1) for y in ys], 'backgroundColor': col} for c, l, col in RUB_LAB if any(g[y].get('rub_' + c, 0) > 1e6 for y in ys)]
    rows = ''.join(f'<div style="margin:7px 0"><div style="display:flex;justify-content:space-between;gap:8px"><span><i style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{col};margin-right:6px"></i>{esc(l)}</span>'
                   f'<b>S/ {fmt(g25.get("rub_" + c, 0) / 1e6)} M · {f1(g25.get("rub_" + c, 0) / tot * 100)}%</b></div></div>' for c, l, col in RUB_LAB if g25.get('rub_' + c, 0) > 1e6)
    nt = nac['x'].get('gasto', {}).get('2025', {}); ncan = (nt.get('rub_18', 0) / nt['dev'] * 100) if nt.get('dev') else None
    return f"""<section><h2>💼 ¿El presupuesto de {esc(r['nombre'])} incluye el canon? ¿De dónde sale el dinero?</h2>
<p class="desc"><b>Sí.</b> El gasto público ejecutado en {esc(r['nombre'])} en 2025 fue de <b>S/ {fmt(tot / 1e6)} millones</b>, y de eso <b>S/ {fmt(can / 1e6)} M ({f1(can / tot * 100)}%) se financió con canon, sobrecanon y regalías</b>{f" (promedio nacional: {f1(ncan)}%)" if ncan else ""}.
El resto, S/ {fmt((tot - can) / 1e6)} M, vino de otras fuentes. La mayor parte del resto viene de <b>recursos ordinarios</b>, es decir, impuestos de todo el país que el Tesoro asigna.</p>
<div class="grid2"><div class="card"><h3 style="margin-bottom:6px">Fuentes de financiamiento 2025</h3>{rows}</div>
<div class="card"><h3 style="margin-bottom:6px">Evolución 2019–2026* (S/ millones)</h3><canvas id="chFF" height="240"></canvas></div></div>
<p class="src" style="margin-top:8px">Fuente: MEF — Datos Abiertos, Gasto Devengado por rubro de financiamiento (3 niveles de gobierno, meta en el departamento, sin transferencias ni deuda). * 2026 a {MEF['corte_2026']}.</p>
<script>window.__FF={json.dumps({'y': ys, 'ds': ds}, ensure_ascii=False)};</script></section>"""

def canon_section(r, nac):
    cn = r['x'].get('canon')
    if not CANON or not cn: return ''
    tipos = [t for t in CANON['tipos'] if t['k'] in CANON_COL]
    ys = [str(y) for y in range(2019, 2027)]
    usados = [t for t in tipos if any((cn.get(y) or {}).get(t['k'], 0) > 1e5 for y in ys)]
    c25 = cn.get('2025') or {}; tot25 = c25.get('total_canon', 0); pob = r['pob_ref']
    rows = ''.join(f'<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{CANON_COL[t["k"]]};margin-right:6px"></span>{esc(t["l"])}</td>'
                   + ''.join(f'<td class="n">{fmt(((cn.get(y) or {}).get(t["k"], 0)) / 1e6)}</td>' for y in ys[-4:]) + '</tr>' for t in usados)
    rows += '<tr><td><b>Total canon y regalías</b></td>' + ''.join(f'<td class="n"><b>{fmt(((cn.get(y) or {}).get("total_canon", 0)) / 1e6)}</b></td>' for y in ys[-4:]) + '</tr>'
    rows += '<tr><td>Foncomun (aparte)</td>' + ''.join(f'<td class="n">{fmt(((cn.get(y) or {}).get("foncomun", 0)) / 1e6)}</td>' for y in ys[-4:]) + '</tr>'
    principal = max(usados, key=lambda t: c25.get(t['k'], 0)) if usados and tot25 else None
    reparto = ' · '.join(f'{lab} {f1(c25.get(k, 0) / tot25 * 100)}%' for k, lab in (('niv_regional', 'gobierno regional'), ('niv_local', 'municipalidades'), ('niv_universidades', 'universidades')) if tot25 and c25.get(k)) if tot25 else ''
    k = [_kpi('Canon y regalías 2025', f'S/ {fmt(tot25 / 1e6)} M', f'{f1(tot25 / nac["x"]["canon"]["2025"]["total_canon"] * 100)}% del total nacional'),
         _kpi('Por habitante', f'S/ {fmt(r["x"].get("canon_pc") or 0)}', f'Perú S/ {fmt(nac["x"].get("canon_pc") or 0)} · puesto {r.get("ranks", {}).get("canon_pc", "—")} de 25'),
         _kpi(f'2026 (a {CANON["corte_2026"]})', f'S/ {fmt(((cn.get("2026") or {}).get("total_canon", 0)) / 1e6)} M', 'transferido en lo que va del año')]
    if principal: k.append(_kpi('Principal fuente', esc(principal['l'].split(' (')[0]), f'{f1(c25.get(principal["k"], 0) / tot25 * 100)}% del canon 2025'))
    data = {'y': ys, 'ds': [{'label': t['l'], 'data': [round(((cn.get(y) or {}).get(t['k'], 0)) / 1e6, 1) for y in ys], 'backgroundColor': CANON_COL[t['k']]} for t in usados]}
    return f"""<section><h2>⛏️ Canon, sobrecanon y regalías que recibe {esc(r['nombre'])}</h2>
<p class="desc">Lo que el gobierno regional, las municipalidades y las universidades públicas de la región reciben por la explotación de sus recursos naturales: minería, gas (Camisea), petróleo, hidroenergía, pesca y bosques. Millones de soles.</p>
<div class="kpis" style="margin:0 0 14px;padding:0">{''.join(k)}</div>
<div class="grid2"><div class="card"><canvas id="chCanon" height="250"></canvas><p class="src">2026 = enero a {CANON['corte_2026']}.{' Reparto 2025: ' + reparto + '.' if reparto else ''}</p></div>
<div class="card scroll"><table class="tbl"><thead><tr><th>Concepto (S/ millones)</th>{''.join(f'<th>{y}{"*" if y == "2026" else ""}</th>' for y in ys[-4:])}</tr></thead><tbody>{rows}</tbody></table></div></div>
<p class="src" style="margin-top:8px">Fuente: <a href="{CANON['url']}">MEF — Datos Abiertos, Presupuesto de Ingresos</a> (ingreso recaudado por gobiernos regionales, municipalidades y universidades del departamento; rubro 18 por específica de ingreso; Foncomun = rubro 07).</p>
<script>window.__CANON={json.dumps(data, ensure_ascii=False)};</script></section>"""

NIVEL_LAB = {'R': 'Gobierno regional', 'M': 'Municipalidad', 'E': 'Universidad / entidad nacional'}

def _entidades(r):
    if not CANON_ENT: return []
    code = r['distritos'][0]['u'][:2] if r['distritos'] else None
    out, gr = [], None
    for e in CANON_ENT['por_departamento'].get(code, []):
        if e['v'] != 'R': out.append(e); continue
        if gr is None: gr = {'u': '', 'v': 'R', 'n': f"Gobierno Regional de {r['nombre']} (todas sus unidades)", 'y': {}, 'd': {}}
        for y, v in e['y'].items(): gr['y'][y] = gr['y'].get(y, 0) + v
        for y, dv in e['d'].items():
            t = gr['d'].setdefault(y, {})
            for k, v in dv.items(): t[k] = t.get(k, 0) + v
    if gr: out.append(gr)
    return sorted(out, key=lambda e: -e['y'].get('2025', 0))

def canon_receptores_section(r):
    ents = _entidades(r)
    if not ents: return ''
    tlab = {t['k']: t['l'].split(' (')[0] for t in CANON['tipos']}
    rows = ''
    for e in ents[:15]:
        t25 = e['y'].get('2025', 0)
        if t25 <= 0: continue
        d = (e['d'].get('2025') or {}); ppal = max((k for k in d if k != 'foncomun'), key=lambda k: d[k], default=None)
        dist = UBI.get(e['u']); ind = IND.get(e['u'], {}) if e['u'] else {}
        pob = ind.get('p25') or ind.get('p'); lugar = f'{dist[2]} ({dist[1]})' if dist else ''
        pc = f'S/ {fmt(t25 / pob)}' if (pob and e['v'] == 'M') else '—'
        nom = e['n'] if e['v'] == 'R' else e['n'].title()
        rows += (f'<tr><td>{esc(nom)}<br><small style="color:var(--muted2)">{esc(NIVEL_LAB.get(e["v"], e["v"]))}{" · " + esc(lugar) if lugar else ""}</small></td>'
                 f'<td class="n"><b>{fmt(t25 / 1e6)}</b></td><td class="n">{fmt(e["y"].get("2026", 0) / 1e6)}</td><td>{esc(tlab.get(ppal, "—"))}</td><td class="n">{pc}</td>'
                 f'<td class="n">{fmt(sum(e["y"].values()) / 1e6)}</td></tr>')
    # por provincia (solo municipalidades)
    prov = {}
    for e in ents:
        if e['v'] != 'M': continue
        dist = UBI.get(e['u'])
        if dist: prov[dist[1]] = prov.get(dist[1], 0) + e['y'].get('2025', 0)
    tot = sum(prov.values()) or 1
    pbars = ''.join(f'<div style="margin:7px 0"><div style="display:flex;justify-content:space-between"><span>{esc(k)}</span><b>S/ {fmt(v / 1e6)} M · {f1(v / tot * 100)}%</b></div><div class="bar"><i style="width:{v / max(prov.values()) * 100:.0f}%"></i></div></div>'
                    for k, v in sorted(prov.items(), key=lambda x: -x[1]) if v > 0)
    return f"""<section><h2>📍 ¿Quién recibe el canon dentro de {esc(r['nombre'])}?</h2>
<p class="desc">Entidades de la región que más canon, sobrecanon y regalías recibieron en 2025 (millones de soles). Por ley, la mayor parte va a las municipalidades de la zona productora; el canon por habitante muestra cuánto le toca a cada vecino.</p>
<div class="grid2"><div class="card scroll"><table class="tbl"><thead><tr><th>Entidad</th><th>2025</th><th>2026*</th><th>Principal fuente</th><th>Por habitante</th><th>Acum. 2019-26</th></tr></thead><tbody>{rows}</tbody></table>
<p class="src" style="margin-top:6px">* 2026 a {CANON['corte_2026']}. Por habitante: municipalidades distritales, con población estimada 2025 del distrito.</p></div>
<div class="card"><h3 style="margin-bottom:6px">Municipalidades por provincia, 2025</h3>{pbars}</div></div>
<p class="src" style="margin-top:8px">Fuente: MEF — Datos Abiertos, Presupuesto de Ingresos (ingreso recaudado de cada entidad, rubro 18).</p></section>"""

def camisea_section(r, nac, regiones):
    cn = r['x'].get('canon') or {}
    ys = [str(y) for y in range(2019, 2027)]
    gas = {y: (cn.get(y) or {}).get('gasifero', 0) for y in ys}; foc = {y: (cn.get(y) or {}).get('focam', 0) for y in ys}
    if sum(gas.values()) + sum(foc.values()) < 1e6: return ''
    acum = sum(gas.values()) + sum(foc.values())
    nat = {d: sum(((rr['x'].get('canon') or {}).get(y) or {}).get('gasifero', 0) + ((rr['x'].get('canon') or {}).get(y) or {}).get('focam', 0) for y in ys) for d, rr in regiones.items()}
    natot = sum(nat.values()) or 1
    reparto = ' · '.join(f"{regiones[d]['nombre']} {f1(v / natot * 100)}%" for d, v in sorted(nat.items(), key=lambda x: -x[1]) if v / natot > 0.005)
    ents = [e for e in _entidades(r) if any((e['d'].get(y) or {}).get('gasifero', 0) + (e['d'].get(y) or {}).get('focam', 0) > 0 for y in ('2024', '2025', '2026'))]
    ents.sort(key=lambda e: -((e['d'].get('2025') or {}).get('gasifero', 0) + (e['d'].get('2025') or {}).get('focam', 0)))
    top = ''
    for e in ents[:8]:
        d25 = e['d'].get('2025') or {}; v = d25.get('gasifero', 0) + d25.get('focam', 0)
        dist = UBI.get(e['u']); ind = IND.get(e['u'], {}) if e['u'] else {}; pob = ind.get('p25') or ind.get('p')
        pc = f' · S/ {fmt(v / pob)} por habitante' if (pob and e['v'] == 'M') else ''
        top += f'<li><b>{esc(e["n"] if e["v"] == "R" else e["n"].title())}</b>{" (" + esc(dist[1]) + ")" if dist else ""}: S/ {fmt(v / 1e6)} M en 2025{pc}</li>'
    tipo_txt = ('canon gasífero (es la región productora: los lotes de Camisea están en La Convención)' if sum(gas.values()) > sum(foc.values())
                else 'FOCAM, el fondo que comparte las regalías de Camisea con las regiones por donde pasa el ducto')
    data = {'y': ys, 'gas': [round(gas[y] / 1e6, 1) for y in ys], 'foc': [round(foc[y] / 1e6, 1) for y in ys]}
    return f"""<section class="card special"><h2>🔥 Camisea en {esc(r['nombre'])}</h2>
<p class="desc">{esc(r['nombre'])} recibe dinero del gas de Camisea vía {tipo_txt}. Acumulado 2019–2026: <b>S/ {fmt(acum / 1e6)} millones</b>.
Reparto nacional del dinero de Camisea (canon gasífero + FOCAM, 2019-2026): {esc(reparto)}.</p>
<div class="grid2"><div><canvas id="chCamisea" height="230"></canvas></div><div><h3 style="margin-bottom:6px">Quién lo recibe (2025)</h3><ul style="margin-left:18px">{top}</ul></div></div>
<p class="src" style="margin-top:8px">Fuente: MEF — Datos Abiertos, Presupuesto de Ingresos (específicas canon gasífero y regalías FOCAM). 2026 a {CANON['corte_2026']}.</p>
<script>window.__CAMISEA={json.dumps(data)};</script></section>"""

FUN_CORTO = {'TRANSPORTE': 'Transporte', 'EDUCACION': 'Educación', 'SALUD': 'Salud', 'SANEAMIENTO': 'Saneamiento', 'AGROPECUARIA': 'Agropecuario',
             'PLANEAMIENTO, GESTION Y RESERVA DE CONTINGENCIA': 'Gestión y administración', 'ORDEN PUBLICO Y SEGURIDAD': 'Seguridad', 'AMBIENTE': 'Ambiente',
             'VIVIENDA Y DESARROLLO URBANO': 'Vivienda y urbanismo', 'ENERGIA': 'Energía', 'CULTURA Y DEPORTE': 'Cultura y deporte', 'COMERCIO': 'Comercio',
             'TURISMO': 'Turismo', 'PROTECCION SOCIAL': 'Protección social', 'COMUNICACIONES': 'Comunicaciones', 'PREVISION SOCIAL': 'Pensiones',
             'TRABAJO': 'Trabajo', 'INDUSTRIA': 'Industria', 'PESCA': 'Pesca', 'MINERIA': 'Minería', 'JUSTICIA': 'Justicia', 'RELACIONES EXTERIORES': 'Rel. exteriores',
             'DEFENSA Y SEGURIDAD NACIONAL': 'Defensa', 'LEGISLATIVA': 'Legislativa', 'DEUDA PUBLICA': 'Deuda'}
def fcorto(f): return FUN_CORTO.get(norm(f), f.title()[:28])

def _det_dep(r):
    if not DET: return None
    return pick(DET['departamentos'], r['dep'], CALLAO_AL if r['dep'] == 'Callao' else None)

def _grupo_receptor(e):
    if e['v'] == 'R': return 'Gobierno regional'
    if e['v'] == 'E': return 'Universidades y otros'
    prov = PROV_BY4.get(e['u'][:4])
    return f'Municipios · {prov}' if prov else 'Municipios · otros'

def flujo_canon_section(r):
    """Dos Sankey: (1) tipo de canon -> receptor 2025; (2) receptor -> función -> gastado / sin gastar (canon, PIM 2025)."""
    ents = _entidades(r); dd = _det_dep(r)
    if not ents or not CANON: return ''
    tlab = {t['k']: t['l'].split(' (')[0] for t in CANON['tipos']}
    # --- Sankey 1
    f1l = {}
    for e in ents:
        g = _grupo_receptor(e)
        for k, v in (e['d'].get('2025') or {}).items():
            if k == 'foncomun' or v < 1e5: continue
            key = (tlab.get(k, k), g); f1l[key] = f1l.get(key, 0) + v
    # agrupa provincias pequeñas para que el diagrama sea legible
    gt = {}
    for (a, b), v in f1l.items(): gt[b] = gt.get(b, 0) + v
    keep = {b for b, _ in sorted(gt.items(), key=lambda x: -x[1])[:9]}
    s1 = {}
    for (a, b), v in f1l.items():
        b2 = b if b in keep else 'Municipios · otras provincias'; s1[(a, b2)] = s1.get((a, b2), 0) + v
    L1 = [{'from': 'T:' + a, 'to': 'R:' + b, 'flow': round(v / 1e6, 1)} for (a, b), v in s1.items() if v >= 5e5]
    # --- Sankey 2 (gasto con canon por ejecutora -> grupo -> función -> estado), año 2025
    L2 = []; tot_pim = tot_dev = 0
    if DET:
        code = r['distritos'][0]['u'][:2]
        acc = {}
        for key, ys in DET['ejecutoras'].items():
            ub, niv, nom = key.split('|', 2)
            if ub[:2] != code: continue
            g = _grupo_receptor({'v': niv, 'u': ub})
            if g not in keep and g.startswith('Municipios'): g = 'Municipios · otras provincias'
            for fn, (dev, pim) in (ys.get('2025') or {}).items():
                k = (g, fcorto(fn)); a = acc.setdefault(k, [0, 0]); a[0] += dev; a[1] += pim
        # top funciones
        ft = {}
        for (g, fn), (dev, pim) in acc.items(): ft[fn] = ft.get(fn, 0) + pim
        topf = {f for f, _ in sorted(ft.items(), key=lambda x: -x[1])[:8]}
        acc2 = {}; est = {}
        for (g, fn), (dev, pim) in acc.items():
            fn2 = fn if fn in topf else 'Otras funciones'
            a = acc2.setdefault((g, fn2), [0, 0]); a[0] += dev; a[1] += pim
            e2 = est.setdefault(fn2, [0, 0]); e2[0] += dev; e2[1] += pim
        L2 = [{'from': 'R:' + g, 'to': 'F:' + fn, 'flow': round(pim / 1e6, 1)} for (g, fn), (dev, pim) in acc2.items() if pim >= 5e5]
        for fn, (dev, pim) in est.items():
            if dev > 0: L2.append({'from': 'F:' + fn, 'to': 'E:Gastado', 'flow': round(dev / 1e6, 1)})
            if pim - dev > 0: L2.append({'from': 'F:' + fn, 'to': 'E:Sin gastar', 'flow': round((pim - dev) / 1e6, 1)})
            tot_pim += pim; tot_dev += dev
    if not L1 and not L2: return ''
    ej = f' Del presupuesto financiado con canon en 2025 (S/ {fmt(tot_pim / 1e6)} M, incluye saldos de años anteriores) se gastó <b>{f1(tot_dev / tot_pim * 100)}%</b> y quedaron <b>S/ {fmt((tot_pim - tot_dev) / 1e6)} M sin gastar</b>.' if tot_pim else ''
    data = {'L1': L1, 'L2': L2}
    return f"""<section><h2>🌊 La ruta del dinero del canon en {esc(r['nombre'])} (2025)</h2>
<p class="desc">Diagrama de flujos: el grosor de cada banda es proporcional a los millones de soles.{ej}</p>
<div class="grid2"><div class="card"><h3 style="margin-bottom:6px">1. De dónde viene y a quién llega</h3><p class="src" style="margin-bottom:6px">Tipo de canon → entidad receptora (transferencias recaudadas 2025)</p><div style="position:relative;height:420px"><canvas id="skA"></canvas></div></div>
<div class="card"><h3 style="margin-bottom:6px">2. En qué se usa y cuánto se gastó</h3><p class="src" style="margin-bottom:6px">Receptor → función → gastado / sin gastar (presupuesto PIM 2025 financiado con canon)</p><div style="position:relative;height:420px"><canvas id="skB"></canvas></div></div></div>
<p class="src" style="margin-top:8px">Fuentes: MEF Datos Abiertos — Presupuesto de Ingresos (canon por entidad) y Gasto Devengado (rubro 18 por función). Montos de ingreso y de presupuesto no coinciden: el PIM incluye saldos no gastados de años anteriores.</p>
<script>window.__SK={json.dumps(data, ensure_ascii=False)};</script></section>"""

def gasto_en_que_section(r):
    dd = _det_dep(r)
    if not dd: return ''
    y = '2025' if '2025' in dd else max(dd)
    d = dd.get(y) or {}
    def fun_rows(key, n=10):
        fx = d.get(key) or {}
        tot = sum(v[0] for v in fx.values()) or 1
        rows = sorted(fx.items(), key=lambda x: -x[1][0])[:n]
        mx = rows[0][1][0] if rows else 1
        return ''.join(f'<div style="margin:7px 0"><div style="display:flex;justify-content:space-between;gap:8px"><span>{esc(fcorto(fn))}</span><b>S/ {fmt(dev / 1e6)} M · {f1(dev / tot * 100)}%</b></div>'
                       f'<div class="bar"><i style="width:{dev / mx * 100:.0f}%"></i></div><div class="rk-ax"><span>PIM S/ {fmt(pim / 1e6)} M</span><span>ejecución {f1(dev / pim * 100) if pim else "—"}%</span></div></div>' for fn, (dev, pim) in rows)
    pc = d.get('proy_canon') or []
    prows = ''.join(f'<tr><td>{esc(p["n"].capitalize())}<br><small style="color:var(--muted2)">CUI {esc(p["cui"])} · {esc(p["e"].title())} · {esc(fcorto(p["f"]))}</small></td>'
                    f'<td class="n">{fmt(p["pim"] / 1e6)}</td><td class="n">{fmt(p["dev"] / 1e6)}</td><td class="n">{f1(p["dev"] / p["pim"] * 100) if p["pim"] else "—"}%</td></tr>' for p in pc[:12])
    pt = d.get('proy_otros') or []
    trows = ''.join(f'<tr><td>{esc(p["n"].capitalize())}<br><small style="color:var(--muted2)">CUI {esc(p["cui"])} · {esc(p["e"].title())}</small></td>'
                    f'<td class="n">{fmt(p["pim"] / 1e6)}</td><td class="n">{fmt(p["dev"] / 1e6)}</td><td class="n">{f1(p["dev"] / p["pim"] * 100) if p["pim"] else "—"}%</td></tr>' for p in pt[:8])
    gc = d.get('gen_canon') or {}
    inv = sum(v[0] for k, v in gc.items() if k.startswith('6 ')); gtot = sum(v[0] for v in gc.values()) or 1
    d26 = dd.get('2026') or {}
    c26 = d26.get('fun_canon') or {}
    t26p = sum(v[1] for v in c26.values()); t26d = sum(v[0] for v in c26.values())
    k26 = f' En 2026 (a {MEF["corte_2026"] if MEF else "la fecha"}) el presupuesto con canon es S/ {fmt(t26p / 1e6)} M y va ejecutado el <b>{f1(t26d / t26p * 100)}%</b>.' if t26p else ''
    return f"""<section><h2>🧾 ¿En qué se gasta el dinero en {esc(r['nombre'])}? ({y})</h2>
<p class="desc">Gasto público ejecutado en la región por función. A la izquierda, solo lo financiado con <b>canon, sobrecanon y regalías</b>: el <b>{f1(inv / gtot * 100)}%</b> se fue a inversión (obras y equipamiento); el resto, a gasto corriente.{k26}</p>
<div class="grid2"><div class="card"><h3 style="margin-bottom:6px">⛏️ Con canon y regalías</h3>{fun_rows('fun_canon')}</div>
<div class="card"><h3 style="margin-bottom:6px">🏛️ Con todas las demás fuentes</h3>{fun_rows('fun_otros')}</div></div>
<div class="grid2" style="margin-top:14px"><div class="card scroll"><h3 style="margin-bottom:6px">🏗️ Proyectos más grandes financiados con canon ({y})</h3>
<table class="tbl"><thead><tr><th>Proyecto</th><th>PIM S/ M</th><th>Gastado</th><th>Avance</th></tr></thead><tbody>{prows}</tbody></table></div>
<div class="card scroll"><h3 style="margin-bottom:6px">🏗️ Proyectos más grandes con otras fuentes ({y})</h3>
<table class="tbl"><thead><tr><th>Proyecto</th><th>PIM S/ M</th><th>Gastado</th><th>Avance</th></tr></thead><tbody>{trows}</tbody></table></div></div>
<p class="src" style="margin-top:8px">Fuente: MEF — Datos Abiertos, Gasto Devengado {y} (función, genérica y proyecto por fuente de financiamiento; excluye transferencias y deuda). CUI = código único de inversión: búscalo en <a href="https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones">Consulta de Inversiones del MEF</a>.</p></section>"""

def _emp_card(e):
    filas = ''.join(f'<li style="margin:5px 0">{esc(d["k"])}: <b>{esc(d["v"])}</b> <a class="src" href="{d["u"]}" target="_blank" rel="noopener">[{esc(d["f"])}]</a></li>' for d in e['datos'])
    nota = f'<p class="src" style="margin-top:6px">{esc(e["nota"])}</p>' if e.get('nota') else ''
    return f'<div class="card"><h3 style="margin-bottom:4px">{esc(e["nombre"])}</h3><p class="src" style="margin-bottom:6px">{esc(e["actividad"])}</p><ul style="margin-left:18px">{filas}</ul>{nota}</div>'

def empresas_section(r):
    es = [e for e in EMP['empresas'] if norm(r['dep']) in {norm(x) for x in e['regiones']}]
    if not es: return ''
    c25 = ((r['x'].get('canon') or {}).get('2025')) or {}
    ctx = []
    if c25.get('gasifero', 0) > 1e6: ctx.append(f"canon gasífero S/ {fmt(c25['gasifero'] / 1e6)} M")
    if c25.get('minero', 0) > 1e6: ctx.append(f"canon minero S/ {fmt(c25['minero'] / 1e6)} M")
    if c25.get('regalias', 0) > 1e6: ctx.append(f"regalías mineras S/ {fmt(c25['regalias'] / 1e6)} M")
    return f"""<section><h2>🏭 Las empresas detrás del canon de {esc(r['nombre'])}</h2>
<p class="desc">{esc(EMP['_meta']['mecanismo'])} En 2025 {esc(r['nombre'])} recibió {', '.join(ctx) if ctx else 'canon'} (MEF). Estas son las ventas y ganancias públicas de las empresas que lo generan:</p>
<div class="grid2">{''.join(_emp_card(e) for e in es)}</div>
<p class="src" style="margin-top:8px">{esc(EMP['_meta']['nota'])} No convertimos a soles para no introducir supuestos de tipo de cambio.</p></section>"""

def salud_vida_section(r, nac):
    X = r['x']; nx = nac['x']; c = r['censo2025'] or {}
    k = []
    if X.get('evn'): k.append(_kpi('Esperanza de vida', f'{f1(X["evn"][0])} años', f'INEI 2020-25 · proyección 2025-30: {f1(X["evn"][1])}' + (f' · Censo 2025: {f1(c["ev"])}' if c.get('ev') else '') + f' · Perú {f1(nx["evn"][0])}'))
    if X.get('tmi'): k.append(_kpi('Mortalidad infantil', f'{f1(X["tmi"][0])} ‰', f'por mil nacidos vivos · Perú {f1(nx["tmi"][0])}'))
    if X.get('camas'): k.append(_kpi('Camas hospitalarias 2024', fmt(X['camas'][-1]), f'{f1(X.get("camas_10k"))} por 10 mil hab. · Perú {f1(nx["camas_10k"])}'))
    if X.get('medicos'): k.append(_kpi('Médicos colegiados 2024', fmt(X['medicos'][-1]), f'{fmt(X["hab_medico"][-1])} habitantes por médico · Perú {fmt(nx["hab_medico"][-1])}' if X.get('hab_medico') else ''))
    if X.get('cnv2026'): k.append(_kpi('Nacimientos 2026', fmt(X['cnv2026']), f'CNV MINSA, enero a {CNV["corte"]}'))
    d26 = X['def'].get('2026'); d25 = X['def'].get('2025')
    if d26: k.append(_kpi('Defunciones 2026', fmt(d26), f'SINADEF ene–sep 2026 · 2025 completo: {fmt(d25 or 0)}'))
    return f"""<section><h2>🏥 Salud y vida: camas, médicos, nacimientos y esperanza de vida</h2>
<p class="desc">Oferta hospitalaria, personal médico y estadísticas vitales con los cortes más recientes disponibles (2026 parcial).</p>
<div class="kpis" style="margin:0 0 14px;padding:0">{''.join(k)}</div>
<div class="grid2"><div class="card"><h3 style="margin-bottom:6px">🛏️ Camas hospitalarias 2014–2024</h3><canvas id="chCam" height="220"></canvas></div>
<div class="card"><h3 style="margin-bottom:6px">👶 Nacimientos inscritos y ⚰️ defunciones</h3><canvas id="chVit" height="220"></canvas>
<p class="src">2026: defunciones hasta setiembre. Los nacimientos inscritos (RENIEC) llegan hasta 2023; el CNV 2026 va en los indicadores.</p></div></div>
<p class="src" style="margin-top:8px">Fuentes: INEI <a href="{EVN['url']}">Estimaciones y Proyecciones 1995-2030</a> (esperanza de vida y mortalidad infantil, proyección previa al Censo 2025);
INEI <a href="https://www.gob.pe/en/institucion/inei/informes-publicaciones/7264121-peru-2025-statistical-compendium">Compendio Estadístico Perú 2025</a> (camas MINSA 6.4, médicos 6.5-6.6, nacimientos inscritos 3.32);
<a href="{CNV['url']}">MINSA CNV</a> (nacimientos 2026); <a href="{SINADEF['url']}">MINSA SINADEF</a> (defunciones, procesado en <a href="https://unimauro.github.io/mortalidad-peru/">mortalidad-peru</a>).</p></section>"""

def lectura_section(r, nac):
    e = r['x'].get('enla') or {}; ne = nac['x'].get('enla') or {}
    if not e: return ''
    def nv(a):
        n = (e.get(a) or {}).get('niveles') or {}
        segs = [('previo', '#7f1d1d'), ('inicio', '#ef4444'), ('proceso', '#f59e0b'), ('satisfactorio', '#22c55e')]
        bar = ''.join(f'<i style="width:{n.get(k, 0)}%;background:{c}" title="{k}: {f1(n.get(k))}%"></i>' for k, c in segs)
        return (f'<div style="margin:10px 0"><div style="display:flex;justify-content:space-between"><b>{"📖 Lectura" if a == "lectura" else "🔢 Matemática"}</b>'
                f'<span><b>{f1(n.get("satisfactorio"))}%</b> satisfactorio · Perú {f1(((ne.get(a) or {}).get("satisfactorio")))}%</span></div>'
                f'<div class="stack">{bar}</div><div class="rk-ax"><span>Previo {f1(n.get("previo"))}% · Inicio {f1(n.get("inicio"))}%</span><span>Proceso {f1(n.get("proceso"))}%</span></div></div>')
    lim = ' (Lima Metropolitana)' if r['dep'] == 'Lima' else ''
    return f"""<section><h2>📚 Lectura y matemática — ENLA 2024</h2>
<p class="desc">Estudiantes de 4.° de primaria por nivel de logro{lim}. Satisfactorio = logró lo esperado para su grado.</p>
<div class="grid2"><div class="card">{nv('lectura')}{nv('matematica')}</div>
<div class="card"><h3 style="margin-bottom:6px">Evolución del % satisfactorio (ECE/ENLA)</h3><canvas id="chEnla" height="200"></canvas></div></div>
<p class="src" style="margin-top:8px">Fuente: <a href="{ENLA['url']}">MINEDU — Oficina de Medición de la Calidad de los Aprendizajes (UMC), ENLA 2024</a>. Ver también el observatorio <a href="https://unimauro.github.io/lecturas-peru/">Lecturas en el Perú</a> (hábitos de lectura, ENL 2022).</p></section>"""

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
    out.append(gasto_pc_section(regiones, nac))
    out.append(canon_nacional_section(regiones, nac))
    out.append(f"""<section id="empresas"><h2>🏭 Las empresas detrás del canon</h2><p class="desc">{esc(EMP['_meta']['mecanismo'])}</p>
<div class="grid2">{''.join(_emp_card(e).replace('<h3 style="margin-bottom:4px">', '<h3 style="margin-bottom:4px">' + ' · '.join(f'<a href="{slug(NOMBRE.get(x, x))}/">{esc(NOMBRE.get(x, x))}</a>' for x in e['regiones']) + ' — ') for e in EMP['empresas'])}</div>
<p class="src" style="margin-top:8px">{esc(EMP['_meta']['nota'])}</p></section>""")
    out.append(footer(depth=1))
    return '\n'.join(out)

FUENTES = [  # tema, fuente, corte, url
    ('Pobreza monetaria, ingreso y gasto real', 'INEI — Evolución de la Pobreza Monetaria 2016-2025 (ENAHO)', '2025 (publicado may-2026)', 'https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025'),
    ('Anemia, desnutrición, vacunas, CRED, hierro, lactancia, agua, saneamiento, violencia, fecundidad', 'INEI — ENDES 2025, Indicadores de Programas Presupuestales', '2025 (publicado may-2026)', 'https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf'),
    ('Población, viviendas y servicios', 'INEI — Censos Nacionales 2025 (notas departamentales)', '2025 (publicado may–oct 2026)', 'https://censos2025.inei.gob.pe/'),
    ('Recaudación tributaria por región', 'SUNAT vía BCRP — tributos internos según departamento', TAX['corte'], TAX['url']),
    ('Ventas y utilidades de empresas que generan canon', 'Estados financieros y reportes anuales (Cerro Verde/SMV, Southern Copper, MMG, Hudbay, Teck, Anglo American) y Perupetro', '2024-2025', 'https://www.smv.gob.pe/'),
    ('Canon, sobrecanon, regalías, FOCAM, renta de aduanas, Foncomun', 'MEF — Datos Abiertos, Presupuesto de Ingresos (ingreso recaudado por GR y GL)', (CANON or {}).get('corte_2026', ''), 'https://datosabiertos.mef.gob.pe/'),
    ('Gasto público ejecutado en la región', 'MEF — Datos Abiertos, Gasto Devengado (3 niveles de gobierno)', (MEF or {}).get('corte_2026', 'en carga'), 'https://datosabiertos.mef.gob.pe/'),
    ('Camas hospitalarias, médicos, nacimientos inscritos', 'INEI — Compendio Estadístico Perú 2025 (MINSA, CMP, RENIEC)', '2024 / 2023', 'https://www.gob.pe/en/institucion/inei/informes-publicaciones/7264121-peru-2025-statistical-compendium'),
    ('Nacimientos 2026', 'MINSA — Certificado de Nacido Vivo (CNV) en línea', CNV['corte'], CNV['url']),
    ('Defunciones', 'MINSA — SINADEF datos abiertos', SINADEF['corte'], SINADEF['url']),
    ('Esperanza de vida y mortalidad infantil', 'INEI — Estimaciones y Proyecciones de Población por departamento 1995-2030', '2020-2025 (proyección)', EVN['url']),
    ('Lectura y matemática', 'MINEDU UMC — ENLA 2024 (4.° primaria)', '2024', ENLA['url']),
    ('IDH distrital', 'PNUD — IDH 2019', '2019', 'https://www.undp.org/es/peru'),
    ('Población, pobreza distrital y geometrías', 'INEI Censo 2017 / mapa de pobreza; ubigeo-peru-aumentado; peru-geojson', '2017-2020', 'https://github.com/jmcastagnetto/ubigeo-peru-aumentado'),
]
FAQ = [
    ('¿De dónde salen los datos?', 'Solo de fuentes oficiales y públicas (INEI, MINSA, MINEDU, MEF, SUNAT/BCRP, PNUD). Cada cifra muestra su fuente, año y fecha de corte. Abajo está la tabla completa con enlaces.'),
    ('¿Por qué algunos datos son de 2026 y otros de 2024?', 'Cada institución publica con un rezago distinto. Usamos siempre el último corte disponible: recaudación hasta julio 2026, gasto público y nacimientos hasta la fecha de consulta, defunciones hasta setiembre 2026; encuestas (ENAHO/ENDES) 2025; camas y médicos 2024. Los valores de 2026 son parciales y se marcan con *.'),
    ('¿Por qué Lima "recauda" casi todo?', 'SUNAT registra los impuestos según el domicilio fiscal. Muchas mineras, bancos y grandes empresas tienen domicilio en Lima aunque produzcan en regiones; por eso la recaudación regional subestima lo que cada región genera. Para comparar, mira la recaudación por habitante y el gasto que regresa.'),
    ('¿Qué significa "cuánto regresa"?', 'Es el gasto público devengado (ejecutado) en el departamento por los tres niveles de gobierno: nacional, regional y municipal, según el lugar de la meta. Excluimos las transferencias entre entidades (para no contar dos veces el mismo sol) y el servicio de la deuda. Ojo: lo que ejecutan entidades nacionales con meta en Lima (por ejemplo pensiones o compras centralizadas) se registra en Lima. Incluye lo financiado con canon, regalías y Foncomun, que mostramos aparte.'),
    ('¿Qué es el canon y por qué unas regiones reciben mucho más?', 'El canon es la parte de los impuestos que pagan las empresas que explotan recursos naturales (minería, gas, petróleo, hidroenergía, pesca, bosques) y que la ley devuelve a la región donde se extraen. Las regalías y el FOCAM (gas de Camisea) son pagos adicionales. Por eso Cusco recibe sobre todo canon gasífero, Áncash, Arequipa y Moquegua canon minero, y Piura y Loreto canon petrolero.'),
    ('¿El presupuesto de una región incluye el canon?', 'Sí. El gasto público ejecutado en cada región incluye lo financiado con canon, sobrecanon y regalías (rubro 18), además de recursos ordinarios del Tesoro, Foncomun, impuestos municipales, endeudamiento y donaciones. En cada carátula mostramos cuánto aporta cada fuente: en Cusco, el canon financió el 28% del gasto de 2025.'),
    ('¿Por qué mostrar ventas y ganancias de las empresas?', 'Porque el canon minero es la mitad del Impuesto a la Renta que pagan las mineras, y el canon gasífero sale de las regalías y la renta del gas: cuando las empresas ganan más, la región recibe más. Solo mostramos cifras publicadas por las propias empresas (estados financieros, reportes anuales) o por Perupetro, con enlace a la fuente.'),
    ('¿Los datos son por distrito o por región?', 'La mayoría de indicadores 2025 son departamentales (encuestas ENDES/ENAHO, Censo). A nivel distrital usamos Censo 2017, IDH 2019 y el mapa de pobreza INEI. Los índices 0-100 del simulador del distrito son ilustrativos y así se indican.'),
    ('¿Qué es la anemia "según OMS 2024"?', 'Desde 2024 el MINSA adoptó la nueva directriz de la OMS (RM 251-2024-MINSA) para el punto de corte de hemoglobina. INEI publica su cifra principal con ese criterio (34,9% nacional en 2025).'),
    ('¿Cómo funciona el chat?', 'El asistente tiene una memoria con todas las cifras oficiales de las 25 regiones y los rankings. Responde rankings, comparaciones ("Compara Cusco y Puno") y fichas. Cuando está conectado al servidor de IA, usa esa misma memoria y tiene prohibido inventar cifras.'),
    ('¿Puedo descargar los datos?', 'Sí: en el dashboard, el Cuadro de indicadores regionales 2025 se descarga en CSV, y todos los archivos están en el repositorio (carpeta data/fuentes).'),
    ('¿Cómo puedo apoyar?', 'Con un café, PayPal o Yape/Plin (abajo). También reportando errores o sugiriendo fuentes en GitHub.'),
]

def gasto_pc_section(regiones, nac, link_prefix=''):
    """Cuadro: gasto público por persona por región (ranking) + recaudación por persona y ratio."""
    rows = []
    for r in regiones.values():
        X = r['x']; g = (X.get('gasto') or {}).get('2025') or {}
        if not g.get('dev'): continue
        pob = r['pob_ref']; t = (X.get('tax') or {}).get('2025')
        rows.append({'n': r['nombre'], 's': r['slug'], 'pob': pob, 'pf': r['pob_ref_fuente'], 'g': g['dev'] / 1e6, 'gpc': g['dev'] / pob,
                     'canpc': (g.get('canon') or 0) / pob, 'tpc': (t or 0) * 1e6 / pob, 'ratio': X.get('retorno'),
                     'pobreza': (r['pobreza_serie'] or [None])[-1]})
    if not rows: return ''
    rows.sort(key=lambda x: -x['gpc'])
    nx = nac['x']; npc = nx.get('gasto_pc')
    trs = ''.join(f'<tr><td class="n">{i + 1}</td><td><a href="{link_prefix}{x["s"]}/">{"☀️ " if x["n"] == "Cusco" else ""}{esc(x["n"])}</a></td>'
                  f'<td class="n">{fmt(x["pob"])}{"" if x["pf"] == "Censo 2025" else "*"}</td><td class="n">{fmt(x["g"])}</td>'
                  f'<td class="n"><b>S/ {fmt(x["gpc"])}</b></td><td class="n">S/ {fmt(x["canpc"])}</td><td class="n">S/ {fmt(x["tpc"])}</td>'
                  f'<td class="n">{f1(x["ratio"])}</td><td class="n">{f1(x["pobreza"])}%</td></tr>' for i, x in enumerate(rows))
    data = {'l': [x['n'] for x in rows], 'v': [round(x['gpc']) for x in rows], 'c': [round(x['canpc']) for x in rows]}
    return f"""<section id="gasto-persona"><h2>💸 Gasto público por persona, 2025</h2>
<p class="desc">¿En qué región el Estado gasta más soles por habitante? Gasto devengado 2025 de los tres niveles de gobierno en cada región (MEF), dividido entre su población.
Perú: <b>S/ {fmt(npc or 0)}</b> por persona. La parte verde es lo financiado con canon, sobrecanon, regalías y participaciones.</p>
<div class="grid2"><div class="card"><div style="position:relative;height:640px"><canvas id="chGpc"></canvas></div></div>
<div class="card scroll"><table class="tbl"><thead><tr><th>#</th><th>Región</th><th>Población</th><th>Gasto (S/ M)</th><th>Gasto por persona</th><th>de canon/regalías</th><th>Recaudación por persona</th><th>Gasto ÷ recaudado</th><th>Pobreza</th></tr></thead><tbody>{trs}</tbody></table>
<p class="src" style="margin-top:6px">* Población estimada 2025 (INEI aún no publica el Censo 2025 de esa región); con Censo 2025 en el resto. Lima incluye Lima Metropolitana y provincias.</p></div></div>
<p class="src" style="margin-top:8px">Fuente: MEF Datos Abiertos (gasto devengado por departamento de la meta, sin transferencias entre entidades ni servicio de la deuda); SUNAT/BCRP (recaudación); INEI (población, pobreza ENAHO 2025).
Lo que entidades nacionales ejecutan con meta en Lima (pensiones, compras centralizadas) se registra en Lima.</p>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script><script src="https://cdn.jsdelivr.net/npm/chartjs-chart-sankey@0.14.0/dist/chartjs-chart-sankey.min.js"></script><script>
(function(){{const G={json.dumps(data, ensure_ascii=False)};Chart.defaults.color='#8b9bc4';Chart.defaults.font.family='Inter,system-ui,sans-serif';
new Chart(document.getElementById('chGpc'),{{type:'bar',data:{{labels:G.l,datasets:[{{label:'Gasto por persona (S/)',data:G.v.map((v,i)=>v-G.c[i]),backgroundColor:G.l.map(n=>n==='Cusco'?'#f5a623':'rgba(59,130,246,.65)'),stack:'s',borderRadius:3}},{{label:'de canon/regalías',data:G.c,backgroundColor:'#22c55e',stack:'s',borderRadius:3}}]}},
options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}},tooltip:{{callbacks:{{footer:(it)=>'Total: S/ '+G.v[it[0].dataIndex].toLocaleString('es-PE')}}}}}},scales:{{x:{{stacked:true,grid:{{color:'rgba(139,155,196,.15)'}}}},y:{{stacked:true,grid:{{display:false}},ticks:{{autoSkip:false}}}}}}}}}});}})();
</script></section>"""

def canon_nacional_section(regiones, nac):
    if not CANON: return ''
    rs = [(r, (r['x'].get('canon') or {}).get('2025') or {}) for r in regiones.values()]
    rs = sorted([x for x in rs if x[1].get('total_canon')], key=lambda x: -x[1]['total_canon'])
    tipos = [t for t in CANON['tipos'] if t['k'] in CANON_COL and any(c.get(t['k'], 0) > 1e6 for _, c in rs)]
    data = {'l': [r['nombre'] for r, _ in rs], 'ds': [{'label': t['l'], 'data': [round(c.get(t['k'], 0) / 1e6, 1) for _, c in rs], 'backgroundColor': CANON_COL[t['k']]} for t in tipos]}
    ct = nac['x']['canon']['2025']
    tl = {t['k']: t['l'].split(' (')[0] for t in tipos}
    top10 = [r['nombre'] for r, _ in rs[:12]]
    sk = {}
    for r, c in rs:
        dest = r['nombre'] if r['nombre'] in top10 else 'Otras regiones'
        for t in tipos:
            v = c.get(t['k'], 0)
            if v >= 1e6: sk[(tl[t['k']], dest)] = sk.get((tl[t['k']], dest), 0) + v
    skl = [{'from': a, 'to': b, 'flow': round(v / 1e6, 1)} for (a, b), v in sk.items()]
    tcolors = {tl[t['k']]: CANON_COL[t['k']] for t in tipos}
    tops = ' · '.join(f"{t['l']}: S/ {fmt(ct.get(t['k'], 0) / 1e6)} M" for t in sorted(tipos, key=lambda t: -ct.get(t['k'], 0)))
    trs = ''.join(f'<tr><td><a href="{r["slug"]}/">{esc(r["nombre"])}</a></td><td class="n"><b>{fmt(c["total_canon"] / 1e6)}</b></td><td class="n">S/ {fmt(r["x"].get("canon_pc") or 0)}</td>'
                  + ''.join(f'<td class="n">{fmt(c.get(t["k"], 0) / 1e6) if c.get(t["k"], 0) > 5e5 else "—"}</td>' for t in tipos) + '</tr>' for r, c in rs)
    return f"""<section id="canon"><h2>⛏️ Canon, sobrecanon y regalías por región, 2025</h2>
<p class="desc">Total transferido en 2025 a gobiernos regionales, municipalidades y universidades: <b>S/ {fmt(ct['total_canon'] / 1e6)} millones</b>. {tops}.</p>
<div class="card"><h3 style="margin-bottom:6px">🌊 Flujo: tipo de canon → región (2025, S/ millones)</h3><div style="position:relative;height:560px"><canvas id="skNac"></canvas></div></div>
<div class="card" style="margin-top:14px"><div style="position:relative;height:640px"><canvas id="chCanonNac"></canvas></div></div>
<div class="card scroll" style="margin-top:14px"><table class="tbl"><thead><tr><th>Región</th><th>Total (S/ M)</th><th>Por habitante</th>{''.join(f'<th>{esc(t["l"].split(" (")[0])}</th>' for t in tipos)}</tr></thead><tbody>{trs}</tbody></table></div>
<p class="src" style="margin-top:8px">Fuente: MEF — Datos Abiertos, Presupuesto de Ingresos (ingreso recaudado, rubro 18). 2026 a {CANON['corte_2026']}: S/ {fmt(nac['x']['canon'].get('2026', {}).get('total_canon', 0) / 1e6)} M transferidos.</p>
<script>(function(){{const K={json.dumps(skl, ensure_ascii=False)},TC={json.dumps(tcolors, ensure_ascii=False)};
if(Chart.registry.controllers.get('sankey'))new Chart(document.getElementById('skNac'),{{type:'sankey',data:{{datasets:[{{data:K,colorFrom:c=>TC[c.raw.from]||'#8b9bc4',colorTo:c=>TC[c.raw.from]||'#3b82f6',colorMode:'gradient',color:'#e8edf7',size:'max',padding:8,font:{{size:11}}}}]}},
options:{{maintainAspectRatio:false,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+c.raw.from+' → '+c.raw.to+': S/ '+c.raw.flow.toLocaleString('es-PE')+' M'}}}}}}}}}});
const C={json.dumps(data, ensure_ascii=False)};new Chart(document.getElementById('chCanonNac'),{{type:'bar',data:{{labels:C.l,datasets:C.ds.map(d=>Object.assign({{stack:'c'}},d))}},
options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{boxWidth:12}}}}}},scales:{{x:{{stacked:true,grid:{{color:'rgba(139,155,196,.15)'}},ticks:{{callback:v=>v.toLocaleString('es-PE')}}}},y:{{stacked:true,grid:{{display:false}},ticks:{{autoSkip:false}}}}}}}}}});}})();</script></section>"""

def page_fuentes():
    url = f'{SITE}fuentes/'
    out = [head('FAQ y fuentes de datos | Proyecto INTI', 'De dónde salen los datos del Proyecto INTI: INEI, MINSA, MINEDU, MEF, SUNAT/BCRP. Fechas de corte y preguntas frecuentes.', url)]
    out.append('<div class="wrap"><nav class="top"><a class="brand" href="../">🌞 Proyecto INTI</a><span><a href="../region/">Regiones</a></span></nav>')
    out.append(f'<header class="cover" style="min-height:220px">{WAVES}<div class="emb">❓</div><div class="kicker">Proyecto INTI</div><h1>FAQ y fuentes</h1><p class="lead">Todo lo que mostramos viene de fuentes oficiales. Aquí está de dónde, con qué fecha de corte y cómo interpretarlo.</p></header>')
    out.append('<section class="faq"><h2>Preguntas frecuentes</h2>' + ''.join(f'<details{" open" if i < 2 else ""}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for i, (q, a) in enumerate(FAQ)) + '</section>')
    rows = ''.join(f'<tr><td>{esc(t)}</td><td><a href="{u}">{esc(f)}</a></td><td class="n">{esc(c)}</td></tr>' for t, f, c, u in FUENTES)
    out.append(f'<section><h2>📚 Fuentes y fechas de corte</h2><div class="card scroll"><table class="tbl"><thead><tr><th>Tema</th><th>Fuente</th><th>Corte</th></tr></thead><tbody>{rows}</tbody></table></div>'
               '<p class="src" style="margin-top:8px">Scripts de extracción y archivos intermedios: <a href="https://github.com/unimauro/proyecto-inti/tree/main/scripts">scripts/</a> y <a href="https://github.com/unimauro/proyecto-inti/tree/main/data/fuentes">data/fuentes/</a>.</p></section>')
    out.append(footer(depth=1))
    return '\n'.join(out)

def main():
    global RANKS
    regiones, nac = build()
    RANKS = rankings(regiones)
    for r in regiones.values():
        r['vals'] = {k: get(r) for k, _, get, *_ in RANK_IND}
    nx = nac['x']; ne = nac['endes']
    nac['vals'] = {'pobreza': nac['pobreza_serie'][-1], 'ingreso': nac['ingreso_real'][-1],
                   **{k: (ne.get(k) or {}).get('y2025') for k in ('anemia', 'dci', 'vacunas12m', 'cred', 'hierro', 'lactancia', 'saneamiento', 'violencia')},
                   'lectura': ((nx.get('enla') or {}).get('lectura') or {}).get('satisfactorio'), 'matematica': ((nx.get('enla') or {}).get('matematica') or {}).get('satisfactorio'),
                   'camas_10k': nx.get('camas_10k'), 'hab_medico': (nx.get('hab_medico') or [None])[-1], 'evn': (nx.get('evn') or [None])[0],
                   'tmi': (nx.get('tmi') or [None])[0], 'canon_pc': nx.get('canon_pc'), 'tax_pc': nx.get('tax_pc'), 'gasto_pc': nx.get('gasto_pc'), 'retorno': nx.get('retorno')}
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
    os.makedirs(D('fuentes'), exist_ok=True)
    open(D('fuentes/index.html'), 'w', encoding='utf-8').write(page_fuentes())
    urls.append(SITE + 'fuentes/')
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
