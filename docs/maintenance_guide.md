# Guía de Mantenimiento y Actualizaciones

Al haber clonado el repositorio oficial, tu carpeta local ya está vinculada al código fuente original de Google. Aquí tienes el flujo de trabajo para mantener tu servidor MCP al día.

## 1. Actualizar el Código Fuente (Git)

Para traer las últimas mejoras o correcciones del repositorio oficial, ejecuta estos comandos en tu terminal dentro de la carpeta `gads-mcp`:

```bash
# Descargar los últimos cambios
git fetch origin

# Fusionar los cambios en tu rama local
git pull origin main
```

> [!TIP]
> Si has hecho cambios personales en el código fuente (no en los archivos `.sh` o `.json` que creamos), te recomiendo usar `git stash` antes de hacer el pull para evitar conflictos, y luego `git stash pop`.

## 2. Actualizar Dependencias

Cada vez que descargues código nuevo, es posible que se hayan añadido nuevas librerías. Debes sincronizar tu entorno virtual ejecutando:

```bash
# Sincroniza las dependencias según el nuevo uv.lock
~/.local/bin/uv sync
```

## 3. Actualizar la Librería MCP

Si el protocolo MCP evoluciona o se actualiza la librería base `fastmcp`, puedes forzar la actualización de los paquetes de Python con:

```bash
~/.local/bin/uv pip install --upgrade fastmcp mcp
```

## 4. Estructura de "Upstream" (Recomendado)

Si decides subir este proyecto a **tu propio repositorio de GitHub** para respaldar tus configuraciones personalizadas (`run_mcp.sh`, etc.), te sugiero renombrar el acceso de la siguiente manera:

1.  Renombra el actual `origin` a `upstream`:
    `git remote rename origin upstream`
2.  Agrega tu propio repositorio como `origin`:
    `git remote add origin https://github.com/tu-usuario/tu-repo.git`

De esta forma, actualizarás con `git pull upstream main` y respaldarás tus cosas con `git push origin main`.

---

**Nota sobre credenciales:** Tus archivos `google-ads.yaml` y `run_mcp.sh` están a salvo. El `.gitignore` del proyecto suele proteger archivos sensibles, pero siempre verifica que tus tokens no se suban a repositorios públicos si decides crear uno propio.
