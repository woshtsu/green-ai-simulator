# Plan de implementación de green-ai-simulator

Fecha: 2026-09-21. Estado: plan para traspaso; implementación pendiente.

Este documento permite continuar en otro agente sin reconstruir la conversación. La carpeta del simulador está vacía al preparar el plan. Crear este documento no significa que exista un simulador funcional.

## 1. Instrucción vigente y límites

El usuario solicitó detener las pruebas adicionales y preparar un plan paso a paso. En esta sesión no implementar código ni ejecutar pruebas. El siguiente agente deberá recibir la instrucción de implementar este plan antes de comenzar la implementación. Las verificaciones descritas aquí son trabajo futuro, no resultados obtenidos.

Trabajar exclusivamente en `green-ai-simulator`. Cada servicio será un repositorio Git independiente: no inicializar un repositorio padre, no crear Gateway ni Deployment, no realizar commits o publicaciones por iniciativa propia. Preservar los cambios existentes de Monitoring. No reejecutar sus pruebas ni su smoke pendiente por iniciativa propia.

El primer incremento será un simulador lógico Python, ejecutable mediante CLI, con persistencia local y un adaptador Prometheus. No generar carga real, actuar sobre Kubernetes, acceder a Supabase ni definir contratos de servicios de otros integrantes en este incremento.

## 2. Lectura inicial obligatoria

Desde la carpeta del simulador, leer en este orden:

1. Instrucciones `AGENTS.md` que sean aplicables a su ruta. El de Monitoring no se hereda por ser un directorio hermano.
2. `../project-docs/2. Conocimiento de Ingenieria.md` y `../project-docs/4. Gestión de Proyecto.md`. Evitar volcar imágenes base64 al contexto.
3. `../green-ai-monitoring/docs/integracion-simulator.md`: referencia principal de integración ya acordada.
4. `../green-ai-monitoring/docs/contrato-monitoring-v0.1.md` y `../green-ai-monitoring/src/main/resources/static/openapi/monitoring-v0.1.json`.
5. `../green-ai-monitoring/docs/validacion-incremento-1.md`: evidencia y limitaciones, sin ejecutar sus comandos.
6. Este plan completo. Si los contratos actuales difieren de lo aquí resumido, registrar la diferencia antes de conectar servicios; no cambiar silenciosamente Monitoring.

## 3. Punto de partida confirmado

Monitoring usa Java 21 y Spring Boot 4.1.1. Su compilación y ejecución Docker deben seguir usando Java 21 aunque el host tenga Java 24. Esto no impone Java al simulador, que será Python.

Monitoring consulta Prometheus mediante HTTP; no recibe inserciones del simulador. Sus rutas internas son `/api/v1/metrics/catalog`, `/api/v1/metrics/current` y `/api/v1/metrics/history`. Su `/actuator/prometheus` expone métricas operativas del propio servicio, no datos del datacenter.

Grupo A disponible: utilización CPU, memoria usada, recepción/transmisión de red y almacenamiento usado. El Grupo B —solicitudes, throughput de negocio, concurrencia, latencia, errores y estado de workloads— sigue pendiente del PMV1 integrado. No declarar finalizado PMV1 por completar este plan.

Evidencia previa: 112 pruebas de Monitoring pasaron en Java 21 dentro de un contenedor. El smoke real obtuvo resultados de las cinco métricas actuales e históricas. Su ejecución completa no terminó satisfactoriamente: se ajustó la espera del scrape de Monitoring, pero ese ajuste no fue revalidado; la fase de caída del upstream tampoco se alcanzó. No presentar esos pendientes como aprobados ni repetirlos ahora.

Flujo aprobado:

```text
Motor lógico → exporter Simulator → Prometheus → Monitoring → Data Processing / Gateway
Frontend → Gateway → servicios internos
```

El simulador no escribe en Monitoring ni en los logs reales de Supabase. Los servicios internos pueden comunicarse por HTTP REST y DNS interno; no necesitan atravesar Gateway. Frontend sí utiliza Gateway.

