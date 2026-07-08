#!/usr/bin/env bash
set -e
# Geen wachtwoord-default: liever hard falen dan stilletjes een zwak wachtwoord.
# Zet APP_PASSWORD via /opt/cpt-tool/.env (die staat in .gitignore).
: "${APP_PASSWORD:?APP_PASSWORD is niet gezet. Maak /opt/cpt-tool/.env met: APP_PASSWORD=<jouw wachtwoord>}"
mkdir -p /app/.streamlit
printf 'password = "%s"\n' "$APP_PASSWORD" > /app/.streamlit/secrets.toml
chmod 600 /app/.streamlit/secrets.toml
exec streamlit run app.py
