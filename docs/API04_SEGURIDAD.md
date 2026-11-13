# API-04 Protección de la comunicación

Estado: implementación de seguridad completada y verificada localmente por HTTPS, independiente de Krayin. Se aprobaron 64 pruebas, se negoció TLS 1.3 y se comprobó también TLS 1.2. La evidencia se guarda en `docs/evidencias_api/07_seguridad_https.json`; las pruebas de regresión, en `docs/evidencias_api/API04_pruebas.txt`. La activación en el servidor definitivo requiere su nombre, certificado e IP de origen autorizada.

## Protección implementada

- HTTPS directo mediante el lanzador `python -m backend.serve`, con TLS 1.2 como mínimo y soporte de TLS 1.3 según la biblioteca SSL instalada.
- Escucha predeterminada en `127.0.0.1:8443`. El certificado, la clave TLS y la clave de API se comprueban antes de abrir el puerto.
- Lista explícita de IPs o redes de clientes. Por defecto solo `127.0.0.1/32` y `::1/128`. No se admiten redes globales `/0`.
- Lista de nombres de servidor aceptados. Por defecto `localhost`, `127.0.0.1` y `::1`; no se aceptan comodines.
- Cabeceras de proxy desactivadas en el lanzador. `X-Forwarded-For` no permite suplantar una IP autorizada y `X-Forwarded-Proto` no convierte HTTP en HTTPS.
- Clave por `X-API-Key`, comparación constante y rechazo de valores ausentes, incorrectos, no ASCII o excesivamente largos. Se valida antes de leer el cuerpo de las rutas protegidas.
- Credencial desde `CHURN_API_KEY_FILE` o `CHURN_API_KEY`, nunca ambas a la vez. No se incluye en logs ni evidencias.
- Predicción, lotes, disponibilidad detallada y documentación OpenAPI protegidos por clave. `/health/live` no necesita clave, pero sí cumple la política de transporte, IP y Host.
- Respuestas de la aplicación con `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`. Los rechazos tempranos no contienen resultados ni secretos.

La política de IP filtra solicitudes después de establecer TLS; no sustituye un firewall del servidor. No se modificó el firewall, el almacén de certificados de Windows ni una instalación de Krayin.

## Preparación y arranque local en Windows

Ejecutar desde la raíz del proyecto con PowerShell 7.4 o superior. El entorno `.venv-clean` ya existe en este equipo; en otro equipo se crea con Python 3.14.6 y `requirements-lock.txt`.

```powershell
python -m venv .venv-clean
.\.venv-clean\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Crear una vez los archivos privados de desarrollo:

```powershell
.\backend\New-LocalSecurity.ps1
```

**En este equipo los archivos ya se generaron durante API-04; no es necesario volver a ejecutar ese comando.** El script rechaza sobrescribir un directorio existente. Genera `.local/security/cert.pem`, `key.pem` y `api-key.txt`; el directorio permite acceso al usuario que lo creó y a SYSTEM. No muestra el secreto. `.local/` está excluido de Git.

El certificado es autofirmado, válido por 30 días y exclusivamente para `localhost`, `127.0.0.1` y `::1`. No se instala como certificado de confianza del sistema. Su finalidad es probar el transporte local; para otro nombre se necesita un certificado que lo incluya.

Configurar el proceso y arrancar:

```powershell
Remove-Item Env:CHURN_API_KEY -ErrorAction SilentlyContinue
$env:CHURN_API_KEY_FILE = '.local/security/api-key.txt'
$env:CHURN_TLS_CERT_FILE = '.local/security/cert.pem'
$env:CHURN_TLS_KEY_FILE = '.local/security/key.pem'
$env:CHURN_ALLOWED_CIDRS = '127.0.0.1/32,::1/128'
$env:CHURN_ALLOWED_HOSTS = 'localhost,127.0.0.1,::1'
$env:CHURN_ALLOW_LOCAL_HTTP = '0'
.\backend\start.ps1
```

La dirección es `https://127.0.0.1:8443`. Los archivos `.env.example` sirven de referencia: no se cargan automáticamente. Detener con Ctrl+C.

## Verificación del certificado por el cliente

El cliente debe confiar explícitamente en `cert.pem` para desarrollo, o en la CA que emita el certificado del servidor definitivo. No desactivar la comprobación del certificado ni del nombre.

Ejemplo Python desde la raíz, usando la misma instalación del proyecto:

```python
import json
import ssl
from pathlib import Path
from urllib.request import Request, urlopen

context = ssl.create_default_context(cafile='.local/security/cert.pem')
key = Path('.local/security/api-key.txt').read_text().strip()
request = Request(
    'https://127.0.0.1:8443/health/ready',
    headers={'X-API-Key': key},
)
with urlopen(request, context=context, timeout=10) as response:
    print(json.load(response))
```

