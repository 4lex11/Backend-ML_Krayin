# Prototipos existentes de integración con Krayin

Estos archivos fueron trasladados desde `ML/` porque preparan datos para el CRM y escriben en su base de datos; no entrenan modelos.

- `Importar_datos_Omitir.ipynb`: lee `ML/predicciones_crm_churn.csv`, agrega contactos ficticios y produce el CSV de esta carpeta.
- `predicciones_crm_churn_perfecto.csv`: exportación histórica de 793 clientes con datos de contacto de demostración.
- `mandar_data.ipynb`: inserta contactos en `persons` y atributos en `attribute_values` de una base MySQL local.

Se actualizaron las rutas para ejecutar los notebooks desde la raíz o esta carpeta. Las salidas guardadas son históricas: el importador no se ejecutó durante la separación.

El importador conserva supuestos del prototipo: usuario `root`, contraseña vacía, base `laravel-crm`, usuario asignado 1 e identificadores de atributos 61–65. Inserta nuevos contactos en cada ejecución, sin deduplicación por identificador externo ni adaptación al esquema de otra instalación. El importador vigente ya usa la capa de aplicación de Krayin, configuración y control de errores; estos notebooks se conservan como antecedentes.

El código PHP operativo está en `C:/xampp/htdocs/KrayinCRM/laravel-crm-2.2/packages/Webkul/Churn/src`. La integración y su validación local están completadas. Utilizar la [guía final](../../docs/GUIA_FINAL_CRM.md); no ejecutar estos notebooks para cargar la demostración actual.
