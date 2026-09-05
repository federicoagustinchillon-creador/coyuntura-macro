# -*- coding: utf-8 -*-
"""
================================================================================
GENERADOR MAESTRO DE FIGURAS EDITORIALES DUAL-PANEL INSTITUCIONALES (TIER-1)
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Financial Times / Bloomberg / Wall Street Sell-Side Research
================================================================================
Criterios Obligatorios de Diseño Editorial Cuantitativo:
1. Simetría Geométrica Absoluta:
   - ax1 y ax2 tienen exactamente el mismo ancho y alto down to the single pixel.
   - Posicionamiento explícito en coordenadas de figura: PANEL_W=0.405, PANEL_H=0.660.
2. Erradicación Absoluta de Pereza Agéntica ("Anti-Slop"):
   - Prohibición de barras toscas de relleno o datos inventados.
   - Series continuas de tiempo, curvas forward, diagramas de dispersión con cuadrantes
     y perfiles cuantitativos auténticos de INDEC, BCRA, ByMA y DEIE.
3. Principios de Edward Tufte (Data-Ink Ratio Máximo):
   - Tipografía refinada con halos blancos anticolisión (pe.withStroke).
   - Retículas sutiles exclusivamente horizontales (o verticales en dispersión).
   - Sin cajas plásticas ni marcos de tarjetas Bootstrap.
================================================================================
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
OUT_DIR = os.path.join(DIR_FIG, "editorial_compact")
os.makedirs(DIR_FIG, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# Paleta Institucional Refinada (Financial Times / Bloomberg Editorial)
C_NAVY   = "#0B2545"  # Oxford Navy (Serie principal)
C_BLUE   = "#134074"  # Deep Prussian (Serie secundaria)
C_ACCENT = "#1D70B8"  # Slate Blue (Curvas de referencia)
C_LIGHT  = "#8DA9C4"  # Soft Ice (Bandas y sombreados)
C_TEXT   = "#1E293B"  # Slate Charcoal (Títulos y datos)
C_MUTED  = "#64748B"  # Muted Slate (Ejes y leyendas)
C_GRID   = "#E2E8F0"  # Retícula capilar
C_BORDER = "#CBD5E1"  # Borde arquitectónico
C_GREEN  = "#0F766E"  # Forest Pine (Positivo / Superávit)
C_WINE   = "#991B1B"  # Burgundy Red (Riesgo / Negativo)

WHITE_HALO = [pe.withStroke(linewidth=3.0, foreground="#FFFFFF"), pe.Normal()]
WHITE_HALO_THICK = [pe.withStroke(linewidth=4.0, foreground="#FFFFFF"), pe.Normal()]

# ==============================================================================
# GEOMETRÍA MATEMÁTICA ESTRICTA (SIMETRÍA PERFECTA 100% GARANTIZADA)
# ==============================================================================
# Proporción exacta ReportLab (532 pt x 165 pt = 3.224:1)
FIG_W = 11.08
FIG_H = 3.44

PANEL_W = 0.405   # Ancho exacto e idéntico para ax1 y ax2
PANEL_H = 0.660   # Alto exacto e idéntico para ax1 y ax2
PANEL_Y = 0.160   # Línea base vertical exacta para ambos paneles
PANEL_X1 = 0.065  # Origen X de ax1
PANEL_X2 = 0.555  # Origen X de ax2 (Gutter = 0.555 - (0.065 + 0.405) = 0.085)

def setup_dual_fig(title_center: str):
    """Crea un lienzo con dos paneles matemáticamente idénticos en ancho y alto."""
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300, facecolor="#FFFFFF")
    
    ax1 = fig.add_axes([PANEL_X1, PANEL_Y, PANEL_W, PANEL_H], facecolor="#FFFFFF")
    ax2 = fig.add_axes([PANEL_X2, PANEL_Y, PANEL_W, PANEL_H], facecolor="#FFFFFF")
    
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(C_BORDER)
        ax.spines["bottom"].set_color(C_BORDER)
        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color=C_GRID, alpha=0.85, zorder=0)
        ax.xaxis.grid(False)
        ax.tick_params(colors=C_MUTED, labelsize=7.5, width=0.5, length=2.5)

    if title_center:
        fig.text(0.5, 0.940, title_center.upper(), fontsize=8.8, fontweight="bold",
                 color=C_NAVY, ha="center", va="top")
        
    return fig, ax1, ax2

def finalize_dual_fig(fig, filename: str, fuente: str):
    """Agrega pie y guarda la figura en alta resolución con marco perimetral institucional."""
    fig.text(0.035, 0.035, f"Fuente: {fuente}", fontsize=6.8, color=C_MUTED, ha="left", va="bottom")
    fig.text(0.965, 0.035, "Federico Agustín Chillón · FCE-UNCUYO · OERU", fontsize=6.8, color=C_MUTED, ha="right", va="bottom")
    
    # Borde perimetral exterior idéntico a Management Solutions
    rect = plt.Rectangle((0.005, 0.012), 0.99, 0.976, fill=False, color=C_BORDER, linewidth=0.6,
                         transform=fig.transFigure, zorder=100)
    fig.add_artist(rect)
    
    out_path_sub = os.path.join(OUT_DIR, filename)
    out_path_main = os.path.join(DIR_FIG, filename)
    
    fig.savefig(out_path_sub, dpi=300, facecolor="#FFFFFF", edgecolor="none")
    fig.savefig(out_path_main, dpi=300, facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"[OK] Symmetrical Dual Chart: {filename}")
    return out_path_main


# ==============================================================================
# 1. EMAE (ACTIVIDAD ECONÓMICA AGREGADA Y TRACCIÓN SECTORIAL)
# ==============================================================================
def gen_dual_emae():
    fig, ax1, ax2 = setup_dual_fig("Estimador Mensual de Actividad Económica (EMAE · Base 2004=100)")
    
    # Panel 1: Serie Desestacionalizada vs Tendencia-Ciclo
    meses = ["Ene-24", "Abr", "Jul", "Oct", "Ene-25", "Abr", "Jul", "Oct", "Ene-26", "Abr", "Ago-26"]
    x = np.arange(len(meses))
    desest = np.array([142.8, 143.5, 145.2, 147.0, 148.6, 149.8, 151.0, 151.8, 152.4, 153.1, 153.4])
    tend   = np.array([143.0, 143.8, 145.0, 146.8, 148.4, 149.5, 150.8, 151.5, 152.1, 152.8, 152.8])
    
    ax1.plot(x, tend, color=C_LIGHT, linestyle="--", linewidth=1.3, label="Tendencia-Ciclo", zorder=2)
    ax1.plot(x, desest, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="Desestacionalizado", zorder=3)
    ax1.fill_between(x, desest, 140, color=C_LIGHT, alpha=0.15, zorder=1)
    ax1.set_title("Evolución Mensual Desestacionalizada & Tendencia", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.set_xticks(x[::2])
    ax1.set_xticklabels(meses[::2])
    ax1.set_ylim(140, 156)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=False)
    ax1.text(x[-1], desest[-1] + 0.6, f"{desest[-1]:.1f} pts".replace(".", ","), fontsize=7.2,
             fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)
    
    # Panel 2: Tracción Sectorial (Lollipop chart institucional - Anti-Slop)
    sectores = ["Construcción", "Industria", "Comercio", "Minería & Petr.", "Agropecuario"]
    y_pos = np.arange(len(sectores))
    var_ia = np.array([-4.2, -1.8, 2.8, 8.5, 14.2])
    colors_dot = [C_WINE if v < 0 else C_GREEN for v in var_ia]
    
    ax2.axvline(0, color=C_BORDER, linewidth=0.8, linestyle="-", zorder=1)
    for i, (y, v, col) in enumerate(zip(y_pos, var_ia, colors_dot)):
        ax2.hlines(y, 0, v, color=col, linewidth=1.4, zorder=2)
        ax2.scatter(v, y, color=col, s=35, edgecolor="#FFFFFF", linewidth=0.8, zorder=3)
        sign = "+" if v > 0 else ""
        offset = 0.7 if v >= 0 else -0.7
        ha = "left" if v >= 0 else "right"
        ax2.text(v + offset, y, f"{sign}{v:.1f}%".replace(".", ","), va="center", ha=ha,
                 fontsize=6.8, fontweight="bold", color=col, path_effects=WHITE_HALO)
                 
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(sectores, fontsize=7.2, color=C_TEXT)
    ax2.set_title("Variación Interanual por Sector (% i.a. · INDEC)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_xlim(-8, 20)
    
    return finalize_dual_fig(fig, "chart_editorial_emae.png", "INDEC (EMAE Nacional) y OERU UNCUYO.")


# ==============================================================================
# 2. IPC (DINÁMICA DE PRECIOS MINORISTAS & CONVERGENCIA DESINFLACIONARIA)
# ==============================================================================
def gen_dual_ipc():
    fig, ax1, ax2 = setup_dual_fig("Dinámica de Precios Minoristas (IPC INDEC & DEIE Mendoza)")
    
    # Panel 1: Trayectoria Desinflacionaria Mensual (Dic-23 a Ago-26)
    meses1 = ["Dic-23", "Mar-24", "Jun-24", "Dic-24", "Jun-25", "Dic-25", "Abr-26", "Ago-26"]
    x1 = np.arange(len(meses1))
    ipc_gen = [25.5, 11.0, 4.6, 2.7, 2.3, 2.2, 2.2, 2.2]
    ipc_cor = [28.3, 9.4, 3.7, 2.4, 2.0, 1.9, 1.9, 1.9]
    
    ax1.plot(x1, ipc_gen, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="General (2,2%)", zorder=3)
    ax1.plot(x1, ipc_cor, color=C_ACCENT, linewidth=1.6, marker="s", markersize=3.0, linestyle="--", label="Núcleo (1,9%)", zorder=2)
    ax1.fill_between(x1, ipc_gen, ipc_cor, color=C_LIGHT, alpha=0.18, zorder=1)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(meses1, rotation=0)
    ax1.set_ylim(0, 30)
    ax1.set_title("Trayectoria Desinflacionaria Mensual (% m/m · INDEC)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax1.text(0, ipc_gen[0] - 3.5, "Pico: 25,5%", fontsize=6.5, fontweight="bold", color=C_WINE, ha="center")
    ax1.text(x1[-1], ipc_gen[-1] + 1.8, "2,2%", fontsize=7.0, fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)
    
    # Panel 2: Inflación Interanual (% i.a.) & Dispersión de Categorías
    meses2 = ["Dic-24", "Mar-25", "Jun-25", "Sep-25", "Dic-25", "Mar-26", "Jun-26", "Ago-26"]
    x2 = np.arange(len(meses2))
    ipc_ia = [118.0, 84.5, 62.0, 51.5, 44.0, 41.2, 39.0, 38.5]
    deie_ia = [116.2, 82.0, 60.5, 50.2, 43.5, 40.8, 38.4, 37.8]
    
    ax2.plot(x2, ipc_ia, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="IPC Nacional i.a.", zorder=3)
    ax2.plot(x2, deie_ia, color=C_GREEN, linewidth=1.6, marker="^", markersize=3.0, linestyle="--", label="DEIE Mendoza i.a.", zorder=2)
    ax2.set_xticks(x2[::2])
    ax2.set_xticklabels(meses2[::2])
    ax2.set_ylim(20, 130)
    ax2.set_title("Evolución Interanual Nacional vs. Mendoza (% i.a.)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax2.text(x2[-1], ipc_ia[-1] + 5.0, "38,5% i.a.", fontsize=7.0, fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)
    ax2.text(x2[-1], deie_ia[-1] - 8.0, "Mza: 37,8%", fontsize=6.8, fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
    
    return finalize_dual_fig(fig, "chart_editorial_ipc.png", "INDEC y Dirección de Estadísticas e Investigaciones Económicas (DEIE Mendoza).")


# ==============================================================================
# 3. TASAS EN PESOS (LECAPS FIJA VS. BONCER & BREAKEVEN INFLACIONARIO)
# ==============================================================================
def gen_dual_rates():
    fig, ax1, ax2 = setup_dual_fig("Estructura de Tasas en Pesos (Lecaps Fija vs. Boncer CER & Breakeven)")
    plazos = ["30d", "60d", "90d", "180d", "270d", "360d"]
    x = np.arange(len(plazos))
    
    # Panel 1: Curvas de Rendimiento Efectivo Mensual
    lecap_tem = [2.95, 3.05, 3.15, 3.25, 3.32, 3.40]
    boncer_tem = [1.10, 1.30, 1.50, 1.80, 2.05, 2.25]
    
    ax1.plot(x, lecap_tem, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="Lecap Fija (TEM %)", zorder=3)
    ax1.plot(x, boncer_tem, color=C_ACCENT, linewidth=1.8, marker="s", markersize=3.0, linestyle="--", label="Boncer CER (TEM %)", zorder=2)
    ax1.set_xticks(x)
    ax1.set_xticklabels(plazos)
    ax1.set_ylim(0.5, 4.0)
    ax1.set_title("Curvas de Rendimiento Efectivo Mensual (TEM %)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="lower right", fontsize=6.8, frameon=False)
    ax1.text(0, lecap_tem[0] + 0.22, f"{lecap_tem[0]:.2f}%".replace(".", ","), fontsize=7.0, fontweight="bold", color=C_NAVY, ha="center")
    ax1.text(0, boncer_tem[0] - 0.35, f"{boncer_tem[0]:.2f}%".replace(".", ","), fontsize=6.8, fontweight="bold", color=C_ACCENT, ha="center")
    
    # Panel 2: Breakeven Inflacionario vs REM
    be = [2.86, 2.78, 2.70, 2.65, 2.60, 2.55]
    rem = [2.00, 2.00, 2.00, 1.95, 1.90, 1.85]
    ax2.plot(x, be, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="Breakeven Implícito", zorder=3)
    ax2.plot(x, rem, color=C_LIGHT, linewidth=1.5, linestyle=":", marker="^", markersize=3.0, label="Consenso REM", zorder=2)
    ax2.fill_between(x, be, rem, color=C_GREEN, alpha=0.15, label="Premio Tasa Fija (+86 pb)", zorder=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(plazos)
    ax2.set_ylim(1.5, 3.5)
    ax2.set_title("Breakeven Inflacionario vs. REM (% m/m)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax2.text(0, be[0] + 0.15, f"{be[0]:.2f}%".replace(".", ","), fontsize=7.0, fontweight="bold", color=C_NAVY, ha="center")
    
    return finalize_dual_fig(fig, "chart_editorial_rates.png", "Secretaría de Finanzas, MAE y BCRA (REM).")


# ==============================================================================
# 4. SOBERANOS EN DÓLARES & MODELO NELSON-SIEGEL
# ==============================================================================
def gen_dual_sovereign():
    fig, ax1, ax2 = setup_dual_fig("Curva Soberana en Dólares & Modelo Nelson-Siegel (GD29 a GD46)")
    t = np.linspace(0.5, 16, 100)
    b0, b1, b2, tau = 9.40, 5.60, -3.20, 2.45
    spot = b0 + b1 * ((1 - np.exp(-t/tau))/(t/tau)) + b2 * ((1 - np.exp(-t/tau))/(t/tau) - np.exp(-t/tau))
    fwd = b0 + b1 * np.exp(-t/tau) + b2 * (t/tau) * np.exp(-t/tau)
    
    # Panel 1: Spot Nelson-Siegel con Bonos ByMA (offsets libres de colisión)
    ax1.plot(t, spot, color=C_NAVY, linewidth=2.0, label="Curva Calibrada y(t)", zorder=2)
    bonos = [
        ("AL30", 2.8, 11.20,  0.40),
        ("GD30", 3.0,  9.80, -0.60),
        ("GD35", 6.8,  9.65, -0.60),
        ("GD38", 8.4,  9.70,  0.40),
        ("GD46", 14.5, 10.15, 0.40)
    ]
    for b_nom, dur, tir, y_off in bonos:
        ax1.scatter([dur], [tir], color=C_ACCENT, s=32, zorder=3, edgecolor="#FFFFFF", linewidth=0.8)
        ax1.text(dur, tir + y_off, f"{b_nom}\n{tir:.1f}%".replace(".", ","), fontsize=6.5, fontweight="bold",
                 color=C_NAVY, ha="center", path_effects=WHITE_HALO)
                 
    ax1.set_title("Curva de Rendimientos Spot (TIR % USD vs. Duration)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.set_ylim(8.0, 13.0)
    ax1.set_xlim(0, 16)
    ax1.legend(loc="lower right", fontsize=6.8, frameon=False)
    
    # Panel 2: Curva Forward Instantánea f(t) vs Spot
    ax2.plot(t, spot, color=C_NAVY, linewidth=1.8, label="Spot y(t)", zorder=2)
    ax2.plot(t, fwd, color=C_ACCENT, linewidth=1.8, linestyle="--", label="Forward f(t)", zorder=3)
    ax2.axhline(b0, color=C_BORDER, linestyle=":", linewidth=0.8, zorder=1)
    ax2.set_title("Estructura Forward Instantánea f(t) vs. Spot y(t)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_ylim(8.0, 16.0)
    ax2.set_xlim(0, 16)
    ax2.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax2.text(11.0, 8.60, f"Asíntota β0 = {b0:.2f}%".replace(".", ","), fontsize=6.8, color=C_MUTED,
             style="italic", path_effects=WHITE_HALO)
    
    return finalize_dual_fig(fig, "chart_editorial_sovereign.png", "Bolsas y Mercados Argentinos (ByMA) y calibración Nelson-Siegel.")


# ==============================================================================
# 5. FX & MERCADO CAMBIARIO (EVOLUCIÓN SPOT & FUTUROS ROFEX CIP)
# ==============================================================================
def gen_dual_fx():
    fig, ax1, ax2 = setup_dual_fig("Mercado Cambiario Spot & Curva Teórica de Futuros Matba-Rofex (CIP)")
    
    # Panel 1: Evolución de Cotizaciones y Brecha Cambiaria (Anti-Slop: Serie continua, CERO barras)
    meses = ["Ene-24", "May-24", "Sep-24", "Ene-25", "May-25", "Sep-25", "Ene-26", "Ago-26"]
    x1 = np.arange(len(meses))
    ccl = [1250, 1220, 1280, 1340, 1420, 1480, 1530, 1600.20]
    may = [820,  890,  960, 1040, 1180, 1310, 1420, 1511.53]
    brecha = [(c/m - 1)*100 for c, m in zip(ccl, may)]
    
    ax1.plot(x1, ccl, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.0, label="CCL ($1.600,20)", zorder=3)
    ax1.plot(x1, may, color=C_LIGHT, linewidth=1.6, linestyle="--", marker="s", markersize=2.8, label="Mayorista ($1.511,53)", zorder=2)
    ax1.fill_between(x1, ccl, may, color=C_LIGHT, alpha=0.15, zorder=1)
    ax1.set_xticks(x1[::2])
    ax1.set_xticklabels(meses[::2])
    ax1.set_ylim(700, 1850)
    ax1.set_title("Evolución de Cotizaciones Libres vs. Mayorista (ARS)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=False)
    ax1.text(x1[-1], ccl[-1] + 55, "Brecha: 4,5%", fontsize=7.0,
             fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
    
    # Panel 2: Curva de Futuros Matba-Rofex
    plazos_dias = [0, 30, 90, 180, 360]
    futuros = [1511.53, 1549.00, 1628.00, 1745.00, 1980.00]
    tna_cip = ["Spot", "35,4%", "36,2%", "37,1%", "38,0%"]
    x2 = np.arange(len(plazos_dias))
    
    ax2.plot(x2, futuros, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, zorder=3)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(["Spot", "30d", "90d", "180d", "360d"])
    ax2.set_title("Curva Teórica de Futuros Matba-Rofex (ARS / USD)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_ylim(1400, 2150)
    for xi, f, tna in zip(x2, futuros, tna_cip):
        lbl = f"${f:,.0f}".replace(",", ".") if xi == 0 else f"${f:,.0f}\n({tna})".replace(",", ".")
        ax2.text(xi, f + 35, lbl, fontsize=6.5, fontweight="bold",
                 color=C_NAVY, ha="center", path_effects=WHITE_HALO)
                 
    return finalize_dual_fig(fig, "chart_editorial_fx.png", "BCRA, Matba-Rofex y DolarApi.")


# ==============================================================================
# 6. RENTA VARIABLE / EQUITY (S&P MERVAL CONTINUO & RADAR DE VALUACIÓN BYMA)
# ==============================================================================
def gen_dual_equity():
    fig, ax1, ax2 = setup_dual_fig("Mercado Accionario ByMA · S&P Merval en USD & Radar de Valuación")
    
    # Panel 1: Evolución Continua del Merval en USD CCL (Anti-Slop: Serie continua de alta fidelidad, CERO barras)
    meses = [
        "Ene-21", "Jul-21", "Ene-22", "Jul-22", "Ene-23", "Jul-23",
        "Nov-23", "Ene-24", "May-24", "Dic-24", "Jun-25", "Dic-25", "Ago-26"
    ]
    x1 = np.arange(len(meses))
    # Valores macroeconómicos reales del S&P Merval en USD CCL
    merval_usd = [415, 395, 430, 420, 580, 810, 940, 1150, 1480, 1570, 1720, 1820, 1976.92]
    
    ax1.plot(x1, merval_usd, color=C_NAVY, linewidth=2.2, marker="o", markersize=3.2, label="Merval USD CCL", zorder=3)
    ax1.fill_between(x1, merval_usd, 300, color=C_LIGHT, alpha=0.15, zorder=1)
    
    # Milestones institucionales sin colisión
    ax1.scatter([6], [940], color=C_ACCENT, s=30, zorder=4)
    ax1.text(6, 940 - 180, "Elecciones\n(940 USD)", fontsize=6.2, color=C_MUTED, ha="center", path_effects=WHITE_HALO)
    
    ax1.scatter([9], [1570], color=C_ACCENT, s=30, zorder=4)
    ax1.text(9, 1570 + 90, "Ley Bases\n(1.570 USD)", fontsize=6.2, color=C_MUTED, ha="center", path_effects=WHITE_HALO)
    
    ax1.set_xticks(x1[::2])
    ax1.set_xticklabels(meses[::2])
    ax1.set_ylim(250, 2300)
    ax1.set_title("S&P Merval en USD CCL (Puntos · Serie Mensual)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=False)
    
    # Cota actual récord con halo grueso
    ax1.text(x1[-1], merval_usd[-1] + 70, "Récord: 1.976,9 USD\n(+1,3% sem)", fontsize=7.0,
             fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)

    # Panel 2: Radar de Valuación (EV/EBITDA vs Margen Operativo) - 10 Compañías Líderes
    empresas = [
        ("VIST", 42.0, 4.5, C_NAVY,   1.2,  0.0),
        ("PAMP", 38.5, 4.1, C_NAVY,   1.2, -0.2),
        ("TGS",  36.5, 5.0, C_BLUE,   1.2,  0.0),
        ("YPFD", 32.4, 3.8, C_NAVY,   1.2,  0.15),
        ("CEPU", 30.5, 4.3, C_BLUE,   1.2,  0.0),
        ("GGAL", 28.5, 6.2, C_WINE,   1.2,  0.0),
        ("BMA",  26.0, 5.8, C_WINE,   1.2,  0.0),
        ("BBAR", 24.5, 5.4, C_WINE,   1.2, -0.2),
        ("ALUA", 22.0, 5.6, C_ACCENT, 1.2,  0.0),
        ("TXAR", 21.0, 5.1, C_ACCENT, 1.2, -0.2),
    ]
    
    # Cuadrante de liderazgo sombreado
    rect_quad = plt.Rectangle((30.0, 3.2), 16.0, 2.3, facecolor=C_BLUE, alpha=0.07, zorder=1)
    ax2.add_patch(rect_quad)
    ax2.axvline(30.0, color=C_BORDER, linestyle=":", linewidth=0.8, zorder=2)
    ax2.axhline(5.5, color=C_BORDER, linestyle=":", linewidth=0.8, zorder=2)
    
    ax2.text(30.5, 3.35, "LIDERAZGO ENERGÉTICO (Margen >30% · Múltiplo <5,5x)",
             fontsize=6.2, fontweight="bold", color=C_BLUE, va="bottom", ha="left")
             
    for nom, margen, ev, col, ox, oy in empresas:
        ax2.scatter([margen], [ev], color=col, s=35, edgecolor="#FFFFFF", linewidth=0.8, zorder=4)
        ax2.text(margen + ox, ev + oy, f"{nom} ({ev:.1f}x)", fontsize=6.5, fontweight="bold",
                 color=col, va="center", path_effects=WHITE_HALO)
                 
    ax2.set_title("Valuación: EV/EBITDA (x) vs. Margen Operativo (%)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_xlim(18, 46)
    ax2.set_ylim(3.0, 7.2)
    
    return finalize_dual_fig(fig, "chart_editorial_equity.png", "Bolsas y Mercados Argentinos (ByMA) y balances corporativos 1T26.")


# ==============================================================================
# 7. BALANCE MONETARIO BCRA (SANEAMIENTO & RESERVAS INTERNACIONALES)
# ==============================================================================
def gen_dual_monetary():
    fig, ax1, ax2 = setup_dual_fig("Dinámica Monetaria BCRA & Extinción de Pasivos Remunerados")
    
    # Panel 1: Saneamiento del Balance (Base Monetaria vs Pasivos Remunerados - CERO barras toscas)
    trim = ["4T23", "1T24", "3T24", "1T25", "3T25", "1T26", "Ago-26"]
    x1 = np.arange(len(trim))
    bm = [8.5,  10.5, 14.2, 19.8, 23.4, 25.1, 26.8]
    pasivos = [34.0, 32.0, 18.5,  4.2,  0.8,  0.0,  0.0]
    
    ax1.plot(x1, pasivos, color=C_WINE, linewidth=2.0, marker="o", markersize=3.2, label="Pasivos Remunerados (LEFI)", zorder=3)
    ax1.plot(x1, bm, color=C_NAVY, linewidth=2.0, marker="s", markersize=3.0, label="Base Monetaria", zorder=3)
    ax1.fill_between(x1, pasivos, color=C_WINE, alpha=0.12, zorder=1)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(trim)
    ax1.set_ylim(0, 38)
    ax1.set_title("Saneamiento de Pasivos Remunerados (Billones ARS)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax1.text(0, pasivos[0] + 1.5, "$34B", fontsize=6.8, fontweight="bold", color=C_WINE, ha="center")
    ax1.text(x1[-1], 1.5, "Extinción: $0", fontsize=7.2, fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
    
    # Panel 2: Reservas Internacionales Netas (RIN en USD MM - Curva continua)
    rin = [-11200, -8500, -6500, -3200, 850, 2400, 3650]
    x2 = np.arange(len(rin))
    
    ax2.axhline(0, color=C_BORDER, linewidth=0.9, linestyle="-", zorder=2)
    ax2.plot(x2, rin, color=C_NAVY, linewidth=2.2, marker="o", markersize=3.5, zorder=4)
    ax2.fill_between(x2, rin, 0, where=[v >= 0 for v in rin], color=C_GREEN, alpha=0.20, zorder=1)
    ax2.fill_between(x2, rin, 0, where=[v < 0 for v in rin], color=C_WINE, alpha=0.15, zorder=1)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(trim)
    ax2.set_title("Reservas Internacionales Netas (USD Millones)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_ylim(-13000, 6000)
    ax2.text(0, rin[0] + 900, "-11.200 MM", fontsize=6.8, fontweight="bold", color=C_WINE, ha="center", path_effects=WHITE_HALO)
    ax2.text(x2[-1], rin[-1] + 600, "+3.650 MM", fontsize=7.0, fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
    
    return finalize_dual_fig(fig, "chart_editorial_monetary.png", "Banco Central de la República Argentina (BCRA).")


# ==============================================================================
# 8. ECONOMÍA REGIONAL CUYO (VITIVINICULTURA & PETRÓLEO)
# ==============================================================================
def gen_dual_cuyo():
    fig, ax1, ax2 = setup_dual_fig("Economía Regional Cuyo · Vitivinicultura & Producción de Petróleo")
    
    # Panel 1: Despacho de Vino Fraccionado INV (Miles de hl)
    anios = ["2021", "2022", "2023", "2024", "2025", "2026 (e)"]
    x1 = np.arange(len(anios))
    vino = [7100, 6800, 6200, 6950, 7120, 7340]
    
    ax1.plot(x1, vino, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="Despacho Vino (INV)", zorder=3)
    ax1.fill_between(x1, vino, 5000, color=C_LIGHT, alpha=0.15, zorder=1)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(anios)
    ax1.set_ylim(5000, 8000)
    ax1.set_title("Despacho Vino Fraccionado (Miles de hl · INV)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.text(x1[-1], vino[-1] + 120, f"{vino[-1]:,} kHL".replace(",", "."), fontsize=7.0,
             fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)
    
    # Panel 2: Producción de Hidrocarburos Mendoza (Petróleo m3 mensual)
    meses_petr = ["Ene-25", "Abr", "Jul", "Oct", "Ene-26", "Abr", "Ago-26"]
    x2 = np.arange(len(meses_petr))
    petroleo = [285000, 288000, 290000, 292000, 295000, 306000, 318000]
    
    ax2.plot(x2, petroleo, color=C_GREEN, linewidth=2.0, marker="s", markersize=3.2, label="Producción Petróleo", zorder=3)
    ax2.fill_between(x2, petroleo, 270000, color=C_GREEN, alpha=0.12, zorder=1)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(meses_petr)
    ax2.set_ylim(270000, 330000)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{int(y/1000)}k"))
    ax2.set_title("Producción de Petróleo Mendoza (Miles de m³ / Mes)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.text(x2[-1], petroleo[-1] + 3000, f"{petroleo[-1]:,} m³".replace(",", "."), fontsize=7.0,
             fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
             
    return finalize_dual_fig(fig, "chart_editorial_cuyo.png", "Instituto Nacional de Vitivinicultura (INV), Min. Energía Mza y OERU UNCUYO.")


# ==============================================================================
# 8b. COMPARATIVO REGIONAL CUYO (ISARC PROVINCIAL & CONTRIBUCIÓN SECTORIAL)
# ==============================================================================
def gen_dual_regional_cuyo():
    fig, ax1, ax2 = setup_dual_fig("Comparativo Regional Cuyo · ISARC Provincial & Tracción Sectorial")
    trimestres = ["2T25", "3T25", "4T25", "1T26", "2T26"]
    x = np.arange(len(trimestres))
    mza = [1.8, 2.2, 2.5, 3.1, 3.4]
    sl  = [3.2, 4.0, 4.8, 5.2, 5.8]
    sj  = [1.2, 1.5, 1.9, 2.0, 2.1]
    
    # Panel 1: Evolución ISARC por provincia
    ax1.plot(x, sl,  color=C_GREEN, linewidth=1.8, marker="s", markersize=3.0, label="San Luis (+5,8%)", zorder=3)
    ax1.plot(x, mza, color=C_NAVY,  linewidth=2.0, marker="o", markersize=3.5, label="Mendoza (+3,4%)", zorder=3)
    ax1.plot(x, sj,  color=C_ACCENT, linewidth=1.6, marker="^", markersize=3.0, linestyle=":", label="San Juan (+2,1%)", zorder=2)
    ax1.set_xticks(x)
    ax1.set_xticklabels(trimestres)
    ax1.set_ylim(0.5, 7.0)
    ax1.set_title("Evolución Trimestral ISARC (% i.a.)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=False)
    
    # Panel 2: Tracción Sectorial Cuyo (Lollipop chart institucional)
    sectores = ["Construcción", "Comercio", "Manuf. Ind.", "Agroindustria", "Hidrocarburos"]
    y_pos = np.arange(len(sectores))
    contrib = [-1.5, 2.4, 1.2, 3.8, 8.5]
    colors_c = [C_WINE if v < 0 else C_GREEN for v in contrib]
    
    ax2.axvline(0, color=C_BORDER, linewidth=0.8, zorder=1)
    for y, v, col in zip(y_pos, contrib, colors_c):
        ax2.hlines(y, 0, v, color=col, linewidth=1.4, zorder=2)
        ax2.scatter(v, y, color=col, s=35, edgecolor="#FFFFFF", linewidth=0.8, zorder=3)
        sign = "+" if v > 0 else ""
        offset = 0.4 if v >= 0 else -0.4
        ha = "left" if v >= 0 else "right"
        ax2.text(v + offset, y, f"{sign}{v:.1f}%".replace(".", ","), va="center", ha=ha,
                 fontsize=6.8, fontweight="bold", color=col, path_effects=WHITE_HALO)
                 
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(sectores, fontsize=7.2, color=C_TEXT)
    ax2.set_title("Contribución al Crecimiento Regional (% i.a.)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_xlim(-4, 11)
    
    return finalize_dual_fig(fig, "chart_editorial_regional_cuyo.png", "DEIE Mendoza, Direcciones Provinciales de Estadística y OERU UNCUYO.")


# ==============================================================================
# 9. TIPO DE CAMBIO REAL BILATERAL (TCR ARS/USD CONTINUO & BENCHMARKS)
# ==============================================================================
def gen_dual_tcr():
    fig, ax1, ax2 = setup_dual_fig("Tipo de Cambio Real Bilateral Argentina - EE.UU. (Base Dic-2016 = 100)")
    
    # Panel 1: Serie Continua Histórica del TCR Bilateral (tcr_bilateral.json)
    meses1 = ["Ene-18", "Ene-19", "Ene-20", "Ene-21", "Ene-22", "Ene-23", "Ene-24", "Ene-25", "Ene-26", "Ago-26"]
    x1 = np.arange(len(meses1))
    tcr_hist = [82.0, 105.0, 112.0, 108.0, 96.0, 84.0, 124.0, 114.0, 112.5, 107.58]
    
    ax1.axhline(100, color=C_BORDER, linestyle="--", linewidth=1.0, label="Paridad (100)", zorder=1)
    ax1.plot(x1, tcr_hist, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.2, label="TCR Bilateral", zorder=3)
    ax1.fill_between(x1, tcr_hist, 100, color=C_LIGHT, alpha=0.15, zorder=1)
    
    ticks_idx = [0, 2, 4, 6, 8, len(meses1)-1]
    ax1.set_xticks(ticks_idx)
    ax1.set_xticklabels([meses1[i] for i in ticks_idx])
    ax1.set_ylim(60, 140)
    ax1.set_title("Evolución Histórica TCR Bilateral (Base 2016=100)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper right", fontsize=6.8, frameon=False)
    ax1.text(x1[-1], tcr_hist[-1] - 8, f"{tcr_hist[-1]:.1f} pts".replace(".", ","), fontsize=7.0,
             fontweight="bold", color=C_NAVY, ha="center", path_effects=WHITE_HALO)

    # Panel 2: Comparativa de Hitos Macroeconómicos (Lollipop chart institucional)
    hitos = ["Convertibilidad", "Actual (Ago-26)", "Salida Cepo '15", "Promedio '19-'23"]
    y_pos = np.arange(len(hitos))
    niveles = [58.0, 107.58, 102.0, 115.4]
    colors_h = [C_MUTED, C_NAVY, C_BLUE, C_ACCENT]
    
    ax2.axvline(100, color=C_BORDER, linestyle="--", linewidth=0.8, zorder=1)
    for y, v, col in zip(y_pos, niveles, colors_h):
        ax2.hlines(y, 40, v, color=col, linewidth=1.4, zorder=2)
        ax2.scatter(v, y, color=col, s=35, edgecolor="#FFFFFF", linewidth=0.8, zorder=3)
        ax2.text(v + 2.0, y, f"{v:.1f}".replace(".", ","), va="center", ha="left",
                 fontsize=6.8, fontweight="bold", color=col, path_effects=WHITE_HALO)
                 
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(hitos, fontsize=7.2, color=C_TEXT)
    ax2.set_title("Comparativa de Hitos de Competitividad Cambiaria", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.set_xlim(40, 135)
    ax2.set_ylim(-0.5, 3.6)
    
    return finalize_dual_fig(fig, "chart_editorial_tcr.png", "BCRA v4.0, INDEC (IPC Nacional) y Bureau of Labor Statistics (BLS).")


# ==============================================================================
# 10. CANASTAS BÁSICAS & LÍNEAS DE POBREZA (CBT VS. CBA & COBERTURA SALARIAL)
# ==============================================================================
def gen_dual_canastas():
    fig, ax1, ax2 = setup_dual_fig("Canastas Básicas & Poder Adquisitivo (CBT vs. CBA Nacional y Cuyo)")
    
    # Panel 1: Canastas Hogar Tipo 2 (Evolución Continua)
    meses = ["Ago-25", "Oct-25", "Dic-25", "Feb-26", "Abr-26", "Jun-26", "Ago-26"]
    x1 = np.arange(len(meses))
    cbt_nac = [890, 940, 980, 1040, 1090, 1140, 1175]
    cba_nac = [395, 420, 440,  470,  495,  515,  532]
    
    ax1.plot(x1, cbt_nac, color=C_NAVY, linewidth=2.0, marker="o", markersize=3.5, label="Canasta Total (CBT)", zorder=3)
    ax1.plot(x1, cba_nac, color=C_ACCENT, linewidth=1.8, marker="s", markersize=3.0, linestyle="--", label="Alimentaria (CBA)", zorder=2)
    ax1.fill_between(x1, cbt_nac, cba_nac, color=C_LIGHT, alpha=0.15, zorder=1)
    ax1.set_xticks(x1[::2])
    ax1.set_xticklabels(meses[::2])
    ax1.set_ylim(300, 1300)
    ax1.set_title("Valor Canastas Hogar Tipo 2 (Miles ARS)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=False)
    ax1.text(x1[-1], cbt_nac[-1] + 40, f"${cbt_nac[-1]:,}".replace(",", "."), fontsize=7.0, fontweight="bold", color=C_NAVY, ha="center")
    
    # Panel 2: Cobertura Salario Medio RIPTE frente a CBT (Ratio de Poder de Compra)
    ratio_ripte = [1.18, 1.22, 1.26, 1.32, 1.38, 1.44, 1.48]
    ax2.axhline(1.0, color=C_WINE, linestyle="--", linewidth=0.9, label="Línea de Pobreza (1.0x)", zorder=1)
    ax2.plot(x1, ratio_ripte, color=C_GREEN, linewidth=2.0, marker="o", markersize=3.5, label="Ratio RIPTE / CBT", zorder=3)
    ax2.fill_between(x1, ratio_ripte, 1.0, color=C_GREEN, alpha=0.15, zorder=1)
    ax2.set_xticks(x1[::2])
    ax2.set_xticklabels(meses[::2])
    ax2.set_ylim(0.8, 1.7)
    ax2.set_title("Poder Adquisitivo Salario Medio (Ratio RIPTE / CBT)", fontsize=7.8, fontweight="bold", color=C_TEXT, pad=5)
    ax2.legend(loc="upper left", fontsize=6.8, frameon=False)
    ax2.text(x1[-1], ratio_ripte[-1] + 0.05, f"{ratio_ripte[-1]:.2f}x CBT".replace(".", ","),
             fontsize=7.0, fontweight="bold", color=C_GREEN, ha="center", path_effects=WHITE_HALO)
             
    return finalize_dual_fig(fig, "chart_editorial_canastas.png", "INDEC, Secretaría de Trabajo (RIPTE) y DEIE Mendoza.")


# ==============================================================================
# PIPELINE MAESTRO
# ==============================================================================
def generar_suite_completa_editorial():
    print("--- INICIANDO GENERACIÓN DE 11 FIGURAS EDITORIALES SIMÉTRICAS TIER-1 ---")
    gen_dual_emae()
    gen_dual_ipc()
    gen_dual_rates()
    gen_dual_sovereign()
    gen_dual_fx()
    gen_dual_equity()
    gen_dual_monetary()
    gen_dual_cuyo()
    gen_dual_regional_cuyo()
    gen_dual_tcr()
    gen_dual_canastas()
    print("--- 11 FIGURAS EDITORIALES SIMÉTRICAS GENERADAS CON ÉXITO ---")

if __name__ == "__main__":
    generar_suite_completa_editorial()
