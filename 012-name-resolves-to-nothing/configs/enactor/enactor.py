#!/usr/bin/env python3
"""Lab DNS enactor: applies the planner's newest plan to db.homelab.test in the DNS service.

Before applying, it checks once that the plan is newer than the one the endpoint has. If the endpoint is busy (a
slow spell, set with `enactorctl slow`), it retries before writing, without checking again. After each apply it
cleans up (at the start of its next round): every plan held by the DNS service that is more than KEEP generations
older than the plan it just applied is deleted. Log: /var/log/enactor.log"""
import json, os, sys, time, urllib.request

NAME = sys.argv[1]                       # enactor-a, enactor-b
PLANNER, DNS = "http://10.0.20.5:8000", "http://10.0.20.53:8053"
ENDPOINT, KEEP = "db.homelab.test", 5
SLOW = "/etc/enactor/slow"               # "retries delay": written by enactorctl slow; used for one plan
LOG = "/var/log/enactor.log"


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"X-Who": NAME, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")
    except OSError:
        return 0, None


last = 0
while True:
    # look for a new plan once a second; with a slow spell pending, often, so this enactor is the one that
    # picks up the next plan (the lab's way to set up the timing of the post-mortem's race)
    time.sleep(0.05 if os.path.exists(SLOW) else 1)
    if last:
        # clean-up after the last apply: plans more than KEEP generations older than it
        code, held = call("GET", f"{DNS}/plans")
        for old in [p for p in held or [] if p < last - KEEP]:
            call("DELETE", f"{DNS}/plans/{old}")
    code, plan = call("GET", f"{PLANNER}/latest")
    if code != 200 or plan["plan"] <= last:
        continue
    code, eps = call("GET", f"{DNS}/endpoints")
    current = (eps or {}).get(ENDPOINT, {}).get("plan") or 0
    if plan["plan"] <= current:                      # the one-time check: newer than what the endpoint has?
        last = plan["plan"]
        continue
    if os.path.exists(SLOW):                         # a slow spell: the endpoint is busy, retry, then write
        retries, delay = (int(x) for x in open(SLOW).read().split())
        os.remove(SLOW)
        log(f"plan {plan['plan']}: newer than plan {current}, applying")
        for i in range(1, retries + 1):
            log(f"plan {plan['plan']}: {ENDPOINT} busy, retry {i} of {retries} in {delay}s")
            time.sleep(delay)
    code, res = call("PUT", f"{DNS}/endpoints/{ENDPOINT}", plan)
    if code != 200:
        log(f"plan {plan['plan']}: not applied: {res['error'] if res else 'no answer'}")
        last = plan["plan"]
        continue
    last = plan["plan"]
