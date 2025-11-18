#!/bin/sh

set -e

# validate the OS -- should run on Alpine Linux
CUR_OS=$(cat /etc/os-release | grep "^ID=" | awk -F "=" '{print $2}')
if [ ${CUR_OS} != "alpine" ]; then
    echo "This script is only meant to run on Alpine Linux. Found operating system ID='${CUR_OS}'."
    exit 1
fi

apk add --no-cache shadow su-exec  # looks good, add the pkgs

# validate PUID and PGID vars
if [ -z "${PUID}" ] || [ -z "${PGID}" ]; then
    echo "ERROR: The 'PUID' and 'PGID' variables must be set."
    exit 1
fi

# change UID and GID as needed
OLD_UID="${OLD_UID:-1000}"
OLD_GID="${OLD_GID:-1000}"
NEW_USERNAME="${NEW_USERNAME:-new_user}"
NEW_GROUPNAME="${NEW_GROUPNAME:-new_group}"
if [[ "${OLD_UID}" != "${PUID}" || "${OLD_GID}" != "${PGID}" ]]; then
    echo "INFO: Creating group, if it doesn't exist already."
    getent group "${NEW_GROUPNAME}" &>/dev/null || groupadd --gid "${PGID}" "${NEW_GROUPNAME}"

    echo "INFO: Creating user, if it doesn't exist already."
    id -u "${NEW_USERNAME}" &>/dev/null || useradd --uid "${PUID}" --gid "${PGID}" "${NEW_USERNAME}" 

    echo "INFO: Changing IDs of user to (${OLD_UID}:${OLD_GID}) to ${PUID}:${PGID}."
    groupmod --gid "${PGID}" "${NEW_GROUPNAME}"
    usermod --uid "${PUID}" "${NEW_USERNAME}"
    find / -user "${OLD_UID}" -exec echo chown "${PUID}" '{}' \; 2>/dev/null
    find / -user "${OLD_UID}" -exec chown "${PUID}:${PGID}" {} + 2>/dev/null
    find / -group "${OLD_GID}" -exec chown "${PUID}:${PGID}" {} + 2>/dev/null
fi

echo "INFO: Deleting the 'shadow' pkg..."
apk del --purge shadow > /dev/null 2>&1 || true

# start the software
# provide the original entrypoint as the arguments here and it will run afterwards
echo "Setup complete!"
echo "Executing the following command '$@' as ${NEW_USERNAME} (${PUID}:${PGID})."
exec su-exec "${NEW_USERNAME}" "$@"
