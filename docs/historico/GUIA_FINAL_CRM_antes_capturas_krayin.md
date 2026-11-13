# Guía final de instalación y uso — CRM-06.2

Cierre: 29/10/2026. CRM-01 a CRM-06 completados para Superstore Sales y demostración local. La aceptación técnica está en [CRM061_VALIDACION_INTEGRAL.md](CRM061_VALIDACION_INTEGRAL.md); las capturas en [INDICE_EVIDENCIAS_FINAL.md](INDICE_EVIDENCIAS_FINAL.md).

## Componentes y requisitos

El proyecto de investigación reside en `C:\Users\Alex11\Documents\Trabajo de Investigacion`: `ML/` prepara datos y ejecuta inferencia; `backend/` publica la API HTTPS. Krayin reside en `C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2`; el módulo operativo es `packages/Webkul/Churn/src`. Los notebooks de `integraciones/krayin/` son antecedentes y no deben ejecutarse como importadores actuales.

Entorno de aceptación: Krayin 2.2.6, Laravel 12.66.0, PHP 8.5.11, MariaDB 10.4.32 y Python 3.14.6. Versiones y hashes en [versiones.json](evidencias_crm061/versiones.json). Conservar las dependencias fijadas del proyecto. La instalación local ya contiene módulo, configuración, datos y cuatro migraciones aplicadas.

## Instalación o traslado

1. Preparar una instalación compatible de Krayin con su base configurada y un usuario activo. Respaldar base y archivos antes de trasladar el módulo.
2. Copiar `packages/Webkul/Churn/src` desde la instalación indicada a la misma ruta relativa del destino. No copiar `.env`, credenciales ni bases completas como parte del código.
3. Registrar en `autoload.psr-4` del `composer.json` raíz: `"Webkul\\Churn\\": "packages/Webkul/Churn/src"`. Registrar `Webkul\Churn\Providers\ChurnServiceProvider::class` en `bootstrap/providers.php` si aún no existe. Conservar las demás entradas.
4. Desde Krayin ejecutar `composer dump-autoload`, `php artisan migrate --path=packages/Webkul/Churn/src/Database/Migrations` y `php artisan optimize:clear`, usando el PHP de la instalación. No ejecutar `migrate:fresh` sobre la base existente.
5. Instalar el entorno Python y crear certificados/clave siguiendo [API04_SEGURIDAD.md](API04_SEGURIDAD.md). En este equipo ya existen `.venv-clean` y `.local/security`. El certificado de desarrollo dura 30 días; la guía incluye renovación. No sustituir TLS por verificación desactivada.
6. Configurar estas rutas en el `.env` de Krayin, adaptándolas al destino. Son rutas, no valores secretos:

```dotenv
CHURN_API_URL=https://127.0.0.1:8443
CHURN_CLIENT_KEY_FILE="C:/Users/Alex11/Documents/Trabajo de Investigacion/.local/security/api-key.txt"
CHURN_CLIENT_CA_FILE="C:/Users/Alex11/Documents/Trabajo de Investigacion/.local/security/cert.pem"
CHURN_EXPECTED_MODEL=churn180-v1
```

La cuenta que ejecuta PHP necesita lectura del archivo de credencial y del certificado público. La API requiere además lectura de su clave TLS privada. No mostrar contenidos en capturas. Tras cambiar configuración, ejecutar `php artisan optimize:clear`. El traslado a otra máquina requiere repetir la aceptación: el cierre actual certifica la instalación local, no una instalación limpia en un destino distinto.

## Iniciar la demostración

Iniciar MySQL desde XAMPP. En PowerShell 7.4 o superior, mantener abierta la API:

```powershell
Set-Location 'C:\Users\Alex11\Documents\Trabajo de Investigacion'
Remove-Item Env:CHURN_API_KEY -ErrorAction SilentlyContinue
$env:CHURN_API_KEY_FILE = (Resolve-Path '.local/security/api-key.txt').Path
$env:CHURN_TLS_CERT_FILE = (Resolve-Path '.local/security/cert.pem').Path
$env:CHURN_TLS_KEY_FILE = (Resolve-Path '.local/security/key.pem').Path
& .\backend\start.ps1 -Port 8443
```

Abrir Krayin mediante su servidor web configurado con raíz pública `public/`. Como alternativa local explícita, desde otra terminal:

