# MEJ-02 Variables temporales de compra

Estado: completada el 29/10/2026. Se añadió `ML/features_v2.py` para experimentos de `churn180-v2`. El módulo de inferencia actual, la API, Krayin y las siete variables de `churn180-v1` no cambian.

## Fuente y límites temporales

Las variables se construyen después de `clean_transactions`, sobre `(corte − 365 días, corte]`. Una transacción en el día inicial de cada ventana queda excluida y una del día de corte queda incluida. Los pedidos posteriores al corte no intervienen. El código usa pedidos distintos para actividad y cadencia, y líneas de venta para importes; por tanto, un pedido con varios productos cuenta una vez como pedido y conserva todas sus ventas.

El cliente permanece en la salida únicamente si su última compra histórica ocurrió hace 180 días o menos. No se crean filas para clientes inactivos ni se les asigna una probabilidad ficticia. `MEJ-03` agregará la etiqueta futura de abandono mediante la función existente, por separado de estas variables.

## Esquema v2

| Variable | Definición | Regla de calidad |
|---|---|---|
| `Orders_30d`, `Orders_90d`, `Orders_180d` | Pedidos distintos en cada ventana reciente | Cero si no hubo pedido en la ventana. |
| `Sales_30d`, `Sales_90d`, `Sales_180d` | Suma de ventas por líneas en cada ventana | Cero si no hubo venta; se mantienen las reglas de ventas finitas/no negativas. |
| `Recent90_To_Prior90_Order_Ratio` | `(pedidos últimos 90 + 1) / (pedidos 90 previos + 1)` | El suavizado evita división entre cero y conserva la señal de actividad reciente. |
| `ActiveMonths_365d` | Meses calendario distintos con al menos una línea de venta | Entre 1 y 13: una ventana móvil de 365 días puede abarcar partes de 13 meses. |
| `MeanOrderGapDays`, `StdOrderGapDays` | Media y desviación muestral de días entre fechas de pedidos consecutivos | Ambas son 0 con un único pedido; consultar el indicador asociado. |
| `HasMultipleOrders` | 1 si existen dos o más pedidos históricos; 0 en caso contrario | Distingue falta de intervalos de una cadencia regular. |

No se incluyen Customer ID, nombre, ciudad, región, segmento, producto ni categoría como identificadores que permitan memorizar clientes. Tampoco se imputan costos, campañas, satisfacción o márgenes inexistentes en el dataset. Estas variables son candidatas; su presencia no presupone que mejoren el modelo.

## Controles implementados

La prueba unitaria cubre límites de 365/180/90 días, pedidos con varias líneas, cliente con un solo pedido, valores finitos y mutación de ventas/pedidos posteriores al corte. Esta última debe producir exactamente el mismo resultado. La verificación sobre el CSV completo confirma hash, esquema de 11 columnas, población en D1/D2/E1 y finitud de todas las columnas.

Ejecutar desde la raíz:

```powershell
& .\.venv-clean\Scripts\python.exe -m pytest tests/test_features_v2.py -q
& .\.venv-clean\Scripts\python.exe scripts/verify_mej02.py
```

La evidencia se escribe en `docs/evidencias_mej02/verificacion.json`. MEJ-03 debe usar este módulo mediante una ruta de experimentación nueva y no ampliar el contrato del endpoint actual.

## Cierre verificado

Se aprobaron 52 pruebas de variables y regresión del contrato existente, excluyendo una prueba que vuelve a entrenar v1. Se corrigió la razón de actividad para clientes ausentes en uno de los periodos: primero se alinean ambos conteos con todos los clientes y luego se suma uno. Se verificaron también eliminación de compras futuras, orden de líneas y elegibilidad exactamente a 180 días. La desviación muestral se representa con cero cuando hay menos de dos intervalos (uno o dos pedidos); `HasMultipleOrders` distingue un único pedido, pero no acredita por sí solo una estimación fiable de dispersión.

La primera regresión encontró restricciones de permisos en el directorio temporal/caché de pytest; al usar un directorio temporal nuevo dentro del proyecto y deshabilitar la caché, las 52 pruebas aprobaron. Permanece un aviso de deprecación de Starlette/TestClient. Comando de regresión: `python -m pytest tests/test_features_v2.py tests/test_separation.py -q -k 'not training_pipeline' -p no:cacheprovider --basetemp=.local/mej02-test-temp-final` (en futuras ejecuciones, usar un directorio temporal nuevo).

Black y Ruff aprobaron los archivos nuevos. La comprobación del dataset produjo 351, 510 y 431 clientes para D1, D2 y E1; todas las variables fueron finitas y no cambiaron al modificar ventas futuras. Estos controles verifican el cálculo, no una mejora predictiva: el entrenamiento sigue pendiente de MEJ-04.
