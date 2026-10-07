#!/usr/bin/env python3
"""Agrega (en streaming, desde stdin) el CSV de Gasto Devengado del MEF (Datos Abiertos) por
departamento de la META x nivel de gobierno x rubro x genérica. Uso:
  curl -s https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Devengado-Mensual.csv | python3 scripts/agg_gasto_mef.py 2025 out.json
"""
import csv, sys, json, io
year, out = sys.argv[1], sys.argv[2]
r = csv.reader(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace'))
h = next(r); ix = {k: i for i, k in enumerate(h)}
MES = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
mi = [ix.get('MONTO_DEVENGADO_' + m) for m in MES]
agg = {}; meses = [0.0] * 12; n = 0
def f(x):
    try: return float(x)
    except: return 0.0
for row in r:
    n += 1
    try:
        dep = row[ix['DEPARTAMENTO_META_NOMBRE']]; niv = row[ix['NIVEL_GOBIERNO']]
        rub = row[ix['RUBRO']] + ' ' + row[ix['RUBRO_NOMBRE']]; gen = row[ix['GENERICA']]
        dev = f(row[ix['MONTO_DEVENGADO_ANUAL']]) if 'MONTO_DEVENGADO_ANUAL' in ix else 0.0
        if not dev and mi[0] is not None: dev = sum(f(row[j]) for j in mi if j is not None)
        pim = f(row[ix['MONTO_PIM']])
    except (IndexError, KeyError):
        continue
    for k, j in enumerate(mi):
        if j is not None: meses[k] += f(row[j])
    key = f'{dep}|{niv}|{rub}|{gen}'
    a = agg.setdefault(key, [0.0, 0.0]); a[0] += dev; a[1] += pim
json.dump({'year': year, 'rows': n, 'meses': meses, 'agg': agg}, open(out, 'w'), ensure_ascii=False)
print(year, 'rows', n, 'keys', len(agg), file=sys.stderr)
