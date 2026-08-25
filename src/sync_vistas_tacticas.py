"""
CONECTOR DE VISTAS TACTICAS CUALITATIVAS -> DATOS_DEL_DIA.JSON
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Sincroniza unicamente black_litterman_tactical_views (juicio de inversion
cualitativo con tesis, no una serie de mercado) desde un registro macro
local. El cambiario y las tasas de referencia se sincronizan aparte, desde
src/fetch_datos_reales.py (BCRA + yfinance, fuentes oficiales verificables)
-- ver ese modulo y src/sync_datos_del_dia.py para el flujo completo.

Este archivo tambien expone los helpers compartidos
(cargar_json/guardar_json/validar_contra_schema) usados por el resto del
pipeline de sincronizacion. Uso standalone:
    python src/sync_vistas_tacticas.py
"""

import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "01_Bases_Datos", "datos_del_dia.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "src", "schema_datos_del_dia.json")

DEFAULT_REGISTRY_PATH = os.path.join(
    os.path.expanduser("~"), "SecondBrain", "core", "macro_coyuntura",
    "live_macro_views_registry.json"
)
REGISTRY_PATH = os.environ.get("MACRO_VIEWS_REGISTRY_PATH", DEFAULT_REGISTRY_PATH)


def cargar_json(ruta):
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validar_contra_schema(data, schema):
    """Validacion estructural minima (requeridos por nivel), consistente
    con la logica de agent_runner.validar_datos_del_dia."""
    for req in schema.get("required", []):
        if req not in data:
            return False, f"Clave requerida ausente tras el sync: {req}"
    return True, None


def sincronizar_vistas_tacticas(verbose=True):
    """Sincroniza SOLO black_litterman_tactical_views (juicio cualitativo).
    No toca cambiario ni fecha. Devuelve (ok: bool, resumen: dict)."""
    registry = cargar_json(REGISTRY_PATH)
    if registry is None:
        if verbose:
            print(f"      [Vistas] Registro no encontrado en {REGISTRY_PATH}")
            print("      [Vistas] Se omite el sync; datos_del_dia.json queda sin cambios.")
        return False, {"actualizados": [], "motivo": "registro_ausente"}

    datos = cargar_json(DATA_PATH)
    if datos is None:
        if verbose:
            print(f"      [Vistas] ERROR: no existe {DATA_PATH}, nada para sincronizar.")
        return False, {"actualizados": [], "motivo": "datos_del_dia_ausente"}

    actualizados = []
    vistas = registry.get("black_litterman_tactical_views")
    if vistas:
        datos["black_litterman_tactical_views"] = vistas
        actualizados.append(("black_litterman_tactical_views", None, f"{len(vistas)} vistas"))

    schema = cargar_json(SCHEMA_PATH)
    if schema:
        ok, error = validar_contra_schema(datos, schema)
        if not ok:
            if verbose:
                print(f"      [Vistas] ERROR de validacion post-sync: {error}")
                print("      [Vistas] Se aborta la escritura para no corromper el contrato.")
            return False, {"actualizados": [], "motivo": error}

    guardar_json(DATA_PATH, datos)

    if verbose:
        if actualizados:
            print("      [Vistas] Vistas tacticas sincronizadas.")
        else:
            print("      [Vistas] Registro leido, sin vistas nuevas.")
        print("      [Vistas] Cambiario y tasas NO se toman de aqui -- ver src/fetch_datos_reales.py")

    return True, {"actualizados": actualizados}


if __name__ == "__main__":
    ok, resumen = sincronizar_vistas_tacticas()
    sys.exit(0 if ok else 1)
