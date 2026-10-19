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
DB_BACKUP_DIR="/mnt/backups/databases"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
MAX_BACKUPS=3 # Number of backups to retain per volume or database

# remove the oldest backups until there are only MAX_BACKUPS backups remaining
prune_old_backups() {
	local volume=$1
	local backups=("${BACKUP_DIR}/${volume}_"*".tar.gz") # array of backups

	# only proceed if there are more backups than MAX_BACKUPS
	if ((${#backups[@]} > MAX_BACKUPS)); then
		local to_delete_count=$((${#backups[@]} - MAX_BACKUPS))
		log_to_file "Pruning ${to_delete_count} old backup(s) for ${volume}." "${LOG_FILE}"

		# 🚨 -- 🤖 below! -- 🚨
		# finds the tarfiles for the current volume in the backup directory + prints timestamps
		find "$BACKUP_DIR" -maxdepth 1 -type f -name "${volume}_*.tar.gz" -printf "%T@ %p\n" |
			# sorts the files by the timestamps
			sort -n |
			# trims to the number of files we have to delete
			head -n "$to_delete_count" |
			# strips the timestamps
			cut -d ' ' -f 2- |
			# removes the files
			xargs -d '\n' rm -f --
	fi
}

# remove the oldest database dumps until there are only MAX_BACKUPS dumps remaining
prune_old_db_backups() {
	local container=$1
	shopt -s nullglob
	local backups=("${DB_BACKUP_DIR}/${container}_"*".sql.gz")
	shopt -u nullglob

	if ((${#backups[@]} > MAX_BACKUPS)); then
		local to_delete_count=$((${#backups[@]} - MAX_BACKUPS))
		log_to_file "Pruning ${to_delete_count} old database backup(s) for ${container}." "${LOG_FILE}"

		find "$DB_BACKUP_DIR" -maxdepth 1 -type f -name "${container}_*.sql.gz" -printf "%T@ %p\n" |
			sort -n |
			head -n "$to_delete_count" |
			cut -d ' ' -f 2- |
			xargs -d '\n' rm -f --
	fi
}

run_database_backups() {
	mkdir -p "${DB_BACKUP_DIR}"

	# dynamically discover active PostgreSQL containers
	local pg_containers
	pg_containers=$(docker ps --format '{{.Names}}' | grep -E 'postgres|db' || true)

	for container in $pg_containers; do
		# check if container has pg_dumpall installed
		if ! docker exec "$container" which pg_dumpall >/dev/null 2>&1; then
			continue
		fi

		log_to_file "Creating transactional database dump for ${container}..." "${LOG_FILE}"
		local dump_file="${DB_BACKUP_DIR}/${container}_${TIMESTAMP}.sql.gz"
		local temp_dump="${dump_file}.tmp"

		# execute pg_dumpall using container's user
		if docker exec "$container" sh -c '
			user=""
			if [ -n "$POSTGRES_USER_FILE" ] && [ -f "$POSTGRES_USER_FILE" ]; then
				user=$(cat "$POSTGRES_USER_FILE")
			elif [ -n "$POSTGRES_USER" ]; then
				user="$POSTGRES_USER"
			else
				user="postgres"
			fi
			pg_dumpall -U "$user" --clean --if-exists
		' 2>/dev/null | gzip >"${temp_dump}"; then
			mv "${temp_dump}" "${dump_file}"
			log_to_file "Database dump for ${container} succeeded: $(du -h "${dump_file}" | cut -f1)" "${LOG_FILE}"
			prune_old_db_backups "${container}"
		else
			rm -f "${temp_dump}"
			log_to_file "ERROR: Database dump for ${container} failed!" "${LOG_FILE}"
			return 1
		fi
	done
}

run_volume_backups() {
	# ensure backup directory exists (in case mount is lost)
	if ! mountpoint -q "/mnt/backups"; then
		log_to_file "ERROR: Backup directory is not mounted!" "${LOG_FILE}"
		return 1
	fi

	# 1. run transactional database dumps first
	run_database_backups

	# 2. clear all unused volumes so we don't back up anything not needed
	docker volume prune --force

	# 3. get a list of all of the volumes and archive them
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

		prune_old_backups "${VOLUME}" # clean old volumes
	done

	log_to_file "Backups completed successfully!" "${LOG_FILE}"
}

# call the function, then "chain" calls to update ntfy
# https://docs.ntfy.sh/examples/#cronjobs
run_volume_backups &&
	clean_log_file "${LOG_FILE}" &&
	curl \
		-H "Authorization: Bearer ${NTFY_TOKEN}" \
		-H "Title: Backups Succeeded" \
		-H "Priority: low" \
		-H "Tags: package,floppy_disk" \
		-d "All Docker database dumps and volume backups completed successfully." \
		"https://ntfy.mattdies.com/${NTFY_BACKUPS_TOPIC}" ||
	curl \
		-H "Authorization: Bearer ${NTFY_TOKEN}" \
		-H "Title: Backups Failed" \
		-H "Priority: high" \
		-H "Tags: warning,rotating_light" \
		-d "Docker volume / database backup script encountered an error!" \
		"https://ntfy.mattdies.com/${NTFY_BACKUPS_TOPIC}"
