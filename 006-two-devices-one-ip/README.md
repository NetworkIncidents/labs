# 006 · Two devices, one IP

A homelab on one switch: a PC, a NAS that serves the family photos, and a new printer. Each device is its own container. Someone set the printer up by hand, and now two devices answer for the same address.

- Video: https://youtu.be/OA4BazNJ3xQ

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
| pc | 10.0.10.20/24 | `docker exec -it clab-dup-ip-pc bash` |
| sw | - | `docker exec -it clab-dup-ip-sw bash` |
| nas | 10.0.10.30/24 | `docker exec -it clab-dup-ip-nas bash` |
| printer | - | `docker exec -it clab-dup-ip-printer bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
pc       curl -s http://10.0.10.30
pc       ping -c 3 10.0.10.30
pc       ip neigh
nas      ip -br link show eth1
pc       arping -b -c 2 -I eth1 10.0.10.30
sw       bridge fdb show br br0 | grep -v permanent
printer  ip -br addr show eth1
printer  ip addr del 10.0.10.30/24 dev eth1
printer  ip addr add 10.0.10.40/24 dev eth1
printer  ip -br addr show eth1
pc       ip neigh flush dev eth1
pc       arping -b -c 2 -I eth1 10.0.10.30
pc       curl -s http://10.0.10.30
pc       curl -s http://10.0.10.40
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 5.3 Incorrect IP address: duplicate IP address
- 5.5 Command-line tools: ip neigh (the arp table)
- 5.5 Device commands: the switch's MAC address table

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
