FROM n8nio/n8n:latest

USER root

# Install TelePilot native TDLib binary into system library path
# This avoids touching /home/node/.n8n/nodes/ which n8n manages
RUN cd /tmp && \
    npm pack @telepilotco/tdlib-binaries-prebuilt 2>/dev/null && \
    tar xzf telepilotco-tdlib-binaries-prebuilt-*.tgz && \
    mkdir -p /usr/local/lib && \
    cp package/prebuilds/libtdjson.so /usr/local/lib/ && \
    rm -rf /tmp/package /tmp/telepilotco-tdlib-binaries-prebuilt-*.tgz

# Init script to clean corrupted nodes dir (one-time fix)
COPY init-telepilot.sh /init-telepilot.sh
RUN chmod +x /init-telepilot.sh

USER node

# Make libtdjson.so discoverable by dynamic linker
ENV LD_LIBRARY_PATH="/usr/local/lib"

ENTRYPOINT ["tini", "--", "/init-telepilot.sh"]
