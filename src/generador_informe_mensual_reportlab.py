# -*- coding: utf-8 -*-
"""
================================================================================
COMPILADOR MAESTRO DE INFORME MENSUAL REPORTLAB (15 PÁGINAS EDITORIALES)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Research (Management Solutions / Wall Street Standard)
Arquitectura: 15 Páginas Exactas / 4 Arquetipos Modulares / Cero Ruido Visual
================================================================================
"""

import os
import shutil
from datetime import datetime
import sys
import re

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
    ('SymFont', ['C:/Windows/Fonts/seguisym.ttf', 'C:/Windows/Fonts/l_10646.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']),
]
BULLET_TRIANGLE = "<font name='SymFont' color='#0284C7'><b>▸</b></font>"


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

# Colores de Bloque para Pestañas Marginales
COLOR_BLOQUE_1 = colors.HexColor("#047857")  # Bloque I: Actividad Real & Regional
COLOR_BLOQUE_2 = colors.HexColor("#0284C7")  # Bloque II: Moneda, Tasas & Deuda
COLOR_BLOQUE_3 = colors.HexColor("#9A3412")  # Bloque III: Renta Variable & Allocation
COLOR_BLOQUE_4 = colors.HexColor("#475569")  # Bloque IV: Metodología & Gobernanza

styles = getSampleStyleSheet()

# Tipografías Editoriales
title_style = ParagraphStyle(
    'SecTitle_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.0, leading=16.0,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=3, keepWithNext=True
)

leadin_style = ParagraphStyle(
    'LeadIn_M', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=8.0, leading=11.0,
    textColor=PRIMARY
)

body_bullet_style = ParagraphStyle(
    'BodyBullet_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.9, leading=11.2,
    textColor=DARK_TEXT, alignment=TA_JUSTIFY,
    leftIndent=11, firstLineIndent=-11, spaceAfter=4
)

table_title_style = ParagraphStyle(
    'TblTitle_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.4, leading=8.8,
    alignment=TA_CENTER, textColor=BLUE_INST
)

table_header_style = ParagraphStyle(
    'TH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.2, leading=8.6,
    alignment=TA_CENTER, textColor=BLUE_INST
)

table_cell_left = ParagraphStyle(
    'TCL_M', parent=styles['Normal'],
    fontName='Sans', fontSize=7.0, leading=8.4,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_bold = ParagraphStyle(
    'TCB_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.0, leading=8.4,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_subhdr = ParagraphStyle(
    'TCSH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.1, leading=8.5,
    alignment=TA_LEFT, textColor=BLUE_INST
)

table_cell_center = ParagraphStyle(
    'TCC_M', parent=styles['Normal'],
    fontName='Sans', fontSize=7.0, leading=8.4,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

table_cell_center_bold = ParagraphStyle(
    'TCCB_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=7.0, leading=8.4,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

footnote_table_style = ParagraphStyle(
    'FtnTbl_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.4, leading=7.8,
    textColor=MUTED, spaceBefore=2, spaceAfter=2
)

footnote_chart_style = ParagraphStyle(
    'FtnChart_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.4, leading=7.8,
    textColor=MUTED, spaceBefore=2, spaceAfter=0
)

h1_style = title_style
h2_style = ParagraphStyle(
    'H2_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=8.3, leading=10.8,
    textColor=PRIMARY, spaceBefore=3, spaceAfter=2, keepWithNext=True
)
body_style = ParagraphStyle(
    'Body_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=8.2, leading=11.6,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=4
)
cell_style_left = table_cell_left
cell_style_center = table_cell_center
cell_header_style = ParagraphStyle(
    'CellH_M', parent=styles['Normal'],
    fontName='Sans-Bold', fontSize=6.9, leading=8.3,
    alignment=TA_CENTER, textColor=colors.white
)

# =============================================================================
# HELPERS INSTITUCIONALES EDITORIALES: BADGES DE VARIACIÓN Y MARCOS
# =============================================================================

def _badge_var_html(val, is_pct=False, decimales=2):
    """Retorna cadena HTML institucional para formato de variaciones (+ en verde, - en rojo)."""
    if val is None:
        return "<font color='#64748B'>-</font>"
    if isinstance(val, (int, float)):
        num = float(val)
        signo = "+" if num > 0 else ""
        sufijo = "%" if is_pct else ""
        col = POS_COLOR if num > 0 else (NEG_COLOR if num < 0 else "#64748B")
        txt = f"{signo}{num:.{decimales}f}".replace(".", ",") + sufijo
        return f"<font color='{col}'><b>{txt}</b></font>"
    s = str(val).strip()
    if "<font" in s:
        s = re.sub(r'<[^>]+>', '', s).strip()
    sufijo = "%" if (is_pct and not s.endswith("%")) else ""
    if s.startswith("+"):
        return f"<font color='{POS_COLOR}'><b>{s}{sufijo}</b></font>"
    elif s.startswith("-"):
        return f"<font color='{NEG_COLOR}'><b>{s}{sufijo}</b></font>"
    elif s in ("0", "0,0", "0,00", "0,00%", "0.0", "0.00"):
        return f"<font color='#64748B'><b>{s}{sufijo}</b></font>"
    else:
        try:
            num = float(s.replace(",", ".").replace("%", ""))
            signo = "+" if num > 0 else ""
            col = POS_COLOR if num > 0 else (NEG_COLOR if num < 0 else "#64748B")
            txt = f"{signo}{num:.{decimales}f}".replace(".", ",") + sufijo
            return f"<font color='{col}'><b>{txt}</b></font>"
        except ValueError:
            return s

def _badge_var(val, is_pct=False, decimales=2):
    """Retorna un Paragraph formateado con el badge de variación institucional."""
    return Paragraph(_badge_var_html(val, is_pct=is_pct, decimales=decimales), table_cell_center)

def _wrap_chart_boxed(chart_filename, chart_footnote="", width=532, height=170):
    """Enmarca la figura institucional con un borde capilar #CBD5E1 y nota al pie."""
    flowables = []
    img_path = _find_image(chart_filename)
    if os.path.exists(img_path):
        img = Image(img_path, width=width, height=height)
        t_img = Table([[img]], colWidths=[width])
        t_img.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ]))
        flowables.append(t_img)
    if chart_footnote:
        flowables.append(Spacer(1, 2))
        flowables.append(Paragraph(chart_footnote, footnote_chart_style))
    return flowables

# =============================================================================
# CANVAS EDITORIAL CON PESTAÑAS MARGINALES (THUMB INDEX & CABECERA)
# =============================================================================

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
            p = self._pageNumber
            
            # Pestaña Marginal de Bloque:
            # Páginas 4 a 8: Bloque I: 'ACTIVIDAD REAL & REGIONAL' (#047857)
            # Páginas 9 a 13: Bloque II: 'MONEDA, TASAS & DEUDA' (#0284C7)
            # Página 14: Bloque III: 'RENTA VARIABLE & ALLOCATION' (#9A3412)
            # Página 15: Bloque IV: 'METODOLOGÍA & GOBERNANZA' (#475569)
            if 4 <= p <= 8:
                block_label = "BLOQUE I · ACTIVIDAD REAL & REGIONAL"
                block_color = COLOR_BLOQUE_1
                thumb_y = 675
            elif 9 <= p <= 13:
                block_label = "BLOQUE II · MONEDA, TASAS & DEUDA"
                block_color = COLOR_BLOQUE_2
                thumb_y = 605
            elif p == 14:
                block_label = "BLOQUE III · RENTA VARIABLE & ALLOCATION"
                block_color = COLOR_BLOQUE_3
                thumb_y = 535
            elif p == 15:
                block_label = "BLOQUE IV · METODOLOGÍA & GOBERNANZA"
                block_color = COLOR_BLOQUE_4
                thumb_y = 465
            else:
                block_label = None
                block_color = None
                thumb_y = None

            if block_label:
                # 1. Pestaña Marginal en Borde Izquierdo (Thumb Tab limpio, fuera de márgenes)
                self.setFillColor(block_color)
                self.roundRect(16, thumb_y, 4.5, 52, 2.0, fill=True, stroke=False)
                
                # 2. Etiqueta / Banda de Bloque en Cabecera
                tab_w = 172
                tab_h = 12.5
                tab_y = header_y - 2.5
                self.setFillColor(block_color)
                self.roundRect(left, tab_y, tab_w, tab_h, 2.5, fill=True, stroke=False)
                
                self.setFont("Sans-Bold", 6.2)
                self.setFillColor(colors.white)
                self.drawCentredString(left + tab_w / 2, tab_y + 3.2, block_label)
                
                # Subtítulo institucional a la derecha de la pestaña
                self.setFont("Georgia", 6.8)
                self.setFillColor(MUTED)
                self.drawString(left + tab_w + 8, header_y + 0.5, f"INFORME MENSUAL · {_INFORME_PERIODO['header']}")
                self.drawRightString(right, header_y + 0.5, "FEDERICO AGUSTÍN CHILLÓN")
            else:
                # Páginas 2 y 3 (Preliminares)
                self.setFont("Georgia", 7.2)
                self.setFillColor(MUTED)
                self.drawString(left, header_y, f"INFORME DE COYUNTURA MACROECONÓMICA & MERCADO DE CAPITALES · {_INFORME_PERIODO['header']}")
                self.drawRightString(right, header_y, "FEDERICO AGUSTÍN CHILLÓN")

            # Filete capilar bajo la cabecera
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.5)
            self.line(left, header_y - 5.5, right, header_y - 5.5)

            # Footer institucional con píldora de página
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

# =============================================================================
# ARQUETIPOS MODULARES DE MAQUETACIÓN (MANAGEMENT SOLUTIONS & WALL STREET)
# =============================================================================

def crear_pagina_arquetipo_scorecard(
    kicker_txt,
    titulo,
    leadin_txt,
    tabla_titulo,
    tabla_data,
    tabla_col_widths,
    tabla_footnote,
    bloques_tematicos,
    chart_filename,
    chart_footnote,
    chart_height=205,
    kicker_color="#047857"
):
    """
    Arquetipo A: Scorecard Comparativo de Actividad (Página 4 EMAE y Página 8 ISARC Cuyo).
    - Kicker temático superior.
    - Título y Lead-in con barra azul izquierda institucional.
    - Tabla comparativa de actividad con formato visual de variación.
    - Prosa analítica estructurada en 2-3 bloques temáticos con viñeta ▸.
    - Gráfico al pie con marco capilar institucional (#CBD5E1), altura 205 pt.
    """
    flowables = []
    
    flowables.append(Paragraph(
        f"<font color='{kicker_color}' size=7.2><b>{kicker_txt.upper()}</b></font>",
        ParagraphStyle('Kicker_SC', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    flowables.append(Paragraph(titulo, title_style))
    
    t_lead = Table([[Paragraph(leadin_txt, leadin_style)]], colWidths=[532])
    t_lead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
    ]))
    flowables.append(t_lead)
    flowables.append(Spacer(1, 4))
    
    flowables.append(Paragraph(f"<b>{tabla_titulo}</b>", table_title_style))
    flowables.append(Spacer(1, 3))
    
    tbl_pad = 2.4 if len(tabla_data) > 10 else 3.0
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
    
    for b_title, b_text in bloques_tematicos:
        p_html = f"{BULLET_TRIANGLE} <b>{b_title.upper()}:</b> {b_text}"
        flowables.append(Paragraph(p_html, body_bullet_style))
        
    flowables.append(Spacer(1, 4))
    flowables.extend(_wrap_chart_boxed(chart_filename, chart_footnote, width=532, height=chart_height))
    flowables.append(PageBreak())
    return flowables

def crear_pagina_arquetipo_desglose(
    kicker_txt,
    titulo,
    leadin_txt,
    tabla_titulo,
    tabla_data,
    tabla_col_widths,
    tabla_footnote,
    bullets_txt_list,
    chart_filename,
    chart_footnote,
    chart_height=210,
    kicker_color="#047857"
):
    """
    Arquetipo B: Desglose Multicontable (Página 5 Precios, Pág 7 Sectores Cuyo, Pág 9 BCRA, Pág 13 TCR).
    - Estilo Pág. 13 de Management Solutions: Kicker, título, lead-in itálico con filetes horizontales finos.
    - Tabla multicontable agrupada con fondos sutiles en período actual (#F1F5F9) y proyección (#EBF3FA).
    - 3 párrafos densos analíticos con viñeta institucional ▸.
    - Gráfico al pie con marco en caja, altura 210 pt.
    """
    flowables = []
    
    flowables.append(Paragraph(
        f"<font color='{kicker_color}' size=7.2><b>{kicker_txt.upper()}</b></font>",
        ParagraphStyle('Kicker_Desg', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    flowables.append(Paragraph(titulo, title_style))
    
    t_lead = Table([[Paragraph(leadin_txt, leadin_style)]], colWidths=[532])
    t_lead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('LINETOP', (0,0), (-1,0), 0.6, PRIMARY),
        ('LINEBELOW', (0,-1), (-1,-1), 0.6, PRIMARY),
    ]))
    flowables.append(t_lead)
    flowables.append(Spacer(1, 4))
    
    flowables.append(Paragraph(f"<b>{tabla_titulo}</b>", table_title_style))
    flowables.append(Spacer(1, 3))
    
    tbl_pad = 2.4 if len(tabla_data) > 10 else 2.9
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
    
    for b_lead, b_body in bullets_txt_list:
        p_html = f"{BULLET_TRIANGLE} <b>{b_lead}:</b> {b_body}"
        flowables.append(Paragraph(p_html, body_bullet_style))
        
    flowables.append(Spacer(1, 4))
    flowables.extend(_wrap_chart_boxed(chart_filename, chart_footnote, width=532, height=chart_height))
    flowables.append(PageBreak())
    return flowables

