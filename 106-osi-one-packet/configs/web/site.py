#!/usr/bin/env python3
"""The web server for explainer 106: one small page, so the whole response fits in one packet."""
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = b"<!doctype html>\n<title>web.homelab.test</title>\n<h1>Hello from web</h1>\n"


class Site(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "homelab-web/1.0"

    def do_GET(self):
        # status line, headers and page in one write: the whole response is one packet in the capture
        head = (f"HTTP/1.1 200 OK\r\nServer: {self.version_string()}\r\nContent-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(PAGE)}\r\nConnection: close\r\n\r\n").encode()
        self.wfile.write(head + PAGE)
        self.close_connection = True

    def log_message(self, *a):
        pass


HTTPServer(("0.0.0.0", 80), Site).serve_forever()
