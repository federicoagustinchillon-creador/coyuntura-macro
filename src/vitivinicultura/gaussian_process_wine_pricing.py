# -*- coding: utf-8 -*-
"""
================================================================================
REGRESIÓN POR PROCESOS GAUSSIANOS (GPR) PARA VALUACIÓN Y GUARDA DE VINOS FINOS
================================================================================
Autor: Federico Agustín Chillón
Filiación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
================================================================================
Implementa GPR con un kernel compuesto Matérn 5/2 (envejecimiento estocástico)
y Kernel Periódico (ciclo anual de vendimia y lanzamientos en primeur),
proporcionando bandas de confianza bayesianas al 95%.
================================================================================
"""

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ExpSineSquared, WhiteKernel, ConstantKernel as C

class ValuadorGuardaGPR:
    def __init__(self):
        # Kernel: C * Matern(5/2) + C * ExpSineSquared(Periodic) + WhiteNoise
        k_matern = C(1.0, (1e-3, 1e3)) * Matern(length_scale=2.5, nu=2.5)
        k_periodic = C(0.5, (1e-3, 1e2)) * ExpSineSquared(length_scale=1.0, periodicity=1.0)
        k_noise = WhiteKernel(noise_level=0.05, noise_level_bounds=(1e-4, 1e0))
        self.kernel = k_matern + k_periodic + k_noise
        self.gpr = GaussianProcessRegressor(kernel=self.kernel, n_restarts_optimizer=5, normalize_y=True)
        self.is_fitted = False

    def entrenar_modelo_historico(self, anios_guarda, precios_relativos):
        X = np.array(anios_guarda).reshape(-1, 1)
        y = np.array(precios_relativos)
        self.gpr.fit(X, y)
        self.is_fitted = True

    def proyectar_trayectoria_con_incertidumbre(self, anios_futuros):
        if not self.is_fitted:
            # Calibración a priori estándar con datos estilizados de añejamiento en roble / estiba
            X_priori = np.array([0, 1, 2, 3, 5, 7, 10]).reshape(-1, 1)
            y_priori = np.array([1.0, 1.18, 1.38, 1.62, 2.25, 2.95, 4.10]) # Múltiplo sobre precio de lanzamiento
            self.entrenar_modelo_historico(X_priori, y_priori)

        X_eval = np.array(anios_futuros).reshape(-1, 1)
        mu, sigma = self.gpr.predict(X_eval, return_std=True)
        
        ic_inf = mu - 1.96 * sigma
        ic_sup = mu + 1.96 * sigma
        
        return {
            "anios": list(anios_futuros),
            "multiplo_esperado_media": [round(float(v), 3) for v in mu],
            "ic_95_inferior": [round(float(v), 3) for v in np.maximum(0.5, ic_inf)],
            "ic_95_superior": [round(float(v), 3) for v in ic_sup],
            "desvio_estandar_sigma": [round(float(v), 3) for v in sigma],
            "kernel_optimizado": str(self.gpr.kernel_)
        }

if __name__ == "__main__":
    valuador = ValuadorGuardaGPR()
    anios_proy = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    trayectoria = valuador.proyectar_trayectoria_con_incertidumbre(anios_proy)
    print("=== PROYECCIÓN DE VALOR EN CAVA (GPR MATÉRN 5/2 + PERIÓDICO) ===")
    for a, m, inf, sup in zip(trayectoria["anios"], trayectoria["multiplo_esperado_media"], trayectoria["ic_95_inferior"], trayectoria["ic_95_superior"]):
        print(f"  Año {a:2d} -> Múltiplo Esperado: {m:.2f}x  [IC 95%: {inf:.2f}x - {sup:.2f}x]")
