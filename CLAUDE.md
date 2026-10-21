# Flight Deal Evaluator

Proyecto de Claude Code que compara opciones de vuelo en **efectivo, puntos/millas o mixto (puntos + efectivo)** y recomienda las mejores.

## Cómo se usa
```
/flights SCL -> SLC, 2026-12-10 to 2026-12-20, flexible ±2 days, nearby airports ok
```
El comando delega en el subagente `flight-evaluator`.

## Reglas del proyecto
- Los precios y la disponibilidad de premios cambian en minutos: **nunca** inventes tarifas. Todo número debe venir de una fuente consultada en esta corrida y registrada en el campo `source` de cada opción.
- Si no puedes verificar una fuente (login, captcha, sin API key), dilo explícitamente y marca la opción como `unverified`.
- Nunca ingreses datos de pago ni completes una compra. El agente termina entregando links/instrucciones para que el usuario reserve.
- La matemática (costo efectivo, cpp, ranking) se hace SIEMPRE con `scripts/evaluate.py`, no "a ojo".
- Saldos y valoraciones del usuario viven en `config/wallet.yaml`; preferencias de viaje en `config/preferences.yaml`. Léelos antes de cada búsqueda.
- Cada corrida guarda su JSON de entrada y su reporte en `data/runs/<fecha>_<ORIGEN>-<DESTINO>/`.

## Flujo
1. Parsear input (origen(es), destino(s), fechas, flexibilidad) y expandir aeropuertos cercanos con `config/preferences.yaml`.
2. Recolectar precios en efectivo (ver `config/sources.md`).
3. Recolectar disponibilidad de premios y co-pago puntos+efectivo.
4. Normalizar todo a `data/runs/.../options.json` (esquema en `README.md`).
5. `python scripts/evaluate.py data/runs/.../options.json` -> ranking + reporte.
6. Presentar top 3, una recomendación clara y los riesgos (verificar en vivo antes de reservar).
