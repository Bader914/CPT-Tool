#!/usr/bin/env bash
# Deploy de volledige Streamlit-tool als container.
set -e
echo "==> git/docker controleren..."
command -v git >/dev/null 2>&1 || { apt-get update -y && apt-get install -y git; }
command -v docker >/dev/null 2>&1 || { echo "==> Docker installeren..."; curl -fsSL https://get.docker.com | sh; }
echo "==> Code ophalen..."
if [ -d /opt/cpt-tool/.git ]; then cd /opt/cpt-tool && git fetch origin main && git reset --hard origin/main; else rm -rf /opt/cpt-tool && git clone https://github.com/Bader914/CPT-Tool.git /opt/cpt-tool; fi
cd /opt/cpt-tool

# Wachtwoord staat in .env (NIET in git). Zonder .env stoppen we bewust.
if [ ! -f .env ]; then
  echo ""
  echo "!! /opt/cpt-tool/.env ontbreekt. Maak hem eenmalig aan met:"
  echo "   printf 'APP_PASSWORD=<jouw wachtwoord>\\n' > /opt/cpt-tool/.env"
  echo "   chmod 600 /opt/cpt-tool/.env"
  exit 1
fi

echo "==> Streamlit-tool bouwen en starten (poort 8080)..."
docker compose up -d --build --remove-orphans
# LET OP: poort 8080 NIET voor iedereen openzetten. De toegang is
# beperkt tot eigen IP via de firewall (zie README/firewall-instructies).
echo ""
echo "================================================================"
echo "  KLAAR ✅   http://178.104.119.117:8080"
echo "  (wachtwoord: uit /opt/cpt-tool/.env — wordt hier niet getoond)"
echo "================================================================"
docker compose ps