## 4. Resultado esperado del primer incremento

Una persona deberá poder validar un inventario sintético, ejecutar escenarios baja/media/alta/pico con semilla y duración explícitas, detener una ejecución, inspeccionar sus archivos y exponer su estado actual para Prometheus. Una misma configuración normalizada, versión del motor y semilla debe producir los mismos resultados lógicos.

Se proponen dos modos separados:

- `offline`: avanza el reloj lógico sin esperas reales y escribe resultados; no publica contadores acelerados en Prometheus.
- `realtime`: avanza con ritmo objetivo 1x y expone `/metrics`. Usa tiempo monotónico para planificación y registra desviaciones de ritmo.

Los valores generados son `simulated`, aun si el inventario futuro procede de hardware real. No producir potencia, energía o temperatura con fórmulas improvisadas. Los servidores modelados no equivalen a nodos físicos disponibles.

## 5. Decisiones técnicas propuestas

Estas decisiones concretan el plan y pueden ajustarse por una razón documentada, sin ampliar el alcance:

- Núcleo con biblioteca estándar, tipos explícitos y objetos de dominio; sin importaciones HTTP, Prometheus, Supabase o Kubernetes.
- Configuración JSON versionada para reducir dependencias iniciales; CLI con `argparse` y exporter con `prometheus_client`, utilizando su servidor HTTP si cubre las necesidades.
- Elegir una versión estable y soportada de Python al implementar; verificarla en documentación oficial y fijarla en metadatos, herramientas y contenedor. No asumir que una etiqueta `latest` es reproducible.
- `pyproject.toml`, dependencias fijadas mediante un mecanismo de lock reproducible y documentación del comando de instalación. Evitar instalar paquetes globalmente.
- Un proceso por ejecución. Una única autoridad modifica el estado del motor; el exporter solo lee snapshots inmutables. Sin API REST de administración en el primer incremento.
- Persistencia mediante archivos JSON/JSONL; no agregar base de datos, RabbitMQ, autenticación empresarial ni plataforma de orquestación.

Estructura orientativa:

```text
green-ai-simulator/
  pyproject.toml
  <archivo de lock>
  README.md
  AGENTS.md
  .gitignore
  src/green_ai_simulator/
    domain/                 # inventario, escenarios, estados, invariantes
    application/            # ejecutar, validar y detener
      ports/                # reloj, repositorio de runs, lector de inventario
    adapters/
      cli/
      configuration/
      persistence/
      prometheus/
      clock/
    bootstrap.py
  configs/inventory.synthetic.json
  configs/scenarios/        # baja, media, alta, pico
  docs/                    # modelos, contratos, integración y evidencia
  tests/                   # se incorporan durante implementación autorizada
  scripts/                 # herramientas portables del nuevo servicio
```

## 6. Secuencia de implementación

### Paso 1 — Inventariar y preparar el proyecto

- Revisar archivos presentes y estado Git antes de editar; el usuario puede haber añadido contenido después de este plan.
- Registrar versiones elegidas y comandos de instalación/ejecución. Crear el esqueleto mínimo y una CLI con ayuda, sin simular datos todavía.
- Documentar límites arquitectónicos en `AGENTS.md`. Ignorar entornos virtuales, cachés, secretos y salidas locales de runs.
- No inicializar Git automáticamente si no existe; dejar instrucciones para crear el repositorio independiente.

Entrega: paquete instalable, entrada CLI y README con alcance. Criterio: ninguna dependencia externa importada desde el dominio.

### Paso 2 — Definir y validar inventario y configuración