```powershell
Set-Location 'C:\xampp\htdocs\KrayinCRM\laravel-crm-2.2'
& C:\xampp\php\php.exe artisan serve --host=127.0.0.1 --port=8765
```

Abrir `http://127.0.0.1:8765`, iniciar sesión con la cuenta existente y entrar a **Predicciones de abandono / Churn predictions**. El puerto debe estar libre. No se creó una cuenta de acceso permanente para QA. El `APP_URL` actual es `http://localhost`; en un traslado debe corresponder al servidor elegido. El prefijo de administración lo resuelve Krayin.

## Datos y corte histórico

El CSV contiene 9.800 líneas, 4.922 pedidos y 793 clientes. Fuente declarada: [Superstore Sales de Rohit Sahoo](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting). La procedencia y licencia declarada se documentan en la tesis; no se afirma igualdad binaria con una descarga remota.

La importación vigente valida el hash del CSV, sus campos y duplicados. Para una instalación nueva, extraer `train.csv.zip`, elegir el ID de un propietario activo y ejecutar desde Krayin (el ejemplo usa el propietario 1, que debe existir):

```powershell
& C:\xampp\php\php.exe artisan churn:import-superstore 'C:\Users\Alex11\Documents\Trabajo de Investigacion\.local\crm01-stage\train.csv' --owner=1 --dry-run
& C:\xampp\php\php.exe artisan churn:import-superstore 'C:\Users\Alex11\Documents\Trabajo de Investigacion\.local\crm01-stage\train.csv' --owner=1
```

No hace falta reimportar en el equipo actual. La repetición compatible reutiliza el mapeo externo; las ambigüedades cancelan la operación. Detalles en [CRM01_DATOS.md](CRM01_DATOS.md).

Usar el corte **2018-06-30**, no la fecha actual: el historial es `(corte − 365 días, corte]` y se exige compra en los últimos 180 días. El resultado estima ausencia de recompra durante los siguientes 180 días. Para ese corte hay 431 elegibles y 362 no elegibles. Las ausencias de resultado nunca representan 0 % de riesgo.

## Panel, permisos y seguimiento

El listado permite buscar cliente/ID, filtrar riesgo, estado y corte, y ordenar probabilidades numéricamente. El detalle muestra variables, fecha de corte, fecha del cálculo, versión, historial y sugerencia. Las orientaciones son reglas explícitas; la calidad insuficiente tiene prioridad sobre el riesgo.

| Permiso | Función |
|---|---|
| `churn` | Consultar listado, detalle e historial dentro del ámbito autorizado. |
| `churn` + `churn.update` | Solicitar actualización individual o lote. |
| `churn` + `churn.review` | Registrar revisión manual. |

Asignar permisos mediante la gestión de roles de Krayin. El ámbito individual limita a clientes propios; el grupal a los propietarios autorizados; un grupo vacío no concede acceso global. El lote web incluye todos los clientes autorizados, aunque no estén en la página o filtros visibles.

Para seguimiento, seleccionar pendiente/revisado/descartado, un responsable activo permitido y una nota de hasta 2.000 caracteres. Cada registro conserva autor y fecha UTC; no borra entradas anteriores ni cambia probabilidades. Si otra persona guardó antes, recargar y revisar el conflicto. No se envían correos ni campañas al guardar.

## Cola y operación

El botón guarda una solicitud; necesita ejecutar el procesador en otra terminal desde Krayin:

```powershell
& C:\xampp\php\php.exe artisan churn:work --limit=100
```

El comando termina al agotar pendientes o alcanzar el límite; repetir si quedan solicitudes. Admite 1–1000. Usar **Consultar progreso** para recargar el panel. La cola es propia del módulo: no requiere `queue:work` ni cambiar `QUEUE_CONNECTION`.

Alternativas de consola para un cliente o todos los clientes:

```powershell
& C:\xampp\php\php.exe artisan churn:queue --customer=AA-10315 --as-of=2018-06-30
& C:\xampp\php\php.exe artisan churn:work --limit=1
# Lote completo; esta acción sí persiste resultados en la demostración.
& C:\xampp\php\php.exe artisan churn:queue --all --as-of=2018-06-30
& C:\xampp\php\php.exe artisan churn:work --limit=1000
```

