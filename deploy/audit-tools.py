"""Auditoria funcional del MCP: ejercita las tools de LECTURA y reporta errores.

Levanta su propia instancia del server por stdio, descubre IDs reales (MCC ->
cuenta hija con campana y ad group activos) y llama a cada tool de la allowlist,
capturando el resultado o el error.

Uso:
  .venv/bin/python deploy/audit-tools.py

Complementa a `deploy/smoke-clients.py`: aquel comprueba que el server ARRANCA
desde cada cliente; este comprueba que las tools RESPONDEN contra la API real.
Atrapa la clase de bug que los tests mockeados no ven (campos GAQL que la v24
dejo de aceptar). Encontro B-12 y B-13 del backlog.

SEGURIDAD: la allowlist READ_ONLY es deliberada. NUNCA agregues aqui una tool
que cree, modifique o borre nada: esto corre contra cuentas de produccion.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time

REPO = "/Users/erickoz/Developer/gads-mcp"
PY = f"{REPO}/.venv/bin/python"
CREDS = os.path.expanduser("~/.config/google-ads.yaml")

# Solo lectura. Cualquier tool que cree/modifique/borre queda fuera a proposito.
READ_ONLY = [
    "list_accessible_accounts",
    "get_gaql_doc",
    "get_reporting_fields_doc",
    "get_reporting_view_doc",
    "get_campaign_performance",
    "get_ad_performance",
    "get_keyword_performance",
    "get_search_terms_report",
    "get_quality_score_report",
    "get_auction_insights",
    "get_change_history",
    "list_conversion_actions",
    "list_audiences",
    "list_labels",
    "list_recommendations",
    "list_experiments",
    "list_shared_budgets",
    "list_portfolio_bidding_strategies",
    "list_campaign_locations",
    "list_ad_schedules",
    "list_ad_group_demographics",
    "list_assets",
    "search_geo_targets",
    "generate_keyword_ideas",
]


class MCP:
  """Cliente JSON-RPC minimo por stdio, con timeout por llamada."""

  def __init__(self):
    env = {**os.environ, "GOOGLE_ADS_CREDENTIALS": CREDS}
    self.proc = subprocess.Popen(
        [PY, "-m", "ads_mcp.stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd="/",
        text=True,
        bufsize=1,
    )
    self.q = queue.Queue()
    self.nid = 0
    threading.Thread(target=self._reader, daemon=True).start()

  def _reader(self):
    for line in self.proc.stdout:
      line = line.strip()
      if line.startswith("{"):
        try:
          self.q.put(json.loads(line))
        except json.JSONDecodeError:
          pass

  def _send(self, msg):
    self.proc.stdin.write(json.dumps(msg) + "\n")
    self.proc.stdin.flush()

  def _await(self, rid, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
      try:
        msg = self.q.get(timeout=deadline - time.time())
      except queue.Empty:
        break
      if msg.get("id") == rid:
        return msg
    raise TimeoutError(f"sin respuesta en {timeout}s")

  def request(self, method, params=None, timeout=120):
    self.nid += 1
    self._send({
        "jsonrpc": "2.0",
        "id": self.nid,
        "method": method,
        "params": params or {},
    })
    return self._await(self.nid, timeout)

  def handshake(self):
    t0 = time.time()
    self.request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "audit", "version": "1"},
    })
    self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    return time.time() - t0

  def call(self, name, args, timeout=120):
    """Devuelve (ok, payload). ok=False si el server marca isError."""
    try:
      msg = self.request("tools/call", {"name": name, "arguments": args},
                         timeout=timeout)
    except TimeoutError as exc:
      return False, f"TIMEOUT: {exc}"
    if "error" in msg:
      return False, f"JSONRPC ERROR: {msg['error']}"
    res = msg.get("result", {})
    text = ""
    for block in res.get("content", []):
      if block.get("type") == "text":
        text += block["text"]
    if res.get("isError"):
      return False, text[:400]
    return True, text

  def close(self):
    try:
      self.proc.stdin.close()
    except OSError:
      pass
    self.proc.kill()
    self.proc.wait()


def jparse(text):
  try:
    return json.loads(text)
  except (json.JSONDecodeError, TypeError):
    return None


def rows(text):
  """Normaliza el payload.

  El server no es uniforme: `execute_gaql` y las tools de reporting devuelven
  {"data": [...]}, otras {"result": [...]}, y alguna la lista pelada.
  """
  data = jparse(text)
  if isinstance(data, dict):
    for key in ("data", "result", "results"):
      if isinstance(data.get(key), list):
        return data[key]
    return None
  return data if isinstance(data, list) else None


def main():
  mcp = MCP()
  try:
    dt = mcp.handshake()
    tools = mcp.request("tools/list")["result"]["tools"]
    by_name = {t["name"]: t for t in tools}
    print(f"handshake {dt:.2f}s · {len(tools)} tools registradas\n")

    # ---- Descubrimiento de IDs reales ----
    ok, txt = mcp.call("list_accessible_accounts", {})
    if not ok:
      print(f"FATAL: list_accessible_accounts fallo: {txt}")
      return 1
    accs = rows(txt) or []
    if not accs:
      print(f"FATAL: sin cuentas accesibles: {txt[:200]}")
      return 1
    mcc = str(accs[0])
    print(f"MCC: {mcc}")

    ok, txt = mcp.call("execute_gaql", {
        "customer_id": mcc,
        "query": ("SELECT customer_client.id, customer_client.descriptive_name "
                  "FROM customer_client WHERE customer_client.manager = FALSE "
                  "AND customer_client.status = 'ENABLED'"),
    })
    children = []
    if ok:
      for row in (rows(txt) or []):
        cid = str(row.get("customer_client.id") or row.get("id") or "")
        if cid:
          children.append((cid, row.get("customer_client.descriptive_name")))
    print(f"cuentas hijas ENABLED: {len(children)}")

    ctx = {"customer_id": mcc, "login_customer_id": mcc}
    campaign_id = ad_group_id = None
    chosen = None

    for cid, nombre in children:
      ok, txt = mcp.call("execute_gaql", {
          "customer_id": cid,
          "login_customer_id": mcc,
          "query": ("SELECT campaign.id, ad_group.id FROM ad_group "
                    "WHERE campaign.status = 'ENABLED' "
                    "AND ad_group.status = 'ENABLED' LIMIT 1"),
      })
      rr = rows(txt) if ok else None
      if rr:
        campaign_id = str(rr[0].get("campaign.id"))
        ad_group_id = str(rr[0].get("ad_group.id"))
        chosen = (cid, nombre)
        break

    if chosen:
      ctx["customer_id"] = chosen[0]
      ctx["campaign_id"] = campaign_id
      ctx["ad_group_id"] = ad_group_id
      print(f"cuenta de prueba: {chosen[0]} ({chosen[1]}) "
            f"campaign={campaign_id} ad_group={ad_group_id}\n")
    else:
      print("aviso: ninguna cuenta hija con campana+ad group activos\n")

    # Valores por defecto para parametros comunes.
    hoy = time.strftime("%Y-%m-%d")
    hace7 = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    ctx.update({
        "days": 7,
        "date_range": "LAST_7_DAYS",
        "limit": 5,
        "start_date": hace7,
        "end_date": hoy,
        "fields": ["campaign.id", "metrics.clicks"],
        "search_term": "Peru",
        "seed_keywords": ["zapatillas running"],
        "query_text": "zapatillas running",
        "keywords": ["zapatillas running"],
        "location_name": "Peru",
        "view_name": "campaign",
        "resource_name": "campaign",
    })

    # ---- Bateria ----
    print(f"{'TOOL':38} {'':6} DETALLE")
    print("-" * 96)
    fails = []
    skipped = []
    for name in READ_ONLY:
      spec = by_name.get(name)
      if not spec:
        skipped.append((name, "no registrada"))
        continue
      schema = spec.get("inputSchema", {})
      required = schema.get("required", [])
      props = schema.get("properties", {})
      args = {}
      missing = []
      for p in required:
        if p in ctx:
          args[p] = ctx[p]
        else:
          missing.append(p)
      if missing:
        falta = ", ".join(missing)
        skipped.append((name, f"faltan params: {falta}"))
        continue
      # login_customer_id ayuda en cuentas bajo MCC
      if "login_customer_id" in props and "login_customer_id" not in args:
        args["login_customer_id"] = mcc

      t0 = time.time()
      ok, txt = mcp.call(name, args, timeout=180)
      el = time.time() - t0
      if ok:
        rr = rows(txt)
        n = len(rr) if rr is not None else None
        extra = f"{n} filas" if n is not None else f"{len(txt)} chars"
        estado = "OK"
        print(f"{name:38} {estado:6} {el:5.1f}s · {extra}")
      else:
        one = " ".join(txt.split())[:150]
        estado = "FALLA"
        print(f"{name:38} {estado:6} {el:5.1f}s · {one}")
        fails.append((name, one))

    print("\n" + "=" * 96)
    print(f"OK: {len(READ_ONLY) - len(fails) - len(skipped)} · "
          f"FALLAS: {len(fails)} · OMITIDAS: {len(skipped)}")
    for name, why in skipped:
      print(f"  omitida  {name:36} {why}")
    for name, why in fails:
      print(f"  FALLA    {name:36} {why}")
    return 1 if fails else 0
  finally:
    mcp.close()


if __name__ == "__main__":
  sys.exit(main())
