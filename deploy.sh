#!/usr/bin/env bash
# Deploy de volledige Streamlit-tool als container.
set -e
echo "==> git/docker controleren..."
command -v git >/dev/null 2>&1 || { apt-get update -y && apt-get install -y git; }
command -v docker >/dev/null 2>&1 || { echo "==> Docker installeren..."; curl -fsSL https://get.docker.com | sh; }
echo "==> Code ophalen..."
if [ -d /opt/cpt-tool/.git ]; then cd /opt/cpt-tool && git fetch origin main && git reset --hard origin/main; else rm -rf /opt/cpt-tool && git clone https://github.com/Bader914/CPT-Tool.git /opt/cpt-tool; fi
echo "==> Streamlit-tool bouwen en starten (poort 8080)..."
cd /opt/cpt-tool
docker compose up -d --build
# LET OP: poort 8080 NIET meer voor iedereen openzetten. De toegang is
# beperkt tot eigen IP via de firewall (zie README/firewall-instructies).
echo ""
echo "================================================================"
echo "  KLAAR ✅   http://178.104.119.117:8080   (wachtwoord: hhsk)"
echo "================================================================"
docker compose ps
