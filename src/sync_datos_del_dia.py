"""
ORQUESTADOR DE SINCRONIZACION DE datos_del_dia.json
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Punto de entrada unico usado por el pipeline (Paso 0) y por el dashboard
(cada request a /api/live). Combina, por orden de autoridad:

1. BCRA (api.bcra.gob.ar v4.0) + yfinance (src/fetch_datos_reales.py):
   fuente PRIMARIA para cambiario oficial/mayorista, tasas de referencia y
   el indice Merval. Estos son los unicos campos que esta funcion sobrescribe
   con dato de mercado verificado contra la fuente oficial.

2. SecondBrain (src/sync_secondbrain_macro.py): fuente para las vistas
   tacticas Black-Litterman (juicio de inversion cualitativo, no serie
   oficial). No se usa para cambiario ni tasas -- ver el docstring de
   fetch_datos_reales.py para el hallazgo que motivo este cambio.

Campos que NINGUNA fuente automatica cubre todavia y siguen siendo carga
manual: dolar.mep, dolar.blue, dolar.ccl (mercado, no oficial), toda
inflacion/actividad/soberano_usd/equity.lideres (multiplos).
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
    "dolar.mep", "dolar.blue", "dolar.ccl (cotizacion de mercado)",
    "tasas_ars.*", "inflacion.*", "actividad.*",
    "soberano_usd.* (TIRes, Nelson-Siegel)",
    "equity.lideres (multiplos EV/EBITDA)",
]


def sincronizar_todo(verbose=True):
    """Devuelve (ok: bool, resumen: dict). Escribe datos_del_dia.json solo
    si el resultado combinado sigue siendo valido contra el schema."""
    datos = cargar_json(DATA_PATH)
    if datos is None:
        if verbose:
            print(f"      [Sync] ERROR: no existe {DATA_PATH}")
        return False, {"actualizados": [], "fuentes": {}}

    reales = sincronizar_datos_reales(verbose=verbose)
    actualizados = []

    if "oficial_minorista" in reales:
        prev = datos.get("dolar", {}).get("oficial_bna")
        nuevo = reales["oficial_minorista"]["valor"]
        datos.setdefault("dolar", {})["oficial_bna"] = nuevo
        actualizados.append(("dolar.oficial_bna [BCRA minorista, proxy]", prev, nuevo))
        datos["fecha"] = reales["oficial_minorista"]["fecha"]

    if "mayorista_a3500" in reales:
        prev = datos.get("dolar", {}).get("mayorista")
        nuevo = reales["mayorista_a3500"]["valor"]
        datos.setdefault("dolar", {})["mayorista"] = nuevo
        actualizados.append(("dolar.mayorista [BCRA A3500]", prev, nuevo))

    # Brecha CCL/oficial: el CCL sigue siendo manual (no hay fuente gratuita
    # confiable todavia), pero recalculamos la brecha contra el oficial
    # REAL para que al menos esa mitad de la cuenta sea correcta.
    ccl_manual = datos.get("dolar", {}).get("ccl")
    oficial_real = datos.get("dolar", {}).get("oficial_bna")
    if ccl_manual and oficial_real:
        prev = datos.get("dolar", {}).get("brecha_ccl_oficial_pct")
        nuevo = round((ccl_manual / oficial_real - 1.0) * 100.0, 2)
        datos["dolar"]["brecha_ccl_oficial_pct"] = nuevo
        actualizados.append(("dolar.brecha_ccl_oficial_pct [recalculada, CCL sigue manual]", prev, nuevo))

    if "merval_ultimo_cierre" in reales:
        prev = datos.get("equity", {}).get("merval_ars")
        nuevo = reales["merval_ultimo_cierre"]["close"]
        datos.setdefault("equity", {})["merval_ars"] = nuevo
        actualizados.append(("equity.merval_ars [yfinance ^MERV]", prev, nuevo))

    # Tasas de referencia BCRA: no forman parte del schema historico, se
    # agregan como bloque informativo aparte (no pisa tasas_ars.*, que sigue
    # siendo el contrato de instrumentos en pesos, carga manual).
    tasas_bcra = {}
    for campo in ("badlar_privados_tna", "pases_1d_tna", "reservas_brutas_usd_m"):
        if campo in reales:
            tasas_bcra[campo] = reales[campo]
    if tasas_bcra:
        datos["tasas_bcra_referencia"] = tasas_bcra
        actualizados.append(("tasas_bcra_referencia [BCRA]", None, tasas_bcra))

    # Vistas tacticas Black-Litterman: SecondBrain, exclusivamente cualitativo.
    registry = cargar_json(REGISTRY_PATH)
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

    return True, {"actualizados": actualizados, "fuentes": reales}


if __name__ == "__main__":
    ok, resumen = sincronizar_todo()
    sys.exit(0 if ok else 1)
