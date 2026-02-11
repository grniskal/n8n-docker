#!/bin/sh
set -e

NODES_DIR="/home/node/.n8n/nodes"
MARKER="/home/node/.n8n/.nodes_cleaned"

# One-time cleanup: remove corrupted community nodes directory
# (caused by manual npm install that broke n8n's internal tracking)
if [ ! -f "$MARKER" ] && [ -d "$NODES_DIR" ]; then
    echo "==> One-time cleanup of corrupted community nodes directory..."
    rm -rf "$NODES_DIR"
    touch "$MARKER"
    echo "==> Done. Reinstall community nodes via n8n Settings UI."
fi

# Delegate to original n8n entrypoint
exec /docker-entrypoint.sh "$@"
