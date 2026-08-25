"""
================================================================================
PIPELINE GENERADOR DE INFOGRAFÍAS VECTORIALES MACROECONÓMICAS (300 DPI)
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Estándar: Institutional Tier / Precision Economics & Market Strategy
================================================================================
"""

import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
OUT_DIR = os.path.join(DIR_FIG, "master_extracted_images")
os.makedirs(OUT_DIR, exist_ok=True)

def cargar_datos_del_dia():
    """Fuente única de verdad de los datos del día, compartida con los pipelines."""
    candidatos = [
        os.path.join(BASE_DIR, "01_Bases_Datos", "datos_del_dia.json"),
        os.path.join(BASE_DIR, "datos_del_dia.json"),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

DATOS_DEL_DIA = cargar_datos_del_dia()

# Configuración tipográfica y de estilo global: Georgia (serif) institucional, sans-serif solo en ejes
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Georgia', 'DejaVu Serif', 'Times New Roman']
plt.rcParams['font.size'] = 8.0
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.left'] = True
plt.rcParams['axes.spines.bottom'] = True
plt.rcParams['axes.edgecolor'] = '#94A3B8'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#1E293B'
plt.rcParams['ytick.color'] = '#1E293B'
plt.rcParams['xtick.labelsize'] = 7.5
plt.rcParams['ytick.labelsize'] = 7.5

C_NAVY  = "#0B3C5D"
C_BLUE  = "#005B96"
C_CYAN  = "#328CC1"
C_TEAL  = "#0D9488"
C_RED   = "#991B1B"
C_AMBER = "#D97706"
C_SLATE = "#475569"
C_GRAY  = "#64748B"
C_GRID  = "#E2E8F0"

def create_master_infographic(filename, date_str, title_str, subtitle_str, kpis, plot_func, source_str, brand_str="UNCUYO"):
    fig = plt.figure(figsize=(10.64, 6.0), dpi=300, facecolor="#F0F4F8")
    
    # Fondo con gradiente sutil
    ax_bg = fig.add_axes([0, 0, 1, 1], zorder=-10)
    ax_bg.axis('off')
    gradient = np.linspace(0.92, 0.98, 256)
    gradient = np.vstack((gradient, gradient))
    ax_bg.imshow(gradient, aspect='auto', cmap='Blues', extent=[0, 1, 0, 1], alpha=0.30)
    
    # Tarjeta principal blanca
    main_card = patches.FancyBboxPatch(
        (0.025, 0.025), 0.950, 0.950,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor="#FFFFFF", edgecolor="#CBD5E1",
        linewidth=1.0, transform=fig.transFigure, zorder=-5
    )
    fig.patches.append(main_card)
    
    # Pastilla superior izquierda de fecha
    pill = patches.FancyBboxPatch(
        (0.055, 0.898), 0.320, 0.042,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        facecolor="#E0F2FE", edgecolor="#BAE6FD",
        linewidth=0.8, transform=fig.transFigure
    )
    fig.patches.append(pill)
    
    plt.figtext(0.068, 0.913, "•", fontname="Georgia", fontsize=10.0, color="#0284C7", transform=fig.transFigure, va='center')
    plt.figtext(0.082, 0.913, date_str, fontname="Georgia", fontsize=7.8, fontweight='bold', color="#0369A1", transform=fig.transFigure, va='center')
    
    # Título y subtítulo en Georgia Serif
    plt.figtext(0.055, 0.845, title_str, fontname="Georgia", fontsize=13.2, fontweight='bold', color="#0F172A", transform=fig.transFigure)
    plt.figtext(0.055, 0.814, subtitle_str, fontname="Georgia", fontsize=8.4, color="#475569", transform=fig.transFigure)
    
    # KPI Cards dinámicas sin solapamiento de líneas (Geometry & Hierarchy Impeccable)
    n_kpis = len(kpis)
    x_start = 0.055
    x_end = 0.945
    total_w = x_end - x_start
    gap = 0.014
    card_w = (total_w - (n_kpis - 1) * gap) / n_kpis
    card_h = 0.126
    y_card_bottom = 0.654
    y_card_top = y_card_bottom + card_h  # 0.780
    
    val_fontsize = 14.0 if n_kpis <= 3 else 12.2
    title_fontsize = 8.2 if n_kpis <= 3 else 7.2
    sub_fontsize = 7.2 if n_kpis <= 3 else 6.4
    
    for idx, (k_title, k_val, k_sub, k_color) in enumerate(kpis):
        x_pos = x_start + idx * (card_w + gap)
        
        # 1. Caja blanca de la tarjeta con borde sutil
        card = patches.FancyBboxPatch(
            (x_pos, y_card_bottom), card_w, card_h,
            boxstyle="round,pad=0.005,rounding_size=0.010",
            facecolor="#FFFFFF", edgecolor="#E2E8F0",
            linewidth=0.8, transform=fig.transFigure
        )
        fig.patches.append(card)
        
        # 2. Filete superior de color nítido sin padding que lo expanda
        top_bar = patches.Rectangle(
            (x_pos + 0.002, y_card_top - 0.004), card_w - 0.004, 0.004,
            facecolor=k_color, edgecolor='none', transform=fig.transFigure, zorder=2
        )
        fig.patches.append(top_bar)
        
        x_mid = x_pos + card_w / 2.0
        
        # 3. Título claramente separado por debajo del filete (distancia vertical = 0.022)
        plt.figtext(x_mid, y_card_top - 0.024, k_title, fontname="Georgia", fontsize=title_fontsize, fontweight='bold', color="#334155", ha='center', va='center', transform=fig.transFigure)
        
        # 4. Valor numérico en el centro de la tarjeta
        plt.figtext(x_mid, y_card_bottom + 0.055, k_val, fontname="Georgia", fontsize=val_fontsize, fontweight='bold', color=k_color, ha='center', va='center', transform=fig.transFigure)
        
        # 5. Subtítulo en la base de la tarjeta
        plt.figtext(x_mid, y_card_bottom + 0.018, k_sub, fontname="Georgia", fontsize=sub_fontsize, color="#64748B", ha='center', va='center', transform=fig.transFigure)
        
    # Área de gráfico con altura segura para evitar cualquier solapamiento
    ax_plot = fig.add_axes([0.065, 0.125, 0.870, 0.490])
    plot_func(ax_plot, fig)
    
    # Forzar que los ticks de ejes usen sans-serif técnico para máxima legibilidad
    for label in ax_plot.get_xticklabels() + ax_plot.get_yticklabels():
        label.set_fontfamily('sans-serif')
        label.set_fontsize(7.8)
    
    # Footer institucional en Georgia Serif con margen inferior seguro
    plt.figtext(0.055, 0.038, source_str, fontname="Georgia", fontsize=7.4, color="#64748B", transform=fig.transFigure)
    plt.figtext(0.935, 0.038, brand_str, fontname="Georgia", fontsize=8.5, fontweight='bold', color="#0284C7", ha='right', transform=fig.transFigure)
    plt.figtext(0.940, 0.044, "•", fontsize=9, color="#EF4444", transform=fig.transFigure)
    
    out_path = os.path.join(OUT_DIR, filename)
    fig.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    fig.savefig(os.path.join(DIR_FIG, filename), dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {filename}")
    return out_path

# ==============================================================================
# 1. FIGURA EMAE MASTER (SERIE HISTÓRICA 32 MESES)
# ==============================================================================
def plot_emae_master(ax, fig):
    ax.set_facecolor("#FFFFFF")
    t_points = 32
    meses_display = [
        "Ene-24", "", "", "Abr-24", "", "", "Jul-24", "", "", "Oct-24", "", "",
        "Ene-25", "", "", "Abr-25", "", "", "Jul-25", "", "", "Oct-25", "", "",
        "Ene-26", "", "", "Abr-26", "", "", "", "Ago-26"
    ]
    
    original = np.array([
        143, 137, 155, 150, 154, 152, 150, 148, 146, 144, 142, 139,
        137, 133, 147, 157, 147, 150, 145, 148, 148, 149, 141, 158,
        165, 156, 153, 151, 153, 152, 148, 152
    ])
    desest = np.array([
        149, 150, 151, 147, 145, 146, 149, 147, 146, 143, 144, 143,
        144, 143, 143, 144, 146, 147, 149, 151, 152, 152, 151, 152,
        151, 152, 154, 152, 152, 154, 155, 156
    ])
    tendencia = np.array([
        149, 149, 148, 148, 147, 146, 145, 145, 144, 144, 144, 144,
        144, 144, 145, 146, 147, 148, 149, 150, 151, 151, 152, 152,
        152, 152, 153, 153, 153, 153, 153, 153.5
    ])
    x_idx = np.arange(t_points)
    
    ax.plot(x_idx, original, color="#1E293B", lw=1.6, marker='o', markersize=4, label='Serie Original (152)')
    ax.plot(x_idx, desest, color=C_TEAL, lw=2.0, marker='s', markersize=4, label='Desestacionalizado (156 / +0,6% MoM)')
    ax.plot(x_idx, tendencia, color=C_CYAN, lw=1.8, linestyle='--', label='Tendencia-Ciclo (153,5 / +0,4% MoM)')
    
    ax.set_ylabel("Número índice (Base 2004 = 100)", fontsize=7.8, color=C_SLATE)
    ax.set_ylim(125, 175)
    ax.set_yticks(np.arange(130, 175, 10))
    ax.grid(True, linestyle='--', color=C_GRID, lw=0.6)
    
    tick_pos = [i for i, s in enumerate(meses_display) if s != ""]
    tick_lbl = [meses_display[i] for i in tick_pos]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_lbl, fontsize=7.2, color=C_SLATE, rotation=0)
    
    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=7.2, loc='upper left')
    
    ax.annotate("Ago-26: 156 desest. (+3,1% i.a.)", xy=(31, 156), xytext=(22, 168),
                arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=1.2),
                bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2FE", ec="#BAE6FD", lw=0.8),
                fontsize=7.5, fontweight='bold', color="#0369A1")

