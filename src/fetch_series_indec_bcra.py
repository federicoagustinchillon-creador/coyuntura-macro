"""
SERIES HISTORICAS REALES PARA LAS INFOGRAFIAS DEL PIPELINE (EMAE, IPC, MONETARIO)
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO

Por que existe este modulo: src/generador_graficos_hd.py generaba sus 9
infografias con arrays de relleno hardcodeados (numpy arrays literales) en
vez de datos reales -- detectado al integrar el Tipo de Cambio Real
bilateral (ver src/fetch_tcr_bilateral.py). Este modulo trae, de fuentes
oficiales gratuitas y sin necesidad de cuenta, lo que SI se puede traer en
vivo; lo que no tiene fuente automatica publica (produccion vitivinicola,
hidrocarburos, cemento de Cuyo, futuros Matba-Rofex, IPC provincial DEIE)
sigue sin cubrirse aca -- ver el comentario en cada funcion de
generador_graficos_hd.py que consume esto para el detalle de que sigue
siendo carga manual y por que.

Fuentes:
  - EMAE (Estimador Mensual de Actividad Economica), serie original,
    desestacionalizada y tendencia-ciclo, base 2004 = 100: INDEC via
    apis.datos.gob.ar/series.
  - IPC nacional (nivel general, nucleo, regulados), indice nivel, base
    dic-2016 = 100: INDEC via apis.datos.gob.ar/series (mismo mecanismo que
    src/fetch_tcr_bilateral.py). La variacion mensual se DERIVA por
    diferencia porcentual entre meses consecutivos del propio indice --
    es la misma definicion que usa el INDEC, no una aproximacion.
  - Base monetaria y pases pasivos del BCRA: api.bcra.gob.ar v4.0,
    variables id=15 (base monetaria) e id=152 (pases pasivos, stock).
"""

import os
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INDEC_SERIES_API = "https://apis.datos.gob.ar/series/api/series/"
BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"

IDS_EMAE = {
    "original": "143.3_NO_PR_2004_A_21",
    "desestacionalizado": "143.3_NO_PR_2004_A_31",
    "tendencia_ciclo": "143.3_NO_PR_2004_A_28",
    "var_interanual_pct": "143.3_ICE_SERVIA_2004_A_25",
}

IDS_IPC_NIVEL = {
    "general": "148.3_INIVELNAL_DICI_M_26",
    "nucleo": "148.3_INUCLEONAL_DICI_M_19",
    "regulados": "148.3_IREGULANAL_DICI_M_22",
}

BCRA_ID_BASE_MONETARIA = 15
BCRA_ID_PASES_PASIVOS = 152


def _serie_indec(serie_id, start_date=None, limit=1000):
    """Trae una serie de indec via el portal de series de tiempo del
    Estado. Devuelve {'YYYY-MM': valor} -- limit=1000 explicito porque el
    default de esta API es 100 (ver docstring de
    src/fetch_tcr_bilateral.obtener_ipc_argentina_mensual para el bug real
    que esto evita: una serie de >100 meses se corta en silencio sin
    limit)."""
    params = {"ids": serie_id, "limit": limit}
    if start_date:
        params["start_date"] = start_date
    r = requests.get(INDEC_SERIES_API, params=params, timeout=30)
    r.raise_for_status()
    return {fecha[:7]: valor for fecha, valor in r.json().get("data", [])}


def _serie_bcra_paginada(id_variable, desde, hasta=None):
    """Igual que fetch_tcr_bilateral._bcra_get pero paginando (metadata.
    resultset) -- ver ese modulo para el bug real que esto evita en rangos
    largos. Devuelve la lista de {'fecha','valor'} en orden de llegada."""
    hasta = hasta or datetime.now().strftime("%Y-%m-%d")
    url = f"{BCRA_BASE}/{id_variable}"
    detalle = []
    offset = 0
    while True:
        r = requests.get(url, params={"desde": desde, "hasta": hasta, "offset": offset}, timeout=30, verify=False)
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
    return detalle