- Definir `schema_version`, identificadores estables, descripción y procedencia del inventario.
- Cada equipo tendrá CPU lógicas enteras positivas, memoria en bytes, interfaces con identificador/capacidad en bytes por segundo y filesystems con dispositivo/montaje/tipo/capacidad en bytes.
- Separar valor, unidad y procedencia de cada parámetro: fixture sintético, dato observado o supuesto de modelado. Toda capacidad ficticia debe decirlo explícitamente.
- Validar IDs únicos, números finitos, rangos, capacidades positivas, interfaces/filesystems duplicados, rutas de montaje y referencias de escenarios. Rechazar claves desconocidas para detectar errores de escritura.
- Validar nombres de nodo y cluster con `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`; no usar IP como identidad obligatoria.
- Declarar límites de nodos, CPU totales, interfaces, filesystems, duración, ticks y tamaño de salida. Validarlos antes de reservar memoria o abrir el exporter.
- Crear un fixture pequeño, claramente ficticio, con dos equipos diferentes. No atribuirlo a la universidad ni a un datacenter real.

Entrega: esquema documentado, fixture y comando de validación con errores útiles. No aceptar valores faltantes mediante capacidades inventadas.

### Paso 3 — Modelar escenarios y reloj lógico

- Los cuatro escenarios son configuraciones del mismo motor; no cuatro implementaciones separadas.
- Representar intensidad CPU y fracción de memoria como valores acotados, tasas de red en bytes/s y evolución de almacenamiento en bytes por tick o bytes/s, con unidades explícitas.
- Documentar valores iniciales, rangos y perturbaciones sintéticas elegidas. Baja/media/alta deben tener una relación clara de intensidad; pico debe declarar inicio, duración, ascenso y recuperación.
- Los límites se aplican por recurso y equipo: no multiplicar demanda total por cada CPU accidentalmente.
- Usar una semilla explícita. Para flujos independientes por nodo/recurso, derivar semillas con un hash estable y versionado, nunca con `hash()` de Python ni con el orden de un diccionario.
- Definir `tick_seconds` positivo y una duración múltiplo del tick para el primer incremento; rechazar configuraciones ambiguas.
- Persistir estado inicial en tiempo lógico 0 y estados después de cada tick hasta duración inclusive. Así hay `duration/tick + 1` snapshots; computar este coste al validar límites.
- Usar enteros o aritmética de precisión definida para acumulaciones sensibles; documentar redondeo y versión del algoritmo. No prometer igualdad entre versiones diferentes del motor.

Entrega: escenario normalizado y transición determinista `estado + intervalo → estado siguiente`, sin sleeps ni lectura del reloj real en el dominio.

### Paso 4 — Implementar invariantes del motor

- Para cada CPU lógica y tick de duración `dt`, incrementar idle por `dt * (1 - utilization)` y user por `dt * utilization`. Su suma aumenta exactamente `dt` dentro de la precisión definida.
- Mantener contadores de CPU/red no negativos y monótonos dentro del run. La red aumenta por tasa por duración, con capacidad máxima por interfaz.
- Mantener `0 <= memoria disponible <= memoria total` y `0 <= espacio libre <= capacidad`. No sumar interfaces ni filesystems para ocultar su identidad.
- Modelar ocupación de almacenamiento explícitamente; una liberación necesita un evento/configuración de liberación, no ruido que borre datos accidentalmente.
- Si se modela fallo de filesystem, propagarlo como tal; no convertir la ausencia de información en cero.
- Garantizar que una consulta del snapshot no avanza el motor ni consume números aleatorios.

Entrega: núcleo utilizable offline sin servidor HTTP ni Prometheus.

### Paso 5 — Registrar ejecuciones y permitir parada

