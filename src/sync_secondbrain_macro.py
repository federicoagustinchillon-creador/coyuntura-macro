"""
CONECTOR DE FEEDS EN VIVO: SECONDBRAIN -> DATOS_DEL_DIA.JSON
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Sincroniza los campos de datos_del_dia.json que tienen equivalencia real y
directa en el registro vivo de SecondBrain (macro_indicators + vistas
tacticas Black-Litterman), sin fabricar conversiones para los campos que
SecondBrain no cubre. Ver implementation_plan.md para el mapeo completo y
su justificacion.

Disenado para ejecutarse tanto como paso del pipeline (integracion en
pipeline_coyuntura_master.py) como de forma standalone:
    python src/sync_secondbrain_macro.py
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
REGISTRY_PATH = os.environ.get("SECONDBRAIN_REGISTRY_PATH", DEFAULT_REGISTRY_PATH)

# Mapeo campo a campo con equivalencia directa y verificada (ver plan).
# clave SecondBrain (dentro de macro_indicators) -> ruta en datos_del_dia.json
MAPEO_DOLAR = {
    "tipo_de_cambio_oficial": ("dolar", "oficial_bna"),
    "ccl_mercado": ("dolar", "ccl"),
    "brecha_cambiaria_pct": ("dolar", "brecha_ccl_oficial_pct"),
}


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


def sincronizar_desde_secondbrain(verbose=True):
    """Punto de entrada. Devuelve (ok: bool, resumen: dict)."""
    registry = cargar_json(REGISTRY_PATH)
    if registry is None:
        if verbose:
            print(f"      [SecondBrain] Registro no encontrado en {REGISTRY_PATH}")
            print("      [SecondBrain] Se omite el sync; datos_del_dia.json queda sin cambios.")
        return False, {"actualizados": [], "motivo": "registro_ausente"}

    datos = cargar_json(DATA_PATH)
    if datos is None:
        if verbose:
            print(f"      [SecondBrain] ERROR: no existe {DATA_PATH}, nada para sincronizar.")
        return False, {"actualizados": [], "motivo": "datos_del_dia_ausente"}

    macro = registry.get("macro_indicators", {})
    actualizados = []
    for clave_sb, (seccion, clave_destino) in MAPEO_DOLAR.items():
        if clave_sb in macro:
            valor_previo = datos.get(seccion, {}).get(clave_destino)
            valor_nuevo = macro[clave_sb]
            datos.setdefault(seccion, {})[clave_destino] = valor_nuevo
            actualizados.append((f"{seccion}.{clave_destino}", valor_previo, valor_nuevo))

    # Fecha del sync: se toma la parte de fecha del timestamp del registro.
    timestamp = registry.get("timestamp")
    if timestamp:
        fecha_sync = timestamp.split(" ")[0]
        fecha_previa = datos.get("fecha")
        if fecha_sync != fecha_previa:
            datos["fecha"] = fecha_sync
            actualizados.append(("fecha", fecha_previa, fecha_sync))

    # Vistas tacticas Black-Litterman: bloque adicional, no pisa nada del
    # schema existente (additionalProperties no esta restringido).
    vistas = registry.get("black_litterman_tactical_views")
    if vistas:
        datos["black_litterman_tactical_views"] = vistas
        actualizados.append(("black_litterman_tactical_views", None, f"{len(vistas)} vistas"))

    schema = cargar_json(SCHEMA_PATH)
    if schema:
        ok, error = validar_contra_schema(datos, schema)
        if not ok:
            if verbose:
                print(f"      [SecondBrain] ERROR de validacion post-sync: {error}")
                print("      [SecondBrain] Se aborta la escritura para no corromper el contrato.")
            return False, {"actualizados": [], "motivo": error}

    guardar_json(DATA_PATH, datos)

    if verbose:
        if actualizados:
            print(f"      [SecondBrain] Sincronizado desde {REGISTRY_PATH}")
            for campo, previo, nuevo in actualizados:
                print(f"        - {campo}: {previo} -> {nuevo}")
        else:
            print("      [SecondBrain] Registro leido, sin cambios respecto al ultimo sync.")

        campos_manuales = [
            "dolar.mayorista", "dolar.mep", "dolar.blue",
            "tasas_ars.*", "inflacion.*", "actividad.*",
            "soberano_usd.* (TIRes, Nelson-Siegel)",
            "equity.* (Merval, lideres EV/EBITDA)",
        ]
        print("      [SecondBrain] Siguen siendo carga manual (SecondBrain no los cubre):")
        print("        " + ", ".join(campos_manuales))

    return True, {"actualizados": actualizados}


if __name__ == "__main__":
    ok, resumen = sincronizar_desde_secondbrain()
    sys.exit(0 if ok else 1)
