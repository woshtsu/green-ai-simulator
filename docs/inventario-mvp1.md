# Inventario MVP 1

Se conserva la exportación entregada por el equipo el 2026-10-01 en
`configs/hardware.snapshot.csv`: 50 equipos activos, HW001–HW050, 1952 cores
declarados. La publicación original no estuvo disponible para verificarla.

`configs/inventory.hardware.json` es la adaptación local ejecutable. No es una
conexión ni sincronización automática con Supabase. No requiere credenciales.
Las modificaciones futuras del inventario deben reflejarse en ambos archivos.

Supuestos explícitos:
- `ram_gb` se interpreta provisionalmente como GB decimal (1 GB = 1000000000 bytes).
- `cpu_cores` se usa como cantidad de CPU lógicas del modelo; no se deduce SMT.
- Cada equipo recibe una interfaz ficticia eth0 de 1 Gbit/s y un disco ficticio
  de 100 GB. No son características verificadas del centro de datos.
- `max_watts` se conserva solo en el CSV. No se generan potencia, energía o
  emisiones sin un modelo sustentado. Los históricos no calibran estos perfiles.
- Las capacidades adaptadas se marcan como modeling_assumption y todas las
  métricas generadas mantienen origin=simulated.

Se amplía el límite agregado a 4096 CPU para admitir este inventario; siguen
vigentes los límites de nodos y almacenamiento de resultados.

## Ejecutar desde el workspace

El Compose usa este inventario y el perfil normal por defecto. Para reconstruir
y activar únicamente Simulator:

```powershell
docker compose build simulator
docker compose up -d --no-deps simulator
```

Esto reinicia la simulación y genera otro cluster sim-run-UUID. Selecciona ese
clúster y HW001 (u otro equipo) en el panel. La inferencia necesita acumular de
nuevo aproximadamente 30–40 minutos de muestras útiles.

Para elegir escenario y una sesión de dos horas, antes de ejecutar compose:

```powershell
$env:SIMULATOR_SCENARIO = 'configs/scenarios/high.json'
$env:SIMULATOR_DURATION_SECONDS = '7200'
```

Perfiles disponibles: low (20% CPU), normal (50%) y high (85%), con ruido
determinista. Son porcentajes relativos a la capacidad; no un modelo de reparto
de trabajos. Cambiar perfil reinicia el run, no es un cambio en caliente.
El escenario normal y low usan 5 puntos porcentuales de ruido, high usa 10.
Red y disco también son sintéticos. El proceso termina al cumplir la duración
o el límite de archivos de salida; no constituye una fuente permanente.

La imagen independiente conserva su fixture pequeño como valor predeterminado.
Para ella, indicar --inventory configs/inventory.hardware.json explícitamente.
