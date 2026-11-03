#!/usr/bin/env python3
"""Loopback-only, read-only paper demo dashboard. Standard library only."""
import argparse
import html
import json
import os
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

DEMO_PATH = os.path.join(os.path.dirname(__file__), 'demo_run.py')
spec = importlib.util.spec_from_file_location('dashboard_demo_run', DEMO_PATH)
demo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo_module)
run = demo_module.run

HOST = "127.0.0.1"
PORT = 8000

def render(result=None, error=None):
    cards = ""
    if result:
        for item in result.get("candidates", []):
            symbol = html.escape(str(item.get("ticker", "?")))
            status = html.escape(str(item.get("status", "BLOCK")))
            reasons = html.escape(", ".join(map(str, item.get("reasons", []))) or "Keine angegeben")
            cards += '<article class="candidate"><h3>%s <span>%s</span></h3><p>%s</p></article>' % (symbol, status, reasons)
    notice = '<p class="error">%s</p>' % html.escape(error) if error else ""
    summary = ""
    if result:
        summary = ('<section class="metrics"><div><small>Geprüfte Kandidaten</small><strong>%d</strong></div>'
                   '<div><small>Risk PASS</small><strong>%d</strong></div>'
                   '<div><small>Risk BLOCK</small><strong>%d</strong></div>'
                   '<div><small>Orderausführung</small><strong>Deaktiviert</strong></div></section>') % (
                    len(result.get("candidates", [])), result.get("passed", 0),
                    len(result.get("candidates", [])) - result.get("passed", 0))
    return """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper Trading – Lokales Dashboard</title>
<style>
:root{font-family:system-ui,Arial,sans-serif;color:#eaf0f8;background:#101827}
*{box-sizing:border-box}body{margin:0;padding:32px 16px}
main{max-width:900px;margin:auto}header{display:flex;justify-content:space-between;gap:16px;align-items:center}
h1{font-size:clamp(24px,4vw,36px);margin-bottom:6px}p{line-height:1.55;color:#b8c8da}
.pill{border:1px solid #76d5a1;color:#76d5a1;border-radius:20px;padding:8px 12px;font-weight:700}
.panel,.candidate,.metrics>div{background:#1b293d;border:1px solid #35475d;border-radius:14px;padding:20px}
.panel{margin:24px 0}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px}
small{display:block;color:#b8c8da;margin-bottom:10px}strong{font-size:24px}
button{background:#72a9ff;color:#091426;border:0;border-radius:9px;padding:13px 18px;font-size:16px;font-weight:700;cursor:pointer}
button:hover{background:#a4c7ff}.candidate{margin:12px 0}.candidate h3{display:flex;justify-content:space-between}
.error{color:#ffb0a9}.warning{border-left:4px solid #f4c66e;padding-left:14px}
</style></head><body><main><header><div><h1>Trading-Kontrollzentrum</h1>
<p>Lokaler, simulierter Handelstag</p></div><span class="pill">PAPER ONLY</span></header>
<section class="panel"><h2>Offline-Demo</h2><p>Starte den vorhandenen deterministischen Test mit
synthetischen Daten. Keine Yahoo-Abfragen, keine Broker-Verbindung, keine Orders.</p>
<form method="post" action="/run"><button type="submit">Simulierten Handelstag starten</button></form>
<p class="warning">Dies ist kein aktueller Markt-Scan. Ein Risk PASS ist keine Handelsempfehlung.</p></section>
%s%s%s<section class="panel"><h2>Ergebnisse</h2>%s</section>
<p>Nur auf diesem Computer erreichbar (127.0.0.1). Keine Konten, keine externen Skripte.</p>
</main></body></html>""" % (notice, summary, "" if not result else "<h2>Paper-Kandidaten</h2>", cards or "<p>Noch kein Test gestartet.</p>")

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path != "/":
            return self._send(404, "Not found")
        self._send(200, render())

    def do_POST(self):
        if self.path != "/run":
            return self._send(404, "Not found")
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme != "http" or parsed.hostname not in ("localhost", HOST) or parsed.port != self.server.server_port:
                return self._send(403, "Forbidden")
        if self.headers.get("Content-Length", "0") != "0":
            return self._send(400, "Request body not allowed")
        try:
            result = run()
            self._send(200, render(result=result))
        except (OSError, ValueError, AssertionError, KeyError, TypeError) as exc:
            self._send(500, render(error="Offline-Demo BLOCK: " + str(exc)))

def main():
    parser = argparse.ArgumentParser(description="Local paper-only dashboard")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be 1024..65535")
    server = ThreadingHTTPServer((HOST, args.port), Handler)
    print("Paper-Dashboard: http://127.0.0.1:%d" % args.port, flush=True)
    print("Beenden: Strg+C. Nur Offline-Demo; keine echten Orders.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
