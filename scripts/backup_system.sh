#!/usr/bin/bash

# ------------------------------------------------------------
# This script runs as a cron job to back up my machine itself.
# I have a network mount to my Synology NAS where I write the
# resulting tarfiles to. It also uses timestamps to create
# rotating backups. It will keep the seven most recent backups
# of each volume, and discard any older than that.
# ------------------------------------------------------------

set -e

. /home/matthewkdies/.envvars
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/backup_system.log"
BACKUP_DIR="/mnt/backups/system"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
MAX_BACKUPS=7  

# remove the oldest backups until there are only MAX_BACKUPS backups remaining
prune_old_backups() {
    # Using a nullglob ensures that if no files match, the array is empty instead of containing the literal string
    shopt -s nullglob
    local backups=( "${BACKUP_DIR}"/system_backup_*.tar.gz )
    shopt -u nullglob

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

# Ensure backup directory exists
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

# prevent 'set -e' at top of file from killing the script when tar encounters vanishing live files (with exit status 1 or 2)
tar -cpzf "${TEMP_BACKUP}" --exclude={"/proc","/sys","/dev","/mnt","/media","/run","/lost+found","/var/lib/docker"} / 2>/dev/null || [[ $? -eq 1 || $? -eq 2 ]]
mv "${TEMP_BACKUP}" "${FINAL_BACKUP}" # once that's done, move the tempfile to the permanant location

log_to_file "Backup completed successfully!" "${LOG_FILE}"

# call the function, then "chain" calls to update ntfy
# https://docs.ntfy.sh/examples/#cronjobs
prune_old_backups \
    && clean_log_file "${LOG_FILE}" \
    && curl \
    -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: System Backup Succeeded" \
    -H "Priority: low" \
    -H "Tags: floppy_disk" \
    -d "Server file system backup completed successfully." \
    "https://ntfy.mattdies.com/${NTFY_BACKUPS_TOPIC}" \
    || curl \
    -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: System Backup Failed" \
    -H "Priority: high" \
    -H "Tags: warning,rotating_light" \
    -d "Server file system backup failed!" \
    "https://ntfy.mattdies.com/${NTFY_BACKUPS_TOPIC}"
