#!/usr/bin/env python3
"""Une det_YYYY.json (agg_gasto_detalle.py) en data/fuentes/mef_gasto_detalle.json: por departamento y año,
funciones (canon y total), genéricas del canon, top proyectos con canon y top proyectos totales; y por ejecutora con canon."""
import json, sys, glob, os, datetime
src, out = sys.argv[1], sys.argv[2]
R = lambda v: [round(v[0]), round(v[1])]
deps, ejes = {}, {}
for fpath in sorted(glob.glob(os.path.join(src, 'det_*.json'))):
    d = json.load(open(fpath)); y = d['year']
    for k, v in d['fun'].items():
        dep, rb, fn = k.split('|', 2)
        deps.setdefault(dep, {}).setdefault(y, {}).setdefault('fun_' + rb, {})[fn] = R(v)
    for k, v in d['gen'].items():
        dep, rb, g = k.split('|', 2)
        deps.setdefault(dep, {}).setdefault(y, {}).setdefault('gen_' + rb, {})[g] = R(v)
    for k, v in d['proy'].items():
        dep, rb, cui, nom, ej, fn = k.split('|', 5)
        deps.setdefault(dep, {}).setdefault(y, {}).setdefault('proy_' + rb, []).append({'cui': cui, 'n': nom, 'e': ej, 'f': fn, 'dev': round(v[0]), 'pim': round(v[1])})
    for k, v in d['eje'].items():
        ub, niv, nom, fn = k.split('|', 3)
        ejes.setdefault(f'{ub}|{niv}|{nom}', {}).setdefault(y, {})[fn] = R(v)
for dep in deps.values():
    for y, dy in dep.items():
        for rb in ('canon', 'otros'):
            if 'proy_' + rb in dy:
                dy['proy_' + rb] = sorted(dy['proy_' + rb], key=lambda p: -p['pim'])[:15]
# ejecutoras: solo con canon relevante (> S/ 1 M de PIM en algún año)
ejes = {k: v for k, v in ejes.items() if any(sum(x[1] for x in fy.values()) > 1e6 for fy in v.values())}
json.dump({'fuente': 'MEF — Datos Abiertos, Gasto Devengado (función, genérica, proyecto, rubro de financiamiento)',
           'url': 'https://datosabiertos.mef.gob.pe/', 'nota': 'Canon = rubro 18 (canon, sobrecanon, regalías, renta de aduanas y participaciones). Excluye genéricas 2.4 y 2.8. Valores [devengado, PIM] en soles.',
           'procesado': datetime.date.today().isoformat(), 'departamentos': deps, 'ejecutoras': ejes},
          open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('deps', len(deps), 'ejecutoras', len(ejes))