- Estados propuestos: `CREATED`, `RUNNING`, `STOPPING`, `COMPLETED`, `STOPPED`, `FAILED`. Definir transiciones válidas y motivos terminales; `COMPLETED` solo al alcanzar duración.
- Generar un UUID por ejecución, sin incluirlo en los valores cuya igualdad determinista se compara. Usar `cluster=sim-run-<uuid>` para su identidad externa.
- Crear una carpeta nueva por run, sin sobrescribir salidas previas. Validar rutas y no construirlas a partir de fragmentos arbitrarios del inventario.
- Guardar `manifest.json`, configuración normalizada, snapshot del inventario y `samples.jsonl`. Incluir semilla, hash SHA-256 de configuración canónica, versión del esquema/motor, dependencias, modo, límites, tiempos lógicos y fechas UTC reales de inicio/fin.
- Si hay Git, registrar revisión y si existen cambios locales; una revisión sola no describe código modificado. No persistir credenciales ni volcar variables de entorno completas.
- Escribir muestras de forma incremental con memoria acotada. Limitar bytes de salida; si se alcanza el límite, detener con motivo explícito, sin descartar silenciosamente muestras.
- Actualizar el manifiesto mediante reemplazo atómico. Manejar errores de disco y limpiar únicamente recursos propios. Una interrupción abrupta puede dejar un run incompleto: documentarlo; no implementar recuperación exacta o resume en este incremento.
- Atender Ctrl+C/SIGINT y SIGTERM donde estén disponibles, finalizar el tick según una política documentada, persistir estado terminal y cerrar servidor/archivos. Limitar el tiempo de cierre.

Entrega: runs inspeccionables y parada segura. Separar metadatos variables —UUID/fecha real— de resultados lógicos reproducibles.

### Paso 6 — Completar la CLI offline

Interfaz propuesta, a concretar en la documentación:

```text
green-ai-simulator validate --inventory <archivo> --scenario <archivo>
green-ai-simulator run --inventory <archivo> --scenario <archivo> --seed 42 --duration-seconds 120 --tick-seconds 1 --mode offline --output-dir <directorio>
```

- Mostrar run ID, ruta de salida y resumen terminal, sin imprimir cada muestra por defecto.
- Usar códigos de salida distintos para configuración inválida, fallo de ejecución y terminación normal; documentar el tratamiento de parada solicitada.
- Evitar arrancar HTTP en modo offline. No generar carga de CPU/memoria artificial para representar los valores del modelo.

Entrega: los cuatro escenarios pueden ejecutarse y dejar registros completos usando únicamente fixtures.

### Paso 7 — Adaptar a Prometheus en modo realtime

Exponer un registro propio por proceso/run; evitar el registro global que pueda mezclar métricas entre pruebas o ejecuciones. Un collector sobre snapshots permite representar los nombres y tipos exactos sin alterar el motor durante el scrape.

Todas las familias del modelo llevan `cluster`, `node` y `origin="simulated"`. Añadir únicamente las etiquetas específicas siguientes:

| Familia | Tipo | Etiquetas adicionales / condición |
| --- | --- | --- |
| `node_cpu_seconds_total` | counter | `cpu`, `mode`; incluir idle y user consistentes |
| `node_memory_MemTotal_bytes` | gauge | total por nodo |
| `node_memory_MemAvailable_bytes` | gauge | disponible por nodo |
| `node_network_receive_bytes_total` | counter | `device` |
| `node_network_transmit_bytes_total` | counter | `device` |
| `node_filesystem_size_bytes` | gauge | `device`, `mountpoint`, `fstype` |
| `node_filesystem_free_bytes` | gauge | mismas etiquetas del tamaño |
| `node_filesystem_device_error` | gauge | mismas etiquetas; 0 sano, 1 fallo modelado |

