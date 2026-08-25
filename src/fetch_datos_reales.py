"""
CONECTORES DE DATOS REALES: BCRA (API oficial) Y MERCADO (yfinance)
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Fuente PRIMARIA y autoritativa para cambiario/tasas: API estadisticas del
BCRA (api.bcra.gob.ar, v4.0, publica y gratuita, sin autenticacion).
Fuente para indice Merval y equity: yfinance (Yahoo Finance).

Por que existe este modulo (hallazgo critico, ver CHANGELOG en el commit):
El conector anterior (src/sync_secondbrain_macro.py) tomaba tipo_de_cambio_
oficial y ccl_mercado del registro de SecondBrain. Al contrastar contra el
BCRA real se encontro una discrepancia enorme: SecondBrain informaba oficial
1055.0 el mismo dia que el BCRA publicaba minorista 1531.07 y mayorista
1511.53 (~45% de diferencia). Ademas, SecondBrain informaba una "tasa de
politica monetaria" de 35.0% cuando el BCRA no publica una tasa de politica
monetaria vigente desde 2025-07 (esquema sin tasa fija) y la tasa de pases a
1 dia real ronda 20-26%. Conclusion: el registro de SecondBrain no debe
tratarse como fuente de datos de mercado verificados -- se reserva para las
tesis cualitativas Black-Litterman (juicio de inversion, no serie oficial).

IDs de variables BCRA usadas (confirmados contra /estadisticas/v4.0/monetarias):
  4   = Tipo de cambio minorista (promedio vendedor)      -> proxy de "oficial"
  5   = Tipo de cambio mayorista de referencia (A3500)     -> "mayorista"
  150 = Tasa de interes por pases entre terceros a 1 dia   -> tasa corta de referencia
  139 = Tasa BADLAR bancos privados
  1   = Reservas internacionales (USD M)

NOTA: la verificacion SSL de api.bcra.gob.ar falla con el certificado por
defecto de Python en este entorno (problema conocido y documentado del
propio BCRA, no de este script); se desactiva verify solo para este host.
"""

import os
import sys
import json
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST_DIR = os.path.join(BASE_DIR, "01_Bases_Datos", "historico")

BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"

BCRA_VARS = {
    "oficial_minorista": 4,
    "mayorista_a3500": 5,
    "pases_1d": 150,
    "badlar_privados": 139,
    "reservas_brutas_usd_m": 1,
}

MERVAL_TICKER = "^MERV"


def _bcra_get(id_variable, timeout=20):
    url = f"{BCRA_BASE}/{id_variable}"
    try:
        r = requests.get(url, timeout=timeout, verify=False)
        r.raise_for_status()
        resultados = r.json().get("results", [])
        if not resultados:
            return []
        # El endpoint por variable devuelve una lista con un unico elemento
        # {idVariable, detalle: [...]}; el endpoint de catalogo (sin id)
        # devuelve directamente la lista de variables -- distinguimos por
        # la presencia de "detalle".
        primero = resultados[0]
        if isinstance(primero, dict) and "detalle" in primero:
            return primero["detalle"]
        return resultados
    except Exception as e:
        print(f"      [BCRA] ERROR consultando variable {id_variable}: {e}")
        return []


def obtener_ultimo_bcra(id_variable):
    """Devuelve (fecha, valor) del dato mas reciente, o (None, None) si falla."""
    detalle = _bcra_get(id_variable)
    if not detalle:
        return None, None
    ultimo = detalle[0]  # la API devuelve orden descendente por fecha
    return ultimo.get("fecha"), ultimo.get("valor")


def obtener_serie_bcra(id_variable):
    """Devuelve la lista completa [{fecha, valor}, ...] tal como la publica el BCRA."""
    return _bcra_get(id_variable)


def obtener_merval_reciente(dias=30):
    """Historial reciente del indice Merval (^MERV) via yfinance. Devuelve
    lista de {fecha, close} o [] si no hay conectividad."""
    try:
        import yfinance as yf
        hist = yf.Ticker(MERVAL_TICKER).history(period=f"{dias}d")
        if hist.empty:
            return []
        return [
            {"fecha": idx.strftime("%Y-%m-%d"), "close": round(float(row["Close"]), 2)}
            for idx, row in hist.iterrows()
        ]
    except Exception as e:
        print(f"      [yfinance] ERROR consultando {MERVAL_TICKER}: {e}")
        return []


