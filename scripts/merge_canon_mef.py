#!/usr/bin/env python3
"""Une canon_YYYY.json (scripts/agg_canon_mef.py) en data/fuentes/mef_canon_departamentos.json,
clasificando cada específica en un tipo de canon/regalía. Montos = transferencias recaudadas por GR + GL del departamento."""
import json, sys, glob, os, datetime, unicodedata
src, out = sys.argv[1], sys.argv[2]
def n(x): return ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn').upper()
TIPOS = [  # (clave, etiqueta, función de match sobre el nombre normalizado)
    ('minero', 'Canon minero', lambda s: s == 'CANON MINERO'),
    ('gasifero', 'Canon gasífero (Camisea)', lambda s: s.startswith('CANON GASIFERO')),
    ('regalias', 'Regalías mineras', lambda s: s in ('REGALIAS MINERAS', 'REGALIA DE LA ACTIVIDAD MINERA')),
    ('petrolero', 'Canon petrolero', lambda s: s == 'CANON PETROLERO'),
    ('sobrecanon', 'Sobrecanon petrolero', lambda s: s == 'SOBRECANON PETROLERO'),
    ('focam', 'FOCAM (Camisea)', lambda s: 'FOCAM' in s),
    ('hidro', 'Canon hidroenergético', lambda s: s.startswith('CANON HIDRO')),
    ('pesquero', 'Canon pesquero', lambda s: s.startswith('CANON PESQUERO')),
    ('forestal', 'Canon forestal', lambda s: s.startswith('CANON FORESTAL')),
    ('aduanas', 'Renta de aduanas', lambda s: s.startswith('RENTA DE ADUANAS')),
    ('participaciones', 'Participaciones (eliminación de exoneraciones)', lambda s: s.startswith('PARTICIPACION POR ELIMINACION')),
    ('foncomun', 'Foncomun', lambda s: s == 'FONCOMUN'),
]
def tipo(nombre):
    s = n(nombre)
    for k, _, f in TIPOS:
        if f(s): return k
    return 'otros'
MES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','setiembre','octubre','noviembre','diciembre']
deps, tot, cortes = {}, {}, {}
for f in sorted(glob.glob(os.path.join(src, 'canon_*.json'))):
    d = json.load(open(f)); y = d['year']
    cortes[y] = MES[max((i for i, v in enumerate(d['meses']) if v > 1e7), default=11)]
    for key, v in d['agg'].items():
        dep, niv, con = key.split('|'); t = tipo(con)
        for tgt in (deps.setdefault(dep, {}).setdefault(y, {}), tot.setdefault(y, {})):
            tgt[t] = tgt.get(t, 0) + v
            tgt['niv_' + {'R': 'regional', 'M': 'local', 'E': 'universidades'}.get(niv, niv)] = tgt.get('niv_' + {'R': 'regional', 'M': 'local', 'E': 'universidades'}.get(niv, niv), 0) + (v if t not in ('foncomun', 'otros') else 0)
CANON_KEYS = [k for k, *_ in TIPOS if k not in ('foncomun',)]
for d in list(deps.values()) + [tot]:
    for y, v in d.items(): v['total_canon'] = sum(v.get(k, 0) for k in CANON_KEYS)
R = lambda d: {y: {k: round(v) for k, v in vv.items()} for y, vv in d.items()}
y26 = max(cortes) if cortes else ''
json.dump({'fuente': 'MEF — Datos Abiertos, Presupuesto de Ingresos (ingreso recaudado) de gobiernos regionales y locales, rubros 18 y 07',
           'url': 'https://datosabiertos.mef.gob.pe/', 'unidad': 'soles corrientes',
           'nota': 'Transferencias efectivamente recaudadas por el gobierno regional y las municipalidades del departamento. total_canon = canon (minero, gasífero, petrolero, hidroenergético, pesquero, forestal), sobrecanon, regalías, FOCAM, renta de aduanas y participaciones. Foncomun aparte.',
           'tipos': [{'k': k, 'l': l} for k, l, _ in TIPOS], 'corte_2026': f'{cortes.get(y26, "")} {y26}', 'cortes': cortes,
           'procesado': datetime.date.today().isoformat(), 'departamentos': {k: R(v) for k, v in deps.items()}, 'total': R(tot)},
          open(out, 'w'), ensure_ascii=False, indent=0)
print('cortes', cortes); print({y: round(v['total_canon'] / 1e6) for y, v in tot.items()})
