"""
API DEL DASHBOARD WEB INSTITUCIONAL DE COYUNTURA MACRO
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Sirve el terminal fintech de acompanamiento entre informes (lunes a jueves).
Cada llamada a /api/live dispara el mismo sync que usa el pipeline
(src/sync_datos_del_dia.sincronizar_todo: registro macro interno como fuente
primaria de cambiario/tasas, BCRA + yfinance como respaldo y unica fuente de
Merval) y devuelve el contenido vigente de 01_Bases_Datos/datos_del_dia.json
-- nunca datos generados en el propio endpoint. No hay valores fabricados en
esta capa: si un campo no esta en el JSON, el frontend lo debe mostrar como
"s/d", no inventarlo.

La respuesta incluye "fuentes" con la fecha real de cada dato para que el
frontend muestre evidencia de frescura en vez de una afirmacion generica de
"conectado".

Ejecucion local:
    uvicorn dashboard.api:app --reload --port 8420
"""

import os
import sys
import json
import time

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.sync_datos_del_dia import sincronizar_todo, DATA_PATH  # noqa: E402
from src.sync_vistas_tacticas import cargar_json as _cargar_json_generico, REGISTRY_PATH  # noqa: E402
from src.fetch_datos_reales import obtener_historicos_dashboard  # noqa: E402

_HISTORICO_CACHE = {"ts": 0, "data": None}
_HISTORICO_TTL_SEG = 600  # el historial de 90 dias no cambia intra-dia; evita pegarle a BCRA/yfinance en cada poll de 60s

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
                "vistas_timestamp": registry.get("timestamp") if registry else None,
            },
        },
    }


@app.get("/api/historico")
def get_historico():
    """Series reales de los ultimos 90 dias (BCRA + yfinance) para los
    graficos del dashboard. Cacheado 10 min en memoria: son datos que
    publican una vez por dia, no tiene sentido re-descargar toda la serie
    en cada poll de 60s del frontend."""
    ahora = time.time()
    if _HISTORICO_CACHE["data"] is None or (ahora - _HISTORICO_CACHE["ts"]) > _HISTORICO_TTL_SEG:
        _HISTORICO_CACHE["data"] = obtener_historicos_dashboard(dias=90)
        _HISTORICO_CACHE["ts"] = ahora
    return _HISTORICO_CACHE["data"]


@app.get("/")
def index():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")