def sincronizar_datos_reales(verbose=True):
    """Trae oficial/mayorista/badlar/reservas desde BCRA y el ultimo cierre
    real de Merval desde yfinance. No fabrica ningun valor: si una fuente
    falla, el campo correspondiente queda ausente del resultado (el llamador
    decide si preserva el valor manual anterior)."""
    resultado = {"fuente": "BCRA_v4 + yfinance", "obtenido_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    fecha_of, val_of = obtener_ultimo_bcra(BCRA_VARS["oficial_minorista"])
    fecha_may, val_may = obtener_ultimo_bcra(BCRA_VARS["mayorista_a3500"])
    fecha_badlar, val_badlar = obtener_ultimo_bcra(BCRA_VARS["badlar_privados"])
    fecha_pases, val_pases = obtener_ultimo_bcra(BCRA_VARS["pases_1d"])
    fecha_res, val_res = obtener_ultimo_bcra(BCRA_VARS["reservas_brutas_usd_m"])

    if val_of is not None:
        resultado["oficial_minorista"] = {"fecha": fecha_of, "valor": val_of}
    if val_may is not None:
        resultado["mayorista_a3500"] = {"fecha": fecha_may, "valor": val_may}
    if val_badlar is not None:
        resultado["badlar_privados_tna"] = {"fecha": fecha_badlar, "valor": val_badlar}
    if val_pases is not None:
        resultado["pases_1d_tna"] = {"fecha": fecha_pases, "valor": val_pases}
    if val_res is not None:
        resultado["reservas_brutas_usd_m"] = {"fecha": fecha_res, "valor": val_res}

    merval_hist = obtener_merval_reciente(dias=5)
    if merval_hist:
        resultado["merval_ultimo_cierre"] = merval_hist[-1]

    if verbose:
        print(f"      [Datos Reales] BCRA oficial minorista: {resultado.get('oficial_minorista')}")
        print(f"      [Datos Reales] BCRA mayorista A3500: {resultado.get('mayorista_a3500')}")
        print(f"      [Datos Reales] BCRA BADLAR privados: {resultado.get('badlar_privados_tna')}")
        print(f"      [Datos Reales] BCRA pases 1 dia: {resultado.get('pases_1d_tna')}")
        print(f"      [Datos Reales] Merval ultimo cierre (yfinance): {resultado.get('merval_ultimo_cierre')}")

    return resultado


def registrar_track_record(resultado_reales, datos_del_dia):
    """Apila el snapshot del dia (dato real de mercado + recomendaciones
    vigentes del contrato) en un CSV historico que se va a ir acumulando de
    ahora en adelante. No hay forma honesta de rellenar el pasado -- no
    existia ningun track record real hasta hoy; esto es el punto de partida,
    no un backfill."""
    os.makedirs(HIST_DIR, exist_ok=True)
    ruta_csv = os.path.join(HIST_DIR, "track_record_diario.csv")

    fecha = datos_del_dia.get("fecha")
    merval = resultado_reales.get("merval_ultimo_cierre", {}).get("close")
    badlar = resultado_reales.get("badlar_privados_tna", {}).get("valor")
    oficial = resultado_reales.get("oficial_minorista", {}).get("valor")
    mayorista = resultado_reales.get("mayorista_a3500", {}).get("valor")

    existe = os.path.exists(ruta_csv)
    ya_registrado = False
    if existe:
        with open(ruta_csv, "r", encoding="utf-8") as f:
            ya_registrado = any(line.startswith(fecha + ",") for line in f.readlines()[1:])

    if ya_registrado:
        return False

    with open(ruta_csv, "a", encoding="utf-8") as f:
        if not existe:
            f.write("fecha,merval_close_real,badlar_tna_real,oficial_minorista_real,mayorista_a3500_real\n")
        f.write(f"{fecha},{merval or ''},{badlar or ''},{oficial or ''},{mayorista or ''}\n")
    return True


if __name__ == "__main__":
    resultado = sincronizar_datos_reales()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