def obtener_emae_reciente(n_meses=32):
    """Devuelve {'meses': [...], 'original': [...], 'desestacionalizado':
    [...], 'tendencia_ciclo': [...], 'var_interanual_ultimo': float} con
    los ultimos `n_meses` reales. Si INDEC no tiene un mes para alguna de
    las 3 series, ese mes se recorta del conjunto comun -- no se rellena."""
    series = {clave: _serie_indec(sid) for clave, sid in IDS_EMAE.items()}
    meses_comunes = sorted(set(series["original"]) & set(series["desestacionalizado"]) & set(series["tendencia_ciclo"]))
    meses_comunes = meses_comunes[-n_meses:]
    if not meses_comunes:
        return None
    return {
        "meses": meses_comunes,
        "original": [series["original"][m] for m in meses_comunes],
        "desestacionalizado": [series["desestacionalizado"][m] for m in meses_comunes],
        "tendencia_ciclo": [series["tendencia_ciclo"][m] for m in meses_comunes],
        # La serie de INDEC viene en fraccion (0,0269 = 2,69%), no en
        # unidades de porcentaje -- se normaliza aca, una sola vez, para
        # que quien consuma este dict no tenga que recordar la escala.
        "var_interanual_ultimo": (
            round(series["var_interanual_pct"][meses_comunes[-1]] * 100, 2)
            if meses_comunes[-1] in series["var_interanual_pct"] else None
        ),
        "var_mensual_desest_ultimo": (
            round(100 * (series["desestacionalizado"][meses_comunes[-1]] / series["desestacionalizado"][meses_comunes[-2]] - 1), 2)
            if len(meses_comunes) >= 2 else None
        ),
    }


def obtener_ipc_trayectoria(n_meses=8):
    """Variacion mensual (%) de IPC general/nucleo/regulados, derivada por
    diferencia porcentual entre niveles consecutivos del propio indice
    oficial del INDEC -- misma definicion que publica el INDEC. Devuelve
    {'meses': [...], 'general': [...], 'nucleo': [...], 'regulados': [...]}."""
    niveles = {clave: _serie_indec(sid) for clave, sid in IDS_IPC_NIVEL.items()}
    meses_todos = sorted(set(niveles["general"]) & set(niveles["nucleo"]) & set(niveles["regulados"]))
    if len(meses_todos) < 2:
        return None

    variaciones = {clave: [] for clave in niveles}
    meses_var = []
    for i in range(1, len(meses_todos)):
        m_prev, m_act = meses_todos[i - 1], meses_todos[i]
        meses_var.append(m_act)
        for clave, serie in niveles.items():
            variaciones[clave].append(round(100 * (serie[m_act] / serie[m_prev] - 1), 2))

    meses_var = meses_var[-n_meses:]
    for clave in variaciones:
        variaciones[clave] = variaciones[clave][-n_meses:]

    return {"meses": meses_var, **variaciones}


def obtener_monetario_reciente(n_meses=8):
    """Promedio mensual de base monetaria y pases pasivos (BCRA), ultimos
    `n_meses`. Los valores de BCRA vienen en millones de ARS -- se
    convierten a billones ($ B, 10^12) para que calcen con la escala del
    grafico existente (stackplot en $ B)."""
    desde = f"{(datetime.now().year - 2)}-01-01"
    base = _serie_bcra_paginada(BCRA_ID_BASE_MONETARIA, desde)
    pases = _serie_bcra_paginada(BCRA_ID_PASES_PASIVOS, desde)

    def _promedio_mensual_en_billones(detalle):
        por_mes = {}
        for punto in detalle:
            mes = punto["fecha"][:7]
            por_mes.setdefault(mes, []).append(punto["valor"])
        return {mes: (sum(vals) / len(vals)) / 1e6 for mes, vals in por_mes.items()}  # millones ARS -> billones ($ B)

    base_m = _promedio_mensual_en_billones(base)
    pases_m = _promedio_mensual_en_billones(pases)

    meses_comunes = sorted(set(base_m) & set(pases_m))[-n_meses:]
    if not meses_comunes:
        return None
    return {
        "meses": meses_comunes,
        "base_m": [round(base_m[m], 2) for m in meses_comunes],
        "pases_m": [round(pases_m[m], 2) for m in meses_comunes],
    }


if __name__ == "__main__":
    import json
    print("EMAE:", json.dumps(obtener_emae_reciente(), indent=2, ensure_ascii=False)[:500])
    print("IPC trayectoria:", json.dumps(obtener_ipc_trayectoria(), indent=2, ensure_ascii=False)[:500])
    print("Monetario:", json.dumps(obtener_monetario_reciente(), indent=2, ensure_ascii=False)[:500])
