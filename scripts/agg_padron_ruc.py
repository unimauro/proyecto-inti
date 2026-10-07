#!/usr/bin/env python3
"""Cuenta contribuyentes ACTIVOS y HABIDOS del Padrón Reducido RUC de SUNAT por ubigeo.
Separa personas jurídicas (RUC 20…, empresas) y personas naturales con negocio (RUC 10…).
Uso: python3 agg_padron_ruc.py padron_reducido_ruc.zip out.json"""
import zipfile, io, sys, json, datetime
zp, out = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(zp); name = z.namelist()[0]
cnt = {}; n = 0; header = None
with z.open(name) as f:
    for raw in io.TextIOWrapper(f, encoding='latin-1', errors='replace'):
        parts = raw.rstrip('\n').split('|')
        if header is None: header = parts; ix = {k.strip().upper(): i for i, k in enumerate(parts)}; continue
        n += 1
        try:
            ruc = parts[0]; est = parts[ix['ESTADO DEL CONTRIBUYENTE']].strip(); cond = parts[ix['CONDICIÓN DE DOMICILIO']].strip(); ub = parts[ix['UBIGEO']].strip()
        except (KeyError, IndexError):
            continue
        if est != 'ACTIVO' or not ub or not ub.isdigit(): continue
        t = 'pj' if ruc.startswith('20') else ('pn' if ruc.startswith('10') else 'otros')
        c = cnt.setdefault(ub, {'pj': 0, 'pn': 0, 'otros': 0, 'habido_pj': 0})
        c[t] += 1
        if t == 'pj' and cond == 'HABIDO': c['habido_pj'] += 1
json.dump({'fuente': 'SUNAT — Padrón Reducido RUC', 'url': 'http://www2.sunat.gob.pe/padron_reducido_ruc.zip', 'fecha': datetime.date.today().isoformat(),
           'nota': 'Contribuyentes con estado ACTIVO, según el ubigeo del domicilio fiscal. pj = personas jurídicas (RUC 20, empresas); pn = personas naturales con negocio (RUC 10).',
           'filas_leidas': n, 'ubigeo': cnt}, open(out, 'w'))
print('filas', n, 'ubigeos', len(cnt), 'header', header[:12], file=sys.stderr)
