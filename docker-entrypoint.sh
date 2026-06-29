#!/usr/bin/env bash
set -e
mkdir -p /app/.streamlit
printf 'password = "%s"\n' "${APP_PASSWORD:-hhsk}" > /app/.streamlit/secrets.toml
exec streamlit run app.py
