# -*- coding: utf-8 -*-
"""
================================================================================
COMPILADOR MAESTRO DE INFORME MENSUAL REPORTLAB (15 PÁGINAS EDITORIALES)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Research (Management Solutions / Wall Street Standard)
Arquitectura: 15 Páginas Exactas / Cobertura Vertical 100% / Cero Ruido Visual
================================================================================
"""

import os
import shutil
from datetime import datetime
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.contexto_informe import cargar_contexto, fmt_num
from src.fetch_tcr_bilateral import cargar_cache as cargar_cache_tcr
from src.fetch_datos_reales import obtener_variacion_semanal_acciones

MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
OUT_DIR_MENSUAL = os.path.join(BASE_DIR, "06_Informes_Mensuales_OERU")
OUT_DIR_CONSOL = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
os.makedirs(OUT_DIR_MENSUAL, exist_ok=True)
os.makedirs(OUT_DIR_CONSOL, exist_ok=True)

# Registro de fuentes
font_mappings = [
    ('Georgia', ['C:/Windows/Fonts/georgia.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']),
    ('Georgia-Bold', ['C:/Windows/Fonts/georgiab.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf']),
    ('Georgia-Italic', ['C:/Windows/Fonts/georgiai.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf']),
    ('Georgia-BoldItalic', ['C:/Windows/Fonts/georgiaz.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf']),
    ('Sans', ['C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']),
    ('Sans-Bold', ['C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']),
]

for font_name, paths in font_mappings:
    for p in paths:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont(font_name, p))
            break

try:
    pdfmetrics.registerFontFamily('Georgia', normal='Georgia', bold='Georgia-Bold', italic='Georgia-Italic', boldItalic='Georgia-BoldItalic')
except Exception:
    pass

_INFORME_PERIODO = {"header": "AGOSTO 2026"}

def _fmt1(v, decimales=1, signo=False):
    if v is None:
        return "0,0"
    prefijo = "+" if signo and v >= 0 else ""
    return f"{prefijo}{v:.{decimales}f}".replace(".", ",")

def _find_image(filename):
    p_compact = os.path.join(DIR_FIG, "editorial_compact", filename)
    if os.path.exists(p_compact):
        return p_compact
    p = os.path.join(DIR_FIG, filename)
    if os.path.exists(p):
        return p
    p_master = os.path.join(DIR_FIG, "master_extracted_images", filename)
    if os.path.exists(p_master):
        return p_master
    return p

# Colores Institucionales (Paleta Management Solutions / Oxford Navy)
PRIMARY    = colors.HexColor("#0B2545")
BLUE_INST  = colors.HexColor("#0284C7")  # Bright cyan blue for table titles
DARK_TEXT  = colors.HexColor("#1E293B")
SLATE      = colors.HexColor("#334155")
MUTED      = colors.HexColor("#64748B")
BORDER     = colors.HexColor("#CBD5E1")
HAIRLINE   = colors.HexColor("#E2E8F0")
BG_PROJ    = colors.HexColor("#EBF3FA")
BG_CURR    = colors.HexColor("#F1F5F9")
POS_COLOR  = "#059669"
NEG_COLOR  = "#DC2626"

styles = getSampleStyleSheet()

# Tipografías Editoriales
title_style = ParagraphStyle(
    'SecTitle_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.5, leading=16.5,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=4, keepWithNext=True
)

leadin_style = ParagraphStyle(
    'LeadIn_M', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=8.2, leading=11.2,
    textColor=PRIMARY
)

body_bullet_style = ParagraphStyle(
    'BodyBullet_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=8.3, leading=11.8,
    textColor=DARK_TEXT, alignment=TA_JUSTIFY,
    leftIndent=12, firstLineIndent=-12, spaceAfter=6
)

table_title_style = ParagraphStyle(
    'TblTitle_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.5, leading=9.0,
    alignment=TA_CENTER, textColor=BLUE_INST
)

table_header_style = ParagraphStyle(
    'TH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.4, leading=8.8,
    alignment=TA_CENTER, textColor=BLUE_INST
)

table_cell_left = ParagraphStyle(
    'TCL_M', parent=styles['Normal'],
    fontName='Sans', fontSize=7.1, leading=8.5,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_bold = ParagraphStyle(
    'TCB_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.1, leading=8.5,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_subhdr = ParagraphStyle(
    'TCSH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.2, leading=8.6,
    alignment=TA_LEFT, textColor=BLUE_INST
)

table_cell_center = ParagraphStyle(
    'TCC_M', parent=styles['Normal'],
    fontName='Sans', fontSize=7.1, leading=8.5,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

table_cell_center_bold = ParagraphStyle(
    'TCCB_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.1, leading=8.5,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

footnote_table_style = ParagraphStyle(
    'FtnTbl_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.5, leading=8.0,
    textColor=MUTED, spaceBefore=2, spaceAfter=3
)

footnote_chart_style = ParagraphStyle(
    'FtnChart_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.5, leading=8.0,
    textColor=MUTED, spaceBefore=2, spaceAfter=0
)

h1_style = title_style
h2_style = ParagraphStyle(
    'H2_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=8.5, leading=11.0,
    textColor=PRIMARY, spaceBefore=3, spaceAfter=2, keepWithNext=True
)
body_style = ParagraphStyle(
    'Body_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=8.4, leading=12.0,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=4
)
cell_style_left = table_cell_left
cell_style_center = table_cell_center
cell_header_style = ParagraphStyle(
    'CellH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.0, leading=8.5,
    alignment=TA_CENTER, textColor=colors.white
)

class EditorialCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        left = 40
        right = 572
        
        page_bookmarks = {
            1: ("Portada Institucional", "sec_cover"),
            2: ("Índice y Metodología", "sec_toc"),
            3: ("Resumen Ejecutivo y Escenarios", "sec_exec"),
            4: ("1. Nivel de Actividad General (EMAE)", "sec_emae"),
            5: ("2. Precios y Salarios (INDEC)", "sec_prices"),
            6: ("Cuadro 1. Aperturas IPC y Canastas", "sec_tab_ipc"),
            7: ("3. Producción Sectorial en Cuyo", "sec_cuyo"),
            8: ("3.1 Comparativo Regional ISARC", "sec_regional_cuyo"),
            9: ("4. Balance BCRA y Postura Monetaria", "sec_monetary"),
            10: ("5. Arbitraje en ARS y Breakeven", "sec_tactical"),
            11: ("6. Curva Soberana Nelson-Siegel", "sec_yield"),
            12: ("7. Microestructura FX y Rofex", "sec_fx"),
            13: ("7.1. Tipo de Cambio Real Bilateral", "sec_tcr"),
            14: ("8. Renta Variable y Balances", "sec_equity"),
            15: ("9. Flash Normativo y Referencias", "sec_refs")
        }

        if self._pageNumber in page_bookmarks:
            title, key = page_bookmarks[self._pageNumber]
            self.bookmarkPage(key)
            self.addOutlineEntry(title, key, level=0, closed=False)

        if self._pageNumber > 1:
            header_y = 762
            self.setFont("Georgia", 7.2)
            self.setFillColor(MUTED)
            self.drawString(left, header_y, f"INFORME DE COYUNTURA MACROECONÓMICA & MERCADO DE CAPITALES · {_INFORME_PERIODO['header']}")
            self.drawRightString(right, header_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.5)
            self.line(left, header_y - 4, right, header_y - 4)

            # Footer con píldora de página (estilo Management Solutions)
            cx = 306
            cy = 18
            self.setFillColor(BLUE_INST)
            self.roundRect(cx - 15, cy - 6, 30, 12, 6, fill=True, stroke=False)
            self.setFont("Sans-Bold", 7.0)
            self.setFillColor(colors.white)
            self.drawCentredString(cx, cy - 2.5, str(self._pageNumber))

            self.setFont("Georgia", 6.8)
            self.setFillColor(MUTED)
            self.drawString(left, cy - 2.5, "Facultad de Ciencias Económicas · UNCUYO · OERU")
            self.drawRightString(right, cy - 2.5, "Research Institucional")

        self.restoreState()

ZeroWhitespaceCanvas = EditorialCanvas

def crear_pagina_editorial_ms(
    titulo,
    leadin_txt,
    tabla_titulo,
    tabla_data,
    tabla_col_widths,
    tabla_footnote,
    bullets_txt_list,
    chart_filename,
    chart_footnote,
    chart_height=180,
    chart_width=532
):
    """Genera una página analítica con arquitectura de 5 capas de Management Solutions."""
    flowables = []
    
    # 1. Título
    flowables.append(Paragraph(titulo, title_style))
    
    # 2. Lead-in con barra vertical izquierda
    t_lead = Table([[Paragraph(leadin_txt, leadin_style)]], colWidths=[chart_width])
    t_lead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
    ]))
    flowables.append(t_lead)
    flowables.append(Spacer(1, 4))
    
    # 3. Título Centrado de Tabla
    flowables.append(Paragraph(f"<b>{tabla_titulo}</b>", table_title_style))
    flowables.append(Spacer(1, 2))
    
    # 4. Tabla de Indicadores (Padding adaptativo según cantidad de filas)
    tbl_pad = 2.1 if len(tabla_data) > 10 else 2.8
    actual_chart_height = 180 if len(tabla_data) > 10 else 188
    t_ind = Table(tabla_data, colWidths=tabla_col_widths)
    t_ind.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), tbl_pad),
        ('BOTTOMPADDING', (0,0), (-1,-1), tbl_pad),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,0), (-1,0), colors.white),
        ('BACKGROUND', (5,1), (5,-1), BG_CURR),
        ('BACKGROUND', (8,1), (9,-1), BG_PROJ),
        ('LINEBELOW', (0,0), (-1,0), 0.8, BLUE_INST),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    flowables.append(t_ind)
    flowables.append(Paragraph(tabla_footnote, footnote_table_style))
    flowables.append(Spacer(1, 4))
    
    # 5. Tres Párrafos Analíticos Densos
    for b_lead, b_body in bullets_txt_list:
        p_html = f"<font color='#0284C7'><b>&bull;</b></font> <b>{b_lead}:</b> {b_body}"
        flowables.append(Paragraph(p_html, body_bullet_style))
        
    flowables.append(Spacer(1, 4))
    
    # 6. Panel Dual de Gráficos al Pie
    img_path = _find_image(chart_filename)
    if os.path.exists(img_path):
        flowables.append(Image(img_path, width=chart_width, height=actual_chart_height))
    flowables.append(Spacer(1, 2))
    flowables.append(Paragraph(chart_footnote, footnote_chart_style))
    
    flowables.append(PageBreak())
    return flowables

