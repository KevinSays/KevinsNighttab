#!/usr/bin/env python3
"""Serve the pre-built HackTricks book and exit once nobody is using it.

Runs inside the HackTricks container instead of `mdbook serve` (which keeps the
whole book and search index in RAM, ~4.5 GB, to support live reload).

Every HTML page gets a tiny script that opens one long-lived connection to
/__alive (an EventSource). Open tabs hold it open even in the background
(Firefox throttles timers in background tabs, but doesn't close connections),
and it closes when the tab closes. The server stays up while any connection
is open; IDLE seconds after the last one closes (and with no other requests),
it exits. The container is --rm, so it goes away too.

  python3 serve.py [book_dir] [port]      env: HT_IDLE (seconds, default 90; 0 = never exit)

Events go to stdout and to <book_dir>/.serve.log (on the host: ~/hacktricks/book/.serve.log),
which survives the container being removed.
"""
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "/app/book")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
IDLE = int(os.environ.get("HT_IDLE", "90"))
KEEPALIVE = 15  # seconds between comment lines on open streams; spots dead connections

HEARTBEAT = b"<script>new EventSource('/__alive');</script>"

lock = threading.Lock()
streams = 0                 # open /__alive connections = open HackTricks tabs
last = time.monotonic()     # last request, or last stream closing
LOG = os.path.join(ROOT, ".serve.log")


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def touch():
    global last
    with lock:
        last = time.monotonic()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *_):  # quiet; `docker logs hacktricks` stays readable
        pass

    def do_GET(self):
        touch()
        if self.path.split("?")[0] == "/__alive":
            return self.alive_stream()
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

    def alive_stream(self):
        global streams, last
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with lock:
            streams += 1
            n = streams
        log(f"tab connected ({n} open)")
        try:
            # retry: how soon EventSource reconnects if the stream drops
            self.wfile.write(b"retry: 3000\n\n")
            self.wfile.flush()
            while True:
                time.sleep(KEEPALIVE)
                self.wfile.write(b": keepalive\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with lock:
                streams -= 1
                n = streams
                last = time.monotonic()
            log(f"tab disconnected ({n} open)")

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
        with lock:
            idle = streams == 0 and time.monotonic() - last > IDLE
        if idle:
            log(f"no tabs open for {IDLE}s, shutting down")
            server.shutdown()
            return


if __name__ == "__main__":
    try:
        os.remove(LOG)
    except OSError:
        pass
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    if IDLE > 0:  # HT_IDLE=0 keeps it running until `docker stop hacktricks`
        threading.Thread(target=watchdog, args=(srv,), daemon=True).start()
    log(f"serving {ROOT} on :{PORT}, " + (f"exits {IDLE}s after the last tab closes" if IDLE > 0 else "no idle exit"))
    srv.serve_forever()
