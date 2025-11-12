#!/bin/bash
set_permissions() {
    local dirs=("$@")  # Capture all arguments as an array

    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "Setting ownership for directory: $dir"
            chown -R plex:plex_stack "$dir"
            echo "Ownership set successfully for $dir"

            echo "Setting permissions for directory: $dir"

            # set directory permissions to 775
            find "$dir" -type d -exec chmod 775 {} \;

            # apply the SGID bit so new dirs inherit existing group ownership
            find "$dir" -type d -exec chmod g+s {} \;

            # set file permissions to 664
            find "$dir" -type f -exec chmod 664 {} \;

            torrents_dir="${dir}/torrents"
            chown -R qbittorrent "${torrents_dir}"

            echo "Permissions set successfully for $dir"
        else
            echo "Warning: $dir does not exist or is not a directory."
        fi
    done
}

source /home/matthewkdies/.envvars
set_permissions "${DATA_DIR}" "${DATA3_DIR}" "${DATA2_DIR}"
