# API-06 — Lotes, carga y recuperación

Implementada y verificada el 28 de octubre de 2026. API 2.1.0, modelo experimental `churn180-v1`. No requiere Krayin para comprobar el servicio; la política del consumidor descrita aquí deberá implementarse en CRM-02.

## Decisión y límites

Se mantiene inferencia síncrona por lote, sin cola persistente. Cada resultado conserva cliente, corte y versión; el orden coincide con el de entrada. El lote se valida completo antes de inferir. Un lote inválido se rechaza completo, sin escrituras parciales.

| Límite | Valor y comportamiento |
|---|---|
| Clientes por lote | 1–500; exceso o claves cliente/corte repetidas: 422 |
| Líneas de compra de un cliente | Hasta 5.000 |
| Cuerpo | Hasta 2.000.000 bytes, incluso fragmentado; exceso: 413 |
| Predicciones en curso | Cuatro solicitudes `/v1/` por proceso; incluye recepción, validación y procesamiento |
| Saturación de predicción | Rechazo inmediato 503, código `capacity_exceeded`, `Retry-After: 1`; no se acumula una cola de inferencia |
| Recepción del cuerpo | Cinco segundos totales desde que se inicia su lectura; vencimiento: 408 `body_timeout` |
| Transporte Uvicorn | Límite de concurrencia 64 y backlog 64; conexiones inactivas persistentes: cinco segundos |
| Parada ordenada | Hasta 15 segundos para solicitudes en curso |

Los cuatro cupos son globales para el proceso, no cuatro por consumidor. El lanzador utiliza un proceso; multiplicar procesos multiplica este límite y requiere otra prueba. Salud y documentación no ocupan cupos de predicción, aunque siguen sujetas a seguridad y límites generales del transporte.

La autenticación se comprueba antes de aceptar el cuerpo y ocupar un cupo. Los errores normales liberan el cupo mediante `finally`. El timeout de recepción no se debe confundir con un timeout de cálculo: no se ha implementado terminación forzada de un hilo de inferencia. El trabajo síncrono termina normalmente aunque el cliente deje de esperar; para un límite duro de cómputo se necesitaría aislamiento por procesos/trabajos y otro diseño. El servicio no promete una duración máxima absoluta de inferencia.

Los límites generales de Uvicorn pueden producir su propio 503 sin el JSON, `Retry-After` ni trazabilidad de la aplicación. El consumidor debe manejar ese caso también. Estos controles no sustituyen límites de red/TLS de un servidor público.

## Política del consumidor PHP/Laravel

1. Empezar con dos solicitudes simultáneas por consumidor y no superar cuatro en total para esta instancia. Dividir clientes en lotes de hasta 500 y verificar también el tamaño en bytes. Coordinar cupos si existen varios consumidores.
2. Usar timeout de conexión de tres segundos y presupuesto total de 15 segundos por intento. Máximo tres intentos y 50 segundos para toda la operación, incluyendo esperas. Son parámetros iniciales para este perfil local, sujetos a validación en el servidor definitivo.
3. Reintentar fallos transitorios de conexión, 408, 500, 502, 503 y 504. Esperar uno y dos segundos respectivamente, más variación aleatoria de 0–250 ms. Si existe `Retry-After`, respetarlo y no reintentar antes; si excede el presupuesto restante, terminar y registrar la operación pendiente/fallida. Una nueva petición 408 debe enviar el cuerpo completo.
4. No reintentar certificados inválidos, 400/401/403/404/413/422/426 sin corregir la causa. No registrar credenciales ni cuerpos personales. Si se recibe un error HTML o texto de un intermediario, conservar estado e identificador disponible, sin asumir que siempre es JSON.
5. Un timeout deja desconocido si el servidor terminó el cálculo. La inferencia no escribe datos, por lo que puede repetirse con el mismo cliente/corte/versión. La escritura posterior en Krayin debe ser idempotente con esa clave; una repetición no debe disparar otra campaña.
6. Al agotar intentos, conservar el fallo para revisión o una nueva ejecución programada. No convertir un error en riesgo bajo ni repetir indefinidamente.

Esta es la política acordada para construir CRM-02; no se ha creado todavía el cliente PHP ni una cola en Krayin. El estado experimental y `automatic_action_allowed=false` siguen vigentes.

