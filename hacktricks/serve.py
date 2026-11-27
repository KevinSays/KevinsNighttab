#!/usr/bin/env python3
"""Serve the pre-built HackTricks book and exit once nobody is using it.

Runs inside the HackTricks container instead of `mdbook serve` (which keeps the
whole book and search index in RAM, ~4.5 GB, to support live reload). Every HTML
page gets a small script that pings /__alive while the tab is open, so reading
a long page keeps it alive. After IDLE seconds with no request at all (every
HackTricks tab closed), the server exits; the container is --rm, so it goes away.

  python3 serve.py [book_dir] [port]      env: HT_IDLE (seconds, default 90)
"""
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "/app/book")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
IDLE = int(os.environ.get("HT_IDLE", "90"))
PING = max(5, IDLE // 4) if IDLE > 0 else 60  # heartbeat interval, well inside the idle window

HEARTBEAT = (
    "<script>(()=>{const p=()=>fetch('/__alive',{cache:'no-store'}).catch(()=>{});"
    f"setInterval(p,{PING * 1000});document.addEventListener('visibilitychange',p);}})();</script>"
).encode()

last = time.monotonic()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *_):  # quiet; `docker logs hacktricks` stays readable
        pass

    def do_GET(self):
        global last
        last = time.monotonic()
        if self.path.split("?")[0] == "/__alive":
            self.send_response(204)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            if not self.path.split("?")[0].endswith("/"):
                return super().do_GET()  # let the base class redirect to "dir/"
            path = os.path.join(path, "index.html")
        if not path.endswith(".html"):
            return super().do_GET()
        if not os.path.isfile(path):
            self.send_html(os.path.join(ROOT, "404.html"), 404)
        else:
            self.send_html(path, 200)

    def send_html(self, path, code):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        i = body.rfind(b"</body>")
        body = body[:i] + HEARTBEAT + body[i:] if i >= 0 else body + HEARTBEAT
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


def watchdog(server):
    while True:
        time.sleep(5)
        if time.monotonic() - last > IDLE:
            print(f"idle for {IDLE}s, shutting down", flush=True)
            server.shutdown()
            return


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    if IDLE > 0:  # HT_IDLE=0 keeps it running until `docker stop hacktricks`
        threading.Thread(target=watchdog, args=(srv,), daemon=True).start()
    print(f"Serving {ROOT} on :{PORT}, " + (f"exits after {IDLE}s unused" if IDLE > 0 else "no idle exit"), flush=True)
    srv.serve_forever()
