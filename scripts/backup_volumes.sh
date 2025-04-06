#!/usr/bin/bash

# ------------------------------------------------------------
# This script runs as a cron job to back up my Docker volumes.
# I have a network mount to my Synology NAS where I write the
# resulting tarfiles to. It also uses timestamps to create
# rotating backups. It will keep the three most recent backups
# of each volume, and discard any older than that. This way
# there are multiple backup files from different dates without
# taking up an insane amount of space. Eventually, I plan to
# do this to another NAS that I have, which may be off-site.
# ------------------------------------------------------------

set -e

. /home/matthewkdies/.envvars

LOG_FILE="${DOCKER_DIR}/log/backup.log"
MAX_LOG_LINES=500
BACKUP_DIR="/mnt/backups"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
MAX_BACKUPS=3  # Number of backups to retain per volume

# function: logs output to stdout and to the logfile
log_msg() {
    echo "$(date) - $1" | tee -a "${LOG_FILE}"
}

# function: keeps the logfile capped at a certain number of lines
clean_log_file() {
    NUM_LINES=$(wc -l "${LOG_FILE}" | awk '{ print $1 }')
    if [ "${NUM_LINES}" -gt "${MAX_LOG_LINES}" ]; then
        LINES_TO_DELETE=$((NUM_LINES - MAX_LOG_LINES))
        sed -i "1,${LINES_TO_DELETE}d" "${LOG_FILE}"
    fi
}


# function: remove the oldest backups until there are only MAX_BACKUPS backups remaining
prune_old_backups() {
    local volume=$1
    local backups=( "${BACKUP_DIR}/${volume}_"*".tar.gz" )  # array of backups

    # only proceed if there are more backups than MAX_BACKUPS
    if (( ${#backups[@]} > MAX_BACKUPS )); then
        local to_delete_count=$(( ${#backups[@]} - MAX_BACKUPS ))
        log_msg "Pruning ${to_delete_count} old backups for ${volume}."

        # 🚨 -- 🤖 below! -- 🚨
        # finds the tarfiles for the current volume in the backup directory + prints timestamps
        find "$BACKUP_DIR" -maxdepth 1 -type f -name "${volume}_*.tar.gz" -printf "%T@ %p\n" | \
            # sorts the files by the timestamps
            sort -n | \
            # trims to the number of files we have to delete
            head -n "$to_delete_count" | \
            # strips the timestamps
            cut -d ' ' -f 2- | \
            # removes the files
            xargs -d '\n' rm -f --
    fi
}

# ensure backup directory exists (in case mount is lost)
if ! mountpoint -q "${BACKUP_DIR}"; then
    log_msg "ERROR: Backup directory is not mounted!"
    exit 1
fi

# clear all unused volumes so we don't back up anything not needed
docker volume prune --force

# get a list of all of the volumes
VOLUMES=$(docker volume ls --format "{{.Name}}")

for VOLUME in $VOLUMES; do
    log_msg "Backing up volume: ${VOLUME}."

    # create a temporary container and use it to archive the volume
    BACKUP_FILESTEM="${VOLUME}_${TIMESTAMP}"
    docker run --rm \
        -v "${VOLUME}":/data \
        -v "${BACKUP_DIR}":/backup \
        alpine \
        tar czf "/backup/${BACKUP_FILESTEM}.tar.gz" -C /data .

    prune_old_backups "${VOLUME}"  # clean old volumes
done

log_msg "Backups completed successfully!"

clean_log_file
