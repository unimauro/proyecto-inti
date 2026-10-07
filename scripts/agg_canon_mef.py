#!/usr/bin/env python3
"""Agrega (streaming, stdin) el CSV MEF de Ingreso Recaudado: transferencias recibidas por gobiernos regionales
y locales del rubro 18 (canon, sobrecanon, regalías, renta de aduanas y participaciones) y del rubro 07 (Foncomun),
por departamento de la entidad receptora x nivel x concepto (específica detallada). Excluye saldos de balance.
Uso: curl -s .../2025-Ingreso-Recaudado-Mensual.csv | python3 scripts/agg_canon_mef.py 2025 out.json"""
import csv, sys, io, json
year, out = sys.argv[1], sys.argv[2]
r = csv.reader(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace'))
h = next(r); ix = {k: i for i, k in enumerate(h)}
MES = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
mi = [ix.get('MONTO_RECAUDADO_' + m) for m in MES]
def f(x):
    try: return float(x)
    except: return 0.0
agg = {}; meses = [0.0] * 12; n = 0
for row in r:
    try:
        rub = row[ix['RUBRO']]
        if rub not in ('18', '07') or row[ix['GENERICA']] == '9': continue
        dep = row[ix['DEPARTAMENTO_EJECUTORA_NOMBRE']].strip(); niv = row[ix['NIVEL_GOBIERNO']]
        con = 'FONCOMUN' if rub == '07' else row[ix['ESPECIFICA_DET_NOMBRE']].strip()
        mv = [f(row[j]) if j is not None else 0.0 for j in mi]
        tot = f(row[ix['MONTO_RECAUDADO_ANUAL']]) if 'MONTO_RECAUDADO_ANUAL' in ix else 0.0
        if not tot: tot = sum(mv)
    except (IndexError, KeyError):
        continue
    n += 1
    for k in range(12): meses[k] += mv[k]
    key = f'{dep}|{niv}|{con}'; agg[key] = agg.get(key, 0.0) + tot
json.dump({'year': year, 'rows': n, 'meses': meses, 'agg': agg}, open(out, 'w'), ensure_ascii=False)
print(year, 'rows', n, 'keys', len(agg), file=sys.stderr)