# ==============================================================================
# 2. FIGURA 1: CURVAS EN ARS & BREAKEVEN INFLACIONARIO
# ==============================================================================
def plot_rates_breakeven(ax, fig, data=None):
    if data is None:
        data = (DATOS_DEL_DIA or {}).get("curva_ars")
    if data is None:
        data = {
            "plazos_dias": [30, 60, 90, 180, 270, 360],
            "lecap_tickers": ["S31O6", "S28N6", "S31D6", "S31M7", "S30J7", "S31A7"],
            "lecap_tem_pct": [2.95, 3.05, 3.15, 3.25, 3.35, 3.40],
            "boncer_tir_real_pct": [1.10, 1.30, 1.50, 1.80, 2.10, 2.30],
            "rem_inflacion_pct": [2.00, 1.95, 1.90, 1.85, 1.80, 1.75],
        }

    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.33, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    dias_plazo = np.array(data["plazos_dias"])
    lecap_tickers = data["lecap_tickers"]
    tasa_lecap = np.array(data["lecap_tem_pct"])
    tasa_boncer = np.array(data["boncer_tir_real_pct"])

    ax1.plot(dias_plazo, tasa_lecap, color=C_NAVY, lw=2.2, marker='o', markersize=5, markeredgecolor='white', label='Curva Lecaps (TEM %)')
    for d, v, tck in zip(dias_plazo, tasa_lecap, lecap_tickers):
        ax1.annotate(f"{tck}\n{v:.2f}%", (d, v), xytext=(0, 7), textcoords="offset points",
                     ha='center', fontsize=6.8, fontweight='bold', color=C_NAVY)

    ax1.set_ylabel("TEM Tasa Fija (%)", fontsize=7.5, color=C_NAVY)
    _pad_lecap = max(0.15, (tasa_lecap.max() - tasa_lecap.min()) * 0.25)
    ax1.set_ylim(tasa_lecap.min() - _pad_lecap, tasa_lecap.max() + _pad_lecap)

    ax1_t = ax1.twinx()
    ax1_t.spines['top'].set_visible(False)
    ax1_t.spines['left'].set_visible(False)
    ax1_t.plot(dias_plazo, tasa_boncer, color=C_AMBER, lw=1.8, linestyle='--', marker='s', markersize=4.5, markeredgecolor='white', label='Curva Boncer CER (TIR Real %)')
    for d, v in zip(dias_plazo, tasa_boncer):
        ax1_t.annotate(f"{v:.2f}%", (d, v), xytext=(0, -12), textcoords="offset points",
                       ha='center', fontsize=6.8, fontweight='bold', color=C_AMBER)
    ax1_t.set_ylabel("TIR Real Anual Boncer (%)", fontsize=7.5, color=C_AMBER, labelpad=6)
    _pad_boncer = max(0.2, (tasa_boncer.max() - tasa_boncer.min()) * 0.35)
    ax1_t.set_ylim(tasa_boncer.min() - _pad_boncer, tasa_boncer.max() + _pad_boncer)
    ax1_t.grid(False)

    ax1.set_title("A. Curvas Soberanas en ARS (Lecap vs. Boncer)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xlabel("Plazo residual (Días)", fontsize=7.5, color=C_SLATE)
    ax1.set_xlim(0, dias_plazo.max() * 1.11)
    ax1.set_xticks(dias_plazo)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)

    breakeven = tasa_lecap - (tasa_boncer / 12)
    rem = np.array(data["rem_inflacion_pct"])
    premio = (breakeven - rem) * 100
    
    x = np.arange(len(dias_plazo))
    w = 0.35
    ax2.bar(x - w/2, breakeven, width=w, label='Breakeven Implícito (% MoM)', color=C_NAVY, alpha=0.9)
    ax2.bar(x + w/2, rem, width=w, label='Inflación Esperada REM (% MoM)', color="#94A3B8", alpha=0.9)
    
    for i in range(len(dias_plazo)):
        ax2.text(x[i] - w/2, breakeven[i] + 0.05, f"{breakeven[i]:.2f}%", ha='center', fontsize=6.5, fontweight='bold', color=C_NAVY)
        ax2.text(x[i] + w/2, rem[i] + 0.05, f"{rem[i]:.2f}%", ha='center', fontsize=6.5, color=C_SLATE)
        ax2.annotate(f"+{premio[i]:.0f} pb", (x[i], max(breakeven[i], rem[i]) + 0.28),
                     ha='center', fontsize=6.2, fontweight='bold', color=C_RED)
        
    ax2.set_title("B. Breakeven Inflacionario vs. Consenso REM", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{d}d" for d in dias_plazo], fontsize=7.2)
    ax2.set_ylabel("Tasa mensual (% MoM)", fontsize=7.5, color=C_SLATE)
    ax2.set_ylim(0, max(breakeven.max(), rem.max()) * 1.35)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='upper left')