La API tiene estado científico experimental aunque la conexión HTTPS funcione. La respuesta conserva `automatic_action_allowed: false`.

Para una comprobación automática que inicia y cierra servidores temporales:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.verify_api04
```

Esta prueba verifica certificado y nombre reales, TLS negociado, autenticación, rechazo de HTTP, rechazo de Host, restricción por IP y cambio de clave tras reiniciar. No escribe claves en su informe. Se ejecuta fuera del aislamiento de red de herramientas que impidan sockets locales.

## Códigos de rechazo

| Código | Motivo |
|---|---|
| 400 | Host distinto de los nombres permitidos |
| 401 | Clave ausente o inválida en una ruta protegida |
| 403 | IP del cliente no autorizada |
| 426 | HTTP recibido en la aplicación cuando no se permite |

Si se envía HTTP plano al puerto TLS, el rechazo ocurre antes de HTTP y puede observarse como cierre de conexión, no como un 426. No se redirigen solicitudes con claves desde HTTP: el consumidor debe utilizar HTTPS desde el inicio.

## Rotación y renovación

Para rotar la clave de API, generar una clave aleatoria nueva en un archivo privado diferente, distribuirla por un canal seguro al futuro consumidor, cambiar `CHURN_API_KEY_FILE` y reiniciar. La clave anterior deja de funcionar tras reiniciar. Coordinar ese cambio con los clientes: no se implementó una ventana de aceptación de dos claves.

Para renovar el certificado local, ejecutar `New-LocalSecurity.ps1 -Directory '.local/security-renovada'`, configurar las nuevas rutas de certificado/clave y reiniciar. Ese script también genera una clave de API nueva, pero solo se rota la credencial del servicio si se cambia `CHURN_API_KEY_FILE`. El cliente debe actualizar la confianza al nuevo certificado local. En un servidor definitivo se utilizará la renovación que corresponda a su CA.

El proceso de servicio necesita permiso de lectura sobre los archivos privados. Si se usa otra cuenta de Windows, conceder acceso exclusivamente a esa cuenta; no abrir el directorio a todos los usuarios. Nunca compartir `key.pem` con el cliente: solo el certificado público o su CA y la credencial de API por un canal seguro.

## Paso al servidor definitivo

No requiere modificar el código de Krayin para probar la seguridad, pero sí conocer los datos del despliegue:

1. Obtener certificado y clave para el nombre real del servicio; configurar `CHURN_TLS_CERT_FILE` y `CHURN_TLS_KEY_FILE`.
2. Elegir la interfaz concreta en `CHURN_BIND_HOST`. Para una interfaz externa, el lanzador exige `CHURN_ALLOWED_HOSTS` y `CHURN_ALLOWED_CIDRS` explícitos.
3. Autorizar solo la IP o red de salida del servidor que consumirá la API y configurar el firewall del servidor con ese mismo criterio. Una IP permitida no elimina la necesidad de clave.
4. Configurar en el consumidor la URL HTTPS, su credencial y la confianza en la CA. Confirmar certificado, nombre, expiración y conectividad desde ese equipo.
5. Ejecutar las pruebas de aceptación desde el origen permitido y otro origen que deba quedar bloqueado.

Este proyecto proporciona TLS directo y no un perfil de proxy inverso. No colocar un proxy delante sin revisar la política: con las cabeceras de proxy desactivadas, la IP observada es la del proxy. Si se adopta uno, la restricción de clientes debe aplicarse también en esa frontera y el backend debe quedar inaccesible directamente.

HTTP sin TLS existe únicamente para pruebas explícitas en loopback (`CHURN_ALLOW_LOCAL_HTTP=1`, sin archivos TLS). No se permite iniciar HTTP en una interfaz externa, incluso si se configura esa opción. El modo habitual es HTTPS.

## Archivos para capturas

- `backend/security.py`: lectura del secreto, validación de origen, Host y transporte.
- `backend/serve.py`: TLS mínimo, certificados, escucha y cabeceras de proxy desactivadas.
- `docs/evidencias_api/07_seguridad_https.json`: resultados de la comprobación real.
- `docs/evidencias_api/API04_pruebas.txt`: pruebas automatizadas.

Las configuraciones TLS y de proxy se basan en las capacidades de la versión instalada de Uvicorn y su [documentación de ajustes](https://uvicorn.dev/settings/). El registro de IPs usa la dirección de conexión proporcionada por el servidor, no una cabecera enviada por el solicitante.