def crear_pagina_arquetipo_social(
    kicker_txt,
    titulo,
    card1_data,
    card2_data,
    tabla_titulo,
    tabla_data,
    tabla_col_widths,
    tabla_footnote,
    bullets_txt_list,
    chart_filename,
    chart_footnote,
    chart_height=210
):
    """
    Arquetipo C: Monitor Social & Canastas Básicas (Página 6 Cuadro 1).
    - Doble tarjeta destacada superior: CBA Indigencia vs CBT Pobreza con cifras de 15.0 pt.
    - Tabla de umbrales de pobreza y relación RIPTE/CBT con padding vertical holgado.
    - 3 párrafos analíticos de coyuntura social con viñeta institucional ▸.
    - Gráfico al pie con marco en caja, altura 210 pt.
    """
    flowables = []
    
    flowables.append(Paragraph(
        f"<font color='#047857' size=7.2><b>{kicker_txt.upper()}</b></font>",
        ParagraphStyle('Kicker_Soc', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    flowables.append(Paragraph(titulo, title_style))
    flowables.append(Spacer(1, 3))
    
    def _render_social_card(c):
        p_hdr = Paragraph(f"<font color='white' size=7.2><b>{c['title'].upper()}</b></font>", ParagraphStyle('CardSH', fontName='Sans-Bold', alignment=TA_CENTER, leading=9.0))
        p_vals = Paragraph(
            f"<font color='{PRIMARY.hexval()}' size=15.0><b>{c['val_nac']}</b></font>&nbsp;<font color='#64748B' size=7.5>Nac.</font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font color='{PRIMARY.hexval()}' size=15.0><b>{c['val_reg']}</b></font>&nbsp;<font color='#64748B' size=7.5>Cuyo</font>",
            ParagraphStyle('CardVals', fontName='Georgia-Bold', alignment=TA_CENTER, leading=16.0)
        )
        p_sub = Paragraph(f"<font color='#334155' size=6.8>{c['sub']}</font>", ParagraphStyle('CardSub', fontName='Georgia', alignment=TA_CENTER, leading=8.8))
        
        t_card = Table([[p_hdr], [p_vals], [p_sub]], colWidths=[258])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(c['color'])),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,0), 3.5),
            ('BOTTOMPADDING', (0,0), (-1,0), 3.5),
            ('TOPPADDING', (0,1), (-1,1), 4.5),
            ('BOTTOMPADDING', (0,1), (-1,1), 2.5),
            ('TOPPADDING', (0,2), (-1,2), 2.0),
            ('BOTTOMPADDING', (0,2), (-1,2), 4.5),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ]))
        return t_card

    t_pair_cards = Table([[_render_social_card(card1_data), "", _render_social_card(card2_data)]], colWidths=[258, 16, 258])
    t_pair_cards.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    flowables.append(t_pair_cards)
    flowables.append(Spacer(1, 4))
    
    flowables.append(Paragraph(f"<b>{tabla_titulo}</b>", table_title_style))
    flowables.append(Spacer(1, 3))
    
    t_ind = Table(tabla_data, colWidths=tabla_col_widths)
    t_ind.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.7),
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
    
    for b_lead, b_body in bullets_txt_list:
        p_html = f"{BULLET_TRIANGLE} <b>{b_lead}:</b> {b_body}"
        flowables.append(Paragraph(p_html, body_bullet_style))
        
    flowables.append(Spacer(1, 4))
    flowables.extend(_wrap_chart_boxed(chart_filename, chart_footnote, width=532, height=chart_height))
    flowables.append(PageBreak())
    return flowables

def crear_pagina_arquetipo_asimetrico(
    kicker_txt,
    titulo,
    leadin_txt,
    col_izq_titulo,
    col_izq_bullets,
    mini_tabla_titulo,
    mini_tabla_data,
    card_der_titulo,
    card_der_table_data,
    catalizador_txt,
    chart_filename,
    chart_footnote,
    chart_height=210,
    kicker_color="#0284C7"
):
    """
    Arquetipo D: Asimétrico Wall Street (Página 10 Arbitraje Tasas y Página 12 Microestructura FX).
    - Columna Izquierda (326 pt): Discusión analítica profunda + mini-tabla comparativa calibrada.
    - Columna Derecha (194 pt): Scorecard Táctico & Monitor con postura OW/N/UW y catalizadores clave.
    - Gráfico al pie de ancho completo (532 pt) con altura 210 pt.
    """
    flowables = []
    
    flowables.append(Paragraph(
        f"<font color='{kicker_color}' size=7.2><b>{kicker_txt.upper()}</b></font>",
        ParagraphStyle('Kicker_Asym', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    flowables.append(Paragraph(titulo, title_style))
    
    t_lead = Table([[Paragraph(leadin_txt, leadin_style)]], colWidths=[532])
    t_lead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
    ]))
    flowables.append(t_lead)
    flowables.append(Spacer(1, 4))
    
    # Cuerpo asimétrico
    col_izq = []
    col_izq.append(Paragraph(f"<font color='{PRIMARY.hexval()}' size=8.0><b>{col_izq_titulo.upper()}</b></font>", ParagraphStyle('AsyLT', fontName='Georgia-Bold', leading=10.0, spaceAfter=2)))
    col_izq.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=1, spaceAfter=3))
    
    for b_lead, b_body in col_izq_bullets:
        p_html = f"{BULLET_TRIANGLE} <b>{b_lead}:</b> {b_body}"
        col_izq.append(Paragraph(p_html, ParagraphStyle('AsyBL', parent=body_bullet_style, fontSize=7.8, leading=10.8, spaceAfter=3.5)))
        
    if mini_tabla_data:
        col_izq.append(Spacer(1, 2))
        col_izq.append(Paragraph(f"<b>{mini_tabla_titulo}</b>", ParagraphStyle('MTH', fontName='Sans-Bold', fontSize=7.0, leading=8.5, textColor=BLUE_INST)))
        t_mini = Table(mini_tabla_data, colWidths=[126, 100, 100])
        t_mini.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2.6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.6),
            ('LEFTPADDING', (0,0), (-1,-1), 3.5),
            ('RIGHTPADDING', (0,0), (-1,-1), 3.5),
            ('LINEBELOW', (0,1), (-1,-1), 0.3, HAIRLINE),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ]))
        col_izq.append(t_mini)
        
    col_der = []
    p_card_hdr = Paragraph(f"<font color='white' size=7.0><b>{card_der_titulo.upper()}</b></font>", ParagraphStyle('CRDH', fontName='Sans-Bold', alignment=TA_CENTER, leading=9.0))
    
    t_tact_body = Table(card_der_table_data, colWidths=[64, 46, 40, 44])
    t_tact_body.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.3, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    
    t_cat = Table([
        [Paragraph(f"<font color='{PRIMARY.hexval()}' size=6.8><b>CATALIZADORES CLAVE (30–60D)</b></font>", ParagraphStyle('CatTH', fontName='Georgia-Bold', leading=8.6))],
        [Paragraph(f"<font color='#1E293B' size=6.5>{catalizador_txt}</font>", ParagraphStyle('CatTB', fontName='Georgia', leading=9.0))]
    ], colWidths=[194])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.0, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    
    t_full_card = Table([[p_card_hdr], [t_tact_body], [t_cat]], colWidths=[194])
    t_full_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,0), 3.2),
        ('BOTTOMPADDING', (0,0), (-1,0), 3.2),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der.append(t_full_card)
    
    t_middle = Table([[col_izq, "", col_der]], colWidths=[326, 12, 194])
    t_middle.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEBEFORE', (2,0), (2,0), 0.5, HAIRLINE),
    ]))
    flowables.append(t_middle)
    flowables.append(Spacer(1, 5))
    
    flowables.extend(_wrap_chart_boxed(chart_filename, chart_footnote, width=532, height=chart_height))
    flowables.append(PageBreak())
    return flowables

def crear_pagina_arquetipo_topchart(
    kicker_txt,
    titulo,
    leadin_txt,
    chart_filename,
    chart_footnote,
    tabla_titulo,
    tabla_data,
    tabla_col_widths,
    tabla_footnote,
    caja_titulo,
    conclusiones_tacticas,
    chart_height=205,
    kicker_color="#0284C7"
):
    """
    Arquetipo E: TopChart Inversor (Página 11 Deuda Soberana y Página 14 Renta Variable).
    - RUPTURA RADICAL DE MONOTONÍA: Figura analítica principal en el tercio superior (altura 205 pt).
    - Mitad inferior: Tabla analítica de valuación con padding calibrado.
    - Caja institucional de 'Conclusiones Tácticas para el Inversor' con 3 viñetas bien explicadas.
    """
    flowables = []
    
    flowables.append(Paragraph(
        f"<font color='{kicker_color}' size=7.2><b>{kicker_txt.upper()}</b></font>",
        ParagraphStyle('Kicker_TC', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    flowables.append(Paragraph(titulo, title_style))
    
    t_lead = Table([[Paragraph(leadin_txt, leadin_style)]], colWidths=[532])
    t_lead.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 3.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.0),
        ('LINETOP', (0,0), (-1,0), 0.5, BORDER),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, BORDER),
    ]))
    flowables.append(t_lead)
    flowables.append(Spacer(1, 4))
    
    # 1. FIGURA EN TERCIO SUPERIOR
    flowables.extend(_wrap_chart_boxed(chart_filename, chart_footnote, width=532, height=chart_height))
    flowables.append(Spacer(1, 4))
    
    # 2. TABLA EN MITAD INFERIOR
    flowables.append(Paragraph(f"<b>{tabla_titulo}</b>", table_title_style))
    flowables.append(Spacer(1, 3))
    
    tbl_pad = 2.6 if len(tabla_data) > 9 else 3.0
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
    
    # 3. CAJA DE CONCLUSIONES TÁCTICAS
    caja_content = []
    caja_content.append(Paragraph(f"<font color='{PRIMARY.hexval()}' size=7.2><b>{caja_titulo.upper()}</b></font>", ParagraphStyle('CTH', fontName='Georgia-Bold', leading=9.0)))
    for c_lead, c_body in conclusiones_tacticas:
        p_html = f"{BULLET_TRIANGLE} <b>{c_lead}:</b> {c_body}"
        caja_content.append(Paragraph(p_html, ParagraphStyle('CTB', parent=body_bullet_style, fontSize=7.6, leading=10.6, spaceAfter=2.5)))
        
    t_caja = Table([[caja_content]], colWidths=[532])
    t_caja.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    flowables.append(t_caja)
    
    flowables.append(PageBreak())
    return flowables

