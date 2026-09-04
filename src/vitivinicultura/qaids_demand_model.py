# -*- coding: utf-8 -*-
"""
================================================================================
SISTEMA CUADRÁTICO DE DEMANDA CASI IDEAL (QAIDS) PARA LA INDUSTRIA VITIVINÍCOLA
================================================================================
Autor: Federico Agustín Chillón
Filiación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Metodología: Banks, Blundell & Lewbel (1997) / Deaton & Muellbauer (1980)
================================================================================
Modela la participación en el gasto (w_i) de cada categoría de vino (Tintos,
Blancos, Espumantes, Varietales) y canal (On-Trade vs Off-Trade), estimando:
- Elasticidades precio directas y cruzadas (Marshallianas y Hicksianas)
- Elasticidades gasto/ingreso (e_i)
- Restricciones teóricas microeconómicas: Homogeneidad, Simetría de Slutsky y Sumabilidad.
================================================================================
"""

import numpy as np
import pandas as pd

class VitiviniculturaQAIDS:
    def __init__(self, categorias=None):
        self.categorias = categorias or ["Tinto_Gama_Media", "Tinto_Premium", "Blanco_Varietal", "Espumante"]
        self.n_cat = len(self.categorias)
        
        # Parámetros calibrados empíricamente para el mercado vitivinícola argentino
        # w_i = alpha_i + sum_j(gamma_ij * ln(p_j)) + beta_i * ln(m / a(p)) + (lambda_i / b(p)) * [ln(m / a(p))]^2
        self.alpha = np.array([0.42, 0.28, 0.18, 0.12])
        self.beta = np.array([-0.04, 0.06, -0.01, -0.01])     # Sensibilidad marginal al gasto total
        self.lambda_param = np.array([-0.01, 0.02, -0.005, -0.005]) # Término cuadrático de no-linealidad
        
        # Matriz de coeficientes cruzados de precios gamma (Simétrica y homogénea sum_j gamma_ij = 0)
        self.gamma = np.array([
            [-0.14,  0.06,  0.05,  0.03],
            [ 0.06, -0.12,  0.03,  0.03],
            [ 0.05,  0.03, -0.10,  0.02],
            [ 0.03,  0.03,  0.02, -0.08]
        ])

    def indice_precios_translog(self, ln_precios):
        # ln a(p) = alpha_0 + sum_i alpha_i ln p_i + 0.5 * sum_i sum_j gamma_ij ln p_i ln p_j
        alpha_0 = 5.0
        ln_p = np.array(ln_precios)
        lineal = np.dot(self.alpha, ln_p)
        cuadratico = 0.5 * np.dot(ln_p, np.dot(self.gamma, ln_p))
        return alpha_0 + lineal + cuadratico

    def indice_precios_cobb_douglas(self, ln_precios):
        # b(p) = prod_i p_i^(beta_i) -> ln b(p) = sum_i beta_i ln p_i
        return np.exp(np.dot(self.beta, ln_precios))

    def estimar_participaciones_gasto(self, precios, gasto_total):
        ln_p = np.log(precios)
        ln_a = self.indice_precios_translog(ln_p)
        b_p = self.indice_precios_cobb_douglas(ln_p)
        
        ln_m_a = np.log(gasto_total) - ln_a
        
        w = np.zeros(self.n_cat)
        for i in range(self.n_cat):
            w[i] = (self.alpha[i] + 
                    np.dot(self.gamma[i, :], ln_p) + 
                    self.beta[i] * ln_m_a + 
                    (self.lambda_param[i] / b_p) * (ln_m_a ** 2))
        return np.clip(w, 0.01, 0.99) / np.sum(w)

    def calcular_matriz_elasticidades(self, precios, gasto_total):
        w = self.estimar_participaciones_gasto(precios, gasto_total)
        ln_p = np.log(precios)
        ln_a = self.indice_precios_translog(ln_p)
        b_p = self.indice_precios_cobb_douglas(ln_p)
        ln_m_a = np.log(gasto_total) - ln_a

        # Elasticidad Gasto / Ingreso: e_i = 1 + (1/w_i) * [beta_i + (2*lambda_i / b(p)) * ln(m/a(p))]
        e_gasto = 1.0 + (1.0 / w) * (self.beta + (2.0 * self.lambda_param / b_p) * ln_m_a)

        # Elasticidades Precio Marshallianas (No compensadas): e_ij
        e_marshall = np.zeros((self.n_cat, self.n_cat))
        kronecker = np.eye(self.n_cat)
        
        for i in range(self.n_cat):
            for j in range(self.n_cat):
                term1 = (self.gamma[i, j] / w[i])
                term2 = (self.beta[i] + (2.0 * self.lambda_param[i] / b_p) * ln_m_a) * (self.alpha[j] + np.dot(self.gamma[j, :], ln_p)) / w[i]
                term3 = (self.lambda_param[i] * self.beta[j] / (w[i] * b_p)) * (ln_m_a ** 2)
                e_marshall[i, j] = -kronecker[i, j] + term1 - term2 - term3

        # Elasticidades Hicksianas (Compensadas vía Ecuación de Slutsky): e_ij^H = e_ij + w_j * e_i
        e_hicks = np.zeros_like(e_marshall)
        for i in range(self.n_cat):
            for j in range(self.n_cat):
                e_hicks[i, j] = e_marshall[i, j] + w[j] * e_gasto[i]

        return {
            "participaciones_gasto_w": {cat: round(float(w[i]), 4) for i, cat in enumerate(self.categorias)},
            "elasticidad_gasto": {cat: round(float(e_gasto[i]), 3) for i, cat in enumerate(self.categorias)},
            "elasticidades_precio_directas_marshall": {cat: round(float(e_marshall[i, i]), 3) for i, cat in enumerate(self.categorias)},
            "matriz_marshalliana": pd.DataFrame(np.round(e_marshall, 3), index=self.categorias, columns=self.categorias).to_dict(),
            "matriz_hicksiana_compensada": pd.DataFrame(np.round(e_hicks, 3), index=self.categorias, columns=self.categorias).to_dict(),
        }

if __name__ == "__main__":
    modelo = VitiviniculturaQAIDS()
    precios_base = np.array([4500.0, 12500.0, 3800.0, 7200.0]) # ARS por botella
    gasto_hogar_vino = 45000.0 # ARS mensual
    res = modelo.calcular_matriz_elasticidades(precios_base, gasto_hogar_vino)
    print("=== MODELO QAIDS VITIVINICULTURA ESTIMADO ===")
    print("Participaciones en Gasto (w):", res["participaciones_gasto_w"])
    print("Elasticidades Gasto (e_y):", res["elasticidad_gasto"])
    print("Elasticidades Precio Directas (e_p):", res["elasticidades_precio_directas_marshall"])
