# Green AI Simulator

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
Las métricas expuestas contienen las etiquetas `cluster` (el UUID del run), `node` y `origin="simulated"`. El servicio de **Monitoring** (Prometheus scraper) debe configurarse para leer el endpoint de este simulador de la siguiente manera:
1. El scrapeo debe ocurrir preferiblemente cada `5s` o `15s`.
2. Las consultas en el frontend/gateway se pueden filtrar por `cluster=sim-run-<uuid>`.
3. El simulador finaliza su proceso (stale) al completarse la `duration-seconds`.

## Uso con Docker
Puedes construir y ejecutar el contenedor que automáticamente se pone en modo `realtime` en el puerto `9090`.
```bash
docker build -t green-ai-simulator .
docker run -p 9090:9090 green-ai-simulator
```
