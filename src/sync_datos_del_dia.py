"""
ORQUESTADOR DE SINCRONIZACION DE datos_del_dia.json
=============================================================================
Autor: Federico Agustin Chillon

Punto de entrada unico usado por el pipeline (Paso 0) y por el dashboard
(cada request a /api/live).

Historia (2026-08-25, mismo dia -- ver git log para el detalle completo):
1. Version original: SecondBrain como fuente de cambiario. Se descubrio que
   su registro nunca tuvo datos reales (bug en el fetch de BCRA -- siempre
   caia a un fallback hardcodeado disfrazado de "verified baseline").
2. Se bypaseo SecondBrain y se armo un conector directo a BCRA/yfinance
   (src/fetch_datos_reales.py) como fuente primaria.
3. SecondBrain se corrigio en la fuente (otra sesion, mismo dia): ahora cada
   campo de su registro lleva su propio tag "<campo>__source" =
   "LIVE:<fuente>:<fecha>" o "STALE_FALLBACK:..." / "MODEL_ASSUMPTION:...".
   Con esa trazabilidad, SecondBrain vuelve a ser la fuente PRIMARIA (es el
   hub que van a leer todos los agentes del ecosistema, no solo este
   proyecto) -- pero SOLO se confia en un campo si su propio tag dice LIVE.
   src/fetch_datos_reales.py (BCRA/yfinance directo) queda como respaldo
   para cualquier campo que SecondBrain no traiga en vivo en una corrida
   puntual, y sigue siendo la fuente de Merval (SecondBrain no lo cubre).

Campos que NINGUNA fuente automatica cubre todavia y siguen siendo carga
manual: dolar.mep, dolar.blue, toda tasas_ars/inflacion/actividad/
soberano_usd/equity.lideres (multiplos).
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.fetch_datos_reales import sincronizar_datos_reales, registrar_track_record  # noqa: E402
from src.sync_secondbrain_macro import (  # noqa: E402
    cargar_json, guardar_json, validar_contra_schema,
    DATA_PATH, SCHEMA_PATH, REGISTRY_PATH,
)

CAMPOS_MANUALES = [
    "dolar.mep", "dolar.blue",
    "tasas_ars.*", "inflacion.*", "actividad.*",
    "soberano_usd.* (TIRes, Nelson-Siegel)",
    "equity.lideres (multiplos EV/EBITDA)",
]

# clave en registry.macro_indicators -> (seccion, clave) en datos_del_dia.json
MAPEO_SECONDBRAIN = {
    "tipo_de_cambio_oficial": ("dolar", "oficial_bna"),
    "tipo_de_cambio_mayorista": ("dolar", "mayorista"),
    "ccl_mercado": ("dolar", "ccl"),
}


def _es_live(registry_macro, campo):
    fuente = registry_macro.get(f"{campo}__source", "")
    return fuente.startswith("LIVE:"), fuente


def sincronizar_todo(verbose=True):
    """Devuelve (ok: bool, resumen: dict). Escribe datos_del_dia.json solo
    si el resultado combinado sigue siendo valido contra el schema."""
    datos = cargar_json(DATA_PATH)
    if datos is None:
        if verbose:
            print(f"      [Sync] ERROR: no existe {DATA_PATH}")
        return False, {"actualizados": [], "fuentes": {}}

    actualizados = []
    cubierto_por_secondbrain = set()  # nombres de campo en MAPEO_SECONDBRAIN ya resueltos con LIVE

    # 1) SecondBrain, PRIMARIO -- solo se toma lo que el propio registro marca LIVE.
    registry = cargar_json(REGISTRY_PATH)
    macro = registry.get("macro_indicators", {}) if registry else {}
    for campo_sb, (seccion, clave) in MAPEO_SECONDBRAIN.items():
        if campo_sb not in macro:
            continue
        es_live, fuente_tag = _es_live(macro, campo_sb)
        if not es_live:
            if verbose:
                print(f"      [SecondBrain] {campo_sb} no esta LIVE ({fuente_tag or 'sin tag'}), se busca en BCRA/yfinance directo.")
            continue
        prev = datos.get(seccion, {}).get(clave)
        nuevo = macro[campo_sb]
        datos.setdefault(seccion, {})[clave] = nuevo
        fuente_corta = fuente_tag.replace("LIVE:", "")
        actualizados.append((f"{seccion}.{clave} [SecondBrain: {fuente_corta}]", prev, nuevo))
        cubierto_por_secondbrain.add(campo_sb)

    if "tipo_de_cambio_oficial" in cubierto_por_secondbrain and registry.get("timestamp"):
        datos["fecha"] = registry["timestamp"].split(" ")[0]

    if macro.get("brecha_cambiaria_pct__source", "").startswith("LIVE:") or \
       ("tipo_de_cambio_oficial" in cubierto_por_secondbrain and "ccl_mercado" in cubierto_por_secondbrain):
        prev = datos.get("dolar", {}).get("brecha_ccl_oficial_pct")
        nuevo = macro.get("brecha_cambiaria_pct")
        if nuevo is not None:
            datos.setdefault("dolar", {})["brecha_ccl_oficial_pct"] = nuevo
            actualizados.append(("dolar.brecha_ccl_oficial_pct [SecondBrain]", prev, nuevo))

    # 2) BCRA + yfinance directo, RESPALDO -- llena lo que SecondBrain no
    #    trajo en vivo esta corrida, y siempre aporta Merval (SecondBrain no
    #    lo cubre todavia).
    reales = sincronizar_datos_reales(verbose=verbose)

    if "tipo_de_cambio_oficial" not in cubierto_por_secondbrain and "oficial_minorista" in reales:
        prev = datos.get("dolar", {}).get("oficial_bna")
        nuevo = reales["oficial_minorista"]["valor"]
        datos.setdefault("dolar", {})["oficial_bna"] = nuevo
        actualizados.append(("dolar.oficial_bna [respaldo BCRA minorista]", prev, nuevo))
        datos["fecha"] = reales["oficial_minorista"]["fecha"]

    if "tipo_de_cambio_mayorista" not in cubierto_por_secondbrain and "mayorista_a3500" in reales:
        prev = datos.get("dolar", {}).get("mayorista")
        nuevo = reales["mayorista_a3500"]["valor"]
        datos.setdefault("dolar", {})["mayorista"] = nuevo
        actualizados.append(("dolar.mayorista [respaldo BCRA A3500]", prev, nuevo))

    if "merval_ultimo_cierre" in reales:
        prev = datos.get("equity", {}).get("merval_ars")
        nuevo = reales["merval_ultimo_cierre"]["close"]
        datos.setdefault("equity", {})["merval_ars"] = nuevo
        actualizados.append(("equity.merval_ars [yfinance ^MERV]", prev, nuevo))

    # Tasas de referencia BCRA/SecondBrain: no forman parte del schema
    # historico, se agregan como bloque informativo aparte (no pisa
    # tasas_ars.*, que sigue siendo el contrato de instrumentos en pesos).
    fecha_registry = registry.get("timestamp", "").split(" ")[0] if registry else None
    tasas_ref = {}
    if macro.get("tasa_badlar_pct__source", "").startswith("LIVE:"):
        tasas_ref["badlar_privados_tna"] = {"valor": macro["tasa_badlar_pct"], "fecha": fecha_registry, "fuente": "SecondBrain"}
    elif "badlar_privados_tna" in reales:
        tasas_ref["badlar_privados_tna"] = {**reales["badlar_privados_tna"], "fuente": "BCRA directo"}
    if macro.get("tna_politica_monetaria_pct__source", "").startswith("LIVE:"):
        tasas_ref["pases_1d_tna"] = {"valor": macro["tna_politica_monetaria_pct"], "fecha": fecha_registry, "fuente": "SecondBrain"}
    elif "pases_1d_tna" in reales:
        tasas_ref["pases_1d_tna"] = {**reales["pases_1d_tna"], "fuente": "BCRA directo"}
    if macro.get("reservas_brutas_usd_m__source", "").startswith("LIVE:"):
        tasas_ref["reservas_brutas_usd_m"] = {"valor": macro["reservas_brutas_usd_m"], "fecha": fecha_registry, "fuente": "SecondBrain"}
    elif "reservas_brutas_usd_m" in reales:
        tasas_ref["reservas_brutas_usd_m"] = {**reales["reservas_brutas_usd_m"], "fuente": "BCRA directo"}
    if tasas_ref:
        datos["tasas_bcra_referencia"] = tasas_ref
        actualizados.append(("tasas_bcra_referencia", None, tasas_ref))

    # Vistas tacticas Black-Litterman: SecondBrain, exclusivamente cualitativo.
    if registry and registry.get("black_litterman_tactical_views"):
        datos["black_litterman_tactical_views"] = registry["black_litterman_tactical_views"]
        actualizados.append(("black_litterman_tactical_views [SecondBrain, cualitativo]", None,
                              f"{len(registry['black_litterman_tactical_views'])} vistas"))

    schema = cargar_json(SCHEMA_PATH)
    if schema:
        ok, error = validar_contra_schema(datos, schema)
        if not ok:
            if verbose:
                print(f"      [Sync] ERROR de validacion post-sync: {error}")
            return False, {"actualizados": [], "fuentes": reales}

    guardar_json(DATA_PATH, datos)
    registrar_track_record(reales, datos)

    if verbose:
        for campo, prev, nuevo in actualizados:
            print(f"      [Sync] {campo}: {prev} -> {nuevo}")
        print("      [Sync] Siguen siendo carga manual: " + ", ".join(CAMPOS_MANUALES))

    return True, {
        "actualizados": actualizados,
        "fuentes": reales,
        "secondbrain_timestamp": registry.get("timestamp") if registry else None,
    }


if __name__ == "__main__":
    ok, resumen = sincronizar_todo()
    sys.exit(0 if ok else 1)
