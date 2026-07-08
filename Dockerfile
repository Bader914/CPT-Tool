# CPT Su Tool — Streamlit-versie (volledige tool) als container
FROM python:3.12-slim

WORKDIR /app

# build-tools voor pandas/numpy wheels zijn meestal niet nodig op slim+wheels
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY modules ./modules
COPY .streamlit ./.streamlit
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8501
# Bewust GEEN standaard-wachtwoord in de image: APP_PASSWORD komt uit .env.
ENTRYPOINT ["./docker-entrypoint.sh"]
