# 005 · Every edge fails at once

Three edge proxies sit in front of one origin web server. Every 20 seconds a generator builds a feature file from one of two database replicas and pushes it to all three edges, which have room for 200 features.

> Incident replay: a lab model of the failure pattern in Cloudflare's post-mortem of 18 November 2025 (https://blog.cloudflare.com/18-november-2025-outage/), not Cloudflare's systems.

- Video: https://youtu.be/CWrIl4Byc5k
- Write-up: https://networkincidents.ca/

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

## The lab

| Node | Address | Shell |
|---|---|---|
| client | 10.0.10.10/24 | `docker exec -it clab-feature-limit-client bash` |
| r1 | 10.0.10.1/24, 10.0.20.1/24 | `docker exec -it clab-feature-limit-r1 bash` |
| sw | - | `docker exec -it clab-feature-limit-sw bash` |
| edge1 | 10.0.20.11/24 | `docker exec -it clab-feature-limit-edge1 bash` |
| edge2 | 10.0.20.12/24 | `docker exec -it clab-feature-limit-edge2 bash` |
| edge3 | 10.0.20.13/24 | `docker exec -it clab-feature-limit-edge3 bash` |
| origin | 10.0.20.80/24 | `docker exec -it clab-feature-limit-origin bash` |
| gen | 10.0.20.5/24 | `docker exec -it clab-feature-limit-gen bash` |

`topology.clab.yml` is the whole lab: the devices, their cables and their settings. `configs/` holds the files
it loads.

<details>
<summary>Spoiler: the commands used in the episode, in order</summary>

```
client   for e in 11 12 13; do curl -s -o /dev/null -w "10.0.20.$e %{http_code}\n" http://10.0.20.$e; done
edge1    curl -s http://10.0.20.80
edge1    cat /var/log/proxy.log
edge1    grep -vc '^#' /etc/proxy/features.txt
edge1    grep -v '^#' /etc/proxy/features.txt | sort | uniq -d | wc -l
gen      cat /var/log/featuregen.log
gen      cat /opt/featuregen/query.sql
gen      dbq replica-a "SELECT database, count(*) FROM system_columns GROUP BY database"
gen      dbq replica-a "SELECT * FROM grants"
gen      pkill -f 'featuregen run'
gen      featuregen push /var/lib/featuregen/v5.txt
client   for e in 11 12 13; do curl -s -o /dev/null -w "10.0.20.$e %{http_code}\n" http://10.0.20.$e; done
gen      featuregen start --max-features 200 --canary edge1
gen      tail -n 1 /var/log/featuregen.log
gen      sed -i "s/^WHERE /WHERE database = 'default' AND /" /opt/featuregen/query.sql
gen      cat /opt/featuregen/query.sql
gen      tail -n 2 /var/log/featuregen.log
```

`scripts/break.sh` is what broke it; `scripts/fix.sh` is the fix.
</details>

---
Images: nicolaka/netshoot:v0.16. Tested on Ubuntu with Docker and containerlab
by this repo's GitHub Actions workflow.
