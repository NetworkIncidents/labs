# 106 · The OSI model in one real packet

A PC fetches a web page from a server on another network, through one router. Every interface has a readable MAC address (02:00:00:00:<network>:<host>). Capture the request on the PC with tcpdump and read its layers with tshark; the web server has been capturing since it started (/arrived.pcap), so compare the same packet on both sides of the router: the Ethernet header and TTL change, the IP addresses and ports don't.

- Video: https://youtu.be/5Eoc3mwtf6Y

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
| pc | 10.0.10.20/24 | `docker exec -it clab-osi-one-packet-pc bash` |
| r1 | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-osi-one-packet-r1 vtysh` (or `bash`) |
| web | 10.0.20.80/24 | `docker exec -it clab-osi-one-packet-web bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

## Try these

The commands from the video, in order (the first column is the device to run them on):

```
pc       timeout 5 tcpdump -c 10 -i eth1 -w pc.pcap tcp port 80 & sleep 1; curl -s http://10.0.20.80/; wait
pc       tshark -r pc.pcap -Y http.request -O http
pc       ip route
pc       ip neigh
r1       ip route
r1       ip neigh
pc       tshark -r pc.pcap -Y http.request -T fields -e eth.src -e eth.dst -e ip.src -e ip.dst -e ip.ttl
web      tshark -r /arrived.pcap -Y http.request -T fields -e eth.src -e eth.dst -e ip.src -e ip.dst -e ip.ttl
web      ip -br link show eth1
web      ip -br addr show eth1
web      ss -ltnp
```

## CompTIA Network+

N10-009 exam objectives this lab practises:

- 1.1 OSI reference model: layers 1, 2, 3, 4 and 7
- 1.4 Protocols and ports: HTTP (80)
- 5.5 Command-line tools: tcpdump, ip
- 5.5 Protocol analyzer

Not affiliated with or endorsed by CompTIA.

---
Images: nicolaka/netshoot:v0.16, quay.io/frrouting/frr:10.7.1. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
