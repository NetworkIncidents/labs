#!/usr/bin/env python3
"""Lab edge proxy: forwards requests to the origin. Loads a feature file pushed by the generator
(PUT :9000/features); it has room for at most 200 features, and a bigger file makes it fail every request."""
import http.server, socketserver, threading, time, urllib.request

ORIGIN = "http://10.0.20.80"
FILE = "/etc/proxy/features.txt"
LOG = "/var/log/proxy.log"
LIMIT = 200
state = {"ok": False}


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def load(text):
    version = next((l.split()[-1] for l in text.splitlines() if l.startswith("# version")), "?")
    features = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    if len(features) > LIMIT:
        state["ok"] = False
        msg = f"PANIC feature file {version}: {len(features)} features exceeds limit {LIMIT}"
    else:
        state["ok"] = True
        msg = f"loaded feature file {version}: {len(features)} features"
    log(msg)
    return msg


class Proxy(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if not state["ok"]:
            body = b"500 Internal Server Error\n"
            self.send_response(500)
        else:
            try:
                with urllib.request.urlopen(ORIGIN + self.path, timeout=3) as r:
                    body = r.read()
                self.send_response(200)
            except Exception:
                body = b"502 Bad Gateway\n"
                self.send_response(502)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class Admin(http.server.BaseHTTPRequestHandler):
    def do_PUT(self):
        text = self.rfile.read(int(self.headers["Content-Length"])).decode()
        with open(FILE, "w") as f:
            f.write(text)
        body = (load(text) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


try:
    load(open(FILE).read())
except FileNotFoundError:
    pass
threading.Thread(target=Server(("", 9000), Admin).serve_forever, daemon=True).start()
Server(("", 80), Proxy).serve_forever()
