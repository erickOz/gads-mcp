"""Handshake MCP contra el comando EXACTO que cada cliente tiene configurado.

Lee las 5 configs reales de cliente (no hardcodea rutas), lanza cada una con
`cwd=/` como hacen los clientes de verdad, y mide `initialize` + `tools/list`.

Uso:
  .venv/bin/python deploy/smoke-clients.py

Esperado: las 5 filas en ✓ con 78 tools. Si una tarda >10 s o falla, revisa
`docs/setup-clients.md` y los "Aprendizajes acumulados" de `AGENTS.md`.

Esto verifica que el comando configurado arranca y responde. NO verifica la app
en sí: para eso hay que ejercitar cada cliente (ver `handoff/PROGRESS.md`,
entrada de T-02, para el método headless de Codex y OpenCode).
"""

import json
import os
import re
import subprocess
import time
import tomllib

expand = os.path.expanduser


def read_json(path):
  """Carga JSON, tolerando comentarios `//` (formato .jsonc de OpenCode)."""
  with open(expand(path), encoding="utf-8") as fh:
    raw = fh.read()
  return json.loads(re.sub(r"^\s*//.*$", "", raw, flags=re.M))


def collect():
  """Devuelve [(cliente, command, args, env)] leido de las configs reales."""
  out = []

  # Los 3 que usan el esquema `mcpServers` de Claude.
  claude_like = (
      ("Claude Code (~/.claude.json)", "~/.claude.json"),
      ("Claude Code (settings.json)", "~/.claude/settings.json"),
      ("Claude Desktop",
       "~/Library/Application Support/Claude/claude_desktop_config.json"),
  )
  for label, path in claude_like:
    s = read_json(path).get("mcpServers", {}).get("google-ads-mcp")
    if s:
      out.append((label, s["command"], s["args"], s.get("env", {})))

  with open(expand("~/.codex/config.toml"), "rb") as fh:
    s = tomllib.load(fh).get("mcp_servers", {}).get("google-ads-mcp")
  if s:
    out.append(("Codex", s["command"], s["args"], s.get("env", {})))

  s = read_json("~/.config/opencode/opencode.jsonc").get("mcp", {}).get(
      "google-ads")
  if s:
    cmd = s["command"]
    out.append(("OpenCode", cmd[0], cmd[1:], s.get("environment", {})))

  return out


INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "smoke", "version": "1"},
    },
}
NOTIF = {"jsonrpc": "2.0", "method": "notifications/initialized"}
LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}


def run(name, command, args, env):
  full = {**os.environ, **env}
  t0 = time.time()
  try:
    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=full,
        cwd="/",  # como lo lanzan los clientes
        text=True,
    )
  except FileNotFoundError as exc:
    print(f"{name:32} ✗ NO ARRANCA: {exc}")
    return

  def send(msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()

  def read_id(target):
    """Lee lineas hasta encontrar la respuesta a `target`."""
    while True:
      line = proc.stdout.readline()
      if not line:
        return None
      line = line.strip()
      if not line.startswith("{"):
        continue
      try:
        msg = json.loads(line)
      except json.JSONDecodeError:
        continue
      if msg.get("id") == target and "result" in msg:
        return msg["result"]

  init_t = None
  n_tools = None
  try:
    send(INIT)
    if read_id(1) is not None:
      init_t = time.time() - t0
    send(NOTIF)
    send(LIST)
    res = read_id(2)
    if res is not None:
      n_tools = len(res.get("tools", []))
  except (BrokenPipeError, OSError):
    pass
  finally:
    proc.kill()
    proc.wait()

  if init_t is None:
    print(f"{name:32} ✗ sin respuesta a initialize")
    return
  print(f"{name:32} ✓ initialize {init_t:5.2f}s · tools: {n_tools}")


if __name__ == "__main__":
  print(f"{'CLIENTE':32} RESULTADO")
  print("-" * 62)
  for entry in collect():
    run(*entry)
