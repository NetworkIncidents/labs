# 001 · Ping works, websites don't

A homelab client can ping the web server by its address, but loading the site by name fails. The client, a router, a web server and the homelab's DNS server, each in its own container.

- Video: https://youtu.be/Q-ZxXCEbYa4

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
| client | 10.0.10.10/24 | `docker exec -it clab-dns-down-client bash` |
| r1 | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-dns-down-r1 vtysh` (or `bash`) |
| dns | 10.0.20.53/24 | `docker exec -it clab-dns-down-dns bash` |
| coredns | shares dns's network | no shell in this image |
| sw | - | `docker exec -it clab-dns-down-sw bash` |
| web | 10.0.20.80/24 | `docker exec -it clab-dns-down-web bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
client   curl -m 5 http://web.homelab.test
client   ping -c 3 10.0.20.80
client   cat /etc/resolv.conf
client   dig web.homelab.test
client   ping -c 3 10.0.20.53
(host)   docker ps -a --filter name=coredns --format "table {{.Names}}\t{{.Status}}"
(host)   docker start clab-dns-down-coredns
(host)   docker ps -a --filter name=coredns --format "table {{.Names}}\t{{.Status}}"
client   dig +short web.homelab.test
client   curl -m 5 http://web.homelab.test
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

---
Images: coredns/coredns:1.14.7, nicolaka/netshoot:v0.16, quay.io/frrouting/frr:10.7.1. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
