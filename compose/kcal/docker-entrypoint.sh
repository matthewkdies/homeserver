#!/bin/sh
set -e

# su-exec: will run entrypoint as another user
# shadow: will enable usermod + groupmod
apk update
apk add --no-cache su-exec shadow

# change existing www user to have UID + GID of my host user that owns the Docker secrets files
# also change existing file ownership from old UID/GID to new UID/GID
usermod -u 148 www
groupmod -g 142 www
find / -user 1000 -exec chown -h 148 {} \;
find / -group 1000 -exec chgrp -h 142 {} \;

# make logfiles for stdout and stderr; they're not owned by the user anymore
mkdir -p /var/log
touch /var/log/myapp-stdout.log /var/log/myapp-stderr.log
chown 148:142 /var/log/myapp-stdout.log /var/log/myapp-stderr.log

# use su-exec to change ownership and then run the other entrypoint stuff:
# script that sets the env vars based on Docker secrets
# any other args passed to it
exec su-exec 148:142 /usr/local/bin/set_secret_vars.sh "$@" > /var/log/myapp-stdout.log 2> /var/log/myapp-stderr.log
