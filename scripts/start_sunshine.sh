#!/bin/bash

export DISPLAY=:0
LOGFILE_PATH="${DOCUMENTS_DIR}/sunshine/sunshine.log"

# check if Sunshine is already running
if pgrep -x "sunshine" > /dev/null; then
  echo "Sunshine is already running."
  exit 0
fi

nohup sunshine > "${LOGFILE_PATH}" 2>&1 &
echo "Sunshine started. Logs are at ${LOGFILE_PATH}."
