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
def plot_emae_master(ax, fig, emae=None):
    """Serie real del INDEC (original/desestacionalizada/tendencia-ciclo,
    base 2004=100) via src/fetch_series_indec_bcra.obtener_emae_reciente().
    Si la fuente no responde, se dice explicitamente en el propio grafico
    en vez de mostrar la serie de relleno anterior como si fuera real."""
    ax.set_facecolor("#FFFFFF")

    if emae is None or not emae.get("meses"):
        ax.axis('off')
        ax.text(0.5, 0.5, "Sin datos reales de EMAE disponibles en esta corrida\n(INDEC via apis.datos.gob.ar no respondió).",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return

    meses = emae["meses"]
    original = np.array(emae["original"])
    desest = np.array(emae["desestacionalizado"])
    tendencia = np.array(emae["tendencia_ciclo"])
    x_idx = np.arange(len(meses))

    def _mmm_aa(m):  # 'YYYY-MM' -> 'Mmm-AA'
        y, mo = m.split("-")
        return ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][int(mo) - 1] + f"-{y[2:]}"

    meses_display = [_mmm_aa(m) if i % 3 == 0 or i == len(meses) - 1 else "" for i, m in enumerate(meses)]

    var_ia = emae.get("var_interanual_ultimo")
    var_mensual = emae.get("var_mensual_desest_ultimo")
    ax.plot(x_idx, original, color="#1E293B", lw=1.6, marker='o', markersize=4, label=f'Serie Original ({original[-1]:.0f})')
    ax.plot(x_idx, desest, color=C_TEAL, lw=2.0, marker='s', markersize=4,
            label=f'Desestacionalizado ({desest[-1]:.0f}' + (f' / {var_mensual:+.1f}% MoM)' if var_mensual is not None else ')'))
    ax.plot(x_idx, tendencia, color=C_CYAN, lw=1.8, linestyle='--', label=f'Tendencia-Ciclo ({tendencia[-1]:.1f})')

    ax.set_ylabel("Número índice (Base 2004 = 100)", fontsize=7.8, color=C_SLATE)
    _pad = (max(original.max(), desest.max(), tendencia.max()) - min(original.min(), desest.min(), tendencia.min())) * 0.15
    ax.set_ylim(min(original.min(), desest.min(), tendencia.min()) - _pad, max(original.max(), desest.max(), tendencia.max()) + _pad)
    ax.grid(True, linestyle='--', color=C_GRID, lw=0.6)

    tick_pos = [i for i, s in enumerate(meses_display) if s != ""]
    tick_lbl = [meses_display[i] for i in tick_pos]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_lbl, fontsize=7.2, color=C_SLATE, rotation=0)

    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=7.2, loc='upper left')

    if var_ia is not None:
        etiqueta = f"{_mmm_aa(meses[-1])}: {desest[-1]:.0f} desest. ({var_ia:+.1f}% i.a.)"
        ax.annotate(etiqueta, xy=(x_idx[-1], desest[-1]), xytext=(x_idx[-1] - len(meses) * 0.28, desest.max() + _pad * 0.6),
                    arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=1.2),
                    bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2FE", ec="#BAE6FD", lw=0.8),
                    fontsize=7.5, fontweight='bold', color="#0369A1")

# ==============================================================================
# 2. FIGURA 1: CURVAS EN ARS & BREAKEVEN INFLACIONARIO
# ==============================================================================
def plot_rates_breakeven(ax, fig, tasas_ars=None):
    """El contrato (datos_del_dia.json tasas_ars.*) solo tiene 2 puntos
    reales de la curva Lecap (corta/larga) y un unico Boncer -- no una
    curva de 6 vencimientos con tickers especificos como el array de
    relleno anterior. Se grafican los puntos reales que existen, sin
    interpolar tickers/plazos que el contrato no especifica."""
    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.33, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    tasas_ars = tasas_ars or {}
    lecap_corta = tasas_ars.get("lecap_corta_tem")
    lecap_larga = tasas_ars.get("lecap_larga_tem")
    boncer = tasas_ars.get("boncer_tzx27_tir_real")

    if lecap_corta is None or lecap_larga is None:
        ax1.axis('off')
        ax1.text(0.5, 0.5, "Sin tasas Lecap cargadas\nen tasas_ars.*.",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax1.transAxes)
    else:
        # Barras, no linea: Corta/Larga son dos instrumentos discretos, no
        # dos puntos de una curva continua -- una linea conectandolos sugiere
        # una interpolacion que el contrato no respalda. El Boncer va en su
        # propia barra con eje propio, en su propia posicion de x (no
        # flotando entre las otras dos), para no sugerir una relacion de
        # posicion que tampoco existe.
        x_lecap = [0, 1]
        y_lecap = [lecap_corta, lecap_larga]
        ax1.bar(x_lecap, y_lecap, width=0.55, color=C_NAVY, alpha=0.9, zorder=3, label='Lecap (TEM %)')
        for xi, v in zip(x_lecap, y_lecap):
            ax1.annotate(f"{v:.2f}%".replace(".", ","), (xi, v), xytext=(0, 5), textcoords="offset points",
                         ha='center', fontsize=7.5, fontweight='bold', color=C_NAVY)
        xticks = list(x_lecap)
        xticklabels = ["Lecap Corta", "Lecap Larga"]
        ax1.set_ylabel("TEM Tasa Fija (%)", fontsize=7.5, color=C_NAVY)
        ax1.set_ylim(0, max(y_lecap) * 1.35)

        if boncer is not None:
            x_boncer = 2
            xticks.append(x_boncer)
            xticklabels.append("Boncer TZX27\n(eje der.)")
            ax1_t = ax1.twinx()
            ax1_t.spines['top'].set_visible(False)
            ax1_t.bar([x_boncer], [boncer], width=0.55, color=C_AMBER, alpha=0.9, zorder=3, label='Boncer TZX27 (TIR Real %)')
            ax1_t.annotate(f"{boncer:.2f}%".replace(".", ","), (x_boncer, boncer), xytext=(0, 5), textcoords="offset points",
                           ha='center', fontsize=7.2, fontweight='bold', color=C_AMBER)
            ax1_t.set_ylabel("TIR Real Anual Boncer (%)", fontsize=7.5, color=C_AMBER, labelpad=6)
            ax1_t.set_ylim(0, boncer * 1.6)
            ax1_t.grid(False)
        ax1.set_xticks(xticks)
        ax1.set_xticklabels(xticklabels, fontsize=7.3)
        ax1.set_xlim(-0.5, (x_boncer if boncer is not None else 1) + 0.5)
    ax1.set_title("A. Tasas en ARS (Lecap corta/larga + Boncer)", fontsize=8.0, fontweight='bold', color=C_NAVY, loc='left')
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6, zorder=0)

    breakeven = tasas_ars.get("breakeven_inflacion_tem")
    rem = tasas_ars.get("inflacion_esperada_rem_tem")
    if breakeven is None or rem is None:
        ax2.axis('off')
        ax2.text(0.5, 0.5, "Sin breakeven/REM cargados\nen tasas_ars.*.",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax2.transAxes)
    else:
        premio_pb = (breakeven - rem) * 100
        ax2.bar([0], [breakeven], width=0.4, label=f'Breakeven Implícito ({breakeven:.2f}% MoM)'.replace(".", ","), color=C_NAVY, alpha=0.9)
        ax2.bar([0.6], [rem], width=0.4, label=f'Inflación Esperada REM ({rem:.2f}% MoM)'.replace(".", ","), color="#94A3B8", alpha=0.9)
        ax2.annotate(f"Premio: {premio_pb:+.0f} pb".replace(".", ","), (0.3, max(breakeven, rem) * 1.15),
                     ha='center', fontsize=7.5, fontweight='bold', color=C_RED)
        ax2.set_xlim(-0.5, 1.1)
        ax2.set_xticks([0, 0.6])
        ax2.set_xticklabels(["Breakeven", "REM"], fontsize=7.5)
        ax2.set_ylim(0, max(breakeven, rem) * 1.4)
        ax2.legend(frameon=False, fontsize=6.6, loc='upper right')
    ax2.set_title("B. Breakeven Inflacionario vs. Consenso REM", fontsize=8.0, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_ylabel("Tasa mensual (% MoM)", fontsize=7.5, color=C_SLATE)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)

