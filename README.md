# Network Incidents labs

The labs from the Network Incidents videos, to run on your own computer: break them, find the fault, fix it.
Each folder is one episode's lab, built with containerlab: `cd` into it and run `./lab.sh up`.

Install Docker and containerlab first: https://networkincidents.ca/run-the-labs/

| Lab | Video |
|---|---|
| [001 · Ping works, websites don't](001-ping-works-websites-dont/) | https://youtu.be/Q-ZxXCEbYa4 |
| [002 · Device can't leave its subnet](002-cant-leave-subnet/) | https://youtu.be/4ae13T5MHI4 |
| [003 · Self-hosted app works at home, not from outside](003-works-at-home-not-outside/) | https://youtu.be/VlzxDQT03O8 |
| [004 · Split into VLANs, now nothing talks](004-vlans-nothing-talks/) | https://youtu.be/v0yr-NPCG00 |
| [005 · Every edge fails at once](005-every-edge-fails-at-once/) | https://youtu.be/CWrIl4Byc5k |
| [012 · A name that resolves to nothing](012-name-resolves-to-nothing/) | https://youtu.be/9TRUjkbSCUc |
| [013 · One line out, routes leak](013-route-leak-one-line/) | https://youtu.be/31cBmA9SZQI |
| [101 · dig, explained](101-dig-explained/) | https://youtu.be/OUhudvNqb-o |
| [102 · curl, explained](102-curl-explained/) | https://youtu.be/XxfnwzI9b-8 |
| [103 · ping, explained](103-ping-explained/) | https://youtu.be/-HAAZJld9kg |

Every lab is tested weekly by GitHub Actions (up, break, fix, down; explainer labs: up, down). Labs numbered
1xx are explainer playgrounds: nothing is broken, they are for trying the commands from the video. MIT licence:
see LICENSE.
