#!/usr/bin/env bash
# Auto-deploy: haalt nieuwe commits van GitHub en herbouwt de container ALLEEN
# als er iets veranderd is. Bedoeld voor een cron-job op de server.
# Installatie (eenmalig, als root op de server):
#   command -v cron >/dev/null || apt-get install -y cron; systemctl enable --now cron
#   ( crontab -l 2>/dev/null | grep -v auto-deploy.sh; \
#     echo "*/3 * * * * bash /opt/cpt-tool/auto-deploy.sh" ) | crontab -
set -e
REPO=/opt/cpt-tool
LOG=/var/log/cpt-autodeploy.log
cd "$REPO" 2>/dev/null || exit 0

git fetch origin main --quiet 2>/dev/null || exit 0
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "$LOCAL")

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date '+%F %T') nieuwe versie ($REMOTE) — deployen" >> "$LOG"
  git reset --hard origin/main >> "$LOG" 2>&1
  docker compose up -d --build >> "$LOG" 2>&1
  echo "$(date '+%F %T') klaar" >> "$LOG"
fi
