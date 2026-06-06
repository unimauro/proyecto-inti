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
