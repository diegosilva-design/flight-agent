# Flight Deal Evaluator (Claude Code)

Agente que, dado origen, destino y fechas (fijas o flexibles, con aeropuertos cercanos), compara **efectivo vs puntos vs mixto** y recomienda qué reservar y con qué método de pago.

## Instalación
```bash
cd flight-agent
pip install -r requirements.txt     # PyYAML
claude                              # abre Claude Code en esta carpeta
```
Para buscar en vivo necesitas la extensión **Claude in Chrome** (Google Flights y sitios de aerolíneas con tus sesiones iniciadas). Opcional: cuenta en seats.aero para disponibilidad de premios multi-programa.

## Configuración (una vez)
1. `config/wallet.yaml`: tus saldos, el valor en centavos (`cpp`) que le asignas a cada punto, y qué monedas financian cada programa. Anota bonos de transferencia vigentes.
2. `config/preferences.yaml`: cuánto vale tu tiempo por hora, penalización por escala, máximo de escalas, aeropuertos cercanos.

## Uso
```
/flights SCL -> SLC, 2026-12-10 to 2026-12-20
/flights CHO -> SCL, ida 12-10, vuelta entre 12-18 y 12-24, aeropuertos cercanos ok
/flights NYC -> LIM, flexible ±3 días, solo ida, puntos Chase y Amex
```

## Cómo decide
Costo efectivo = `cash desembolsado + (puntos usados × tu cpp) + penalización por tiempo extra + penalización por escalas`.
- **Mixto/premio**: elige la moneda más barata (según tu cpp) entre las que pueden financiar el programa, aplicando bonos de transferencia. Si no te alcanza, queda en "No financiables".
- **cpp obtenido** = (cash de ese mismo vuelo − cash que pagas) / puntos usados × 100. Si supera tu cpp de referencia → `USAR PUNTOS`; si no → `PAGAR CASH`.
- Opciones no verificadas, de otra cabina o con demasiadas escalas se excluyen y se listan aparte.

## Esquema de `options.json`
```json
{
  "search": {"origin": "SCL", "destination": "SLC", "depart": "2026-12-10", "return": "2026-12-20", "cabin": "economy"},
  "options": [
    {"id": "C1", "type": "cash", "airline": "Delta", "route": "SCL-ATL-SLC", "origin": "SCL", "destination": "SLC",
     "depart_date": "2026-12-10", "return_date": "2026-12-20", "stops": 1, "duration_min": 1260,
     "cabin": "economy", "fare_type": "main", "cash_price": 1180, "source": "google_flights", "retrieved_at": "2026-10-21", "link": "..."},
    {"id": "A1", "type": "award", "program": "United MileagePlus", "points": 70000, "taxes_fees": 95, "...": "..."},
    {"id": "M1", "type": "points_and_cash", "currency": "Delta SkyMiles", "points": 10000, "cash": 1000, "...": "..."}
  ]
}
```
- `type`: `cash` | `award` | `points_and_cash`.
- `award` usa `program` (+ `points`, `taxes_fees`); `points_and_cash` usa `currency` (moneda directa, p. ej. portal de tarjeta) o `program`, más `points` y `cash`.
- `itinerary_key` (opcional) fuerza qué cash se usa como referencia para medir cpp.
- `unverified: true` deja la opción fuera del ranking (usa `--include-unverified` para verla).

Prueba el motor sin buscar nada: `python scripts/evaluate.py data/sample_options.json` (datos de ejemplo, no son tarifas reales).

## Limitaciones conocidas
- No combina transferencias de varias monedas para un mismo premio (p. ej. 30k Chase + 30k Amex).
- La calidad del resultado depende de las fuentes consultadas en cada corrida; el agente no inventa tarifas y marca lo no verificado.
- No reserva ni transfiere puntos: eso lo haces tú después de confirmar en vivo.