# Compatibilidad hacia atrás si es invocado por otros módulos
def crear_pagina_editorial_ms(
    titulo, leadin_txt, tabla_titulo, tabla_data, tabla_col_widths, tabla_footnote,
    bullets_txt_list, chart_filename, chart_footnote, chart_height=180, chart_width=532
):
    return crear_pagina_arquetipo_desglose(
        kicker_txt="RESEARCH INSTITUCIONAL · COYUNTURA",
        titulo=titulo,
        leadin_txt=leadin_txt,
        tabla_titulo=tabla_titulo,
        tabla_data=tabla_data,
        tabla_col_widths=tabla_col_widths,
        tabla_footnote=tabla_footnote,
        bullets_txt_list=bullets_txt_list,
        chart_filename=chart_filename,
        chart_footnote=chart_footnote,
        chart_height=chart_height
    )

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
    # PÁGINA 1: PORTADA DE GALA INSTITUCIONAL (CARÁTULA MONUMENTAL)
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

    # a) MÁSTIL SUPERIOR FORMAL CON DOBLE FILETE INSTITUCIONAL
    elements.append(HRFlowable(width="100%", thickness=2.2, color=PRIMARY, spaceBefore=0, spaceAfter=1.5))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D97706"), spaceBefore=0, spaceAfter=4))

    masthead_cov = Table([
        [
            Paragraph("<font color='#0B2545' size=9.2><b>UNIVERSIDAD NACIONAL DE CUYO</b> · FCE · OERU</font><br/><font color='#64748B' size=7.0>OBSERVATORIO ECONÓMICO REGIONAL URBANO · INSTITUTO DE INVESTIGACIONES ECONÓMICAS</font>", ParagraphStyle('MHC_L', fontName='Georgia', alignment=TA_LEFT, leading=10.2)),
            Paragraph("<font color='#0B2545' size=9.2><b>DIVISIÓN DE ECONOMÍA APLICADA & ESTRATEGIA</b></font><br/><font color='#64748B' size=7.0>MACROECONOMIC RESEARCH & ASSET ALLOCATION · VOL. IV</font>", ParagraphStyle('MHC_R', fontName='Georgia', alignment=TA_RIGHT, leading=10.2))
        ]
    ], colWidths=[320, 212])
    masthead_cov.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(masthead_cov)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=3, spaceAfter=6))

    # b) CÁPSULA KICKER INSTITUCIONAL
    t_kicker = Table([[
        Paragraph(
            f"<font color='white' size=7.0><b>ESTRATEGIA MACROECONÓMICA & ASSET ALLOCATION · CIERRE MENSUAL · {periodo_header.upper()} · VOL. IV</b></font>",
            ParagraphStyle('KickerCovP', fontName='Sans-Bold', alignment=TA_CENTER, leading=8.8)
        )
    ]], colWidths=[532])
    t_kicker.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_kicker)
    elements.append(Spacer(1, 5))

    # c) TÍTULO MONUMENTAL & SUBTÍTULO
    elements.append(Paragraph(
        "INFORME DE COYUNTURA MACROECONÓMICA",
        ParagraphStyle('MonumentalTitle', fontName='Georgia-Bold', fontSize=21.5, leading=25.0, textColor=PRIMARY, spaceAfter=4)
    ))
    elements.append(Paragraph(
        f"Desinflación Núcleo al {_fmt1(ipc_core)}%, Ancla Fiscal en Base Caja, Extinción de Pasivos Cuasifiscales y Normalización de Curvas Soberanas",
        ParagraphStyle('MonumentalSub', fontName='Georgia-Italic', fontSize=9.8, leading=13.5, textColor=colors.HexColor("#334155"), spaceAfter=6)
    ))

    # d) HERO CENTERPIECE VISUAL (cover_macro_hero.png a 285 pt de altura para ratio nativo 16:9)
    hero_path = _find_image("cover_macro_hero.png")
    if os.path.exists(hero_path):
        img_hero = Image(hero_path, width=532, height=280)
        t_hero = Table([
            [img_hero],
            [Paragraph("<font color='#64748B' size=6.5>Topología de flujos macrofinancieros, calibración de curvas soberanas y convergencia de equilibrios · FCE UNCUYO</font>", ParagraphStyle('HeroEpig', fontName='Georgia', alignment=TA_CENTER, leading=8.4))]
        ], colWidths=[532])
        t_hero.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,1), (-1,1), 2.8),
            ('BOTTOMPADDING', (0,1), (-1,1), 2.8),
            ('BOX', (0,0), (0,0), 0.6, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(t_hero)
    elements.append(Spacer(1, 6))

    # e) EXECUTIVE KPI DASHBOARD RIBBON (5 Tarjetas Horizontales con cifras grandes de 13.5 pt)
    def _render_kpi_card(top_color, title_kpi, val_kpi, sub_kpi):
        p_top = Table([[""]], colWidths=[102.4], rowHeights=[2.5])
        p_top.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(top_color)),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        p_tit = Paragraph(f"<font color='#475569' size=6.2><b>{title_kpi.upper()}</b></font>", ParagraphStyle('KPITit', fontName='Sans-Bold', alignment=TA_CENTER, leading=7.6))
        p_val = Paragraph(f"<font color='{PRIMARY.hexval()}' size=13.5><b>{val_kpi}</b></font>", ParagraphStyle('KPIVal', fontName='Georgia-Bold', alignment=TA_CENTER, leading=15.0))
        p_sub = Paragraph(f"<font color='#64748B' size=6.2>{sub_kpi}</font>", ParagraphStyle('KPISub', fontName='Georgia', alignment=TA_CENTER, leading=7.6))
        
        t_card = Table([[p_top], [p_tit], [p_val], [p_sub]], colWidths=[102.4])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,0), 0),
            ('BOTTOMPADDING', (0,0), (-1,0), 0),
            ('TOPPADDING', (0,1), (-1,1), 3.0),
            ('BOTTOMPADDING', (0,1), (-1,1), 1.5),
            ('TOPPADDING', (0,2), (-1,2), 1.5),
            ('BOTTOMPADDING', (0,2), (-1,2), 2.0),
            ('TOPPADDING', (0,3), (-1,3), 1.5),
            ('BOTTOMPADDING', (0,3), (-1,3), 4.0),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        return t_card

    card_kpi1 = _render_kpi_card("#0284C7", "Inflación Núcleo", f"{_fmt1(ipc_core)}% m/m", "Mínimo 6 trimestres")
    card_kpi2 = _render_kpi_card("#0B2545", "Lecap Corta", f"{_fmt1(lecap_corta)}% TEM", f"Tasa real: +{_fmt1(tasa_real_exante_val)}%")
    card_kpi3 = _render_kpi_card("#059669", "Dólar CCL", f"${fmt_num(ccl_val, 0)} / {_fmt1(brecha_val)}%", "Ancla cambiaria 2%")
    card_kpi4 = _render_kpi_card("#D97706", "EMBI+ Soberano", f"{fmt_num(embi_val, 0)} pb", "Compresión -174 pb")
    card_kpi5 = _render_kpi_card("#047857", "Actividad EMAE", f"+{_fmt1(emae_ia_val)}% i.a.", "Tracción energía")

    t_kpi_row = Table([[card_kpi1, card_kpi2, card_kpi3, card_kpi4, card_kpi5]], colWidths=[106.4, 106.4, 106.4, 106.4, 106.4])
    t_kpi_row.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_kpi_row)
    elements.append(Spacer(1, 6))

    # f) PIE DE AUTORÍA & IMPRINT INSTITUCIONAL
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=2, spaceAfter=4))
    t_imp_cover = Table([
        [
            Paragraph(
                "<font color='#0B2545' size=7.8><b>FEDERICO AGUSTÍN CHILLÓN</b></font> · <font color='#475569' size=7.0>Investigador & Estratega Macrofinanciero</font><br/>"
                "<font color='#64748B' size=6.5>Facultad de Ciencias Económicas · Universidad Nacional de Cuyo (UNCUYO) · OERU<br/>"
                "federico.chillon@fce.uncuyo.edu.ar · Mendoza, República Argentina</font>",
                ParagraphStyle('CovImpL', fontName='Georgia', leading=8.8)
            ),
            Paragraph(
                "<font color='#0B2545' size=7.4><b>RESEARCH INSTITUCIONAL & ASSET ALLOCATION</b></font><br/>"
                "<font color='#64748B' size=6.5>Modelos Nelson-Siegel, Taylor Rule & Simulación de Riesgo<br/>"
                "Consenso REM BCRA · INDEC · DEIE · ByMA · Matba-Rofex</font>",
                ParagraphStyle('CovImpR', fontName='Georgia', alignment=TA_RIGHT, leading=8.8)
            )
        ]
    ], colWidths=[330, 202])
    t_imp_cover.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_imp_cover)
    elements.append(HRFlowable(width="100%", thickness=3.2, color=PRIMARY, spaceBefore=4, spaceAfter=1))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D97706"), spaceBefore=0, spaceAfter=0))
    elements.append(PageBreak())

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
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Jerarquía por Importancia Relativa:</b> Priorización de componentes macroeconómicos determinantes (precios regulados sobre estacionales, transables sobre no transables, y deuda soberana sobre derivados).<br/>"
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Fuentes Primarias Consolidadas:</b> Series provistas por INDEC, DEIE Mendoza, Banco Central de la República Argentina (BCRA), Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía y ByMA.<br/>"
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Modelos Econométricos Aplicados:</b> Calibración paramétrica de Nelson-Siegel (1987) para curvas de deuda en USD, regla de Taylor con tasa real ex-ante (1993), paridad de tasas cubierta (CIP) y descomposición factorial multivariada (PCA Absorption Ratio y Turbulencia de Mahalanobis).",
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
    # PÁGINA 3: WALL STREET STRATEGY TEAR-SHEET (DIAGNÓSTICO EJECUTIVO, ASIGNACIÓN TÁCTICA Y ESCENARIOS)
    # =========================================================================
    elements.append(Paragraph(
        f"<font color='#0284C7' size=7.2><b>RESEARCH INSTITUCIONAL · WALL STREET STRATEGY TEAR-SHEET</b></font>",
        ParagraphStyle('Kicker_P3', parent=styles['Normal'], fontName='Georgia-Bold', leading=9.0, spaceAfter=2)
    ))
    elements.append(Paragraph("Resumen Ejecutivo: Diagnóstico Macroeconómico, Asignación Táctica y Escenarios", title_style))
    
    t_lead_p3 = Table([[Paragraph(
        "Evaluación del régimen de absorción monetaria, ancla fiscal en base caja, dinámica de precios relativos INDEC/DEIE, "
        f"compresión del riesgo país a {fmt_num(embi_val, 0)} pb y directrices tácticas de asignación multiactivo.",
        leadin_style
    )]], colWidths=[532])
    t_lead_p3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.0),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
    ]))
    elements.append(t_lead_p3)
    elements.append(Spacer(1, 4))

    # Columna Izquierda (330 pt)
    col_izq_p3 = []
    col_izq_p3.append(Paragraph("<font color='#0B2545' size=8.4><b>DIAGNÓSTICO EJECUTIVO & ANCLA MACROECONÓMICA</b></font>", ParagraphStyle('SecL3', fontName='Georgia', leading=10.5)))
    col_izq_p3.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=5))

    p1_cov = (
        f"El proceso de estabilización macroeconómica consolida su sendero de desinflación con el registro del IPC general "
        f"en <b>{_fmt1(ipc_gral)}% m/m</b> y una desaceleración del componente núcleo al <b>{_fmt1(ipc_core)}% m/m</b> (con la medición regional DEIE Mendoza "
        f"situándose en <b>{_fmt1(deie)}%</b>). La convergencia nominal responde a la persistencia del ancla fiscal en base caja —sin emisión monetaria directa al Tesoro— "
        f"y al sostenimiento de rendimientos reales ex-ante positivos en la curva en pesos: la Lecap corta opera en una <b>TEM de {_fmt1(lecap_corta)}%</b> frente a una "
        f"expectativa de inflación REM del {_fmt1(rem)}%, garantizando una tasa real contractual de <b>+{_fmt1(tasa_real_exante_val)}% mensual</b>. Este diferencial comprime "
        f"la brecha del CCL al <b>{_fmt1(brecha_val)}%</b> sobre el tipo de cambio oficial mayorista (${fmt_num(ccl_val, 2)}), desarticulando expectativas de salto cambiario."
    )
    col_izq_p3.append(Paragraph(p1_cov, ParagraphStyle('CovBL1', fontName='Georgia', fontSize=8.0, leading=11.2, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=5)))

    p2_cov = (
        f"En el frente monetario, la ejecución de la segunda etapa del programa económico ha consolidado la extinción de los pasivos remunerados del Banco Central "
        f"(migración de pases y LeFis hacia Letras del Tesoro), clausurando la emisión cuasifiscal endógena y guiando la tasa hacia el nivel neutral real (r*). "
        f"En simultáneo, la economía real refleja una reactivación cíclica con el EMAE expandiéndose <b>+{_fmt1(emae_ia_val)}% i.a.</b> (<b>+{_fmt1(emae_mom_val)}% m/m</b> desestacionalizado), "
        f"traccionada por la región Cuyo (Mendoza <b>+{_fmt1(isarc_mdz_val)}%</b>, San Luis <b>+{_fmt1(isarc_sl_val)}%</b>). En deuda soberana, el riesgo país EMBI+ "
        f"comprime a <b>{fmt_num(embi_val, 0)} pb</b> con una tasa asintótica Nelson-Siegel de <b>{_fmt1(beta0_val)}%</b> y el GD35 rindiendo <b>{_fmt1(gd35_tir_val)}% TIR</b>."
    )
    col_izq_p3.append(Paragraph(p2_cov, ParagraphStyle('CovBL2', fontName='Georgia', fontSize=8.0, leading=11.2, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=5)))

    p3_cov = (
        f"En el sector externo y cambiario, las reservas brutas del BCRA alcanzan los <b>${fmt_num(tasas_bcra.get('reservas_brutas_usd_m', {}).get('valor', 50660), 0)} M USD</b>, "
        f"con recomposición de reservas netas y reversión del déficit cuasifiscal. Las liquidaciones de la balanza comercial energética y agroindustrial sostienen "
        f"la oferta en el segmento financiero bajo el esquema blend 80/20, mientras el programa de rollover del Tesoro supera el 110% de cobertura sobre vencimientos "
        f"en moneda local, extendiendo los plazos de colocación hacia 2027 sin fricciones de liquidez."
    )
    col_izq_p3.append(Paragraph(p3_cov, ParagraphStyle('CovBL3', fontName='Georgia', fontSize=8.0, leading=11.2, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=5)))

    # Bloque de catalizadores
    t_cat = Table([
        [Paragraph("<font color='#0B2545' size=7.2><b>CATALIZADORES & FACTORES DE RIESGO TÁCTICO (30–60 DÍAS)</b></font>", ParagraphStyle('CatT', fontName='Georgia-Bold', leading=9.0))],
        [Paragraph(
            "<font color='#1E293B' size=6.5>"
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Transición Cambiaria & Reservas:</b> Sostenibilidad de la acumulación de divisas y calibración del crawling peg.<br/>"
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Roll-over de Deuda en Pesos:</b> Capacidad del Tesoro para refinanciar más del 100% en Lecaps sin convalidar tasas elevadas.<br/>"
            "<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Compresión Soberana:</b> Ruptura del piso de 500 pb en EMBI+ como condición para retornar al crédito internacional."
            "</font>",
            ParagraphStyle('CatB', fontName='Georgia', leading=8.8)
        )]
    ], colWidths=[324])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CURR),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    col_izq_p3.append(t_cat)
    col_izq_p3.append(Spacer(1, 5))

    # Matriz de escenarios en P3
    t_esc_cov = Table([
        [
            Paragraph("<b>Escenario Macro (30–90d)</b>", ParagraphStyle('EH1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)),
            Paragraph("<b>Prob.</b>", ParagraphStyle('EH2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Directriz de Asignación Sugerida</b>", ParagraphStyle('EH3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white))
        ],
        [Paragraph("<b>Base (Convergencia)</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=PRIMARY)), Paragraph("<b>65%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor(POS_COLOR))), Paragraph("Ancla fiscal y monetaria firme; sostener Lecaps cortas y acumular GD35.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
        [Paragraph("<b>Shock Tarifario / Brecha</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.HexColor("#B45309"))), Paragraph("<b>25%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor("#B45309"))), Paragraph("Rebote de regulados; rotar 15% hacia Boncer TZX26/TZX27.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
        [Paragraph("<b>Estrés Externo / Salida</b>", ParagraphStyle('EB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.HexColor(NEG_COLOR))), Paragraph("<b>10%</b>", ParagraphStyle('EB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor(NEG_COLOR))), Paragraph("Volatilidad global; cobertura en Bopreal y acortar duration.", ParagraphStyle('EB3', fontName='Georgia', fontSize=6.2, leading=7.8, textColor=DARK_TEXT))],
    ], colWidths=[88, 30, 206])
    t_esc_cov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_izq_p3.append(t_esc_cov)

    # Columna Derecha (192 pt)
    col_der_p3 = []
    col_der_p3.append(Paragraph("<font color='#0B2545' size=8.2><b>ASIGNACIÓN TÁCTICA DE ACTIVOS</b></font>", ParagraphStyle('SecR1', fontName='Georgia', leading=10.2)))
    col_der_p3.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    t_tact = Table([
        [
            Paragraph("<b>Activo</b>", ParagraphStyle('TH1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)),
            Paragraph("<b>Postura</b>", ParagraphStyle('TH2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Peso</b>", ParagraphStyle('TH3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Target</b>", ParagraphStyle('TH4', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))
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
        ('TOPPADDING', (0,0), (-1,-1), 3.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.0),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der_p3.append(t_tact)
    col_der_p3.append(Spacer(1, 5))

    col_der_p3.append(Paragraph("<font color='#0B2545' size=8.2><b>MACRO & MARKET SCORECARD</b></font>", ParagraphStyle('SecR2', fontName='Georgia', leading=10.2)))
    col_der_p3.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    t_sc = Table([
        [Paragraph("<b>Métrica Clave</b>", ParagraphStyle('SH1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)), Paragraph("<b>Nivel Observado</b>", ParagraphStyle('SH2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("IPC General / Núcleo", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(ipc_gral)}% / {_fmt1(ipc_core)}% m/m", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Lecap Corta (TEM)", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(lecap_corta)}% (Real: +{_fmt1(tasa_real_exante_val)}%)", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=colors.HexColor(POS_COLOR)))],
        [Paragraph("Dólar CCL / Brecha", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"${fmt_num(ccl_val, 2)} / {_fmt1(brecha_val)}%", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("EMBI+ Riesgo País", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{fmt_num(embi_val, 0)} pb (-174 pb)", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=PRIMARY))],
        [Paragraph("Curva N-S (Beta 0)", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(beta0_val)}%", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Actividad EMAE", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{_fmt1(emae_ia_val, signo=True)}% i.a.", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Régimen Sistémico", ParagraphStyle('SD1', fontName='Georgia', fontSize=6.4, leading=7.8, textColor=DARK_TEXT)), Paragraph(f"{_regimen_txt} (Turb {_turb_txt})", ParagraphStyle('SD2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, alignment=TA_RIGHT, textColor=colors.HexColor(POS_COLOR)))],
    ], colWidths=[100, 92])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der_p3.append(t_sc)
    col_der_p3.append(Spacer(1, 5))

    t_cal_cov = Table([
        [Paragraph("<b>Hito Financiero (30d)</b>", ParagraphStyle('CL1', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, textColor=colors.white)), Paragraph("<b>Estrategia</b>", ParagraphStyle('CL2', fontName='Georgia-Bold', fontSize=6.4, leading=7.8, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("Licitación Tesoro", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.6, textColor=DARK_TEXT)), Paragraph("Rollover &ge; 100% en Lecaps", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.6, alignment=TA_RIGHT, textColor=PRIMARY))],
        [Paragraph("Publicación IPC INDEC", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.6, textColor=DARK_TEXT)), Paragraph("Ancla núcleo &le; 2,0%", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.6, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Vencimiento CIP / Rofex", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.6, textColor=DARK_TEXT)), Paragraph("Arbitraje blend 80/20", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.6, alignment=TA_RIGHT, textColor=DARK_TEXT))],
        [Paragraph("Directorio BCRA", ParagraphStyle('CD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.6, textColor=DARK_TEXT)), Paragraph("Tasa neutral r*", ParagraphStyle('CD2', fontName='Georgia', fontSize=6.1, leading=7.6, alignment=TA_RIGHT, textColor=PRIMARY))],
    ], colWidths=[108, 84])
    t_cal_cov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    col_der_p3.append(t_cal_cov)

    t_main_p3 = Table([[col_izq_p3, "", col_der_p3]], colWidths=[330, 10, 192])
    t_main_p3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEBEFORE', (2,0), (2,0), 0.5, HAIRLINE),
    ]))
    elements.append(t_main_p3)
    elements.append(Spacer(1, 6))

    # Pull-quote institucional a ancho completo
    p_cita = Paragraph("<i>«El trípode de superávit primario irrestricto, tasa de interés real positiva y saneamiento patrimonial del Banco Central convalida la mayor compresión de primas de riesgo soberano de la última década, transformando el arbitraje financiero y consolidando la normalización de curvas de rendimiento.»</i>", ParagraphStyle('PQuoteP3', fontName='Georgia-Italic', fontSize=7.8, leading=10.5, alignment=TA_JUSTIFY, textColor=PRIMARY))
    p_aut = Paragraph("<b>— Comité de Estrategia Macroeconómica & Asset Allocation · FCE UNCUYO · OERU</b>", ParagraphStyle('PQuoteAutP3', fontName='Sans-Bold', fontSize=6.8, leading=8.4, alignment=TA_RIGHT, textColor=MUTED))
    t_pq = Table([[p_cita], [p_aut]], colWidths=[532])
    t_pq.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_pq)
    elements.append(Spacer(1, 5))

    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=3))
    t_imp_p3 = Table([
        [
            Paragraph("<font color='#0B2545' size=7.0><b>ESTRATEGIA MACROECONÓMICA & ASSET ALLOCATION</b> · FCE UNCUYO · OERU</font>", ParagraphStyle('IL3', fontName='Georgia', leading=8.4)),
            Paragraph("<font color='#64748B' size=6.5>Resumen Ejecutivo · Modelos Nelson-Siegel & CIP Rofex</font>", ParagraphStyle('IR3', fontName='Georgia', alignment=TA_RIGHT, leading=8.4))
        ]
    ], colWidths=[370, 162])
    t_imp_p3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_imp_p3)
    elements.append(PageBreak())

    # PÁGINA 4: 1. NIVEL DE ACTIVIDAD GENERAL (EMAE) — ARQUETIPO SCORECARD
    # =========================================================================
    p4_lead = (
        "El crecimiento económico de Argentina consolidó su sendero de recuperación positiva en el segundo trimestre de 2026 (+3,1% i.a.), "
        "apoyado en la expansión récord de hidrocarburos no convencionales en Vaca Muerta y minería cuyana, junto a la normalización del crédito "
        "comercial bancario. La industria y la construcción moderaron su ritmo de contracción, sentando las bases para una convergencia cíclica equilibrada."
    )
    p4_tabla_data = [
        [Paragraph("<b>ACTIVIDAD / SECTOR</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>PIB REAL Y DEMANDA AGREGADA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>EMAE / PIB Total (% i.a.)</b>", table_cell_bold), Paragraph("1,20", table_cell_center_bold), Paragraph("1,80", table_cell_center_bold), Paragraph("2,40", table_cell_center_bold), Paragraph("2,80", table_cell_center_bold), Paragraph("3,10", table_cell_center_bold), _badge_var("+0,30"), _badge_var("+1,90"), Paragraph("3,50", table_cell_center_bold), Paragraph("4,20", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Consumo Privado Hogares", table_cell_left), Paragraph("-1,80", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("2,70", table_cell_center), _badge_var("+0,30"), _badge_var("+4,50"), Paragraph("3,10", table_cell_center), Paragraph("3,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Consumo Público Nacional", table_cell_left), Paragraph("-8,40", table_cell_center), Paragraph("-5,20", table_cell_center), Paragraph("-3,10", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("-0,90", table_cell_center), _badge_var("+0,60"), _badge_var("+7,50"), Paragraph("-0,50", table_cell_center), Paragraph("0,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Formación Bruta Capital Fijo", table_cell_left), Paragraph("-12,50", table_cell_center), Paragraph("-6,80", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("5,80", table_cell_center), Paragraph("6,40", table_cell_center), _badge_var("+0,60"), _badge_var("+18,90"), Paragraph("7,20", table_cell_center), Paragraph("8,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Reales de Bienes", table_cell_left), Paragraph("6,20", table_cell_center), Paragraph("8,40", table_cell_center), Paragraph("9,50", table_cell_center), Paragraph("10,20", table_cell_center), Paragraph("11,40", table_cell_center), _badge_var("+1,20"), _badge_var("+5,20"), Paragraph("10,80", table_cell_center), Paragraph("7,50", table_cell_center)],
        [Paragraph("<b>TRACCIÓN SECTORIAL PRIMARIA & INDUSTRIAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Minería, Petróleo & Gas", table_cell_left), Paragraph("6,50", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("8,10", table_cell_center), Paragraph("8,40", table_cell_center), Paragraph("8,50", table_cell_center), _badge_var("+0,10"), _badge_var("+2,00"), Paragraph("9,20", table_cell_center), Paragraph("11,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Sector Agropecuario", table_cell_left), Paragraph("8,40", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("13,40", table_cell_center), Paragraph("14,20", table_cell_center), _badge_var("+0,80"), _badge_var("+5,80"), Paragraph("12,50", table_cell_center), Paragraph("6,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Comercio Mayorista / Minorista", table_cell_left), Paragraph("-3,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("0,40", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,80", table_cell_center), _badge_var("+1,00"), _badge_var("+6,00"), Paragraph("3,20", table_cell_center), Paragraph("4,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Industria Manufacturera", table_cell_left), Paragraph("-7,80", table_cell_center), Paragraph("-5,20", table_cell_center), Paragraph("-3,40", table_cell_center), Paragraph("-2,10", table_cell_center), Paragraph("-1,80", table_cell_center), _badge_var("+0,30"), _badge_var("+6,00"), Paragraph("0,50", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Construcción & Cemento", table_cell_left), Paragraph("-14,20", table_cell_center), Paragraph("-10,50", table_cell_center), Paragraph("-7,20", table_cell_center), Paragraph("-5,10", table_cell_center), Paragraph("-4,20", table_cell_center), _badge_var("+0,90"), _badge_var("+10,00"), Paragraph("-1,00", table_cell_center), Paragraph("5,00", table_cell_center)],
    ]
    p4_bloques = [
        ("Tracción Sectorial & Heterogeneidad Productiva",
         "El Estimador Mensual de Actividad Económica (EMAE) registró una expansión interanual del +3,1%, acumulando siete meses consecutivos de variación positiva en la serie desestacionalizada (+0,4% m/m, alcanzando 153,4 puntos base 2004=100). La recuperación presenta una asimetría liderada por los sectores transables e intensivos en capital: la extracción de hidrocarburos (+8,5% i.a.) y la producción agropecuaria (+14,2% i.a.) operan como los motores centrales, compensando la transición en la industria manufacturera (-1,8% i.a.) y la construcción (-4,2% i.a.), las cuales moderan sustancialmente su ritmo de caída frente al piso de 2024."),
        ("Perspectivas Cíclicas & Proyecciones RIGI",
         "Las perspectivas para el segundo semestre de 2026 y 2027 anticipan una consolidación del crecimiento hacia el +3,5% y +4,2% anual, sustentadas en la maduración de proyectos mineros y energéticos enmarcados en el Régimen de Incentivo para Grandes Inversiones (RIGI) y la ampliación de capacidad de transporte en Vaca Muerta (oleoducto VM Sur y reversión del Gasoducto Norte). La estabilidad de la brecha cambiaria en torno al 4,5% y la recuperación del crédito comercial (+14,5% real i.a.) convalidan la inversión fija.")
    ]
    elements.extend(crear_pagina_arquetipo_scorecard(
        kicker_txt="ACTIVIDAD REAL & SECTORIAL · ESTIMADOR MENSUAL DE ACTIVIDAD ECONÓMICA",
        titulo="1. Estimador Mensual de Actividad Económica (EMAE)",
        leadin_txt=p4_lead,
        tabla_titulo="Principales indicadores de actividad económica agregada y sectorial (%)",
        tabla_data=p4_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos trimestrales y mensuales basados en series desestacionalizadas del INDEC. Variaciones interanuales y proyecciones basadas en modelo macroeconométrico FCE UNCUYO y consenso REM BCRA.",
        bloques_tematicos=p4_bloques,
        chart_filename="chart_editorial_emae.png",
        chart_footnote="Nota: Estimador Mensual de Actividad Económica (base 2004=100) provisto por INDEC. Tracción sectorial estimada por la FCE UNCUYO.",
        chart_height=205,
        kicker_color="#047857"
    ))

    # =========================================================================
    # PÁGINA 5: 2. PRECIOS Y SALARIOS (INDEC) — ARQUETIPO DESGLOSE
    # =========================================================================
    p5_lead = (
        "La inflación de Argentina profundizó su sendero de desaceleración en el segundo trimestre de 2026 (IPC general en 2,2% m/m y núcleo en 1,9% m/m), "
        "convalidando el ancla cambiaria del 2% y la disciplina fiscal en base caja. En Mendoza, el IPC DEIE convergió al 2,3% m/m, mientras que los salarios "
        "formales (RIPTE) comenzaron a recomponer poder adquisitivo en términos reales frente a la canasta básica alimentaria."
    )
    p5_tabla_data = [
        [Paragraph("<b>INDICADOR DE PRECIOS & INGRESOS</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>NIVEL GENERAL & APERTURAS INDEC</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>IPC General Nacional (% m/m)</b>", table_cell_bold), Paragraph("3,80", table_cell_center_bold), Paragraph("3,20", table_cell_center_bold), Paragraph("2,60", table_cell_center_bold), Paragraph("2,40", table_cell_center_bold), Paragraph("2,20", table_cell_center_bold), _badge_var("-0,20"), _badge_var("-1,60"), Paragraph("29,50", table_cell_center_bold), Paragraph("15,80", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;IPC Núcleo (Core Inflation)", table_cell_left), Paragraph("3,40", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("1,90", table_cell_center), _badge_var("-0,10"), _badge_var("-1,50"), Paragraph("24,80", table_cell_center), Paragraph("12,40", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Precios Regulados (Tarifas)", table_cell_left), Paragraph("5,20", table_cell_center), Paragraph("4,50", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("3,00", table_cell_center), _badge_var("-0,40"), _badge_var("-2,20"), Paragraph("38,20", table_cell_center), Paragraph("18,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Precios Estacionales", table_cell_left), Paragraph("2,90", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("1,60", table_cell_center), Paragraph("1,40", table_cell_center), _badge_var("-0,20"), _badge_var("-1,50"), Paragraph("20,50", table_cell_center), Paragraph("14,00", table_cell_center)],
        [Paragraph("<b>MEDICIÓN REGIONAL & SALARIOS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;IPC DEIE Mendoza (% m/m)", table_cell_left), Paragraph("3,90", table_cell_center), Paragraph("3,30", table_cell_center), Paragraph("2,70", table_cell_center), Paragraph("2,50", table_cell_center), Paragraph("2,30", table_cell_center), _badge_var("-0,20"), _badge_var("-1,60"), Paragraph("30,20", table_cell_center), Paragraph("16,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Salario Formal RIPTE (% i.a. nom.)", table_cell_left), Paragraph("145,2", table_cell_center), Paragraph("112,4", table_cell_center), Paragraph("85,2", table_cell_center), Paragraph("62,4", table_cell_center), Paragraph("48,5", table_cell_center), _badge_var("-13,9"), _badge_var("-96,7"), Paragraph("34,20", table_cell_center), Paragraph("18,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Variación Salario Real (% trim.)", table_cell_left), Paragraph("-4,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("0,80", table_cell_center), Paragraph("1,40", table_cell_center), Paragraph("1,80", table_cell_center), _badge_var("+0,40"), _badge_var("+6,00"), Paragraph("2,80", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa Real Ex-Ante Contractual", table_cell_left), Paragraph("0,25", table_cell_center), Paragraph("0,45", table_cell_center), Paragraph("0,65", table_cell_center), Paragraph("0,85", table_cell_center), Paragraph("0,95", table_cell_center), _badge_var("+0,10"), _badge_var("+0,70"), Paragraph("1,05", table_cell_center), Paragraph("0,80", table_cell_center)],
    ]
    p5_bullets = [
        ("La dinámica de precios confirmó la consolidación del sendero desinflacionario nacional (2,2% m/m)",
         "y provincial (Mendoza: 2,3% m/m), quebrando la inercia histórica de tres dígitos anuales. Por orden de incidencia relativa, los aumentos estuvieron encabezados por precios regulados (3,0% m/m) y servicios públicos, derivados de la actualización de cuadros tarifarios de gas y energía eléctrica en búsqueda del equilibrio de subsidios, mientras que los transables operaron alineados a la pauta cambiaria."),
        ("La inflación núcleo se ubicó en 1,9% m/m, marcando el nivel más bajo en seis trimestres",
         "Este registro confirma que las presiones no provienen de desequilibrios monetarios primarios ni de una espiralización de costos, sino de ajustes puntuales de precios relativos. La tasa de interés real en pesos (Lecaps en 2,95% TEM frente a expectativas REM de 2,00%) proporciona un dique de contención que esteriliza saldos transaccionales y consolida la convergencia hacia el crawling peg del 2%."),
        ("En el plano salarial, el RIPTE verificó ganancias reales marginales por tercer trimestre consecutivo",
         "El salario formal privado acumula tres trimestres de recomposición en capacidad de compra de alimentos básicos. No obstante, el sector informal continúa rezagado, evidenciando una heterogeneidad distributiva que mantiene tensiones en los segmentos de ingresos bajos frente al costo de la Canasta Básica Total.")
    ]
    elements.extend(crear_pagina_arquetipo_desglose(
        kicker_txt="PRECIOS & SALARIOS · TRAYECTORIA DESINFLACIONARIA Y SALARIO REAL",
        titulo="2. Precios, Canastas Básicas y Salario Real",
        leadin_txt=p5_lead,
        tabla_titulo="Evolución del Índice de Precios al Consumidor y variables laborales (%)",
        tabla_data=p5_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos provistos por INDEC (IPC Nacional), DEIE Mendoza y Secretaría de Trabajo (RIPTE). Proyecciones de inflación y salario real por FCE UNCUYO.",
        bullets_txt_list=p5_bullets,
        chart_filename="chart_editorial_ipc.png",
        chart_footnote="Nota: Aperturas del IPC INDEC y serie de trayectoria desinflacionaria mensual 2025-2026.",
        chart_height=210,
        kicker_color="#047857"
    ))

    # =========================================================================
    # PÁGINA 6: CUADRO 1. APERTURAS IPC Y CANASTAS — ARQUETIPO SOCIAL
    # =========================================================================
    p6_lead = (
        "El análisis desagregado de las canastas básicas refleja una moderación en la línea de indigencia (CBA en $532.000 nacional y $485.000 Mendoza), "
        "mientras que la Canasta Básica Total ($1.175.000 nacional) mantiene una brecha exigente frente a los ingresos de los deciles no registrados. "
        "La dispersión regional confirma presiones más acotadas en Cuyo frente al Gran Buenos Aires y la Patagonia."
    )
    p6_tabla_data = [
        [Paragraph("<b>CANASTA / UMBRAL DE POBREZA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>VALORIZACIÓN DE CANASTAS (MILES ARS)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>CBT Nacional (Línea Pobreza)</b>", table_cell_bold), Paragraph("820,4", table_cell_center_bold), Paragraph("910,2", table_cell_center_bold), Paragraph("980,5", table_cell_center_bold), Paragraph("1.045", table_cell_center_bold), Paragraph("1.175", table_cell_center_bold), _badge_var("+130"), _badge_var("+354"), Paragraph("1.250", table_cell_center_bold), Paragraph("1.420", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;CBA Nacional (Línea Indigencia)", table_cell_left), Paragraph("370,5", table_cell_center), Paragraph("412,0", table_cell_center), Paragraph("445,2", table_cell_center), Paragraph("478,0", table_cell_center), Paragraph("532,0", table_cell_center), _badge_var("+54,0"), _badge_var("+161"), Paragraph("565,0", table_cell_center), Paragraph("640,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;CBT Mendoza (DEIE Cuyo)", table_cell_left), Paragraph("765,0", table_cell_center), Paragraph("845,0", table_cell_center), Paragraph("912,0", table_cell_center), Paragraph("963,0", table_cell_center), Paragraph("1.085", table_cell_center), _badge_var("+122"), _badge_var("+320"), Paragraph("1.160", table_cell_center), Paragraph("1.310", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;CBA Mendoza (DEIE Cuyo)", table_cell_left), Paragraph("345,0", table_cell_center), Paragraph("380,0", table_cell_center), Paragraph("410,0", table_cell_center), Paragraph("435,0", table_cell_center), Paragraph("485,0", table_cell_center), _badge_var("+50,0"), _badge_var("+140"), Paragraph("515,0", table_cell_center), Paragraph("585,0", table_cell_center)],
        [Paragraph("<b>INDICADORES SOCIALES & COBERTURA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Brecha Salario RIPTE / CBT (%)", table_cell_left), Paragraph("105,4", table_cell_center), Paragraph("108,2", table_cell_center), Paragraph("112,0", table_cell_center), Paragraph("115,4", table_cell_center), Paragraph("118,5", table_cell_center), _badge_var("+3,10"), _badge_var("+13,1"), Paragraph("122,0", table_cell_center), Paragraph("128,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa de Pobreza Urbana (% est.)", table_cell_left), Paragraph("54,20", table_cell_center), Paragraph("51,80", table_cell_center), Paragraph("48,50", table_cell_center), Paragraph("46,20", table_cell_center), Paragraph("44,10", table_cell_center), _badge_var("-2,10"), _badge_var("-10,1"), Paragraph("41,50", table_cell_center), Paragraph("36,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa de Indigencia (% est.)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("16,20", table_cell_center), Paragraph("14,10", table_cell_center), Paragraph("12,80", table_cell_center), Paragraph("11,40", table_cell_center), _badge_var("-1,40"), _badge_var("-7,10"), Paragraph("10,00", table_cell_center), Paragraph("8,20", table_cell_center)],
    ]
    p6_bullets = [
        ("La Canasta Básica Total (CBT) nacional alcanzó los $1.175.000 para un hogar tipo 2",
         "exhibiendo un incremento mensual del 2,2% que acompaña la tasa general de inflación. La estabilidad en los precios de alimentos básicos contuvo la aceleración de la Canasta Alimentaria (CBA: $532.000 nacional y $485.000 en Mendoza), frenando el deterioro en los umbrales de indigencia extrema en los centros urbanos."),
        ("En la Provincia de Mendoza, la medición DEIE sitúa la Canasta Básica Total en $1.085.000",
         "mostrando una brecha favorable de aproximadamente 7,6% respecto a la media nacional, explicada por menores costos relativos en transporte y servicios comerciales. La Canasta Alimentaria mendocina cerró en $485.000, reflejando la tracción de programas locales de abastecimiento y la estabilidad de productos frescos."),
        ("La relación entre el salario registrado (RIPTE) y la CBT alcanzó el 118,5%",
         "Este indicador ratifica que los trabajadores formales han recuperado un margen operativo sobre la línea de pobreza estadística, tras haber tocado niveles críticos cercanos al 100% en 2024. La disminución estimada de la tasa de pobreza hacia el 44,1% confirma el impacto directo de la desaceleración del IPC sobre los estratos medios asalariados.")
    ]
    c1_data = {
        "title": "Canasta Básica Alimentaria (CBA) · Línea Indigencia",
        "val_nac": "$532.000", "val_reg": "$485.000",
        "sub": "Variación mensual: +2,1% m/m · Hogar Tipo 2 (4 miembros) · Cobertura RIPTE: 0,45 salarios.",
        "color": "#0284C7"
    }
    c2_data = {
        "title": "Canasta Básica Total (CBT) · Línea de Pobreza",
        "val_nac": "$1.175.000", "val_reg": "$1.085.000",
        "sub": "Cobertura Salario RIPTE / CBT: 118,5% · Tasa pobreza urbana estimada: 44,1% (-2,1 pp).",
        "color": "#0B2545"
    }
    elements.extend(crear_pagina_arquetipo_social(
        kicker_txt="ESTADÍSTICAS SOCIALES · DISTRIBUCIÓN DEL INGRESO Y LÍNEAS DE POBREZA",
        titulo="Cuadro 1. Aperturas IPC, Canastas Básicas y Líneas de Pobreza",
        card1_data=c1_data,
        card2_data=c2_data,
        tabla_titulo="Valorización de Canastas Básicas e Indicadores de Pobreza e Indigencia (Miles ARS / %)",
        tabla_data=p6_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Datos de canastas valorizadas por INDEC y DEIE Mendoza para Hogar Tipo 2. Estimaciones de pobreza e indigencia basadas en microdatos EPH y modelo FCE UNCUYO.",
        bullets_txt_list=p6_bullets,
        chart_filename="chart_editorial_canastas.png",
        chart_footnote="Nota: Comparativa nacional y regional de canastas básicas CBT y CBA en miles de pesos.",
        chart_height=210
    ))

    # =========================================================================
    # PÁGINA 7: 3. SECTORES CUYO — ARQUETIPO DESGLOSE SECTORIAL
    # =========================================================================
    p7_lead = (
        "La producción sectorial en Mendoza y Cuyo consolidó una dinámica heterogénea durante el segundo trimestre de 2026: "
        "los hidrocarburos no convencionales crecieron a tasas de dos dígitos (+12,5% i.a.) gracias a las inversiones piloto en Vaca Muerta mendocina, "
        "mientras que el despacho de vino fraccionado repuntó un +2,8% i.a., compensando la retracción de la cuenca petrolera convencional madura."
    )
    p7_tabla_data = [
        [Paragraph("<b>CADENA PRODUCTIVA / SECTOR</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>VITIVINICULTURA & AGROINDUSTRIA</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Vino Fraccionado (Miles hl)</b>", table_cell_bold), Paragraph("6.200", table_cell_center_bold), Paragraph("6.850", table_cell_center_bold), Paragraph("7.120", table_cell_center_bold), Paragraph("7.250", table_cell_center_bold), Paragraph("7.340", table_cell_center_bold), _badge_var("+90"), _badge_var("+1.140"), Paragraph("7.500", table_cell_center_bold), Paragraph("7.850", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Despacho Mercado Interno (%)", table_cell_left), Paragraph("-4,20", table_cell_center), Paragraph("-1,80", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("2,80", table_cell_center), _badge_var("+1,00"), _badge_var("+7,00"), Paragraph("3,20", table_cell_center), Paragraph("4,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Vino Fraccionado (%)", table_cell_left), Paragraph("1,50", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("4,80", table_cell_center), _badge_var("+0,70"), _badge_var("+3,30"), Paragraph("5,50", table_cell_center), Paragraph("6,80", table_cell_center)],
        [Paragraph("<b>HIDROCARBUROS & CEMENTO PORTLAND</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Petróleo Total Mendoza (Miles m³)", table_cell_left), Paragraph("205,0", table_cell_center), Paragraph("208,5", table_cell_center), Paragraph("210,4", table_cell_center), Paragraph("211,8", table_cell_center), Paragraph("212,0", table_cell_center), _badge_var("+0,20"), _badge_var("+7,00"), Paragraph("215,0", table_cell_center), Paragraph("224,0", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Vaca Muerta Sur Mendoza (Shale)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("22,00", table_cell_center), Paragraph("25,40", table_cell_center), Paragraph("28,10", table_cell_center), Paragraph("30,00", table_cell_center), _badge_var("+1,90"), _badge_var("+11,5"), Paragraph("34,00", table_cell_center), Paragraph("45,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Cuenca Cuyana Convencional (%)", table_cell_left), Paragraph("-3,20", table_cell_center), Paragraph("-2,40", table_cell_center), Paragraph("-1,80", table_cell_center), Paragraph("-1,20", table_cell_center), Paragraph("-0,80", table_cell_center), _badge_var("+0,40"), _badge_var("+2,40"), Paragraph("-0,50", table_cell_center), Paragraph("0,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Despacho Cemento Cuyo (AFCP %)", table_cell_left), Paragraph("-12,4", table_cell_center), Paragraph("-8,50", table_cell_center), Paragraph("-4,20", table_cell_center), Paragraph("-1,50", table_cell_center), Paragraph("1,20", table_cell_center), _badge_var("+2,70"), _badge_var("+13,6"), Paragraph("3,50", table_cell_center), Paragraph("7,80", table_cell_center)],
    ]
    p7_bullets = [
        ("El sector vitivinícola registró un incremento interanual del +2,8% en despacho doméstico",
         "alcanzando las 7.340 miles de hectolitros acumuladas según datos del INV, convalidando la estabilización del consumo en el canal minorista y la moderación en insumos secos. En el plano exportador, los envíos crecieron +4,8% i.a. impulsados por varietales Malbec de alta gama en EE.UU., Brasil y Reino Unido."),
        ("En la cuenca hidrocarburífera de Mendoza, el shale en Vaca Muerta superó los 30.000 m³/mes",
         "con un crecimiento interanual del +12,5% que compensa la declinación de los yacimientos maduros de la Cuenca Cuyana (-0,8% i.a.). Las inversiones vía RIGI en bloques CN-VII A y Paso Bardas Norte anticipan una aceleración hacia 45.000 m³/mes para 2027, dinamizando las regalías provinciales."),
        ("El despacho de cemento portland en Cuyo anotó su primera variación positiva (+1,2% i.a.) en 18 meses",
         "Este indicador de la AFCP refleja la reactivación de obras de infraestructura privada, desarrollos inmobiliarios y ampliaciones mineras. La normalización del financiamiento comercial en pesos y la estabilidad cambiaria han reducido los sobrecostos de acopio en corralones.")
    ]
    elements.extend(crear_pagina_arquetipo_desglose(
        kicker_txt="ECONOMÍA REGIONAL · DESAGREGACIÓN SECTORIAL Y PRODUCCIÓN EN CUYO",
        titulo="3. Desagregación Sectorial y Producción en Mendoza y Cuyo",
        leadin_txt=p7_lead,
        tabla_titulo="Principales indicadores de producción sectorial en Mendoza y Cuyo (Miles hl / m³ / %)",
        tabla_data=p7_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía de la Nación y AFCP. Cálculos y proyecciones por FCE UNCUYO.",
        bullets_txt_list=p7_bullets,
        chart_filename="chart_editorial_cuyo.png",
        chart_footnote="Nota: Despacho de vino fraccionado (INV) y variación interanual del ISARC provincial en Cuyo.",
        chart_height=210,
        kicker_color="#047857"
    ))

    # =========================================================================
    # PÁGINA 8: 3.1 COMPARATIVO REGIONAL CUYO (ISARC) — ARQUETIPO SCORECARD
    # =========================================================================
    p8_lead = (
        "El Índice Sintético de Actividad Regional de Cuyo (ISARC) ratifica la recuperación sincronizada de las economías provinciales (+3,1% i.a. regional), "
        "con San Luis liderando el dinamismo manufacturero (+5,8% i.a.), seguida por Mendoza (+3,4% i.a.) apoyada en hidrocarburos y turismo, "
        "y San Juan (+2,1% i.a.) consolidando la preparación de proyectos cupríferos de escala global adheridos al marco normativo del RIGI."
    )
    p8_tabla_data = [
        [Paragraph("<b>JURISDICCIÓN / INDICADOR ISARC</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>ÍNDICE REGIONAL CUYO & PROVINCIAS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>ISARC Región Cuyo (% i.a.)</b>", table_cell_bold), Paragraph("1,50", table_cell_center_bold), Paragraph("2,10", table_cell_center_bold), Paragraph("2,60", table_cell_center_bold), Paragraph("2,80", table_cell_center_bold), Paragraph("3,10", table_cell_center_bold), _badge_var("+0,30"), _badge_var("+1,60"), Paragraph("3,40", table_cell_center_bold), Paragraph("4,50", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Mendoza (Petróleo / Vitivinicultura)", table_cell_left), Paragraph("1,80", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,50", table_cell_center), Paragraph("3,10", table_cell_center), Paragraph("3,40", table_cell_center), _badge_var("+0,30"), _badge_var("+1,60"), Paragraph("3,60", table_cell_center), Paragraph("4,60", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;San Luis (Manufacturas / Alimentos)", table_cell_left), Paragraph("3,20", table_cell_center), Paragraph("4,00", table_cell_center), Paragraph("4,80", table_cell_center), Paragraph("5,20", table_cell_center), Paragraph("5,80", table_cell_center), _badge_var("+0,60"), _badge_var("+2,60"), Paragraph("6,20", table_cell_center), Paragraph("5,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;San Juan (Minería / Agroindustria)", table_cell_left), Paragraph("1,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("1,90", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,10", table_cell_center), _badge_var("+0,10"), _badge_var("+0,90"), Paragraph("2,80", table_cell_center), Paragraph("5,20", table_cell_center)],
        [Paragraph("<b>TRACCIÓN SECTORIAL REGIONAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Minería Metalífera & Hidrocarburos", table_cell_left), Paragraph("5,40", table_cell_center), Paragraph("6,50", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("8,10", table_cell_center), Paragraph("8,50", table_cell_center), _badge_var("+0,40"), _badge_var("+3,10"), Paragraph("9,50", table_cell_center), Paragraph("12,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Agroindustria Alimentaria Cuyo", table_cell_left), Paragraph("2,10", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("3,60", table_cell_center), Paragraph("3,80", table_cell_center), _badge_var("+0,20"), _badge_var("+1,70"), Paragraph("4,20", table_cell_center), Paragraph("4,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Comercio & Servicios Cuyanos", table_cell_left), Paragraph("-1,80", table_cell_center), Paragraph("0,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("2,40", table_cell_center), _badge_var("+0,30"), _badge_var("+4,20"), Paragraph("2,80", table_cell_center), Paragraph("3,60", table_cell_center)],
    ]
    p8_bloques = [
        ("Polos de Tracción Regional & Dinámica Provincial",
         "San Luis encabeza la reactivación regional con una expansión del +5,8% interanual en el ISARC, apuntalada por la alta densidad de su parque industrial químico, farmacéutico y de alimentos. La disponibilidad de capacidad ociosa y la normalización del crédito bancario permitieron a las plantas fabriles responder con agilidad a la demanda interna. Mendoza consolidó una suba del +3,4% i.a., sustentada en el polo energético de Malargüe y la solidez del turismo receptivo internacional."),
        ("Horizonte Minero Sanjuanino & Sinergias Cuyanas",
         "San Juan se expandió al +2,1% i.a., marcando una fase de preparación e inversión preliminar en minería de cobre de gran escala (Josemaría, Los Azules) en el marco del régimen RIGI. Los desembolsos en ingeniería y caminos de acceso anticipan un fuerte salto hacia 2027 al iniciarse la construcción de plantas concentradoras, generando encadenamientos de proveedores en todo Cuyo."),
        ("Integración Logística y Corredor Bioceánico",
         "La convergencia de inversiones en pasos cordilleranos (Paso Cristo Redentor y Pehuenche) y la reactivación del ferrocarril San Martín Cargas consolidan a la región como nodo estratégico del comercio con el Pacífico. La reducción estimada del 18% en costos de flete fortalece la proyección exportadora agroindustrial y minera hacia mercados asiáticos.")
    ]
    elements.extend(crear_pagina_arquetipo_scorecard(
        kicker_txt="DESARROLLO REGIONAL · ÍNDICE SINTÉTICO DE ACTIVIDAD DE CUYO (ISARC)",
        titulo="3.1. Comparativo Regional: Índice Sintético de Actividad (ISARC)",
        leadin_txt=p8_lead,
        tabla_titulo="Evolución trimestral del ISARC y tracción sectorial en Cuyo (%)",
        tabla_data=p8_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: DEIE Mendoza, Dirección Provincial de Estadística de San Juan y San Luis, y OERU FCE UNCUYO. Base 2004=100.",
        bloques_tematicos=p8_bloques,
        chart_filename="chart_editorial_regional_cuyo.png",
        chart_footnote="Nota: Evolución comparada del ISARC provincial y contribución por sectores productivos de Cuyo.",
        chart_height=205,
        kicker_color="#047857"
    ))

    # =========================================================================
    # PÁGINA 9: 4. BALANCE BCRA Y POSTURA MONETARIA — ARQUETIPO DESGLOSE
    # =========================================================================
    p9_lead = (
        "El balance del Banco Central de la República Argentina consolidó su saneamiento estructural en el segundo trimestre de 2026: "
        "los pasivos remunerados cuasifiscales (pases pasivos y LeFis) se encuentran completamente extinguidos ($0 stock), mientras que "
        "las Reservas Internacionales Netas (RIN) alcanzaron terreno positivo (+USD 3.650 M), permitiendo al BCRA transitar hacia un esquema monetario ortodoxo."
    )
    p9_tabla_data = [
        [Paragraph("<b>VARIABLE DE BALANCE BCRA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>AGREGADOS MONETARIOS (BILLONES ARS)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Base Monetaria (Promedio)</b>", table_cell_bold), Paragraph("19,80", table_cell_center_bold), Paragraph("21,50", table_cell_center_bold), Paragraph("23,40", table_cell_center_bold), Paragraph("24,80", table_cell_center_bold), Paragraph("26,80", table_cell_center_bold), _badge_var("+2,00"), _badge_var("+7,00"), Paragraph("28,50", table_cell_center_bold), Paragraph("32,00", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Circulante en Poder Público", table_cell_left), Paragraph("12,40", table_cell_center), Paragraph("13,80", table_cell_center), Paragraph("14,90", table_cell_center), Paragraph("15,80", table_cell_center), Paragraph("16,90", table_cell_center), _badge_var("+1,10"), _badge_var("+4,50"), Paragraph("18,00", table_cell_center), Paragraph("20,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Encajes Bancarios en BCRA", table_cell_left), Paragraph("7,40", table_cell_center), Paragraph("7,70", table_cell_center), Paragraph("8,50", table_cell_center), Paragraph("9,00", table_cell_center), Paragraph("9,90", table_cell_center), _badge_var("+0,90"), _badge_var("+2,50"), Paragraph("10,50", table_cell_center), Paragraph("11,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Stock Pases Remunerados", table_cell_left), Paragraph("4,20", table_cell_center), Paragraph("1,50", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center), _badge_var("0,00"), _badge_var("-4,20"), Paragraph("0,00", table_cell_center), Paragraph("0,00", table_cell_center)],
        [Paragraph("<b>RESERVAS & TASAS DE INTERÉS</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Reservas Brutas (USD Millones)", table_cell_left), Paragraph("27.120", table_cell_center), Paragraph("29.450", table_cell_center), Paragraph("31.200", table_cell_center), Paragraph("32.800", table_cell_center), Paragraph("34.150", table_cell_center), _badge_var("+1.350"), _badge_var("+7.030"), Paragraph("36.000", table_cell_center), Paragraph("41.500", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Reservas Netas (RIN USD MM)", table_cell_left), Paragraph("-3.200", table_cell_center), Paragraph("-1.100", table_cell_center), Paragraph("+850", table_cell_center), Paragraph("+2.400", table_cell_center), Paragraph("+3.650", table_cell_center), _badge_var("+1.250"), _badge_var("+6.850"), Paragraph("+5.000", table_cell_center), Paragraph("+8.500", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Tasa Política Monetaria (TNA %)", table_cell_left), Paragraph("45,00", table_cell_center), Paragraph("40,00", table_cell_center), Paragraph("35,00", table_cell_center), Paragraph("35,00", table_cell_center), Paragraph("32,00", table_cell_center), _badge_var("-3,00"), _badge_var("-13,0"), Paragraph("30,00", table_cell_center), Paragraph("25,00", table_cell_center)],
    ]
    p9_bullets = [
        ("La extinción definitiva de los pasivos remunerados clausuró el motor de emisión endógena",
         "El stock de pases pasivos y LeFis se mantiene en cero desde julio de 2025, trasladando la absorción bancaria hacia Letras del Tesoro (Lecaps) financiadas con superávit primario. Esta transformación erradicó el déficit cuasifiscal que equivalía a 10 puntos del PIB en 2023, recomponiendo el patrimonio neto del Banco Central."),
        ("Las Reservas Internacionales Netas (RIN) alcanzaron los +USD 3.650 millones, un giro de USD 14.850 M",
         "frente al piso de -USD 11.200 millones registrado a fines de 2023. La compra neta en el Mercado Libre de Cambios (MLC) y la recomposición de depósitos privados en dólares (+USD 6.500 M) han fortalecido la liquidez sistémica, allanando el camino hacia la remoción gradual de restricciones cruzadas."),
        ("La Base Monetaria se expande al compás de la remonetización del crédito privado",
         "Alcanzando los $26,8 billones, el circulante crece por debajo de la inflación interanual, convalidando una contracción real frente a promedios históricos. La autoridad monetaria mantiene una postura contractiva mediante tasas reales ex-ante positivas en letras fiscales, anclando las cotizaciones financieras.")
    ]
    elements.extend(crear_pagina_arquetipo_desglose(
        kicker_txt="RÉGIMEN MONETARIO · BALANCE PATRIMONIAL Y EXTINCIÓN DE PASIVOS CUASIFISCALES",
        titulo="4. Balance del BCRA, Pasivos Cuasifiscales y Postura Monetaria",
        leadin_txt=p9_lead,
        tabla_titulo="Evolución de los agregados monetarios y balance patrimonial del BCRA",
        tabla_data=p9_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Banco Central de la República Argentina (BCRA v4.0). Base monetaria e instrumentos de absorción en billones de ARS; reservas en millones de USD.",
        bullets_txt_list=p9_bullets,
        chart_filename="chart_editorial_monetary.png",
        chart_footnote="Nota: Dinámica de base monetaria frente a pasivos remunerados extintos y reservas internacionales netas (RIN).",
        chart_height=210,
        kicker_color="#0284C7"
    ))

    # =========================================================================
    # PÁGINA 10: 5. ARBITRAJE EN PESOS Y BREAKEVEN — ARQUETIPO ASIMÉTRICO
    # =========================================================================
    p10_lead = (
        "La estructura temporal de tasas en moneda local convalidó una compresión ordenada del rendimiento efectivo mensual (TEM 2,95% en tramo corto), "
        "ofreciendo una prima real ex-ante de +95 pb sobre la inflación esperada REM (2,00% m/m). "
        "El spread de breakeven inflacionario frente a bonos indexados otorga un colchón defensivo para la estrategia de carry trade."
    )
    p10_bullets_asym = [
        ("Pendiente de Curva Lecap & Carry Contractual",
         "La curva de Letras del Tesoro a tasa fija presenta una pendiente ligeramente ascendente (TEM 2,95% en tramo corto hasta 3,40% a doce meses), convalidando la disciplina fiscal y la capacidad de rollover del Tesoro. Con una inflación REM de 2,00%, el tramo corto ofrece una prima real contractual de +95 pb mensual que incentiva el estacionamiento de liquidez corporativa."),
        ("Breakeven Inflacionario vs Boncer Indexados",
         "El breakeven de indiferencia entre la Lecap corta y el Boncer TZX27 (CER+1,10%) se sitúa en 2,86% m/m, un colchón de 86 pb sobre la expectativa del mercado. La tasa fija absorbe holgadamente el riesgo de reacomodamiento tarifario y devenga el carry más eficiente del sistema financiero."),
        ("Mecanismo de Transmisión & Absorción Bancaria",
         "La extinción de los pasivos remunerados del BCRA canalizó la liquidez bancaria hacia letras del Tesoro sin convalidar emisión cuasifiscal. Este ordenamiento monetario afianza la estabilidad de la brecha cambiaria y estimula la remonetización del crédito comercial.")
    ]
    p10_mini_tabla = [
        [Paragraph("<b>Instrumento</b>", cell_header_style), Paragraph("<b>Tasa / Spread</b>", cell_header_style), Paragraph("<b>Diagnóstico</b>", cell_header_style)],
        [Paragraph("Lecap Corta (S31G5)", table_cell_bold), Paragraph("TEM 2,95% (TNA 35,4%)", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Carry Real +95 pb</font>", table_cell_center)],
        [Paragraph("Lecap Larga (S30J6)", table_cell_bold), Paragraph("TEM 3,40% (TNA 40,8%)", table_cell_center), Paragraph("Pendiente Normal", table_cell_center)],
        [Paragraph("Boncer TZX27", table_cell_bold), Paragraph("CER + 1,10%", table_cell_center), Paragraph("Hedge Tarifario", table_cell_center)],
        [Paragraph("Breakeven Lecap/CER", table_cell_bold), Paragraph("2,86% mensual", table_cell_center), Paragraph("Colchón +86 pb", table_cell_center)],
        [Paragraph("Inflación REM BCRA", table_cell_bold), Paragraph("2,00% mensual", table_cell_center), Paragraph("Ancla Sostenida", table_cell_center)],
        [Paragraph("Caución Bursátil ByMA", table_cell_bold), Paragraph("TNA 32,5% (1d-7d)", table_cell_center), Paragraph("Piso de Fondeo", table_cell_center)],
    ]
    p10_scorecard_data = [
        [Paragraph("<b>Activo</b>", ParagraphStyle('THC1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)), Paragraph("<b>Postura</b>", ParagraphStyle('THC2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)), Paragraph("<b>Peso</b>", ParagraphStyle('THC3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)), Paragraph("<b>Target</b>", ParagraphStyle('THC4', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("Lecaps Cortas", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>OW</b></font>", table_cell_center), Paragraph("40%", table_cell_center_bold), Paragraph("TEM 2,95%", table_cell_center)],
        [Paragraph("Boncer TZX27", table_cell_bold), Paragraph(f"<font color='{MUTED.hexval()}'><b>N</b></font>", table_cell_center), Paragraph("15%", table_cell_center_bold), Paragraph("CER+1,1%", table_cell_center)],
        [Paragraph("Bopreal Serie 3", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>OW</b></font>", table_cell_center), Paragraph("10%", table_cell_center_bold), Paragraph("TIR 10,4%", table_cell_center)],
        [Paragraph("Duales / Dólar Link", table_cell_bold), Paragraph(f"<font color='{MUTED.hexval()}'><b>N</b></font>", table_cell_center), Paragraph("5%", table_cell_center_bold), Paragraph("Hedge FX", table_cell_center)],
        [Paragraph("ByMA Equity", table_cell_bold), Paragraph(f"<font color='{NEG_COLOR}'><b>UW</b></font>", table_cell_center), Paragraph("5%", table_cell_center_bold), Paragraph("Selectivo", table_cell_center)],
    ]
    p10_catalizador = "• <b>Rollover del Tesoro &ge; 100%:</b> Refinanciación de vencimientos en Lecaps sin convalidar saltos de corte.<br/>• <b>Licitación Lecaps:</b> Monitoreo de extensión de plazos hacia 2027.<br/>• <b>Depósitos a Plazo:</b> Crecimiento sostenido por tasas reales contractuales positivas."
    elements.extend(crear_pagina_arquetipo_asimetrico(
        kicker_txt="CURVAS EN PESOS · ARBITRAJE DE TASAS, BREAKEVEN & CARRY TRADE",
        titulo="5. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera",
        leadin_txt=p10_lead,
        col_izq_titulo="DISCUSIÓN ANALÍTICA DE CURVAS & RENDIMIENTOS REALES",
        col_izq_bullets=p10_bullets_asym,
        mini_tabla_titulo="Indicadores Clave de la Curva en Pesos",
        mini_tabla_data=p10_mini_tabla,
        card_der_titulo="SCORECARD TÁCTICO & MONITOR DE TASAS",
        card_der_table_data=p10_scorecard_data,
        catalizador_txt=p10_catalizador,
        chart_filename="chart_editorial_rates.png",
        chart_footnote="Nota: Curvas de rendimiento TEM Lecaps vs. Boncer y spread de breakeven inflacionario frente al REM.",
        chart_height=210,
        kicker_color="#0284C7"
    ))

    # =========================================================================
    # PÁGINA 11: 6. DEUDA SOBERANA Y NELSON-SIEGEL — ARQUETIPO TOPCHART
    # =========================================================================
    p11_lead = (
        "La curva soberana de deuda en moneda extranjera profundizó una notable compresión de rendimientos en el segundo trimestre de 2026: "
        "el riesgo país EMBI+ quebró el umbral de los 510 pb (-174 pb en 30 días), mientras que el ajuste paramétrico de Nelson-Siegel situó la "
        "tasa asintótica de largo plazo (Beta 0) en 9,40%, con el GD35 rindiendo 9,65% TIR y convalidando una elevada convexidad."
    )
    p11_tabla_data = [
        [Paragraph("<b>PARÁMETRO / BONO SOBERANO</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>PARÁMETROS NELSON-SIEGEL (1987)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Nivel Asintótico Largo Plazo (Beta 0 %)</b>", table_cell_bold), Paragraph("14,20", table_cell_center_bold), Paragraph("12,50", table_cell_center_bold), Paragraph("11,20", table_cell_center_bold), Paragraph("10,10", table_cell_center_bold), Paragraph("9,40", table_cell_center_bold), _badge_var("-0,70"), _badge_var("-4,80"), Paragraph("8,80", table_cell_center_bold), Paragraph("7,50", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Pendiente Corto-Largo (Beta 1 %)", table_cell_left), Paragraph("12,40", table_cell_center), Paragraph("9,80", table_cell_center), Paragraph("7,50", table_cell_center), Paragraph("6,20", table_cell_center), Paragraph("5,60", table_cell_center), _badge_var("-0,60"), _badge_var("-6,80"), Paragraph("4,20", table_cell_center), Paragraph("2,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Curvatura Joroba Media (Beta 2 %)", table_cell_left), Paragraph("-8,50", table_cell_center), Paragraph("-6,20", table_cell_center), Paragraph("-4,80", table_cell_center), Paragraph("-3,90", table_cell_center), Paragraph("-3,20", table_cell_center), _badge_var("+0,70"), _badge_var("+5,30"), Paragraph("-2,40", table_cell_center), Paragraph("-1,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Bondad de Ajuste Modelo (R²)", table_cell_left), Paragraph("0,945", table_cell_center), Paragraph("0,962", table_cell_center), Paragraph("0,974", table_cell_center), Paragraph("0,980", table_cell_center), Paragraph("0,984", table_cell_center), _badge_var("+0,004"), _badge_var("+0,039"), Paragraph("0,988", table_cell_center), Paragraph("0,992", table_cell_center)],
        [Paragraph("<b>RENDIMIENTOS DE MERCADO (TIR %)</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Bonar 2030 (AL30 Ley Local)", table_cell_left), Paragraph("18,50", table_cell_center), Paragraph("15,20", table_cell_center), Paragraph("13,40", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("11,20", table_cell_center), _badge_var("-0,90"), _badge_var("-7,30"), Paragraph("10,00", table_cell_center), Paragraph("8,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Global 2035 (GD35 Ley NY)", table_cell_left), Paragraph("14,80", table_cell_center), Paragraph("12,90", table_cell_center), Paragraph("11,50", table_cell_center), Paragraph("10,40", table_cell_center), Paragraph("9,65", table_cell_center), _badge_var("-0,75"), _badge_var("-5,15"), Paragraph("8,90", table_cell_center), Paragraph("7,60", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Global 2038 (GD38 Ley NY)", table_cell_left), Paragraph("15,10", table_cell_center), Paragraph("13,10", table_cell_center), Paragraph("11,70", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("9,70", table_cell_center), _badge_var("-0,80"), _badge_var("-5,40"), Paragraph("9,00", table_cell_center), Paragraph("7,80", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Riesgo País EMBI+ (Puntos Básicos)", table_cell_left), Paragraph("1.240", table_cell_center), Paragraph("980", table_cell_center), Paragraph("810", table_cell_center), Paragraph("680", table_cell_center), Paragraph("506", table_cell_center), _badge_var("-174"), _badge_var("-734"), Paragraph("450", table_cell_center), Paragraph("320", table_cell_center)],
    ]
    p11_conclusiones = [
        ("Sobreponderar Tramo Medio-Largo (GD35 / GD38)",
         "Con modified duration de 6,8 años y convexidad favorable (+0,42), una compresión adicional de 150 pb en el spread EMBI+ convalidaría una ganancia de capital del +10,2% en dólares, superando ampliamente a créditos corporativos comparables."),
        ("Aplanamiento Estructural de Curva Nelson-Siegel",
         "La reducción continua de Beta 1 (+5,60%) y el anclaje asintótico de Beta 0 (9,40%, R²=0,984) confirman la transición desde una curva históricamente invertida hacia una morfología ascendente de crédito soberano normalizado."),
        ("Arbitraje de Legislación Ley Local vs Ley NY",
         "La compresión de la prima de legislación (spread AL30 vs GD30 en mínimos de 80 pb) habilita la rotación hacia títulos Ley Nueva York para maximizar la liquidez global ante la reapertura del crédito voluntario internacional.")
    ]
    elements.extend(crear_pagina_arquetipo_topchart(
        kicker_txt="DEUDA SOBERANA · MODELIZACIÓN PARAMÉTRICA DE CURVAS NELSON-SIEGEL",
        titulo="6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel",
        leadin_txt=p11_lead,
        chart_filename="chart_editorial_sovereign.png",
        chart_footnote="Nota: Curva spot de rendimientos soberanos USD calibrada y estructura de tasas forward instantáneas f(t).",
        tabla_titulo="Parámetros econométricos Nelson-Siegel y rendimientos spot de la curva soberana USD",
        tabla_data=p11_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: ByMA, MAE y estimación paramétrica Nelson-Siegel (1987) por FCE UNCUYO. Riesgo país EMBI+ de J.P. Morgan.",
        caja_titulo="CONCLUSIONES TÁCTICAS PARA EL INVERSOR INSTITUCIONAL",
        conclusiones_tacticas=p11_conclusiones,
        chart_height=205,
        kicker_color="#0284C7"
    ))

    # =========================================================================
    # PÁGINA 12: 7. MICROESTRUCTURA FX Y ROFEX CIP — ARQUETIPO ASIMÉTRICO
    # =========================================================================
    p12_lead = (
        "El mercado cambiario cerró en un régimen de marcada estabilidad financiera: el Dólar CCL finalizó en $1.600,20 con una brecha cambiaria "
        "acotada al 4,5% sobre el mayorista ($1.511,53). La curva teórica de futuros por Paridad de Tasas Cubierta (CIP) descarta saltos discretos "
        "y las métricas multivariadas ratifican baja vulnerabilidad sistémica."
    )
    p12_bullets_asym = [
        ("Compresión de Brecha Cambiaria al 4,52%",
         "La vigencia del esquema blend 80/20 y la esterilización de excedentes de liquidez contuvieron la demanda de dólares financieros. La cotización del CCL ($1.600,20) converge hacia el oficial mayorista ($1.511,53), desarticulando expectativas de devaluación y reduciendo las primas de riesgo corporativo."),
        ("Alineación de Futuros CIP & Paridad Cubierta",
         "Los contratos Matba-Rofex operan a una TNA del 35,4% a 30 días, en perfecta paridad con letras del Tesoro, validando el crawling peg del 2% mensual. La curva de futuros descarta saltos discretos, facilitando la cobertura financiera del sector importador."),
        ("Métricas de Resiliencia Sistémica & Mahalanobis",
         "El monitoreo multivariado sitúa la turbulencia en 5,40 dt (muy por debajo del umbral crítico Chi² de 11,07) y el Ratio de Absorción PCA en 64,2%, confirmando la solidez del sistema financiero y la ausencia de correlaciones desestabilizadoras.")
    ]
    p12_mini_tabla = [
        [Paragraph("<b>Variable</b>", cell_header_style), Paragraph("<b>Nivel Observado</b>", cell_header_style), Paragraph("<b>Semáforo</b>", cell_header_style)],
        [Paragraph("Dólar CCL / Brecha", table_cell_bold), Paragraph("$1.600,20 / 4,52%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Normalizado</font>", table_cell_center)],
        [Paragraph("Dólar MEP AL30", table_cell_bold), Paragraph("$1.532,40 / 1,38%", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Equilibrio</font>", table_cell_center)],
        [Paragraph("Mayorista A3500", table_cell_bold), Paragraph("$1.511,53 (Crawling 2%)", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Anclado</font>", table_cell_center)],
        [Paragraph("Futuro CIP 30d", table_cell_bold), Paragraph("$1.549 (TNA 35,4%)", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Alineado</font>", table_cell_center)],
        [Paragraph("Turbulencia Mahalanobis", table_cell_bold), Paragraph("5,40 dt (Chi²=11,07)", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Sin Estrés</font>", table_cell_center)],
        [Paragraph("Absorption Ratio PCA", table_cell_bold), Paragraph("64,2% (1-PC)", table_cell_center), Paragraph(f"<font color='{POS_COLOR}'>Resiliente</font>", table_cell_center)],
    ]
    p12_scorecard_data = [
        [Paragraph("<b>Pilar FX</b>", ParagraphStyle('THFX1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)), Paragraph("<b>Estado</b>", ParagraphStyle('THFX2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)), Paragraph("<b>Nivel</b>", ParagraphStyle('THFX3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)), Paragraph("<b>Umbral</b>", ParagraphStyle('THFX4', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))],
        [Paragraph("Brecha CCL", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>Baja</b></font>", table_cell_center), Paragraph("4,52%", table_cell_center_bold), Paragraph("&lt; 15,0%", table_cell_center)],
        [Paragraph("Futuros 30d", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>Normal</b></font>", table_cell_center), Paragraph("35,4%", table_cell_center_bold), Paragraph("&le; Lecap", table_cell_center)],
        [Paragraph("Reservas RIN", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>Positivas</b></font>", table_cell_center), Paragraph("+USD 3.650M", table_cell_center_bold), Paragraph("&gt; USD 0", table_cell_center)],
        [Paragraph("Depósitos USD", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>Sólido</b></font>", table_cell_center), Paragraph("USD 20.800M", table_cell_center_bold), Paragraph("En Alza", table_cell_center)],
        [Paragraph("PCA AR", table_cell_bold), Paragraph(f"<font color='{POS_COLOR}'><b>Resiliente</b></font>", table_cell_center), Paragraph("64,2%", table_cell_center_bold), Paragraph("&lt; 75,0%", table_cell_center)],
    ]
    p12_catalizador = "• <b>Oferta Blend 80/20 & Reservas:</b> Liquidación continua de agroindustria y crudo no convencional.<br/>• <b>Remoción de Restricciones:</b> Desarme secuencial y programado de cepos cambiarios cruzados.<br/>• <b>Balanza de Pagos:</b> Superávit comercial sostenido por balanza energética positiva."
    elements.extend(crear_pagina_arquetipo_asimetrico(
        kicker_txt="MERCADO DE CAMBIOS · MICROESTRUCTURA FX, ROFEX CIP & RIESGO SISTÉMICO",
        titulo="7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica",
        leadin_txt=p12_lead,
        col_izq_titulo="MICROESTRUCTURA SPOT, PARIDAD CUBIERTA & ESTABILIDAD",
        col_izq_bullets=p12_bullets_asym,
        mini_tabla_titulo="Monitor de Variables Cambiarias & Sistémicas",
        mini_tabla_data=p12_mini_tabla,
        card_der_titulo="MONITOR FX & SEMÁFORO DE VULNERABILIDAD",
        card_der_table_data=p12_scorecard_data,
        catalizador_txt=p12_catalizador,
        chart_filename="chart_editorial_fx.png",
        chart_footnote="Nota: Cotizaciones spot en ARS y curva teórica de futuros por paridad cubierta de tasas (CIP).",
        chart_height=210,
        kicker_color="#0284C7"
    ))

    # =========================================================================
    # PÁGINA 13: 7.1. TIPO DE CAMBIO REAL BILATERAL — ARQUETIPO DESGLOSE
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
        [Paragraph("<b>TCR Bilateral ARS/USD (Base 100)</b>", table_cell_bold), Paragraph("84,00", table_cell_center_bold), Paragraph("81,20", table_cell_center_bold), Paragraph("80,50", table_cell_center_bold), Paragraph("79,50", table_cell_center_bold), Paragraph("78,40", table_cell_center_bold), _badge_var("-1,10"), _badge_var("-5,60"), Paragraph("76,50", table_cell_center_bold), Paragraph("75,00", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;TCR Multilateral BCRA (TCRM)", table_cell_left), Paragraph("89,50", table_cell_center), Paragraph("87,40", table_cell_center), Paragraph("86,20", table_cell_center), Paragraph("85,80", table_cell_center), Paragraph("84,50", table_cell_center), _badge_var("-1,30"), _badge_var("-5,00"), Paragraph("83,00", table_cell_center), Paragraph("82,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;TCR Bilateral con Brasil (Real/ARS)", table_cell_left), Paragraph("92,40", table_cell_center), Paragraph("90,10", table_cell_center), Paragraph("88,50", table_cell_center), Paragraph("87,40", table_cell_center), Paragraph("86,20", table_cell_center), _badge_var("-1,20"), _badge_var("-6,20"), Paragraph("85,00", table_cell_center), Paragraph("84,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Crawling Peg Mensual BCRA (%)", table_cell_left), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), Paragraph("2,00", table_cell_center), _badge_var("0,00"), _badge_var("0,00"), Paragraph("2,00", table_cell_center), Paragraph("1,50", table_cell_center)],
        [Paragraph("<b>CUENTAS EXTERNAS & BALANZA COMERCIAL</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Superávit Comercial (USD MM trim.)", table_cell_left), Paragraph("4.120", table_cell_center), Paragraph("4.580", table_cell_center), Paragraph("4.250", table_cell_center), Paragraph("3.950", table_cell_center), Paragraph("3.850", table_cell_center), _badge_var("-100"), _badge_var("-270"), Paragraph("15.200", table_cell_center), Paragraph("18.400", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Exportaciones Totales (USD MM)", table_cell_left), Paragraph("19.450", table_cell_center), Paragraph("21.200", table_cell_center), Paragraph("20.800", table_cell_center), Paragraph("20.100", table_cell_center), Paragraph("20.450", table_cell_center), _badge_var("+350"), _badge_var("+1.000"), Paragraph("84.500", table_cell_center), Paragraph("92.000", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Importaciones Totales (USD MM)", table_cell_left), Paragraph("15.330", table_cell_center), Paragraph("16.620", table_cell_center), Paragraph("16.550", table_cell_center), Paragraph("16.150", table_cell_center), Paragraph("16.600", table_cell_center), _badge_var("+450"), _badge_var("+1.270"), Paragraph("69.300", table_cell_center), Paragraph("73.600", table_cell_center)],
    ]
    p13_bullets = [
        ("El Tipo de Cambio Real Bilateral se ubicó en 78,4 puntos en el marco de la desinflación",
         "La absorción del salto discreto de diciembre de 2023 por la inflación acumulada sitúa el poder de compra del dólar mayorista en niveles comparables a los promedios históricos de la post-convertibilidad. Los programas de consolidación fiscal de shock convalidan tipos de cambio de equilibrio más apreciados gracias a la atracción de inversión fija."),
        ("El superávit comercial trimestral alcanzó USD 3.850 millones gracias a la energía y el agro",
         "A pesar de la apreciación cambiaria nominal y real, la balanza de bienes sostiene un elevado saldo positivo traccionado por Vaca Muerta (saldo energético proyectado en +USD 4.500 M) y embarques agrícolas récord, compensando la mayor demanda de bienes de capital importados."),
        ("La competitividad estructural no depende de saltos devaluatorios nominales",
         "sino de la reducción de costos tributarios en frontera (baja de aranceles e impuesto PAIS) y mejoras logísticas viales y ferroviarias. La estabilidad cambiaria otorga previsibilidad para estructurar contratos comerciales y financieros de mediano plazo.")
    ]
    elements.extend(crear_pagina_arquetipo_desglose(
        kicker_txt="SECTOR EXTERNO · TIPO DE CAMBIO REAL BILATERAL & BALANZA COMERCIAL",
        titulo="7.1. Tipo de Cambio Real Bilateral (TCR) y Competitividad Cambiaria",
        leadin_txt=p13_lead,
        tabla_titulo="Evolución del Tipo de Cambio Real Bilateral, Multilateral y Cuentas Externas",
        tabla_data=p13_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: BCRA (series TCR y TCRM), INDEC (intercambio comercial argentino ICA) y BLS (Estados Unidos). Base dic-2016=100.",
        bullets_txt_list=p13_bullets,
        chart_filename="chart_editorial_tcr.png",
        chart_footnote="Nota: Evolución histórica del TCR Bilateral ARS/USD y comparativa frente a hitos macroeconómicos.",
        chart_height=205,
        kicker_color="#0284C7"
    ))

    # =========================================================================
    # PÁGINA 14: 8. RENTA VARIABLE Y BALANCES (MERVAL) — ARQUETIPO TOPCHART
    # =========================================================================
    p14_lead = (
        "El mercado accionario argentino (S&P Merval) consolidó su cotización en máximos de la década al superar los USD 1.900 CCL, "
        "traccionado por la solidez de los balances corporativos de los sectores energético y financiero. "
        "Las compañías líderes presentan múltiplos EV/EBITDA comprimidos (3,8x a 4,1x) y elevados márgenes operativos EBITDA, "
        "convalidando un cambio de régimen desde cobertura inflacionaria hacia flujos genuinos de inversión en capital."
    )
    p14_tabla_data = [
        [Paragraph("<b>EMPRESA LÍDER / RATIO BYMA</b>", table_header_style), Paragraph("<b>1T25</b>", table_header_style), Paragraph("<b>2T25</b>", table_header_style), Paragraph("<b>3T25</b>", table_header_style), Paragraph("<b>4T25</b>", table_header_style), Paragraph("<b>1T26</b>", table_header_style), Paragraph("<b>Var.<br/>4T25</b>", table_header_style), Paragraph("<b>Var.<br/>1T25</b>", table_header_style), Paragraph("<b>2026</b>", table_header_style), Paragraph("<b>2027</b>", table_header_style)],
        [Paragraph("<b>ÍNDICE S&P MERVAL Y RATIOS GENERALES</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("<b>Merval en USD CCL (Puntos)</b>", table_cell_bold), Paragraph("1.420", table_cell_center_bold), Paragraph("1.580", table_cell_center_bold), Paragraph("1.720", table_cell_center_bold), Paragraph("1.820", table_cell_center_bold), Paragraph("1.905", table_cell_center_bold), _badge_var("+85,0"), _badge_var("+485"), Paragraph("2.100", table_cell_center_bold), Paragraph("2.400", table_cell_center_bold)],
        [Paragraph("&nbsp;&nbsp;Volumen Operado ByMA (USD MM día)", table_cell_left), Paragraph("35,20", table_cell_center), Paragraph("42,00", table_cell_center), Paragraph("48,50", table_cell_center), Paragraph("52,40", table_cell_center), Paragraph("58,00", table_cell_center), _badge_var("+5,60"), _badge_var("+22,8"), Paragraph("65,00", table_cell_center), Paragraph("85,00", table_cell_center)],
        [Paragraph("<b>VALUACIONES DE ACCIONES LÍDERES</b>", table_cell_subhdr), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center), Paragraph("", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;YPF S.A. (EV/EBITDA x)", table_cell_left), Paragraph("4,80", table_cell_center), Paragraph("4,40", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("3,90", table_cell_center), Paragraph("3,80", table_cell_center), _badge_var("-0,10"), _badge_var("-1,00"), Paragraph("3,50", table_cell_center), Paragraph("3,20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;YPF S.A. (Margen EBITDA %)", table_cell_left), Paragraph("28,50", table_cell_center), Paragraph("30,10", table_cell_center), Paragraph("31,40", table_cell_center), Paragraph("32,00", table_cell_center), Paragraph("32,40", table_cell_center), _badge_var("+0,40"), _badge_var("+3,90"), Paragraph("34,00", table_cell_center), Paragraph("36,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Pampa Energía (EV/EBITDA x)", table_cell_left), Paragraph("5,10", table_cell_center), Paragraph("4,70", table_cell_center), Paragraph("4,40", table_cell_center), Paragraph("4,20", table_cell_center), Paragraph("4,10", table_cell_center), _badge_var("-0,10"), _badge_var("-1,00"), Paragraph("3,80", table_cell_center), Paragraph("3,50", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Pampa Energía (Margen EBITDA %)", table_cell_left), Paragraph("34,20", table_cell_center), Paragraph("36,00", table_cell_center), Paragraph("37,50", table_cell_center), Paragraph("38,00", table_cell_center), Paragraph("38,50", table_cell_center), _badge_var("+0,50"), _badge_var("+4,30"), Paragraph("40,00", table_cell_center), Paragraph("42,00", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;Grupo Financiero Galicia (EV/EBITDA)", table_cell_left), Paragraph("7,80", table_cell_center), Paragraph("7,20", table_cell_center), Paragraph("6,80", table_cell_center), Paragraph("6,40", table_cell_center), Paragraph("6,20", table_cell_center), _badge_var("-0,20"), _badge_var("-1,60"), Paragraph("5,80", table_cell_center), Paragraph("5,00", table_cell_center)],
    ]
    p14_conclusiones = [
        ("Sobreponderar Sector Energético Integrado (YPF, Pampa Energía)",
         "Cotizando con un descuento del 40% en múltiplos EV/EBITDA (3,8x a 4,1x) frente a comparables regionales de América Latina, los proyectos de transporte en Vaca Muerta y plantas de GNL transforman a estas empresas en productoras estructurales de flujo libre de caja en dólares."),
        ("Rotación Hacia Intermediación Crediticia Bancaria",
         "Con los pasivos del BCRA desmantelados, los bancos privados expanden préstamos comerciales al +14,5% real i.a., reconstruyendo márgenes netos de interés (NIM) con ratios de mora acotados (<2,5%)."),
        ("Catalizador RIGI & Expansión de Múltiplos Bursátiles",
         "La adhesión de grandes proyectos de infraestructura minera y de licuefacción proyecta un ciclo plurianual de inversión fija de capital (Capex) que consolidará la revalorización de múltiplos bursátiles hacia niveles de 6,0x EV/EBITDA.")
    ]
    elements.extend(crear_pagina_arquetipo_topchart(
        kicker_txt="RENTA VARIABLE BYMA · VALUACIÓN CORPORATIVA & MÚLTIPLOS OPERATIVOS",
        titulo="8. Sector Financiero, Renta Variable y Radar de Balances",
        leadin_txt=p14_lead,
        chart_filename="chart_editorial_equity.png",
        chart_footnote="Nota: Evolución histórica del Merval en USD y dispersión de múltiplos EV/EBITDA vs. margen operativo.",
        tabla_titulo="Valuaciones bursátiles ByMA, múltiplos EV/EBITDA y márgenes operativos",
        tabla_data=p14_tabla_data,
        tabla_col_widths=[140, 44, 44, 44, 44, 44, 45, 45, 45, 45],
        tabla_footnote="(1) Fuentes: Bolsas y Mercados Argentinos (ByMA), balances contables consolidados 1T26 presentados ante CNV y estimaciones FCE UNCUYO.",
        caja_titulo="CONCLUSIONES TÁCTICAS & ASSET ALLOCATION EN EQUITY",
        conclusiones_tacticas=p14_conclusiones,
        chart_height=205,
        kicker_color="#9A3412"
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
            f"<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Gestión de Liquidez Corporativa (30-60 días):</b> Maximizar colocaciones en Lecaps del tramo corto (TEM {_fmt1(lecap_corta)}%), complementadas con cauciones bursátiles para optimizar rendimientos diarios de caja operativa.<br/>"
            f"<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Estrategia Cambiaria y Comercio Exterior (90-180 días):</b> Coberturas selectivas mediante futuros CIP para compromisos rígidos de importación de bienes de capital e insumos.<br/>"
            f"<font name='SymFont' color='#0284C7'><b>▸</b></font> <b>Posicionamiento Soberano en Moneda Extranjera (+12 meses):</b> Sobreponderar bonos globales GD35 y GD38 (TIR: {_fmt1(gd35_tir_val)}%), capturando la aceleración del retorno total ante convergencia del EMBI+ ({fmt_num(embi_val, 0)} pb).",
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
