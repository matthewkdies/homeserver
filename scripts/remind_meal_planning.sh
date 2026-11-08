#!/usr/bin/bash
set -euo pipefail

# --------------------------------------------------------------------------
# Sends a push notification to Matt's phone via Ntfy reminding him to
# plan the week's meals using the meal planner CLI script.
# Scheduled weekly via cron (Sunday at 9:00 AM).
# --------------------------------------------------------------------------

if [ -f /home/matthewkdies/.envvars ]; then
	. /home/matthewkdies/.envvars
fi

if [ -f "${SCRIPTS_DIR}/global_functions.sh" ]; then
	. "${SCRIPTS_DIR}/global_functions.sh"
fi

LOG_FILE="${DOCKER_DIR}/log/remind_meal_planning.log"
NTFY_BASE_URL="${NTFY_URL:-https://ntfy.mattdies.com}"

if [ -z "${NTFY_MEALIE_TOPIC:-}" ]; then
	echo "ERROR: NTFY_MEALIE_TOPIC environment variable is not set. Please set it in ~/.envvars." >&2
	exit 1
fi

NTFY_TOPIC="${NTFY_MEALIE_TOPIC}"
NTFY_FULL_URL="${NTFY_BASE_URL}/${NTFY_TOPIC}"
MEALIE_PLANNER_URL="${MEALIE_URL:-https://mealie.mattdies.com}/household/mealplan/planner/view"

is_test=false
if [ "${1:-}" = "--test" ]; then
	is_test=true
fi

if [ -n "${LOG_FILE:-}" ] && [ -d "$(dirname "${LOG_FILE}")" ]; then
	log_to_file "Sending weekly meal planning reminder to Ntfy..." "${LOG_FILE}"
fi

title="Weekly Meal Planning Reminder"
if [ "${is_test}" = true ]; then
	title="[Test] Weekly Meal Planning Reminder"
fi

msg="Time to plan this week's meals! Run 'mealie-plan' in your terminal."

auth_header=()
if [ -n "${NTFY_TOKEN:-}" ]; then
	auth_header=(-H "Authorization: Bearer ${NTFY_TOKEN}")
fi

response=$(curl -s -w "\n%{http_code}" \
	"${auth_header[@]}" \
	-H "Title: ${title}" \
	-H "Priority: default" \
	-H "Tags: plate_with_cutlery,calendar" \
	-H "Click: termius://" \
	-H "Actions: view, Open Termius, termius://; view, Open Mealie, ${MEALIE_PLANNER_URL}" \
	-d "${msg}" \
	"${NTFY_FULL_URL}")

http_code=$(echo "${response}" | tail -n1)
body=$(echo "${response}" | sed '$d')

if [ "${http_code}" -ge 200 ] && [ "${http_code}" -lt 300 ]; then
	echo "Successfully sent meal planning reminder to Ntfy."
	if [ -n "${LOG_FILE:-}" ] && [ -d "$(dirname "${LOG_FILE}")" ]; then
		log_to_file "Notification successfully delivered (HTTP ${http_code})." "${LOG_FILE}"
		clean_log_file "${LOG_FILE}" 500
	fi
	exit 0
else
	echo "Failed to send notification to Ntfy. HTTP status: ${http_code}, response: ${body}" >&2
	if [ -n "${LOG_FILE:-}" ] && [ -d "$(dirname "${LOG_FILE}")" ]; then
		log_to_file "ERROR sending notification (HTTP ${http_code}): ${body}" "${LOG_FILE}"
		clean_log_file "${LOG_FILE}" 500
	fi
	exit 1
fi
