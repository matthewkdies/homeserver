#!/usr/bin/bash

# logs output to stdout and to the logfile
log_to_file() {
    local log_msg="$1"
    local log_file="$2"
    echo "$(date) - ${log_msg}" | tee -a "${log_file}"
}

# keeps the a logfile capped at a certain number of lines
clean_log_file() {
    local log_file="$1"
    local max_log_lines="${2:-500}"
    local num_lines
    num_lines=$(wc -l "${log_file}" | awk '{ print $1 }')
    if [ "${num_lines}" -gt "${max_log_lines}" ]; then
        lines_to_delete=$((num_lines - max_log_lines))
        sed -i "1,${lines_to_delete}d" "${log_file}"
    fi
}
