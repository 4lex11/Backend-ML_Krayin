# API-07 — Despliegue reproducible y aceptación

Esta tarea prepara entregas versionadas del backend y del artefacto ML, con instalación aislada, arranque administrado, parada ordenada, recuperación tras caída y reversión. La implementación está orientada a **Windows, PowerShell 7.4 o superior y Python 3.14.6 de 64 bits**, que es el entorno utilizado en esta investigación. No necesita Krayin.

**Verificación completada el 28 de octubre de 2026:** 94 pruebas aprobadas, con 95,21 % de cobertura Python, también ejecutadas en el entorno recién instalado. En el ensayo operativo, Windows creó un nuevo proceso 50,11 segundos después de la caída simulada; posteriormente pasó la aceptación HTTPS. Se verificaron actualización a `api-2.0.1-api07-test`, reversión a `api-2.0.0-api07` y parada normal con código 0. La tarea temporal fue eliminada al finalizar.

## Qué se entrega

| Archivo | Función |
|---|---|
| `deploy/New-Release.ps1` | Construye una carpeta nueva, crea su propio entorno virtual, instala `requirements-lock.txt`, ejecuta `pip check` y carga el modelo para una predicción de prueba. |
| `deploy/release.py` | Copia una lista explícita de archivos y genera `release.json` con versión de aplicación, Python, modelo y SHA-256 de cada archivo. Rechaza alteraciones, código adicional, rutas escapadas y otra versión de Python. |
| `deploy/Service.ps1` | Instala, inicia, detiene, reinicia, consulta, actualiza, revierte y desinstala la tarea de Windows. Comprueba que la tarea pertenece al despliegue antes de modificarla. |
| `deploy/runtime.py` | Carga el perfil de entorno, verifica la entrega y ejecuta HTTPS. Observa una señal local de parada y limita los logs a un archivo de 5 MB y tres respaldos. |
| `deploy/acceptance.py` | Comprueba certificado/nombre del servidor, estado, predicción individual y por lote, coincidencia con el artefacto, autenticación, validaciones y OpenAPI. |
| `scripts/Verify-API07.ps1` | Ensayo operativo: reinicio manual, caída intencional del proceso propio, recuperación de Windows, actualización, rollback y parada limpia. Elimina la tarea temporal al terminar. |

Las carpetas de entrega no contienen el CSV original, notebooks, credenciales ni la integración PHP. Cada una incluye código Python, contrato, modelo, metadatos, ejemplo sintético de aceptación y dependencias fijadas. Las versiones anteriores se conservan para poder volver a ellas. No se sobrescribe una entrega existente ni se borra automáticamente un intento incompleto.

El identificador de entrega, por ejemplo `api-2.0.0-api07`, es distinto de la versión del modelo `churn180-v1`. Una actualización técnica no implica un nuevo entrenamiento.

## Crear una entrega

Desde la raíz del proyecto:

```powershell
.\deploy\New-Release.ps1 -Version api-2.0.0-api07 -Python C:\Python314\python.exe
```

En este equipo esa entrega ya fue creada. Para repetir la instalación utilice otro identificador. El resultado queda en `.local/releases/<version>/`; su entorno está en `.venv/`. El script escribe `installed.json` solamente después de comprobar instalación, integridad y carga del modelo.

Se instala el lock completo, que incluye herramientas de entrenamiento y verificación. Esto ocupa más espacio que un entorno dedicado exclusivamente a inferencia, pero mantiene las versiones ya evaluadas. La reproducibilidad está acotada al sistema y versión de Python indicados; no se ha verificado Linux ni otra arquitectura.

Para instalar sin acceso a un índice de paquetes puede preparar un directorio de wheels en el mismo sistema y arquitectura:

```powershell
.\.venv-clean\Scripts\python.exe -m pip download --only-binary=:all: -r requirements-lock.txt -d .local/wheels
.\deploy\New-Release.ps1 -Version api-otra-version -Wheelhouse .local/wheels
```

El manifiesto detecta corrupción o cambios accidentales en el código/modelo. No es una firma digital: el administrador debe proteger las entregas, sus entornos y el manifiesto contra modificaciones no autorizadas, y obtener las dependencias de una fuente de confianza.

## Configurar el entorno