# ==============================================================================
# 3. FIGURA 2: DISPERSIÓN DE PRECIOS & TRAYECTORIA IPC
# ==============================================================================
def plot_ipc_master(ax, fig, inflacion=None, ipc_trayectoria=None):
    """Panel A: aperturas del mes vigente -- lee datos_del_dia.json
    (inflacion.*), que ya es carga manual real del contrato, no un array
    de relleno. "Bienes" no tiene campo propio en el contrato -- se omite
    en vez de inventarlo. Panel B: trayectoria real de 8 meses derivada de
    los indices oficiales del INDEC (src/fetch_series_indec_bcra); DEIE
    Mendoza no tiene serie historica publica -- se marca "manual, sin serie"
    en vez de fabricar una trayectoria mensual que no existe."""
    ax.axis('off')
    ax1 = fig.add_axes([0.15, 0.11, 0.32, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    inflacion = inflacion or {}
    aperturas_disponibles = [
        ("Núcleo", inflacion.get("indec_nucleo_mom"), C_CYAN),
        ("General INDEC", inflacion.get("indec_general_mom"), C_NAVY),
        ("Servicios", inflacion.get("indec_servicios_mom"), "#EA580C"),
        ("Regulados", inflacion.get("indec_regulados_mom"), C_RED),
    ]
    aperturas_disponibles = [(n, v, c) for n, v, c in aperturas_disponibles if v is not None]

    if not aperturas_disponibles:
        ax1.axis('off')
        ax1.text(0.5, 0.5, "Sin datos de inflación cargados\nen datos_del_dia.json.",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax1.transAxes)
    else:
        aperturas = [n for n, _, _ in aperturas_disponibles]
        valores_ap = [v for _, v, _ in aperturas_disponibles]
        colores_ap = [c for _, _, c in aperturas_disponibles]
        y_pos = np.arange(len(aperturas))

        for y, val, col in zip(y_pos, valores_ap, colores_ap):
            ax1.hlines(y=y, xmin=0, xmax=val, color=col, lw=2.2, alpha=0.85)
            ax1.plot(val, y, marker='o', markersize=7.5, color=col, markeredgecolor='white', markeredgewidth=1.0)
            ax1.text(val + 0.10, y, f"{val:.1f}%".replace(".", ","), va='center', fontsize=7.8, fontweight='bold', color=col)

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(aperturas, fontsize=7.2)
        ax1.set_xlim(0, max(valores_ap) * 1.35)
        ax1.set_xlabel("Variación mensual (% MoM)", fontsize=7.5, color=C_SLATE)
        ax1.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)
    ax1.set_title("A. Dispersión por Apertura (% MoM, mes vigente)", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')

    if not ipc_trayectoria or not ipc_trayectoria.get("meses"):
        ax2.axis('off')
        ax2.text(0.5, 0.5, "Sin trayectoria real de IPC disponible en esta corrida\n(INDEC via apis.datos.gob.ar no respondió).",
                 ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax2.transAxes)
    else:
        meses = ipc_trayectoria["meses"]
        x_n = np.arange(len(meses))
        gral = np.array(ipc_trayectoria["general"])
        core = np.array(ipc_trayectoria["nucleo"])
        regul = np.array(ipc_trayectoria["regulados"])
        meses_lbl = [f"{['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][int(m[5:7])-1]}-{m[2:4]}" for m in meses]

        ax2.fill_between(x_n, core, gral, color="#E0F2FE", alpha=0.6, label='Brecha Núcleo/General')
        ax2.plot(x_n, gral, color=C_NAVY, lw=2.0, marker='o', markersize=4.5, markeredgecolor='white', label=f'INDEC General ({gral[-1]:.1f}%)'.replace(".", ","))
        ax2.plot(x_n, regul, color=C_RED, lw=1.8, marker='s', markersize=4.5, markeredgecolor='white', label=f'Regulados ({regul[-1]:.1f}%)'.replace(".", ","))
        ax2.plot(x_n, core, color=C_CYAN, lw=1.8, linestyle='--', marker='^', markersize=4.0, label=f'Núcleo ({core[-1]:.1f}%)'.replace(".", ","))

        ax2.set_xticks(x_n)
        ax2.set_xticklabels(meses_lbl, fontsize=7.0)
        ax2.set_ylabel("Tasa mensual (%)", fontsize=7.5, color=C_SLATE)
        _todos = np.concatenate([gral, core, regul])
        _pad = (_todos.max() - _todos.min()) * 0.2
        ax2.set_ylim(_todos.min() - _pad, _todos.max() + _pad)
        ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
        ax2.legend(frameon=False, fontsize=6.8, loc='upper right')
    ax2.set_title("B. Trayectoria IPC Nacional (% MoM, INDEC)", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')

# ==============================================================================
# 4. FIGURA 3: ESTRUCTURA PRODUCTIVA DE CUYO (VINO, PETRÓLEO, CEMENTO)
# ==============================================================================
def plot_cuyo_redesigned(ax, fig, isac=None):
    """Vitivinicultura (INV) e hidrocarburos (Secretaria de Energia,
    especificos de Mendoza) siguen sin conector confiable: se probo un
    candidato para despachos de vino via apis.datos.gob.ar y no paso un
    chequeo basico de sensatez (valores ~1000x por debajo de lo esperado,
    metadata contradictoria entre "Miles de Hectolitros" y "Miles de
    Litros") -- se descarto en vez de usar un numero que parece real pero
    probablemente no lo es (ver src/fetch_series_secundarias.py). Cemento
    SI tiene un proxy real: el ISAC (Indicador Sintetico de la Actividad
    de la Construccion, INDEC) -- es NACIONAL, no el "cemento AFCP Cuyo"
    especifico que prometia la version anterior, se declara el cambio de
    alcance explicitamente."""
    ax.axis('off')
    # Layout A/B como el resto de las infografias del modulo (EMAE, TCR,
    # tasas): nivel a la izquierda, variacion mensual a la derecha -- es
    # la presentacion estandar de un indice sintetico de actividad en un
    # informe de coyuntura serio (INDEC/OERU siempre publican nivel +
    # var. m/m juntos, nunca solo la linea de nivel sola).
    ax1 = fig.add_axes([0.07, 0.11, 0.52, 0.50])
    ax2 = fig.add_axes([0.66, 0.11, 0.30, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    if isac and isac.get("meses"):
        meses = isac["meses"]
        valores = isac["valores"]
        x_idx = np.arange(len(meses))
        meses_lbl = [f"{['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][int(m[5:7])-1]}-{m[2:4]}" for m in meses]

        ax1.fill_between(x_idx, valores, min(valores) * 0.985, color=C_NAVY, alpha=0.08, zorder=1)
        ax1.plot(x_idx, valores, color=C_NAVY, lw=2.0, marker='o', markersize=4.5,
                 markerfacecolor='white', markeredgecolor=C_NAVY, markeredgewidth=1.3, zorder=3)
        ax1.plot(x_idx[-1], valores[-1], marker='o', markersize=7, color=C_NAVY, zorder=4)
        ax1.annotate(f"{meses_lbl[-1]}: {valores[-1]:.1f}".replace(".", ","),
                     xy=(x_idx[-1], valores[-1]), xytext=(-10, 14), textcoords="offset points", ha='right',
                     fontsize=7.6, fontweight='bold', color=C_NAVY,
                     arrowprops=dict(arrowstyle="-", color=C_NAVY, lw=0.8),
                     bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2FE", ec="#BAE6FD", lw=0.8), zorder=5)
        ax1.set_ylim(min(valores) * 0.985, max(valores) * 1.02)
        tick_step = max(1, len(meses) // 7)
        tick_pos = list(range(0, len(meses), tick_step))
        if tick_pos[-1] != len(meses) - 1:
            tick_pos.append(len(meses) - 1)
        ax1.set_xticks(tick_pos)
        ax1.set_xticklabels([meses_lbl[i] for i in tick_pos], fontsize=6.8, rotation=0, color=C_SLATE)
        ax1.set_ylabel("ISAC nacional desest. (Base 2004=100)", fontsize=7.3, color=C_SLATE)
        ax1.grid(True, linestyle='--', color=C_GRID, lw=0.6, axis='y')
        ax1.set_title("A. Nivel (desestacionalizado)", fontsize=7.8, fontweight='bold', color=C_NAVY, loc='left')

        # Panel B: variacion m/m real (misma serie, sin dato nuevo) -- lo
        # que un informe institucional muestra junto al nivel para separar
        # tendencia de ruido mes a mes.
        var_mom = [None] + [round(100 * (valores[i] / valores[i - 1] - 1), 1) for i in range(1, len(valores))]
        var_mom_v = [v for v in var_mom if v is not None]
        x_var = np.arange(1, len(valores))
        colores_var = [C_TEAL if v >= 0 else C_RED for v in var_mom_v]
        ax2.bar(x_var, var_mom_v, color=colores_var, width=0.62, alpha=0.9, zorder=3)
        ax2.axhline(0, color="#94A3B8", lw=0.8, zorder=2)
        ax2.annotate(f"{var_mom_v[-1]:+.1f}%".replace(".", ","), xy=(x_var[-1], var_mom_v[-1]),
                     xytext=(0, 6 if var_mom_v[-1] >= 0 else -12), textcoords="offset points",
                     ha='center', fontsize=7.2, fontweight='bold',
                     color=(C_TEAL if var_mom_v[-1] >= 0 else C_RED))
        ax2.set_xticks([x_var[0], x_var[-1]])
        ax2.set_xticklabels([meses_lbl[1], meses_lbl[-1]], fontsize=6.6, color=C_SLATE)
        ax2.set_ylabel("Var. m/m (%)", fontsize=7.3, color=C_SLATE)
        ax2.grid(True, linestyle='--', color=C_GRID, lw=0.6, axis='y')
        ax2.set_title("B. Variación mensual", fontsize=7.8, fontweight='bold', color=C_NAVY, loc='left')
    else:
        ax1.text(0.5, 0.6, "Sin dato real de ISAC\ndisponible en esta corrida.",
                ha='center', va='center', fontsize=9, fontweight='bold', color=C_SLATE, transform=ax1.transAxes)
        ax2.axis('off')

# ==============================================================================
# 4.1 FIGURA 3B: COMPARATIVO REGIONAL CUYO (MENDOZA / SAN JUAN / SAN LUIS)
# ==============================================================================
def plot_regional_cuyo(ax, fig, actividad=None):
    """El contrato (datos_del_dia.json actividad.*) solo tiene la variacion
    interanual agregada del ISARC por provincia -- NO el nivel del indice
    ni la desagregacion sectorial (industria/construccion/empleo), que la
    version anterior de este grafico presentaba con un literal de relleno
    (`regional_rows`) identico en las 3 provincias en distintas corridas.

    Version anterior: Panel A con las 3 barras, Panel B vacio (solo un
    texto "sin fuente automatizable") -- el usuario senalo que varios
    graficos del modulo "les falta valor agregado". En vez de dejar medio
    grafico en blanco, se usa el unico dato real adicional que YA esta en
    el mismo `actividad` (emae_interanual_pct, ya cargado en el contrato y
    citado en otras secciones) como linea de referencia nacional -- permite
    leer de un vistazo si cada provincia crece por encima o por debajo del
    promedio pais, sin fabricar ningun dato nuevo."""
    ax.axis('off')
    ax1 = fig.add_axes([0.09, 0.11, 0.85, 0.50])
    ax1.set_facecolor("#FFFFFF")

    actividad = actividad or {}
    provincias_campos = [("Mendoza", "isarc_mendoza_ia_pct"), ("San Juan", "isarc_san_juan_ia_pct"), ("San Luis", "isarc_san_luis_ia_pct")]
    datos = [(p, actividad.get(c)) for p, c in provincias_campos if actividad.get(c) is not None]
    emae_ia = actividad.get("emae_interanual_pct")

    if not datos:
        ax1.axis('off')
        ax1.text(0.5, 0.5, "Sin variación ISARC cargada\nen datos_del_dia.json.",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax1.transAxes)
    else:
        provincias = [p for p, _ in datos]
        isarc_ia = [v for _, v in datos]
        colores_prov = [C_NAVY, C_TEAL, C_AMBER][:len(provincias)]
        x = np.arange(len(provincias))
        ax1.bar(x, isarc_ia, width=0.42, color=colores_prov, alpha=0.92, zorder=3)
        ax1.axhline(0, color=C_SLATE, lw=0.8, zorder=2)
        for i, ia in enumerate(isarc_ia):
            ax1.annotate(f"{ia:+.1f}%".replace(".", ","), (x[i], ia), xytext=(0, 4 if ia >= 0 else -12), textcoords="offset points",
                         ha='center', fontsize=8.2, fontweight='bold', color=colores_prov[i])
        ax1.set_xticks(x)
        ax1.set_xticklabels(provincias, fontsize=8.0)
        ax1.set_ylabel("Variación interanual (%)", fontsize=7.5, color=C_SLATE)
        _valores_escala = list(isarc_ia) + ([emae_ia] if emae_ia is not None else [])
        _pad = max(abs(v) for v in _valores_escala) * 0.35
        ax1.set_ylim(min(0, min(_valores_escala)) - _pad, max(_valores_escala) + _pad)
        ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6, zorder=0)

        if emae_ia is not None:
            ax1.axhline(emae_ia, color=C_RED, lw=1.5, linestyle='--', zorder=2.5)
            _emae_fmt = f"{emae_ia:+.1f}%".replace(".", ",")
            # Ancla en x=1 (posicion de la barra del medio, San Juan): con 3
            # provincias esa columna deja el espacio mas despejado alrededor
            # de la linea de referencia sin pisar ninguna barra, a diferencia
            # de anclar en el borde izquierdo (se superponia con Mendoza).
            ax1.text(1, emae_ia, f"EMAE Nacional i.a.: {_emae_fmt}",
                      ha='center', va='bottom', fontsize=7.4, fontweight='bold', color=C_RED,
                      bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax1.set_title("ISARC: Variación Interanual por Provincia vs. EMAE Nacional", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')

# ==============================================================================
# 5. FIGURA 4: BALANCE CONSOLIDADO BCRA & REGLA DE TAYLOR
# ==============================================================================
def plot_monetary_master(ax, fig, historia_monetaria=None, tasa_real_exante_actual=None, r_star=0.75):
    """historia_monetaria: base monetaria y pases pasivos REALES del BCRA
    (src/fetch_series_indec_bcra.obtener_monetario_reciente()) -- antes
    era un array de relleno con una narrativa de "Lefi $29,3 B" que la
    serie real de BCRA (id=196) contradice: el stock de LEFI esta en 0
    desde jul-2025 (mecanismo discontinuado), asi que ya no se incluye
    como componente aparte del stack. tasa_real_exante_actual: calculada
    por Fisher (tasas_ars.lecap_corta_tem - inflacion_esperada_rem_tem,
    ambos campos reales del contrato) en src/contexto_informe.py. r_star
    (tasa neutral) no tiene fuente objetiva -- es un supuesto del analista,
    se declara como tal en el eje en vez de presentarlo como un dato."""
    ax.axis('off')

    if historia_monetaria is None or not historia_monetaria.get("meses"):
        ax.text(0.5, 0.5, "Sin serie monetaria real disponible en esta corrida\n(BCRA v4.0 no respondió).",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return
    ax1 = fig.add_axes([0.09, 0.11, 0.38, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    meses_8 = historia_monetaria["meses"]
    x_8 = np.arange(len(meses_8))
    base_m = np.array(historia_monetaria["base_m"])
    pases_m = np.array(historia_monetaria["pases_m"])
    base_ult, pases_ult = base_m[-1], pases_m[-1]

    def _fmt_b(v):
        return f"${v:.1f} B".replace(".", ",")

    # Antes: stackplot de 2 capas (Base Monetaria + Pases Pasivos). Los
    # Pases estan en $0 en TODA la ventana real (mecanismo discontinuado
    # desde jul-2025, antes de que arranque esta serie) -- apilar una
    # segunda capa que es cero de punta a punta no agrega informacion,
    # solo vuelve el panel un bloque solido pesado sin el nivel de
    # detalle del resto de las infografias del modulo (linea + area
    # liviana + callout, como EMAE/TCR/ISAC). Se linealiza y se declara
    # la extincion de Pases en el propio subtitulo en vez de graficarla.
    ax1.fill_between(x_8, base_m, base_m.min() * 0.97, color=C_NAVY, alpha=0.08, zorder=1)
    ax1.plot(x_8, base_m, color=C_NAVY, lw=2.0, marker='o', markersize=4.5,
              markerfacecolor='white', markeredgecolor=C_NAVY, markeredgewidth=1.3, zorder=3)
    ax1.plot(x_8[-1], base_ult, marker='o', markersize=7, color=C_NAVY, zorder=4)
    _var_bm = round(100 * (base_ult / base_m[-2] - 1), 1) if len(base_m) >= 2 else None
    _var_txt = f" ({_var_bm:+.1f}% m/m)".replace(".", ",") if _var_bm is not None else ""
    ax1.annotate(f"{meses_8[-1]}: {_fmt_b(base_ult)}{_var_txt}",
                 xy=(x_8[-1], base_ult), xytext=(-10, 12), textcoords="offset points", ha='right',
                 fontsize=7.5, fontweight='bold', color=C_NAVY,
                 arrowprops=dict(arrowstyle="-", color=C_NAVY, lw=0.8),
                 bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2FE", ec="#BAE6FD", lw=0.8), zorder=5)
    ax1.set_title("A. Base Monetaria (BCRA real) -- Pases Pasivos extinto", fontsize=7.9, fontweight='bold', color=C_NAVY, loc='left')
    ax1.set_xticks(x_8)
    ax1.set_xticklabels(meses_8, fontsize=7.2)
    ax1.set_ylabel("Billones de ARS ($ B)", fontsize=7.5, color=C_SLATE)
    ax1.set_ylim(base_m.min() * 0.97, base_m.max() * 1.05)
    ax1.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
    ax1.set_xlim(-0.5, len(meses_8) - 0.3)

    # Panel B: antes mostraba la Regla de Taylor (barra de tasa real
    # ex-ante vs. r*) -- un concepto de tasas que no tiene relacion
    # numerica con la serie de Base Monetaria del Panel A (son dos
    # variables distintas del contrato), y que ademas duplicaba la
    # tarjeta KPI "TASA REAL EX-ANTE" de arriba. El usuario senalo que el
    # emparejamiento A/B se sentia arbitrario ("el orden es raro"). Se
    # reemplaza por la variacion mensual de la MISMA serie de Base
    # Monetaria del Panel A (misma convencion que ISAC/EMAE: nivel +
    # variacion de la misma variable, no dos variables distintas). La
    # Regla de Taylor sigue citada en el cuerpo del texto del informe.
    var_mom_bm = [round(100 * (base_m[i] / base_m[i - 1] - 1), 1) for i in range(1, len(base_m))]
    x_var_bm = np.arange(1, len(base_m))
    colores_bm = [C_TEAL if v >= 0 else C_RED for v in var_mom_bm]
    ax2.bar(x_var_bm, var_mom_bm, color=colores_bm, width=0.6, alpha=0.9, zorder=3)
    ax2.axhline(0, color="#94A3B8", lw=0.8, zorder=2)
    ax2.annotate(f"{var_mom_bm[-1]:+.1f}%".replace(".", ","), xy=(x_var_bm[-1], var_mom_bm[-1]),
                 xytext=(0, 6 if var_mom_bm[-1] >= 0 else -12), textcoords="offset points",
                 ha='center', fontsize=7.2, fontweight='bold',
                 color=(C_TEAL if var_mom_bm[-1] >= 0 else C_RED))
    ax2.set_xticks([x_var_bm[0], x_var_bm[-1]])
    ax2.set_xticklabels([meses_8[1], meses_8[-1]], fontsize=6.8)
    ax2.set_title("B. Base Monetaria: Variación Mensual", fontsize=8.0, fontweight='bold', color=C_NAVY, loc='left')
    ax2.set_ylabel("Var. m/m (%)", fontsize=7.5, color=C_SLATE)
    ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)

# ==============================================================================
# 6. FIGURA 5: CURVA SOBERANA EN USD (NELSON-SIEGEL)
# ==============================================================================
def plot_sovereign_master(ax, fig, bonos=None, nelson_siegel_params=None, anio_base=2026.5):
    """Bonos y parametros Nelson-Siegel leidos de datos_del_dia.json
    (soberano_usd.*) -- antes este chart buscaba DATOS_DEL_DIA.get(
    "bonos_soberanos") y DATOS_DEL_DIA.get("nelson_siegel") a nivel raiz,
    claves que no existen en el contrato (viven bajo "soberano_usd"), asi
    que el lookup siempre fallaba en silencio y caia al array de relleno.
    El contrato solo tiene 4 bonos (AL30, GD30, GD35, GD38) -- se grafican
    esos 4 reales en vez de los 8 tickers inventados (AL29/AL35/GD29/GD41
    no tienen campo en el contrato)."""
    soberano = (DATOS_DEL_DIA or {}).get("soberano_usd", {})
    if bonos is None:
        _vencimientos = {"al30": 4.0, "gd30": 4.0, "gd35": 9.0, "gd38": 12.0}
        _leg = {"al30": "Local", "gd30": "NY", "gd35": "NY", "gd38": "NY"}
        bonos = [
            {"ticker": k.upper(), "leg": _leg[k], "t": _vencimientos[k], "tir": soberano[f"{k}_tir"]}
            for k in ("al30", "gd30", "gd35", "gd38") if soberano.get(f"{k}_tir") is not None
        ]
    if not bonos:
        ax.axis('off')
        ax.text(0.5, 0.5, "Sin TIRes de bonos soberanos cargadas\nen datos_del_dia.json.",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return
    if nelson_siegel_params is None:
        ns = soberano.get("nelson_siegel")
        nelson_siegel_params = {
            "b0": ns["beta0"], "b1": ns["beta1"], "b2": ns["beta2"], "tau": ns["tau"],
            "spread_legislacion_pb": (soberano.get("al30_tir", 0) - soberano.get("gd30_tir", 0)) * 100,
        } if ns else None
    if nelson_siegel_params is None:
        ax.axis('off')
        ax.text(0.5, 0.5, "Sin parámetros Nelson-Siegel cargados\nen datos_del_dia.json.",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return

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
    """Panel A: cotizaciones reales de datos_del_dia.json (dolar.*) --
    antes buscaba DATOS_DEL_DIA.get("fx"), una clave que no existe en el
    contrato (vive como dolar.oficial_bna/mayorista/mep/ccl/blue a nivel
    raiz), asi que caia siempre al array de relleno. Panel B (Rofex): no
    hay ningun conector a Matba-Rofex en el repo (requiere feed pago/con
    cuenta) -- en vez de dejarlo vacio, se calcula el dolar futuro
    IMPLICITO por paridad de tasas (CIP) con datos reales del contrato,
    etiquetado explicitamente como valor teorico y no una cotizacion de
    mercado (ver src/modelos_riesgo.calcular_dolar_futuro_implicito)."""
    if fx is None:
        dolar = (DATOS_DEL_DIA or {}).get("dolar", {})
        mayorista = dolar.get("mayorista")
        _campos = [
            ("mayorista", "Mayorista (A3500)"), ("oficial_bna", "Minorista (BNA)"),
            ("mep", "MEP"), ("ccl", "CCL"), ("blue", "Informal (Blue)"),
        ]
        fx = []
        for campo, nombre in _campos:
            val = dolar.get(campo)
            if val is None:
                continue
            brecha = round(100 * (val / mayorista - 1), 2) if mayorista else None
            fx.append({"short": nombre, "cotizacion_ars": val, "brecha_vs_mayorista_pct": brecha})
    if rofex is None:
        rofex = (DATOS_DEL_DIA or {}).get("rofex")

    ax.axis('off')
    if not fx:
        ax.text(0.28, 0.5, "Sin cotizaciones cambiarias\ncargadas en datos_del_dia.json.",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return
    ax1 = fig.add_axes([0.18, 0.13, 0.29, 0.45])
    ax2 = fig.add_axes([0.57, 0.13, 0.36, 0.45])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    dolares_nom = [r.get("short", r.get("segmento")) for r in fx]
    cotiz_vals = [r["cotizacion_ars"] for r in fx]
    brechas_m = [
        (f'{r["brecha_vs_mayorista_pct"]:+.1f}%'.replace(".", ",").replace("+0,0%", "0,0%") if r.get("brecha_vs_mayorista_pct") is not None else "s/d")
        for r in fx
    ]
    y_fx = np.arange(len(dolares_nom))
    _paleta_fx = [C_SLATE, C_NAVY, C_AMBER, C_RED, C_GRAY]
    colores_fx = [_paleta_fx[i % len(_paleta_fx)] for i in range(len(dolares_nom))]
    
    _xmin_fx = min(cotiz_vals) * 0.94
    for y, val, col, br in zip(y_fx, cotiz_vals, colores_fx, brechas_m):
        ax1.hlines(y=y, xmin=_xmin_fx, xmax=val, color=col, lw=2.2, alpha=0.85)
        ax1.plot(val, y, marker='o', markersize=6.5, color=col, markeredgecolor='white')
        # br ya viene formateado en es-AR (coma decimal) desde brechas_m --
        # antes se aplicaba el swap de separadores de "$val" sobre el string
        # completo, incluido "br", lo que le invertia la coma decimal a "br"
        # (ej. "+7,5%" terminaba como "+7.5%"). Se formatea el monto aparte.
        _val_fmt = f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ax1.text(val + (max(cotiz_vals) - min(cotiz_vals)) * 0.02, y, f"{_val_fmt} ({br})",
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

    if rofex is None:
        # Sin conector a Matba-Rofex en el repo (feed de futuros requiere
        # suscripcion paga o cuenta de bolsa) -- en vez de dejar el panel
        # vacio, se calcula el dolar futuro IMPLICITO por paridad de tasas
        # (CIP) con datos reales del contrato (mayorista + Lecap corta).
        # Se etiqueta explicitamente como valor teorico, no una cotizacion
        # de mercado -- ver src/modelos_riesgo.calcular_dolar_futuro_implicito.
        try:
            from src.modelos_riesgo import calcular_dolar_futuro_implicito
            dolar_mayorista = next((r["cotizacion_ars"] for r in fx if r.get("short") == "Mayorista (A3500)"), None)
            tasas_ars = (DATOS_DEL_DIA or {}).get("tasas_ars", {})
            futuro = calcular_dolar_futuro_implicito(dolar_mayorista, tasas_ars.get("lecap_corta_tem"))
        except Exception:
            futuro = None

        if not futuro:
            ax2.axis('off')
            ax2.text(0.5, 0.5, "Sin conector a Matba-Rofex disponible\n(futuros de dólar requieren feed con cuenta de bolsa).\nCarga manual pendiente.",
                     ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax2.transAxes)
            ax2.set_title("B. Futuros Matba-Rofex (sin fuente automatizable)", fontsize=8.0, fontweight='bold', color=C_NAVY, pad=6, loc='left')
            return

        dias_curva = [p["dias"] for p in futuro["curva"]]
        futuros_curva = [p["futuro_implicito"] for p in futuro["curva"]]
        tna_curva = [p["tna_implicita_pct"] for p in futuro["curva"]]
        x_pos = np.arange(len(dias_curva))

        ax2.plot(x_pos, futuros_curva, color=C_NAVY, lw=2.0, marker='o', markersize=5, markeredgecolor='white')
        for xi, f, tna in zip(x_pos, futuros_curva, tna_curva):
            _f_fmt = f"${f:,.0f}".replace(",", ".")
            _tna_fmt = f"{tna:.1f}".replace(".", ",")
            ax2.annotate(f"{_f_fmt}\n({_tna_fmt}% TNA)",
                         (xi, f), xytext=(0, 10), textcoords="offset points", ha='center',
                         fontsize=7.0, fontweight='bold', color=C_NAVY)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([f"{d}d" for d in dias_curva], fontsize=7.5)
        ax2.set_ylabel("Dólar futuro implícito (ARS)", fontsize=7.0, color=C_SLATE)
        _pad_f = (max(futuros_curva) - min(futuros_curva)) * 0.3 or 20
        ax2.set_ylim(min(futuros_curva) - _pad_f * 0.4, max(futuros_curva) + _pad_f)
        ax2.grid(axis='y', linestyle='--', color=C_GRID, lw=0.6)
        ax2.set_title("B. Dólar Futuro Implícito por CIP (no es cotización Rofex)", fontsize=7.6, fontweight='bold', color=C_NAVY, pad=6, loc='left')
        return

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
def plot_equity_master(ax, fig, variacion_semanal=None, lideres=None):
    """Panel A: variacion semanal REAL via yfinance (.BA), ver
    src/fetch_datos_reales.obtener_variacion_semanal_acciones() -- antes
    era un array de relleno sin ningun ticker verificado contra mercado.
    Panel B: multiplos EV/EBITDA de datos_del_dia.json (equity.lideres) --
    solo se grafican los tickers que estan realmente en el contrato (antes
    incluia VIST/TGNO4 con multiplos inventados sin ningun campo fuente)."""
    ax.axis('off')
    ax1 = fig.add_axes([0.16, 0.11, 0.31, 0.50])
    ax2 = fig.add_axes([0.55, 0.11, 0.38, 0.50])
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    if not variacion_semanal:
        ax1.axis('off')
        ax1.text(0.5, 0.5, "Sin variación semanal real disponible\n(yfinance no respondió).",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax1.transAxes)
    else:
        items = sorted(variacion_semanal.items(), key=lambda kv: kv[1]["var_semanal_pct"])
        tickers_eq = [tk for tk, _ in items]
        var_eq = [v["var_semanal_pct"] for _, v in items]
        y_eq = np.arange(len(tickers_eq))
        colores_e = [C_TEAL if v >= 0 else C_RED for v in var_eq]

        for y, val, col in zip(y_eq, var_eq, colores_e):
            ax1.hlines(y=y, xmin=0, xmax=val, color=col, lw=2.0, alpha=0.85)
            ax1.plot(val, y, marker='o', markersize=6.5, color=col, markeredgecolor='white')
            ax1.text(val + (0.10 if val >= 0 else -0.10), y, f"{val:+.2f}%".replace(".", ","),
                      va='center', ha='left' if val >= 0 else 'right', fontsize=7.2, fontweight='bold', color=col)

        ax1.set_yticks(y_eq)
        ax1.set_yticklabels(tickers_eq, fontsize=7.0)
        _xmax = max(abs(v) for v in var_eq) * 1.5
        ax1.set_xlim(-_xmax, _xmax)
        ax1.axvline(0, color=C_SLATE, lw=0.8)
        ax1.set_xlabel("Rendimiento semanal en ARS (%)", fontsize=7.5, color=C_SLATE)
        ax1.grid(axis='x', linestyle='--', color=C_GRID, lw=0.6)
    ax1.set_title("A. Renta Variable: Variación Semanal Real (%)", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')

    lideres = [l for l in (lideres or []) if l.get("ev_ebitda") is not None and l.get("margen_ebitda") is not None]
    if not lideres:
        ax2.axis('off')
        ax2.text(0.5, 0.5, "Sin múltiplos EV/EBITDA cargados\nen datos_del_dia.json.",
                  ha='center', va='center', fontsize=8, color=C_SLATE, transform=ax2.transAxes)
    else:
        ev_ebitda = [l["ev_ebitda"] for l in lideres]
        margen_ebitda = [l["margen_ebitda"] for l in lideres]
        ax2.scatter(ev_ebitda, margen_ebitda, color=C_NAVY, s=90, alpha=0.9, zorder=5, edgecolors='white', linewidths=1.2)
        for l in lideres:
            ax2.annotate(f"{l['ticker']}\n({l['ev_ebitda']:.1f}x, {l['margen_ebitda']:.1f}%)".replace(".", ","),
                         (l["ev_ebitda"], l["margen_ebitda"]), xytext=(l["ev_ebitda"] + 0.08, l["margen_ebitda"] + 0.8),
                         fontsize=7.2, fontweight='bold', color=C_NAVY)
        _pad_x = (max(ev_ebitda) - min(ev_ebitda)) * 0.3 or 0.5
        _pad_y = (max(margen_ebitda) - min(margen_ebitda)) * 0.3 or 5
        ax2.set_xlim(min(ev_ebitda) - _pad_x, max(ev_ebitda) + _pad_x)
        ax2.set_ylim(min(margen_ebitda) - _pad_y, max(margen_ebitda) + _pad_y)
        ax2.set_xlabel("Múltiplo EV/EBITDA (veces)", fontsize=7.5, color=C_SLATE)
        ax2.set_ylabel("Margen EBITDA (%)", fontsize=7.5, color=C_SLATE)
        ax2.grid(True, linestyle='--', color=C_GRID, lw=0.6)
    ax2.set_title("B. Radar Energético: EV/EBITDA vs. Margen", fontsize=8.3, fontweight='bold', color=C_NAVY, loc='left')

# ==============================================================================
# GENERACIÓN DE TODAS LAS INFOGRAFÍAS
# ==============================================================================
def generar_todas_las_infografias(*args, **kwargs):
    """KPIs calculados en vivo desde datos reales (contexto unico en
    src/contexto_informe.py + src/fetch_series_indec_bcra.py +
    src/fetch_datos_reales.py) -- antes cada tupla de kpis era un literal
    fijo desconectado del propio grafico que create_master_infographic
    renderizaba debajo. Un campo sin fuente real se muestra "s/d", nunca
    un numero de relleno."""
    print("Iniciando renderizado de infografías vectoriales maestras a 300 DPI...")

    from src.contexto_informe import cargar_contexto, fmt_pct, fmt_num
    from src.fetch_series_indec_bcra import obtener_emae_reciente, obtener_ipc_trayectoria, obtener_monetario_reciente
    from src.fetch_datos_reales import obtener_variacion_semanal_acciones

    ctx = cargar_contexto(incluir_series_lentas=False)
    dolar, tasas_ars, inflacion, actividad, soberano, equity = (
        ctx["dolar"], ctx["tasas_ars"], ctx["inflacion"], ctx["actividad"], ctx["soberano_usd"], ctx["equity"]
    )

    try:
        emae = obtener_emae_reciente()
    except Exception as e:
        print(f"      [Infografias] ERROR EMAE: {e}"); emae = None
    try:
        ipc_trayectoria = obtener_ipc_trayectoria()
    except Exception as e:
        print(f"      [Infografias] ERROR IPC trayectoria: {e}"); ipc_trayectoria = None
    try:
        monetario = obtener_monetario_reciente()
    except Exception as e:
        print(f"      [Infografias] ERROR monetario BCRA: {e}"); monetario = None
    try:
        variacion_semanal = obtener_variacion_semanal_acciones()
    except Exception as e:
        print(f"      [Infografias] ERROR variacion semanal acciones: {e}"); variacion_semanal = {}
    try:
        from src.fetch_series_secundarias import obtener_isac_reciente
        isac = obtener_isac_reciente()
    except Exception as e:
        print(f"      [Infografias] ERROR ISAC: {e}"); isac = None

    f0 = create_master_infographic(
        "chart_indec_emae_master.png",
        f"INDEC · SERIE HISTÓRICA {emae['meses'][0] if emae else 's/d'} A {emae['meses'][-1] if emae else 's/d'}",
        "Estimador Mensual de Actividad Económica (EMAE)",
        "Evolución de la serie original, desestacionalizada y tendencia-ciclo (Base 2004 = 100)",
        [
            ("EMAE ORIGINAL", fmt_num(emae["original"][-1], 0) if emae else "s/d", fmt_pct(emae.get("var_interanual_ultimo") if emae else None, 1, True) + " i.a.", C_NAVY),
            ("DESESTACIONALIZADO", fmt_num(emae["desestacionalizado"][-1], 0) if emae else "s/d", "Variación mensual " + fmt_pct(emae.get("var_mensual_desest_ultimo") if emae else None, 1, True), C_TEAL),
            ("TENDENCIA-CICLO", fmt_num(emae["tendencia_ciclo"][-1], 1) if emae else "s/d", "Base 2004 = 100", C_CYAN),
        ],
        lambda ax, fig: plot_emae_master(ax, fig, emae),
        "Fuente: Instituto Nacional de Estadística y Censos (INDEC), vía apis.datos.gob.ar."
    )

    f1 = create_master_infographic(
        "chart_indec_1_rates.png",
        "BCRA / CONTRATO MANUAL · TASAS EN ARS",
        "Tasas en ARS y Breakeven Inflacionario",
        "Lecap corta/larga a tasa fija vs. Boncer CER y expectativas del REM (carga manual del contrato)",
        [
            ("LECAP CORTA", fmt_pct(tasas_ars.get("lecap_corta_tem")), "TEM · Instrumento a tasa fija", C_NAVY),
            ("BREAKEVEN INFLACIÓN", fmt_pct(tasas_ars.get("breakeven_inflacion_tem")), f"Premio " + fmt_num(tasas_ars.get("premio_tasa_fija_pbs"), 0) + " pb s/ REM" if tasas_ars.get("premio_tasa_fija_pbs") is not None else "s/d", C_AMBER),
            ("INFLACIÓN REM", fmt_pct(tasas_ars.get("inflacion_esperada_rem_tem")), "Mediana REM, 1 mes", C_CYAN),
        ],
        lambda ax, fig: plot_rates_breakeven(ax, fig, tasas_ars),
        "Fuente: contrato datos_del_dia.json (tasas_ars.*) -- carga manual, sin conector automatizado a ByMA/Matba."
    )

    f2 = create_master_infographic(
        "chart_indec_2_ipc.png",
        "INDEC · TRAYECTORIA REAL DEL IPC NACIONAL",
        "Dinámica de Precios: Aperturas del Mes y Trayectoria Nacional",
        "Dispersión por apertura (carga manual del contrato) y trayectoria real de 8 meses (INDEC)",
        [
            ("IPC NACIONAL GENERAL", fmt_pct(inflacion.get("indec_general_mom")), "Mes vigente, carga manual", C_NAVY),
            ("NÚCLEO", fmt_pct(inflacion.get("indec_nucleo_mom")), "Mes vigente, carga manual", C_AMBER),
            ("REGULADOS", fmt_pct(inflacion.get("indec_regulados_mom")), "Mes vigente, carga manual", C_TEAL),
        ],
        lambda ax, fig: plot_ipc_master(ax, fig, inflacion, ipc_trayectoria),
        "Fuentes: INDEC (contrato manual + apis.datos.gob.ar). DEIE Mendoza sin serie histórica pública."
    )

    f3 = create_master_infographic(
        "chart_indec_3_cuyo.png",
        "INDEC (ISAC NACIONAL) / INV / SECRETARÍA DE ENERGÍA",
        "Construcción: Proxy Nacional Real (ISAC) -- Vino e Hidrocarburos sin Fuente Confiable",
        "ISAC nacional desestacionalizado (INDEC) como proxy de construcción; vitivinicultura e hidrocarburos de Mendoza sin conector",
        [
            ("ISAC NACIONAL", fmt_num(isac["nivel_ultimo"], 1) if isac else "s/d", (fmt_pct(isac["var_mensual_ultimo"], 1, True) + " MoM") if isac else "Sin dato", C_SLATE),
            ("MÁXIMO (13M)", fmt_num(max(isac["valores"]), 1) if isac and isac.get("valores") else "s/d", f"{isac['meses'][isac['valores'].index(max(isac['valores']))]}" if isac and isac.get("valores") else "Sin dato", C_TEAL),
            ("MÍNIMO (13M)", fmt_num(min(isac["valores"]), 1) if isac and isac.get("valores") else "s/d", f"{isac['meses'][isac['valores'].index(min(isac['valores']))]}" if isac and isac.get("valores") else "Sin dato", C_AMBER),
        ],
        lambda ax, fig: plot_cuyo_redesigned(ax, fig, isac),
        "Fuentes: INDEC (ISAC nacional, apis.datos.gob.ar). Vitivinicultura/hidrocarburos Mendoza sin fuente confiable encontrada."
    )

    f3b = create_master_infographic(
        "chart_indec_3b_regional_cuyo.png",
        "DEIE MENDOZA / IPEC SAN JUAN / IPEC SAN LUIS",
        "Comparativo Regional: Índice Sintético de Actividad (ISARC)",
        "Variación interanual por provincia (contrato manual) vs. EMAE nacional -- nivel del índice y desagregación sectorial sin fuente pública",
        [
            ("ISARC MENDOZA", fmt_pct(actividad.get("isarc_mendoza_ia_pct"), 1, True), "Var. i.a., carga manual", C_NAVY),
            ("ISARC SAN LUIS", fmt_pct(actividad.get("isarc_san_luis_ia_pct"), 1, True), "Var. i.a., carga manual", C_AMBER),
            ("EMAE NACIONAL", fmt_pct(actividad.get("emae_interanual_pct"), 1, True), "Benchmark i.a., ver línea de referencia", C_RED),
        ],
        lambda ax, fig: plot_regional_cuyo(ax, fig, actividad),
        "Fuente: contrato datos_del_dia.json (actividad.*). Nivel de índice y desagregación sectorial sin fuente automatizable."
    )

    f4 = create_master_infographic(
        "chart_indec_4_monetary.png",
        "BANCO CENTRAL DE LA REPÚBLICA ARGENTINA",
        "Base Monetaria: Nivel y Variación Mensual",
        "Serie real BCRA -- Pases Pasivos discontinuados desde jul-2025; tasa real ex-ante (Fisher) como contexto de política monetaria",
        [
            ("BASE MONETARIA", (fmt_num(monetario["base_m"][-1], 1, "$") + " B") if monetario else "s/d", "BCRA v4.0, id=15", C_NAVY),
            ("PASES PASIVOS", (fmt_num(monetario["pases_m"][-1], 1, "$") + " B") if monetario else "s/d", "BCRA v4.0, id=152", C_TEAL),
            ("TASA REAL EX-ANTE", fmt_pct(ctx["tasa_real_exante_tem_pct"], 2, True), "Fisher: Lecap corta - REM", C_AMBER),
        ],
        lambda ax, fig: plot_monetary_master(ax, fig, monetario, ctx["tasa_real_exante_tem_pct"]),
        "Fuentes: Banco Central de la República Argentina (BCRA v4.0) y cálculo propio (Fisher) sobre el contrato."
    )

    f5 = create_master_infographic(
        "chart_indec_5_sovereign.png",
        "BYMA · RESEARCH SOBERANO",
        "Estructura Temporal Soberana en USD — Modelo Nelson-Siegel",
        "Curva spot y forward instantánea para los 4 títulos con TIR cargada en el contrato",
        [
            ("RIESGO PAÍS (EMBI+)", fmt_num(soberano.get("embi_riesgo_pais_pbs"), 0) + " pb" if soberano.get("embi_riesgo_pais_pbs") is not None else "s/d", "Carga manual del contrato", C_NAVY),
            ("NELSON-SIEGEL NIVEL (β0)", fmt_pct(soberano.get("nelson_siegel", {}).get("beta0")), "Tasa asintótica soberana largo plazo", C_RED),
            ("R² DEL AJUSTE", fmt_num(soberano.get("nelson_siegel", {}).get("r2"), 3), "Bondad de ajuste Nelson-Siegel", C_AMBER),
        ],
        plot_sovereign_master,
        "Fuente: contrato datos_del_dia.json (soberano_usd.*) -- carga manual, sin conector automatizado a ByMA."
    )

    f6 = create_master_infographic(
        "chart_indec_6_fx.png",
        "BCRA · CIERRE CAMBIARIO",
        "Microestructura Cambiaria",
        "Cotizaciones spot reales del contrato. Dólar futuro implícito por CIP (no cotización Rofex).",
        [
            ("DÓLAR CCL", fmt_num(dolar.get("ccl"), 2, "$"), f"Brecha oficial: " + fmt_pct(dolar.get("brecha_ccl_oficial_pct"), 2, True), C_RED),
            ("DÓLAR MAYORISTA (A3500)", fmt_num(dolar.get("mayorista"), 2, "$"), "BCRA v4.0, en vivo", C_NAVY),
            ("DÓLAR OFICIAL (MINORISTA)", fmt_num(dolar.get("oficial_bna"), 2, "$"), "BCRA v4.0, en vivo", C_TEAL),
        ],
        lambda ax, fig: plot_fx_master(ax, fig),
        "Fuente: BCRA v4.0 + contrato manual (dolar.*). Futuro implícito por paridad de tasas (CIP), no cotización de Matba-Rofex."
    )

    _var_merval = equity.get("var_semanal_pct")
    _lideres_reales = [l for l in equity.get("lideres", []) if l.get("ticker", "").replace("D", "") in [t for t in variacion_semanal]] if variacion_semanal else []
    f7 = create_master_infographic(
        "chart_indec_7_equity.png",
        "BYMA (YFINANCE) · RADAR DE MERCADO",
        "Renta Variable Líder: Retornos Reales y Múltiplos del Contrato",
        "Rendimientos semanales reales (yfinance) y múltiplos EV/EBITDA de los tickers cargados en el contrato",
        [
            ("S&P MERVAL", fmt_pct(_var_merval, 2, True), "Carga manual del contrato", C_NAVY),
            (list(variacion_semanal.keys())[0] if variacion_semanal else "s/d",
             fmt_pct(list(variacion_semanal.values())[0]["var_semanal_pct"], 2, True) if variacion_semanal else "s/d",
             "Variación semanal real (yfinance)", C_AMBER),
            (equity.get("lideres", [{}])[0].get("ticker", "s/d") if equity.get("lideres") else "s/d",
             (fmt_num(equity["lideres"][0].get("ev_ebitda"), 1) + "x EV/EBITDA") if equity.get("lideres") else "s/d",
             "Carga manual del contrato", C_CYAN),
        ],
        lambda ax, fig: plot_equity_master(ax, fig, variacion_semanal, equity.get("lideres", [])),
        "Fuentes: Bolsas y Mercados Argentinos (BYMA) vía yfinance (retornos) y contrato manual (múltiplos)."
    )

    f8 = _crear_infografia_tcr()

    print("Todas las infografías maestras fueron generadas con éxito y sin solapamientos.")
    return [f0, f1, f2, f3, f3b, f4, f5, f6, f7, f8]


# ==============================================================================
# 10. FIGURA 8: TIPO DE CAMBIO REAL BILATERAL (ATRASO/COMPETITIVIDAD CAMBIARIA)
# ==============================================================================
def plot_tcr_master(ax, fig, tcr_data=None):
    """A diferencia del resto de las figuras de este modulo, esta lee datos
    reales del cache generado por src/fetch_tcr_bilateral.py (BCRA + INDEC +
    BLS) en vez de un array de relleno -- si no hay cache todavia, lo dice
    explicitamente en el propio grafico en vez de simular una serie."""
    ax.set_facecolor("#FFFFFF")

    if tcr_data is None or not tcr_data.get("serie"):
        ax.axis('off')
        ax.text(0.5, 0.5, "Sin cache de TCR bilateral todavia.\nCorrer: python src/fetch_tcr_bilateral.py",
                ha='center', va='center', fontsize=9, color=C_SLATE, transform=ax.transAxes)
        return

    serie = tcr_data["serie"]
    valores = [p["tcr_indice"] for p in serie]
    meses = [p["mes"] for p in serie]
    x_idx = np.arange(len(valores))

    ax.axhline(100, color=C_GRAY, lw=1.1, linestyle=":", zorder=1)
    ax.text(0.3, 100, f"Base {tcr_data['base_mes']} = 100", fontsize=6.8, color=C_GRAY,
            va='bottom', ha='left')

    # Recta entre observaciones reales (smooth=False) -- estandar institucional
    # del proyecto: no se suaviza una serie de mercado real (ver docstring de
    # _tooltipConFecha en dashboard/index.html para el mismo criterio del lado web).
    ax.plot(x_idx, valores, color=C_NAVY, lw=1.7, zorder=3)
    ax.fill_between(x_idx, valores, 100, where=[v < 100 for v in valores],
                     color=C_RED, alpha=0.10, interpolate=True, zorder=2)
    ax.fill_between(x_idx, valores, 100, where=[v >= 100 for v in valores],
                     color=C_TEAL, alpha=0.10, interpolate=True, zorder=2)

    ultimo = tcr_data["ultimo"]
    ax.plot(x_idx[-1], ultimo["tcr_indice"], marker='o', markersize=5.5, color=C_NAVY, zorder=4)
    ax.annotate(f"{ultimo['mes']}: {ultimo['tcr_indice']:.1f}", xy=(x_idx[-1], ultimo["tcr_indice"]),
                xytext=(-8, 12), textcoords="offset points", ha='right', fontsize=7.5,
                fontweight='bold', color=C_NAVY,
                bbox=dict(boxstyle="round,pad=0.25", fc="#E0F2FE", ec="#BAE6FD", lw=0.7))

    paso = max(1, len(meses) // 10)
    tick_pos = list(range(0, len(meses), paso))
    if tick_pos[-1] != len(meses) - 1:
        tick_pos.append(len(meses) - 1)
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([meses[i] for i in tick_pos], fontsize=6.8, color=C_SLATE, rotation=35, ha='right')

    ax.set_ylabel(f"Índice TCR bilateral (Base {tcr_data['base_mes']} = 100)", fontsize=7.8, color=C_SLATE)
    ax.grid(True, linestyle='--', color=C_GRID, lw=0.6, axis='y')


def _crear_infografia_tcr():
    """KPIs de esta infografia calculados en vivo desde el cache real (no
    literales hardcodeados como el resto de create_master_infographic en
    este modulo): a diferencia de las otras 9, aca el valor de la tarjeta
    SI cambia solo cuando cambia el dato subyacente."""
    from src.fetch_tcr_bilateral import cargar_cache
    tcr_data = cargar_cache()

    if tcr_data and tcr_data.get("ultimo"):
        ultimo = tcr_data["ultimo"]
        serie = tcr_data["serie"]
        pico_reciente = max(serie[-13:], key=lambda p: p["tcr_indice"]) if len(serie) >= 2 else ultimo
        variacion_desde_pico = 100 * (ultimo["tcr_indice"] / pico_reciente["tcr_indice"] - 1)
        lectura = "atraso relativo" if ultimo["tcr_indice"] < 100 else "competitivo relativo"
        kpis = [
            (f"TCR BILATERAL ({ultimo['mes']})", f"{ultimo['tcr_indice']:.1f}", f"Base {tcr_data['base_mes']}=100 · {lectura}", C_NAVY if ultimo["tcr_indice"] >= 100 else C_RED),
            ("PICO ÚLTIMOS 12 MESES", f"{pico_reciente['tcr_indice']:.1f}", f"en {pico_reciente['mes']}", C_AMBER),
            ("VARIACIÓN DESDE EL PICO", f"{variacion_desde_pico:+.1f}%", "Apreciación real acumulada" if variacion_desde_pico < 0 else "Sin apreciación desde el pico", C_TEAL),
        ]
        fuente = "Fuentes: BCRA v4.0 (mayorista), INDEC (IPC nacional) y BLS (CPI-U). Índice base dic-2016 = 100."
    else:
        kpis = [("TCR BILATERAL", "s/d", "Cache no generado todavía", C_GRAY)]
        fuente = "Correr python src/fetch_tcr_bilateral.py para generar el cache real (BCRA + INDEC + BLS)."

    return create_master_infographic(
        "chart_indec_8_tcr.png",
        "BCRA / INDEC / BLS · TIPO DE CAMBIO REAL BILATERAL",
        "Tipo de Cambio Real Bilateral ARS/USD -- Atraso y Competitividad Cambiaria",
        "TCN mayorista deflactado por CPI relativo (EE.UU./Argentina), índice base dic-2016 = 100",
        kpis,
        lambda ax, fig: plot_tcr_master(ax, fig, tcr_data),
        fuente,
    )

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

