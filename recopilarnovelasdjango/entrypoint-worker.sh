#!/bin/bash

set -e

echo "Starting Xvfb display server..."

Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

sleep 2

echo "Xvfb started on DISPLAY=:99"
echo "Chrome will run in virtual display"

exec "$@"