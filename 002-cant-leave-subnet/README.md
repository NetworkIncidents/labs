# 002 · Device can't leave its subnet

A NAS on a home network can reach the PC next to it, but nothing on another subnet. The NAS, a PC, a switch, a router and a web server on the other side, each in its own container.

- Video: https://youtu.be/4ae13T5MHI4

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
| nas | 10.0.10.30/24 | `docker exec -it clab-wrong-gateway-nas bash` |
| sw | - | `docker exec -it clab-wrong-gateway-sw bash` |
| pc | 10.0.10.20/24 | `docker exec -it clab-wrong-gateway-pc bash` |
| r1 | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-wrong-gateway-r1 vtysh` (or `bash`) |
| web | 10.0.20.80/24 | `docker exec -it clab-wrong-gateway-web bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
nas      curl -m 5 http://10.0.20.80
nas      ping -c 3 10.0.20.80
nas      ping -c 3 10.0.10.20
pc       ping -c 3 10.0.20.80
nas      ip route
pc       ip route
nas      ip neigh show
nas      ping -c 3 10.0.10.1
nas      ip route replace default via 10.0.10.1 dev eth1
nas      ip route
nas      ping -c 3 10.0.20.80
nas      curl -m 5 http://10.0.20.80
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 5.3 Incorrect default gateway
- 5.3 Route selection: routing table, default routes
- 5.5 Command-line tools: ip, ping

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16, quay.io/frrouting/frr:10.7.1. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
