# Instrucciones y Límites Arquitectónicos para Agentes

Al trabajar en `green-ai-simulator`, los agentes deben respetar estrictamente los siguientes límites:

1. **Aislamiento**: El dominio no debe depender de librerías externas (HTTP, Supabase, Prometheus, Kubernetes). Toda lógica de negocio debe usar tipos nativos y de la librería estándar de Python.
2. **Repositorio**: Este proyecto debe tratarse como un repositorio independiente. NO inicializar un repositorio padre ni mezclar código con otros proyectos como `Monitoring`.
3. **Persistencia**: La persistencia es estrictamente a través de archivos locales (JSON/JSONL). No se debe agregar configuraciones para bases de datos relacionales u orquestadores en el simulador lógico inicial.
4. **Dependencias**: Solo se añade dependencias a `pyproject.toml` usando `uv`. Evitar el uso de entornos virtuales ocultos o instalaciones globales; documentar los pasos explícitamente en el `README.md`. No ignorar los archivos de caché o *lockfiles* (a menos que se especifique en `.gitignore`).
5. **No inventar datos**: Todo dato modelado o capacidad sintética debe declararse explícitamente. No utilizar fórmulas improvisadas para calcular potencia o energía a menos que se derive lógicamente de un modelo especificado.
