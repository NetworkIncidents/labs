# 014 · Every clock agrees on 2006

One time network. nmi is the national time reference; syd2 and mel2 take their time from it (stratum 2); syd3, mel3 and perth3 serve the next level (stratum 3), and mme, a core node, takes its time from those three. mel3 also has its own reference, a GPS card. Every node runs chrony with -x, so it never changes your computer's clock: a wrong date only lives in chrony's own estimate.

> Incident replay: a lab model of the failure pattern in the external review of Telstra's 8 July 2026 outage (https://www.telstra.com.au/content/dam/tcom/dynamic-media-projects/luke-campbell/TAP-Findings-for-Telstra-Outage.pdf), not Telstra's network.

- Video: https://youtu.be/RxSKxE_NDV4
- Write-up: https://networkincidents.ca/incidents/telstra-2026-07-08/

## Run it

You need Docker and containerlab on Linux (or WSL2, or a Linux VM): see https://networkincidents.ca/run-the-labs/ for the install
steps. Then, from this folder:

```bash
./lab.sh up       # build the lab and wait until it works
./lab.sh break    # break it the way the episode does
./lab.sh hint     # one hint at a time, if you want one
./lab.sh check    # healthy or broken?
./lab.sh fix      # the fix, if you give up (scripts/fix.sh)
./lab.sh down     # remove the lab
```

If containerlab needs root on your machine, run them with `sudo`. The first `up` downloads the device images.

### Optional: the live dashboard

The dashboard from the videos, in your browser: the lab's map with traffic on each link, interfaces, ping
probes, the health checks turning red and green, and an event log. In a second terminal, from this folder:

```bash
./lab.sh dashboard    # then open http://localhost:8090 (Ctrl-C to stop)
```

It needs Python 3 (already on Ubuntu and WSL) and nothing else. It only listens on your own computer; add
`--port 8091` if 8090 is taken.

## The lab

| Node | Address | Shell |
|---|---|---|
| mme | 10.0.40.50/24 | no shell in this image |
| syd3 | 10.0.40.31/24 | no shell in this image |
| mel3 | 10.0.40.32/24 | no shell in this image |
| perth3 | 10.0.40.33/24 | no shell in this image |
| syd2 | 10.0.40.21/24 | no shell in this image |
| mel2 | 10.0.40.22/24 | no shell in this image |
| nmi | 10.0.40.10/24 | no shell in this image |
| sw | - | `docker exec -it clab-clocks-agree-on-2006-sw bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
mme      chronyc tracking
mme      chronyc sources
syd3     chronyc sources
mel3     chronyc tracking
mel3     chronyc add server nmi iburst minpoll 0 maxpoll 1
mme      chronyc tracking
mme      chronyc sources
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 3.4 Time protocols: NTP
- 3.1 Change management and configuration management

Not affiliated with or endorsed by CompTIA.

---
Images: dockurr/chrony:4.9, nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
