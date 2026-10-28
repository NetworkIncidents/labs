#!/usr/bin/env python3
"""Lab DNS service for homelab.test (a stand-in for a managed DNS service): answers DNS on UDP 53, and takes
record updates over HTTP on :8053 from the enactors.

Each endpoint's addresses come from a DNS plan (a numbered set of load balancers). The service keeps a copy of
every plan written to it; deleting a plan removes the addresses of any endpoint still using it, and leaves that
endpoint unable to take updates until an operator repairs it (`dnsctl repair`).

  GET    /endpoints                 every endpoint: plan, addresses, needs_repair
  PUT    /endpoints/<name>          {"plan": n, "ips": [...]} from an enactor (header X-Who)
  GET    /plans                     plan numbers held
  DELETE /plans/<n>                 a clean-up
  POST   /repair/<name>             {"plan": n, "ips": [...]} from the operator
  POST   /guard                     {"on": true}: refuse a plan older than the endpoint's, and refuse to delete a
                                    plan an endpoint is using
"""
import json, socket, struct, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ZONE = "homelab.test"
SOA = ("dns.homelab.test", "admin.homelab.test", 2025102001, 7200, 3600, 1209600, 5)
LOG = "/var/log/r53.log"
lock = threading.Lock()
endpoints = {"db.homelab.test": {"plan": None, "ips": [], "needs_repair": False}}
static = {"dns.homelab.test": ["10.0.20.53"]}
plans = {}
guard = {"on": False}


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


# ---------------------------------------------------------------- DNS
def qname(data, off):
    labels = []
    while data[off]:
        n = data[off]
        labels.append(data[off + 1:off + 1 + n].decode())
        off += n + 1
    return ".".join(labels).lower(), off + 1


def enc(name):
    return b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\0"


def answer(q):
    tid, flags = struct.unpack(">HH", q[:4])
    name, off = qname(q, 12)
    qtype, _ = struct.unpack(">HH", q[off:off + 4])
    question = q[12:off + 4]
    with lock:
        ips = endpoints[name]["ips"] if name in endpoints else static.get(name)
    if ips is None:
        rcode, ans = (3 if name.endswith(ZONE) else 5), []         # NXDOMAIN in the zone, REFUSED outside
    else:
        rcode, ans = 0, (ips if qtype == 1 else [])               # an endpoint with no addresses: NOERROR, none
    hdr = struct.pack(">HHHHHH", tid, 0x8400 | (flags & 0x0100) | rcode, 1, len(ans), 0 if ans or rcode == 5 else 1, 0)
    body = question
    for ip in ans:
        body += b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 5, 4) + socket.inet_aton(ip)
    if not ans and rcode != 5:                                    # the zone's SOA, as a real server sends
        m, r, *nums = SOA
        rdata = enc(m) + enc(r) + struct.pack(">IIIII", *nums)
        body += enc(ZONE) + struct.pack(">HHIH", 6, 1, 5, len(rdata)) + rdata
    return hdr + body


def dns_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 53))
    while True:
        q, addr = s.recvfrom(512)
        try:
            s.sendto(answer(q), addr)
        except Exception:
            pass


# ---------------------------------------------------------------- update API
class Api(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj):
        body = (json.dumps(obj) + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")

    def do_GET(self):
        with lock:
            if self.path == "/endpoints":
                return self.reply(200, endpoints)
            if self.path == "/plans":
                return self.reply(200, sorted(plans))
        self.reply(404, {"error": "not found"})

    def do_PUT(self):
        name = self.path.removeprefix("/endpoints/")
        req, who = self.body(), self.headers.get("X-Who", "?")
        with lock:
            ep = endpoints.get(name)
            if ep is None:
                return self.reply(404, {"error": f"no endpoint {name}"})
            if ep["needs_repair"]:
                return self.reply(409, {"error": f"{name}: its plan {ep['plan']} was deleted, needs repair"})
            if guard["on"] and ep["plan"] is not None and req["plan"] <= ep["plan"]:
                log(f"{who}: plan {req['plan']} refused for {name}: older than its plan {ep['plan']}")
                return self.reply(409, {"error": f"plan {req['plan']} is older than {name}'s plan {ep['plan']}"})
            plans[req["plan"]] = req["ips"]
            ep.update(plan=req["plan"], ips=list(req["ips"]))
            log(f"{who}: {name} -> plan {req['plan']} ({' '.join(req['ips'])})")
        self.reply(200, {"ok": True})

    def do_DELETE(self):
        n = int(self.path.removeprefix("/plans/"))
        with lock:
            using = [name for name, ep in endpoints.items() if ep["plan"] == n]
            if guard["on"] and using:
                log(f"clean-up: plan {n} kept, {' '.join(using)} uses it")
                return self.reply(409, {"error": f"plan {n} is in use"})
            plans.pop(n, None)
            for name in using:
                endpoints[name].update(ips=[], needs_repair=True)
                log(f"clean-up: deleted plan {n}; {name} used it and now has no addresses")
        self.reply(200, {"ok": True})

    def do_POST(self):
        req = self.body()
        with lock:
            if self.path == "/guard":
                guard["on"] = bool(req.get("on"))
                log(f"guard {'on' if guard['on'] else 'off'}: no older plans, no deleting a plan in use")
                return self.reply(200, guard)
            name = self.path.removeprefix("/repair/")
            if name not in endpoints:
                return self.reply(404, {"error": f"no endpoint {name}"})
            plans[req["plan"]] = req["ips"]
            endpoints[name].update(plan=req["plan"], ips=list(req["ips"]), needs_repair=False)
            log(f"operator: {name} repaired -> plan {req['plan']} ({' '.join(req['ips'])})")
        self.reply(200, endpoints[name])


threading.Thread(target=dns_server, daemon=True).start()
log("DNS service up")
ThreadingHTTPServer(("0.0.0.0", 8053), Api).serve_forever()
