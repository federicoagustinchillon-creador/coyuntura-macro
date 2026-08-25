"""
API DEL DASHBOARD WEB INSTITUCIONAL DE COYUNTURA MACRO
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Sirve el terminal fintech de acompanamiento entre informes (lunes a jueves).
Cada llamada a /api/live dispara el sync desde SecondBrain (mismo conector
que usa el pipeline, src/sync_secondbrain_macro.py) y devuelve el contenido
vigente de 01_Bases_Datos/datos_del_dia.json -- nunca datos generados en el
propio endpoint. No hay valores fabricados en esta capa: si un campo no
esta en el JSON, el frontend lo debe mostrar como "s/d", no inventarlo.

Ejecucion local:
    uvicorn dashboard.api:app --reload --port 8420
"""

import os
import sys
import json

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.sync_secondbrain_macro import sincronizar_desde_secondbrain, DATA_PATH  # noqa: E402

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Coyuntura Macro -- Terminal de Acompanamiento")


def _cargar_datos_del_dia():
    if not os.path.exists(DATA_PATH):
        return None
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/live")
def get_live():
    ok, resumen = sincronizar_desde_secondbrain(verbose=False)
    datos = _cargar_datos_del_dia()
    if datos is None:
        return JSONResponse(status_code=404, content={"error": "datos_del_dia.json no encontrado"})
    return {
        "datos": datos,
        "sync_secondbrain": {
            "ok": ok,
            "campos_actualizados": [c for c, _, _ in resumen.get("actualizados", [])],
        },
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")
