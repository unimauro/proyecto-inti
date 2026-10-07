#!/usr/bin/env python3
"""Une los agregados de scripts/agg_gasto_mef.py (gasto_YYYY.json) en data/fuentes/mef_gasto_departamentos.json.
Gasto 'que regresa' = devengado por departamento de la meta, 3 niveles de gobierno, SIN la genérica 2.4
(donaciones y transferencias, para no contar dos veces lo que una entidad transfiere a otra)."""
import json, sys, glob, os, datetime
src, out = sys.argv[1], sys.argv[2]
MES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','setiembre','octubre','noviembre','diciembre']
deps, total, cortes, meta_years = {}, {}, {}, []
for f in sorted(glob.glob(os.path.join(src, 'gasto_*.json'))):
    d = json.load(open(f)); y = d['year']; meta_years.append(y)
    ult = max((i for i, v in enumerate(d['meses']) if v > 1e8), default=11)
    cortes[y] = MES[ult]
    for key, (dev, pim) in d['agg'].items():
        dep, niv, rub, gen = key.split('|')
        if gen.strip() == '4':  # 2.4 donaciones y transferencias
            continue
        for tgt in (deps.setdefault(dep.strip(), {}).setdefault(y, {}), total.setdefault(y, {})):
            for k, v in (('dev', dev), ('pim', pim)):
                tgt[k] = tgt.get(k, 0) + v
            nk = {'E': 'nacional', 'R': 'regional', 'M': 'local'}.get(niv, niv)
            tgt['dev_' + nk] = tgt.get('dev_' + nk, 0) + dev
            if rub.startswith('18 '): tgt['canon'] = tgt.get('canon', 0) + dev
            if rub.startswith('07 '): tgt['foncomun'] = tgt.get('foncomun', 0) + dev
r = lambda d: {y: {k: round(v) for k, v in vv.items()} for y, vv in d.items()}
y26 = max(meta_years) if meta_years else None
json.dump({'fuente': 'MEF — Datos Abiertos, Presupuesto y Ejecución del Gasto (Gasto Devengado), por departamento de la meta',
           'url': 'https://datosabiertos.mef.gob.pe/', 'unidad': 'soles corrientes',
           'nota': 'Devengado de los tres niveles de gobierno según el departamento donde se ejecuta la meta; excluye la genérica 2.4 (transferencias entre entidades). canon = rubro 18 (canon, sobrecanon, regalías, renta de aduanas y participaciones); foncomun = rubro 07.',
           'corte_2026': f"{cortes.get(y26, '')} {y26}" if y26 else '', 'cortes': cortes, 'procesado': datetime.date.today().isoformat(),
           'departamentos': {k: r(v) for k, v in deps.items()}, 'total': r(total)},
          open(out, 'w'), ensure_ascii=False, indent=0)
print('deps', sorted(deps)[:40]); print('total', {y: round(v['dev'] / 1e9, 1) for y, v in total.items()}, 'cortes', cortes)
