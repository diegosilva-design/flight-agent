## Qué cambia

<!-- Una o dos líneas: qué cambia y por qué -->

## Checklist de QA (antes de hacer merge a `main`)

Hacer merge publica el cambio en el sitio de prueba.

- [ ] `python scripts/evaluate.py data/sample_options.json` corre sin errores
- [ ] La página de prueba carga sin errores en la consola del navegador
- [ ] "Cargar ejemplo" + "Evaluar" muestra la recomendación y el ranking
- [ ] Cambiar un cpp o saldo en la billetera cambia el resultado
- [ ] Se lee bien en un teléfono (sin scroll lateral fuera de las tablas)

## Después del merge

- [ ] Esperar 1–2 minutos y abrir https://diegosilva-design.github.io/flight-agent/ para una prueba rápida
