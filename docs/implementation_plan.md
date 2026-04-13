# Implementación Local de Google Ads MCP

El objetivo es instalar y dejar funcional el servidor MCP de Google Ads dentro de tu carpeta `gads-mcp`. Con esto lograrás que clientes MCP (como Gemini o la aplicación de escritorio de Claude) se puedan conectar directamente a tus campañas y descargar/analizar data usando tus credenciales.

## Cambios Propuestos

### 1. Descarga del Código Fuente
Copiaremos los archivos desde el repositorio oficial de Google (alojados temporalmente en `tmp`) hacia tu directorio de proyecto local.
* **Directorio Destino:** `/Users/erickoz/.../gads-mcp`

### 2. Configuración de Credenciales
Dado que tu archivo `google-ads.yaml` se encuentra en `~/.config/google-ads.yaml`, tenemos dos alternativas de configuración para el servidor MCP, y la forma más limpia y robusta es pasar la ruta mediante una variable de entorno `GOOGLE_ADS_CREDENTIALS`. Modificaremos ligeramente el entorno para que lo lea desde allí automáticamente sin tener que hacer _hardcode_ en el código.

### 3. Instalación de Dependencias
El repositorio original usa `uv` (un instalador de paquetes de Python de la compañía Astral muy rápido). 
* Crearemos un entorno virtual en la carpeta y ejecutaremos `uv sync` o `uv pip install` para asegurar que dependencias como `google-ads`, `fastmcp` y demás estén listas.
* Si no tienes `uv` instalado a nivel sistema en macOS, usaremos `pip` estándar usando el `pyproject.toml` proporcionado, o bien instalaremos `uv` primero si estás de acuerdo.

### 4. Archivo Ejecutor `.env` o `.sh` (Opcional pero Recomendado)
Crearemos un pequeño _script_ `run_mcp.sh` que puedes apuntar en la configuración de tu cliente MCP. Este ejecutor exportará la variable `GOOGLE_ADS_CREDENTIALS=~/.config/google-ads.yaml` y luego levantará el servidor (`uv run -m ads_mcp.server`).

## Cuentas Requeridas / Revisión del Usuario
> [!IMPORTANT]
> **Manejador de dependencias:** ¿Tienes `uv` instalado en tu sistema Mac? Si no lo tienes, ¿puedo proceder a instalarlo con `curl -LsSf https://astral.sh/uv/install.sh | sh` o prefieres que configuremos el entorno con `pip` estándar y `venv`? El repositorio oficial recomienda fuertemente usar `uv`.

> [!NOTE]
> **Cliente MCP:** ¿Desde dónde piensas interactuar con este MCP? (¿Claude Desktop, Cursor, Gemini avanzado o algún otro?). Esto me ayudará a dejarte lista la porción de texto JSON que deberás copiar y pegar en la configuración de la aplicación cliente.

## Plan de Verificación

### Pruebas Automatizadas (Local)
1. Ejecutar el comando del servidor MCP usando tu archivo `google-ads.yaml` para asegurar que el servidor levante sin errores `FileNotFoundError` o errores de autenticación.
2. Validaremos que la ruta a `~/.config/google-ads.yaml` es resuelta correctamente por el sistema.
