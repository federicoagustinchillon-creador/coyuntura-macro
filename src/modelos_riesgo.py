"""
RATIO DE ABSORCION Y TURBULENCIA DE MAHALANOBIS -- CALCULADOS SOBRE DATOS REALES
=============================================================================
Autor: Federico Agustin Chillon
Facultad de Ciencias Economicas -- UNCUYO / OERU

Por que existe este modulo: los 3 generadores de informes citaban un
"Ratio de Absorcion (AR)" y una "Turbulencia de Mahalanobis (dt)" con
valores fijos (64,2% / 4,12) sin ningun modelo real detras -- ni un
calculo, ni una fuente. La metodologia (Kritzman & Li, 2010) SI es
replicable con datos que este repo ya trae en vivo: series historicas
reales de BCRA (oficial, mayorista, badlar, pases) y yfinance (Merval),
via src/fetch_datos_reales.obtener_historicos_dashboard().

Metodologia:
  - Retornos diarios (% var) de los 5 activos sobre la ventana disponible
    (~60-90 dias habiles reales).
  - Ratio de Absorcion: proporcion de la varianza total explicada por las
    primeras k componentes principales de la matriz de correlacion de
    esos retornos (k = max(1, round(20% * n_activos)), el estandar del
    paper original).
  - Turbulencia de Mahalanobis: distancia de Mahalanobis del vector de
    retornos del ultimo dia respecto a la media y covarianza historica de
    la misma ventana -- mide cuan "anomalo" fue el ultimo dia frente al
    regimen reciente.

Esto NO es la misma cesta de activos que la version anterior (que
mencionaba Lecap/Boncer/GD30/CCL/Merval sin nunca calcularlos) -- se usa
la cesta que el repo realmente puede traer en vivo, declarada
explicitamente. Si no hay suficientes datos (menos de ~15 observaciones
comunes), la funcion devuelve None en vez de forzar un calculo fragil.
"""

import os
import sys

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def _serie_a_df(nombre, detalle, campo_valor="valor"):
    if not detalle:
        return pd.Series(dtype=float, name=nombre)
    df = pd.DataFrame(detalle)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.set_index("fecha")[campo_valor].rename(nombre)


def calcular_absorption_ratio_y_turbulencia(historicos=None, k_componentes=None):
    """`historicos`: el dict que devuelve
    fetch_datos_reales.obtener_historicos_dashboard() -- se pide aparte
    (no se hace el fetch aca adentro) para no duplicar la llamada si el
    caller ya la hizo. Devuelve un dict con 'absorption_ratio_pct',
    'turbulencia_dt', 'umbral_chi2_95', 'activos' (lista de nombres
    usados), 'n_observaciones', 'regimen' -- o None si no hay datos
    suficientes."""
    if not historicos:
        from src.fetch_datos_reales import obtener_historicos_dashboard
        historicos = obtener_historicos_dashboard(dias=90)

    series = {
        "oficial": _serie_a_df("oficial", historicos.get("oficial_minorista"), "valor"),
        "mayorista": _serie_a_df("mayorista", historicos.get("mayorista_a3500"), "valor"),
        "badlar": _serie_a_df("badlar", historicos.get("badlar_privados"), "valor"),
        "pases": _serie_a_df("pases", historicos.get("pases_1d"), "valor"),
        "merval": _serie_a_df("merval", historicos.get("merval"), "close"),
    }
    series = {k: v for k, v in series.items() if len(v) >= 10}
    if len(series) < 3:
        return None

    df = pd.concat(series.values(), axis=1, join="inner").sort_index()
    retornos = df.pct_change().dropna()
    if len(retornos) < 15:
        return None

    activos = list(retornos.columns)
    n = len(activos)
    k = k_componentes or max(1, round(0.2 * n))

    corr = retornos.corr().values
    autovalores = np.linalg.eigvalsh(corr)
    autovalores = np.sort(autovalores)[::-1]
    autovalores = np.clip(autovalores, 0, None)  # ruido numerico puede dar negativos ~0
    absorption_ratio = float(autovalores[:k].sum() / autovalores.sum()) * 100

    media = retornos.mean().values
    cov = retornos.cov().values
    ultimo = retornos.iloc[-1].values
    try:
        cov_inv = np.linalg.pinv(cov)  # pseudo-inversa: robusta si la matriz es casi singular
        diff = ultimo - media
        turbulencia = float(diff @ cov_inv @ diff.T)
    except np.linalg.LinAlgError:
        turbulencia = None

    from scipy import stats
    umbral_chi2_95 = float(stats.chi2.ppf(0.95, df=n))

    regimen = None
    if turbulencia is not None:
        regimen = "Turbulento" if turbulencia > umbral_chi2_95 else "Normal"

    return {
        "absorption_ratio_pct": round(absorption_ratio, 1),
        "turbulencia_dt": round(turbulencia, 2) if turbulencia is not None else None,
        "umbral_chi2_95": round(umbral_chi2_95, 2),
        "regimen": regimen,
        "activos": activos,
        "n_observaciones": len(retornos),
        "k_componentes": k,
        "fuente": f"Calculado sobre retornos reales de {', '.join(a.capitalize() for a in activos)} "
                  f"(BCRA v4.0 + yfinance, {len(retornos)} observaciones). Metodologia: Kritzman & Li (2010).",
    }


def calcular_dolar_futuro_implicito(spot_mayorista, tem_lecap_corta, plazos_dias=(30, 90, 180)):
    """Dolar futuro implicito por paridad de tasas cubierta (CIP) --
    NO es una cotizacion de mercado de Matba-Rofex (no hay conector real a
    eso en el repo, ver docstring de plot_fx_master en
    generador_graficos_hd.py), es un valor teorico derivado de datos
    reales del contrato: F(T) = S0 * (1 + TEM_lecap)^(T/30). Se asume TEM
    constante entre plazos (la unica tasa real disponible en el contrato
    es la Lecap corta) y tasa en USD ~0 (simplificacion estandar cuando la
    tasa externa es marginal frente a la de pesos). Devuelve None si falta
    algun insumo real -- nunca fabrica un spot o una tasa."""
    if spot_mayorista is None or tem_lecap_corta is None:
        return None
    tem = tem_lecap_corta / 100.0
    curva = []
    for dias in plazos_dias:
        factor = (1 + tem) ** (dias / 30.0)
        f_implicito = spot_mayorista * factor
        tna_implicita = ((f_implicito / spot_mayorista) - 1) * (365.0 / dias) * 100
        curva.append({"dias": dias, "futuro_implicito": round(f_implicito, 2), "tna_implicita_pct": round(tna_implicita, 2)})
    return {
        "curva": curva,
        "metodologia": "CIP: F(T) = Mayorista_spot * (1 + TEM_Lecap_corta)^(T/30). Tasa USD asumida ~0. NO es cotizacion de mercado.",
    }


if __name__ == "__main__":
    import json
    resultado = calcular_absorption_ratio_y_turbulencia()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    futuro = calcular_dolar_futuro_implicito(1511.53, 2.95)
    print(json.dumps(futuro, indent=2, ensure_ascii=False))
