"""
TIPO DE CAMBIO REAL BILATERAL ARS/USD -- INDICADOR DE ATRASO/COMPETITIVIDAD CAMBIARIA
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Por que existe este modulo: "brecha cambiaria" (CCL vs. oficial, ya cubierta
en datos_del_dia.json) y "atraso cambiario" son conceptos DISTINTOS que el
dashboard venia mezclando implicitamente. La brecha es una prima de mercado
paralelo por cepo cambiario; el atraso es una desalineacion del tipo de
cambio real frente al poder de compra relativo -- se puede estar sin brecha
(sin cepo) y con atraso cambiario severo (ej. la Convertibilidad 1998-2001).

Formula (tipo de cambio real bilateral, definicion estandar de manual de
macro internacional -- Krugman-Obstfeld cap. 15, Dornbusch):

    TCR(t) = TCN(t) * P_EEUU(t) / P_ARG(t)

Se indexa a 100 en la fecha base para que se lea como "nivel relativo al
punto de partida", no como un numero en pesos:

    TCR_indice(t) = 100 * [TCN(t) / TCN(base)] * [P_EEUU(t)/P_EEUU(base)]
                        / [P_ARG(t) / P_ARG(base)]

Lectura: TCR_indice(t) < 100 -> el peso esta MAS APRECIADO en terminos
reales que en la fecha base (atraso cambiario relativo a ese punto de
partida). TCR_indice(t) > 100 -> mas depreciado (mas competitivo).

Fecha base elegida: diciembre 2016 (dic-2016 = 100). No es una eleccion
arbitraria ni un "nivel de equilibrio" que este modulo afirme conocer -- es
la MISMA base que el propio INDEC usa para su serie de IPC nacional vigente
(no hay una serie de IPC nacional continua anterior a esa fecha con la
metodologia actual). El indice no dice "100 es el nivel correcto"; dice
"esto es cuanto se aprecio o deprecio el peso en terminos reales desde el
primer punto donde la serie oficial vigente tiene datos".

Fuentes, las tres publicas, gratuitas, verificadas sin necesidad de cuenta
ni API key:
  - Tipo de cambio nominal: BCRA v4.0 (api.bcra.gob.ar), variable id=5
    (tipo de cambio mayorista A3500) -- se usa el mayorista, no el
    minorista, porque es la referencia de competitividad comercial
    estandar (mismo criterio que usa el propio ITCRM del BCRA).
  - IPC Argentina: INDEC, via el portal de series de tiempo del Estado
    (apis.datos.gob.ar/series), serie 148.3_INIVELNAL_DICI_M_26 ("IPC.
    Nivel General Nacional. Base dic 2016. Mensual").
  - CPI EE.UU.: Bureau of Labor Statistics, API publica v2 sin API key
    (api.bls.gov/publicAPI/v2), serie CUUR0000SA0 (CPI-U, all items,
    U.S. city average, not seasonally adjusted).

No hay ningun valor fabricado: si una de las tres fuentes no responde para
un mes dado, ese mes queda ausente del resultado en vez de rellenarse.
"""

import json
import os
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CACHE = os.path.join(BASE_DIR, "01_Bases_Datos", "tcr_bilateral.json")

BASE_MES = "2016-12"  # dic-2016 = 100, misma base que el IPC nacional del INDEC

BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
BCRA_ID_MAYORISTA = 5

INDEC_SERIES_API = "https://apis.datos.gob.ar/series/api/series/"
INDEC_ID_IPC_NACIONAL = "148.3_INIVELNAL_DICI_M_26"

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_ID_CPI_US = "CUUR0000SA0"


def _mes(fecha_iso):
    """'2026-07-15' -> '2026-07' -- para agrupar series diarias/mensuales por mes calendario."""
    return fecha_iso[:7]


def obtener_tc_mayorista_mensual(desde=BASE_MES):
    """Promedio mensual del tipo de cambio mayorista A3500 (BCRA), desde
    `desde` (formato 'YYYY-MM') hasta hoy. Devuelve {'YYYY-MM': valor}.

    La API pagina en bloques de 1000 registros (`metadata.resultset`) -- un
    rango de ~10 anios en frecuencia diaria son ~2500+ puntos, mas de una
    pagina. Pedir un solo request y quedarse con "lo que vino" trunca
    silenciosamente la serie a los ultimos ~2.7 anios (se detecto asi: el
    primer intento devolvia datos recien desde 2022, faltando el mes base
    dic-2016 por completo)."""
    hasta = datetime.now().strftime("%Y-%m-%d")
    desde_fecha = f"{desde}-01"
    url = f"{BCRA_BASE}/{BCRA_ID_MAYORISTA}"

    detalle = []
    offset = 0
    while True:
        r = requests.get(url, params={"desde": desde_fecha, "hasta": hasta, "offset": offset}, timeout=30, verify=False)
        r.raise_for_status()
        body = r.json()
        resultados = body.get("results", [])
        pagina = resultados[0]["detalle"] if resultados and "detalle" in resultados[0] else []
        detalle.extend(pagina)

        resultset = body.get("metadata", {}).get("resultset", {})
        total = resultset.get("count", len(pagina))
        offset += resultset.get("limit", len(pagina)) or len(pagina) or 1
        if offset >= total or not pagina:
            break

    por_mes = {}
    for punto in detalle:
        mes = _mes(punto["fecha"])
        por_mes.setdefault(mes, []).append(punto["valor"])

    return {mes: sum(vals) / len(vals) for mes, vals in por_mes.items()}


