#!/usr/bin/bash
set -euo pipefail

# --------------------------------------------------------------------------
# Pulls latest changes from main, updates running Docker Compose containers,
# and sends a report of image upgrades to Ntfy.
# Runs daily at 5:00 AM via cron (after Renovate runs at 4:00 AM).
# --------------------------------------------------------------------------

# Load environment and helpers
. /home/matthewkdies/.envvars
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/update_containers.log"
DOCS_DIR="/home/matthewkdies/Documents"

log_to_file "Starting container update check..." "${LOG_FILE}"

cd "${DOCS_DIR}"

REPO_URL="https://github.com/matthewkdies/homeserver.git"

# 1. Fetch origin main to check for remote updates without touching working copy
git fetch "${REPO_URL}" main:refs/remotes/origin/main --quiet

LOCAL_MAIN=$(git rev-parse refs/heads/main)
REMOTE_MAIN=$(git rev-parse refs/remotes/origin/main)

# Bounce pattern: exit early if main is already up to date
if [ "${LOCAL_MAIN}" = "${REMOTE_MAIN}" ]; then
	log_to_file "Main branch is up to date with origin/main. Nothing to deploy." "${LOG_FILE}"
	clean_log_file "${LOG_FILE}" 500
	exit 0
fi

log_to_file "New commits detected on main (${LOCAL_MAIN:0:7}..${REMOTE_MAIN:0:7}). Preparing deployment." "${LOG_FILE}"

# 2. Branch management: save state and restore on exit
ORIGINAL_BRANCH=$(git branch --show-current)
WAS_DIRTY=false

cleanup() {
	local exit_code=$?
	if [ -n "${ORIGINAL_BRANCH:-}" ] && [ "$(git branch --show-current)" != "${ORIGINAL_BRANCH}" ]; then
		log_to_file "Returning to original branch: ${ORIGINAL_BRANCH}" "${LOG_FILE}"
		git checkout "${ORIGINAL_BRANCH}" --quiet || true
	fi
	if [ "${WAS_DIRTY}" = true ]; then
		log_to_file "Restoring stashed changes on ${ORIGINAL_BRANCH:-main}..." "${LOG_FILE}"
		git stash pop --quiet || true
	fi
	clean_log_file "${LOG_FILE}" 500
	exit "${exit_code}"
}
trap cleanup EXIT INT TERM

# If working tree has uncommitted changes, stash them
if [ -n "$(git status --porcelain)" ]; then
	log_to_file "Stashing uncommitted local changes on ${ORIGINAL_BRANCH}..." "${LOG_FILE}"
	git stash push -u -m "auto-deploy-temp-stash-$(date +%s)" --quiet
	WAS_DIRTY=true
fi

# Switch to main if not currently checked out
if [ "${ORIGINAL_BRANCH}" != "main" ]; then
	log_to_file "Switching from ${ORIGINAL_BRANCH} to main..." "${LOG_FILE}"
	git checkout main --quiet
fi

# 3. Fast-forward merge fetched updates into main
git merge --ff-only refs/remotes/origin/main --quiet

# Capture git commit log for the report
COMMITS_LOG=$(git log --pretty=format:"• %s" "${LOCAL_MAIN}..${REMOTE_MAIN}")

# 4. Loop through compose stacks and deploy updates
RECREATED_CONTAINERS=""
FAILED_STACKS=""

# Stacks that should not be auto-deployed on this host (e.g. remote servers, NAS, one-shot runners, etc.)
EXCLUDED_STACKS=("pihole" "renovate")

is_stack_excluded() {
	local target="$1"
	for excluded in "${EXCLUDED_STACKS[@]}"; do
		if [ "${excluded}" = "${target}" ]; then
			return 0
		fi
	done
	return 1
}

for compose_file in "${COMPOSE_DIR}"/*/*compose.y*ml; do
	[ -f "${compose_file}" ] || continue

	stack_name=$(basename "$(dirname "${compose_file}")")

	if is_stack_excluded "${stack_name}"; then
		log_to_file "Skipping stack: ${stack_name} (excluded from local deployment)" "${LOG_FILE}"
		continue
	fi

	log_to_file "Checking stack: ${stack_name}..." "${LOG_FILE}"

	if ! output=$(docker compose -f "${compose_file}" up -d --remove-orphans 2>&1); then
		log_to_file "ERROR updating stack ${stack_name}: ${output}" "${LOG_FILE}"
		FAILED_STACKS="${FAILED_STACKS}\n• ${stack_name}"
		continue
	fi

	# Extract any containers that were recreated or started
	changed=$(echo "${output}" | grep -E "Container.*(Started|Created|Recreated)" | awk '{print $2}' | sort -u || true)
	if [ -n "${changed}" ]; then
		for c in ${changed}; do
			RECREATED_CONTAINERS="${RECREATED_CONTAINERS}\n• ${c} (${stack_name})"
			log_to_file "Updated container: ${c} in ${stack_name}" "${LOG_FILE}"
		done
	fi
done

# Prune dangling images to reclaim space (equivalent to watchtower cleanup)
docker image prune -f >/dev/null 2>&1 || true

# 5. Send report via Ntfy
NTFY_TOPIC="${NTFY_WATCHTOWER_TOPIC:-watchtower-LNZnUdP8EXFBrdXB}"
NTFY_URL="https://ntfy.mattdies.com/${NTFY_TOPIC}"

if [ -n "${FAILED_STACKS}" ]; then
	error_msg="Some container updates failed to deploy:${FAILED_STACKS}\n\nCommits pulled:\n${COMMITS_LOG}"
	curl -s \
		-H "Authorization: Bearer ${NTFY_TOKEN}" \
		-H "Title: Container Update Failed" \
		-H "Priority: high" \
		-H "Tags: warning,whale" \
		-d "$(echo -e "${error_msg}")" \
		"${NTFY_URL}" || true
elif [ -n "${RECREATED_CONTAINERS}" ]; then
	report_msg="The following containers were updated:${RECREATED_CONTAINERS}\n\nCommits pulled:\n${COMMITS_LOG}"
	curl -s \
		-H "Authorization: Bearer ${NTFY_TOKEN}" \
		-H "Title: Containers Updated" \
		-H "Priority: default" \
		-H "Tags: whale,package" \
		-d "$(echo -e "${report_msg}")" \
		"${NTFY_URL}" || true
else
	report_msg="Pulled latest changes on main. No running containers required restart.\n\nCommits:\n${COMMITS_LOG}"
	curl -s \
		-H "Authorization: Bearer ${NTFY_TOKEN}" \
		-H "Title: Homeserver Synced" \
		-H "Priority: min" \
		-H "Tags: white_check_mark" \
		-d "$(echo -e "${report_msg}")" \
		"${NTFY_URL}" || true
fi

log_to_file "Container update process finished successfully." "${LOG_FILE}"
