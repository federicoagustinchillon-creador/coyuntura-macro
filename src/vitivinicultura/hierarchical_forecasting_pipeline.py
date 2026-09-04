# -*- coding: utf-8 -*-
"""
================================================================================
RECONCILIACIÓN JERÁRQUICA DE PRONÓSTICOS VITIVINÍCOLAS (MINTRACE / INV STANDARD)
================================================================================
Autor: Federico Agustín Chillón
Filiación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Metodología: Wickramasuriya, Athanasopoulos & Hyndman (2019) / Nixtla
================================================================================
Estructura la sumación jerárquica de 4 niveles:
Nivel 0: Total Nacional de Despachos (INV)
Nivel 1: Canal Comercial (Mercado Interno vs Exportación)
Nivel 2: Envase (Botella vs Tetra Brik vs Damajuana/Bag-in-Box)
Nivel 3: Varietal / SKU Individual (Malbec, Cabernet, Bonarda, Blancos)

Aplica el operador MinTrace para garantizar coherencia contable exacta:
  y_tilde = S * (S^T * W^-1 * S)^-1 * S^T * W^-1 * y_hat
================================================================================
"""

import numpy as np
import pandas as pd

class ReconciliadorJerarquicoINV:
    def __init__(self):
        # Matriz de Sumación Jerárquica S (Filas = Todos los niveles, Columnas = Nodos base / Bottom level)
        # Nodos base (4 varietales en 3 envases en 2 canales = 6 series representativas)
        # 1. MI_Botella_Malbec, 2. MI_Tetra_Genérico, 3. MI_Botella_Blanco, 4. EXP_Botella_Malbec, 5. EXP_Botella_Cabernet, 6. EXP_Granel
        self.nombres_bottom = [
            "MI_Botella_Malbec", "MI_Tetra_Generico", "MI_Botella_Blanco",
            "EXP_Botella_Malbec", "EXP_Botella_Cabernet", "EXP_Granel"
        ]
        self.n_bottom = len(self.nombres_bottom)
        
        # Estructura de agregación S (11 series totales = 1 Total + 2 Canales + 2 Envases + 6 Base)
        self.nombres_todas = [
            "Total_Nacional_INV",
            "Canal_Mercado_Interno", "Canal_Exportacion",
            "MI_Botella_Total", "EXP_Botella_Total",
            "MI_Botella_Malbec", "MI_Tetra_Generico", "MI_Botella_Blanco",
            "EXP_Botella_Malbec", "EXP_Botella_Cabernet", "EXP_Granel"
        ]
        
        # Matriz S de dimensión (11 x 6)
        S = np.zeros((len(self.nombres_todas), self.n_bottom))
        # Total Nacional (suma las 6)
        S[0, :] = 1.0
        # Mercado Interno (series 0, 1, 2)
        S[1, 0:3] = 1.0
        # Exportación (series 3, 4, 5)
        S[2, 3:6] = 1.0
        # MI Botella (series 0, 2)
        S[3, [0, 2]] = 1.0
        # EXP Botella (series 3, 4)
        S[4, [3, 4]] = 1.0
        # Nivel base (Identidad 6x6)
        S[5:11, :] = np.eye(self.n_bottom)
        
        self.S = S

    def reconciliar_mintrace(self, pronosticos_incoherentes_y_hat, matriz_cov_errores_W=None):
        y_hat = np.array(pronosticos_incoherentes_y_hat).reshape(-1, 1)
        
        if matriz_cov_errores_W is None:
            # Estimador OLS Shrinkage / Diagonal (W = Identidad o varianza residual)
            W_inv = np.eye(len(self.nombres_todas))
        else:
            W_inv = np.linalg.pinv(matriz_cov_errores_W)

        # Operador de Proyección MinTrace: P = (S^T * W^-1 * S)^-1 * S^T * W^-1
        S_T_W_inv = np.dot(self.S.T, W_inv)
        denom = np.dot(S_T_W_inv, self.S)
        P = np.dot(np.linalg.pinv(denom), S_T_W_inv)

        # Pronósticos reconciliados coherentes: y_tilde = S * P * y_hat
        y_bottom_reconciliados = np.dot(P, y_hat)
        y_tilde = np.dot(self.S, y_bottom_reconciliados)

        # Verificación de coherencia: suma(MI + EXP) == Total Nacional
        total_rec = y_tilde[0, 0]
        mi_rec = y_tilde[1, 0]
        exp_rec = y_tilde[2, 0]
        error_coherencia = abs(total_rec - (mi_rec + exp_rec))

        return {
            "pronosticos_reconciliados": {nombre: round(float(y_tilde[i, 0]), 2) for i, nombre in enumerate(self.nombres_todas)},
            "pronosticos_originales_y_hat": {nombre: round(float(y_hat[i, 0]), 2) for i, nombre in enumerate(self.nombres_todas)},
            "ajuste_neto_mintrace": {nombre: round(float(y_tilde[i, 0] - y_hat[i, 0]), 2) for i, nombre in enumerate(self.nombres_todas)},
            "error_coherencia_sumacion": round(float(error_coherencia), 8),
            "es_perfectamente_coherente": bool(error_coherencia < 1e-4)
        }

if __name__ == "__main__":
    reconciliador = ReconciliadorJerarquicoINV()
    
    # Supongamos pronósticos incoherentes generados independientemente por 11 modelos distintos (en miles de hectolitros)
    y_hat_raw = [
        820.0, # Total predicho directo por modelo Macro
        540.0, 310.0, # MI y EXP (suman 850 != 820)
        330.0, 240.0,
        210.0, 220.0, 110.0, # Base MI (suman 540)
        140.0, 110.0, 70.0   # Base EXP (suman 320 != 310)
    ]
    
    res = reconciliador.reconciliar_mintrace(y_hat_raw)
    print("=== RECONCILIACIÓN JERÁRQUICA MINTRACE (INV) ===")
    print("Total Nacional Reconciliado:", res["pronosticos_reconciliados"]["Total_Nacional_INV"], "mil hl")
    print("Mercado Interno:", res["pronosticos_reconciliados"]["Canal_Mercado_Interno"], "mil hl")
    print("Exportación:", res["pronosticos_reconciliados"]["Canal_Exportacion"], "mil hl")
    print("¿Es perfectamente coherente?:", res["es_perfectamente_coherente"])