## Ensayo reproducible

```powershell
.\.venv-clean\Scripts\python.exe -m pytest -q --cov=ML --cov=backend --cov=deploy --cov-report=term-missing
.\.venv-clean\Scripts\python.exe -m scripts.verify_api06
```

El segundo comando usa un servidor temporal y certificado local de API-04, verifica certificado y nombre, mide HTTPS real y cierra el proceso al terminar. Requiere Windows para las mediciones de recursos y un entorno que permita sockets locales.

Perfil: Windows 11, Python 3.14.6, 16 CPU lógicas, cliente y servidor en el mismo equipo. Se usan tres calentamientos y 80 solicitudes por escenario, lotes de 1/500 clientes y concurrencia 1/4/16: **480 solicitudes medidas**. Cada solicitud abre una conexión TLS nueva. Las características son sintéticas repetidas con IDs distintos; el script verifica probabilidad, cantidad y correspondencia de IDs. No aplica reintentos durante la medición.

Criterios definidos en el ensayo: ausencia de 503 con concurrencia 1 y 4, ausencia de errores inesperados, p95 exitoso menor de 5.000 ms y una predicción exitosa después de cada escenario. El umbral de 5 segundos es un criterio de aceptación local, no un SLA comercial. En sobrecarga se admiten rechazos explícitos, que se cuentan aparte de los éxitos.

| Clientes por solicitud | Concurrencia | HTTP 200 / 503 | p95 de éxitos, ms |
|---|---|---|---|
| 1 | 1 | 80 / 0 | 32,62 |
| 1 | 4 | 80 / 0 | 60,58 |
| 1 | 16 | 16 / 64 | 114,22 |
| 500 | 1 | 80 / 0 | 62,51 |
| 500 | 4 | 80 / 0 | 158,48 |

La tabla resume parte del ensayo; los seis escenarios completos, p50/p95/p99, rendimiento, CPU y memoria están en `docs/evidencias_api/09_carga_https.json`. Las latencias de éxitos no deben interpretarse sin sus tasas de rechazo. El escenario de 16 concurrentes es una prueba de sobrecarga, no una recomendación de operación.

Se verificó además por HTTPS que cuatro cuerpos incompletos ocupan los cuatro cupos, una quinta predicción recibe 503, las cuatro solicitudes vencen con 408 y una nueva predicción vuelve a devolver 200. Las pruebas automatizadas incluyen salud y autenticación durante saturación y recuperación tras validación inválida. **96 pruebas aprobadas; cobertura Python 95,38 %.**

La medición de memoria suma el launcher Python y sus hijos directos: informa instantáneas y suma de máximos por proceso desde el arranque, que no equivale a un pico simultáneo. El tiempo de CPU incluye el intervalo de consulta posterior de recursos. Son ensayos breves: no prueban estabilidad durante horas, capacidad en otra máquina, rendimiento con todos los historiales posibles ni tráfico real de Krayin.

## Entrega y capturas

- Código: `backend/main.py` y `backend/serve.py`.
- Casos de saturación/timeout: `tests/test_api_capacity.py`.
- Ejecución de carga: `scripts/verify_api06.py`.
- Evidencia para captura de resultados: `docs/evidencias_api/09_carga_https.json`.
- Evidencia para captura de regresión: final de `docs/evidencias_api/API06_pruebas.txt`.
- Entrega nueva: `.local/releases/api-2.1.0-api06/`, con su propio entorno y `release.json`. Las entregas anteriores de API-07 se conservan y no reciben estos cambios automáticamente.

Para activar la entrega se utiliza `deploy/Service.ps1` según `API07_DESPLIEGUE.md`, con un perfil y tarea propios. No se instala una tarea permanente ni se publica un servidor como parte de este ensayo. El servidor definitivo debe repetir la carga con su hardware, volumen y concurrencia esperados antes de fijar su capacidad comercial.

## Conclusión

API-06 queda cerrada para el perfil local evaluado: lotes acotados, admisión limitada, rechazo explícito de saturación, timeout de recepción, recuperación comprobada y política del consumidor documentada. La siguiente fase integra esa política en PHP y valida el perfil del destino. Este resultado es técnico: no modifica la validez predictiva del modelo ni demuestra mejora de fidelización.
