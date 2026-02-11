FROM n8nio/n8n:latest

USER root

COPY init-telepilot.sh /init-telepilot.sh
RUN chmod +x /init-telepilot.sh

USER node

ENTRYPOINT ["tini", "--", "/init-telepilot.sh"]