def obtener_ipc_argentina_mensual(desde=BASE_MES):
    """Serie mensual del IPC nacional nivel general (INDEC), desde `desde`.
    Devuelve {'YYYY-MM': indice}."""
    # limit=1000: el default de esta API es 100 registros -- con eso, un
    # rango de ~116 meses (desde dic-2016) se corta silenciosamente en el
    # mes 100 (marzo-2025) sin ningun error ni aviso. Detectado asi: el
    # calculo terminaba en 2025-03 pese a que la fuente real llega a 2026-07.
    r = requests.get(INDEC_SERIES_API, params={"ids": INDEC_ID_IPC_NACIONAL, "start_date": f"{desde}-01", "limit": 1000}, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    return {fecha[:7]: valor for fecha, valor in data}


def obtener_cpi_eeuu_mensual(desde_anio):
    """Serie mensual del CPI-U (BLS), desde el anio `desde_anio` (int) hasta
    el anio actual. Devuelve {'YYYY-MM': indice}.

    La API publica de BLS sin API key acepta como maximo 10 anios de rango
    POR CONSULTA -- si se pide un rango mayor, la API lo achica sola y
    devuelve status "REQUEST_SUCCEEDED" igual, con el recorte explicado
    solo en el campo `message` (no falla, no avisa por status). Detectado
    asi: pedir 2016-2026 devolvia 2025 como el anio mas reciente, sin
    ningun error visible, hasta leer message = "Year range has been reduced
    to the system-allowed limit of 10 years." Por eso se pide en bloques de
    <=10 anios y se combinan."""
    anio_actual = datetime.now().year
    resultado = {}
    inicio = desde_anio
    while inicio <= anio_actual:
        fin = min(inicio + 9, anio_actual)
        payload = {"seriesid": [BLS_ID_CPI_US], "startyear": str(inicio), "endyear": str(fin)}
        r = requests.post(BLS_API, json=payload, timeout=30)
        r.raise_for_status()
        body = r.json()
        if body.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS API respondio con error: {body.get('message')}")

        for punto in body["Results"]["series"][0]["data"]:
            if not punto["period"].startswith("M") or punto["period"] == "M13":
                continue  # M13 es el promedio anual, no un mes
            valor = punto["value"]
            if valor in (None, "", "-"):
                continue  # BLS marca asi un mes todavia no publicado (o interrumpido, ej. shutdown) -- se omite, no se fabrica
            mes = f"{punto['year']}-{punto['period'][1:]}"
            resultado[mes] = float(valor)

        inicio = fin + 1
    return resultado


def calcular_tcr_bilateral(base_mes=BASE_MES):
    """Devuelve la serie mensual del TCR bilateral ARS/USD indexada a 100 en
    `base_mes`, mas el ultimo valor. No fabrica ningun mes: si a alguna de
    las tres fuentes le falta ese mes, se omite del resultado."""
    anio_base = int(base_mes[:4])

    tc = obtener_tc_mayorista_mensual(desde=base_mes)
    ipc_arg = obtener_ipc_argentina_mensual(desde=base_mes)
    cpi_us = obtener_cpi_eeuu_mensual(desde_anio=anio_base)

    if base_mes not in tc or base_mes not in ipc_arg or base_mes not in cpi_us:
        raise RuntimeError(
            f"Falta el mes base {base_mes} en alguna fuente -- "
            f"TC:{base_mes in tc} IPC_ARG:{base_mes in ipc_arg} CPI_US:{base_mes in cpi_us}"
        )

    tc_base, ipc_arg_base, cpi_us_base = tc[base_mes], ipc_arg[base_mes], cpi_us[base_mes]

    meses_comunes = sorted(set(tc) & set(ipc_arg) & set(cpi_us))
    serie = []
    for mes in meses_comunes:
        indice = 100 * (tc[mes] / tc_base) * (cpi_us[mes] / cpi_us_base) / (ipc_arg[mes] / ipc_arg_base)
        serie.append({"mes": mes, "tcr_indice": round(indice, 2)})

    return {
        "base_mes": base_mes,
        "fuente": "BCRA v4.0 (mayorista) + INDEC (IPC nacional, apis.datos.gob.ar) + BLS (CPI-U, api.bls.gov)",
        "metodologia": "TCR = TC_mayorista * CPI_EEUU / IPC_Argentina, indice base 100 = dic-2016",
        "serie": serie,
        "ultimo": serie[-1] if serie else None,
        "calculado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def guardar_cache(base_mes=BASE_MES):
    """Recalcula el TCR bilateral y lo guarda en 01_Bases_Datos/tcr_bilateral.json.
    Se llama una vez por corrida del pipeline (no en cada poll del dashboard):
    son 3 fuentes externas con paginacion, ~5-10s -- no tiene sentido pedirlo
    de nuevo cada 60s cuando el IPC/CPI subyacente cambia una vez por mes."""
    resultado = calcular_tcr_bilateral(base_mes=base_mes)
    os.makedirs(os.path.dirname(RUTA_CACHE), exist_ok=True)
    with open(RUTA_CACHE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    return resultado


def cargar_cache():
    """Lee la ultima instantanea cacheada. Devuelve None si todavia no se
    corrio guardar_cache() ni una vez -- el llamador decide como degradar
    (nunca se fabrica un valor de reemplazo)."""
    if not os.path.exists(RUTA_CACHE):
        return None
    with open(RUTA_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    resultado = guardar_cache()
    print(f"Meses calculados: {len(resultado['serie'])}")
    print(f"Ultimo: {resultado['ultimo']}")
    print(f"Cache guardado en: {RUTA_CACHE}")