El perfil es un JSON con exactamente siete opciones. No ejecuta expresiones ni interpreta un archivo `.env`. Los secretos permanecen en los archivos privados creados para API-04; el JSON solo guarda sus rutas absolutas. Ejemplo local:

```powershell
$project = (Get-Location).Path
New-Item -ItemType Directory -Path .local/profiles -Force | Out-Null
@{
    CHURN_API_KEY_FILE = (Join-Path $project '.local/security/api-key.txt')
    CHURN_TLS_CERT_FILE = (Join-Path $project '.local/security/cert.pem')
    CHURN_TLS_KEY_FILE = (Join-Path $project '.local/security/key.pem')
    CHURN_BIND_HOST = '127.0.0.1'
    CHURN_PORT = '8443'
    CHURN_ALLOWED_CIDRS = '127.0.0.1/32,::1/128'
    CHURN_ALLOWED_HOSTS = 'localhost,127.0.0.1,::1'
} | ConvertTo-Json | Set-Content .local/profiles/local.json -Encoding utf8
```

El proceso administrado limpia las variables `CHURN_*` heredadas antes de cargar este perfil. Siempre exige HTTPS y selecciona el modelo de su propia entrega. Para entornos diferentes se crea otro perfil, otra tarea y otro directorio de estado. El monitor local debe estar admitido por las IPs y nombres configurados; su certificado debe coincidir con `ProbeHost`.

Los certificados de desarrollo duran 30 días. Para un servidor definitivo se requieren certificado, DNS, cuenta operativa y reglas de red propios, según `API04_SEGURIDAD.md`.

## Instalar y operar

```powershell
.\deploy\Service.ps1 -Action Install `
  -ReleasePath "$PWD/.local/releases/api-2.0.0-api07" `
  -Profile "$PWD/.local/profiles/local.json" `
  -CAFile "$PWD/.local/security/cert.pem"

