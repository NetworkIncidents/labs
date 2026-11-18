#!/bin/sh
# Start chronyd for the lab. -x: chronyd never adjusts the system clock (containers share the host's clock;
# the lab's wrong date lives only in chrony's own estimate of the time, which is what it serves and reports).
# The command socket needs /var/run/chrony owned by chrony, mode 750, or chronyc's privileged commands fail.
mkdir -p /var/run/chrony && chown chrony:chrony /var/run/chrony && chmod 750 /var/run/chrony
cat /etc/hosts.lab >> /etc/hosts
exec chronyd -x -d -f /etc/chrony/lab.conf
