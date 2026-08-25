"""
================================================================================
MOTOR CUANTITATIVO DE RIESGO SISTÉMICO Y FRAGILIDAD DE MERCADO (CROSS-ASSET)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Estándares: Kritzman & Li (2010), Chow et al. (1999) — Institutional Risk Engine
================================================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional


def calcular_turbulencia_mahalanobis(
    retornos: np.ndarray,
    mu: Optional[np.ndarray] = None,
    sigma: Optional[np.ndarray] = None
) -> np.ndarray:
    r"""
    Calcula el Índice de Turbulencia Financiera de Mahalanobis para una serie
    multivariada de retornos de activos cruzados.

    Fórmula:
        d_t = (r_t - \mu)^T \Sigma^{-1} (r_t - \mu)

    Bajo normalidad multivariada: d_t ~ \chi^2(N)
    """
    T, N = retornos.shape
    if mu is None:
        mu = np.mean(retornos, axis=0)
    if sigma is None:
        sigma = np.cov(retornos, rowvar=False)

    try:
        sigma_inv = np.linalg.inv(sigma)
    except np.linalg.LinAlgError:
        sigma_inv = np.linalg.pinv(sigma)

    diff = retornos - mu
    dt_values = np.einsum('ti,ij,tj->t', diff, sigma_inv, diff)
    return dt_values


def calcular_absorption_ratio(
    retornos: np.ndarray,
    k_components: int = 2,
    window: int = 30
) -> Tuple[np.ndarray, np.ndarray]:
    r"""
    Calcula el Ratio de Absorción (Absorption Ratio, AR) continuo en ventana rodante.

    Fórmula:
        AR = \frac{\sum_{i=1}^k \lambda_i}{\sum_{j=1}^N \lambda_j} = \frac{\sum_{i=1}^k \text{Var}(PC_i)}{\operatorname{Tr}(\Sigma)}
    """
    T, N = retornos.shape
    ar_series = np.full(T, np.nan)

    for i in range(window, T + 1):
        sub_rets = retornos[i - window:i, :]
        cov_matrix = np.cov(sub_rets, rowvar=False)
        evals = np.linalg.eigvalsh(cov_matrix)
        evals = np.sort(evals)[::-1]
        total_var = np.sum(evals)
        if total_var > 1e-12:
            ar_series[i - 1] = np.sum(evals[:k_components]) / total_var

    delta_ar_series = np.full(T, np.nan)
    valid_idx = np.where(~np.isnan(ar_series))[0]
    if len(valid_idx) > 15:
        for idx in valid_idx[15:]:
            mu_hist = np.nanmean(ar_series[:idx])
            std_hist = np.nanstd(ar_series[:idx])
            if std_hist > 1e-6:
                delta_ar_series[idx] = (ar_series[idx] - mu_hist) / std_hist

    return ar_series, delta_ar_series


def evaluar_estado_fragilidad_mercado(
    retornos_recientes: np.ndarray,
    nombres_activos: List[str]
) -> Dict[str, any]:
    """
    Realiza una evaluación integral de turbulencia y fragilidad sistémica.
    """
    T, N = retornos_recientes.shape
    k = min(2, N)
    
    dt_all = calcular_turbulencia_mahalanobis(retornos_recientes)
    dt_actual = float(dt_all[-1])
    chi2_95 = N * (1 - 2/(9*N) + 1.64485 * np.sqrt(2/(9*N)))**3
    
    window_calc = min(30, T // 2) if T >= 20 else T
    ar_all, delta_ar_all = calcular_absorption_ratio(retornos_recientes, k_components=k, window=window_calc)
    ar_actual = float(ar_all[-1]) if not np.isnan(ar_all[-1]) else 0.65
    delta_ar_actual = float(delta_ar_all[-1]) if not np.isnan(delta_ar_all[-1]) else 0.0

    es_turbulento = dt_actual > chi2_95
    es_fragil = ar_actual > 0.75 or delta_ar_actual > 1.5

    if es_fragil and es_turbulento:
        regimen = "ESTRÉS SISTÉMICO AGUDO (Régimen de Pánico / Acoplamiento Total)"
        accion_cartera = "DESARMAR RIESGO: Rotar 70% a Letras de Corto Plazo (Lecaps) y 30% a Cobertura Dura (Bopreal)."
    elif es_fragil and not es_turbulento:
        regimen = "FRAGILIDAD LATENTE (Alta Sincronización sin Shock Aún)"
        accion_cartera = "PRECAUCIÓN TÁCTICA: Reducir beta de cartera y acortar duration en bonos soberanos."
    elif not es_fragil and es_turbulento:
        regimen = "SHOCK IDIOSINCRÁTICO AISLADO (Dispersión Asimétrica)"
        accion_cartera = "OPORTUNIDAD DE ARBITRAJE: Comprar activos castigados por sobrerreacción transitoria."
    else:
        regimen = "RÉGIMEN RESILIENTE / DESACOPLADO (Diversificación Óptima)"
        accion_cartera = "SOBREPONDERAR RIESGO: Mantener exposición a renta variable y tramo medio de Globales."

    return {
        "dt_actual": round(dt_actual, 2),
        "chi2_umbral_95": round(chi2_95, 2),
        "es_turbulento": es_turbulento,
        "absorption_ratio": round(ar_actual * 100, 1),
        "delta_ar_zscore": round(delta_ar_actual, 2),
        "es_fragil": es_fragil,
        "regimen": regimen,
        "accion_cartera": accion_cartera,
        "activos_evaluados": nombres_activos
    }


if __name__ == "__main__":
    np.random.seed(42)
    sample_rets = np.random.normal(0.001, 0.02, size=(60, 5))
    res = evaluar_estado_fragilidad_mercado(sample_rets, ['Lecap', 'Boncer', 'GD30', 'CCL', 'Merval'])
    print("Test OK:", res['regimen'])
