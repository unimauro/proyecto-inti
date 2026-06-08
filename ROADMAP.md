# 🗺️ Roadmap — Proyecto INTI (Gemelo Digital del Perú 2075)

Hoja de ruta para que INTI **sirva a todo el país**: de demostración a herramienta real
de planificación distrital basada en evidencia, útil para las **elecciones municipales**.

> 🔗 Dashboard: https://unimauro.github.io/proyecto-inti/
> Estado: **demostración funcional** con datos reales parciales + índices ilustrativos.

## ✅ Fase 0 — Base (hecho)
- [x] Dashboard ejecutivo: 12 índices con semáforos, diagnóstico, prospectiva 2075.
- [x] **1,834 distritos reales** (jerarquía + geometría) y **mapa nacional** (Leaflet, coropletas).
- [x] **Datos reales**: población **Censo 2017 (INEI)**, **IDH 2019 (PNUD)**, **pobreza/pobreza extrema**, **vulnerabilidad alimentaria**.
- [x] **Ranking nacional** por distrito (IDH y pobreza).
- [x] Planes descargables (PDF): Municipal 2027–2031 y Maestro 2075.
- [x] Motor de IA (OpenRouter) + proxy opcional. FAQ, tooltips y metodología. Compartir + temas.
- [x] 🎛️ **Simulador de políticas** (mueve palancas → impacto proyectado al 2075).

## 🚧 Fase 1 — Más datos reales por distrito
Prioridad y dependencias (lo que necesitamos para cada uno):
- [ ] 🏫 **Educación** — N.º de colegios/IIEE, aulas, matrícula, ECE. *Fuente: MINEDU ESCALE (padrón). Dependencia: descarga directa del CSV (hoy tras portal/captcha).*
- [ ] 🩺 **Salud** — anemia, desnutrición, vacunación, TBC, VIH. *Fuente: MINSA/ENDES. Nota: varios son **regionales**, no distritales → se marcarán como "dato regional".*
- [ ] 🏥 **Oferta de salud** — camas hospitalarias (incl. privado), personal médico. *Fuente: MINSA RENIPRESS / SUSALUD (ETL grande).*
- [ ] 💰 **Ingresos** — ingreso per cápita por distrito (ENAHO/INEI) y referencia SalariosPerú.
- [ ] 📉 Reemplazar progresivamente los índices ilustrativos por oficiales (marcando ●real).

**Qué ayudaría:** que la data sea **pública y descargable** (CSV/JSON). Donde haya captcha, se requiere un paso manual de descarga o un acuerdo de datos abiertos.

## 🧩 Fase 2 — Documentos base por distrito (para definir políticas)
- [ ] Generar un **"Documento Base Distrital"** estandarizado por cada uno de los 1,891 distritos: diagnóstico + brechas + cartera priorizada + metas. (Hoy se genera **on-demand** en PDF; objetivo: pre-generarlos y versionarlos).
- [ ] Catálogo nacional descargable (1 doc por distrito) para alcaldes/candidatos.
- [ ] Plantillas de **políticas tipo** vinculadas a cada brecha.

## 🏛️ Fase 3 — Simulación y participación
- [x] Simulador de políticas (palancas de inversión → impacto).
- [x] **Comparador de distritos** (hasta 4, datos reales + perfil de índices).
- [ ] **Comparador** entre distritos y benchmarking regional.
- [ ] **Benchmarking regional** y agrupamiento (clustering) de distritos por perfil.
- [ ] **Forecasting con datos reales**: proyecciones poblacionales y de pobreza basadas en series oficiales.
- [ ] Escenarios de política comparables entre distritos.

## 🔒 Fase 4 — Confianza y escala
- [ ] Fuentes y fecha visibles en cada dato (trazabilidad total).
- [ ] Exportar datos (CSV/JSON) y API pública.
- [ ] Versionado de datos por año censal (Censo 2017 → **Censo 2025** cuando INEI publique).
- [ ] Accesibilidad, i18n (quechua/aymara) y rendimiento móvil.

## 📌 Principios
- **Anti-overclaiming**: siempre distinguir dato **real** (con fuente y año) de **ilustrativo**.
- **Datos abiertos primero**. Evidencia sobre promesas. Participación ciudadana.

---
*Sugerencias y aportes: issues en este repo o vía [Carlos Mauro Cárdenas](https://unimauro.github.io/).*
