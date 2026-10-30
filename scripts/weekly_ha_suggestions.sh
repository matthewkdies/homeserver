#!/usr/bin/bash
set -euo pipefail

# --------------------------------------------------------------------------
# Runs an Antigravity CLI agent session to inspect Home Assistant via MCP,
# update the 'Weekly HA Suggestions' dashboard card and persistent
# notification, and send a summary push notification to Matt's iPhone.
# Scheduled weekly via cron (Saturday at 8:00 AM).
# --------------------------------------------------------------------------

. /home/matthewkdies/.envvars
. "${SCRIPTS_DIR}/global_functions.sh"

LOG_FILE="${DOCKER_DIR}/log/weekly_ha_suggestions.log"
HA_COMPOSE_DIR="${COMPOSE_DIR}/home-assistant"
AGY_BIN="/home/matthewkdies/.local/bin/agy"

log_to_file "Starting weekly Home Assistant suggestions check..." "${LOG_FILE}"

cd "${HA_COMPOSE_DIR}"

PROMPT="Weekly Home Assistant Suggestion Task:
1. Use the 'home-assistant' MCP tools (ha_get_overview, ha_get_integration, ha_config_get_automation, ha_config_get_dashboard, ha_get_hacs_info, ha_search, etc.) to inspect the current state of the Home Assistant setup (integrations, devices, entities, automations, dashboards/views, areas, HACS).
2. Identify practical, tailored suggestions for:
   - New integrations or HACS components that complement existing hardware/services
   - New automations or improvements to existing ones
   - Useful dashboard views, cards, or helpers
   - Any notable device/entity optimizations (e.g., ungrouped entities, missing area assignments, unavailable devices, repairs)
3. Format a detailed Markdown report of the suggestions (with a 'Last updated' date header).
4. Persist the full report in Home Assistant in two places:
   a) Update the 'Weekly HA Suggestions' markdown card at '/views/0/sections/0/cards/1' on the 'server-rack' dashboard (call ha_config_get_dashboard(url_path='server-rack') to get config_hash, call ha_get_skill_guide() to get BestPracticeKey, then call ha_config_set_dashboard with patch=[{'op': 'replace', 'path': '/views/0/sections/0/cards/1/content', 'value': '<full_markdown>'}]).
   b) Create/update a persistent notification inside Home Assistant using ha_call_service(domain='persistent_notification', service='create', data={'notification_id': 'weekly_ha_suggestions', 'title': '🏠 Weekly HA Suggestions', 'message': '<full_markdown>'}).
5. Send a concise summary push notification to Matt's iPhone using ha_call_service with domain='notify', service='mobile_app_matts_phone', and data={'title': '🏠 Weekly HA Suggestions', 'message': '<concise_summary>\n(Tap to view full details in Home Assistant)', 'data': {'url': '/server-rack/overview', 'actions': [{'action': 'URI', 'title': 'View Full Digest', 'uri': '/server-rack/overview'}]}}."

if output=$("${AGY_BIN}" --project "home-assistant" --dangerously-skip-permissions -p "${PROMPT}" 2>&1); then
	log_to_file "Weekly HA suggestions completed successfully." "${LOG_FILE}"
	log_to_file "${output}" "${LOG_FILE}"
else
	exit_code=$?
	log_to_file "ERROR running weekly HA suggestions (exit ${exit_code}): ${output}" "${LOG_FILE}"
	clean_log_file "${LOG_FILE}" 500
	exit "${exit_code}"
fi

clean_log_file "${LOG_FILE}" 500
