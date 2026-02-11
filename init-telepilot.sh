#!/bin/sh
set -e

TDLIB_PATH="/home/node/.n8n/nodes/node_modules/@telepilotco/tdlib-binaries-prebuilt/prebuilds/libtdjson.so"

if [ ! -f "$TDLIB_PATH" ]; then
    echo "==> Installing TelePilot native binaries (tdlib)..."
    mkdir -p /home/node/.n8n/nodes
    cd /home/node/.n8n/nodes

    # Initialize package.json if not exists
    if [ ! -f "package.json" ]; then
        npm init -y > /dev/null 2>&1
    fi

    npm install @telepilotco/tdlib-binaries-prebuilt
    echo "==> TelePilot native binaries installed successfully"
else
    echo "==> TelePilot native binaries already present"
fi

# Delegate to original n8n entrypoint
exec /docker-entrypoint.sh "$@"
