#!/bin/bash

if pgrep -x "sunshine" > /dev/null; then
  pkill -x sunshine
  echo "Sunshine stopped."
else
  echo "Sunshine is not running."
fi
