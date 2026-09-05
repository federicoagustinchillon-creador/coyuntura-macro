"""
FUENTES SECUNDARIAS REALES: RIPTE, ISAC, EMBI+ HISTORICO, DESPACHOS DE VINO
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO

Por que existe este modulo: tras la primera pasada de correccion de datos
hardcodeados, varios campos quedaron marcados "sin fuente automatizable"
(RIPTE, cemento/construccion, variacion del EMBI+, despachos de vino).
Ninguno tiene el conector oficial exacto que el texto original prometia
(INV desagregado por fraccionado/granel, AFCP Cuyo especifico, ByMA
intradiario de EMBI+), pero SI hay fuentes reales de segunda mano,
publicas y verificables, aunque a nivel nacional en vez de provincial o
con un dia de rezago -- mejor eso, con la fuente declarada, que dejar el
campo vacio o un numero inventado.

Fuentes:
  - RIPTE (Remuneracion Imponible Promedio de los Trabajadores Estables),
    nacional, nominal: Secretaria de Trabajo via apis.datos.gob.ar. Es
    NOMINAL (pesos corrientes), no "real" (deflactada) -- la variacion %
    mes a mes que se deriva aca tampoco esta deflactada; si se necesita
    poder adquisitivo real hay que restarle inflacion del mismo periodo.
  - ISAC (Indicador Sintetico de la Actividad de la Construccion), base
    2004, nacional, desestacionalizado: INDEC via apis.datos.gob.ar. Es UN
    PROXY NACIONAL, no el "cemento Portland AFCP" especifico de Cuyo que
    el texto original prometia -- se declara explicitamente el cambio de
    alcance donde se usa.
  - Despachos de vino al mercado interno, miles de hectolitros, NACIONAL:
    INV via apis.datos.gob.ar. Es el agregado nacional, no el desglose
    fraccionado/granel de Mendoza que el texto original prometia.
  - Riesgo pais (EMBI+), historico diario: ArgentinaDatos
    (api.argentinadatos.com), un agregador comunitario de datos publicos
    argentinos -- NO es la fuente primaria (JP Morgan/Bloomberg), es una
    fuente de segunda mano. Se usa solo para la VARIACION (delta), no como
    reemplazo del nivel manual ya cargado en el contrato
    (soberano_usd.embi_riesgo_pais_pbs), que sigue siendo la fuente
    primaria para el nivel.

No hay ningun valor fabricado: un campo sin dato en la fuente queda
ausente, nunca se rellena.
"""

import requests

INDEC_SERIES_API = "https://apis.datos.gob.ar/series/api/series/"
ARGENTINADATOS_RIESGO_PAIS = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"

ID_RIPTE = "158.1_REPTE_0_0_5"
ID_ISAC_DESESTACIONALIZADO = "33.2_ISAC_SIN_EDAD_0_M_23_56"
ID_VINO_DESPACHOS_MI = "41.3_DAVMI_0_A_42"  # anual/mensual segun distribution -- se valida el formato real al usar


def _serie_indec(serie_id, limit=1000):
    r = requests.get(INDEC_SERIES_API, params={"ids": serie_id, "limit": limit}, timeout=30)
    r.raise_for_status()
    return {fecha[:7]: valor for fecha, valor in r.json().get("data", [])}


def obtener_ripte_reciente(n_meses=13):
    """RIPTE nacional nominal, ultimos n_meses. Devuelve {'meses': [...],
    'valores': [...], 'var_mensual_ultimo': %, 'var_interanual_ultimo': %}
    -- ambas variaciones son NOMINALES, no deflactadas."""
    serie = _serie_indec(ID_RIPTE)
    meses = sorted(serie.keys())[-n_meses:]
    if len(meses) < 2:
        return None
    valores = [serie[m] for m in meses]
    var_mensual = round(100 * (valores[-1] / valores[-2] - 1), 2)
    var_ia = round(100 * (valores[-1] / valores[-13] - 1), 2) if len(serie) >= 13 and meses[-1][:4] != "" and f"{int(meses[-1][:4])-1}-{meses[-1][5:]}" in serie else None
    return {"meses": meses, "valores": valores, "var_mensual_ultimo": var_mensual, "var_interanual_ultimo": var_ia}


def obtener_isac_reciente(n_meses=13):
    """ISAC nacional desestacionalizado, base 2004. PROXY NACIONAL de
    construccion, no el 'cemento AFCP Cuyo' especifico del texto original."""
    serie = _serie_indec(ID_ISAC_DESESTACIONALIZADO)
    meses = sorted(serie.keys())[-n_meses:]
    if len(meses) < 2:
        return None
    valores = [serie[m] for m in meses]
    var_mensual = round(100 * (valores[-1] / valores[-2] - 1), 2)
    return {"meses": meses, "valores": valores, "nivel_ultimo": valores[-1], "var_mensual_ultimo": var_mensual}


def obtener_vino_despachos_reciente():
    """DESCARTADA A PROPOSITO. La serie 41.3_DAVMI_0_A_42 no pasa un chequeo
    basico de sensatez: valores de ~5 (con metadata que dice "Miles de
    Hectolitros" en la descripcion pero "Miles de Litros" en units -- las
    dos etiquetas se contradicen entre si en el propio catalogo del
    INDEC), muy por debajo del orden de magnitud real de despachos de vino
    argentinos, y el dataset padre tiene metadata de "temporal" fijada en
    2017 pese a que el campo sigue actualizandose. Ante una fuente
    inconsistente, se prefiere no usarla en vez de mostrar un numero que
    parece real pero probablemente no lo es -- vitivinicultura sigue sin
    fuente automatizable confiable."""
    return None


def obtener_riesgo_pais_variacion(dias=30):
    """Variacion del EMBI+ en los ultimos `dias` dias corridos, via
    ArgentinaDatos (fuente de SEGUNDA MANO, agregador comunitario -- no
    JP Morgan/Bloomberg directo). Solo para la variacion (delta pb); el
    nivel sigue viniendo del contrato (soberano_usd.embi_riesgo_pais_pbs).
    Devuelve {'valor_actual': pb, 'fecha_actual': ..., 'valor_hace_N_dias':
    pb, 'variacion_pb': int} o None si la fuente no responde."""
    r = requests.get(ARGENTINADATOS_RIESGO_PAIS, timeout=20)
    r.raise_for_status()
    serie = r.json()
    if len(serie) < 2:
        return None
    actual = serie[-1]
    objetivo_idx = max(0, len(serie) - 1 - dias)
    pasado = serie[objetivo_idx]
    return {
        "valor_actual": actual["valor"], "fecha_actual": actual["fecha"],
        "valor_hace_dias": pasado["valor"], "fecha_hace_dias": pasado["fecha"],
        "variacion_pb": actual["valor"] - pasado["valor"],
        "fuente": "ArgentinaDatos (agregador comunitario, fuente secundaria)",
    }


if __name__ == "__main__":
    import json
    print("RIPTE:", json.dumps(obtener_ripte_reciente(), indent=2, ensure_ascii=False))
    print("ISAC:", json.dumps(obtener_isac_reciente(), indent=2, ensure_ascii=False))
    print("Vino:", json.dumps(obtener_vino_despachos_reciente(), indent=2, ensure_ascii=False))
    print("Riesgo pais var:", json.dumps(obtener_riesgo_pais_variacion(), indent=2, ensure_ascii=False))
