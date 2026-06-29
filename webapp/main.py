"""
CPT Su Tool — FastAPI backend.

Serveert de lichte HHSK-frontend en biedt een API om een GEF-sondering te
analyseren (rekenhart in cpt_core, volledig streamlit-vrij).
"""
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import cpt_core

app = FastAPI(title="CPT Su Tool — HHSK", version="2.0")

STATIC = Path(__file__).parent / "static"


@app.get("/api/health")
def health():
    return {"status": "ok", "tool": "CPT Su Tool", "versie": "2.0"}


@app.post("/api/analyse")
async def analyse(file: UploadFile = File(...), gwl_nap: float = Form(0.0)):
    """Analyseer één GEF-bestand en geef het volledige resultaat als JSON terug."""
    if not file.filename.lower().endswith(".gef"):
        raise HTTPException(400, "Upload een .gef-bestand.")
    raw = await file.read()
    content = raw.decode("utf-8", errors="ignore")
    try:
        result = cpt_core.analyseer_gef(content, gwl_nap=gwl_nap)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Analyse mislukt: {e}")
    if not result.get("ok"):
        raise HTTPException(422, result.get("error", "Onbekende fout"))
    result["bestand"] = file.filename
    return JSONResponse(result)


# Frontend als statische bestanden (index.html op /)
app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
