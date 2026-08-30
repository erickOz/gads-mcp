#!/usr/bin/env python3
"""Repoint every MCP client config from an old repo path to a new one.

Cuando este repo se mueve de carpeta, cinco archivos de configuración quedan
apuntando a la ruta vieja y todos los clientes fallan con "Connection closed".
Este script los actualiza de una vez. Ver docs/setup-clients.md.

Uso:
    python3 deploy/repoint-mcp-configs.py <ruta-vieja> <ruta-nueva>          # dry run
    python3 deploy/repoint-mcp-configs.py <ruta-vieja> <ruta-nueva> --apply

Reemplazo literal de texto, así que el formato y los comentarios (JSONC, TOML)
sobreviven. Deja un .bak-gadspath junto a cada archivo que toca. Es idempotente.

Recuerda: después de mover la carpeta hay que recrear el entorno con `uv sync`,
porque el editable install guarda rutas absolutas.
"""
import os
import shutil
import sys

TARGETS = [
    "~/.claude.json",
    "~/.claude/settings.json",
    "~/Library/Application Support/Claude/claude_desktop_config.json",
    "~/.codex/config.toml",
    "~/.config/opencode/opencode.jsonc",
]


def main(argv: list[str]) -> int:
  args = [a for a in argv[1:] if not a.startswith("--")]
  if len(args) != 2:
    print(__doc__)
    return 2
  old, new = args
  dry = "--apply" not in argv

  for target in TARGETS:
    path = os.path.expanduser(target)
    if not os.path.isfile(path):
      print(f"SKIP (no existe): {path}")
      continue
    with open(path, encoding="utf-8") as f:
      text = f.read()
    n = text.count(old)
    if n == 0:
      print(f"OK (nada que cambiar): {path}")
      continue
    if dry:
      print(f"CAMBIARÍA {n} ocurrencia(s): {path}")
      continue
    shutil.copy2(path, path + ".bak-gadspath")
    with open(path, "w", encoding="utf-8") as f:
      f.write(text.replace(old, new))
    print(f"CAMBIADAS {n} ocurrencia(s): {path}")

  print("\n(dry run — pasa --apply para escribir)" if dry else "\nListo.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main(sys.argv))
