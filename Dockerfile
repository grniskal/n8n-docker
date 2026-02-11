FROM n8nio/n8n:latest

USER root

# Install TelePilot native TDLib binary via npm (node-pre-gyp downloads the prebuilt .so)
RUN cd /tmp && \
    npm install @telepilotco/tdlib-binaries-prebuilt && \
    mkdir -p /usr/local/lib && \
    cp node_modules/@telepilotco/tdlib-binaries-prebuilt/prebuilds/libtdjson.so /usr/local/lib/ && \
    rm -rf /tmp/node_modules /tmp/package-lock.json

# Init script to clean corrupted nodes dir (one-time fix)
COPY init-telepilot.sh /init-telepilot.sh
RUN chmod +x /init-telepilot.sh

USER node

# Make libtdjson.so discoverable by dynamic linker
ENV LD_LIBRARY_PATH="/usr/local/lib"

ENTRYPOINT ["tini", "--", "/init-telepilot.sh"]