- No establecer `instance` como identidad del hardware: Prometheus lo asigna al target. El consumidor Monitoring deberá usar `monitoring.prometheus.instance-label=node` en un entorno de integración acordado.
- La misma instancia de Monitoring requiere un esquema coherente para todos sus targets. Si hay exporters observados, también necesitan `node`; no modificar sus configuraciones automáticamente.
- Usar FS compatibles: ext2/ext3/ext4/xfs/btrfs/zfs. Monitoring excluye `/proc`, `/sys`, `/dev`, `/run` y descendientes. Crear fixtures cuyo almacenamiento principal sea consumible.
- No publicar timestamps históricos en `/metrics`. Los timestamps lógicos quedan en JSONL; Prometheus asigna tiempo de scrape.
- El modo realtime usa planificación monotónica 1x. Registrar retraso; ante retraso sostenido, detener con motivo explícito o marcar la ejecución degradada según política documentada. No acelerar silenciosamente muchos ticks para fingir ritmo 1x.
- Mantener snapshots atómicos entre hilos. Acotar cardinalidad desde la validación del inventario.
- Escuchar en loopback por defecto; dirección y puerto configurables. En contenedor, habilitar explícitamente `0.0.0.0`. No añadir endpoints de acciones remotas.
- Al terminar, cerrar el exporter y documentar staleness de Prometheus; no dejar un servidor que aparente una simulación activa con contadores congelados.
- Si se añaden métricas operativas del proceso, usar un namespace propio y documentarlas separadamente de las métricas del modelo.

Entrega: scrape del estado actual compatible con Grupo A sin cambios de contrato en Monitoring.

### Paso 8 — Documentar integración y distribución portable

- Preparar ejemplos de configuración dentro del repositorio Simulator; no crear `green-ai-deployment` ni editar el entorno real.
- Indicar scrape de 15 s o menor, arranque escalonado y calentamiento de la ventana `rate(...[1m])`. Un resultado inicial `no_data` no representa utilización cero.
- Mostrar filtros de Monitoring por cluster de run y nodo, consultando su OpenAPI para los nombres exactos de parámetros. Nunca ofrecer PromQL arbitrario desde la API pública.
- Documentar que la utilización obtenida con rate es una estimación temporal a partir de scrapes; no exigir igualdad exacta con cada tick ni ignorar jitter.
- Preparar Dockerfile del simulador con Python fijado, usuario sin privilegios, señales de terminación correctas, directorio de salida montable y sin secretos. No crear/modificar el Dockerfile de Monitoring como parte de esta tarea.
- Usar rutas portables y scripts que no dependan del Python global de Windows. Mantener acotados recursos y duración en ejemplos Docker.

Entrega: README ejecutable paso a paso, ejemplo offline/realtime y guía de contenedor. No ejecutar un nuevo smoke integrado de Monitoring sin autorización posterior.

## 7. Verificaciones futuras del simulador

No se ejecutan al redactar este plan. Al autorizar su implementación, acordar el alcance de estas verificaciones si sigue vigente la restricción de no hacer más pruebas; nunca interpretarlas como permiso para repetir las de Monitoring.

Prioridad de verificación:

1. Determinismo: misma semilla/configuración produce muestras lógicas idénticas; lectura del exporter no cambia la secuencia. No comparar UUID ni hora real.
2. Invariantes: conservación del tiempo por CPU, límites de memoria/FS, monotonía de contadores y capacidades de red en los cuatro escenarios.
3. Validación: duplicados, NaN/infinito, rangos, unidades desconocidas, pico fuera de duración y configuraciones que exceden límites fallan antes de arrancar.
4. Persistencia y parada: salida incremental, límites de disco, señales, manifiesto terminal y conservación de runs anteriores.
5. Exporter: tipos, nombres, labels, aislamiento entre nodos/runs y snapshots coherentes. Usar reloj controlado para evitar pruebas lentas basadas en sleeps.
6. Portabilidad: ejecutar las verificaciones finales del nuevo servicio dentro de su contenedor; registrar comando, versión/digest, resultado y limitaciones. No sustituirlas por resultados del host.

La integración completa Simulator → Prometheus → Monitoring es un hito posterior expresamente autorizado. Debe usar recursos aislados, sin borrar clústeres, volúmenes, configuraciones o históricos existentes. La limpieza solo puede actuar sobre recursos creados por esa ejecución.

## 8. Supabase, carga real y ampliaciones posteriores

