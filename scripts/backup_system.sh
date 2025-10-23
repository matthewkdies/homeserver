#!/usr/bin/bash

# ------------------------------------------------------------
# This script runs as a cron job to back up my machine itself.
# I have a network mount to my Synology NAS where I write the
# resulting tarfiles to. It also uses timestamps to create
# rotating backups. It will keep the seven most recent backups
# of each volume, and discard any older than that. This way
# there are multiple backup files from different dates without
# taking up an insane amount of space. Eventually, I plan to
# do this to another NAS that I have, which may be off-site.
# ------------------------------------------------------------

set -e

. /home/matthewkdies/.envvars
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/backup_system.log"
BACKUP_DIR="/mnt/backups/system"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
MAX_BACKUPS=7  # Number of backups to retain per volume

# TODO: rethink cleanup logic
# remove the oldest backups until there are only MAX_BACKUPS backups remaining
prune_old_backups() {
    local backups=( "${BACKUP_DIR}/system_backup_"*".tar.gz" )  # array of backups

    # only proceed if there are more backups than MAX_BACKUPS
    if (( ${#backups[@]} > MAX_BACKUPS )); then
        local to_delete_count=$(( ${#backups[@]} - MAX_BACKUPS ))
        log_to_file "Pruning ${to_delete_count} old backup(s) for system." "${LOG_FILE}"

        # 🚨 -- 🤖 below! -- 🚨
        # finds the tarfiles for the current volume in the backup directory + prints timestamps
        find "$BACKUP_DIR" -maxdepth 1 -type f -name "system_backup_*.tar.gz" -printf "%T@ %p\n" | \
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

log_to_file "Beginning system backup at ${TIMESTAMP}." "${LOG_FILE}"

# backup by creating archive file
# I use a temp and final file in case of power loss during the backup
# hey, I'm not paranoid, you're paranoid!
TEMP_BACKUP="${BACKUP_DIR}/.system_backup_${TIMESTAMP}.tar.gz.tmp"
FINAL_BACKUP="${BACKUP_DIR}/system_backup_${TIMESTAMP}.tar.gz"
tar -cpzf "${BACKUP_DIR}/system_backup_${TIMESTAMP}.tar.gz" --exclude={"/proc","/sys","/dev","/mnt","/media","/run","/lost+found","/var/lib/docker"} /  2>/dev/null
mv "${TEMP_BACKUP}" "${FINAL_BACKUP}"
rm "${TEMP_BACKUP}"

log_to_file "Backup completed successfully!" "${LOG_FILE}"

prune_old_backups

clean_log_file "${LOG_FILE}"
