#!/usr/bin/env python3
"""Extrae tablas 'según departamento' del Compendio Estadístico INEI (pdftotext -layout).
Los miles vienen separados por espacio ('18 117'), ambiguo con columnas; se resuelve con
programación dinámica: N valores esperados y mínima variación logarítmica entre años."""
import re, sys, json, math, functools
DEPS = ['Total','Amazonas','Áncash','Apurímac','Arequipa','Ayacucho','Cajamarca','Prov. Const. del Callao','Cusco','Huancavelica','Huánuco',
        'Ica','Junín','La Libertad','Lambayeque','Lima Metropolitana','Región Lima','Lima','Loreto','Madre de Dios','Moquegua','Pasco','Piura',
        'Puno','San Martín','Tacna','Tumbes','Ucayali']
def segment(toks, n):
    toks = tuple(toks)
    @functools.lru_cache(None)
    def go(i, k, prev):
        if i == len(toks): return (0.0, ()) if k == n else (math.inf, ())
        if k == n: return (math.inf, ())
        best = (math.inf, ())
        for j in range(i + 1, min(len(toks), i + 3) + 1):
            grp = toks[i:j]
            if j - i > 1 and not (1 <= len(grp[0]) <= 3 and all(len(g) == 3 for g in grp[1:])): continue
            v = float(''.join(grp).replace(',', '.'))
            cost = 0.0 if prev is None else abs(math.log((v + 1) / (prev + 1)))
            c, rest = go(j, k + 1, v)
            if cost + c < best[0]: best = (cost + c, (v,) + rest)
        return best
    c, vals = go(0, 0, None)
    return list(vals) if c < math.inf else None
def parse(txt, title_regex, n):
    lines = txt.split('\n'); i = next(k for k, l in enumerate(lines) if re.search(title_regex, l))
    out = {}
    for l in lines[i:i + 90]:
        s = l.strip()
        d = next((d for d in DEPS if s.startswith(d)), None)
        if not d or d in out: continue
        rest = re.sub(r'\d+/', '', s[len(d):])
        toks = re.findall(r'\d+(?:,\d+)?', rest)
        vals = segment(toks, n)
        if vals: out[d] = vals
    return out
if __name__ == '__main__':
    txt = open(sys.argv[1], encoding='utf-8').read()
    res = {}
    for key, rx, n, years in [('camas', r'6\.4 NÚMERO DE CAMAS HOSPITALARIAS', 11, list(range(2014, 2025))),
                              ('medicos', r'6\.5 NÚMERO DE MÉDICOS COLEGIADOS', 10, list(range(2015, 2025))),
                              ('hab_por_medico', r'6\.6 NÚMERO DE HABITANTES POR CADA MÉDICO', 10, list(range(2015, 2025))),
                              ('nacimientos_inscritos', r'3\.32 NACIMIENTOS INSCRITOS POR AÑO', 7, list(range(2017, 2024)))]:
        res[key] = {'years': years, 'v': parse(txt, rx, n)}
        print(key, len(res[key]['v']), res[key]['v'].get('Cusco'), res[key]['v'].get('Total'), file=sys.stderr)
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
