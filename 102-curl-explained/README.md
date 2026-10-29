# 102 · curl, explained

A small home network to try curl on: a PC, a switch, the homelab's DNS server and a web server with a home page, a page that moved (/old to /new) and nothing else (404). Open a shell on the PC and make requests.

- Video: https://youtu.be/XxfnwzI9b-8

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
| pc | 10.0.10.20/24 | `docker exec -it clab-curl-basics-pc bash` |
| sw | - | `docker exec -it clab-curl-basics-sw bash` |
| dns | 10.0.10.53/24 | `docker exec -it clab-curl-basics-dns bash` |
| coredns | shares dns's network | no shell in this image |
| web | 10.0.10.80/24 | `docker exec -it clab-curl-basics-web bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

## Try these

The commands from the video, in order (the first column is the device to run them on):

```
pc       curl http://web.homelab.test
pc       curl -I http://web.homelab.test
pc       curl -v http://web.homelab.test
pc       curl -I http://web.homelab.test/missing
pc       curl -I http://web.homelab.test/old
pc       curl -L http://web.homelab.test/old
pc       curl http://nope.homelab.test
pc       curl http://10.0.10.53
```

---
Images: coredns/coredns:1.14.7, nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
