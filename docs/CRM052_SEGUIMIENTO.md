# CRM-05.2 — seguimiento manual de demostración

Completada el 29/10/2026. El detalle del cliente incorpora una sección de seguimiento para el **cliente, fecha de corte y versión seleccionados**. Puede revisarse también un contexto sin predicción: la revisión no inventa una probabilidad ni convierte al cliente en elegible.

## Uso

1. Entrar al módulo y abrir el detalle del cliente en el corte y versión que se quieren revisar.
2. En «Seguimiento manual de demostración», seleccionar estado y responsable, escribir una nota y pulsar «Registrar revisión».
3. Comprobar el estado más reciente y el historial inferior. Cada guardado añade una entrada; no modifica ni elimina las anteriores.

| Estado | Interpretación |
|---|---|
| Pendiente | La revisión queda por completar o se reabre con una nota. |
| Revisado | Se ha registrado una revisión humana del contexto. No acredita contacto ni una acción comercial. |
| Descartado | Se decide no continuar con ese seguimiento de demostración; el motivo se consigna en la nota. No borra al cliente ni su predicción. |

No hay transiciones comerciales automáticas ni estados de «cliente retenido». El usuario puede cambiar entre los tres estados agregando una nueva justificación. El primer registro puede usar cualquiera de ellos; antes de registrar algo se muestra «Sin revisión registrada», sin asignar responsable ni autor ficticios.

## Permisos y responsable

- Lectura: permiso `churn` y ámbito del cliente por propietario, igual que el detalle existente.
- Escritura: requiere **`churn` y `churn.review`** («Registrar seguimiento manual»). El permiso `churn.update` de predicciones no autoriza por sí solo revisar.
- Los roles con todos los permisos pueden registrar revisiones. Para un rol personalizado, habilitar el nuevo permiso desde la gestión normal de roles de Krayin. No se modificaron permisos de cuentas existentes.
- Responsables: usuarios activos dentro del ámbito del revisor. En ámbito individual, el propio usuario; en grupo, los usuarios autorizados del grupo; en global, usuarios activos. La asignación es un dato del registro, no envía notificaciones ni concede permisos a otra cuenta.
- Autor y fecha UTC se obtienen en el servidor. No se aceptan valores de autoría o fecha enviados desde el formulario.

## Historial y validación

Cada registro conserva estado, nota, ID/nombre del responsable, ID/nombre del autor y fecha UTC con microsegundos. Los nombres se guardan como referencia histórica para no perder la atribución si una cuenta cambia de nombre o se elimina; los IDs de usuario no tienen borrado en cascada. El cliente tiene clave foránea restrictiva. La pantalla muestra el registro más reciente y pagina el historial en grupos de diez, con paginación independiente de las predicciones.

La nota es obligatoria, se recorta el espacio exterior y admite hasta 2.000 caracteres. Solo se aceptan los tres estados, una fecha dentro de la cobertura y una versión con formato validado. El responsable debe seguir activo y dentro del ámbito al guardar. El contenido se escapa y las notas se presentan como texto literal, también frente a expresiones de plantilla Vue. No incluir secretos ni datos personales innecesarios.

El formulario envía el ID del último registro que vio. Dentro de una transacción se bloquea el cliente, se comprueba el ámbito y se compara ese ID. Si otra revisión se guardó entretanto, o se reenvía el mismo formulario, se rechaza la entrada desactualizada. La nota se conserva en el formulario con un mensaje: copiarla si se necesita, recargar el detalle, revisar el último estado y volver a guardar. No se sobrescribe silenciosamente el trabajo de otra persona.

POST protegido por sesión, ACL, CSRF y límite de solicitudes. La ruta usa el adaptador CSRF ya verificado en CRM-04.4 para devolver 419 correctamente. No existen endpoints de edición o borrado de revisiones.

## Implementación y operación

- Migración aplicada: `2026_10_29_000004_create_churn_reviews_table.php`.
- Tabla: `churn_reviews`.
- Modelo `Models/Review.php`, contrato/repositorio `ReviewRepository`, registro en el proveedor y permiso `churn.review`.
- Ruta: `POST /{prefijo}/churn/customers/{customer}/reviews`, nombre `admin.churn.review`.
- Vista `Resources/views/show.blade.php` y traducciones españolas/inglesas.

No requiere la API Python ni el procesador de predicciones para registrar o leer revisiones: usa la base local de Krayin. No altera resultados ML, probabilidades, categorías o sugerencias. El seguimiento manual no crea campañas, contactos ni actividades comerciales.

## Verificación y capturas

**65 casos y 218 aserciones sin fallos**: 54 casos / 186 aserciones de seguimiento, detalle, sugerencias e importación, más 11 / 32 de acceso aislado. Incluyen 21 casos nuevos de seguimiento. Persisten avisos preexistentes de deprecación PDO bajo PHP 8.5; no se midió cobertura.

Las pruebas verificaron estados, historial sin sobreescritura, fecha/versión independientes, ámbito vacío o ajeno, responsables inactivos o ajenos, permisos separados, entradas inválidas, notas escapadas, autoría no falsificable, reenvíos, paginación y conservación de predicciones. Los cambios de prueba se revirtieron con transacciones.

La prueba real en Edge registró dos notas de demostración con una cuenta temporal, comprobó el estado «Revisado», rechazó un formulario antiguo, rechazó POST sin CSRF con 419 y comprobó que un usuario de solo lectura puede ver el historial pero no registrar revisiones. También verificó una nota con expresión de plantilla como texto literal y ausencia de desbordamiento móvil/errores JavaScript.

Archivos para capturar o revisar:

1. `docs/evidencias_crm052/seguimiento_historial.png`: formulario, estado más reciente e historial con responsable, autor y fecha.
2. `docs/evidencias_crm052/seguimiento_movil.png`: sección en pantalla pequeña.
3. `docs/evidencias_crm052/navegador.json`: comprobaciones reales del navegador.
4. `docs/evidencias_crm052/pruebas.txt` y `acceso.txt`: resultados de las pruebas.
5. `docs/evidencias_crm052/rutas.txt`: protección de la ruta.

Las capturas contienen notas y una cuenta **QA de demostración**, no revisiones reales del negocio. Se eliminaron exclusivamente esas notas y la cuenta/rol temporales al finalizar; el servidor web temporal se cerró. Los archivos anteriores se conservan en `.local/crm052-backup`. No se modificaron los contactos ni sus atributos.

## Pendiente

CRM-01 a CRM-05 completados en el alcance local. CRM-06.1 se completó posteriormente: [acta de aceptación integral](CRM061_VALIDACION_INTEGRAL.md). CRM-06.2 también completada: [guía final](GUIA_FINAL_CRM.md) e [índice de evidencias](INDICE_EVIDENCIAS_FINAL.md).
