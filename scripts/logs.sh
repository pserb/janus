#!/bin/bash

# Default values
FOLLOW=false
SERVICE=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f|--follow) FOLLOW=true ;;
        frontend|backend|db) SERVICE="$1" ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo "=== Janus Logs ==="

# Construct the command
CMD="docker compose logs"
if [ "$FOLLOW" = true ]; then
    CMD="${CMD} -f"
fi
if [ -n "$SERVICE" ]; then
    CMD="${CMD} ${SERVICE}"
fi

# Execute the command
$CMD
