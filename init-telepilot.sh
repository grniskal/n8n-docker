#!/bin/sh
set -e

TDLIB_SOURCE="/usr/local/lib/libtdjson.so"
TDLIB_TARGET="/home/node/.n8n/nodes/node_modules/@telepilotco/tdlib-binaries-prebuilt/prebuilds/libtdjson.so"

# Copy TDLib binary from Docker image to the path TelePilot expects
if [ -f "$TDLIB_SOURCE" ] && [ ! -f "$TDLIB_TARGET" ]; then
    echo "==> Copying TDLib binary to community nodes path..."
    mkdir -p "$(dirname "$TDLIB_TARGET")"
    cp "$TDLIB_SOURCE" "$TDLIB_TARGET"
    echo "==> Done: $TDLIB_TARGET"
fi

# Delegate to original n8n entrypoint
exec /docker-entrypoint.sh "$@"
