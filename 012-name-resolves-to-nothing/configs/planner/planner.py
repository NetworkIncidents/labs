#!/usr/bin/env python3
"""Lab DNS planner: every second, a new numbered plan for db.homelab.test (which load balancers it should point
to), served over HTTP on :8000. GET /latest, GET /plans/<n>."""
import json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LBS = ["10.0.20.11", "10.0.20.12"]
state = {"n": 100, "plans": {}}
lock = threading.Lock()


def plan_loop():
    while True:
        with lock:
            state["n"] += 1
            state["plans"][state["n"]] = {"plan": state["n"], "ips": LBS}
            for old in [k for k in state["plans"] if k < state["n"] - 50]:
                del state["plans"][old]                 # the planner only keeps recent plans to hand out
        time.sleep(1)                                   # a new plan every second (the lab's pace)


class Api(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        with lock:
            p = state["plans"].get(state["n"]) if self.path == "/latest" else \
                state["plans"].get(int(self.path.rsplit("/", 1)[1])) if self.path.startswith("/plans/") else None
        body = (json.dumps(p) + "\n").encode()
        self.send_response(200 if p else 404)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


threading.Thread(target=plan_loop, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", 8000), Api).serve_forever()
