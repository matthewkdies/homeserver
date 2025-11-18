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
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/backup_volumes.log"
BACKUP_DIR="/mnt/backups/volumes"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
MAX_BACKUPS=3  # Number of backups to retain per volume

# remove the oldest backups until there are only MAX_BACKUPS backups remaining
prune_old_backups() {
    local volume=$1
    local backups=( "${BACKUP_DIR}/${volume}_"*".tar.gz" )  # array of backups

    # only proceed if there are more backups than MAX_BACKUPS
    if (( ${#backups[@]} > MAX_BACKUPS )); then
        local to_delete_count=$(( ${#backups[@]} - MAX_BACKUPS ))
        log_to_file "Pruning ${to_delete_count} old backup(s) for ${volume}." "${LOG_FILE}"

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
if ! mountpoint -q "/mnt/backups"; then
    log_to_file "ERROR: Backup directory is not mounted!" "${LOG_FILE}"
    exit 1
fi

# clear all unused volumes so we don't back up anything not needed
docker volume prune --force

# get a list of all of the volumes
VOLUMES=$(docker volume ls --format "{{.Name}}")

for VOLUME in $VOLUMES; do
    log_to_file "Backing up volume: ${VOLUME}." "${LOG_FILE}"

    # create a temporary container and use it to archive the volume
    BACKUP_FILESTEM="${VOLUME}_${TIMESTAMP}"
    docker run --rm \
        -v "${VOLUME}":/data \
        -v "${BACKUP_DIR}":/backup \
        alpine \
        tar czf "/backup/${BACKUP_FILESTEM}.tar.gz" -C /data .

    prune_old_backups "${VOLUME}"  # clean old volumes
done

log_to_file "Backups completed successfully!" "${LOG_FILE}"

clean_log_file "${LOG_FILE}"
