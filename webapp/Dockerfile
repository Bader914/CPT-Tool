# CPT Su Tool — lichte FastAPI-container (streamlit-vrij)
FROM python:3.12-slim

WORKDIR /app

# alleen requirements eerst → betere build-cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# applicatie
COPY cpt_core.py main.py ./
COPY static ./static

EXPOSE 8000

# 1 worker is genoeg voor dit gebruik; pas --workers aan bij meer load
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