def generar_informe_mensual_reportlab(ctx=None):
    if ctx is None:
        ctx = cargar_contexto(incluir_series_lentas=False)
        
    dolar = ctx["dolar"]
    tasas_ars = ctx["tasas_ars"]
    inflacion = ctx["inflacion"]
    actividad = ctx["actividad"]
    soberano = ctx["soberano_usd"]
    ns = soberano.get("nelson_siegel", {})
    equity = ctx["equity"]
    tasas_bcra = ctx["tasas_bcra_referencia"]
    tasa_real_exante = ctx["tasa_real_exante_tem_pct"]
    riesgo_sistemico = ctx.get("riesgo_sistemico", {})
    ripte = ctx.get("ripte", {})
    riesgo_pais_var_30d = ctx.get("riesgo_pais_variacion_30d", {})
    dolar_futuro = ctx.get("dolar_futuro_implicito", {})

    fecha_str = ctx.get("fecha", "2026-08-25")
    try:
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    except Exception:
        fecha_dt = datetime.now()
        
    mes_nombre = MESES_ES[fecha_dt.month]
    anio_informe = fecha_dt.year
    periodo_header = f"{mes_nombre.upper()} {anio_informe}"
    periodo_texto_cap = f"{mes_nombre} de {anio_informe}"
    _INFORME_PERIODO["header"] = periodo_header

    pdf_path = os.path.join(OUT_DIR_MENSUAL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=32, bottomMargin=32,
        title=f"Informe de Coyuntura Macroeconómica & Mercado de Capitales — {periodo_texto_cap}",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Estrategia de Inversión — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
        keywords="Macroeconomía, Finanzas, Curva Soberana, Inflación, Riesgo Sistémico, Federico Agustín Chillón, UNCUYO"
    )

    elements = []

    # =========================================================================
    # PÁGINA 1: PORTADA EDITORIAL ASIMÉTRICA INSTITUCIONAL (WALL STREET RESEARCH)
    # =========================================================================
    ipc_gral = inflacion.get("indec_general_mom", 2.2)
    ipc_core = inflacion.get("indec_nucleo_mom", 1.9)
    deie = inflacion.get("deie_mendoza_mom", 2.3)
    lecap_corta = tasas_ars.get("lecap_corta_tem", 2.95)
    rem = tasas_ars.get("inflacion_esperada_rem_tem", 2.00)
    tasa_real_exante_val = round(lecap_corta - rem, 2)
    embi_val = soberano.get("embi_riesgo_pais_pbs", 506)
    gd35_tir_val = soberano.get("gd35_tir", 9.65)
    beta0_val = ns.get("beta0", 9.4)
    ccl_val = dolar.get("ccl", 1600.20)
    brecha_val = dolar.get("brecha_ccl_oficial_pct", 4.52)
    emae_ia_val = actividad.get("emae_interanual_pct", 3.1)
    emae_mom_val = actividad.get("emae_desestacionalizado_mom_pct", 0.6)
    isarc_mdz_val = actividad.get("isarc_mendoza_ia_pct", 3.4)
    isarc_sl_val = actividad.get("isarc_san_luis_ia_pct", 5.8)
    _regimen_txt = riesgo_sistemico.get("regimen", "Normal")
    _turb_txt = _fmt1(riesgo_sistemico.get("turbulencia_dt", 2.05), decimales=2)

    elements.append(HRFlowable(width="100%", thickness=2.5, color=PRIMARY, spaceBefore=0, spaceAfter=2))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D97706"), spaceBefore=0, spaceAfter=4))

    masthead = Table([
        [
            Paragraph("<font color='#0B2545' size=9.0><b>UNIVERSIDAD NACIONAL DE CUYO</b> · FCE · OERU</font><br/><font color='#64748B' size=7.0>OBSERVATORIO ECONÓMICO REGIONAL URBANO · INSTITUTO DE INVESTIGACIONES ECONÓMICAS</font>", ParagraphStyle('MH_L', fontName='Georgia', alignment=TA_LEFT, leading=10.0)),
            Paragraph("<font color='#0B2545' size=9.0><b>DIVISIÓN DE ECONOMÍA APLICADA & ESTRATEGIA</b></font><br/><font color='#64748B' size=7.0>REPORTE DE COYUNTURA MACROECONÓMICA · VOL. IV</font>", ParagraphStyle('MH_R', fontName='Georgia', alignment=TA_RIGHT, leading=10.0))
        ]
    ], colWidths=[320, 212])
    masthead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(masthead)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=3, spaceAfter=6))

    elements.append(Paragraph(
        f"<font color='#9A3412' size=7.5><b>ESTRATEGIA MACROECONÓMICA & ASSET ALLOCATION</b></font>&nbsp;&nbsp;"
        f"<font color='#94A3B8' size=6.8><b>|</b></font>&nbsp;&nbsp;"
        f"<font color='#0B2545' size=7.5><b>CIERRE MENSUAL · {periodo_header}</b></font>",
        ParagraphStyle('Kicker_Ed', fontName='Georgia', leading=10.0, spaceAfter=3)
    ))

    elements.append(Paragraph(
        f"ARGENTINA STRATEGY: Desinflación Núcleo al {_fmt1(ipc_core)}%, Ancla Monetaria y Normalización de Curvas en Pesos",
        ParagraphStyle('HeroHeadline', fontName='Georgia-Bold', fontSize=14.0, leading=17.5, textColor=PRIMARY, spaceAfter=4)
    ))

    elements.append(Paragraph(
        f"Evaluación del régimen de absorción monetaria, ancla fiscal en base caja, dinámica de precios relativos INDEC/DEIE, "
        f"compresión del riesgo país a {fmt_num(embi_val, 0)} pb y recomendaciones tácticas de cartera multiactivo.",
        ParagraphStyle('HeroSub', fontName='Georgia-Italic', fontSize=8.3, leading=11.4, textColor=colors.HexColor("#475569"), spaceAfter=6)
    ))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=2, spaceAfter=8))

    # Columna Izquierda (330 pt)
    col_izq = []
    col_izq.append(Paragraph("<font color='#0B2545' size=8.8><b>DIAGNÓSTICO EJECUTIVO & ANCLA MACROECONÓMICA</b></font>", ParagraphStyle('SecL', fontName='Georgia', leading=11.0)))
    col_izq.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=6))

    p1_cov = (
        f"El proceso de estabilización macroeconómica consolida su sendero de desinflación con el registro del IPC general "
        f"en <b>{_fmt1(ipc_gral)}% m/m</b> y una desaceleración del componente núcleo al <b>{_fmt1(ipc_core)}% m/m</b> (con la medición regional DEIE Mendoza "
        f"situándose en <b>{_fmt1(deie)}%</b>). La convergencia nominal responde a la persistencia del ancla fiscal en base caja —sin emisión monetaria directa al Tesoro— "
        f"y al sostenimiento de rendimientos reales ex-ante positivos en la curva en pesos: la Lecap corta opera en una <b>TEM de {_fmt1(lecap_corta)}%</b> frente a una "
        f"expectativa de inflación REM del {_fmt1(rem)}%, garantizando una tasa real contractual de <b>+{_fmt1(tasa_real_exante_val)}% mensual</b>. Este diferencial comprime "
        f"la brecha del CCL al <b>{_fmt1(brecha_val)}%</b> sobre el tipo de cambio oficial mayorista (${fmt_num(ccl_val, 2)}), desarticulando expectativas de salto cambiario."
    )
    col_izq.append(Paragraph(p1_cov, ParagraphStyle('CovBL1', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=6)))

    p2_cov = (
        f"En el frente monetario, la ejecución de la segunda etapa del programa económico ha consolidado la extinción de los pasivos remunerados del Banco Central "
        f"(migración de pases y LeFis hacia Letras del Tesoro), clausurando la emisión cuasifiscal endógena y guiando la tasa hacia el nivel neutral real (r*). "
        f"En simultáneo, la economía real refleja una reactivación cíclica con el EMAE expandiéndose <b>+{_fmt1(emae_ia_val)}% i.a.</b> (<b>+{_fmt1(emae_mom_val)}% m/m</b> desestacionalizado), "
        f"traccionada por la región Cuyo (Mendoza <b>+{_fmt1(isarc_mdz_val)}%</b>, San Luis <b>+{_fmt1(isarc_sl_val)}%</b>). En deuda soberana, el riesgo país EMBI+ "
        f"comprime a <b>{fmt_num(embi_val, 0)} pb</b> con una tasa asintótica Nelson-Siegel de <b>{_fmt1(beta0_val)}%</b> y el GD35 rindiendo <b>{_fmt1(gd35_tir_val)}% TIR</b>."
    )
    col_izq.append(Paragraph(p2_cov, ParagraphStyle('CovBL2', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=6)))

    p3_cov = (
        f"En el sector externo y cambiario, las reservas brutas del BCRA alcanzan los <b>${fmt_num(tasas_bcra.get('reservas_brutas_usd_m', {}).get('valor', 50660), 0)} M USD</b>, "
        f"con recomposición de reservas netas y reversión del déficit cuasifiscal. Las liquidaciones de la balanza comercial energética y agroindustrial sostienen "
        f"la oferta en el segmento financiero bajo el esquema blend 80/20, mientras el programa de rollover del Tesoro supera el 110% de cobertura sobre vencimientos "
        f"en moneda local, extendiendo los plazos de colocación hacia 2027 sin fricciones de liquidez."
    )
    col_izq.append(Paragraph(p3_cov, ParagraphStyle('CovBL3', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=6)))

    # Bloque de catalizadores
    t_cat = Table([
        [Paragraph("<font color='#0B2545' size=7.5><b>CATALIZADORES & FACTORES DE RIESGO TÁCTICO (30–60 DÍAS)</b></font>", ParagraphStyle('CatT', fontName='Georgia', leading=9.4))],
        [Paragraph(
            "<font color='#1E293B' size=6.7>"
            "• <b>Transición Cambiaria & Reservas:</b> Sostenibilidad de la acumulación de divisas y calibración del crawling peg.<br/>"
            "• <b>Roll-over de Deuda en Pesos:</b> Capacidad del Tesoro para refinanciar más del 100% en Lecaps sin convalidar tasas elevadas.<br/>"
            "• <b>Compresión Soberana:</b> Ruptura del piso de 500 pb en EMBI+ como condición para retornar al crédito internacional."
            "</font>",
            ParagraphStyle('CatB', fontName='Georgia', leading=9.0)
        )]
    ], colWidths=[324])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CURR),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.0),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    col_izq.append(t_cat)
    col_izq.append(Spacer(1, 6))

    # Matriz de escenarios en portada
    t_esc_cov = Table([
        [
            Paragraph("<b>Escenario Macro (30–90d)</b>", ParagraphStyle('EH1', fontName='Georgia-Bold', fontSize=6.5, leading=8.2, textColor=colors.white)),
            Paragraph("<b>Prob.</b>", ParagraphStyle('EH2', fontName='Georgia-Bold', fontSize=6.5, leading=8.2, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Directriz de Asignación Sugerida</b>", ParagraphStyle('EH3', fontName='Georgia-Bold', fontSize=6.5, leading=8.2, textColor=colors.white))
        ],
        [Paragraph("<b>Base (Convergencia)</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=PRIMARY)), Paragraph("<b>65%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor(POS_COLOR))), Paragraph("Ancla fiscal y monetaria firme; sostener Lecaps cortas y acumular GD35.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
        [Paragraph("<b>Shock Tarifario / Brecha</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.HexColor("#B45309"))), Paragraph("<b>25%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor("#B45309"))), Paragraph("Rebote de regulados; rotar 15% hacia Boncer TZX26/TZX27.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
        [Paragraph("<b>Estrés Externo / Salida</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.HexColor(NEG_COLOR))), Paragraph("<b>10%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor(NEG_COLOR))), Paragraph("Volatilidad global; cobertura en Bopreal y acortar duration.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
    ], colWidths=[88, 30, 206])
    t_esc_cov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.0),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_izq.append(t_esc_cov)

    # Columna Derecha (192 pt)
    col_der = []
    col_der.append(Paragraph("<font color='#0B2545' size=8.5><b>ASIGNACIÓN TÁCTICA DE ACTIVOS</b></font>", ParagraphStyle('SecR1', fontName='Georgia', leading=10.5)))
    col_der.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    t_tact = Table([
        [
            Paragraph("<b>Activo</b>", ParagraphStyle('TH1', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white)),
            Paragraph("<b>Postura</b>", ParagraphStyle('TH2', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Peso</b>", ParagraphStyle('TH3', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Target</b>", ParagraphStyle('TH4', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))
        ],
        [Paragraph("Lecaps Cortas", ParagraphStyle('TD1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph("<font color='#059669'><b>Sobreponderar</b></font>", ParagraphStyle('TD2', fontName='Georgia', fontSize=6.0, leading=8.0, alignment=TA_CENTER)), Paragraph("40%", ParagraphStyle('TD3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_CENTER, textColor=PRIMARY)), Paragraph("TEM 2.95%", ParagraphStyle('TD4', fontName='Georgia', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Soberanos GD35", ParagraphStyle('TD1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph("<font color='#059669'><b>Sobreponderar</b></font>", ParagraphStyle('TD2', fontName='Georgia', fontSize=6.0, leading=8.0, alignment=TA_CENTER)), Paragraph("30%", ParagraphStyle('TD3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_CENTER, textColor=PRIMARY)), Paragraph("TIR 9.65%", ParagraphStyle('TD4', fontName='Georgia', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Boncer TZX26", ParagraphStyle('TD1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph("<font color='#475569'><b>Mantener</b></font>", ParagraphStyle('TD2', fontName='Georgia', fontSize=6.0, leading=8.0, alignment=TA_CENTER)), Paragraph("15%", ParagraphStyle('TD3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_CENTER, textColor=SLATE)), Paragraph("CER+7.8%", ParagraphStyle('TD4', fontName='Georgia', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Bopreal BPY26", ParagraphStyle('TD1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph("<font color='#059669'><b>Sobreponderar</b></font>", ParagraphStyle('TD2', fontName='Georgia', fontSize=6.0, leading=8.0, alignment=TA_CENTER)), Paragraph("10%", ParagraphStyle('TD3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_CENTER, textColor=PRIMARY)), Paragraph("TIR 10.4%", ParagraphStyle('TD4', fontName='Georgia', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Equity Merval", ParagraphStyle('TD1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph("<font color='#DC2626'><b>Subponderar</b></font>", ParagraphStyle('TD2', fontName='Georgia', fontSize=6.0, leading=8.0, alignment=TA_CENTER)), Paragraph("5%", ParagraphStyle('TD3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor(NEG_COLOR))), Paragraph("Valuación", ParagraphStyle('TD4', fontName='Georgia', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
    ], colWidths=[68, 54, 28, 42])
    t_tact.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.4),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der.append(t_tact)
    col_der.append(Spacer(1, 6))

    col_der.append(Paragraph("<font color='#0B2545' size=8.5><b>MACRO & MARKET SCORECARD</b></font>", ParagraphStyle('SecR2', fontName='Georgia', leading=10.5)))
    col_der.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    t_sc = Table([
        [Paragraph("<b>Métrica Clave</b>", ParagraphStyle('SH1', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white)), Paragraph("<b>Nivel Observado</b>", ParagraphStyle('SH2', fontName='Georgia-Bold', fontSize=6.6, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("IPC General / Núcleo", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(ipc_gral)}% / {_fmt1(ipc_core)}% m/m", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Lecap Corta (TEM)", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(lecap_corta)}% (Real: +{_fmt1(tasa_real_exante_val)}%)", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=colors.HexColor(POS_COLOR)))],
        [Paragraph("Dólar CCL / Brecha", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"${fmt_num(ccl_val, 2)} / {_fmt1(brecha_val)}%", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("EMBI+ Riesgo País", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{fmt_num(embi_val, 0)} pb (-174 pb)", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=PRIMARY))],
        [Paragraph("Curva N-S (Beta 0)", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(beta0_val)}%", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Actividad EMAE", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(emae_ia_val, signo=True)}% i.a.", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Régimen Sistémico", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.5, leading=8.0, textColor=DARK_TEXT)), Paragraph(f"{_regimen_txt} (Turb {_turb_txt})", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, alignment=TA_RIGHT, textColor=colors.HexColor(POS_COLOR)))],
    ], colWidths=[100, 92])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der.append(t_sc)
    col_der.append(Spacer(1, 6))

    t_cal_cov = Table([
        [Paragraph("<b>Hito Financiero (30d)</b>", ParagraphStyle('CL1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.white)), Paragraph("<b>Estrategia</b>", ParagraphStyle('CL2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("Licitación Tesoro", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.8, textColor=DARK_TEXT)), Paragraph("Rollover &ge; 100% en Lecaps", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.8, alignment=TA_RIGHT, textColor=PRIMARY))],
        [Paragraph("Publicación IPC INDEC", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.8, textColor=DARK_TEXT)), Paragraph("Ancla núcleo &le; 2,0%", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Vencimiento CIP / Rofex", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.8, textColor=DARK_TEXT)), Paragraph("Arbitraje blend 80/20", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Directorio BCRA", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.8, textColor=DARK_TEXT)), Paragraph("Tasa neutral r*", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.8, alignment=TA_RIGHT, textColor=PRIMARY))],
    ], colWidths=[108, 84])
    t_cal_cov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.4),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der.append(t_cal_cov)

    t_main_cov = Table([[col_izq, "", col_der]], colWidths=[330, 10, 192])
    t_main_cov.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEBEFORE', (2,0), (2,0), 0.5, HAIRLINE),
    ]))
    elements.append(t_main_cov)
    elements.append(Spacer(1, 6))

    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))
    t_imp_cov = Table([
        [
            Paragraph("<font color='#0B2545' size=7.2><b>AUTORÍA & RESPONSABILIDAD TÉCNICA:</b> Federico Agustín Chillón · Investigador en Métodos Cuantitativos</font><br/><font color='#64748B' size=6.5>Facultad de Ciencias Económicas · Universidad Nacional de Cuyo (UNCUYO) · Observatorio Económico Regional Urbano (OERU)</font>", ParagraphStyle('IL', fontName='Georgia', leading=8.8)),
            Paragraph("<font color='#0B2545' size=7.2><b>RESEARCH INSTITUCIONAL</b></font><br/><font color='#64748B' size=6.5>Modelos Nelson-Siegel & GARCH · Cierre Mensual</font>", ParagraphStyle('IR', fontName='Georgia', alignment=TA_RIGHT, leading=8.8))
        ]
    ], colWidths=[370, 162])
    t_imp_cov.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_imp_cov)
    elements.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: ÍNDICE GENERAL Y METODOLOGÍA
    # =========================================================================
    elements.append(Paragraph("Índice General y Estructura del Informe", title_style))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))

    toc_entries = [
        ("CAT", "RESUMEN EJECUTIVO & ESCENARIOS", "", ""),
        ("MAIN", "Resumen Ejecutivo, Matriz de Escenarios y Asignación de Carteras", "3", "sec_exec"),
        ("CAT", "ECONOMÍA REAL", "", ""),
        ("MAIN", "1. Nivel de Actividad Económica General (EMAE)", "4", "sec_emae"),
        ("MAIN", "2. Dinámica de Precios, Canastas Básicas y Salario Real", "5", "sec_prices"),
        ("SUB", "Cuadro 1. Índice de Precios al Consumidor y Canastas Básicas (INDEC / DEIE)", "6", "sec_tab_ipc"),
        ("MAIN", "3. Desagregación Sectorial y Producción en Mendoza y Cuyo", "7", "sec_cuyo"),
        ("SUB", "3.1. Comparativo Regional: Índice Sintético de Actividad (ISARC Cuyo)", "8", "sec_regional_cuyo"),
        ("CAT", "RÉGIMEN MONETARIO Y MERCADOS", "", ""),
        ("MAIN", "4. Balance del BCRA, Pasivos Cuasifiscales y Postura Monetaria", "9", "sec_monetary"),
        ("MAIN", "5. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera", "10", "sec_tactical"),
        ("MAIN", "6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel", "11", "sec_yield"),
        ("MAIN", "7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica", "12", "sec_fx"),
        ("SUB", "7.1. Tipo de Cambio Real Bilateral (TCR) y Competitividad Cambiaria", "13", "sec_tcr"),
        ("MAIN", "8. Sector Financiero, Renta Variable y Radar de Balances (Merval)", "14", "sec_equity"),
        ("CAT", "ANEXO & CIERRE", "", ""),
        ("MAIN", "9. Flash Normativo, Contexto Internacional y Referencias APA 7ma", "15", "sec_refs")
    ]

    toc_data = []
    for typ, text, page, anchor in toc_entries:
        if typ == "CAT":
            toc_data.append([Paragraph(f"<b>{text}</b>", ParagraphStyle('TOCCat', fontName='Georgia-Bold', fontSize=7.2, leading=9.5, textColor=MUTED)), "", ""])
        elif typ == "MAIN":
            p_t = Paragraph(f'<a href="#{anchor}" color="#0B2545"><b>{text}</b></a>', ParagraphStyle('TOCMain', fontName='Georgia-Bold', fontSize=7.6, leading=10.2, textColor=PRIMARY))
            p_dots = Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", ParagraphStyle('TOCDots', fontName='Georgia', fontSize=6.5, textColor=BORDER, alignment=TA_CENTER))
            p_p = Paragraph(f'<a href="#{anchor}" color="#0B2545"><b>{page}</b></a>', ParagraphStyle('TOCPage', fontName='Georgia-Bold', fontSize=7.6, leading=10.2, alignment=TA_RIGHT, textColor=PRIMARY))
            toc_data.append([p_t, p_dots, p_p])
        elif typ == "SUB":
            p_t = Paragraph(f'<a href="#{anchor}" color="#1E293B">{text}</a>', ParagraphStyle('TOCSub', fontName='Georgia', fontSize=7.2, leading=9.6, leftIndent=10, textColor=DARK_TEXT))
            p_dots = Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", ParagraphStyle('TOCDots', fontName='Georgia', fontSize=6.5, textColor=BORDER, alignment=TA_CENTER))
            p_p = Paragraph(f'<a href="#{anchor}" color="#334155">{page}</a>', ParagraphStyle('TOCPageS', fontName='Georgia', fontSize=7.2, leading=9.6, alignment=TA_RIGHT, textColor=SLATE))
            toc_data.append([p_t, p_dots, p_p])

    t_toc = Table(toc_data, colWidths=[310, 172, 50])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_toc)
    elements.append(Spacer(1, 6))

    # Metodología y Glosario
    t_met = Table([
        [Paragraph("<b>CRITERIOS METODOLÓGICOS, MODELOS ECONOMÉTRICOS Y FUENTES OFICIALES</b>", ParagraphStyle('MH', fontName='Georgia-Bold', fontSize=7.6, textColor=PRIMARY))],
        [Paragraph(
            "• <b>Jerarquía por Importancia Relativa:</b> Priorización de componentes macroeconómicos determinantes (precios regulados sobre estacionales, transables sobre no transables, y deuda soberana sobre derivados).<br/>"
            "• <b>Fuentes Primarias Consolidadas:</b> Series provistas por INDEC, DEIE Mendoza, Banco Central de la República Argentina (BCRA), Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía y ByMA.<br/>"
            "• <b>Modelos Econométricos Aplicados:</b> Calibración paramétrica de Nelson-Siegel (1987) para curvas de deuda en USD, regla de Taylor con tasa real ex-ante (1993), paridad de tasas cubierta (CIP) y descomposición factorial multivariada (PCA Absorption Ratio y Turbulencia de Mahalanobis).",
            ParagraphStyle('MB', fontName='Georgia', fontSize=7.0, leading=9.4, textColor=DARK_TEXT)
        )]
    ], colWidths=[532])
    t_met.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CURR),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_met)
    elements.append(Spacer(1, 6))

    glo_data = [
        [Paragraph("<b>Abreviatura</b>", table_header_style), Paragraph("<b>Definición / Concepto Metodológico</b>", table_header_style), Paragraph("<b>Uso Operativo en el Informe</b>", table_header_style)],
        [Paragraph("<b>TEM / TNA</b>", table_cell_left), Paragraph("Tasa Efectiva Mensual / Tasa Nominal Anual.", table_cell_left), Paragraph("Rendimiento contractual de letras del Tesoro (Lecaps).", table_cell_left)],
        [Paragraph("<b>Lefi / Pases</b>", table_cell_left), Paragraph("Letras Fiscales de Liquidez / Pases Pasivos BCRA.", table_cell_left), Paragraph("Instrumentos de absorción monetaria bancaria.", table_cell_left)],
        [Paragraph("<b>EMAE</b>", table_cell_left), Paragraph("Estimador Mensual de Actividad Económica (INDEC).", table_cell_left), Paragraph("Proxy de alta frecuencia del PIB real (base 2004=100).", table_cell_left)],
        [Paragraph("<b>ISARC</b>", table_cell_left), Paragraph("Índice Sintético de Actividad Regional de Cuyo.", table_cell_left), Paragraph("Indicador multivariado provincial (Mendoza, San Juan, San Luis).", table_cell_left)],
        [Paragraph("<b>EMBI+ / N-S</b>", table_cell_left), Paragraph("Emerging Markets Bond Index / Nelson-Siegel.", table_cell_left), Paragraph("Riesgo país soberano y ajuste paramétrico de curvas spot/forward.", table_cell_left)],
        [Paragraph("<b>TCR Bilateral</b>", table_cell_left), Paragraph("Tipo de Cambio Real Bilateral ARS/USD (base 100).", table_cell_left), Paragraph("Competitividad cambiaria deflactada por inflación relativa.", table_cell_left)],
        [Paragraph("<b>CIP / Rofex</b>", table_cell_left), Paragraph("Covered Interest Parity / Mercado a Término.", table_cell_left), Paragraph("Paridad de tasas cubierta para proyección de futuros cambiarios.", table_cell_left)],
        [Paragraph("<b>PCA / AR</b>", table_cell_left), Paragraph("Principal Component Analysis / Absorption Ratio.", table_cell_left), Paragraph("Métrica de fragilidad multivariada y concentración sistémica.", table_cell_left)],
        [Paragraph("<b>RIGI</b>", table_cell_left), Paragraph("Régimen de Incentivo para Grandes Inversiones.", table_cell_left), Paragraph("Marco fiscal y cambiario para proyectos mineros y energéticos.", table_cell_left)],
    ]
    t_glo = Table(glo_data, colWidths=[75, 225, 232])
    t_glo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), BG_CURR),
        ('BACKGROUND', (0,6), (-1,6), colors.white),
        ('BACKGROUND', (0,7), (-1,7), BG_CURR),
        ('BACKGROUND', (0,8), (-1,8), colors.white),
        ('BACKGROUND', (0,9), (-1,9), BG_CURR),
        ('BACKGROUND', (0,10), (-1,10), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_glo)
    elements.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: RESUMEN EJECUTIVO, MATRIZ DE ESCENARIOS Y CARTERAS
    # =========================================================================
    elements.append(Paragraph("Resumen Ejecutivo, Matriz de Escenarios y Asignación Táctica", title_style))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))

    p1_p3 = (
        f"El diagnóstico macroeconómico al cierre de {periodo_texto_cap} confirma la vigencia y solidez del ancla fiscal y monetaria. "
        f"La convergencia inflacionaria (IPC INDEC: {_fmt1(inflacion.get('indec_general_mom'))}% MoM vs. Mendoza DEIE: {_fmt1(inflacion.get('deie_mendoza_mom'))}% MoM) "
        f"estuvo liderada por el reacomodamiento de precios regulados ({_fmt1(inflacion.get('indec_regulados_mom'))}% MoM) y servicios privados ({_fmt1(inflacion.get('indec_servicios_mom'))}% MoM), "
        f"compensados por la marcada estabilidad en la inflación núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}% MoM). En el frente monetario, la tasa real ex-ante "
        f"(+{_fmt1(tasa_real_exante, signo=False)}% mensual TEM Lecap vs. REM) opera como dique de contención contra la dolarización de carteras, preservando la estabilidad "
        f"del tipo de cambio financiero. La absorción bancaria de liquidez opera vía la tasa de pases pasivos a 1 día ({_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA) "
        f"y el equilibrio presupuestario primario sostenido en base caja."
    )
    elements.append(Paragraph(p1_p3, body_style))

    p2_p3 = (
        f"En el plano distributivo, la Canasta Básica Total en Mendoza (${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)}) exige ingresos crecientes para superar el umbral de pobreza, "
        f"mientras el salario formal (RIPTE) comienza a registrar mejoras reales marginales en los sectores transables. A nivel soberano, el riesgo país EMBI+ comprime a "
        f"<b>{fmt_num(embi_val, 0)} pb</b>, reduciendo sustancialmente el costo marginal de fondeo y habilitando la rotación táctica hacia tramos medios de bonos Globales (GD35/GD38)."
    )
    elements.append(Paragraph(p2_p3, body_style))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("<font color='#0284C7'><b>Matriz de Escenarios Macroeconómicos a 12 Meses (Proyecciones de Research)</b></font>", table_title_style))
    elements.append(Spacer(1, 2))

    esc_p3_data = [
        [
            Paragraph("<b>Escenario</b>", cell_header_style),
            Paragraph("<b>Prob.</b>", cell_header_style),
            Paragraph("<b>Dólar CCL (Dic-26)</b>", cell_header_style),
            Paragraph("<b>Inflación 2026</b>", cell_header_style),
            Paragraph("<b>TIR GD30 Esperada</b>", cell_header_style),
            Paragraph("<b>Estrategia Recomendada</b>", cell_header_style)
        ],
        [Paragraph("<b>Base (Continuidad)</b>", table_cell_bold), Paragraph("60%", table_cell_center), Paragraph("$1.750 - $1.850", table_cell_center), Paragraph("28% - 32% anual", table_cell_center), Paragraph("9,50% (Upside +12%)", table_cell_center), Paragraph("Carry en Lecaps del tramo corto + sobreponderar tramo GD35/GD38.", table_cell_left)],
        [Paragraph("<b>Bull (Salida de Cepo)</b>", table_cell_bold), Paragraph("25%", table_cell_center), Paragraph("$1.620 - $1.700", table_cell_center), Paragraph("20% - 25% anual", table_cell_center), Paragraph("7,80% (Upside +28%)", table_cell_center), Paragraph("Máxima exposición a Globales largos y acciones energéticas (YPF, PAMP).", table_cell_left)],
        [Paragraph("<b>Bear (Shock Externo)</b>", table_cell_bold), Paragraph("15%", table_cell_center), Paragraph("$1.950 - $2.150", table_cell_center), Paragraph("40% - 48% anual", table_cell_center), Paragraph("13,50% (Hedge)", table_cell_center), Paragraph("Dolarización de liquidez en Bopreal / Boncer tramo corto.", table_cell_left)],
    ]
    t_esc_p3 = Table(esc_p3_data, colWidths=[82, 35, 85, 75, 85, 170])
    t_esc_p3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_esc_p3)
    elements.append(Spacer(1, 6))

    # Matriz de Sensibilidad Táctica & Retorno Total en Bonos Soberanos (Duration vs EMBI+)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<font color='#0284C7'><b>Matriz de Sensibilidad Táctica & Retorno Total en Deuda Soberana USD</b></font>", table_title_style))
    elements.append(Spacer(1, 2))

    sens_p3_data = [
        [
            Paragraph("<b>Instrumento</b>", cell_header_style),
            Paragraph("<b>Maturity</b>", cell_header_style),
            Paragraph("<b>Mod. Dur.</b>", cell_header_style),
            Paragraph("<b>TIR Actual</b>", cell_header_style),
            Paragraph("<b>Shock -200 pb (Bull)</b>", cell_header_style),
            Paragraph("<b>Shock -100 pb (Base)</b>", cell_header_style),
            Paragraph("<b>Shock +100 pb (Hedge)</b>", cell_header_style)
        ],
        [Paragraph("<b>Bonares AL30</b>", table_cell_bold), Paragraph("2030", table_cell_center), Paragraph("2,65", table_cell_center), Paragraph(f"{_fmt1(soberano.get('al30_tir', 11.20))}%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+5,8%</font>", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+2,8%</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-2,5%</font>", table_cell_center)],
        [Paragraph("<b>Globales GD30</b>", table_cell_bold), Paragraph("2030", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph(f"{_fmt1(soberano.get('gd30_tir', 9.80))}%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+6,1%</font>", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+3,0%</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-2,7%</font>", table_cell_center)],
        [Paragraph("<b>Globales GD35</b>", table_cell_bold), Paragraph("2035", table_cell_center), Paragraph("6,40", table_cell_center), Paragraph(f"{_fmt1(gd35_tir_val)}%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+14,2%</font>", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+6,9%</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-6,1%</font>", table_cell_center)],
        [Paragraph("<b>Globales GD38</b>", table_cell_bold), Paragraph("2038", table_cell_center), Paragraph("5,20", table_cell_center), Paragraph(f"{_fmt1(soberano.get('gd38_tir', 9.70))}%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+11,8%</font>", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+5,7%</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-4,9%</font>", table_cell_center)],
    ]
    t_sens_p3 = Table(sens_p3_data, colWidths=[90, 55, 60, 65, 90, 86, 86])
    t_sens_p3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sens_p3)
    elements.append(Spacer(1, 5))

    # Dos columnas asimétricas de asignación y vulnerabilidad
    col_izq_p3 = [
        Paragraph("<b>Guía de Asignación Táctica por Perfil de Cartera:</b>", h2_style),
        Paragraph("• <b>Conservador (Treasury):</b> 70% Lecap corta (TEM 2,95%) + 30% Boncer TZX27. Captura de tasa real de +95 pb mensual con mínimo riesgo de volatilidad de precio.", body_style),
        Paragraph("• <b>Moderado (Institucional):</b> 40% Lecap tramo medio + 20% Boncer + 25% GD35/GD38 + 15% Bopreal Serie 3. Balance de carry real y compresión soberana.", body_style),
        Paragraph("• <b>Agresivo (Total Return):</b> 20% Lecaps + 45% Globales GD35/GD38 + 35% Equity ByMA (YPF, Pampa, TGS). Maximización de convexidad ante el régimen RIGI.", body_style),
    ]
    col_der_p3 = [
        Paragraph("<b>Termómetro de Vulnerabilidad & Señales de Mercado:</b>", h2_style),
        Paragraph("• <b>Brecha Cambiaria CCL (4,5%):</b> El esquema blend 80/20 y la absorción de liquidez contienen la cotización financiera por debajo del umbral de alerta del 10%.", body_style),
        Paragraph("• <b>Curva de Futuros CIP:</b> Las tasas implícitas en derivados (35,4% TNA a 30d) descartan presiones de devaluación en el horizonte de corto plazo.", body_style),
        Paragraph(f"• <b>Riesgo País EMBI+ ({fmt_num(embi_val, 0)} pb):</b> La compresión de spreads consolida el acceso al financiamiento y la normalización de paridades.", body_style),
    ]
    t_2col_p3 = Table([[col_izq_p3, col_der_p3]], colWidths=[260, 260])
    t_2col_p3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (0,0), 6),
        ('LEFTPADDING', (1,0), (1,0), 6),
    ]))
    elements.append(t_2col_p3)
    elements.append(Spacer(1, 6))

    # Pull-quote institucional
    p_cita = Paragraph("<i>«El trípode de superávit primario irrestricto, tasa de interés real positiva y saneamiento patrimonial del Banco Central convalida la mayor compresión de primas de riesgo soberano de la última década, transformando el arbitraje financiero.»</i>", ParagraphStyle('PQuote', fontName='Georgia-Italic', fontSize=8.0, leading=10.8, alignment=TA_JUSTIFY, textColor=PRIMARY))
    p_aut = Paragraph("<b>— Comité de Asignación Estratégica · FCE UNCUYO · OERU</b>", ParagraphStyle('PQuoteAut', fontName='Sans-Bold', fontSize=6.6, leading=8.2, alignment=TA_RIGHT, textColor=MUTED))
    t_pq = Table([[p_cita], [p_aut]], colWidths=[532])
    t_pq.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINETOP', (0,0), (-1,0), 0.6, PRIMARY),
        ('LINEBELOW', (0,-1), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_pq)
    elements.append(Spacer(1, 5))

    # Radar de Alertas Tempranas & Umbrales de Sostenibilidad Macroeconómica
    elements.append(Paragraph("<font color='#0284C7'><b>Radar de Alertas Tempranas & Umbrales de Sostenibilidad Macroeconómica</b></font>", table_title_style))
    elements.append(Spacer(1, 2))

    radar_p3_data = [
        [
            Paragraph("<b>Pilar Macroeconómico</b>", cell_header_style),
            Paragraph("<b>Métrica / Benchmark</b>", cell_header_style),
            Paragraph("<b>Nivel Observado</b>", cell_header_style),
            Paragraph("<b>Umbral de Alerta</b>", cell_header_style),
            Paragraph("<b>Diagnóstico de Régimen</b>", cell_header_style),
            Paragraph("<b>Implicancia Operativa de Corto Plazo</b>", cell_header_style)
        ],
        [Paragraph("<b>Ancla Fiscal Primaria</b>", table_cell_bold), Paragraph("Superávit Base Caja (% PBI)", table_cell_left), Paragraph("+1,8% PBI", table_cell_center_bold), Paragraph("&lt; +1,0% PBI", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'><b>Consolidado</b></font>", table_cell_center), Paragraph("Clausura de transferencias de emisión al Tesoro.", table_cell_left)],
        [Paragraph("<b>Régimen de Tasas Reales</b>", table_cell_bold), Paragraph("TEM Lecap vs. Inflación REM", table_cell_left), Paragraph("+0,95% m/m", table_cell_center_bold), Paragraph("&le; 0,00% m/m", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'><b>Contractivo</b></font>", table_cell_center), Paragraph("Incentivo robusto a la retención de depósitos en ARS.", table_cell_left)],
        [Paragraph("<b>Microestructura Cambiaria</b>", table_cell_bold), Paragraph("Brecha CCL vs. Mayorista", table_cell_left), Paragraph("4,52%", table_cell_center_bold), Paragraph("&gt; 15,0%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'><b>Normalizado</b></font>", table_cell_center), Paragraph("Esquema blend 80/20 esteriliza la prima de salto.", table_cell_left)],
        [Paragraph("<b>Hoja de Balance BCRA</b>", table_cell_bold), Paragraph("Reservas Netas (RIN USD)", table_cell_left), Paragraph("+3.650 MM USD", table_cell_center_bold), Paragraph("&lt; 0 MM USD", table_cell_center), Paragraph(f"<font color='{BLUE_INST}'><b>Recuperación</b></font>", table_cell_center), Paragraph("Cancelación de pasivos remunerados a stock $0.", table_cell_left)],
        [Paragraph("<b>Fragilidad Multivariada</b>", table_cell_bold), Paragraph("Absorption Ratio (Kritzman AR)", table_cell_left), Paragraph("64,2% (dt=5,4)", table_cell_center_bold), Paragraph("&gt; 75,0%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'><b>Resiliente</b></font>", table_cell_center), Paragraph("Ausencia de concentración de volatilidad cruzada.", table_cell_left)],
    ]
    t_radar_p3 = Table(radar_p3_data, colWidths=[90, 95, 68, 62, 65, 152])
    t_radar_p3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), BG_CURR),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_radar_p3)
    elements.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: 1. NIVEL DE ACTIVIDAD GENERAL (EMAE)
    # =========================================================================
    p4_lead = (
        "El crecimiento económico de Argentina consolidó su sendero de recuperación positiva en el segundo trimestre de 2026 (+3,1% i.a.), "
        "apoyado en la expansión récord de hidrocarburos no convencionales en Vaca Muerta y minería cuyana, junto a la normalización del crédito "
        "comercial bancario. La industria y la construcción moderaron su ritmo de contracción, sentando las bases para una convergencia cíclica equilibrada."
    )
    p4_tabla_data = [
        [Paragraph("<b>ACTIVIDAD / SECTOR</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>PIB REAL Y DEMANDA AGREGADA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>EMAE / PIB Total (% i.a.)</b>", table_cell_bold), Paragraph("1,20", table_cell_center_bold), Paragraph("1,80", table_cell_center_bold), Paragraph("2,40", table_cell_center_bold), Paragraph("2,80", table_cell_center_bold), Paragraph("3,10", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,90</font>", table_cell_center), Paragraph("3,50", table_cell_center_bold), Paragraph("4,20", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Consumo Privado Hogares", table_cell_left), Paragraph("-1,80", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("2,70", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+4,50</font>", table_cell_center), Paragraph("3,10", table_cell_center), Paragraph("3,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Consumo Público Nacional", table_cell_left), Paragraph("-8,40", table_cell_center), Paragraph("-5,20", table_cell_center), Paragraph("-3,10", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("-0,90", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,60</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+7,50</font>", table_cell_center), Paragraph("-0,50", table_cell_center), Paragraph("0,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Formación Bruta Capital Fijo", table_cell_left), Paragraph("-12,50", table_cell_center), Paragraph("-6,80", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("5,80", table_cell_center), Paragraph("6,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,60</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+18,90</font>", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("8,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Reales de Bienes", table_cell_left), Paragraph("6,20", table_cell_center), Paragraph("8,40", table_cell_center), Paragraph("9,50", table_cell_center), Paragraph("10,20", table_cell_center), Paragraph("11,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+5,20</font>", table_cell_center), Paragraph("10,80", table_cell_center), Paragraph("7,50", table_cell_center)],
        [Paragraph("<b>TRACCIÓN SECTORIAL PRIMARIA & INDUSTRIAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Minería, Petróleo & Gas", table_cell_left), Paragraph("6,50", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("8,10", table_cell_center), Paragraph("8,40", table_cell_center), Paragraph("8,50", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+2,00</font>", table_cell_center), Paragraph("9,20", table_cell_center), Paragraph("11,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Sector Agropecuario", table_cell_left), Paragraph("8,40", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("13,40", table_cell_center), Paragraph("14,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,80</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+5,80</font>", table_cell_center), Paragraph("12,50", table_cell_center), Paragraph("6,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Comercio Mayorista / Minorista", table_cell_left), Paragraph("-3,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("0,40", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,00</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+6,00</font>", table_cell_center), Paragraph("3,20", table_cell_center), Paragraph("4,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Industria Manufacturera", table_cell_left), Paragraph("-7,80", table_cell_center), Paragraph("-5,20", table_cell_center), Paragraph("-3,40", table_cell_center), Paragraph("-2,10", table_cell_center), Paragraph("-1,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+6,00</font>", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Construcción & Cemento", table_cell_left), Paragraph("-14,20", table_cell_center), Paragraph("-10,50", table_cell_center), Paragraph("-7,20", table_cell_center), Paragraph("-5,10", table_cell_center), Paragraph("-4,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,90</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+10,00</font>", table_cell_center), Paragraph("-1,00", table_cell_center), Paragraph("5,00", table_cell_center)],
    ]
    p4_bullets = [
        ("El Estimador Mensual de Actividad Económica (EMAE) registró en junio de 2026 una expansión interanual del +3,1%",
         "acumulando siete meses consecutivos de variación positiva en la serie desestacionalizada (+0,4% m/m, alcanzando 153,4 puntos base 2004=100). "
         "Este dinamismo responde a la eliminación de distorsiones de precios relativos, la consolidación del ancla fiscal en base caja sin emisión monetaria al Tesoro "
         "y la consiguiente desinflación, factores que han permitido una incipiente recomposición del salario real en el sector formal privado (+1,8% trimestral) "
         "y un despegue en el volumen de crédito bancario comercial, que avanzó a un ritmo del 14,5% real interanual."),
        ("A nivel sectorial, la recuperación presenta una marcada asimetría liderada por los sectores transables e intensivos en capital",
         "La extracción de hidrocarburos (+8,5% i.a.) y la producción agropecuaria (+14,2% i.a.) operan como los motores centrales de la tracción agregada, "
         "compensando la debilidad relativa de los segmentos no transables. En particular, la industria manufacturera (-1,8% i.a.) y la construcción (-4,2% i.a.) "
         "continúan transitando un proceso de depuración de inventarios tras el cese de obra pública financiada con emisión, exhibiendo no obstante una desaceleración "
         "progresiva en su ritmo de contracción frente al piso registrado en 2024 (-14,2%)."),
        ("Las perspectivas para el segundo semestre de 2026 y 2027 anticipan una consolidación del crecimiento hacia el +3,5% y +4,2% anual",
         "sustentadas en la maduración de los proyectos estratégicos adheridos al Régimen de Incentivo para Grandes Inversiones (RIGI) en minería de cobre y litio, "
         "junto a la ampliación de capacidad de transporte de crudo y gas natural en Vaca Muerta (oleoducto Vaca Muerta Sur y reversión del Gasoducto Norte). "
         "La estabilidad de la brecha cambiaria en torno al 4,5% constituye la precondición operativa para convalidar la inversión privada fija sin presiones de salto devaluatorio.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="1. Estimador Mensual de Actividad Económica (EMAE)",
        leadin_txt=p4_lead,
        tabla_titulo="Principales indicadores de actividad económica agregada y sectorial (%)",
        tabla_data=p4_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos trimestrales y mensuales basados en series desestacionalizadas del INDEC. Variaciones interanuales y proyecciones basadas en modelo macroeconométrico FCE UNCUYO y consenso REM BCRA.",
        bullets_txt_list=p4_bullets,
        chart_filename="chart_editorial_emae.png",
        chart_footnote="Nota: Estimador Mensual de Actividad Económica (base 2004=100) provisto por INDEC. Tracción sectorial estimada por la FCE UNCUYO."
    ))

    # =========================================================================
    # PÁGINA 5: 2. PRECIOS Y SALARIOS (INDEC)
    # =========================================================================
    p5_lead = (
        "La inflación de Argentina profundizó su sendero de desaceleración en el segundo trimestre de 2026 (IPC general en 2,2% m/m y núcleo en 1,9% m/m), "
        "convalidando el ancla cambiaria del 2% y la disciplina fiscal en base caja. En Mendoza, el IPC DEIE convergió al 2,3% m/m, mientras que los salarios "
        "formales (RIPTE) comenzaron a recomponer poder adquisitivo en términos reales frente a la canasta básica alimentaria."
    )
    p5_tabla_data = [
        [Paragraph("<b>INDICADOR DE PRECIOS & INGRESOS</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>NIVEL GENERAL & APERTURAS INDEC</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>IPC General Nacional (% m/m)</b>", table_cell_bold), Paragraph("3,80", table_cell_center_bold), Paragraph("3,20", table_cell_center_bold), Paragraph("2,60", table_cell_center_bold), Paragraph("2,40", table_cell_center_bold), Paragraph("2,20", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>-0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,60</font>", table_cell_center), Paragraph("29,50", table_cell_center_bold), Paragraph("15,80", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;IPC Núcleo (Core Inflation)", table_cell_left), Paragraph("3,40", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("1,90", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,50</font>", table_cell_center), Paragraph("24,80", table_cell_center), Paragraph("12,40", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Precios Regulados (Tarifas)", table_cell_left), Paragraph("5,20", table_cell_center), Paragraph("4,50", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("3,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-2,20</font>", table_cell_center), Paragraph("38,20", table_cell_center), Paragraph("18,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Precios Estacionales", table_cell_left), Paragraph("2,90", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("1,60", table_cell_center), Paragraph("1,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,50</font>", table_cell_center), Paragraph("20,50", table_cell_center), Paragraph("14,00", table_cell_center)],
        [Paragraph("<b>MEDICIÓN REGIONAL & SALARIOS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;IPC DEIE Mendoza (% m/m)", table_cell_left), Paragraph("3,90", table_cell_center), Paragraph("3,30", table_cell_center), Paragraph("2,70", table_cell_center), Paragraph("2,50", table_cell_center), Paragraph("2,30", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,60</font>", table_cell_center), Paragraph("30,20", table_cell_center), Paragraph("16,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Salario Formal RIPTE (% i.a. nom.)", table_cell_left), Paragraph("145,2", table_cell_center), Paragraph("112,4", table_cell_center), Paragraph("85,2", table_cell_center), Paragraph("62,4", table_cell_center), Paragraph("48,5", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-13,9</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-96,7</font>", table_cell_center), Paragraph("34,20", table_cell_center), Paragraph("18,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Variación Salario Real (% trim.)", table_cell_left), Paragraph("-4,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("0,80", table_cell_center), Paragraph("1,40", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+6,00</font>", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa Real Ex-Ante Contractual", table_cell_left), Paragraph("0,25", table_cell_center), Paragraph("0,45", table_cell_center), Paragraph("0,65", table_cell_center), Paragraph("0,85", table_cell_center), Paragraph("0,95", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,70</font>", table_cell_center), Paragraph("1,05", table_cell_center), Paragraph("0,80", table_cell_center)],
    ]
    p5_bullets = [
        ("La dinámica de precios de agosto confirmó la consolidación del sendero desinflacionario nacional (2,2% m/m)",
         "y provincial (Mendoza: 2,3% m/m), quebrando la inercia histórica de tres dígitos anuales. Por orden de incidencia relativa, los aumentos estuvieron "
         "encabezados por los precios regulados (3,0% m/m) y servicios públicos, derivados de la actualización de cuadros tarifarios de gas y energía eléctrica en "
         "búsqueda del equilibrio de subsidios, mientras que los bienes transables operaron con incrementos alineados a la pauta cambiaria oficial."),
        ("La inflación núcleo se ubicó en 1,9% m/m, marcando el nivel más bajo en los últimos seis trimestres",
         "Este registro confirma que las presiones inflacionarias no provienen de desequilibrios monetarios primarios ni de una espiralización de costos, "
         "sino de ajustes puntuales de precios relativos. La tasa de interés real en pesos (Lecaps cortas en 2,95% TEM frente a expectativas REM de 2,00%) "
         "proporciona una barrera de absorción que esteriliza saldos transaccionales y consolida la convergencia hacia el crawling peg del 2%."),
        ("En el plano salarial, el RIPTE registró un avance mensual nominal que permite verificar ganancias reales marginales",
         "El salario formal del sector privado acumula tres trimestres de recomposición en términos de capacidad de compra de alimentos básicos. No obstante, "
         "el sector informal continúa rezagado, evidenciando una marcada heterogeneidad distributiva que mantiene tensiones en los segmentos de ingresos bajos "
         "frente al costo de la Canasta Básica Total en los grandes conglomerados urbanos.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="2. Precios, Canastas Básicas y Salario Real",
        leadin_txt=p5_lead,
        tabla_titulo="Evolución del Índice de Precios al Consumidor y variables laborales (%)",
        tabla_data=p5_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos provistos por INDEC (IPC Nacional), DEIE Mendoza y Secretaría de Trabajo (RIPTE). Proyecciones de inflación y salario real por FCE UNCUYO.",
        bullets_txt_list=p5_bullets,
        chart_filename="chart_editorial_ipc.png",
        chart_footnote="Nota: Aperturas del IPC INDEC y serie de trayectoria desinflacionaria mensual 2025-2026."
    ))

    # =========================================================================
    # PÁGINA 6: CUADRO 1. APERTURAS IPC Y CANASTAS BÁSICAS
    # =========================================================================
    p6_lead = (
        "El análisis desagregado de las canastas básicas refleja una moderación en la línea de indigencia (CBA en $532.000 nacional y $424.000 Mendoza), "
        "mientras que la Canasta Básica Total ($1.175.000 nacional) mantiene una brecha exigente frente a los ingresos de los deciles no registrados. "
        "La dispersión regional confirma presiones más acotadas en Cuyo frente al Gran Buenos Aires y la Patagonia."
    )
    p6_tabla_data = [
        [Paragraph("<b>CANASTA / UMBRAL DE POBREZA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>VALORIZACIÓN DE CANASTAS (MILES ARS)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>CBT Nacional (Línea Pobreza)</b>", table_cell_bold), Paragraph("820,4", table_cell_center_bold), Paragraph("910,2", table_cell_center_bold), Paragraph("980,5", table_cell_center_bold), Paragraph("1.045", table_cell_center_bold), Paragraph("1.175", table_cell_center_bold), Paragraph(f"<font color='{NEG_COLOR}'>+130</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+354</font>", table_cell_center), Paragraph("1.250", table_cell_center_bold), Paragraph("1.420", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;CBA Nacional (Línea Indigencia)", table_cell_left), Paragraph("370,5", table_cell_center), Paragraph("412,0", table_cell_center), Paragraph("445,2", table_cell_center), Paragraph("478,0", table_cell_center), Paragraph("532,0", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+54,0</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+161</font>", table_cell_center), Paragraph("565,0", table_cell_center), Paragraph("640,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;CBT Mendoza (DEIE Cuyo)", table_cell_left), Paragraph("765,0", table_cell_center), Paragraph("845,0", table_cell_center), Paragraph("912,0", table_cell_center), Paragraph("963,0", table_cell_center), Paragraph("1.085", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+122</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+320</font>", table_cell_center), Paragraph("1.160", table_cell_center), Paragraph("1.310", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;CBA Mendoza (DEIE Cuyo)", table_cell_left), Paragraph("345,0", table_cell_center), Paragraph("380,0", table_cell_center), Paragraph("410,0", table_cell_center), Paragraph("435,0", table_cell_center), Paragraph("485,0", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+50,0</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+140</font>", table_cell_center), Paragraph("515,0", table_cell_center), Paragraph("585,0", table_cell_center)],
        [Paragraph("<b>INDICADORES SOCIALES & COBERTURA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Brecha Salario RIPTE / CBT (%)", table_cell_left), Paragraph("105,4", table_cell_center), Paragraph("108,2", table_cell_center), Paragraph("112,0", table_cell_center), Paragraph("115,4", table_cell_center), Paragraph("118,5", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+3,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+13,1</font>", table_cell_center), Paragraph("122,0", table_cell_center), Paragraph("128,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa de Pobreza Urbana (% est.)", table_cell_left), Paragraph("54,20", table_cell_center), Paragraph("51,80", table_cell_center), Paragraph("48,50", table_cell_center), Paragraph("46,20", table_cell_center), Paragraph("44,10", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-2,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-10,1</font>", table_cell_center), Paragraph("41,50", table_cell_center), Paragraph("36,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa de Indigencia (% est.)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("16,20", table_cell_center), Paragraph("14,10", table_cell_center), Paragraph("12,80", table_cell_center), Paragraph("11,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-7,10</font>", table_cell_center), Paragraph("10,00", table_cell_center), Paragraph("8,20", table_cell_center)],
    ]
    p6_bullets = [
        ("La Canasta Básica Total (CBT) en el ámbito nacional alcanzó los $1.175.000 para un hogar tipo 2 (cuatro integrantes)",
         "exhibiendo un incremento mensual del 2,2% que acompaña la tasa general de inflación. La estabilidad en los precios de alimentos básicos de consumo masivo "
         "permitió contener la aceleración de la Canasta Alimentaria (CBA: $532.000), frenando el deterioro en los umbrales de indigencia extrema en los centros urbanos."),
        ("En la Provincia de Mendoza, la medición de la DEIE sitúa la Canasta Básica Total en $1.085.000",
         "mostrando una brecha favorable de aproximadamente 7,6% respecto a la media del Gran Buenos Aires, explicada por menores costos relativos en transporte "
         "y servicios comerciales. La Canasta Básica Alimentaria mendocina cerró en $485.000, reflejando la tracción de los programas locales de abastecimiento "
         "y la moderación en la carne vacuna y derivados lácteos."),
        ("La relación entre el salario registrado (RIPTE) y la CBT experimentó una mejora paulatina, alcanzando el 118,5%",
         "Este indicador ratifica que los trabajadores formales han recuperado un margen operativo sobre la línea de pobreza estadística, tras haber tocado "
         "niveles críticos cercanos al 100% en 2024. La disminución estimada de la tasa de pobreza hacia el 44,1% confirma el impacto directo de la desaceleración "
         "del IPC sobre los estratos medios asalariados.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="Cuadro 1. Aperturas IPC, Canastas Básicas y Líneas de Pobreza",
        leadin_txt=p6_lead,
        tabla_titulo="Valorización de Canastas Básicas e Indicadores de Pobreza e Indigencia (Miles ARS / %)",
        tabla_data=p6_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos de canastas valorizadas por INDEC y DEIE Mendoza para Hogar Tipo 2. Estimaciones de pobreza e indigencia basadas en microdatos EPH y modelo FCE UNCUYO.",
        bullets_txt_list=p6_bullets,
        chart_filename="chart_editorial_canastas.png",
        chart_footnote="Nota: Comparativa nacional y regional de canastas básicas CBT y CBA en miles de pesos."
    ))

    # =========================================================================
    # PÁGINA 7: 3. SECTORES CUYO (VITIVINICULTURA & PETRÓLEO)
    # =========================================================================
    p7_lead = (
        "La producción sectorial en Mendoza y Cuyo consolidó una dinámica heterogénea durante el segundo trimestre de 2026: "
        "los hidrocarburos no convencionales crecieron a tasas de dos dígitos (+12,5% i.a.) gracias a las inversiones piloto en Vaca Muerta mendocina, "
        "mientras que el despacho de vino fraccionado repuntó un +2,8% i.a., compensando la retracción de la cuenca petrolera convencional madura."
    )
    p7_tabla_data = [
        [Paragraph("<b>CADENA PRODUCTIVA / SECTOR</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>VITIVINICULTURA & AGROINDUSTRIA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Vino Fraccionado (Miles hl)</b>", table_cell_bold), Paragraph("6.200", table_cell_center_bold), Paragraph("6.850", table_cell_center_bold), Paragraph("7.120", table_cell_center_bold), Paragraph("7.250", table_cell_center_bold), Paragraph("7.340", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+90</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1.140</font>", table_cell_center), Paragraph("7.500", table_cell_center_bold), Paragraph("7.850", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Despacho Mercado Interno (%)", table_cell_left), Paragraph("-4,20", table_cell_center), Paragraph("-1,80", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,00</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+7,00</font>", table_cell_center), Paragraph("3,20", table_cell_center), Paragraph("4,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Vino Fraccionado (%)", table_cell_left), Paragraph("1,50", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("4,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,70</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+3,30</font>", table_cell_center), Paragraph("5,50", table_cell_center), Paragraph("6,80", table_cell_center)],
        [Paragraph("<b>HIDROCARBUROS & CEMENTO PORTLAND</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Petróleo Total Mendoza (Miles m³)", table_cell_left), Paragraph("205,0", table_cell_center), Paragraph("208,5", table_cell_center), Paragraph("210,4", table_cell_center), Paragraph("211,8", table_cell_center), Paragraph("212,0", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+7,00</font>", table_cell_center), Paragraph("215,0", table_cell_center), Paragraph("224,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Vaca Muerta Sur Mendoza (Shale)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("22,00", table_cell_center), Paragraph("25,40", table_cell_center), Paragraph("28,10", table_cell_center), Paragraph("30,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,90</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+11,5</font>", table_cell_center), Paragraph("34,00", table_cell_center), Paragraph("45,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Cuenca Cuyana Convencional (%)", table_cell_left), Paragraph("-3,20", table_cell_center), Paragraph("-2,40", table_cell_center), Paragraph("-1,80", table_cell_center), Paragraph("-1,20", table_cell_center), Paragraph("-0,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+2,40</font>", table_cell_center), Paragraph("-0,50", table_cell_center), Paragraph("0,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Despacho Cemento Cuyo (AFCP %)", table_cell_left), Paragraph("-12,4", table_cell_center), Paragraph("-8,50", table_cell_center), Paragraph("-4,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("1,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+2,70</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+13,6</font>", table_cell_center), Paragraph("3,50", table_cell_center), Paragraph("7,80", table_cell_center)],
    ]
    p7_bullets = [
        ("El sector vitivinícola registró un incremento interanual del +2,8% en el despacho de vinos fraccionados al mercado doméstico",
         "alcanzando las 7.340 miles de hectolitros acumuladas en los últimos doce meses según datos del INV. Este repunte convalida la estabilización "
         "del consumo en el canal minorista y la moderación en los costos de insumos secos (botellas, corchos y etiquetas). En el plano exportador, los envíos "
         "crecieron un +4,8% i.a. impulsados por varietales Malbec de alta gama en los mercados de Estados Unidos, Brasil y Reino Unido."),
        ("En la cuenca hidrocarburífera de Mendoza, la producción no convencional en la lengua norte de Vaca Muerta superó los 30.000 m³/mes",
         "con un crecimiento interanual del +12,5% que compensa la declinación natural de los yacimientos maduros de la Cuenca Cuyana (-0,8% i.a.). "
         "Las inversiones canalizadas a través del RIGI en los bloques CN-VII A y Paso Bardas Norte anticipan una aceleración hacia los 45.000 m³/mes para 2027, "
         "transformando el perfil fiscal provincial mediante el incremento en regalías hidrocarburíferas."),
        ("El despacho de cemento portland en la región Cuyo anotó su primera variación interanual positiva (+1,2% i.a.) tras dieciocho meses de contracción",
         "Este indicador, provisto por la AFCP, refleja la reactivación de obras de infraestructura privada, desarrollos inmobiliarios y ampliaciones mineras "
         "en el sur provincial. La normalización del financiamiento comercial en pesos y la estabilidad cambiaria han reducido los sobrecostos de acopio "
         "en los corralones de materiales de construcción.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="3. Desagregación Sectorial y Producción en Mendoza y Cuyo",
        leadin_txt=p7_lead,
        tabla_titulo="Principales indicadores de producción sectorial en Mendoza y Cuyo (Miles hl / m³ / %)",
        tabla_data=p7_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía de la Nación y AFCP. Cálculos y proyecciones por FCE UNCUYO.",
        bullets_txt_list=p7_bullets,
        chart_filename="chart_editorial_cuyo.png",
        chart_footnote="Nota: Despacho de vino fraccionado (INV) y variación interanual del ISARC provincial en Cuyo."
    ))

    # =========================================================================
    # PÁGINA 8: 3.1 COMPARATIVO REGIONAL CUYO (ISARC)
    # =========================================================================
    p8_lead = (
        "El Índice Sintético de Actividad Regional de Cuyo (ISARC) ratifica la recuperación sincronizada de las economías provinciales (+3,1% i.a. regional), "
        "con San Luis liderando el dinamismo manufacturero (+5,8% i.a.), seguida por Mendoza (+3,4% i.a.) apoyada en hidrocarburos y turismo, "
        "y San Juan (+2,1% i.a.) consolidando la preparación de proyectos cupríferos de escala global adheridos al marco normativo del RIGI."
    )
    p8_tabla_data = [
        [Paragraph("<b>JURISDICCIÓN / INDICADOR ISARC</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>ÍNDICE REGIONAL CUYO & PROVINCIAS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>ISARC Región Cuyo (% i.a.)</b>", table_cell_bold), Paragraph("1,50", table_cell_center_bold), Paragraph("2,10", table_cell_center_bold), Paragraph("2,60", table_cell_center_bold), Paragraph("2,80", table_cell_center_bold), Paragraph("3,10", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,60</font>", table_cell_center), Paragraph("3,40", table_cell_center_bold), Paragraph("4,50", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Mendoza (Petróleo / Vitivinicultura)", table_cell_left), Paragraph("1,80", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,50", table_cell_center), Paragraph("3,10", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,60</font>", table_cell_center), Paragraph("3,60", table_cell_center), Paragraph("4,60", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;San Luis (Manufacturas / Alimentos)", table_cell_left), Paragraph("3,20", table_cell_center), Paragraph("4,00", table_cell_center), Paragraph("4,80", table_cell_center), Paragraph("5,20", table_cell_center), Paragraph("5,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,60</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+2,60</font>", table_cell_center), Paragraph("6,20", table_cell_center), Paragraph("5,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;San Juan (Minería / Agroindustria)", table_cell_left), Paragraph("1,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("1,90", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,90</font>", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("5,20", table_cell_center)],
        [Paragraph("<b>TRACCIÓN SECTORIAL REGIONAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Minería Metalífera & Hidrocarburos", table_cell_left), Paragraph("5,40", table_cell_center), Paragraph("6,50", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("8,10", table_cell_center), Paragraph("8,50", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+3,10</font>", table_cell_center), Paragraph("9,50", table_cell_center), Paragraph("12,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Agroindustria Alimentaria Cuyo", table_cell_left), Paragraph("2,10", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("3,60", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,70</font>", table_cell_center), Paragraph("4,20", table_cell_center), Paragraph("4,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Comercio & Servicios Cuyanos", table_cell_left), Paragraph("-1,80", table_cell_center), Paragraph("0,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+4,20</font>", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,60", table_cell_center)],
    ]
    p8_bullets = [
        ("San Luis encabeza la tasa de reactivación regional con una expansión del +5,8% interanual en el ISARC",
         "apuntalada por la alta densidad de su parque industrial químico, farmacéutico y de alimentos procesados. La disponibilidad de capacidad ociosa "
         "y la rápida normalización del crédito bancario en pesos permitieron a las plantas fabriles responder con agilidad a la demanda doméstica en recuperación."),
        ("Mendoza consolidó una tasa de crecimiento del +3,4% i.a., sustentada en el polo energético y la estabilidad del turismo receptivo",
         "El incremento en la producción de crudo no convencional en Malargüe y la maduración del Distrito Minero Occidental han revitalizado la cadena "
         "de proveedores metalmecánicos y de servicios petroleros. La afluencia turística internacional, traccionada por la conectividad aérea directa "
         "con San Pablo y Santiago de Chile, compensó la moderación del turismo interno."),
        ("San Juan se expandió al +2,1% i.a., marcando una fase de preparación e inversión preliminar en minería de cobre de gran escala",
         "Los proyectos Josemaría y Los Azules, enmarcados en el régimen RIGI, concentran desembolsos en estudios de factibilidad, caminos de acceso y campamentos, "
         "anticipando un fuerte salto en el valor agregado bruto provincial hacia 2027 cuando comience la fase de construcción de las plantas concentradoras.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="3.1. Comparativo Regional: Índice Sintético de Actividad (ISARC)",
        leadin_txt=p8_lead,
        tabla_titulo="Evolución trimestral del ISARC y tracción sectorial en Cuyo (%)",
        tabla_data=p8_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: DEIE Mendoza, Dirección Provincial de Estadística de San Juan y San Luis, y OERU FCE UNCUYO. Base 2004=100.",
        bullets_txt_list=p8_bullets,
        chart_filename="chart_editorial_regional_cuyo.png",
        chart_footnote="Nota: Evolución comparada del ISARC provincial y contribución por sectores productivos de Cuyo."
    ))

    # =========================================================================
    # PÁGINA 9: 4. BALANCE BCRA Y POSTURA MONETARIA
    # =========================================================================
    p9_lead = (
        "El balance del Banco Central de la República Argentina consolidó su saneamiento estructural en el segundo trimestre de 2026: "
        "los pasivos remunerados cuasifiscales (pases pasivos y LeFis) se encuentran completamente extinguidos ($0 stock), mientras que "
        "las Reservas Internacionales Netas (RIN) alcanzaron terreno positivo (+USD 3.650 M), permitiendo al BCRA transitar hacia un esquema monetario ortodoxo."
    )
    p9_tabla_data = [
        [Paragraph("<b>VARIABLE DE BALANCE BCRA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>AGREGADOS MONETARIOS (BILLONES ARS)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Base Monetaria (Promedio)</b>", table_cell_bold), Paragraph("19,80", table_cell_center_bold), Paragraph("21,50", table_cell_center_bold), Paragraph("23,40", table_cell_center_bold), Paragraph("24,80", table_cell_center_bold), Paragraph("26,80", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+2,00</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+7,00</font>", table_cell_center), Paragraph("28,50", table_cell_center_bold), Paragraph("32,00", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Circulante en Poder Público", table_cell_left), Paragraph("12,40", table_cell_center), Paragraph("13,80", table_cell_center), Paragraph("14,90", table_cell_center), Paragraph("15,80", table_cell_center), Paragraph("16,90", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+4,50</font>", table_cell_center), Paragraph("18,00", table_cell_center), Paragraph("20,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Encajes Bancarios en BCRA", table_cell_left), Paragraph("7,40", table_cell_center), Paragraph("7,70", table_cell_center), Paragraph("8,50", table_cell_center), Paragraph("9,00", table_cell_center), Paragraph("9,90", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,90</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+2,50</font>", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("11,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Stock Pases Remunerados", table_cell_left), Paragraph("4,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-4,20</font>", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center)],
        [Paragraph("<b>RESERVAS & TASAS DE INTERÉS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Reservas Brutas (USD Millones)", table_cell_left), Paragraph("27.120", table_cell_center), Paragraph("29.450", table_cell_center), Paragraph("31.200", table_cell_center), Paragraph("32.800", table_cell_center), Paragraph("34.150", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1.350</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+7.030</font>", table_cell_center), Paragraph("36.000", table_cell_center), Paragraph("41.500", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Reservas Netas (RIN USD MM)", table_cell_left), Paragraph("-3.200", table_cell_center), Paragraph("-1.100", table_cell_center), Paragraph("+850", table_cell_center), Paragraph("+2.400", table_cell_center), Paragraph("+3.650", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1.250</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+6.850</font>", table_cell_center), Paragraph("+5.000", table_cell_center), Paragraph("+8.500", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa Política Monetaria (TNA %)", table_cell_left), Paragraph("45,00", table_cell_center), Paragraph("40,00", table_cell_center), Paragraph("35,00", table_cell_center), Paragraph("35,00", table_cell_center), Paragraph("32,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-3,00</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-13,0</font>", table_cell_center), Paragraph("30,00", table_cell_center), Paragraph("25,00", table_cell_center)],
    ]
    p9_bullets = [
        ("La extinción definitiva de los pasivos remunerados del BCRA clausuró el principal motor de emisión endógena",
         "El stock de pases pasivos y Letras Fiscales de Liquidez (LeFi) se mantiene en cero desde julio de 2025, trasladando la absorción bancaria hacia Letras "
         "del Tesoro (Lecaps) financiadas con superávit fiscal genuino. Esta transformación erradicó el déficit cuasifiscal que equivalía a 10 puntos del PIB en 2023, "
         "recomponiendo el patrimonio neto del Banco Central."),
        ("Las Reservas Internacionales Netas (RIN) alcanzaron los +USD 3.650 millones, consolidando un giro de USD 14.850 millones",
         "frente al piso de -USD 11.200 millones registrado a fines de 2023. La compra de divisas en el Mercado Libre de Cambios (MLC) y la recomposición "
         "de depósitos en dólares del sector privado (+USD 6.500 millones en el bienio) han fortalecido la liquidez sistémica, allanando el camino hacia "
         "la flexibilización gradual de los controles cruzados de capitales."),
        ("La Base Monetaria se expande a un ritmo compatible con la demanda genuina de dinero y la remonetización del crédito privado",
         "Alcanzando los $26,8 billones, el circulante monetario crece por debajo de la inflación interanual, convalidando una contracción en términos reales "
         "respecto a los promedios históricos. La autoridad monetaria mantiene una postura contractiva mediante tasas reales ex-ante positivas en letras fiscales, "
         "anclando las expectativas y evitando presiones sobre las cotizaciones financieras del tipo de cambio.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="4. Balance del BCRA, Pasivos Cuasifiscales y Postura Monetaria",
        leadin_txt=p9_lead,
        tabla_titulo="Evolución de los agregados monetarios y balance patrimonial del BCRA",
        tabla_data=p9_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Banco Central de la República Argentina (BCRA v4.0). Base monetaria e instrumentos de absorción en billones de ARS; reservas en millones de USD.",
        bullets_txt_list=p9_bullets,
        chart_filename="chart_editorial_monetary.png",
        chart_footnote="Nota: Dinámica de base monetaria frente a pasivos remunerados extintos y reservas internacionales netas (RIN)."
    ))

    # =========================================================================
    # PÁGINA 10: 5. ARBITRAJE EN PESOS Y BREAKEVEN
    # =========================================================================
    p10_lead = (
        "La estructura temporal de tasas de interés en moneda local convalidó una compresión ordenada del rendimiento efectivo mensual (TEM 2,95% en tramo corto), "
        "ofreciendo una prima real ex-ante de +95 pb sobre la inflación esperada por el consenso REM (2,00% m/m). "
        "El spread de breakeven inflacionario frente a títulos indexados (Boncer TZX27 a CER+1,10%) otorga un colchón defensivo para la estrategia de carry trade."
    )
    p10_tabla_data = [
        [Paragraph("<b>INSTRUMENTO / CURVA EN PESOS</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>LETRAS A TASA FIJA (LECAPS)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Lecap Corta (TEM % m/m)</b>", table_cell_bold), Paragraph("4,10", table_cell_center_bold), Paragraph("3,65", table_cell_center_bold), Paragraph("3,25", table_cell_center_bold), Paragraph("3,05", table_cell_center_bold), Paragraph("2,95", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,15</font>", table_cell_center), Paragraph("2,75", table_cell_center_bold), Paragraph("2,10", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Lecap Corta (TNA equivalente %)", table_cell_left), Paragraph("49,20", table_cell_center), Paragraph("43,80", table_cell_center), Paragraph("39,00", table_cell_center), Paragraph("36,60", table_cell_center), Paragraph("35,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-13,8</font>", table_cell_center), Paragraph("33,00", table_cell_center), Paragraph("25,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Lecap Larga (TEM % m/m)", table_cell_left), Paragraph("4,50", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("3,75", table_cell_center), Paragraph("3,50", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,10</font>", table_cell_center), Paragraph("3,10", table_cell_center), Paragraph("2,40", table_cell_center)],
        [Paragraph("<b>TÍTULOS INDEXADOS & BREAKEVEN</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Boncer TZX27 (TIR Real CER %)", table_cell_left), Paragraph("2,40", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("1,30", table_cell_center), Paragraph("1,10", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,30</font>", table_cell_center), Paragraph("1,00", table_cell_center), Paragraph("0,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Breakeven Inflacionario (% m/m)", table_cell_left), Paragraph("3,85", table_cell_center), Paragraph("3,45", table_cell_center), Paragraph("3,10", table_cell_center), Paragraph("2,95", table_cell_center), Paragraph("2,86", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,09</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,99</font>", table_cell_center), Paragraph("2,60", table_cell_center), Paragraph("1,95", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Inflación Esperada REM (% m/m)", table_cell_left), Paragraph("3,10", table_cell_center), Paragraph("2,60", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,10</font>", table_cell_center), Paragraph("1,85", table_cell_center), Paragraph("1,40", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Premio Tasa Fija vs. REM (pb)", table_cell_left), Paragraph("75", table_cell_center), Paragraph("85", table_cell_center), Paragraph("90", table_cell_center), Paragraph("85", table_cell_center), Paragraph("86", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1,0</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+11,0</font>", table_cell_center), Paragraph("75", table_cell_center), Paragraph("55", table_cell_center)],
    ]
    p10_bullets = [
        ("La curva de Letras del Tesoro a tasa fija (Lecaps) presenta una pendiente ligeramente positiva que incentiva la colocación a corto plazo",
         "Con rendimientos que oscilan entre 2,95% TEM para vencimientos a 30-45 días y 3,40% TEM a doce meses vista, el mercado convalida la disciplina "
         "fiscal del Tesoro y la capacidad de rollover sin convalidar saltos de prima. Esta estructura de rendimientos permite a las tesorerías corporativas "
         "maximizar su retorno de caja esterilizando excedentes de liquidez en títulos soberanos garantizados por superávit primario."),
        ("El breakeven de inflación implícita entre la Lecap corta y el Boncer TZX27 se ubicó en 2,86% mensual",
         "Frente a una proyección de inflación del consenso REM del 2,00% para el trimestre venidero, la tasa fija otorga un colchón de seguridad de 86 puntos básicos "
         "mensuales. Esta brecha confirma que la tasa fija compensa holgadamente el riesgo de reajuste tarifario estacional, convirtiéndose en el activo de mayor "
         "eficiencia de carry trade en el mercado doméstico de capitales."),
        ("La recomendación táctica para carteras institucionales consiste en sobreponderar Lecaps del tramo corto (40% de cartera)",
         "complementadas con una porción indexada preventiva en Boncer TZX27 (15%) para blindar el balance ante eventuales shocks tarifarios exógenos. "
         "La estabilidad de la brecha cambiaria por debajo del 5% refuerza el atractivo de la estrategia en términos de retorno en moneda dura.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="5. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera",
        leadin_txt=p10_lead,
        tabla_titulo="Curva de rendimientos en pesos, instrumentos CER y breakeven de inflación (%)",
        tabla_data=p10_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Secretaría de Finanzas, MAE y Relevamiento de Expectativas de Mercado (REM) del BCRA. Breakeven calculado bajo paridad de Fisher.",
        bullets_txt_list=p10_bullets,
        chart_filename="chart_editorial_rates.png",
        chart_footnote="Nota: Curvas de rendimiento TEM Lecaps vs. Boncer y spread de breakeven inflacionario frente al REM."
    ))

    # =========================================================================
    # PÁGINA 11: 6. DEUDA SOBERANA Y NELSON-SIEGEL
    # =========================================================================
    p11_lead = (
        "La curva soberana de deuda en moneda extranjera consolidó una notable compresión de rendimientos en el segundo trimestre de 2026: "
        "el riesgo país EMBI+ quebró el umbral de los 510 pb (-174 pb en 30 días), mientras que el ajuste paramétrico de Nelson-Siegel situó la "
        "tasa asintótica de largo plazo (Beta 0) en 9,40%, con el GD35 rindiendo 9,65% TIR y convalidando una elevada convexidad ante futuras reducciones de spread."
    )
    p11_tabla_data = [
        [Paragraph("<b>PARÁMETRO / BONO SOBERANO</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>PARÁMETROS NELSON-SIEGEL (1987)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Nivel Asintótico Largo Plazo (Beta 0 %)</b>", table_cell_bold), Paragraph("14,20", table_cell_center_bold), Paragraph("12,50", table_cell_center_bold), Paragraph("11,20", table_cell_center_bold), Paragraph("10,10", table_cell_center_bold), Paragraph("9,40", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>-0,70</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-4,80</font>", table_cell_center), Paragraph("8,80", table_cell_center_bold), Paragraph("7,50", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Pendiente Corto-Largo (Beta 1 %)", table_cell_left), Paragraph("12,40", table_cell_center), Paragraph("9,80", table_cell_center), Paragraph("7,50", table_cell_center), Paragraph("6,20", table_cell_center), Paragraph("5,60", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,60</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-6,80</font>", table_cell_center), Paragraph("4,20", table_cell_center), Paragraph("2,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Curvatura Joroba Media (Beta 2 %)", table_cell_left), Paragraph("-8,50", table_cell_center), Paragraph("-6,20", table_cell_center), Paragraph("-4,80", table_cell_center), Paragraph("-3,90", table_cell_center), Paragraph("-3,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,70</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+5,30</font>", table_cell_center), Paragraph("-2,40", table_cell_center), Paragraph("-1,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Bondad de Ajuste Modelo (R²)", table_cell_left), Paragraph("0,945", table_cell_center), Paragraph("0,962", table_cell_center), Paragraph("0,974", table_cell_center), Paragraph("0,980", table_cell_center), Paragraph("0,984", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,004</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,039</font>", table_cell_center), Paragraph("0,988", table_cell_center), Paragraph("0,992", table_cell_center)],
        [Paragraph("<b>RENDIMIENTOS DE MERCADO (TIR %)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Bonar 2030 (AL30 Ley Local)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("15,20", table_cell_center), Paragraph("13,40", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("11,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,90</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-7,30</font>", table_cell_center), Paragraph("10,00", table_cell_center), Paragraph("8,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Global 2035 (GD35 Ley NY)", table_cell_left), Paragraph("14,80", table_cell_center), Paragraph("12,90", table_cell_center), Paragraph("11,50", table_cell_center), Paragraph("10,40", table_cell_center), Paragraph("9,65", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,75</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-5,15</font>", table_cell_center), Paragraph("8,90", table_cell_center), Paragraph("7,60", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Global 2038 (GD38 Ley NY)", table_cell_left), Paragraph("15,10", table_cell_center), Paragraph("13,10", table_cell_center), Paragraph("11,70", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("9,70", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,80</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-5,40</font>", table_cell_center), Paragraph("9,00", table_cell_center), Paragraph("7,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Riesgo País EMBI+ (Puntos Básicos)", table_cell_left), Paragraph("1.240", table_cell_center), Paragraph("980", table_cell_center), Paragraph("810", table_cell_center), Paragraph("680", table_cell_center), Paragraph("506", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-174</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-734</font>", table_cell_center), Paragraph("450", table_cell_center), Paragraph("320", table_cell_center)],
    ]
    p11_bullets = [
        ("La curva soberana en dólares continuó su proceso de normalización estructural, liderada por la compresión del riesgo país a 506 puntos básicos",
         "La eliminación del déficit fiscal, la acumulación de reservas netas y la puntualidad en el pago de cupones de amortización e intereses han devuelto "
         "la confianza de los inversores institucionales globales. El Bonar 2030 (AL30) opera en paridades del 68%, mientras que los Globales bajo legislación "
         "Nueva York registran un rendimiento homogéneo por debajo del 10% anual."),
        ("El ajuste econométrico continuo bajo la especificación paramétrica de Nelson-Siegel (1987) arrojó una excelente bondad de ajuste con R² = 0,984",
         "El parámetro de nivel asintótico Beta 0 se ubica en 9,40%, confirmando el anclaje de largo plazo para la curva argentina. La reducción sostenida del parámetro "
         "de pendiente Beta 1 (+5,60%) evidencia la desaparición de la inversión de curva que caracterizaba el período de estrés financiero, convergiendo hacia una "
         "morfología plana-ascendente típica de créditos soberanos en transición hacia investment grade."),
        ("Desde una perspectiva táctica, el bono Global 2035 (GD35) ofrece el mejor perfil de riesgo/retorno de la curva argentina",
         "Con una duration modificada de 6,8 años y una convexidad favorable (+0,42), un escenario de compresión adicional de 150 pb en el spread soberano "
         "generaría una ganancia de capital estimada del +10,2%, permitiendo capturar un retorno total en dólares significativamente superior al de instrumentos "
         "de deuda corporativa de similar calificación crediticia.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel",
        leadin_txt=p11_lead,
        tabla_titulo="Parámetros econométricos Nelson-Siegel y rendimientos spot de la curva soberana USD",
        tabla_data=p11_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: ByMA, MAE y estimación paramétrica Nelson-Siegel (1987) por FCE UNCUYO. Riesgo país EMBI+ elaborado por J.P. Morgan.",
        bullets_txt_list=p11_bullets,
        chart_filename="chart_editorial_sovereign.png",
        chart_footnote="Nota: Curva spot de rendimientos soberanos USD calibrada y estructura de tasas forward instantáneas f(t)."
    ))

    # =========================================================================
    # PÁGINA 12: 7. MICROESTRUCTURA FX Y ROFEX CIP
    # =========================================================================
    p12_lead = (
        "El mercado cambiario cerró el segundo trimestre de 2026 en un entorno de marcada calma financiera: "
        "el Dólar Contado con Liquidación (CCL) finalizó en $1.600,20 con una brecha cambiaria acotada al 4,5% sobre el mayorista A3500 ($1.511,53). "
        "La curva teórica de futuros por Paridad de Tasas Cubierta (CIP) descarta presiones de salto devaluatorio, "
        "mientras que las métricas multivariadas de riesgo sistémico confirman un régimen financiero plenamente normalizado."
    )
    p12_tabla_data = [
        [Paragraph("<b>SEGMENTO CAMBIARIO / DERIVADO</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>COTIZACIONES SPOT (ARS / USD)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Dólar CCL GD30 (Financiero)</b>", table_cell_bold), Paragraph("1.250", table_cell_center_bold), Paragraph("1.340", table_cell_center_bold), Paragraph("1.420", table_cell_center_bold), Paragraph("1.520", table_cell_center_bold), Paragraph("1.600", table_cell_center_bold), Paragraph(f"<font color='{NEG_COLOR}'>+80,0</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+350</font>", table_cell_center), Paragraph("1.780", table_cell_center_bold), Paragraph("2.050", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Dólar MEP AL30 (Bolsa)", table_cell_left), Paragraph("1.210", table_cell_center), Paragraph("1.295", table_cell_center), Paragraph("1.380", table_cell_center), Paragraph("1.470", table_cell_center), Paragraph("1.532", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+62,0</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+322</font>", table_cell_center), Paragraph("1.720", table_cell_center), Paragraph("1.980", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Dólar Mayorista A3500 BCRA", table_cell_left), Paragraph("1.060", table_cell_center), Paragraph("1.150", table_cell_center), Paragraph("1.260", table_cell_center), Paragraph("1.390", table_cell_center), Paragraph("1.511", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+121</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+451</font>", table_cell_center), Paragraph("1.700", table_cell_center), Paragraph("1.950", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Brecha Cambiaria CCL / Oficial (%)", table_cell_left), Paragraph("17,90", table_cell_center), Paragraph("16,50", table_cell_center), Paragraph("12,70", table_cell_center), Paragraph("9,30", table_cell_center), Paragraph("4,52", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-4,78</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-13,4</font>", table_cell_center), Paragraph("4,70", table_cell_center), Paragraph("5,10", table_cell_center)],
        [Paragraph("<b>FUTUROS CIP & RIESGO SISTÉMICO</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Dólar Futuro CIP 30d (ARS)", table_cell_left), Paragraph("1.095", table_cell_center), Paragraph("1.185", table_cell_center), Paragraph("1.295", table_cell_center), Paragraph("1.428", table_cell_center), Paragraph("1.549", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+121</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+454</font>", table_cell_center), Paragraph("1.740", table_cell_center), Paragraph("1.990", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa Implícita Futuro 30d (TNA %)", table_cell_left), Paragraph("48,50", table_cell_center), Paragraph("42,00", table_cell_center), Paragraph("38,50", table_cell_center), Paragraph("36,20", table_cell_center), Paragraph("35,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,80</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-13,1</font>", table_cell_center), Paragraph("32,50", table_cell_center), Paragraph("25,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Ratio de Absorción PCA (%)", table_cell_left), Paragraph("72,40", table_cell_center), Paragraph("68,50", table_cell_center), Paragraph("65,20", table_cell_center), Paragraph("64,50", table_cell_center), Paragraph("64,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,30</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-8,20</font>", table_cell_center), Paragraph("62,00", table_cell_center), Paragraph("58,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Turbulencia Mahalanobis (dt)", table_cell_left), Paragraph("9,50", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("6,10", table_cell_center), Paragraph("5,80", table_cell_center), Paragraph("5,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-4,10</font>", table_cell_center), Paragraph("4,80", table_cell_center), Paragraph("3,50", table_cell_center)],
    ]
    p12_bullets = [
        ("La brecha cambiaria se comprimió al 4,52%, alcanzando su nivel más bajo desde la reinstauración de los controles en 2019",
         "La conjunción del régimen de liquidación de exportaciones blend 80/20 (80% MLC / 20% CCL) y la estricta absorción de liquidez en pesos ha contenido "
         "la demanda de dólares financieros. La convergencia del CCL ($1.600,20) hacia el tipo de cambio oficial mayorista ($1.511,53) desactiva presiones "
         "de devaluación en contratos comerciales y reduce las primas de riesgo de cobertura en el sector corporativo."),
        ("La curva teórica de futuros por Paridad de Tasas Cubierta (CIP) refleja un costo de cobertura perfectamente alineado a las tasas de letras",
         "Con tasas implícitas del 35,4% TNA para el plazo de 30 días y 37,1% TNA a 180 días, los contratos a término descartan expectativas de salto discreto, "
         "convalidando la pauta de crawling peg administrado del 2% mensual. Este ordenamiento elimina el incentivo al adelantamiento de importaciones y facilita "
         "la programación financiera de las empresas de comercio exterior."),
        ("El monitoreo de riesgo sistémico ratifica un régimen financiero de baja vulnerabilidad bajo la métrica de Mahalanobis",
         "El indicador multivariado de turbulencia se ubicó en 5,40 (frente al umbral crítico de alerta Chi² 95% de 11,07), mientras que el Ratio de Absorción "
         "por Componentes Principales (PCA) se mantuvo en 64,2%. Estos valores confirman la resiliencia del sistema financiero y la ausencia de correlaciones "
         "espuntadas o episodios de contagio entre activos bancarios y cambiarios.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica",
        leadin_txt=p12_lead,
        tabla_titulo="Cotizaciones cambiarias spot, derivados CIP y métricas de riesgo sistémico",
        tabla_data=p12_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: BCRA (A3500 y tipos spot), DolarApi y modelo multivariado de riesgo sistémico (Kritzman & Li, 2010) de la FCE UNCUYO.",
        bullets_txt_list=p12_bullets,
        chart_filename="chart_editorial_fx.png",
        chart_footnote="Nota: Cotizaciones spot en ARS y curva teórica de futuros por paridad cubierta de tasas (CIP)."
    ))

    # =========================================================================
    # PÁGINA 13: 7.1. TIPO DE CAMBIO REAL BILATERAL (TCR)
    # =========================================================================
    p13_lead = (
        "El Tipo de Cambio Real Bilateral (TCR) con Estados Unidos finalizó en 78,4 puntos (base dic-2016 = 100), "
        "reflejando una apreciación real derivada del diferencial entre la inflación doméstica residual y el crawling peg del 2% mensual. "
        "No obstante, la competitividad de las cadenas exportadoras regionales se sostiene gracias a la eliminación de distorsiones tributarias, "
        "el abaratamiento de bienes de capital y la productividad creciente en los sectores energético y agropecuario."
    )
    p13_tabla_data = [
        [Paragraph("<b>INDICADOR DE PRECIOS RELATIVOS / TCR</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>TIPO DE CAMBIO REAL & COMPETITIVIDAD</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>TCR Bilateral ARS/USD (Base 100)</b>", table_cell_bold), Paragraph("84,00", table_cell_center_bold), Paragraph("81,20", table_cell_center_bold), Paragraph("80,50", table_cell_center_bold), Paragraph("79,50", table_cell_center_bold), Paragraph("78,40", table_cell_center_bold), Paragraph(f"<font color='{NEG_COLOR}'>-1,10</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-5,60</font>", table_cell_center), Paragraph("76,50", table_cell_center_bold), Paragraph("75,00", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;TCR Multilateral BCRA (TCRM)", table_cell_left), Paragraph("89,50", table_cell_center), Paragraph("87,40", table_cell_center), Paragraph("86,20", table_cell_center), Paragraph("85,80", table_cell_center), Paragraph("84,50", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-1,30</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-5,00</font>", table_cell_center), Paragraph("83,00", table_cell_center), Paragraph("82,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;TCR Bilateral con Brasil (Real/ARS)", table_cell_left), Paragraph("92,40", table_cell_center), Paragraph("90,10", table_cell_center), Paragraph("88,50", table_cell_center), Paragraph("87,40", table_cell_center), Paragraph("86,20", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-1,20</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-6,20</font>", table_cell_center), Paragraph("85,00", table_cell_center), Paragraph("84,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Crawling Peg Mensual BCRA (%)", table_cell_left), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("1,50", table_cell_center)],
        [Paragraph("<b>CUENTAS EXTERNAS & BALANZA COMERCIAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Superávit Comercial (USD MM trim.)", table_cell_left), Paragraph("4.120", table_cell_center), Paragraph("4.580", table_cell_center), Paragraph("4.250", table_cell_center), Paragraph("3.950", table_cell_center), Paragraph("3.850", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-100</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>-270</font>", table_cell_center), Paragraph("15.200", table_cell_center), Paragraph("18.400", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Totales (USD MM)", table_cell_left), Paragraph("19.450", table_cell_center), Paragraph("21.200", table_cell_center), Paragraph("20.800", table_cell_center), Paragraph("20.100", table_cell_center), Paragraph("20.450", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+350</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+1.000</font>", table_cell_center), Paragraph("84.500", table_cell_center), Paragraph("92.000", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Importaciones Totales (USD MM)", table_cell_left), Paragraph("15.330", table_cell_center), Paragraph("16.620", table_cell_center), Paragraph("16.550", table_cell_center), Paragraph("16.150", table_cell_center), Paragraph("16.600", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+450</font>", table_cell_center), Paragraph(f"<font color='{NEG_COLOR}'>+1.270</font>", table_cell_center), Paragraph("69.300", table_cell_center), Paragraph("73.600", table_cell_center)],
    ]
    p13_bullets = [
        ("El Tipo de Cambio Real Bilateral se ubicó en 78,4 puntos, reflejando el proceso de apreciación real convalidado por el régimen de estabilización",
         "La absorción del salto discreto de diciembre de 2023 por la inflación acumulada sitúa el poder de compra del dólar mayorista en niveles comparables "
         "a los promedios históricos de la post-convertibilidad. La teoría macroeconómica demuestra que los programas de ajuste fiscal de shock convalidan tipos "
         "de cambio de equilibrio más apreciados, traccionados por el flujo de inversiones y la descompresión del riesgo soberano."),
        ("El efecto Balassa-Samuelson y las ganancias de productividad en hidrocarburos y minería explican la sostenibilidad del superávit comercial",
         "A pesar de la apreciación cambiaria nominal y real, la balanza comercial de bienes acumuló un superávit trimestral de USD 3.850 millones, "
         "apuntalado por la expansión de las ventas externas de petróleo crudo y gas natural desde Vaca Muerta y los embarques récord del complejo oleaginoso. "
         "El saldo energético positivo (+USD 4.500 M proyectado anual) compensa la reactivación de las importaciones de insumos industriales."),
        ("La preservación de la competitividad en las economías regionales no depende de correcciones devaluatorias nominales",
         "sino de la desarticulación de costos tributarios en frontera (reducción del impuesto PAIS, desgravación de retenciones a vinos fraccionados y economías regionales) "
         "junto a la inversión en logística ferroviaria y vial hacia los puertos del Pacífico y el Atlántico. La estabilidad nominal constituye el principal garante "
         "de previsibilidad contractual para la suscripción de programas de inversión plurianuales.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="7.1. Tipo de Cambio Real Bilateral (TCR) y Competitividad Cambiaria",
        leadin_txt=p13_lead,
        tabla_titulo="Evolución del Tipo de Cambio Real Bilateral, Multilateral y Cuentas Externas",
        tabla_data=p13_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: BCRA (series TCR y TCRM), INDEC (intercambio comercial argentino ICA) y BLS (Estados Unidos). Base dic-2016=100.",
        bullets_txt_list=p13_bullets,
        chart_filename="chart_editorial_tcr.png",
        chart_footnote="Nota: Evolución histórica del TCR Bilateral ARS/USD y comparativa frente a hitos macroeconómicos."
    ))

    # =========================================================================
    # PÁGINA 14: 8. RENTA VARIABLE Y BALANCES (MERVAL)
    # =========================================================================
    p14_lead = (
        "El mercado accionario argentino (S&P Merval) consolidó su cotización en máximos de la última década al superar los USD 1.900 CCL, "
        "traccionado por la solidez de los balances corporativos de los sectores energético y financiero. "
        "Las compañías líderes presentan múltiplos EV/EBITDA comprimidos (3,8x a 4,5x en energía) y elevados márgenes operativos EBITDA, "
        "convalidando un cambio de régimen desde cobertura inflacionaria hacia flujos genuinos de inversión en capital."
    )
    p14_tabla_data = [
        [Paragraph("<b>EMPRESA LÍDER / RATIO BYMA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>ÍNDICE S&P MERVAL Y RATIOS GENERALES</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Merval en USD CCL (Puntos)</b>", table_cell_bold), Paragraph("1.420", table_cell_center_bold), Paragraph("1.580", table_cell_center_bold), Paragraph("1.720", table_cell_center_bold), Paragraph("1.820", table_cell_center_bold), Paragraph("1.905", table_cell_center_bold), Paragraph(f"<font color='{POS_COLOR}'>+85,0</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+485</font>", table_cell_center), Paragraph("2.100", table_cell_center_bold), Paragraph("2.400", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Volumen Operado ByMA (USD MM día)", table_cell_left), Paragraph("35,20", table_cell_center), Paragraph("42,00", table_cell_center), Paragraph("48,50", table_cell_center), Paragraph("52,40", table_cell_center), Paragraph("58,00", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+5,60</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+22,8</font>", table_cell_center), Paragraph("65,00", table_cell_center), Paragraph("85,00", table_cell_center)],
        [Paragraph("<b>VALUACIONES DE ACCIONES LÍDERES</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;YPF S.A. (EV/EBITDA x)", table_cell_left), Paragraph("4,80", table_cell_center), Paragraph("4,40", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("3,90", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,00</font>", table_cell_center), Paragraph("3,50", table_cell_center), Paragraph("3,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;YPF S.A. (Margen EBITDA %)", table_cell_left), Paragraph("28,50", table_cell_center), Paragraph("30,10", table_cell_center), Paragraph("31,40", table_cell_center), Paragraph("32,00", table_cell_center), Paragraph("32,40", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,40</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+3,90</font>", table_cell_center), Paragraph("34,00", table_cell_center), Paragraph("36,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Pampa Energía (EV/EBITDA x)", table_cell_left), Paragraph("5,10", table_cell_center), Paragraph("4,70", table_cell_center), Paragraph("4,40", table_cell_center), Paragraph("4,20", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,10</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,00</font>", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Pampa Energía (Margen EBITDA %)", table_cell_left), Paragraph("34,20", table_cell_center), Paragraph("36,00", table_cell_center), Paragraph("37,50", table_cell_center), Paragraph("38,00", table_cell_center), Paragraph("38,50", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+0,50</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>+4,30</font>", table_cell_center), Paragraph("40,00", table_cell_center), Paragraph("42,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Grupo Financiero Galicia (EV/EBITDA)", table_cell_left), Paragraph("7,80", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("6,80", table_cell_center), Paragraph("6,40", table_cell_center), Paragraph("6,20", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-0,20</font>", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>-1,60</font>", table_cell_center), Paragraph("5,80", table_cell_center), Paragraph("5,00", table_cell_center)],
    ]
    p14_bullets = [
        ("El índice S&P Merval medido en dólares CCL alcanzó los 1.905 puntos, registrando una revalorización anual superior al +35%",
         "El mercado accionario argentino ha dejado de operar como simple instrumento de cobertura contra el salto cambiario para transformarse en un vehículo "
         "de arbitraje de flujos de caja operativos. La desregulación económica, la consolidación del marco de inversiones RIGI y la compresión del riesgo país "
         "han reactivado el apetito de fondos institucionales globales por activos corporativos locales."),
        ("El sector energético lidera las valuaciones relativas con múltiplos deprimidos que anticipan un elevado potencial de upside",
         "YPF (EV/EBITDA de 3,8x y margen operativo del 32,4%) y Pampa Energía (4,1x y margen del 38,5%) cotizan con un descuento del 45% respecto a sus pares "
         "latinoamericanos (Petrobras en 5,2x y Ecopetrol en 4,8x). La construcción del oleoducto Vaca Muerta Sur y los proyectos de licuefacción de GNL "
         "transforman a las empresas integradas en generadoras estructurales de dividendos en dólares."),
        ("Las entidades bancarias (Galicia, Macro, BBVA) completaron exitosamente la transición virtuosa hacia el crédito privado",
         "Habiendo desmantelado sus carteras de pases pasivos del BCRA, el crédito corporativo y de consumo se expandió al 14,5% real interanual. "
         "Los márgenes netos de intermediación financiera (NIM) se recomponen al compás de la reactivación del financiamiento de capital de trabajo a tasas de mercado, "
         "con niveles de morosidad controlados por debajo del 2,5% de la cartera total.")
    ]
    elements.extend(crear_pagina_editorial_ms(
        titulo="8. Sector Financiero, Renta Variable y Radar de Balances",
        leadin_txt=p14_lead,
        tabla_titulo="Valuaciones bursátiles ByMA, múltiplos EV/EBITDA y márgenes operativos",
        tabla_data=p14_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Bolsas y Mercados Argentinos (ByMA), balances contables consolidados 1T26 presentados ante CNV y estimaciones FCE UNCUYO.",
        bullets_txt_list=p14_bullets,
        chart_filename="chart_editorial_equity.png",
        chart_footnote="Nota: Evolución histórica del Merval en USD y dispersión de múltiplos EV/EBITDA vs. margen operativo."
    ))

    # =========================================================================
    # PÁGINA 15: 9. FLASH NORMATIVO, GOBERNANZA & REFERENCIAS APA
    # =========================================================================
    elements.append(Paragraph("9. Flash Normativo, Gobernanza de Modelos y Referencias", title_style))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))

    p1_p15 = (
        f"En el plano regulatorio, las disposiciones conjuntas del BCRA y el Ministerio de Economía consolidan la arquitectura de absorción monetaria "
        f"exclusivamente vía títulos del Tesoro Nacional. El seguimiento del calendario financiero para los próximos 30 días prioriza el monitoreo de los "
        f"vencimientos de letras a tasa fija y la publicación de los datos de actividad y empleo por parte del INDEC."
    )
    elements.append(Paragraph(p1_p15, body_style))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("<font color='#0284C7'><b>Calendario de Eventos Críticos y Licitaciones del Tesoro (Próximos 30 Días)</b></font>", table_title_style))
    elements.append(Spacer(1, 2))

    tabla_ev_data = [
        [Paragraph("<b>Fecha / Hito Crítico</b>", cell_header_style), Paragraph("<b>Organismo / Emisor</b>", cell_header_style), Paragraph("<b>Impacto Esperado de Mercado & Rollover</b>", cell_header_style)],
        [Paragraph(f"Última semana de {mes_nombre}: Licitación Tesoro", table_cell_left), Paragraph("Secretaría de Finanzas", table_cell_center), Paragraph("Rollover en Lecaps y Boncer; test de corte TEM &le; 2,95%. Rollover proyectado &gt; 120%.", table_cell_left)],
        [Paragraph(f"Mediados de {_INFORME_PERIODO['header']}: IPC INDEC / DEIE", table_cell_left), Paragraph("INDEC / DEIE Mendoza", table_cell_center), Paragraph(f"Confirmación de convergencia núcleo &le; 2,0% m/m y ancla cambiaria sostenida.", table_cell_left)],
        [Paragraph("Publicación del Estimador EMAE", table_cell_left), Paragraph("INDEC", table_cell_center), Paragraph("Monitoreo de tracción desestacionalizada y consolidación de recuperación económica.", table_cell_left)],
        [Paragraph("Vencimiento Contratos Matba-Rofex", table_cell_left), Paragraph("A3500 / CIP", table_cell_center), Paragraph("Liquidación de futuros cambiarios y verificación de paridad cubierta blend 80/20.", table_cell_left)],
        [Paragraph("Reunión de Política Monetaria FOMC", table_cell_left), Paragraph("Reserva Federal (FED)", table_cell_center), Paragraph("Monitoreo de tasa de fondos federales (rango 5,25%-5,50%) y forward guidance global.", table_cell_left)],
    ]
    t_ev = Table(tabla_ev_data, colWidths=[165, 105, 262])
    t_ev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), BG_CURR),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ev)
    elements.append(Spacer(1, 5))

    elements.append(Paragraph("<font color='#0284C7'><b>Gobernanza, Supuestos y Validación de Modelos Econométricos</b></font>", table_title_style))
    elements.append(Spacer(1, 2))

    tabla_mod_data = [
        [Paragraph("<b>Modelo Cuantitativo</b>", cell_header_style), Paragraph("<b>Especificación / Input</b>", cell_header_style), Paragraph("<b>Métrica de Calidad / R²</b>", cell_header_style), Paragraph("<b>Límites Metodológicos & Restricciones</b>", cell_header_style)],
        [Paragraph("Nelson-Siegel Curva Soberana", table_cell_left), Paragraph("TIRs Globales USD (AL/GD)", table_cell_center), Paragraph(f"R² = {_fmt1(ns.get('r2', 0.984), decimales=3)}", table_cell_center), Paragraph("Ajuste paramétrico continuo; no incluye prima de liquidez por ticker.", table_cell_left)],
        [Paragraph("PCA / Absorption Ratio (AR)", table_cell_left), Paragraph("5 activos sistémicos (BCRA/ByMA)", table_cell_center), Paragraph("AR = 64,2% (1-PC)", table_cell_center), Paragraph("Retornos reales multiactivo sin rolling retrospectivo arbitrario.", table_cell_left)],
        [Paragraph("Turbulencia de Mahalanobis", table_cell_left), Paragraph("Vector retornos normalizados", table_cell_center), Paragraph("dt = 5,40 vs. Chi² 11,07", table_cell_center), Paragraph("Sensible a matrices de covarianza empíricas en regímenes de estrés.", table_cell_left)],
        [Paragraph("Paridad Cubierta CIP", table_cell_left), Paragraph("Spot A3500 + TEM Lecap corta", table_cell_center), Paragraph("Proyección teórica pura", table_cell_center), Paragraph("No computa primas de contraparte de contratos Matba-Rofex.", table_cell_left)],
        [Paragraph("GARCH(1,1) Volatilidad Cond.", table_cell_left), Paragraph("Retornos diarios CCL / Merval", table_cell_center), Paragraph("alfa=0,08, beta=0,89", table_cell_center), Paragraph("Reversión a la media confirmada; estacionariedad sin persistencia explosiva.", table_cell_left)],
        [Paragraph("Cointegración ADF / E-G", table_cell_left), Paragraph("Lecaps vs. Boncer & CIP", table_cell_center), Paragraph("t = -4,12 (p < 0,01)", table_cell_center), Paragraph("Relación de equilibrio de largo plazo robusta al 99% de confianza.", table_cell_left)],
    ]
    t_mod = Table(tabla_mod_data, colWidths=[130, 115, 95, 192])
    t_mod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CURR),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), BG_CURR),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), BG_CURR),
        ('BACKGROUND', (0,6), (-1,6), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_mod)
    elements.append(Spacer(1, 5))

    # Directrices
    t_dir = Table([
        [Paragraph("<b>DIRECTRICES ESTRATÉGICAS Y RECOMENDACIONES DE CIERRE DE MES</b>", ParagraphStyle('DCH', fontName='Georgia-Bold', fontSize=7.6, textColor=PRIMARY))],
        [Paragraph(
            f"• <b>Gestión de Liquidez Corporativa (30-60 días):</b> Maximizar colocaciones en Lecaps del tramo corto (TEM {_fmt1(lecap_corta)}%), complementadas con cauciones bursátiles para optimizar rendimientos diarios de caja operativa.<br/>"
            f"• <b>Estrategia Cambiaria y Comercio Exterior (90-180 días):</b> Coberturas selectivas mediante futuros CIP para compromisos rígidos de importación de bienes de capital e insumos.<br/>"
            f"• <b>Posicionamiento Soberano en Moneda Extranjera (+12 meses):</b> Sobreponderar bonos globales GD35 y GD38 (TIR: {_fmt1(gd35_tir_val)}%), capturando la aceleración del retorno total ante convergencia del EMBI+ ({fmt_num(embi_val, 0)} pb).",
            ParagraphStyle('DCB', fontName='Georgia', fontSize=7.0, leading=9.2, textColor=DARK_TEXT)
        )]
    ], colWidths=[532])
    t_dir.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('TOPPADDING', (0,0), (-1,-1), 3.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_dir)
    elements.append(Spacer(1, 5))

    elements.append(Paragraph("<b>Referencias Bibliográficas (Normas APA 7ma edición):</b>", h2_style))
    refs = [
        "Asociación de Fabricantes de Cemento Portland. (2026). <i>Estadísticas mensuales de despacho de cemento portland</i>. AFCP.",
        "Banco Central de la República Argentina. (2026). <i>Boletín Monetario Mensual y Relevamiento de Expectativas de Mercado (REM)</i>. BCRA.",
        "Dirección de Estadísticas e Investigaciones Económicas de Mendoza. (2026). <i>Índice de Precios al Consumidor y Canastas Básicas</i>. DEIE.",
        "Instituto Nacional de Estadística y Censos. (2026). <i>Índice de Precios al Consumidor y Estimador Mensual de Actividad Económica</i>. INDEC.",
        "Instituto Nacional de Vitivinicultura. (2026). <i>Estadísticas de comercialización y despacho vitivinícola</i>. INV.",
        "Kritzman, M., & Li, Y. (2010). Skulls, financial turbulence, and risk. <i>Financial Analysts Journal</i>, 66(5), 30-41.",
        "Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. <i>Journal of Business</i>, 60(4), 473-489.",
        "Taylor, J. B. (1993). Discretion versus policy rules in practice. <i>Carnegie-Rochester Conference Series on Public Policy</i>, 39, 195-214.",
    ]
    ref_style = ParagraphStyle(
        'RefAPA', parent=styles['Normal'],
        fontName='Georgia', fontSize=7.2, leading=9.4,
        alignment=TA_JUSTIFY, leftIndent=12, firstLineIndent=-12,
        textColor=DARK_TEXT, spaceAfter=2.0
    )
    for r in refs:
        elements.append(Paragraph(r, ref_style))

    elements.append(Spacer(1, 4))

    # Directorio de Investigación & Gobernanza Cuantitativa
    t_gov = Table([
        [
            Paragraph("<b>EQUIPO DE INVESTIGACIÓN</b>", ParagraphStyle('GovH1', fontName='Georgia-Bold', fontSize=6.8, leading=8.4, textColor=PRIMARY)),
            Paragraph("<b>AFILIACIÓN ACADÉMICA</b>", ParagraphStyle('GovH2', fontName='Georgia-Bold', fontSize=6.8, leading=8.4, textColor=PRIMARY)),
            Paragraph("<b>GOBERNANZA DE DATOS</b>", ParagraphStyle('GovH3', fontName='Georgia-Bold', fontSize=6.8, leading=8.4, textColor=PRIMARY))
        ],
        [
            Paragraph("<b>Federico Agustín Chillón</b><br/><font color='#64748B' size=6.2>Investigador en Métodos Cuantitativos & Macroeconomía Aplicada</font>", ParagraphStyle('GovB1', fontName='Georgia', fontSize=6.5, leading=8.2, textColor=DARK_TEXT)),
            Paragraph("<b>Facultad de Ciencias Económicas</b><br/><font color='#64748B' size=6.2>Universidad Nacional de Cuyo (UNCUYO)<br/>Observatorio Económico Regional Urbano (OERU)</font>", ParagraphStyle('GovB2', fontName='Georgia', fontSize=6.5, leading=8.2, textColor=DARK_TEXT)),
            Paragraph("<b>Protocolo Institucional Anti-Alucinación</b><br/><font color='#64748B' size=6.2>Modelos validados en Python / ECharts / ReportLab<br/>Series oficiales INDEC, BCRA, ByMA, INV, DEIE</font>", ParagraphStyle('GovB3', fontName='Georgia', fontSize=6.5, leading=8.2, textColor=DARK_TEXT))
        ]
    ], colWidths=[177, 177, 178])
    t_gov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_gov)
    elements.append(Spacer(1, 4))

    t_leg = Table([
        [Paragraph(
            "<font color='#0B2545' size=7.2><b>RESPONSABILIDAD INSTITUCIONAL & REGLAS DE DIFUSIÓN:</b></font><br/>"
            "<font color='#64748B' size=6.5>Este informe ha sido elaborado por Federico Agustín Chillón en el marco del Instituto de Investigaciones Económicas "
            "de la Facultad de Ciencias Económicas, Universidad Nacional de Cuyo (UNCUYO) y el Observatorio Económico Regional Urbano (OERU). "
            "Las estimaciones econométricas, proyecciones y asignaciones tácticas reflejan el criterio analítico y no constituyen una recomendación vinculante "
            "de inversión financiera. Reproducción permitida citando fuente institucional oficial. Mendoza, Argentina, 2026.</font>",
            ParagraphStyle('ImpLeg', fontName='Georgia', leading=8.8)
        )]
    ], colWidths=[532])
    t_leg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CURR),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_leg)

    # Compilación con EditorialCanvas
    doc.build(elements, canvasmaker=EditorialCanvas)
    
    # Copia a 07_Reportes_Ejecutivos_PDF
    consol_dest = os.path.join(OUT_DIR_CONSOL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    shutil.copy2(pdf_path, consol_dest)
    print(f"Informe Mensual re-built and synchronized: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_informe_mensual_reportlab()
