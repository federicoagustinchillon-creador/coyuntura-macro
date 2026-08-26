"""
CONTEXTO UNICO DE DATOS REALES PARA LOS GENERADORES DE INFORMES
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Por que existe este modulo: la auditoria de src/generador_informe_diario.py,
src/generador_paper_semanal.py y src/generador_informe_mensual_reportlab.py
encontro que NINGUNO de los tres cargaba datos_del_dia.json, y que el mismo
concepto (riesgo pais EMBI+, reservas brutas, parametros Nelson-Siegel,
tasa de pases) aparecia con valores DISTINTOS entre archivos y hasta dentro
del mismo archivo -- ej. EMBI+ 680pb en la portada del informe mensual vs.
506pb en el resto del mismo documento; "pases pasivos extinguidos ($0)" en
los tres informes contra el dato real vigente de tasas_bcra_referencia
(23,12% TNA). Esto no es un problema de "falta un conector" sino de que
cada archivo escribia su propio numero de memoria en vez de leer de un
unico lugar -- la causa estructural de la divergencia.

Este modulo es ESE unico lugar. Los tres generadores deben leer de aca, no
volver a hardcodear ni volver a decidir cada uno por su cuenta que fuente
usar. Combina:
  - 01_Bases_Datos/datos_del_dia.json (contrato principal: dolar, tasas_ars,
    inflacion, actividad, soberano_usd, equity, tasas_bcra_referencia,
    black_litterman_tactical_views)
  - src/fetch_datos_reales.py (respaldo BCRA/yfinance en vivo)
  - src/fetch_tcr_bilateral.py (TCR bilateral cacheado)
  - src/fetch_series_indec_bcra.py (EMAE, trayectoria IPC, monetario BCRA)

No fabrica ningun valor: un campo sin fuente queda como None, y
`fmt_o_manual()` lo señala explicitamente en el texto en vez de omitirlo en
silencio o inventar un numero.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_PATH = os.path.join(BASE_DIR, "01_Bases_Datos", "datos_del_dia.json")


def _cargar_datos_del_dia():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_contexto(incluir_series_lentas=True):
    """Punto de entrada unico. `incluir_series_lentas=False` salta EMAE/IPC/
    monetario (3 llamadas a APIs externas, ~10-20s) cuando el llamador solo
    necesita el contrato principal (ej. para armar un KPI puntual) -- los
    tres informes que compilan un documento completo si las necesitan."""
    datos = _cargar_datos_del_dia()

    ctx = {
        "datos": datos,
        "dolar": datos.get("dolar", {}),
        "tasas_ars": datos.get("tasas_ars", {}),
        "inflacion": datos.get("inflacion", {}),
        "actividad": datos.get("actividad", {}),
        "soberano_usd": datos.get("soberano_usd", {}),
        "equity": datos.get("equity", {}),
        "tasas_bcra_referencia": datos.get("tasas_bcra_referencia", {}),
        "black_litterman_tactical_views": datos.get("black_litterman_tactical_views", []),
        "fecha": datos.get("fecha"),
    }

    # Real ex-ante (Fisher, metodologia B del README): TEM Lecap corta vs.
    # inflacion esperada REM -- ambos ya son campos reales del contrato
    # (aunque manuales), el calculo en si no fabrica nada nuevo.
    lecap_corta = ctx["tasas_ars"].get("lecap_corta_tem")
    rem = ctx["tasas_ars"].get("inflacion_esperada_rem_tem")
    ctx["tasa_real_exante_tem_pct"] = round(lecap_corta - rem, 2) if lecap_corta is not None and rem is not None else None

    ctx["tcr_bilateral"] = None
    try:
        from src.fetch_tcr_bilateral import cargar_cache
        ctx["tcr_bilateral"] = cargar_cache()
    except Exception:
        pass

    if not incluir_series_lentas:
        return ctx

    for clave, funcion in [
        ("emae_historico", lambda: __import__("src.fetch_series_indec_bcra", fromlist=["obtener_emae_reciente"]).obtener_emae_reciente()),
        ("ipc_trayectoria", lambda: __import__("src.fetch_series_indec_bcra", fromlist=["obtener_ipc_trayectoria"]).obtener_ipc_trayectoria()),
        ("monetario_historico", lambda: __import__("src.fetch_series_indec_bcra", fromlist=["obtener_monetario_reciente"]).obtener_monetario_reciente()),
    ]:
        try:
            ctx[clave] = funcion()
        except Exception as e:
            print(f"      [Contexto] ERROR trayendo {clave}: {e}")
            ctx[clave] = None

    return ctx


def fmt_pct(v, decimales=1, signo=False):
    """Formatea un porcentaje real o devuelve 's/d' -- nunca un numero
    inventado cuando el campo no existe."""
    if v is None:
        return "s/d"
    prefijo = "+" if signo and v >= 0 else ""
    return f"{prefijo}{v:.{decimales}f}%".replace(".", ",")


def fmt_num(v, decimales=2, prefijo=""):
    if v is None:
        return "s/d"
    return f"{prefijo}{v:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_o_manual(v, formatear=str, nota="carga manual pendiente"):
    """Para campos sin ninguna fuente automatizable en el repo (ver
    auditoria): en vez de omitir el dato o dejar un numero fijo sin decir
    nada, se marca explicitamente. `v` puede venir de un futuro campo
    manual del contrato -- si esta ausente, se declara ausente."""
    if v is None:
        return f"s/d ({nota})"
    return formatear(v)
