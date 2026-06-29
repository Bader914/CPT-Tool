#!/usr/bin/env bash
# CPT Su Tool — één-commando deploy op de server (geïsoleerde container).
# Gebruik:  curl -fsSL https://raw.githubusercontent.com/Bader914/CPT-Tool/main/webapp/deploy.sh | bash
set -e

echo "==> git/docker controleren..."
command -v git >/dev/null 2>&1 || { apt-get update -y && apt-get install -y git; }
command -v docker >/dev/null 2>&1 || { echo "==> Docker installeren..."; curl -fsSL https://get.docker.com | sh; }

echo "==> Code ophalen..."
if [ -d /opt/cpt-tool/.git ]; then
  cd /opt/cpt-tool && git pull
else
  rm -rf /opt/cpt-tool
  git clone https://github.com/Bader914/CPT-Tool.git /opt/cpt-tool
fi

echo "==> Container bouwen en starten..."
cd /opt/cpt-tool/webapp
docker compose up -d --build

# poort openzetten als ufw actief is (raakt verder niets aan)
ufw allow 8080/tcp >/dev/null 2>&1 || true

echo ""
echo "================================================================"
echo "  KLAAR ✅   Open in je browser:   http://178.104.119.117:8080"
echo "================================================================"
docker compose ps
