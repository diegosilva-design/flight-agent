---
description: Compara efectivo vs puntos vs mixto para un viaje. Uso /flights ORIGEN -> DESTINO, fechas, flexibilidad
argument-hint: SCL -> SLC, 2026-12-10 to 2026-12-20, flexible ±2 days, nearby airports ok
---

Usa el subagente `flight-evaluator` para evaluar esta búsqueda de vuelos:

$ARGUMENTS

Sigue el flujo completo del subagente (contexto, expandir búsqueda, efectivo, puntos y mixto, normalizar, calcular con `scripts/evaluate.py`, entregar recomendación con top 3 y riesgos).
