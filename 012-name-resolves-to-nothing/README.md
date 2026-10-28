# 012 · A name that resolves to nothing

A planner makes a new DNS plan for db.homelab.test every second; two enactors apply the newest plan to a small DNS service, each checking once beforehand that it's newer, then clean up old plans. Two load balancers sit behind the name.

> Incident replay: a lab model of the failure pattern in AWS's post-event summary of the 19-20 October 2025 us-east-1 disruption (https://aws.amazon.com/message/101925/), not AWS's systems.

- Video: https://youtu.be/9TRUjkbSCUc
- Write-up: https://networkincidents.ca/incidents/aws-2025-10-20/

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
| client | 10.0.20.10/24 | `docker exec -it clab-dns-race-client bash` |
| sw | - | `docker exec -it clab-dns-race-sw bash` |
| dns | 10.0.20.53/24 | `docker exec -it clab-dns-race-dns bash` |
| lb1 | 10.0.20.11/24 | `docker exec -it clab-dns-race-lb1 bash` |
| lb2 | 10.0.20.12/24 | `docker exec -it clab-dns-race-lb2 bash` |
| planner | 10.0.20.5/24 | `docker exec -it clab-dns-race-planner bash` |
| enactor-a | 10.0.20.6/24 | `docker exec -it clab-dns-race-enactor-a bash` |
| enactor-b | 10.0.20.7/24 | `docker exec -it clab-dns-race-enactor-b bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
client   curl -sS -m 3 http://db.homelab.test
client   dig db.homelab.test
client   curl -s http://10.0.20.11
client   curl -s http://10.0.20.12
dns      dnsctl show
dns      tail -n 3 /var/log/r53.log
enactor-a head -n 4 /var/log/enactor.log
enactor-b tail -n 3 /var/log/enactor.log
dns      dnsctl repair db.homelab.test
dns      dnsctl show
client   dig +short db.homelab.test
client   curl -s http://db.homelab.test
dns      dnsctl guard on
enactor-a enactorctl slow 3 4
dns      grep refused /var/log/r53.log
dns      dnsctl show
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