.\deploy\Service.ps1 -Action Start
.\deploy\Service.ps1 -Action Status
.\deploy\Service.ps1 -Action Restart
.\deploy\Service.ps1 -Action Stop
```

El nombre predeterminado es `CRM-Churn-API`; el estado queda en `.local/deployment/`. La instalación deja la tarea detenida y deshabilitada hasta ejecutar `Start`. Ese comando ejecuta la aceptación HTTPS: no considera suficiente haber solicitado el arranque a Windows. Si falla, detiene la tarea.

La tarea se ejecuta con el usuario actual y privilegios limitados. Al habilitarla, puede arrancar al iniciar sesión y mediante un disparador periódico de recuperación. `-ManualOnly` omite únicamente el disparador de inicio de sesión; conserva la recuperación periódica después de `Start` y se usa en las pruebas. **Este perfil requiere una sesión iniciada: no es un servicio de Windows disponible antes del inicio de sesión ni una instalación de servidor 24/7.** Si el destino requiere funcionamiento sin sesión, se debe desplegar bajo una cuenta de servicio y un supervisor apropiado para ese servidor.

Windows intenta iniciar la tarea cada minuto mientras esté habilitada. Si la instancia sigue ejecutándose, `IgnoreNew` descarta el intento y conserva el proceso actual. Si el proceso terminó, el siguiente disparo lo recupera. La recuperación tarda hasta aproximadamente un minuto más la carga del modelo y continúa intentando una vez por minuto hasta que se deshabilite la tarea. Un error persistente de configuración debe corregirse o detenerse con `Stop`.

Se eligió este mecanismo porque el ensayo local mostró que `RestartOnFailure` no recuperaba la terminación del proceso, incluso con código de salida no cero. El disparador periódico no depende de cómo se clasifique esa salida. Cubre caídas del proceso; no detecta automáticamente bloqueos de un proceso que permanece vivo. `Status` muestra estado de la tarea y resultado de la última ejecución; la comprobación funcional es la aceptación HTTPS.

`Stop` deshabilita la tarea, escribe `stop.request` y espera hasta 45 segundos. El servidor revisa la señal cada 100 ms y usa la parada ordenada de Uvicorn, con hasta 15 segundos para solicitudes en curso. Si no se confirma el cierre, el comando informa el fallo; no mata un PID de forma indiscriminada. La recuperación automática de caídas no anula una parada voluntaria.

La política utiliza las opciones oficiales de [New-ScheduledTaskSettingsSet de Microsoft](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset?view=windowsserver2025-ps).

## Actualizar y revertir

Primero ejecute la regresión del código candidato y construya una entrega nueva. Luego:

```powershell
.\deploy\Service.ps1 -Action Switch -ReleasePath "$PWD/.local/releases/api-nueva-version"
.\deploy\Service.ps1 -Action Rollback
```

`Switch` verifica la entrega antes de detener la anterior; actualiza el ejecutable de la tarea y el descriptor `current.json`, inicia y ejecuta aceptación. Si esta falla, restaura el descriptor y la acción anterior y vuelve a comprobarla. Si la restauración tampoco puede arrancar, el comando devuelve error y debe revisarse la causa común, por ejemplo certificado vencido o puerto ocupado.

`Rollback` intercambia la entrega actual y la anterior, repitiendo las mismas comprobaciones. Esto revierte código, entorno Python y modelo. El perfil compartido no se revierte: antes de cambiar configuración o credenciales, conserve su versión previa en un lugar privado. La actualización implica una breve interrupción; no se implementó un despliegue sin interrupciones.

Para retirar el registro de Windows:

```powershell
.\deploy\Service.ps1 -Action Uninstall
```

Se conservan las entregas, el descriptor, perfil y logs como evidencia. Si posteriormente se reinstala, utilice otro directorio de estado o archive el anterior tras comprobar que no se necesita.

## Evidencia y capturas

- `docs/evidencias_api/API07_instalacion.txt`: instalación en un entorno nuevo, `pip check`, manifiesto y predicción local del artefacto.
- `docs/evidencias_api/API07_instalacion_actualizacion.txt`: segunda entrega con entorno independiente para ensayar actualización y reversión.
- `docs/evidencias_api/API07_pruebas.txt`: resultado de la suite y cobertura del código Python. La cobertura no incluye los scripts PowerShell, que se comprueban mediante el ensayo operativo.
- `docs/evidencias_api/API07_pruebas_entorno_limpio.txt`: misma regresión ejecutada con el intérprete de la entrega recién instalada.
- `docs/evidencias_api/08_despliegue_reversion.json`: resultados del ensayo HTTPS, reinicio, recuperación, actualización y reversión.
- `docs/evidencias_api/API07_tarea_windows.xml`: configuración exportada de la tarea temporal, incluida política de recuperación.
- `docs/evidencias_api/API07_ensayo_operativo.txt`: salida de los comandos del ensayo completo.
- `.local/releases/api-2.0.0-api07/release.json`: versión y hashes para una captura de trazabilidad.
- `.local/api07-verification/state/service.log`: arranques, solicitudes y cierre del ensayo. Evite mostrar rutas personales innecesarias en la tesis.

Para capturas de conclusiones, priorice el JSON de resultados y la última sección de `API07_pruebas.txt`. No fotografíe `api-key.txt` ni `key.pem`. El XML y los logs no contienen la credencial de API, pero sí pueden incluir nombres de usuario y rutas del equipo.

`Verify-API07.ps1` supone que ya existe y está iniciada la tarea de prueba `CRM-Churn-API07Verification`, con estado en `.local/api07-verification/state`, puerto libre y las dos entregas instaladas. Al repetir el ensayo, archive primero el directorio de estado del ensayo anterior; instale e inicie esa tarea mediante `Service.ps1` con un perfil local y `-ManualOnly`. El script no se debe apuntar a una tarea de producción: interrumpe deliberadamente el proceso de prueba y elimina su registro al finalizar. Cuando capture su salida con `Tee-Object`, use una ruta absoluta porque los comandos cambian temporalmente de directorio.

## Conclusión técnica y límites

API-07 permite reproducir una entrega del servicio, detectar alteraciones antes de ejecutarla, verificar su comportamiento por HTTPS y regresar a una entrega conservada. Estas propiedades reducen la dependencia del estado de notebooks o de una terminal abierta y dejan un procedimiento auditable para operar el prototipo.

La aceptación confirma funcionamiento del software y coherencia con el artefacto evaluado. No cambia la conclusión científica: `churn180-v1` sigue siendo experimental y no ha demostrado utilidad predictiva suficiente para automatizar campañas. No se ha probado impacto real en fidelización, conexión con Krayin, reinicio del equipo ni despliegue externo.
