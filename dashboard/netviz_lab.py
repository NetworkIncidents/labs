#!/usr/bin/env python3
"""netviz_lab - the Network Incidents lab dashboard, for running a lab on your own computer.

    python3 netviz_lab.py ../005-every-edge-fails-at-once/dashboard.json [--port 8090] [--host 127.0.0.1]

(or ./lab.sh dashboard from a lab's folder). Open http://localhost:8090 while the lab runs: the topology with
traffic on each link, interfaces, ping probes, the lab's health checks and an event log, updated every second.
Python 3 standard library only; it reads the lab through `docker exec`, so run it as a user who can use docker.
No password: it listens on localhost only unless you pass --host.

The dashboard used to make the videos shares these parts: dexec, Interfaces, PingProbe, column_layout.
"""
import argparse, json, re, shlex, subprocess, threading, time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRID_W, GRID_H = 82, 19                                  # the dashboard's node grid (netviz's character grid)


def dexec(container, cmd, timeout=3):
    """docker exec with a timeout; stdout, or None on any failure."""
    try:
        r = subprocess.run(["docker", "exec", container, "sh", "-c", cmd],
                           capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


def column_layout(ends):
    """Grid positions {node: [x, y]}: columns by hop count from the first link's first node (as the videos' lab
    map), nodes sharing a column stacked in link order. A chain becomes one row."""
    adj, order = {}, []
    for a, _, b, _ in ends:
        for x, y in ((a, b), (b, a)):
            adj.setdefault(x, []).append(y)
            if x not in order:
                order.append(x)
    if not order:
        return {}
    col, queue = {order[0]: 0}, [order[0]]
    while queue:
        n = queue.pop(0)
        for m in adj[n]:
            if m not in col:
                col[m] = col[n] + 1
                queue.append(m)
    cols = {}
    for n in order:
        cols.setdefault(col.get(n, 0), []).append(n)
    ncols = max(cols) + 1
    step = (GRID_W - 14) / max(1, ncols - 1)
    pos = {}
    for c, ns in cols.items():
        gap = min(5.0, (GRID_H - 3) / max(1, len(ns) - 1)) if len(ns) > 1 else 0
        for i, n in enumerate(ns):
            pos[n] = [round(2 + c * step, 2), round(8 + (i - (len(ns) - 1) / 2) * gap, 2)]
    return pos


# ---------------------------------------------------------------- lab state
class LabSource:
    """Polls a running lab: packets per second on each link (A side), OSPF neighbours where FRR runs."""
    def __init__(self, lab, ends):
        self.lab, self.ends = lab, ends
        self.links = [(a, b) for a, _, b, _ in ends]
        self.side = {(a, b): (a, ai) for a, ai, b, _ in ends}
        self.link_of = {}
        for a, ai, b, bi in ends:
            self.link_of[(a, ai)] = self.link_of[(b, bi)] = (a, b)
        self.nodes = column_layout(ends)
        self.prev = {}

    def poll(self):
        rate, fault, neigh = {}, set(), []
        for link, (node, ifc) in self.side.items():
            out = (dexec(f"clab-{self.lab}-{node}", f"cat /sys/class/net/{ifc}/statistics/tx_packets") or "").split()
            if out:
                tx = int(out[0])
                rate[link] = min(1.0, (tx - self.prev.get(link, tx)) / 20)
                self.prev[link] = tx
            else:
                rate[link] = 0.0
        for n in self.nodes:
            try:
                j = json.loads(dexec(f"clab-{self.lab}-{n}", "vtysh -c 'show ip ospf neighbor json' 2>/dev/null")
                               or "{}")
            except ValueError:
                continue
            for rid, entries in j.get("neighbors", {}).items():
                for e in entries if isinstance(entries, list) else [entries]:
                    st = e.get("nbrState", e.get("converged", "?")).split("/")[0]
                    neigh.append((n, rid, st, e.get("ifaceName", "").split(":")[0]))
        for n, rid, st, ifc in neigh:                   # only the link a stuck adjacency runs over goes red
            if st != "Full":
                link = self.link_of.get((n, ifc))
                fault |= {link} if link else {l for l in self.links if n in l}
        return dict(rate=rate, fault=fault, neigh=[(n, rid, st) for n, rid, st, _ in neigh], broken=bool(fault))


class Interfaces:
    """Address / MTU / state of every lab-link interface, keyed (node, ifname)."""
    def __init__(self, lab, ends):
        self.lab, self.ends = lab, ends
        self.wanted = {}
        for a, ai, b, bi in ends:
            self.wanted.setdefault(a, set()).add(ai)
            self.wanted.setdefault(b, set()).add(bi)
        self.pool = ThreadPoolExecutor(max_workers=8)

    def one(self, node):
        out = dexec(f"clab-{self.lab}-{node}", "ip -j addr show")
        if not out:
            return {}
        try:
            entries = json.loads(out)
        except ValueError:
            return {}
        res = {}
        for e in entries:
            if e.get("ifname") in self.wanted[node]:
                v4 = [f"{a['local']}/{a['prefixlen']}" for a in e.get("addr_info", []) if a.get("family") == "inet"]
                res[(node, e["ifname"])] = {"addr": v4[0] if v4 else "-", "mtu": e.get("mtu"),
                                            "state": e.get("operstate", "?").lower()}
        return res

    def poll(self, broken):
        res = {}
        for part in self.pool.map(self.one, self.wanted):
            res.update(part)
        return res


class PingProbe(threading.Thread):
    """Continuous ping from a lab node; keeps the last 60 results and raw lines."""
    MARK = "6e76"                                       # payload pattern, so stale probes can be found and killed

    def __init__(self, lab, src, dst, on_event, demo_broken=None):
        super().__init__(daemon=True)
        self.lab, self.src, self.dst, self.on_event, self.demo_broken = lab, src, dst, on_event, demo_broken
        self.lock, self.stop = threading.Lock(), threading.Event()
        self.results, self.lines = deque(maxlen=60), deque(maxlen=5)
        self.last_rtt, self.down_since, self.ever_ok = None, None, False

    def feed(self, line):
        line = line.rstrip()
        if not line:
            return
        now = time.time()
        stamp = time.strftime("%H:%M:%S", time.localtime(now)) + f".{int(now % 1 * 1000):03d}"
        ok = "bytes from" in line
        lost = "no answer yet" in line or "Unreachable" in line or "Time to live exceeded" in line
        with self.lock:
            self.lines.append(f"{stamp}  {line}")
            if ok:
                m = re.search(r"time=([\d.]+)", line)
                self.last_rtt = float(m.group(1)) if m else None
                self.results.append(1)
                if self.down_since is not None:
                    self.on_event(self.src, f"ping {self.dst} back after", f"{now - self.down_since:.1f} s", False)
                    self.down_since = None
                self.ever_ok = True
            elif lost:
                self.results.append(0)
                if self.down_since is None and self.ever_ok:
                    self.down_since = now
                    self.on_event(self.src, f"ping {self.dst}", "no reply", True)

    def run(self):
        if self.demo_broken:
            seq = 0
            while not self.stop.wait(0.5):              # simulated probe interval
                seq += 1
                if self.demo_broken():
                    self.feed(f"From 10.0.1.1 icmp_seq={seq} Destination Net Unreachable")
                else:
                    self.feed(f"64 bytes from {self.dst}: icmp_seq={seq} ttl=62 time=0.0{4 + seq % 3} ms")
            return
        container = f"clab-{self.lab}-{self.src}"
        cmd = ["ping", "-O", "-i", "0.5", "-W", "1", "-p", self.MARK, self.dst]
        self.proc = None
        while not self.stop.is_set():
            # a docker exec client dying leaves its ping running in the container; clear old probes first
            dexec(container, f"pkill -f 'ping -O -i 0.5 -W 1 -p {self.MARK} {self.dst}'")
            try:
                p = self.proc = subprocess.Popen(["docker", "exec", container, *cmd], stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True,
                                                 bufsize=1)
                for line in p.stdout:
                    self.feed(line)
                p.wait()
            except OSError as e:
                self.feed(f"probe error: {e}")
            self.stop.wait(2)                           # container gone or restarting: retry

    def halt(self):
        """Stop probing and clear its ping in the container."""
        self.stop.set()
        if getattr(self, "proc", None):
            self.proc.kill()
        if not self.demo_broken:
            dexec(f"clab-{self.lab}-{self.src}", f"pkill -f 'ping -O -i 0.5 -W 1 -p {self.MARK} {self.dst}'")

    def snapshot(self):
        with self.lock:
            res = list(self.results)
            return {"src": self.src, "dst": self.dst, "results": res,
                    "ok": bool(res) and res[-1] == 1, "rtt": self.last_rtt,
                    "lost": res.count(0), "lines": list(self.lines),
                    "downFor": round(time.time() - self.down_since, 1) if self.down_since else None}


# ---------------------------------------------------------------- the public dashboard
class Feed:
    """Latest snapshot plus a sequence number; HTTP clients wait for the next one."""
    def __init__(self):
        self.cond, self.seq, self.snap = threading.Condition(), 0, None

    def publish(self, snap):
        with self.cond:
            self.snap, self.seq = snap, self.seq + 1
            self.cond.notify_all()

    def next_after(self, seq, timeout=15):
        with self.cond:
            self.cond.wait_for(lambda: self.seq > seq, timeout=timeout)
            return self.seq, self.snap


def lab_running(lab):
    try:
        return bool(subprocess.run(["docker", "ps", "-q", "--filter", f"label=containerlab={lab}"],
                                   capture_output=True, text=True, timeout=10).stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        return False


class Health(threading.Thread):
    """The lab's health checks (what ./lab.sh check runs), every 2 s, as the 'lab health' panel's text."""
    def __init__(self, lab, checks, feed, on_change):
        super().__init__(daemon=True)
        self.lab, self.checks, self.feed, self.on_change = lab, checks, feed, on_change
        self.ok, self.prev = None, None

    def one(self, c):
        try:
            r = subprocess.run(["docker", "exec", f"clab-{self.lab}-{c['node']}", *shlex.split(c["cmd"])],
                               capture_output=True, text=True, timeout=10)
            out = r.stdout + r.stderr
        except (subprocess.TimeoutExpired, OSError):
            out = ""
        pats = c["expect"] if isinstance(c["expect"], list) else [c["expect"]]
        return all(re.search(p, out, re.M) for p in pats)

    def run(self):
        green, red, dim, amber, reset = "\x1b[38;5;114m", "\x1b[38;5;203m", "\x1b[38;5;244m", "\x1b[38;5;215m", "\x1b[0m"
        while True:
            t0 = time.monotonic()
            up = lab_running(self.lab)
            results = [(c, self.one(c)) for c in self.checks] if up else []
            self.ok = None if not up else all(r for _, r in results)
            lines = [f"{amber}The checks ./lab.sh check runs, every 2 seconds:{reset}", ""]
            if not up:
                lines.append(f"{dim}no lab running: ./lab.sh up{reset}")
            for c, r in results:
                lines.append(f"{green}  ✓ pass{reset}  " if r else f"{red}  ✗ FAIL{reset}  ")
                lines[-1] += f"{c['node']}: {c['cmd']}"
            lines += ["", f"{green}All checks pass: the lab works.{reset}" if self.ok
                      else f"{red}Broken. Find out why; ./lab.sh hint if you're stuck.{reset}" if up else ""]
            self.feed.publish({"live": True, "heading": "lab health", "text": "\n".join(lines),
                               "cursor": [0, 0], "showCursor": False})
            if self.ok != self.prev and self.ok is not None:
                self.on_change(self.ok)
            self.prev = self.ok
            time.sleep(max(0.0, 2 - (time.monotonic() - t0)))   # check interval


class Dashboard(threading.Thread):
    """Polls the lab once a second and publishes the dashboard's snapshot."""
    def __init__(self, cfg):
        super().__init__(daemon=True)
        self.cfg, self.lab = cfg, cfg["lab"]
        ends = [tuple(e) for e in cfg["ends"]]
        self.src, self.ifaces = LabSource(self.lab, ends), Interfaces(self.lab, ends)
        self.feed, self.term = Feed(), Feed()
        self.log = deque(maxlen=12)
        self.pings = [PingProbe(self.lab, *str(p).split(":", 1), self.add_event) for p in cfg.get("pings", [])]
        self.health = Health(self.lab, cfg.get("checks", []), self.term,
                             lambda ok: self.add_event("lab", "health checks", "pass" if ok else "FAIL", not ok))

    def add_event(self, node, msg, state, bad):
        self.log.append({"ts": time.strftime("%H:%M:%S"), "node": node, "msg": msg, "state": state, "bad": bad})

    def snapshot(self):
        state, ifs = self.src.poll(), self.ifaces.poll(False)
        links, rows, seen = [], [], set()
        for a, ai, b, bi in self.ifaces.ends:
            ia, ib = ifs.get((a, ai)), ifs.get((b, bi))
            mismatch = bool(ia and ib and ia["mtu"] != ib["mtu"])
            links.append({"a": a, "b": b, "aIf": ai, "bIf": bi, "aMtu": ia and ia["mtu"], "bMtu": ib and ib["mtu"],
                          "mismatch": mismatch, "fault": mismatch or (a, b) in state["fault"],
                          "rate": state["rate"].get((a, b), 0)})
            for n, i, info in ((a, ai, ia), (b, bi, ib)):
                if (n, i) not in seen:
                    seen.add((n, i))
                    rows.append({"node": n, "iface": i, **(info or {"addr": "-", "mtu": None, "state": "?"}),
                                 "mismatch": mismatch})
        ok = self.health.ok
        status = "nolab" if ok is None and not ifs else "nodata" if ok is None else "healthy" if ok else "fault"
        return {"title": "NETWORK INCIDENTS", "lab": self.lab,
                "caption": "no lab running: ./lab.sh up" if status == "nolab" else self.cfg.get("title", ""),
                "status": status, "broken": status == "fault",
                "grid": [GRID_W, GRID_H], "nodes": self.src.nodes, "links": links, "ifaces": rows,
                "neigh": [list(x) for x in state["neigh"]], "pings": [p.snapshot() for p in self.pings],
                "log": list(self.log)}

    def run(self):
        self.health.start()
        for p in self.pings:
            p.start()
        self.add_event("lab", self.lab, "dashboard started", None)
        while True:
            t0 = time.monotonic()
            try:
                snap = self.snapshot()
            except Exception as e:                      # keep serving; show the error on the page
                snap = {**(self.feed.snap or {}), "error": f"{type(e).__name__}: {e}"}
            if snap.get("grid"):
                self.feed.publish(snap)
            time.sleep(max(0.0, 1 - (time.monotonic() - t0)))   # poll interval


class Handler(BaseHTTPRequestHandler):
    server_version = "netviz-lab"

    def log_message(self, *a):
        pass

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            body = (HERE / "dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        if path in ("/events", "/term"):
            return self.stream(self.server.dash.feed if path == "/events" else self.server.dash.term)
        self.send_error(404)

    def stream(self, feed):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        seq = 0
        try:
            while True:
                seq, snap = feed.next_after(seq)
                self.wfile.write(b": waiting\n\n" if snap is None else f"data: {json.dumps(snap)}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    ap = argparse.ArgumentParser(description="Network Incidents lab dashboard")
    ap.add_argument("config", type=Path, help="a lab's dashboard.json")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--host", default="127.0.0.1", help="listen address (default: this computer only)")
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text())
    dash = Dashboard(cfg)
    dash.start()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.daemon_threads, srv.dash = True, dash
    print(f"Dashboard for {cfg['lab']}: http://localhost:{a.port}  (Ctrl-C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        for p in dash.pings:
            p.halt()


if __name__ == "__main__":
    main()
