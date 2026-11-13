# 104 · ip addr and ip route, explained

Two small home networks joined by a router: a PC and a NAS on one side, a web server and a printer on the other. Open a shell on the PC and read its address and its routing table, ask ip route get which way an address would go, then look at the router, which has an address on each network.

- Video: https://youtu.be/ODhnj1IHtto

## Run it

You need Docker and containerlab on Linux (or WSL2, or a Linux VM): see https://networkincidents.ca/run-the-labs/ for the install
steps. Then, from this folder:

```bash
./lab.sh up       # build the lab and wait until it's ready
./lab.sh down     # remove the lab when you're done
```

Nothing is broken in this one: it's a small network to try the commands from the video on.

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
| pc | 10.0.10.20/24 | `docker exec -it clab-iproute-basics-pc bash` |
| sw | - | `docker exec -it clab-iproute-basics-sw bash` |
| nas | 10.0.10.30/24 | `docker exec -it clab-iproute-basics-nas bash` |
| router | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-iproute-basics-router bash` |
| sw2 | - | `docker exec -it clab-iproute-basics-sw2 bash` |
| web | 10.0.20.80/24 | `docker exec -it clab-iproute-basics-web bash` |
| printer | 10.0.20.40/24 | `docker exec -it clab-iproute-basics-printer bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

## Try these

The commands from the video, in order (the first column is the device to run them on):

```
pc       ip -br addr show up
pc       ip addr show eth1
pc       ip route
pc       ip route get 10.0.20.80
pc       ip route get 10.0.10.30
router   ip -br addr show up
router   ip route
```

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 5.3 Route selection: routing table, default routes
- 5.5 Command-line tools: ip

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
