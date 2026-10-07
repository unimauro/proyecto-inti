# 🌞 Proyecto INTI — Gemelo Digital del Perú 2075

**Sistema Nacional de Inteligencia Territorial y Desarrollo Distrital.**

Dashboard ejecutivo que cubre (como objetivo) los **1,891 distritos del Perú** y genera
diagnósticos, índices, proyecciones, recomendaciones y **planes municipales automáticos**.

🔗 **Live:** https://unimauro.github.io/proyecto-inti/

## Módulos
- 📊 **Resumen ejecutivo** — población proyectada (10/25/50 años) + 12 índices con semáforos.
- 🔬 **Diagnóstico profundo** — demografía, economía, educación, salud, seguridad, vivienda, ambiente, infraestructura.
- 👨‍👩‍👧‍👦 **Fortalecimiento Familiar** — índice propio + recomendaciones de tejido social.
- 🔮 **Prospectiva 2075** — escenarios Conservador / Esperado / Transformador.
- 🌦️ **Cambio climático**, ⚖️ **Conflictos socioambientales**, 🛡️ **Seguridad y resiliencia**.
- 💡 **Oportunidades económicas**, 🏗️ **Proyectos prioritarios** (Top 10/25/50).
- 🔗 **Interconexión territorial** (corredores), 🤖 **Motor de consultas (IA)**.
- 📄 **Planes descargables (PDF)**: Plan Municipal 2027–2031 y Plan Maestro 2075.

## 🗺️ Carátulas por región (oct-2026)
Cada una de las 25 regiones tiene su página propia: `/region/<slug>/` (ej. [Cusco](https://unimauro.github.io/proyecto-inti/region/cusco/)),
con portada, KPIs y tablas de **datos oficiales 2025**: pobreza monetaria 2016–2025 (INEI/ENAHO), anemia, desnutrición, vacunas,
CRED, hierro, agua, saneamiento y violencia (INEI/ENDES 2025), y viviendas/servicios del **Censo 2025** (notas INEI, donde ya se publicaron).
Cusco incluye una sección ampliada (vivienda, energía para cocinar, migración, educación, turismo).
Cada carátula incluye además un **ranking visual entre las 25 regiones** (13 indicadores) y un gráfico de pobreza/IDH por provincia.
En el dashboard, la sección **📊 Cuadro de indicadores regionales 2025** muestra ranking por indicador, ficha de la región y tabla comparativa ordenable (descarga CSV).

**Memoria del chatbot:** `data/memoria_chat.json` (generada por el script) contiene los hechos oficiales 2025 de cada región, el nacional y los rankings.
El motor de IA la inyecta como contexto al LLM (si hay `proxy`/`apiKey` en `config.js`) y, sin LLM, responde directamente rankings, comparaciones
("Compara Cusco y Puno"), fichas de región e indicadores puntuales con esos datos.

El dashboard acepta enlaces directos: `?region=cusco` o `?u=081301` (ubigeo).

**Fiscal, salud y educación (oct-2026):** cada carátula muestra además cuánto recauda la región (SUNAT/BCRP, 2015 → jul-2026) y cuánto gasto público
se ejecuta en ella (MEF Datos Abiertos, 2019 → set-2026, sin transferencias ni deuda), camas hospitalarias y médicos (Compendio INEI 2025), nacimientos
(inscritos 2017-2023 y CNV 2026), defunciones (SINADEF a set-2026), esperanza de vida y mortalidad infantil (INEI) y lectura/matemática (ENLA 2024).
FAQ y tabla de fuentes con fechas de corte: [/fuentes/](https://unimauro.github.io/proyecto-inti/fuentes/).

Gasto MEF (CSV de ~2,5 GB por año, se procesa en streaming):
`curl -s https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Devengado-Mensual.csv | python3 scripts/agg_gasto_mef.py 2026 /tmp/gasto_2026.json`
y luego `python3 scripts/merge_gasto_mef.py /tmp data/fuentes/mef_gasto_departamentos.json`.

Canon por tipo (minero, gasífero, petrolero, sobrecanon, regalías, FOCAM, hidroenergético, pesquero, forestal, renta de aduanas, Foncomun):
MEF Presupuesto de Ingresos (~100 MB/año) → `scripts/agg_canon_mef.py` + `scripts/merge_canon_mef.py` → `data/fuentes/mef_canon_departamentos.json`.
La portada `/region/` incluye los cuadros **💸 Gasto público por persona** y **⛏️ Canon por región y tipo**.

**Provincias:** `region/<region>/<provincia>/` (196 carátulas): indicadores distritales, canon de sus municipalidades,
Sankey tipo → municipalidad → función → gastado/sin gastar y tabla de distritos (incluye distritos creados después de 2016).
**Empresas detrás del canon:** `data/fuentes/empresas_canon.json` (15 empresas, solo cifras publicadas con fuente).
**Navegación:** `assets/nav.js` (menú lateral / "☰ Secciones" en móvil).

**Chat:** usa el gateway propio `ai.tunky.net` si `config.js` tiene `token` (proyecto `proyecto-inti` en el servidor); sin token responde en modo memoria.

Regenerar: `python3 scripts/build_regiones.py` (lee `data/fuentes/*.json`; parsers en `scripts/parse_*.py`).

## 📊 Sobre los datos
**Datos reales** (1,892 distritos): IDH 2019, % de pobreza y pobreza extrema, y población
estimada 2020 — fuentes **PNUD/INEI** vía [ubigeo-peru-aumentado](https://github.com/jmcastagnetto/ubigeo-peru-aumentado);
geometrías de [peru-geojson](https://github.com/juaneladio/peru-geojson). El **motor de IA** usa **OpenRouter**
(configurable, con proxy Vercel opcional en `proxy-vercel/`).

⚠️ Los **demás índices** (seguridad, educación, salud, etc.) son **ilustrativos** (sintéticos pero consistentes por distrito).
La arquitectura está lista para integrar **fuentes oficiales**: INEI, MEF, MINSA, MINEDU,
SENAMHI, IGP, INDECI, CENEPRED.

## Stack
`index.html` único (HTML + CSS + JS vanilla) + Chart.js. Sin backend. GitHub Pages.

> "Construir un Perú seguro, próspero, innovador, sostenible y resiliente, con familias fuertes y oportunidades para todos hacia 2075."
