# Instrucciones para agentes

Contrato de navegación web y pruebas E2E. Leer también la documentación y las restricciones propias del proyecto. Este documento no cambia su propósito, titularidad, arquitectura ni autorizaciones de operación.

<!-- navegacion-e2e-coherencia-20261025 -->
## Navegación E2E y acceso autorizado — regla vigente (2026-10-25)

Esta regla se aplica automáticamente a la navegación web y a las pruebas E2E web de este proyecto y sus agentes, skills y subdirectorios. En este ámbito prevalece sobre instrucciones anteriores incompatibles, como exigir un navegador visible, un perfil personal, una ruta fija de caché de otro sistema o el tecleo manual de credenciales disponibles.

- Aplicar los skills `playwright` y `chromium-headless`: Chromium interno de Playwright en modo headless, sin abrir ventanas ni depender de Chrome del usuario o de una extensión. Reutilizar el runtime, la configuración y las pruebas del proyecto; resolver el ejecutable con la API y comprobar los parámetros efectivos. Las pruebas nativas de escritorio o móvil conservan su herramienta específica. Si el usuario solicita expresamente su Chrome o su sesión, aplicar `chrome-browser` y los permisos de esa superficie.
- Si el usuario autoriza expresamente cuenta, destino y tarea autenticada, aplicar `acceso-web-autorizado` automáticamente: recuperar e introducir internamente la credencial pertinente de Obsidian, Llavero o la fuente local autorizada, o la que proporcione el usuario. No exigir invocación manual del skill ni volver a pedir su tecleo. Esta cláusula por sí sola no autoriza entrar a cuentas.
- Comprobar origen y cuenta antes de introducir y enviar credenciales; respetar MFA, CAPTCHA y permisos. No eludir una denegación. Máximo dos intentos; no exponer secretos en scripts, argumentos, registros, snapshots, capturas, trazas, repositorios ni informes. Para accesos reales prevalece la fuente autorizada vigente sobre literales heredados.
- El acceso conserva las autorizaciones específicas para envíos, publicaciones, firmas, pagos, borrados y cambios de datos o producción. Cerrar solo la sesión propia. La instalación global no demuestra que este proyecto pase sus pruebas: en otro equipo, cloud o CI comprobar skills, dependencias y navegador por separado; no copiar perfiles ni almacenes de credenciales por inferencia.

Para seleccionar Chromium completo, usar `channel="chromium"` con headless activo (por ejemplo, `headless=True` en Python o `headless: true` en JavaScript). El agente realiza internamente la navegación y las capturas de evidencia cuando la herramienta y el alcance estén autorizados; solicita intervención solo ante una autorización que falte, MFA, CAPTCHA, permisos o un recurso inaccesible. Esta precisión prevalece sobre ejemplos anteriores que deleguen al usuario abrir y capturar una página que el agente puede comprobar dentro del alcance autorizado.

Los procedimientos específicos de grabación o demostración de una interfaz solicitada conservan sus herramientas y permisos. Las comprobaciones internas y E2E web de esos repositorios siguen el carril anterior; los motores productivos existentes conservan su arquitectura.
