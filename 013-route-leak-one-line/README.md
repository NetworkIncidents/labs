# 013 · One line out, routes leak

Our network (edge and core, AS64500) sends its provider, transit (AS64502), only what the export policy TO-TRANSIT allows. peer (AS64501) is a network we exchange routes with; user is one of transit's customers. Every router runs FRR.

> Incident replay: a lab model of the failure pattern in Cloudflare's post-mortem of its 22 January 2026 route leak (https://blog.cloudflare.com/route-leak-incident-january-22-2026/), not Cloudflare's network.

- Video: https://youtu.be/31cBmA9SZQI
- Write-up: https://networkincidents.ca/incidents/cloudflare-2026-01-22/

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
| user | 203.0.113.10/24 | `docker exec -it clab-route-leak-user bash` |
| transit | 203.0.113.1/24, 10.0.1.1/30, 10.0.4.1/30 | `docker exec -it clab-route-leak-transit vtysh` (or `bash`) |
| edge | 192.0.2.1/25, 10.0.1.2/30, 10.0.2.1/30 | `docker exec -it clab-route-leak-edge vtysh` (or `bash`) |
| edge-fw | shares edge's network | `docker exec -it clab-route-leak-edge-fw bash` |
| core | 192.0.2.129/25, 10.0.2.2/30, 10.0.3.1/30 | `docker exec -it clab-route-leak-core vtysh` (or `bash`) |
| peer | 198.51.100.10/24, 10.0.4.2/30, 10.0.3.2/30 | `docker exec -it clab-route-leak-peer vtysh` (or `bash`) |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
user     ping -c 3 -W 1 198.51.100.10
user     traceroute -n 198.51.100.10
transit  show ip bgp 198.51.100.0/24
edge     show ip bgp neighbors 10.0.1.1 advertised-routes
edge     cat /var/log/policy-push.log
edge     vtysh -c 'show running-config' | grep -A2 '^route-map TO-TRANSIT'
edge     show ip bgp 198.51.100.0/24
edge     conf t
edge     route-map TO-TRANSIT permit 20
edge     match ip address prefix-list SITE-B
edge     end
transit  show ip bgp 198.51.100.0/24
user     ping -c 3 -W 1 198.51.100.10
user     traceroute -n 198.51.100.10
edge     conf t
edge     bgp community-list standard FROM-PEER permit 64500:3
edge     route-map TO-TRANSIT deny 5
edge     match community FROM-PEER
edge     end
edge     conf t
edge     route-map TO-TRANSIT permit 20
edge     no match ip address prefix-list SITE-B
edge     end
edge     show ip bgp neighbors 10.0.1.1 advertised-routes
user     ping -c 3 -W 1 198.51.100.10
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 2.1 Dynamic routing: BGP
- 2.1 Route selection
- 3.1 Change management and configuration management
- 5.5 Command-line tools: ping, traceroute

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16, quay.io/frrouting/frr:10.7.1. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
