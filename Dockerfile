FROM python:3.12-slim

# Evitar escritura de bytecode y obligar stdout a flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear un usuario no root
RUN useradd -m -s /bin/bash simuser

WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar los metadatos de dependencias y el lockfile
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Instalar exactamente las dependencias fijadas por uv.lock
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Copiar directorios de configuración y preparar salida
COPY configs/ ./configs/
RUN mkdir /app/runs && chown simuser:simuser /app/runs

USER simuser

# Escuchar en todas las interfaces para Prometheus
ENV HOST=0.0.0.0
ENV PORT=9090

# Exponer el puerto de Prometheus
EXPOSE 9090

# Punto de entrada predeterminado
ENTRYPOINT ["green-ai-simulator"]

# Argumentos por defecto si solo se ejecuta `docker run` (modo realtime)
CMD ["run", "--inventory", "configs/inventory.synthetic.json", "--scenario", "configs/scenarios/high.json", "--seed", "12345", "--duration-seconds", "3600", "--tick-seconds", "1", "--mode", "realtime", "--output-dir", "/app/runs", "--host", "0.0.0.0", "--port", "9090"]
