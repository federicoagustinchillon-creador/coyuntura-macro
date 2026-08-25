"""
CONECTOR DE VISTAS CUALITATIVAS: SECONDBRAIN -> DATOS_DEL_DIA.JSON
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

AVISO (2026-08-25): este modulo sincronizaba antes tambien el cambiario
(oficial/CCL/brecha) desde SecondBrain. Se dio de baja esa parte porque al
contrastar contra la fuente oficial (BCRA) se encontro una discrepancia de
~45% (SecondBrain informaba oficial 1055.0 el mismo dia que el BCRA publicaba
1531.07) y una tasa de politica monetaria que el BCRA ya no publica desde
2025-07. Ver el docstring de src/fetch_datos_reales.py para el detalle
completo. Desde ese hallazgo, el cambiario y las tasas de referencia se
sincronizan exclusivamente desde src/fetch_datos_reales.py (BCRA + yfinance,
fuentes oficiales verificables), y SecondBrain queda restringido a lo que
es -- juicio de inversion cualitativo (vistas tacticas Black-Litterman con
tesis), no una serie de mercado.

El orquestador real usado por el pipeline y el dashboard es
src/sync_datos_del_dia.py (sincronizar_todo), que llama a ambas fuentes con
el alcance correcto. Este archivo se conserva por sus helpers compartidos
(cargar_json/guardar_json/validar_contra_schema) y para uso standalone:
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
    """Sincroniza SOLO black_litterman_tactical_views (juicio cualitativo).
    Ya no toca cambiario ni fecha -- ver aviso en el docstring del modulo.
    Devuelve (ok: bool, resumen: dict)."""
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
                print(f"      [SecondBrain] ERROR de validacion post-sync: {error}")
                print("      [SecondBrain] Se aborta la escritura para no corromper el contrato.")
            return False, {"actualizados": [], "motivo": error}

    guardar_json(DATA_PATH, datos)

    if verbose:
        if actualizados:
            print(f"      [SecondBrain] Vistas tacticas sincronizadas desde {REGISTRY_PATH}")
        else:
            print("      [SecondBrain] Registro leido, sin vistas nuevas.")
        print("      [SecondBrain] Cambiario y tasas NO se toman de aqui -- ver src/fetch_datos_reales.py")

    return True, {"actualizados": actualizados}


if __name__ == "__main__":
    ok, resumen = sincronizar_desde_secondbrain()
    sys.exit(0 if ok else 1)
