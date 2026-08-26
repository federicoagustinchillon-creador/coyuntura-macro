"""
EXPORTADOR ESTATICO DEL DASHBOARD PARA GITHUB PAGES
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

GitHub Pages sirve unicamente archivos estaticos -- no hay forma de correr
FastAPI/uvicorn ahi. Este script corre el mismo sync que usa el pipeline y el
dashboard local (src/sync_datos_del_dia.sincronizar_todo +
src/fetch_datos_reales.obtener_historicos_dashboard) y vuelca el resultado a
dos archivos JSON en docs/, con exactamente la misma forma que devuelven
/api/live y /api/historico -- asi docs/index.html reutiliza sin cambios toda
la logica de terminal() (labelDolar, fuenteDolar, formatearFuente, los 4
graficos) que ya esta verificada en dashboard/index.html.

No hay datos fabricados en este paso: si un campo no vino de ninguna fuente
real en esta corrida, sigue ausente en el JSON exportado, igual que en
/api/live.

Uso (correr antes de cada publicacion a GitHub Pages para refrescar la
instantanea publica):
    python dashboard/build_static_export.py
"""

import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.sync_datos_del_dia import sincronizar_todo, DATA_PATH  # noqa: E402
from src.sync_vistas_tacticas import cargar_json as _cargar_json_generico, REGISTRY_PATH  # noqa: E402
from src.fetch_datos_reales import obtener_historicos_dashboard  # noqa: E402

DOCS_DIR = os.path.join(BASE_DIR, "docs")


def _cargar_datos_del_dia():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_snapshot():
    """Misma forma que GET /api/live -- ver dashboard/api.py:get_live()."""
    ok, resumen = sincronizar_todo(verbose=True)
    datos = _cargar_datos_del_dia()
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
        "publicado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def construir_historico():
    """Misma forma que GET /api/historico -- ver dashboard/api.py:get_historico()."""
    return obtener_historicos_dashboard(dias=90)


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    snapshot = construir_snapshot()
    historico = construir_historico()

    ruta_snapshot = os.path.join(DOCS_DIR, "snapshot.json")
    ruta_historico = os.path.join(DOCS_DIR, "historico.json")

    with open(ruta_snapshot, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    with open(ruta_historico, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    print(f"      [Export estatico] {ruta_snapshot}")
    print(f"      [Export estatico] {ruta_historico}")
    print(f"      [Export estatico] Instantanea publicada en: {snapshot['publicado_en']}")


if __name__ == "__main__":
    main()
