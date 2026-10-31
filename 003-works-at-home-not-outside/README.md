# 003 · Self-hosted app works at home, not from outside

A media server on a home network loads fine at home but not from a phone on mobile data. The phone, a stand-in for the internet, the home router (NAT and one port forward, TCP 8096), a switch, the server and a laptop at home, each in its own container.

- Video: https://youtu.be/VlzxDQT03O8

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
| phone | 198.51.100.20/24 | `docker exec -it clab-port-forward-phone bash` |
| isp | 198.51.100.1/24, 203.0.113.1/24 | `docker exec -it clab-port-forward-isp bash` |
| router | 203.0.113.10/24, 10.0.10.1/24 | `docker exec -it clab-port-forward-router bash` |
| sw | - | `docker exec -it clab-port-forward-sw bash` |
| server | 10.0.10.50/24 | `docker exec -it clab-port-forward-server bash` |
| laptop | 10.0.10.20/24 | `docker exec -it clab-port-forward-laptop bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
phone    curl -m 5 http://203.0.113.10:8096
phone    ping -c 3 203.0.113.10
server   ip -br addr show dev eth1
laptop   curl -m 5 http://10.0.10.51:8096
router   iptables -t nat -L PREROUTING -n -v
router   ip neigh
router   iptables -t nat -R PREROUTING 1 -i eth1 -p tcp --dport 8096 -j DNAT --to-destination 10.0.10.51:8096
router   iptables -t nat -L PREROUTING -n -v
phone    curl -m 5 http://203.0.113.10:8096
router   ip neigh
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 2.1 Address translation: NAT
- 3.4 Dynamic addressing: DHCP reservations
- 5.5 Command-line tools: ip, ping

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
