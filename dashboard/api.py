"""
API DEL DASHBOARD WEB INSTITUCIONAL DE COYUNTURA MACRO
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Sirve el terminal fintech de acompanamiento entre informes (lunes a jueves).
Cada llamada a /api/live dispara el mismo sync que usa el pipeline
(src/sync_datos_del_dia.sincronizar_todo: BCRA + yfinance como fuente
autoritativa de cambiario/tasas/Merval, SecondBrain solo para las vistas
tacticas cualitativas) y devuelve el contenido vigente de
01_Bases_Datos/datos_del_dia.json -- nunca datos generados en el propio
endpoint. No hay valores fabricados en esta capa: si un campo no esta en el
JSON, el frontend lo debe mostrar como "s/d", no inventarlo.

La respuesta incluye "fuentes" con la fecha real de cada dato (BCRA,
yfinance, timestamp del registro de SecondBrain) para que el frontend
muestre evidencia de frescura en vez de una afirmacion generica de
"conectado".

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

from src.sync_datos_del_dia import sincronizar_todo, DATA_PATH  # noqa: E402
from src.sync_secondbrain_macro import cargar_json as _cargar_json_generico, REGISTRY_PATH  # noqa: E402

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Coyuntura Macro -- Terminal de Acompanamiento")


def _cargar_datos_del_dia():
    if not os.path.exists(DATA_PATH):
        return None
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/live")
def get_live():
    ok, resumen = sincronizar_todo(verbose=False)
    datos = _cargar_datos_del_dia()
    if datos is None:
        return JSONResponse(status_code=404, content={"error": "datos_del_dia.json no encontrado"})

    registry = _cargar_json_generico(REGISTRY_PATH)

    return {
        "datos": datos,
        "sync": {
            "ok": ok,
            "campos_actualizados": [c for c, _, _ in resumen.get("actualizados", [])],
            "fuentes": {
                "bcra_yfinance": resumen.get("fuentes", {}),
                "secondbrain_registry_timestamp": registry.get("timestamp") if registry else None,
            },
        },
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")
