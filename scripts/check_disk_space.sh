#!/usr/bin/bash

# --------------------------------------------------------------
# This script runs as a cron job to monitor disk usage.
# It checks the root server disk usage against a threshold,
# and dynamically finds and checks all mounted filesystems under
# /mnt against a separate threshold. It alerts via Ntfy if any
# drive exceeds its allowed capacity.
# --------------------------------------------------------------

set -e

. /home/matthewkdies/.envvars
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/disk_monitor.log"

# --- thresholds (percentages) ---
SERVER_THRESHOLD=75   # Max allowed usage for root (/) server disk
MOUNT_THRESHOLD=80    # Max allowed usage for network mounts under /mnt

# dynamic tracker to check if anything triggered an alert
DISK_ALERT_TRIGGERED=0

check_disk_usage() {
    log_to_file "Starting disk usage checks..." "${LOG_FILE}"

    # 1. check root server disk (/)
    # extracts the numeric percentage from df output
    local root_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if (( root_usage >= SERVER_THRESHOLD )); then
        log_to_file "ALERT: Root filesystem (/) is at ${root_usage}% (Threshold: ${SERVER_THRESHOLD}%)" "${LOG_FILE}"
        DISK_ALERT_TRIGGERED=1
    else
        log_to_file "Root filesystem (/) is healthy at ${root_usage}%" "${LOG_FILE}"
    fi

    # 2. check network mounts under /mnt
    # reads /proc/mounts to find active mounts sitting under /mnt
    while read -r mount_point; do
        # Ensure the mount point is currently accessible and valid
        if mountpoint -q "$mount_point"; then
            local mount_usage=$(df "$mount_point" | awk 'NR==2 {print $5}' | sed 's/%//')
            
            if (( mount_usage >= MOUNT_THRESHOLD )); then
                log_to_file "ALERT: Mount [${mount_point}] is at ${mount_usage}% (Threshold: ${MOUNT_THRESHOLD}%)" "${LOG_FILE}"
                DISK_ALERT_TRIGGERED=1
            else
                log_to_file "Mount [${mount_point}] is healthy at ${mount_usage}%" "${LOG_FILE}"
            fi
        fi
    done < <(awk '$2 ~ /^\/mnt\// {print $2}' /proc/mounts)

    # if any threshold was broken, return a non-zero exit code to trip the failure notification
    if (( DISK_ALERT_TRIGGERED == 1 )); then
        return 1
    fi

    log_to_file "All disk checks passed within normal limits." "${LOG_FILE}"
}

check_disk_usage \
    && clean_log_file "${LOG_FILE}" \
    && curl \
    -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: Disk Space OK" \
    -H "Priority: low" \
    -H "Tags: minidisc" \
    -d "Server and network storage levels are within safe parameters." \
    "https://ntfy.mattdies.com/${NTFY_SERVER_HEALTH_TOPIC}" \
    || curl \
    -H "Authorization: Bearer ${NTFY_TOKEN}" \
    -H "Title: Storage Warning: Disk Space Critical" \
    -H "Priority: high" \
    -H "Tags: warning,rotating_light" \
    -d "One or more storage drives have exceeded their capacity thresholds! Check '${LOG_FILE}' for details." \
    "https://ntfy.mattdies.com/${NTFY_SERVER_HEALTH_TOPIC}"
    