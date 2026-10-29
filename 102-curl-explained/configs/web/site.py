#!/usr/bin/env python3
"""The homelab's web server for explainer 102: a home page, a page that moved (301 to /new), and nothing else (404)."""
from http.server import BaseHTTPRequestHandler, HTTPServer

HOME = b"<!doctype html>\n<title>web.homelab.test</title>\n<h1>It works</h1>\n"
NEW = b"<!doctype html>\n<title>new page</title>\n<h1>You followed the redirect</h1>\n"
MISSING = b"<!doctype html>\n<title>not found</title>\n<h1>404: no such page</h1>\n"


class Site(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def version_string(self):
        return "homelab-web/1.0"

    def send(self, code, body, extra=()):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self.send(200, HOME)
        if self.path == "/old":
            return self.send(301, b"", [("Location", "/new")])
        if self.path == "/new":
            return self.send(200, NEW)
        self.send(404, MISSING)

    do_HEAD = do_GET

    def log_message(self, *a):
        pass


HTTPServer(("0.0.0.0", 80), Site).serve_forever()
