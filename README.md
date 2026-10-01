# Green AI Simulator

Inventario de 50 equipos y escenarios para la demostración: [guía MVP 1](docs/inventario-mvp1.md).

Simulador lógico, ejecutable mediante CLI, con persistencia local y un adaptador Prometheus para el proyecto Green AI.

## Alcance del Incremento 1

- Generación sintética determinista de métricas (CPU, memoria, red, disco) a partir de semillas (fixtures).
- Ejecución en modo `offline` (cálculo rápido persistido en disco).
- Ejecución en modo `realtime` (tiempo 1x y exportación mediante `/metrics` de Prometheus).
- Mínimas dependencias (`prometheus-client`).
- Independiente del acceso a Supabase, base de datos relacional, o despliegues de Kubernetes (se agregará en futuros incrementos).

## Instrucciones de Instalación

Este proyecto utiliza `uv` para la gestión de dependencias, garantizando la consistencia y reproducibilidad sin contaminar el entorno global.

### Requisitos

- Python 3.12 o superior.
- `uv` instalado.

## Comandos de Instalación

1. (Opcional pero recomendado) Crea un entorno virtual y sincroniza las dependencias:
   ```bash
   uv sync
   ```
2. Activa el entorno virtual:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

## Modo Offline (Generación Rápida)
Ejecuta una simulación completa sin esperar el tiempo real. Útil para pruebas, generación de datos masivos y validación lógica.
```bash
green-ai-simulator run \
  --inventory configs/inventory.synthetic.json \
  --scenario configs/scenarios/high.json \
  --seed 42 \
  --duration-seconds 60 \
  --tick-seconds 1 \
  --mode offline \
  --output-dir runs
```

## Modo Realtime (Prometheus)
El reloj avanzará 1 segundo real por cada tick lógico. Expondrá un servidor HTTP en `http://127.0.0.1:9090/metrics`.
```bash
green-ai-simulator run \
  --inventory configs/inventory.synthetic.json \
  --scenario configs/scenarios/high.json \
  --seed 42 \
  --duration-seconds 3600 \
  --tick-seconds 5 \
  --mode realtime \
  --output-dir runs \
  --host 127.0.0.1 --port 9090
```

### Integración con Monitoring
Las métricas expuestas contienen las etiquetas `cluster` (`sim-run-<uuid>`), `node` y `origin="simulated"`. Prometheus recolecta `/metrics` del Simulator y Monitoring consulta Prometheus. Configurar Monitoring con `monitoring.prometheus.instance-label=node` para preservar el ID del inventario. La integración requiere:
1. El scrapeo debe ocurrir preferiblemente cada `5s` o `15s`.
2. Las consultas en el frontend/gateway se pueden filtrar por `cluster=sim-run-<uuid>`.
3. El simulador finaliza su proceso (stale) al completarse la `duration-seconds`.

## Uso con Docker
Puedes construir y ejecutar el contenedor que automáticamente se pone en modo `realtime` en el puerto `9090`.
```bash
docker build -t green-ai-simulator .
docker run -p 9090:9090 green-ai-simulator
```

## Modelo de base de datos

## Verificación de entrega (2026-09-30)

La imagen instala dependencias mediante `uv sync --locked --no-dev` y excluye entornos locales, secretos y runs del contexto de construcción. Se rechazan duraciones no positivas y el límite de 100 MiB se comprueba antes de escribir cada registro completo.

Cinco pruebas pasaron dentro de Docker con Python 3.12: determinismo/etiquetas, duración inválida, límite de escritura, finalización offline con JSONL y manifest, y exporter realtime con parada SIGTERM en estado STOPPED. El flujo Simulator → Prometheus → Monitoring → Data Processing también devolvió las cinco métricas preservando su origen simulado.

Desde este repositorio, en PowerShell:

```powershell
docker build -t green-ai-simulator:local .
docker run --rm --entrypoint python --mount "type=bind,source=$($PWD.Path)\tests,target=/tests,readonly" green-ai-simulator:local -m unittest discover -s /tests -v
```

La simulación termina al alcanzar su duración; no equivale a una fuente permanente. Los archivos `/app/runs` pertenecen al contenedor: copiarlos con `docker cp` antes de eliminarlo o recrearlo si se necesitan como evidencia. El Compose del workspace utiliza el puerto interno 8000; el ejemplo independiente de arriba utiliza 9090.

No se incluye lectura de inventario Supabase, control HTTP de runs ni Kubernetes en este incremento. El inventario sintético está declarado como tal; no se calculan watts o energía a partir de CPU.

### Referencia del modelo de datos

El [modelo de BD](docs/modelo-bd.md) incluye el diagrama recibido el 2026-09-22, las tres tablas completas y las correspondencias de identidad, unidades y procedencia. Documenta los límites actuales y los requisitos del futuro adaptador de inventario.
