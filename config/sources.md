# Fuentes de datos (en orden de prioridad)

## Efectivo
1. **Google Flights** (navegador, vía Claude in Chrome): grilla de fechas y gráfico de precios sirven para explorar flexibilidad; luego abrir los 3-5 mejores candidatos. Incluir aeropuertos cercanos separándolos por coma en origen/destino.
2. **Sitios de la aerolínea** para confirmar precio final y tipo de tarifa del candidato elegido.
3. APIs opcionales si el usuario configura llave: Amadeus Self-Service, Duffel, SerpApi (Google Flights).

## Premios (puntos)
1. **seats.aero** (requiere cuenta; Pro para API): disponibilidad de premios en múltiples programas a la vez.
2. **Sitios de cada programa** (United, Delta, Aeroplan, BA Avios, etc.) para confirmar puntos e impuestos exactos.
3. Búsqueda web solo para contexto (bonos de transferencia vigentes, cambios de tabla de premios), nunca como fuente de disponibilidad.

## Mixto (puntos + efectivo)
- Programas con "Pay with Miles/Points" (p. ej. Delta, Alaska, Chase/Amex travel portals con puntos como descuento en cash).
- Portal de viajes de la tarjeta: puntos fijos (p. ej. 1 punto = 1-1.5 centavo) aplicados contra el precio cash. Registrar como `points_and_cash` con los puntos usados y el cash restante.

## Reglas
- Cada opción lleva `source` y `retrieved_at`.
- Si un sitio exige login/captcha, el agente se detiene y pide al usuario que lo haga; nunca ingresa contraseñas ni resuelve captchas.
