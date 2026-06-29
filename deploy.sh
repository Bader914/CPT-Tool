#!/usr/bin/env bash
# Deploy de volledige Streamlit-tool als container (vervangt de FastAPI-webapp).
set -e
echo "==> git/docker controleren..."
command -v git >/dev/null 2>&1 || { apt-get update -y && apt-get install -y git; }
command -v docker >/dev/null 2>&1 || { echo "==> Docker installeren..."; curl -fsSL https://get.docker.com | sh; }
echo "==> Code ophalen..."
if [ -d /opt/cpt-tool/.git ]; then cd /opt/cpt-tool && git pull; else rm -rf /opt/cpt-tool && git clone https://github.com/Bader914/CPT-Tool.git /opt/cpt-tool; fi
echo "==> Oude (FastAPI) webapp stoppen indien actief..."
( cd /opt/cpt-tool/webapp && docker compose down ) >/dev/null 2>&1 || true
echo "==> Streamlit-tool bouwen en starten (poort 8080)..."
cd /opt/cpt-tool
docker compose up -d --build
ufw allow 8080/tcp >/dev/null 2>&1 || true
echo ""
echo "================================================================"
echo "  KLAAR ✅   http://178.104.119.117:8080   (wachtwoord: hhsk)"
echo "================================================================"
docker compose ps
