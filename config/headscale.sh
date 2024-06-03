#!/bin/bash

useradd  --home-dir /var/lib/headscale/ \
    --system \
    --user-group \
    --shell /usr/sbin/nologin headscale

mkdir -p /var/lib/headscale/ \
    /var/run/headscale/

chown -R headscale:headscale /var/run/headscale/ \
    /var/lib/headscale/

su -s /bin/headscale -l headscale configtest 
su -s /bin/headscale -l headscale serve 