La consola administrativa no aplica el ámbito de un usuario web. No ejecutar simultáneamente el diagnóstico `churn:predict-customer --save` sobre los mismos clientes: no participa en la cola. Los duplicados pendientes se reutilizan; MariaDB impide dos procesadores concurrentes. Un resultado idéntico conserva su fecha original; un contenido distinto para cliente/corte/versión produce conflicto sin sobrescritura.

El progreso considera la última solicitud por cliente/corte/versión: completados + errores + no elegibles. **100 % terminado no significa 100 % exitoso.** Tras una interrupción, el siguiente procesador cierra trabajos abandonados como `worker_interrupted`; revisar el servicio y solicitar otra actualización. Los pendientes restantes continúan.

| Problema | Acción |
|---|---|
| Base inaccesible | Iniciar MySQL y comprobar configuración de Krayin. |
| Pendiente sin avance | Iniciar API y ejecutar `churn:work`; recargar progreso. |
| 401 | Revisar que PHP lea la credencial correspondiente a la API. No imprimirla. |
| 422 | Revisar contrato/datos; no repetir sin corregir el origen. |
| 503 | Servicio saturado; el cliente realiza hasta tres intentos acotados. Revisar carga antes de reenviar. |
| Error de TLS/conexión | Verificar API, puerto, certificado vigente, nombre y archivo CA; no omitir validación TLS. |
| 419 en formulario | Renovar sesión/página y reenviar con token CSRF válido. |
| Sin resultado | Distinguir pendiente, fallo y no elegibilidad; conservar el resultado válido anterior si existe. |

El consumidor limita el presupuesto a 50 segundos y tres intentos; 401/422 no se reintentan. Detalle operativo: [CRM044_ACTUALIZACIONES.md](CRM044_ACTUALIZACIONES.md). La operación de este módulo es manual; no se instaló un worker permanente. El despliegue administrado de la API se explica por separado en [API07_DESPLIEGUE.md](API07_DESPLIEGUE.md).

## Aceptación y estado entregado

CRM-06.1 registró 161 pruebas PHP (477 aserciones) y 98 Python aprobadas. El lote real HTTPS produjo 431 resultados y 362 no elegibles, con diferencia máxima de probabilidad 4,9960 × 10⁻¹⁵ frente al test. Sus escrituras se revirtieron: el estado final documentado conserva **una predicción original y 792 clientes sin resultado**, sin cuentas ni revisiones temporales de QA. Las 431 predicciones de la prueba no quedaron cargadas. Para conservar un lote nuevo, ejecutar los comandos operativos anteriores.

La reproducción de pruebas está en [CRM061_VALIDACION_INTEGRAL.md](CRM061_VALIDACION_INTEGRAL.md). Requiere base disponible y ausencia de otros operadores escribiendo. Esta tarea documental no repitió entrenamiento ni modificó el modelo. Los avisos de deprecación permanecen documentados; la cobertura 95,14 % corresponde al ensayo Python previo ML-06, no a una medición nueva.

La tesis actualizada contiene 42 páginas revisadas. Su capítulo 4 documenta integración y pantallas; el capítulo 6 conserva el resultado científico: ROC-AUC 0,4571 y AP 0,2119 no demuestran utilidad predictiva suficiente. La implementación funciona dentro del alcance probado, pero no demuestra mejora de fidelización ni rentabilidad. La validación comercial y el despliegue externo quedan fuera del alcance acordado.

## Cierre de la mejora experimental (MEJ-08)

La ronda está cerrada: MEJ-01 a MEJ-06 y MEJ-08 completadas; MEJ-07 no aplica porque el candidato incumplió dos criterios de Brier. Se conserva v1 y la integración existente. La tesis reorganizada presenta implementación en páginas 7–18, resultados en 19–27, conclusiones en 29 y recomendaciones en 30. El índice de evidencias contiene la paginación vigente. Archivos concretos para capturas y límites: [acta de cierre](MEJ08_CIERRE_DOCUMENTAL.md).



Reestructura de capítulos 3 y 4 (30/10/2026): metodología en páginas 7–18 y resultados en 19–27, con las cuatro imágenes originales indicadas. Ubicaciones y archivos para capturas: [índice vigente](INDICE_EVIDENCIAS_FINAL.md).
