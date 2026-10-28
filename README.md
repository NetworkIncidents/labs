# Network Incidents labs

The labs from the Network Incidents videos, to run on your own computer: break them, find the fault, fix it.
Each folder is one episode's lab, built with containerlab: `cd` into it and run `./lab.sh up`.

Install Docker and containerlab first: https://networkincidents.ca/run-the-labs/

| Lab | Video |
|---|---|
| [001 · Ping works, websites don't](001-ping-works-websites-dont/) | https://youtu.be/Q-ZxXCEbYa4 |
| [002 · Device can't leave its subnet](002-cant-leave-subnet/) | https://youtu.be/4ae13T5MHI4 |
| [005 · Every edge fails at once](005-every-edge-fails-at-once/) | https://youtu.be/CWrIl4Byc5k |
| [101 · dig, explained](101-dig-explained/) | https://youtu.be/OUhudvNqb-o |

Every lab is tested weekly by GitHub Actions (up, break, fix, down; explainer labs: up, down). Labs numbered
1xx are explainer playgrounds: nothing is broken, they are for trying the commands from the video. MIT licence:
see LICENSE.