No bloquear el motor por falta de infraestructura. Implementar ahora puertos y fixtures; agregar adaptadores cuando existan datos y autorización concreta.

- Supabase: el esquema de `usuario`, `hardware` y `logs` está confirmado por la extracción del usuario; consultar docs/modelo-bd.md para tipos, claves, índices, defaults y RLS. Las credenciales previamente expuestas deben considerarse comprometidas: no usarlas ni probarlas.
- Un adaptador futuro de inventario podrá leer exclusivamente campos necesarios de `hardware`, con credenciales rotadas y mínimos permisos. No acceder a `usuario`, no escribir `logs` y no otorgar acceso general a tablas por compartir instancia.
- Confirmar si `ram_gb` representa GB decimales o GiB antes de convertir. `max_watts` no es una curva de consumo calibrada; watts representa potencia, no energía. Conservar datos no utilizados como metadatos identificados, sin derivar resultados falsos.
- El inventario real debe fijarse en un snapshot por run. Procedencia observada del inventario y procedencia simulada de resultados son campos diferentes.
- Carga real será otro adaptador/modo, con destino explícito, duración, concurrencia, límites y parada. Sus mediciones no tienen reproducibilidad exacta por semilla.
- Acciones Kubernetes requieren namespace dedicado, RBAC mínimo y un acuerdo posterior. No asumir que cada equipo inventariado existe como nodo del clúster.
- Grupo B y modelos energéticos requieren especificaciones e instrumentación propias. No reutilizar métricas HTTP del exporter como throughput del negocio ni asignar estimaciones a `observed`.

## 9. Criterios de cierre y traspaso

El primer incremento puede declararse implementado cuando existen el motor independiente, inventario validado, cuatro escenarios, CLI offline/realtime, límites/parada, archivos por run y exporter compatible documentado. El informe debe distinguir código implementado, verificaciones ejecutadas, verificaciones omitidas por instrucción del usuario y pendientes de integración. Si no se ejecutaron verificaciones, no declarar validación o portabilidad comprobada.

Entregar rutas y comandos concretos, ejemplo de un run cuando esté autorizado ejecutarlo, esquema/versiones fijados, decisiones de modelado y riesgos conocidos. No declarar terminado el PMV1 completo. No cambiar Monitoring, Gateway, Deployment ni contratos de compañeros para resolver cómodamente una diferencia del simulador.

### Mensaje sugerido para iniciar al siguiente agente

> Implementa el primer incremento de green-ai-simulator siguiendo este plan y los documentos de referencia. Empieza revisando el estado actual de la carpeta y las instrucciones aplicables. Trabaja solo en este repositorio, conserva el núcleo Python independiente y usa fixtures explícitamente sintéticos. Respeta la separación entre reloj lógico offline y exportación realtime 1x, persiste cada run y publica origin=simulated con identidad propia por ejecución. No accedas a Supabase ni generes carga real o acciones Kubernetes. No repitas pruebas ni el smoke de Monitoring. La instrucción previa de detener pruebas debe respetarse: si no se autoriza verificarlas en esta nueva implementación, deja las verificaciones del simulador preparadas y reportadas como pendientes. Avanza por los pasos del plan, registra decisiones y entrega un estado honesto de lo implementado y lo validado.

## Referencia de BD actualizada — 2026-09-22

Consultar el [modelo de BD](docs/modelo-bd.md): diagrama y campos completos de `usuario`, `hardware` y `logs`, con mapeos y limitaciones de integración. El diagrama aporta tipos y relaciones; la extracción SQL del usuario confirma tipos y nulabilidad. La extracción completa confirma defaults, longitudes/precisión, restricciones, índices y RLS; verificación documental del esquema cerrada. Monitoring conserva Prometheus como fuente y Simulator conserva JSON/JSONL como persistencia; el acceso a inventario SQL es futuro. Esta referencia actualiza las suposiciones del esquema, sin ampliar el catálogo de métricas ni implementar acceso a BD.
