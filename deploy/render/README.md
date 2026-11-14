# Preparación de API para Render Free

Estado: configuración preparada, aún no construida ni desplegada. Docker no está instalado en el equipo de preparación. No se afirma compatibilidad Linux ni consumo inferior a 512 MB hasta comprobar el build y medir el servicio.

Repositorio: https://github.com/4lex11/Backend-ML_Krayin
Dockerfile: `deploy/render/Dockerfile`, contexto raíz, plan Free, un proceso de inferencia.
Variables privadas: `CHURN_API_KEY` (32 a 512 caracteres ASCII sin espacios). No añadirla a Git ni como argumento de build.

## Transporte

Render termina HTTPS público. Nginx recibe su tráfico HTTP en PORT y lo reenvía únicamente a 127.0.0.1:8443, donde Python aplica la excepción explícita de HTTP local ya existente. No se confía en cabeceras reenviadas para autorizar clientes. Los endpoints de predicción conservan X-API-Key. La lista de IP de Python verifica el proxy local, no la IP del cliente público. La autenticación de aplicación es por clave. Esta configuración solo corresponde al entorno detrás del HTTPS administrado de Render.

Comprobar `/health/live` y luego `/health/ready` con autenticación y una predicción contra el artefacto local. El health check público no sustituye la aceptación autenticada.

## Pendientes antes de publicar el sistema completo

- Construir imagen y validar disponibilidad Linux de todas las versiones fijadas en el manifiesto del modelo. No cambiar versiones para forzar el build.
- Medir RAM de inferencia y arranque en Free.
- Preparar Krayin desde https://github.com/4lex11/FrontendKrayin con TLS de TiDB, sesiones y cola persistentes en la base.
- Crear TiDB Starter MySQL, gasto máximo US$0. Probar migraciones e importación en una base nueva antes de cambiar la conexión.
- Configurar en Krayin la clave como archivo privado y el bundle CA del sistema para verificar HTTPS de la API.
- Verificar el despertar de la API: el cliente PHP tiene un presupuesto de 50 segundos que puede agotarse mientras Render inicia el servicio.
- Los archivos subidos al disco local de Render no persisten. Resolver adjuntos antes de habilitar su uso.
- El espacio ya contiene otro servicio Free. Las 750 horas gratuitas mensuales se comparten entre todos los servicios del espacio. No prometer tres servicios encendidos todo el mes.
- No modificar ni detener el servicio existente `traductor-lsp-api`.

Fuentes: https://render.com/docs/free y https://render.com/docs/docker (consultadas el 13/11/2026).
