# 004 · Split into VLANs, now nothing talks

A homelab split into two VLANs on one managed switch: the PC on VLAN 10, a media server and a NAS on VLAN 20. A router routes between them over a single trunk cable from the switch. Each device is its own container.

- Video: https://youtu.be/v0yr-NPCG00

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
| pc | 10.0.10.20/24 | `docker exec -it clab-vlan-trunk-pc bash` |
| sw | - | `docker exec -it clab-vlan-trunk-sw bash` |
| server | 10.0.20.80/24 | `docker exec -it clab-vlan-trunk-server bash` |
| router | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-vlan-trunk-router bash` |
| nas | 10.0.20.30/24 | `docker exec -it clab-vlan-trunk-nas bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
pc       curl -m 5 http://10.0.20.80
server   ping -c 3 -W 1 10.0.20.1
server   ip neigh show
server   ping -c 3 10.0.20.30
pc       ping -c 3 10.0.10.1
router   ip -br addr show type vlan
sw       bridge vlan show
sw       bridge vlan add vid 20 dev eth1
sw       bridge vlan show dev eth1
server   ping -c 3 10.0.20.1
pc       curl -m 5 http://10.0.20.80
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 2.2 VLANs and 802.1Q tagging
- 5.3 Switching issues: incorrect VLAN assignment
- 5.5 Command-line tools: ip, ping

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
