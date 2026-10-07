#!/usr/bin/env python3
"""En qué se gasta (streaming, stdin = CSV Gasto Devengado MEF). Agrega por departamento de la meta:
 - fun: rubro(canon|otros) x función -> [devengado, PIM]
 - gen: rubro x genérica -> [dev, PIM]
 - proy: (solo canon y todo) proyecto/actividad -> [dev, PIM, ejecutora]  (se guardan los top por depto)
 - eje: por ejecutora con canon: función -> [dev, PIM]
Excluye genéricas 2.4 (transferencias) y 2.8 (deuda). Uso: curl ... | python3 agg_gasto_detalle.py 2025 out.json"""
import csv, sys, io, json, heapq
year, out = sys.argv[1], sys.argv[2]
r = csv.reader(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace'))
h = next(r); ix = {k: i for i, k in enumerate(h)}
MES = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
mi = [ix.get('MONTO_DEVENGADO_' + m) for m in MES]
def f(x):
    try: return float(x)
    except: return 0.0
fun, gen, proy, eje = {}, {}, {}, {}
def add(d, k, dev, pim):
    a = d.get(k)
    if a is None: d[k] = [dev, pim]
    else: a[0] += dev; a[1] += pim
for row in r:
    try:
        g = row[ix['GENERICA']].strip()
        if g in ('4', '8'): continue
        dep = row[ix['DEPARTAMENTO_META_NOMBRE']].strip()
        canon = row[ix['RUBRO']].strip() == '18'
        rb = 'canon' if canon else 'otros'
        dev = f(row[ix['MONTO_DEVENGADO_ANUAL']]) if 'MONTO_DEVENGADO_ANUAL' in ix else 0.0
        if not dev: dev = sum(f(row[j]) for j in mi if j is not None)
        pim = f(row[ix['MONTO_PIM']])
        if not dev and not pim: continue
        fn = row[ix['FUNCION_NOMBRE']].strip()
        add(fun, f'{dep}|{rb}|{fn}', dev, pim)
        add(gen, f'{dep}|{rb}|{g} {row[ix["GENERICA_NOMBRE"]].strip()}', dev, pim)
        tipo = row[ix['TIPO_ACT_PROY']].strip()
        if tipo.upper().startswith('PROY'):
            pk = f"{dep}|{rb}|{row[ix['PRODUCTO_PROYECTO']].strip()}|{row[ix['PRODUCTO_PROYECTO_NOMBRE']].strip()[:160]}|{row[ix['EJECUTORA_NOMBRE']].strip()}|{fn}"
            add(proy, pk, dev, pim)
        if canon:
            ub = row[ix['DEPARTAMENTO_EJECUTORA']] + row[ix['PROVINCIA_EJECUTORA']] + row[ix['DISTRITO_EJECUTORA']]
            add(eje, f"{ub}|{row[ix['NIVEL_GOBIERNO']]}|{row[ix['EJECUTORA_NOMBRE']].strip()}|{fn}", dev, pim)
    except (IndexError, KeyError):
        continue
# top proyectos por depto y rubro (por PIM, para incluir los que no ejecutan)
best = {}
for k, v in proy.items():
    dep, rb = k.split('|', 2)[:2]
    best.setdefault((dep, rb), []).append((v[1], k, v))
proy_top = {}
for (dep, rb), lst in best.items():
    for _, k, v in heapq.nlargest(40, lst, key=lambda x: x[0]): proy_top[k] = v
json.dump({'year': year, 'fun': fun, 'gen': gen, 'proy': proy_top, 'eje': eje}, open(out, 'w'), ensure_ascii=False)
print(year, 'fun', len(fun), 'proy', len(proy), 'eje', len(eje), file=sys.stderr)