# ==============================================================================
# 3. FIGURA 2: DISPERSIÓN DE PRECIOS & TRAYECTORIA IPC
# ==============================================================================
def plot_ipc_master(ax, fig):
    ax.axis('off')
    ax1 = fig.add_axes([0.15, 0.11, 0.32, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")
    
    aperturas = ["Bienes", "Núcleo", "General INDEC", "Servicios", "Regulados"]
    valores_ap = [1.9, 1.9, 2.2, 2.9, 3.0]
    colores_ap = [C_SLATE, C_CYAN, C_NAVY, "#EA580C", C_RED]
    y_pos = np.arange(len(aperturas))
    
    for y, val, col in zip(y_pos, valores_ap, colores_ap):
        ax1.hlines(y=y, xmin=0, xmax=val, color=col, lw=2.2, alpha=0.85)
        ax1.plot(val, y, marker='o', markersize=7.5, color=col, markeredgecolor='white', markeredgewidth=1.0)
        ax1.text(val + 0.10, y, f"{val:.1f}%", va='center', fontsize=7.8, fontweight='bold', color=col)
        
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(aperturas, fontsize=7.2)
    ax1.set_xlim(0, 3.8)
    ax1.set_title("A. Dispersión por Apertura (% MoM Ago-26)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xlabel("Variación mensual (% MoM)", fontsize=7.5, color=C_SLATE)
    ax1.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)
    
    meses_8 = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago"]
    x_8 = np.arange(len(meses_8))
    ipc_gral_8 = np.array([3.8, 3.5, 3.2, 2.8, 2.5, 2.4, 2.3, 2.2])
    ipc_core_8 = np.array([3.4, 3.1, 2.8, 2.4, 2.2, 2.1, 2.0, 1.9])
    ipc_mza_8  = np.array([4.0, 3.6, 3.4, 2.9, 2.6, 2.5, 2.4, 2.3])
    
    ax2.fill_between(x_8, ipc_core_8, ipc_gral_8, color="#E0F2FE", alpha=0.6, label='Brecha Regulados')
    ax2.plot(x_8, ipc_gral_8, color=C_NAVY, lw=2.0, marker='o', markersize=4.5, markeredgecolor='white', label='INDEC General (2,2%)')
    ax2.plot(x_8, ipc_mza_8, color=C_AMBER, lw=1.8, marker='s', markersize=4.5, markeredgecolor='white', label='Mendoza DEIE (2,3%)')
    ax2.plot(x_8, ipc_core_8, color=C_CYAN, lw=1.8, linestyle='--', marker='^', markersize=4.0, label='Núcleo (1,9%)')
    
    ax2.annotate("Mendoza: 2,3%", xy=(7, 2.3), xytext=(5.2, 2.85),
                 arrowprops=dict(arrowstyle="->", color=C_AMBER, lw=1.0),
                 fontsize=6.8, fontweight='bold', color=C_AMBER)
    ax2.annotate("INDEC: 2,2%", xy=(7, 2.2), xytext=(5.5, 1.70),
                 arrowprops=dict(arrowstyle="->", color=C_NAVY, lw=1.0),
                 fontsize=6.8, fontweight='bold', color=C_NAVY)
                 
    ax2.set_title("B. Convergencia Inflacionaria 2026 (% MoM)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xticks(x_8)
    ax2.set_xticklabels(meses_8, fontsize=7.2)
    ax2.set_ylabel("Tasa mensual (%)", fontsize=7.5, color=C_SLATE)
    ax2.set_ylim(1.4, 4.4)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='upper right')

# ==============================================================================
# 4. FIGURA 3: ESTRUCTURA PRODUCTIVA DE CUYO (VINO, PETRÓLEO, CEMENTO)
# ==============================================================================
def plot_cuyo_redesigned(ax, fig):
    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.40, 0.50])
    ax2 = fig.add_axes([0.56, 0.11, 0.37, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")
    
    meses_8 = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago"]
    x_8 = np.arange(len(meses_8))
    
    fracc = np.array([40.2, 41.5, 43.0, 45.2, 46.5, 47.8, 48.9, 50.1])
    gran  = np.array([14.0, 15.3, 16.1, 17.2, 17.5, 18.0, 18.3, 18.4])
    total_vino = fracc + gran
    
    ax1.bar(x_8, fracc, width=0.45, label='Fraccionado (50,1k hl)', color=C_RED, alpha=0.9)
    ax1.bar(x_8, gran, width=0.45, bottom=fracc, label='Granel (18,4k hl)', color=C_AMBER, alpha=0.9)
    ax1.plot(x_8, total_vino, color=C_NAVY, lw=1.8, marker='o', markersize=4, label='Total Despachos (68,5k hl)')
    
    ax1.set_title("A. Vitivinicultura: Despachos INV (Miles hl)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xticks(x_8)
    ax1.set_xticklabels(meses_8, fontsize=7.2)
    ax1.set_ylabel("Miles de hectolitros (hl)", fontsize=7.5, color=C_SLATE)
    ax1.set_ylim(0, 85)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax1.legend(frameon=False, fontsize=6.8, loc='upper left')
    
    ax1.annotate("68,5k hl", xy=(7, 68.5), xytext=(5.8, 75.0),
                 arrowprops=dict(arrowstyle="->", color=C_NAVY, lw=1.0),
                 fontsize=7.2, fontweight='bold', color=C_NAVY)
            
    conv = np.array([170, 171, 173, 174, 176, 178, 180, 182])
    noconv = np.array([15, 17, 19, 21, 23, 26, 28, 30])
    total_oil = conv + noconv
    
    ax2.bar(x_8, conv, width=0.45, label='Convencional (182k m³)', color=C_SLATE, alpha=0.85)
    ax2.bar(x_8, noconv, width=0.45, bottom=conv, label='Vaca Muerta Mza (30k m³)', color=C_TEAL, alpha=0.85)
    ax2.plot(x_8, total_oil, color=C_NAVY, lw=1.8, marker='s', markersize=4, label='Total Crudo (212k m³)')
    
    ax2.set_title("B. Hidrocarburos en Mendoza (Miles m³)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xticks(x_8)
    ax2.set_xticklabels(meses_8, fontsize=7.2)
    ax2.set_ylabel("Miles de metros cúbicos (m³)", fontsize=7.5, color=C_SLATE)
    ax2.set_ylim(0, 260)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='upper left')
    
    ax2.annotate("212k m³", xy=(7, 212), xytext=(5.8, 232),
                 arrowprops=dict(arrowstyle="->", color=C_NAVY, lw=1.0),
                 fontsize=7.2, fontweight='bold', color=C_NAVY)

# ==============================================================================
# 4.1 FIGURA 3B: COMPARATIVO REGIONAL CUYO (MENDOZA / SAN JUAN / SAN LUIS)
# ==============================================================================
def plot_regional_cuyo(ax, fig, regional=None):
    ax.axis('off')
    ax1 = fig.add_axes([0.08, 0.11, 0.40, 0.50])
    ax2 = fig.add_axes([0.56, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    if regional is None and DATOS_DEL_DIA is not None:
        regional = DATOS_DEL_DIA.get("regional_cuyo")
    if regional is None:
        regional = {
            "provincias": ["Mendoza", "San Juan", "San Luis"],
            "isarc_nivel": [104.8, 102.1, 106.4],
            "isarc_var_interanual_pct": [3.4, 2.1, 5.8],
            "industria_manufacturera_var_interanual_pct": [2.8, 1.4, 9.7],
            "construccion_var_interanual_pct": [5.1, -2.3, 14.2],
            "empleo_registrado_var_interanual_pct": [1.2, 0.5, 3.9],
        }

    provincias = regional["provincias"]
    isarc = regional["isarc_nivel"]
    isarc_ia = regional["isarc_var_interanual_pct"]
    colores_prov = [C_NAVY, C_TEAL, C_AMBER]

    x = np.arange(len(provincias))
    bars = ax1.bar(x, isarc, width=0.52, color=colores_prov, alpha=0.92)
    ax1.axhline(100, color=C_GRID, lw=1.0, linestyle='--', zorder=0)
    ax1.text(2.62, 100.3, "Base 100\n(ene-24)", fontsize=6.2, color=C_GRAY, ha='right')
    for i, (v, ia) in enumerate(zip(isarc, isarc_ia)):
        ax1.annotate(f"{v:.1f}", (x[i], v), xytext=(0, 4), textcoords="offset points",
                     ha='center', fontsize=8.2, fontweight='bold', color=colores_prov[i])
        signo = "+" if ia >= 0 else ""
        col_ia = C_TEAL if ia >= 0 else C_RED
        ax1.annotate(f"{signo}{ia:.1f}% i.a.", (x[i], v), xytext=(0, -11), textcoords="offset points",
                     ha='center', fontsize=6.6, fontweight='bold', color=col_ia)

    ax1.set_title("A. Índice Sintético de Actividad Regional (ISARC)", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(provincias, fontsize=7.6)
    ax1.set_ylabel("Índice (base 100 = ene-2024)", fontsize=7.2, color=C_SLATE)
    ax1.set_ylim(94, max(isarc) * 1.08)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)

    sectores = ["Industria\nManufacturera", "Construcción", "Empleo\nRegistrado"]
    datos_sect = [
        regional["industria_manufacturera_var_interanual_pct"],
        regional["construccion_var_interanual_pct"],
        regional["empleo_registrado_var_interanual_pct"],
    ]
    y = np.arange(len(sectores))
    h = 0.24
    for i, (prov, col) in enumerate(zip(provincias, colores_prov)):
        vals = [s[i] for s in datos_sect]
        offset = (i - 1) * h
        ax2.barh(y + offset, vals, height=h * 0.92, color=col, alpha=0.9, label=prov)
        for yi, v in zip(y + offset, vals):
            signo = "+" if v >= 0 else ""
            ax2.annotate(f"{signo}{v:.1f}%", (v, yi), xytext=(4 if v >= 0 else -4, 0),
                         textcoords="offset points", va='center',
                         ha='left' if v >= 0 else 'right', fontsize=6.2, fontweight='bold', color=col)

    ax2.axvline(0, color=C_SLATE, lw=0.8)
    ax2.set_title("B. Variación Interanual por Sector y Provincia", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_yticks(y)
    ax2.set_yticklabels(sectores, fontsize=7.0)
    ax2.set_xlabel("Var. i.a. %", fontsize=7.2, color=C_SLATE)
    xmax = max(abs(v) for s in datos_sect for v in s) * 1.55
    ax2.set_xlim(-xmax, xmax)
    ax2.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.4, loc='lower right', ncol=1)

# ==============================================================================
# 5. FIGURA 4: BALANCE CONSOLIDADO BCRA & REGLA DE TAYLOR
# ==============================================================================
def plot_monetary_master(ax, fig, historia_monetaria=None, taylor=None):
    if historia_monetaria is None:
        historia_monetaria = {
            "meses": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago"],
            "base_m": [21.5, 22.8, 23.9, 24.8, 25.4, 26.2, 26.9, 27.4],
            "lefi_m": [0.0, 5.0, 12.5, 18.0, 22.8, 26.5, 28.1, 29.3],
            "pases_m": [32.0, 26.5, 18.2, 11.0, 5.5, 1.2, 0.0, 0.0],
        }
    if taylor is None:
        mon = (DATOS_DEL_DIA or {}).get("monetario", {})
        taylor = {
            "meses": historia_monetaria["meses"],
            "tasa_real_exante": [0.40, 0.50, 0.60, 0.70, 0.80, 0.80, 0.90, mon.get("tasa_real_exante_tem_pct", 0.95)],
            "r_star": mon.get("r_star_pct", 0.75),
        }

    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.38, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    meses_8 = historia_monetaria["meses"]
    x_8 = np.arange(len(meses_8))
    base_m = np.array(historia_monetaria["base_m"])
    lefi_m = np.array(historia_monetaria["lefi_m"])
    pases_m = np.array(historia_monetaria["pases_m"])
    base_ult, lefi_ult, pases_ult = base_m[-1], lefi_m[-1], pases_m[-1]

    def _fmt_b(v):
        return f"${v:.1f} B".replace(".", ",")

    ax1.stackplot(x_8, base_m, lefi_m, pases_m,
                  labels=[f'Base Ampliada ({_fmt_b(base_ult)})', f'Lefi Tesoro ({_fmt_b(lefi_ult)})', f'Pases BCRA ({_fmt_b(pases_ult)})'],
                  colors=[C_NAVY, C_TEAL, "#CBD5E1"], alpha=0.9)
    ax1.set_title("A. Pasivos Monetarios Consolidados ($ B)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xticks(x_8)
    ax1.set_xticklabels(meses_8, fontsize=7.2)
    ax1.set_ylabel("Billones de ARS ($ B)", fontsize=7.5, color=C_SLATE)
    _tope_stack = (base_m + lefi_m + pases_m).max()
    ax1.set_ylim(0, _tope_stack * 1.20)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax1.legend(frameon=False, fontsize=6.8, loc='upper right')

    _x_label = len(meses_8) - 1.7
    ax1.set_xlim(-0.5, len(meses_8) - 0.3)
    ax1.text(_x_label, base_ult/2, _fmt_b(base_ult), ha='center', va='center', fontsize=7.2, fontweight='bold', color='white', clip_on=False)
    ax1.text(_x_label, base_ult + lefi_ult/2, _fmt_b(lefi_ult), ha='center', va='center', fontsize=7.2, fontweight='bold', color='white', clip_on=False)

    tasa_real_exante = np.array(taylor["tasa_real_exante"])
    r_star = taylor["r_star"]
    ax2.plot(x_8, tasa_real_exante, color=C_NAVY, lw=2.2, marker='o', markersize=4.5, markeredgecolor='white', label='Tasa Real Ex-Ante (TEM %)')
    ax2.axhline(y=r_star, color=C_AMBER, linestyle='--', lw=1.5, label=f'Tasa Neutral (r* = {r_star:.2f}%)'.replace(".", ","))
    ax2.fill_between(x_8, r_star, tasa_real_exante, where=(tasa_real_exante >= r_star), color="#E0F2FE", alpha=0.6, label=f'Brecha Taylor (+{(tasa_real_exante[-1]-r_star)*100:.0f} pb)')

    ax2.annotate(f"{meses_8[-1]}-26: +{tasa_real_exante[-1]:.2f}% TEM\n(Brecha +{(tasa_real_exante[-1]-r_star)*100:.0f} pb)".replace(".", ","),
                 xy=(len(meses_8)-1, tasa_real_exante[-1]), xytext=(len(meses_8)-3.5, tasa_real_exante.max() + 0.10),
                 arrowprops=dict(arrowstyle="->", color=C_NAVY, lw=1.0),
                 bbox=dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec="#CBD5E1", lw=0.6),
                 fontsize=6.8, fontweight='bold', color=C_NAVY)

    ax2.set_title("B. Postura Monetaria: Regla de Taylor", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xticks(x_8)
    ax2.set_xticklabels(meses_8, fontsize=7.2)
    ax2.set_ylabel("Tasa Efectiva Mensual (%)", fontsize=7.5, color=C_SLATE)
    _pad_taylor = max(0.15, (tasa_real_exante.max() - tasa_real_exante.min()) * 0.3)
    ax2.set_ylim(min(tasa_real_exante.min(), r_star) - _pad_taylor, max(tasa_real_exante.max(), r_star) + _pad_taylor * 1.6)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='lower right')

# ==============================================================================
# 6. FIGURA 5: CURVA SOBERANA EN USD (NELSON-SIEGEL)
# ==============================================================================
def plot_sovereign_master(ax, fig, bonos=None, nelson_siegel_params=None, anio_base=2026.5):
    if bonos is None:
        bonos = (DATOS_DEL_DIA or {}).get("bonos_soberanos")
    if bonos is None:
        bonos = [
            {"ticker": "AL29", "leg": "Local", "t": 3.0, "tir": 12.60},
            {"ticker": "AL30", "leg": "Local", "t": 4.0, "tir": 11.20},
            {"ticker": "AL35", "leg": "Local", "t": 9.0, "tir": 10.40},
            {"ticker": "GD29", "leg": "NY", "t": 3.0, "tir": 12.10},
            {"ticker": "GD30", "leg": "NY", "t": 4.0, "tir": 10.70},
            {"ticker": "GD35", "leg": "NY", "t": 9.0, "tir": 10.00},
            {"ticker": "GD38", "leg": "NY", "t": 12.0, "tir": 9.70},
            {"ticker": "GD41", "leg": "NY", "t": 15.0, "tir": 9.40},
        ]
    if nelson_siegel_params is None:
        nelson_siegel_params = (DATOS_DEL_DIA or {}).get("nelson_siegel")
    if nelson_siegel_params is None:
        nelson_siegel_params = {"b0": 9.40, "b1": 5.60, "b2": -3.20, "tau": 2.40, "spread_legislacion_pb": 50}

    al_data = [(b["ticker"], round(anio_base + b["t"], 1), b["tir"]) for b in bonos if b["leg"] == "Local"]
    gd_data = [(b["ticker"], round(anio_base + b["t"], 1), b["tir"]) for b in bonos if b["leg"] == "NY"]
    al_years = {yr for _, yr, _ in al_data}

    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.38, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    todos_los_anios = [yr for _, yr, _ in al_data + gd_data]
    grid_t = np.linspace(min(todos_los_anios) - 1.0, max(todos_los_anios) + 1.0, 100)
    t = grid_t - anio_base
    b0, b1, b2, tau = nelson_siegel_params["b0"], nelson_siegel_params["b1"], nelson_siegel_params["b2"], nelson_siegel_params["tau"]
    spread = nelson_siegel_params["spread_legislacion_pb"] / 100.0
    curve_gd = b0 + b1 * ((1 - np.exp(-t/tau)) / (t/tau)) + b2 * (((1 - np.exp(-t/tau)) / (t/tau)) - np.exp(-t/tau))
    curve_al = curve_gd + spread
    forward_gd = b0 + b1 * np.exp(-t/tau) + b2 * (t/tau) * np.exp(-t/tau)

    ax1.fill_between(grid_t, curve_gd, curve_al, color="#FEE2E2", alpha=0.55, label=f'Spread Ley Local/NY ({nelson_siegel_params["spread_legislacion_pb"]:.0f} pb)')
    ax1.plot(grid_t, curve_al, color=C_RED, lw=2.0, label='Ajuste Bonares (AL - Ley Arg)')
    ax1.plot(grid_t, curve_gd, color=C_NAVY, lw=2.0, linestyle='--', label='Ajuste Globales (GD - Ley NY)')

    for tck, yr, tir in al_data:
        ax1.scatter(yr, tir, color=C_RED, s=35, zorder=5, edgecolors='white')
        ax1.annotate(f"{tck}\n{tir:.1f}%", (yr, tir), xytext=(-16, 6), textcoords="offset points",
                     ha='right', fontsize=6.5, fontweight='bold', color=C_RED)

    for tck, yr, tir in gd_data:
        ax1.scatter(yr, tir, color=C_NAVY, s=35, zorder=5, edgecolors='white')
        offset_pt = (16, -8) if yr in al_years else (16, 6)
        ax1.annotate(f"{tck}\n{tir:.1f}%", (yr, tir), xytext=offset_pt, textcoords="offset points",
                     ha='left', fontsize=6.5, fontweight='bold', color=C_NAVY)

    ax1.set_title("A. Curva Spot en USD: Modelo Nelson-Siegel", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xlabel("Año de vencimiento", fontsize=7.5, color=C_SLATE)
    ax1.set_ylabel("TIR Anual (%)", fontsize=7.5, color=C_SLATE)
    _todas_tir = [tir for _, _, tir in al_data + gd_data]
    _pad_tir = max(0.5, (max(_todas_tir) - min(_todas_tir)) * 0.25)
    ax1.set_ylim(min(_todas_tir) - _pad_tir, max(_todas_tir) + _pad_tir * 1.6)
    ax1.set_xlim(min(todos_los_anios) - 1.5, max(todos_los_anios) + 1.5)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax1.legend(frameon=False, fontsize=6.8, loc='upper right')
    
    # Panel B: Spot vs Forward Instantánea
    ax2.plot(grid_t, curve_gd, color=C_NAVY, lw=2.0, label='Spot y(t) Globales NY')
    ax2.plot(grid_t, forward_gd, color=C_AMBER, lw=2.0, linestyle='-.', label='Forward Instantánea f(t)')
    
    _anot_x = min(todos_los_anios) + (max(todos_los_anios) - min(todos_los_anios)) * 0.5
    _anot_y = min(forward_gd.min(), curve_gd.min())
    ax2.annotate("Inversión de curva forward:\nCompresión de largo plazo", xy=(_anot_x, _anot_y), xytext=(min(todos_los_anios) + 1.5, max(curve_gd.max(), forward_gd.max()) - 1.0),
                 arrowprops=dict(arrowstyle="->", color=C_AMBER, lw=1.0),
                 bbox=dict(boxstyle="round,pad=0.2", fc="#FEF3C7", ec="#FDE68A", lw=0.6),
                 fontsize=6.8, fontweight='bold', color=C_AMBER)

    ax2.set_title("B. Curva Spot vs. Forward Implícita f(t)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xlabel("Año de vencimiento", fontsize=7.5, color=C_SLATE)
    ax2.set_ylabel("Rendimiento implícito (%)", fontsize=7.5, color=C_SLATE)
    _todos_y_b = np.concatenate([curve_gd, forward_gd])
    _pad_b = (_todos_y_b.max() - _todos_y_b.min()) * 0.15
    ax2.set_ylim(_todos_y_b.min() - _pad_b, _todos_y_b.max() + _pad_b)
    ax2.set_xlim(min(todos_los_anios) - 1.5, max(todos_los_anios) + 1.5)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='upper right')

# ==============================================================================
# 7. FIGURA 6: MERCADO CAMBIARIO & FUTUROS MATBA-ROFEX
# ==============================================================================
def plot_fx_master(ax, fig, fx=None, rofex=None):
    if fx is None:
        fx = (DATOS_DEL_DIA or {}).get("fx")
    if fx is None:
        fx = [
            {"short": "Mayorista (A3500)", "cotizacion_ars": 1485.00, "brecha_vs_mayorista_pct": 0.0},
            {"short": "Minorista (BNA)", "cotizacion_ars": 1515.00, "brecha_vs_mayorista_pct": 2.02},
            {"short": "MEP (AL30 48hs)", "cotizacion_ars": 1532.33, "brecha_vs_mayorista_pct": 3.19},
            {"short": "CCL (GD30 Cable)", "cotizacion_ars": 1596.59, "brecha_vs_mayorista_pct": 7.51},
            {"short": "Informal (Blue)", "cotizacion_ars": 1615.00, "brecha_vs_mayorista_pct": 8.75},
        ]
    if rofex is None:
        rofex = (DATOS_DEL_DIA or {}).get("rofex")
    if rofex is None:
        rofex = {
            "posiciones": ["Ago-26", "Sep-26", "Oct-26", "Dic-26", "Ago-27"],
            "tna_pct": [35.2, 36.4, 37.1, 38.5, 41.2],
            "open_interest_k": [1250, 890, 620, 450, 180],
            "prob_salto_discreto_pct": [8.5, 12.4, 16.8, 24.5, 34.0],
        }

    ax.axis('off')
    ax1 = fig.add_axes([0.18, 0.13, 0.29, 0.45])
    ax2 = fig.add_axes([0.57, 0.13, 0.36, 0.45])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    dolares_nom = [r.get("short", r.get("segmento")) for r in fx]
    cotiz_vals = [r["cotizacion_ars"] for r in fx]
    brechas_m = [f'{r["brecha_vs_mayorista_pct"]:+.1f}%'.replace(".", ",").replace("+0,0%", "0,0%") for r in fx]
    y_fx = np.arange(len(dolares_nom))
    _paleta_fx = [C_SLATE, C_NAVY, C_AMBER, C_RED, C_GRAY]
    colores_fx = [_paleta_fx[i % len(_paleta_fx)] for i in range(len(dolares_nom))]
    
    _xmin_fx = min(cotiz_vals) * 0.94
    for y, val, col, br in zip(y_fx, cotiz_vals, colores_fx, brechas_m):
        ax1.hlines(y=y, xmin=_xmin_fx, xmax=val, color=col, lw=2.2, alpha=0.85)
        ax1.plot(val, y, marker='o', markersize=6.5, color=col, markeredgecolor='white')
        ax1.text(val + (max(cotiz_vals) - min(cotiz_vals)) * 0.02, y, f"${val:,.2f} ({br})".replace(",", "X").replace(".", ",").replace("X", "."),
                 va='center', fontsize=6.8, fontweight='bold', color=col)

    ax1.set_yticks(y_fx)
    ax1.set_yticklabels(dolares_nom, fontsize=6.8)
    for lbl in ax1.get_yticklabels():
        lbl.set_fontfamily('sans-serif')
    for lbl in ax1.get_xticklabels():
        lbl.set_fontfamily('sans-serif')
        lbl.set_fontsize(6.8)
    ax1.set_xlim(_xmin_fx, max(cotiz_vals) * 1.10)
    ax1.set_title("A. Cotizaciones Cambiarias y Brechas Spot", fontsize=8.0, fontweight='bold', color=C_NAVY, pad=6, loc='left')
    ax1.set_xlabel("Cotización en Pesos (ARS)", fontsize=7.0, color=C_SLATE, labelpad=2)
    ax1.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)

    posiciones = rofex["posiciones"]
    tna_rofex = rofex["tna_pct"]
    oi_contratos = rofex["open_interest_k"]
    prob_salto = rofex["prob_salto_discreto_pct"]

    x_pos = np.arange(len(posiciones))
    ax2.bar(x_pos, oi_contratos, color="#E2E8F0", width=0.45, label='Open Interest (k contratos)')
    for i, oi in enumerate(oi_contratos):
        ax2.text(x_pos[i], oi + max(oi_contratos) * 0.02, f"{oi}k", ha='center', fontsize=6.5, color=C_SLATE)

    ax2.set_ylabel("Open Interest (Miles de contratos)", fontsize=7.0, color=C_SLATE)
    ax2.set_ylim(0, max(oi_contratos) * 1.30)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(posiciones, fontsize=6.8)
    for lbl in ax2.get_xticklabels() + ax2.get_yticklabels():
        lbl.set_fontfamily('sans-serif')
    
    ax2_t = ax2.twinx()
    ax2_t.spines['top'].set_visible(False)
    ax2_t.spines['left'].set_visible(False)
    ax2_t.plot(x_pos, tna_rofex, color=C_RED, lw=2.0, marker='o', markersize=4.5, label='TNA Implícita (%)')
    n_pos = len(x_pos)
    for i, (tna, pr) in enumerate(zip(tna_rofex, prob_salto)):
        if i == n_pos - 1:
            ax2_t.annotate(f"{tna:.1f}%\n(P:{pr:.1f}%)", (x_pos[i], tna), xytext=(0, 9), textcoords="offset points",
                           ha='center', va='bottom', fontsize=6.2, fontweight='bold', color=C_RED)
        else:
            ax2_t.annotate(f"{tna:.1f}%\n(P:{pr:.1f}%)", (x_pos[i], tna), xytext=(12, 0), textcoords="offset points",
                           ha='left', va='center', fontsize=6.2, fontweight='bold', color=C_RED)
    ax2_t.set_ylabel("Tasa Implícita TNA (%)", fontsize=7.0, color=C_RED, labelpad=6)
    _pad_tna = max(1.5, (max(tna_rofex) - min(tna_rofex)) * 0.35)
    ax2_t.set_ylim(min(tna_rofex) - _pad_tna * 1.6, max(tna_rofex) + _pad_tna)
    ax2_t.grid(False)
    for lbl in ax2_t.get_yticklabels():
        lbl.set_fontfamily('sans-serif')
        lbl.set_fontsize(6.8)
    
    ax2.set_title("B. Futuros Matba-Rofex y Prob. Salto", fontsize=8.0, fontweight='bold', color=C_NAVY, pad=6, loc='left')

# ==============================================================================
# 8. FIGURA 7: RENTA VARIABLE & RADAR DE VALUACIÓN
# ==============================================================================
def plot_equity_master(ax, fig):
    ax.axis('off')
    ax1 = fig.add_axes([0.16, 0.11, 0.31, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")
    
    tickers_eq = ["BBAR (BBVA)", "BMA (Macro)", "IMV (S&P Merval)", "GGAL (Galicia)", "PAMP (Pampa)", "TGSU2 (TGS)", "YPFD (YPF)"]
    var_eq = [1.20, 1.50, 1.30, 1.90, 2.40, 2.80, 3.20]
    y_eq = np.arange(len(tickers_eq))
    colores_e = [C_CYAN, C_CYAN, C_NAVY, C_CYAN, C_AMBER, C_AMBER, C_AMBER]
    
    for y, val, col in zip(y_eq, var_eq, colores_e):
        ax1.hlines(y=y, xmin=0, xmax=val, color=col, lw=2.0, alpha=0.85)
        ax1.plot(val, y, marker='o', markersize=6.5, color=col, markeredgecolor='white')
        ax1.text(val + 0.08, y, f"+{val:.2f}%", va='center', fontsize=7.2, fontweight='bold', color=col)
        
    ax1.set_yticks(y_eq)
    ax1.set_yticklabels(tickers_eq, fontsize=7.0)
    ax1.set_xlim(0, 4.0)
    ax1.set_title("A. Renta Variable: Variación Semanal (%)", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xlabel("Rendimiento semanal en ARS (%)", fontsize=7.5, color=C_SLATE)
    ax1.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)
    
    tickers_sc = ["YPFD", "PAMP", "TGSU2", "VIST", "TGNO4"]
    ev_ebitda = [3.8, 4.1, 4.4, 4.8, 5.2]
    margen_ebitda = [32.4, 38.5, 42.1, 55.0, 36.0]
    
    ax2.scatter(ev_ebitda, margen_ebitda, color=C_NAVY, s=90, alpha=0.9, zorder=5, edgecolors='white', linewidths=1.2)
    for t, x, y in zip(tickers_sc, ev_ebitda, margen_ebitda):
        offset_x = 0.08
        offset_y = 0.8 if t != "TGNO4" else -2.5
        ax2.annotate(f"{t}\n({x:.1f}x, {y:.1f}%)", (x, y), xytext=(x + offset_x, y + offset_y),
                     fontsize=7.2, fontweight='bold', color=C_NAVY)
        
    ax2.axvline(x=4.5, color=C_RED, linestyle='--', lw=1.2, label='Umbral atractivo (< 4,5x)')
    ax2.set_title("B. Radar Energético: EV/EBITDA vs. Margen", fontsize=8.5, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_xlabel("Múltiplo EV/EBITDA (veces)", fontsize=7.5, color=C_SLATE)
    ax2.set_ylabel("Margen EBITDA (%)", fontsize=7.5, color=C_SLATE)
    ax2.set_xlim(3.2, 5.8)
    ax2.set_ylim(25, 62)
    ax2.grid(True, linestyle='--', color=C_GRID, lw=0.6)
    ax2.legend(frameon=False, fontsize=6.8, loc='upper left')

# ==============================================================================
# GENERACIÓN DE TODAS LAS INFOGRAFÍAS
# ==============================================================================
def generar_todas_las_infografias(*args, **kwargs):
    print("Iniciando renderizado de infografías vectoriales maestras a 300 DPI...")
    
    f0 = create_master_infographic(
        "chart_indec_emae_master.png",
        "INDEC · SERIE HISTÓRICA 2024-2026",
        "Estimador Mensual de Actividad Económica (EMAE)",
        "Evolución de la serie original, desestacionalizada y tendencia-ciclo (Base 2004 = 100)",
        [
            ("EMAE ORIGINAL", "152,0", "Variación i.a. +3,1%", C_NAVY),
            ("DESESTACIONALIZADO", "156,0", "Variación mensual +0,6%", C_TEAL),
            ("TENDENCIA-CICLO", "153,5", "Variación mensual +0,4%", C_CYAN)
        ],
        plot_emae_master,
        "Fuente: Instituto Nacional de Estadística y Censos (INDEC). Serie oficial 2024-2026."
    )
    
    f1 = create_master_infographic(
        "chart_indec_1_rates.png",
        "BYMA / BCRA · CIERRE AGOSTO 2026",
        "Arbitraje de Tasas en ARS y Breakeven Inflacionario",
        "Estructura a término de Lecaps a tasa fija vs. Boncer CER y expectativas del REM",
        [
            ("LECAP CORTA (S31O6)", "2,95% TEM", "TNA 35,4% · Carry positivo", C_NAVY),
            ("BREAKEVEN INFLACIÓN", "2,86% MoM", "Premio tasa fija +86 pb s/ REM", C_AMBER),
            ("INFLACIÓN REM 1M", "2,00% MoM", "Sendero descendente proyectado", C_CYAN)
        ],
        plot_rates_breakeven,
        "Fuentes: Bolsas y Mercados Argentinos (ByMA), BCRA y Relevamiento de Expectativas de Mercado (REM)."
    )
    
    f2 = create_master_infographic(
        "chart_indec_2_ipc.png",
        "INDEC / DEIE MENDOZA · AGOSTO 2026",
        "Dinámica de Precios, Canastas Básicas y Salario Real",
        "Dispersión por aperturas, convergencia mensual y comparación regional Cuyo vs. Nación",
        [
            ("IPC NACIONAL GENERAL", "2,2% MoM", "Núcleo: 1,9% · Regulados: 3,0%", C_NAVY),
            ("IPC PROVINCIA MENDOZA", "2,3% MoM", "DEIE · Brecha regional +0,10 pp", C_AMBER),
            ("SALARIO REAL RIPTE", "84,4 pts", "+2,4% acumulado s/ dic-23", C_TEAL)
        ],
        plot_ipc_master,
        "Fuentes: INDEC, Dirección de Estadísticas e Investigaciones Económicas (DEIE) Mendoza y Secretaría de Trabajo."
    )
    
    f3 = create_master_infographic(
        "chart_indec_3_cuyo.png",
        "INV / SECRETARÍA DE ENERGÍA / AFCP",
        "Estructura Productiva y Desagregación Sectorial en Cuyo",
        "Despachos vitivinícolas totales, extracción hidrocarburífera y despacho de cemento",
        [
            ("DESPACHOS VINO INV", "68,5 mil hl", "50,1k fracc. + 18,4k granel", C_RED),
            ("PETRÓLEO MENDOZA", "212 mil m³", "182k conv. + 30k no conv.", C_NAVY),
            ("CEMENTO PORTLAND", "100,4 pts", "AFCP Cuyo · Obra privada", C_SLATE)
        ],
        plot_cuyo_redesigned,
        "Fuentes: Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía de la Nación y AFCP."
    )
 
    f3b = create_master_infographic(
        "chart_indec_3b_regional_cuyo.png",
        "DEIE MENDOZA / IPEC SAN JUAN / IPEC SAN LUIS",
        "Comparativo Regional: Índice Sintético de Actividad (ISARC)",
        "Desagregación provincial de Cuyo — nivel de actividad, industria, construcción y empleo",
        [
            ("ISARC SAN LUIS", "106,4 pts", "+5,8% i.a. · Líder regional", C_AMBER),
            ("ISARC MENDOZA", "104,8 pts", "+3,4% i.a. · Motor vitivinícola", C_NAVY),
            ("ISARC SAN JUAN", "102,1 pts", "+2,1% i.a. · Convergencia minera", C_TEAL)
        ],
        plot_regional_cuyo,
        "Fuentes: DEIE Mendoza, IPEC San Juan, IPEC San Luis y elaboración propia (índice compuesto ISARC)."
    )
 
    f4 = create_master_infographic(
        "chart_indec_4_monetary.png",
        "BANCO CENTRAL DE LA REPÚBLICA ARGENTINA",
        "Balance Consolidado del BCRA y Regla de Taylor",
        "Absorción cuasifiscal del Tesoro mediante Lefi y brecha de tasa real ex-ante",
        [
            ("BASE MONETARIA AMPLIADA", "$27,4 B", "Control estricto en términos reales", C_NAVY),
            ("LEFI TESORO NACIONAL", "$29,3 B", "Pases pasivos BCRA extinguidos ($0 B)", C_TEAL),
            ("BRECHA DE TAYLOR", "+20 bps", "Tasa real +0,95% vs. Neutral r* 0,75%", C_AMBER)
        ],
        plot_monetary_master,
        "Fuentes: Banco Central de la República Argentina (BCRA) y Secretaría de Finanzas."
    )
    
    f5 = create_master_infographic(
        "chart_indec_5_sovereign.png",
        "BYMA / BLOOMBERG · RESEARCH SOBERANO",
        "Estructura Temporal Soberana en USD — Modelo Nelson-Siegel",
        "Curva spot y forward instantánea para títulos Bonares (AL) y Globales (GD)",
        [
            ("RIESGO PAÍS (EMBI+)", "506 pb", "Compresión sovereign (-26 pb)", C_NAVY),
            ("NELSON-SIEGEL NIVEL (β0)", "9,40%", "Tasa asintótica soberana largo plazo", C_RED),
            ("SPREAD LEGISLACIÓN", "50 bps", "Diferencial promedio Ley Local vs. NY", C_AMBER)
        ],
        plot_sovereign_master,
        "Fuentes: Bolsas y Mercados Argentinos (ByMA), Bloomberg y estimaciones econométricas propias."
    )
    
    f6 = create_master_infographic(
        "chart_indec_6_fx.png",
        "BCRA / MATBA-ROFEX / MIT RESEARCH · CIERRE FINANCIERO",
        "Microestructura Cambiaria, Rofex y Fragilidad Sistémica",
        "Brechas spot, futuros y métricas de acoplamiento multivariado (Ratio de Absorción & Mahalanobis)",
        [
            ("DÓLAR CCL (GD30)", "$1.596,59", "Brecha BNA: 5,39% (7,51% May)", C_RED),
            ("FUTURO DIC-26", "$1.680,00", "TNA implícita 38,5% · OI 450k", C_NAVY),
            ("ABSORPTION RATIO", "64,2%", "Régimen Resiliente (<75%)", C_TEAL),
            ("TURBULENCIA dt", "4,12", "Normal (Umbral Chi2: 11,07)", C_AMBER)
        ],
        plot_fx_master,
        "Fuentes: BCRA, Matba-Rofex, ByMA y modelo cuantitativo de fragilidad de activos cruzados."
    )
    
    f7 = create_master_infographic(
        "chart_indec_7_equity.png",
        "BYMA / NYSE · RADAR DE MERCADO",
        "Renta Variable Líder y Radar Sectorial Energético",
        "Rendimientos semanales en ARS y múltiplos de valuación EV/EBITDA vs. margen operativo",
        [
            ("S&P MERVAL (IMV)", "+1,30%", "Panel líder traccionado por energía", C_NAVY),
            ("YPFD (YPF S.A.)", "+3,20%", "EV/EBITDA 3,8x · Margen 32,4%", C_AMBER),
            ("TGSU2 (TGS)", "+2,80%", "EV/EBITDA 4,4x · Margen 42,1%", C_CYAN)
        ],
        plot_equity_master,
        "Fuentes: Bolsas y Mercados Argentinos (ByMA), New York Stock Exchange (NYSE) y balances corporativos."
    )
    
    print("Todas las infografías maestras fueron generadas con éxito y sin solapamientos.")
    return [f0, f1, f2, f3, f3b, f4, f5, f6, f7]

if __name__ == "__main__":
    generar_todas_las_infografias()


import os
import shutil
import openpyxl
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = r'C:\Users\fedea\Downloads\coyuntura-macro'
EXCEL_PATH = os.path.join(BASE_DIR, "01_Bases_Datos", "Base_Datos_Macro_Financiera.xlsx")
OUT_DIR = os.path.join(BASE_DIR, "03_Figuras_HD", "master_extracted_images")
DIR_HD = os.path.join(BASE_DIR, "03_Figuras_HD")
os.makedirs(OUT_DIR, exist_ok=True)

# Tokens Cromáticos Institucionales
NAVY = '#0C2340'         # Oxford Navy (Principal)
NAVY_LIGHT = '#1E3A8A'   # Royal Navy
WINE = '#722F37'         # Deep Wine / Burgundy (Secundario)
WINE_LIGHT = '#991B1B'   # Wine Accent
FOREST = '#0D5C46'       # Forest Green / Dark Emerald
EMERALD = '#059669'      # Vibrant Emerald
OCHRE = '#B45309'        # Warm Amber / Ochre
AMBER_LIGHT = '#D97706'  # Gold Amber
CHARCOAL = '#0F172A'     # Slate Charcoal
SLATE = '#334155'        # Medium Slate
MUTED = '#64748B'        # Slate Gray
LIGHT_BG = '#F8FAFC'     # Off-white card background
CARD_BG = '#F1F5F9'      # Secondary card fill
BORDER_COL = '#CBD5E1'   # Card border
GRID_COL = '#E2E8F0'     # Subtle gridline

# Tipografía y Estilo Global
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = BORDER_COL
plt.rcParams['axes.linewidth'] = 0.9
plt.rcParams['axes.labelsize'] = 8.8
plt.rcParams['xtick.labelsize'] = 8.2
plt.rcParams['ytick.labelsize'] = 8.2

def get_df(sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    except Exception as e:
        print(f"Advertencia al leer solapa {sheet_name}: {e}")
        return pd.DataFrame()

def save_fig(fig, filename):
    out_p = os.path.join(OUT_DIR, filename)
    fig.savefig(out_p, dpi=300, bbox_inches='tight', facecolor='#FFFFFF', edgecolor='none')
    plt.close(fig)
    return out_p

def apply_panel_styling(ax, title_text, xlabel_text="", ylabel_text=""):
    ax.set_facecolor('#FFFFFF')
    ax.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BORDER_COL)
    ax.spines['bottom'].set_color(BORDER_COL)
    ax.set_title(title_text, fontsize=10.2, fontweight='bold', color=NAVY, pad=10, loc='left')
    if xlabel_text:
        ax.set_xlabel(xlabel_text, fontsize=8.5, color=SLATE, labelpad=5)
    if ylabel_text:
        ax.set_ylabel(ylabel_text, fontsize=8.5, color=SLATE, labelpad=5)

# =============================================================================
# 1. FIGURA 1: Tasas en ARS y Breakeven (img_p4_1_5.png)
# =============================================================================
def generate_fig1():
    df_pesos = get_df("Curva_Pesos_y_Breakeven")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    # Panel A: Curva Spot en Pesos (Lecap TEM vs Boncer TIR Real)
    apply_panel_styling(ax1, 'PANEL A | Curvas de Rendimiento en ARS (Lecap vs. Boncer)', 'Plazo residual (Días al vencimiento)', 'TEM (%)')
    ax1_r = ax1.twinx()
    ax1_r.spines['top'].set_visible(False)
    ax1_r.spines['left'].set_visible(False)
    ax1_r.spines['right'].set_color(OCHRE)
    
    if not df_pesos.empty and "Dias_al_Vencimiento" in df_pesos.columns:
        df_lec = df_pesos[df_pesos["Tipo_Instrumento"] == "Tasa Fija"]
        df_cer = df_pesos[df_pesos["Tipo_Instrumento"] == "Ajustable CER"]
        dias_lec = df_lec["Dias_al_Vencimiento"].values
        tem_lec = df_lec["TEM_%"].values
        dias_cer = df_cer["Dias_al_Vencimiento"].values
        tir_cer = df_cer["TIR_Real_ExAnte_Fisher_%"].values
    else:
        dias_lec = np.array([71, 99, 116, 163, 191])
        tem_lec = np.array([3.15, 3.10, 3.02, 2.95, 2.90])
        dias_cer = np.array([80, 116, 812])
        tir_cer = np.array([6.00, 5.40, 7.80])
    
    # Fill & Line
    ax1.plot(dias_lec, tem_lec, color=NAVY, marker='o', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, label='Lecap (TEM %)')
    ax1.fill_between(dias_lec, 2.6, tem_lec, color=NAVY, alpha=0.06)
    
    ax1_r.plot(dias_cer[:2], tir_cer[:2], color=OCHRE, marker='s', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, linestyle='--', label='Boncer (TIR Real %)')
    
    for d, tem in zip(dias_lec, tem_lec):
        ax1.annotate(f'{tem:.2f}%', (d, tem), textcoords="offset points", xytext=(0, 7), ha='center',
                     fontsize=8.0, fontweight='bold', color=NAVY,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=NAVY, alpha=0.9, linewidth=0.6))
    for d, tir in zip(dias_cer[:2], tir_cer[:2]):
        ax1_r.annotate(f'{tir:.2f}%', (d, tir), textcoords="offset points", xytext=(0, -14), ha='center',
                       fontsize=8.0, fontweight='bold', color=OCHRE,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=OCHRE, alpha=0.9, linewidth=0.6))
        
    ax1.set_ylim(2.6, 3.5); ax1_r.set_ylim(4.5, 7.2)
    ax1_r.set_ylabel('TIR Real Anual (%)', fontsize=8.5, color=OCHRE, fontweight='bold')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7.8, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    # Panel B: Breakeven vs REM
    apply_panel_styling(ax2, 'PANEL B | Breakeven Inflacionario vs. Expectativa REM', 'Plazo residual (Días al vencimiento)', 'Inflación Mensual (%)')
    if not df_pesos.empty and "Breakeven_Inflacion_Mensual_%" in df_pesos.columns:
        df_lec_b = df_pesos[df_pesos["Tipo_Instrumento"] == "Tasa Fija"]
        dias_b = df_lec_b["Dias_al_Vencimiento"].values
        breakeven = df_lec_b["Breakeven_Inflacion_Mensual_%"].values
        rem_exp = df_lec_b["Inflacion_Esperada_REM_%"].values
    else:
        dias_b = np.array([71, 99, 116, 163, 191])
        breakeven = np.array([2.65, 2.58, 2.50, 2.42, 2.38])
        rem_exp = np.array([2.80, 2.60, 2.50, 2.30, 2.20])
    
    ax2.plot(dias_b, breakeven, color=WINE, marker='o', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, label='Breakeven Inflación')
    ax2.plot(dias_b, rem_exp, color=FOREST, marker='^', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, linestyle='--', label='Consenso REM (BCRA)')
    ax2.fill_between(dias_b, breakeven, rem_exp, color=WINE, alpha=0.10, label='Prima de Tasa Fija (Fisher)')
    
    for d, b in zip(dias_b, breakeven):
        ax2.annotate(f'{b:.2f}%', (d, b), textcoords="offset points", xytext=(0, 7), ha='center',
                     fontsize=8.0, fontweight='bold', color=WINE,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=WINE, alpha=0.9, linewidth=0.6))
    for d, r in zip(dias_b, rem_exp):
        ax2.annotate(f'{r:.2f}%', (d, r), textcoords="offset points", xytext=(0, -14), ha='center',
                     fontsize=8.0, fontweight='bold', color=FOREST,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=FOREST, alpha=0.9, linewidth=0.6))
        
    ax2.set_ylim(1.9, 3.2)
    ax2.legend(loc='upper right', fontsize=7.8, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p4_1_5.png')

# =============================================================================
# 2. FIGURA 2: Precios e IPC (img_p5_1_7.png)
# =============================================================================
def generate_fig2():
    fig = plt.figure(figsize=(12, 6.8), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.22)
    fig.patch.set_facecolor('#FFFFFF')
    
    # Panel A: Apertura IPC
    ax1 = fig.add_subplot(gs[0])
    apply_panel_styling(ax1, 'PANEL A | Dispersión por Apertura Minorista y Mayorista (% MoM)', 'Variación mensual (% MoM)')
    ax1.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, axis='x')
    
    rubros = ['IPC Mendoza (DEIE)', 'Inflación Núcleo', 'IPC General INDEC', 'IPIM Mayorista', 'Precios Regulados']
    valores = [2.3, 1.9, 2.2, 2.3, 3.0]
    colores = [OCHRE, FOREST, NAVY, WINE, WINE]
    y_pos = np.arange(len(rubros))
    
    # Reference line at 2.2% INDEC with clean top badge (no overlapping legend)
    ax1.axvline(x=2.2, color=NAVY, linestyle=':', linewidth=1.4, alpha=0.7)
    ax1.text(2.2, 4.45, 'Nivel General INDEC: 2,2%', color=NAVY, fontsize=8.0, ha='center', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.25', facecolor='#FFFFFF', edgecolor=NAVY, alpha=0.95, linewidth=0.7))
    
    ax1.hlines(y=y_pos, xmin=0, xmax=valores, color='#CBD5E1', linewidth=2.8, zorder=1)
    
    for y, v, c in zip(y_pos, valores, colores):
        ax1.scatter(v, y, color=c, s=140, zorder=2, edgecolors='#FFFFFF', linewidth=1.5)
        ax1.text(v + 0.10, y, f'+{v:.1f}%', color=c, fontweight='bold', fontsize=8.8, va='center',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#F8FAFC', edgecolor=c, alpha=0.85, linewidth=0.5))
                 
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(rubros, fontsize=8.8, fontweight='bold', color=CHARCOAL)
    ax1.set_xlim(0, 3.8)
    ax1.set_ylim(-0.6, 4.8)
    
    # Panel B: Matriz Institucional SIPM
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor('#FFFFFF'); ax2.axis('off')
    
    matrix_sipm = [
        ("IPIM (Mayorista)", "2,3%", "48,5% i.a.", "Prod. Nacionales: +2,4%", "Prod. Importados: +1,8%", NAVY),
        ("IPIB (Básico)", "2,2%", "47,2% i.a.", "Prod. Nacionales: +2,3%", "Prod. Importados: +1,8%", WINE),
        ("IPP (Productor)", "2,1%", "46,1% i.a.", "Bienes Primarios: +2,0%", "Manufacturas: +2,1%", FOREST)
    ]
    
    for i, (name, val, ia, nac, imp, col) in enumerate(matrix_sipm):
        y_box = 0.68 - i * 0.32
        card = patches.FancyBboxPatch((0.02, y_box), 0.96, 0.28, boxstyle="round,pad=0.02", facecolor='#F8FAFC', edgecolor=BORDER_COL, linewidth=1.2)
        ax2.add_patch(card)
        accent = patches.FancyBboxPatch((0.02, y_box), 0.025, 0.28, boxstyle="round,pad=0.005", facecolor=col, edgecolor='none')
        ax2.add_patch(accent)
        
        # Left side: Title
        ax2.text(0.08, y_box + 0.19, name, fontsize=10.0, fontweight='bold', color=NAVY, va='center')
        
        # Right side: Metric and Interanual percentage (spatially separated)
        ax2.text(0.68, y_box + 0.19, f"+{val}", fontsize=13.0, fontweight='bold', color=col, ha='right', va='center')
        ax2.text(0.72, y_box + 0.19, f"({ia})", fontsize=7.8, color=MUTED, ha='left', va='center')
        
        # Dividing rule
        ax2.plot([0.08, 0.94], [y_box + 0.11, y_box + 0.11], color='#E2E8F0', linewidth=1)
        
        # Bottom details
        ax2.text(0.08, y_box + 0.05, f"• {nac}", fontsize=7.8, color=CHARCOAL, va='center')
        ax2.text(0.55, y_box + 0.05, f"• {imp}", fontsize=7.8, color=CHARCOAL, va='center')
        
    ax2.set_title('PANEL B | Sistema de Índices de Precios Mayoristas (SIPM INDEC)', fontsize=10.2, fontweight='bold', color=NAVY, pad=10, loc='left')
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p5_1_7.png')

# =============================================================================
# 3. FIGURA 3: Actividad Económica EMAE (img_p7_1_9.png)
# =============================================================================
def generate_fig3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300, gridspec_kw={'width_ratios': [1.25, 1.0]})
    fig.patch.set_facecolor('#FFFFFF')
    
    # Panel A: Serie Temporal EMAE
    apply_panel_styling(ax1, 'PANEL A | Estimador Mensual de Actividad (EMAE)', 'Meses de serie', 'Número índice (Base 2004=100)')
    meses_cod = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D',
                 'E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D',
                 'E', 'F', 'M', 'A', 'M', 'J', 'J', 'A']
    x = np.arange(len(meses_cod))
    orig = np.array([143, 137, 155, 150, 154, 152, 150, 148, 146, 143, 142, 139,
                     133, 147, 157, 147, 150, 145, 148, 148, 149, 141, 158, 165,
                     156, 154, 151, 153, 152, 148, 152, 154.2])
    desest = np.array([149, 150, 151, 147, 145, 146, 149, 147, 146, 144, 144, 144,
                       143, 144, 146, 147, 149, 151, 152, 152, 152, 152, 152, 152,
                       153, 153, 153, 154, 155, 156.0, 155.8, 156.2])
    tend = np.array([149, 149, 148, 148, 147, 146, 145, 145, 144, 144, 144, 144,
                     145, 146, 147, 148, 149, 150, 151, 151, 151, 152, 152, 152,
                     153, 153, 153, 153, 153, 153.2, 153.3, 153.5])
    
    ax1.plot(x, orig, color=MUTED, marker='o', markersize=3.2, linewidth=1.2, alpha=0.6, label='Original')
    ax1.plot(x, desest, color=FOREST, marker='s', markersize=4.0, linewidth=2.0, label='Desestacionalizada (+0,6% MoM)')
    ax1.plot(x, tend, color=NAVY, marker='^', markersize=3.5, linewidth=1.8, label='Tendencia-ciclo')
    
    ax1.axvline(x=11.5, color='#94A3B8', linestyle='-', linewidth=0.9)
    ax1.axvline(x=23.5, color='#94A3B8', linestyle='-', linewidth=0.9)
    ax1.text(5.5, 126, '2024', ha='center', fontsize=8.5, fontweight='bold', color=CHARCOAL)
    ax1.text(17.5, 126, '2025', ha='center', fontsize=8.5, fontweight='bold', color=CHARCOAL)
    ax1.text(27.5, 126, '2026', ha='center', fontsize=8.5, fontweight='bold', color=CHARCOAL)
    
    ax1.set_xticks(x); ax1.set_xticklabels(meses_cod, fontsize=6.8)
    ax1.set_ylim(124, 172)
    ax1.legend(loc='upper left', fontsize=7.2, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    # Panel B: Variación Sectorial Interanual (% i.a.)
    apply_panel_styling(ax2, 'PANEL B | Variación Sectorial Interanual (% i.a.)', 'Variación interanual (% i.a.)')
    ax2.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, axis='x')
    sectores = ['Construcción', 'Comercio', 'Industria Manuf.', 'Electricidad / Gas', 'Agricultura / Caza', 'Minería / Petróleo']
    var_sec = [-5.2, -3.5, -1.2, 3.4, 8.5, 14.2]
    colors_sec = [WINE, WINE, WINE, NAVY, FOREST, FOREST]
    y_pos_sec = np.arange(len(sectores))
    
    bars = ax2.barh(y_pos_sec, var_sec, height=0.55, color=colors_sec, edgecolor='#CBD5E1', zorder=2)
    ax2.axvline(x=0, color='#64748B', linestyle='-', linewidth=1.0, zorder=1)
    
    for y, v, c in zip(y_pos_sec, var_sec, colors_sec):
        if v > 0:
            ax2.text(v + 0.4, y, f'+{v:.1f}%', va='center', ha='left', fontsize=8.0, fontweight='bold', color=c,
                     bbox=dict(boxstyle='round,pad=0.15', facecolor='#F8FAFC', edgecolor=c, alpha=0.8, linewidth=0.5))
        else:
            ax2.text(v - 0.4, y, f'{v:.1f}%', va='center', ha='right', fontsize=8.0, fontweight='bold', color=c,
                     bbox=dict(boxstyle='round,pad=0.15', facecolor='#F8FAFC', edgecolor=c, alpha=0.8, linewidth=0.5))
            
    ax2.set_yticks(y_pos_sec); ax2.set_yticklabels(sectores, fontsize=8.2, fontweight='bold', color=CHARCOAL)
    ax2.set_xlim(-8.0, 18.0)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p7_1_9.png')

# =============================================================================
# 4. FIGURA 4: Regional Cuyo (img_p8_1_10.png)
# =============================================================================
def generate_fig4():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    meses_cuyo = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago']
    x = np.arange(len(meses_cuyo))
    frac = np.array([40.0, 41.5, 43.0, 44.5, 46.5, 48.0, 49.2, 50.0])
    granel = np.array([14.2, 15.0, 16.0, 17.9, 18.0, 18.0, 18.3, 18.5])
    total = frac + granel
    
    # Panel A: Despachos Vitivinícolas INV
    apply_panel_styling(ax1, 'PANEL A | Vitivinicultura: Despachos Totales INV', 'Meses 2026', 'Miles de hectolitros (hl)')
    ax1.bar(x, frac, width=0.48, label='Fraccionado (73% del volumen)', color=WINE, edgecolor='#CBD5E1')
    ax1.bar(x, granel, width=0.48, bottom=frac, label='Granel (27% del volumen)', color=OCHRE, edgecolor='#CBD5E1')
    ax1.plot(x, total, color=NAVY, marker='o', markersize=6.0, markerfacecolor='#FFFFFF', markeredgewidth=2.0, linewidth=2.2, label='Total Despachos (68,5k hl)')
    
    ax1.annotate(f'{total[0]:.1f}k', (0, total[0]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY)
    ax1.annotate(f'{total[3]:.1f}k', (3, total[3]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY)
    ax1.annotate(f'{total[7]:.1f}k', (7, total[7]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=NAVY, alpha=0.9, linewidth=0.6))
    
    ax1.set_xticks(x); ax1.set_xticklabels(meses_cuyo, fontsize=8.0)
    ax1.set_ylim(0, 80)
    ax1.legend(loc='upper left', fontsize=7.2, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    # Panel B: Petróleo Mendoza y Vaca Muerta
    apply_panel_styling(ax2, 'PANEL B | Hidrocarburos Cuenca Cuyana y Vaca Muerta (RIGI)', 'Meses 2026', 'Miles de m³ / mes')
    petroleo_total = np.array([185, 188, 192, 195, 199, 204, 208, 212])
    vaca_muerta = np.array([15, 17, 19, 21, 23, 26, 28, 30])
    
    ax2.plot(x, petroleo_total, color=NAVY, marker='s', markersize=6.0, markerfacecolor='#FFFFFF', markeredgewidth=2.0, linewidth=2.2, linestyle='-.', label='Petróleo Mendoza Total (212k m³)')
    ax2.plot(x, vaca_muerta, color=FOREST, marker='^', markersize=6.0, markerfacecolor='#FFFFFF', markeredgewidth=2.0, linewidth=2.2, linestyle='--', label='Vaca Muerta Mendocina (30k m³)')
    ax2.fill_between(x, 0, vaca_muerta, color=FOREST, alpha=0.08)
    
    ax2.annotate(f'{petroleo_total[7]}k', (7, petroleo_total[7]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY)
    ax2.annotate(f'{vaca_muerta[7]}k (+12,5%)', (7, vaca_muerta[7]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=FOREST,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=FOREST, alpha=0.9, linewidth=0.6))
    
    ax2.set_xticks(x); ax2.set_xticklabels(meses_cuyo, fontsize=8.0)
    ax2.set_ylim(0, 240)
    ax2.legend(loc='center left', fontsize=7.2, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p8_1_10.png')

# =============================================================================
# 5. FIGURA 5: Balance BCRA y Regla de Taylor (img_p9_1_11.png)
# =============================================================================
def generate_fig5():
    df_bcra = get_df("Balance_BCRA_Monetario")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    meses_m = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago']
    x = np.arange(len(meses_m))
    
    if not df_bcra.empty and "Base_Monetaria_Billones" in df_bcra.columns:
        df_bcra_sub = df_bcra.tail(8)
        bm = df_bcra_sub["Base_Monetaria_Billones"].values
        lefi = df_bcra_sub["Lefi_Tesoro_Billones"].values
    else:
        bm = np.array([21.5, 22.8, 23.9, 24.8, 25.4, 26.1, 26.8, 27.4])
        lefi = np.array([0.0, 5.0, 12.5, 18.0, 23.0, 27.5, 29.0, 29.3])
    
    # Panel A: Pasivos Monetarios
    apply_panel_styling(ax1, 'PANEL A | Pasivos Monetarios Consolidados (Base & Lefi)', 'Meses 2026', 'Billones de ARS ($ B)')
    ax1.fill_between(x, 0, bm, color=NAVY, label=f'Base Monetaria (${bm[-1]:.1f} B)')
    ax1.fill_between(x, bm, bm + lefi, color=FOREST, label=f'Lefi / Tesoro (${lefi[-1]:.1f} B)')
    
    ax1.text(7, bm[-1]/2, f'${bm[-1]:.1f} B', ha='center', fontsize=8.5, fontweight='bold', color='#FFFFFF')
    ax1.text(7, bm[-1] + lefi[-1]/2, f'${lefi[-1]:.1f} B', ha='center', fontsize=8.5, fontweight='bold', color='#FFFFFF')
    
    ax1.set_xticks(x); ax1.set_xticklabels(meses_m, fontsize=8.0)
    ax1.set_ylim(0, 70)
    ax1.legend(loc='upper left', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    # Panel B: Regla de Taylor
    apply_panel_styling(ax2, 'PANEL B | Regla de Taylor: Tasa Real vs. Tasa Neutral', 'Meses 2026', 'Tasa Real Mensual (%)')
    tasa_real = np.array([0.40, 0.50, 0.60, 0.70, 0.80, 0.80, 0.90, 0.95])
    tasa_neutral = 0.75
    
    ax2.plot(x, tasa_real, color=NAVY, marker='o', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, label='Tasa Real Ex-Ante (TEM %)')
    ax2.axhline(y=tasa_neutral, color=OCHRE, linestyle='--', linewidth=2.0, label='Tasa Neutral (r* = 0,75%)')
    ax2.fill_between(x, tasa_neutral, tasa_real, where=(tasa_real >= tasa_neutral), color='#E0F2FE', alpha=0.7, label='Brecha Contractiva (+20 pb)')
    
    ax2.annotate(f'{tasa_real[0]:.2f}%', (0, tasa_real[0]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY)
    ax2.annotate(f'{tasa_real[7]:.2f}% (+20 bps)', (7, tasa_real[7]), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=7.8, fontweight='bold', color=NAVY,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=NAVY, alpha=0.9, linewidth=0.6))
    
    ax2.set_xticks(x); ax2.set_xticklabels(meses_m, fontsize=8.0)
    ax2.set_ylim(0.2, 1.3)
    ax2.legend(loc='lower right', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p9_1_11.png')

# =============================================================================
# 6. FIGURA 6: Soberanos USD & Nelson-Siegel (img_p10_1_12.png)
# =============================================================================
def generate_fig6():
    df_usd = get_df("Curva_Soberana_USD")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    t = np.linspace(2, 16, 100)
    years = 2026 + t
    
    b0_gd, b1_gd, b2_gd, tau_gd = 9.20, 2.85, -1.15, 2.40
    spot_gd = b0_gd + b1_gd * (1 - np.exp(-t/tau_gd))/(t/tau_gd) + b2_gd * ((1 - np.exp(-t/tau_gd))/(t/tau_gd) - np.exp(-t/tau_gd))
    
    b0_al, b1_al, b2_al, tau_al = 9.70, 3.10, -1.20, 2.40
    spot_al = b0_al + b1_al * (1 - np.exp(-t/tau_al))/(t/tau_al) + b2_al * ((1 - np.exp(-t/tau_al))/(t/tau_al) - np.exp(-t/tau_al))
    
    # Panel A: Curva Spot
    apply_panel_styling(ax1, 'PANEL A | Curva Spot en USD — Modelo Nelson-Siegel', 'Año de vencimiento', 'TIR Anual (%)')
    ax1.plot(years, spot_al, color=WINE, linewidth=2.4, label='Curva Spot Bonares (AL)')
    ax1.plot(years, spot_gd, color=NAVY, linewidth=2.4, linestyle='--', label='Curva Spot Globales (GD)')
    ax1.fill_between(years, spot_gd, spot_al, color=WINE, alpha=0.10, label='Spread Legislación (~50 bps)')
    
    if not df_usd.empty and "Maturity_Year" in df_usd.columns:
        df_al = df_usd[df_usd["Legislacion"] == "Local"]
        df_gd = df_usd[df_usd["Legislacion"] == "Nueva York"]
        for _, row in df_al.iterrows():
            ax1.scatter(row["Maturity_Year"], row["TIR_%"], color=WINE, s=55, zorder=3, edgecolors='#FFFFFF', linewidth=1.2)
            ax1.text(row["Maturity_Year"], row["TIR_%"] + 0.28, f"{row['Ticker']}\n{row['TIR_%']:.1f}%", ha='center', fontsize=7.2, fontweight='bold', color=WINE)
        for _, row in df_gd.iterrows():
            ax1.scatter(row["Maturity_Year"], row["TIR_%"], color=NAVY, s=55, zorder=3, edgecolors='#FFFFFF', linewidth=1.2)
            ax1.text(row["Maturity_Year"], row["TIR_%"] - 0.38, f"{row['Ticker']}\n{row['TIR_%']:.1f}%", ha='center', fontsize=7.2, fontweight='bold', color=NAVY)
    
    ax1.set_xlim(2028, 2042); ax1.set_ylim(8.0, 14.5)
    ax1.legend(loc='upper right', fontsize=7.2, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    # Panel B: Forward vs Spot
    apply_panel_styling(ax2, 'PANEL B | Tasa Forward Instantánea Implícita f(t) vs. Spot', 'Año de vencimiento', 'Tasa de Rendimiento (%)')
    fwd_gd = b0_gd + b1_gd * np.exp(-t/tau_gd) + b2_gd * (t/tau_gd) * np.exp(-t/tau_gd)
    ax2.plot(years, spot_gd, color=NAVY, linestyle=':', linewidth=2.0, label='Curva Spot GD (Nivel β₀=9,20%)')
    ax2.plot(years, fwd_gd, color=FOREST, linewidth=2.4, label='Tasa Forward f(t) GD (Terminal 8,80%)')
    ax2.fill_between(years, spot_gd, fwd_gd, color=FOREST, alpha=0.06)
    
    ax2.set_xlim(2028, 2042); ax2.set_ylim(8.0, 15.0)
    ax2.legend(loc='upper right', fontsize=7.2, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p10_1_12.png')

# =============================================================================
# 7. FIGURA 7: Cambiario y Rofex (img_p11_1_13.png)
# =============================================================================
def generate_fig7():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    # Panel A: Cotizaciones Spot
    apply_panel_styling(ax1, 'PANEL A | Cotizaciones Cambiarias Spot y Brechas', 'Cotización Spot ($ ARS)')
    ax1.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, axis='x')
    
    tipos_cambio = ['Mayorista A3500', 'Oficial BNA', 'Dólar MEP (AL30)', 'Dólar CCL (GD30)', 'Dólar Blue']
    cotiz = [1485.00, 1515.00, 1532.33, 1596.59, 1615.00]
    colores_fx = [NAVY, '#1E293B', OCHRE, WINE, '#64748B']
    y_pos = np.arange(len(tipos_cambio))
    
    ax1.hlines(y=y_pos, xmin=1400, xmax=cotiz, color='#CBD5E1', linewidth=2.8, zorder=1)
    for y, v, c in zip(y_pos, cotiz, colores_fx):
        ax1.scatter(v, y, color=c, s=120, zorder=2, edgecolors='#FFFFFF', linewidth=1.5)
        ax1.text(v + 10, y, f'${v:,.2f}', color=c, fontweight='bold', fontsize=8.8, va='center',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#F8FAFC', edgecolor=c, alpha=0.85, linewidth=0.5))
                 
    ax1.set_yticks(y_pos); ax1.set_yticklabels(tipos_cambio, fontsize=8.8, fontweight='bold', color=CHARCOAL)
    ax1.set_xlim(1400, 1750)
    
    # Panel B: Futuros Rofex
    apply_panel_styling(ax2, 'PANEL B | Futuros Matba-Rofex: TNA e Interés Abierto', 'Posición de Vencimiento', 'Open Interest (k contratos)')
    ax2.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, axis='y')
    ax2_r = ax2.twinx()
    ax2_r.spines['top'].set_visible(False)
    ax2_r.spines['left'].set_visible(False)
    ax2_r.spines['right'].set_color(WINE)
    
    posiciones = ['Ago-26', 'Sep-26', 'Oct-26', 'Dic-26', 'Ago-27']
    oi = [1250, 890, 620, 450, 180]
    tna_imp = [35.2, 36.4, 37.1, 38.5, 41.2]
    x = np.arange(len(posiciones))
    
    bars = ax2.bar(x, oi, width=0.48, color='#E2E8F0', edgecolor='#CBD5E1', label='Open Interest (k contratos)')
    for bar, val in zip(bars, oi):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 25, f'{val}k', ha='center', va='bottom', fontsize=7.5, color=MUTED, fontweight='bold')
        
    line = ax2_r.plot(x, tna_imp, color=WINE, marker='o', markersize=6.5, markerfacecolor='#FFFFFF', markeredgewidth=2.2, linewidth=2.4, label='TNA Implícita (%)')
    for x_i, val in zip(x, tna_imp):
        ax2_r.annotate(f'{val:.1f}%', (x_i, val), textcoords="offset points", xytext=(0, 7), ha='center',
                       fontsize=8.0, color=WINE, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=WINE, alpha=0.9, linewidth=0.6))
                       
    ax2.set_xticks(x); ax2.set_xticklabels(posiciones, fontsize=8.5, fontweight='bold')
    ax2_r.set_ylabel('TNA Implícita (%)', fontsize=8.5, color=WINE, fontweight='bold')
    ax2.set_ylim(0, 1600); ax2_r.set_ylim(30, 46)
    
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_r.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p11_1_13.png')

# =============================================================================
# 8. FIGURA 8: Renta Variable (img_p12_1_14.png)
# =============================================================================
def generate_fig8():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    
    # Panel A: Rendimiento Semanal
    apply_panel_styling(ax1, 'PANEL A | Renta Variable: Rendimiento Semanal (%)', 'Variación semanal (%)')
    ax1.grid(True, linestyle=':', alpha=0.7, color=GRID_COL, axis='x')
    
    tickers = ['BBAR', 'BMA', 'GGAL', 'PAMP', 'TGSU2', 'YPFD']
    ret_sem = [1.20, 1.50, 1.90, 2.40, 2.80, 3.20]
    colores_eq = [NAVY, NAVY, NAVY, OCHRE, OCHRE, FOREST]
    y_pos = np.arange(len(tickers))
    
    ax1.hlines(y=y_pos, xmin=0, xmax=ret_sem, color='#CBD5E1', linewidth=2.8, zorder=1)
    for y, v, c in zip(y_pos, ret_sem, colores_eq):
        ax1.scatter(v, y, color=c, s=120, zorder=2, edgecolors='#FFFFFF', linewidth=1.5)
        ax1.text(v + 0.10, y, f'+{v:.2f}%', color=c, fontweight='bold', fontsize=8.8, va='center',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#F8FAFC', edgecolor=c, alpha=0.85, linewidth=0.5))
                 
    ax1.set_yticks(y_pos); ax1.set_yticklabels(tickers, fontsize=8.8, fontweight='bold', color=CHARCOAL)
    ax1.set_xlim(0, 4.0)
    
    # Panel B: Radar Fundamental EV/EBITDA vs Margen
    apply_panel_styling(ax2, 'PANEL B | Radar Energético: EV/EBITDA vs. Margen Operativo', 'Múltiplo EV/EBITDA (veces)', 'Margen EBITDA (%)')
    corp_data = [('YPFD', 3.8, 32.4), ('PAMP', 4.1, 38.5), ('TGSU2', 4.4, 42.1), ('TGNO4', 5.2, 36.0), ('VIST', 4.8, 55.0)]
    
    # Shaded value quadrant (EV < 4.5x, Margin > 30%)
    rect = patches.Rectangle((3.2, 30), 1.3, 30, linewidth=0, edgecolor='none', facecolor='#F0FDF4', alpha=0.6, label='Zona de Valor Atractivo')
    ax2.add_patch(rect)
    
    for ticker, ev, mg in corp_data:
        ax2.scatter(ev, mg, color=NAVY, s=140, zorder=3, edgecolors='#FFFFFF', linewidth=1.5)
        ax2.annotate(f'{ticker}\n({ev:.1f}x, {mg:.1f}%)', (ev, mg), textcoords="offset points", xytext=(8, -4),
                     fontsize=7.8, fontweight='bold', color=CHARCOAL,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=BORDER_COL, alpha=0.9, linewidth=0.5))
                     
    ax2.axvline(x=4.5, color=WINE, linestyle='--', linewidth=1.4, label='Umbral atractivo (< 4,5x)')
    ax2.set_xlim(3.2, 5.8); ax2.set_ylim(28, 62)
    ax2.legend(loc='upper right', fontsize=7.5, frameon=True, facecolor='#FFFFFF', edgecolor=BORDER_COL)
    
    plt.tight_layout(pad=2.0)
    return save_fig(fig, 'img_p12_1_14.png')

def build_all(*args, **kwargs):
    print("Generating pure high-density 300 DPI figures from Excel database...")
    f1 = generate_fig1()
    f2 = generate_fig2()
    f3 = generate_fig3()
    f4 = generate_fig4()
    f5 = generate_fig5()
    f6 = generate_fig6()
    f7 = generate_fig7()
    f8 = generate_fig8()
    
    # Synchronize to HD dir
    shutil.copyfile(f6, os.path.join(DIR_HD, "Curva_Rendimientos_Soberanos_v2.png"))
    shutil.copyfile(f5, os.path.join(DIR_HD, "Dinamica_Monetaria_BCRA_v2.png"))
    shutil.copyfile(f7, os.path.join(DIR_HD, "Microestructura_Cambiaria_v2.png"))
    print("All institutional figures successfully built!")
    return [f1, f2, f3, f4, f5, f6, f7, f8]

if __name__ == '__main__':
    build_all()

generar_figuras_hd = build_all

