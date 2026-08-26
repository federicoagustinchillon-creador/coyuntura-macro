"""
================================================================================
COMPILADOR MAESTRO DE INFORME MENSUAL REPORTLAB (14 PÁGINAS EDITORIALES)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Estándar: Tier-1 Institutional Research (Goldman Sachs GIR / Bridgewater Standard)
================================================================================
"""

import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
OUT_DIR_MENSUAL = os.path.join(BASE_DIR, "06_Informes_Mensuales_OERU")
OUT_DIR_CONSOL = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
os.makedirs(OUT_DIR_MENSUAL, exist_ok=True)
os.makedirs(OUT_DIR_CONSOL, exist_ok=True)

# Registrar fuentes Georgia y Sans con fallback Windows/Linux
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

class ZeroWhitespaceCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(ZeroWhitespaceCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        left = 40
        right = 572
        header_text_y = 762
        header_line_y = 754
        footer_line_y = 30
        footer_text_y = 18

        page_bookmarks = {
            1: ("Portada Institucional", "sec_cover"),
            2: ("Índice y Metodología", "sec_toc"),
            3: ("Resumen Ejecutivo y Escenarios", "sec_exec"),
            4: ("1. Arbitraje en ARS y Breakeven", "sec_tactical"),
            5: ("2. Precios y Salarios (INDEC)", "sec_prices"),
            6: ("Cuadro 1. Aperturas IPC y Pass-Through", "sec_tab_ipc"),
            7: ("3. Nivel de Actividad General (EMAE)", "sec_emae"),
            8: ("4. Producción Sectorial en Cuyo", "sec_cuyo"),
            9: ("4.1 Comparativo Regional ISARC", "sec_regional_cuyo"),
            10: ("5. Balance BCRA y Regla de Taylor", "sec_monetary"),
            11: ("6. Curva Soberana Nelson-Siegel", "sec_yield"),
            12: ("7. Microestructura FX y Rofex", "sec_fx"),
            13: ("8. Renta Variable y Balances", "sec_equity"),
            14: ("9. Flash Normativo y Referencias", "sec_refs")
        }

        if self._pageNumber in page_bookmarks:
            title, key = page_bookmarks[self._pageNumber]
            self.bookmarkPage(key)
            self.addOutlineEntry(title, key, level=0, closed=False)

        if self._pageNumber > 1:
            self.setFont("Georgia", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, header_text_y, "INFORME DE COYUNTURA MACROECONÓMICA & MERCADO DE CAPITALES · AGOSTO 2026")
            self.drawRightString(right, header_text_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, header_line_y, right, header_line_y)

            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, footer_line_y, right, footer_line_y)

            self.setFont("Georgia", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, footer_text_y, "Federico Agustín Chillón · Lead Macro & Financial Strategist · Cs. Económicas UNCUYO")
            self.drawRightString(right, footer_text_y, f"Página {self._pageNumber} de {page_count}")

        self.restoreState()

PRIMARY    = colors.HexColor("#0B3C5D")
SECONDARY  = colors.HexColor("#328CC1")
DARK_TEXT  = colors.HexColor("#0F172A")
SLATE      = colors.HexColor("#334155")
MUTED      = colors.HexColor("#64748B")
BG_CARD    = colors.HexColor("#F8FAFC")
BORDER     = colors.HexColor("#E2E8F0")
POS        = colors.HexColor("#15803D")
NEG        = colors.HexColor("#991B1B")

def _heat_bg(v, cap=6.0):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return colors.white
    if n == 0:
        return colors.white
    frac = min(abs(n) / cap, 1.0)
    if n > 0:
        return colors.Color(1 - 0.13 * frac, 1 - 0.02 * frac, 1 - 0.13 * frac)
    return colors.Color(1 - 0.02 * frac, 1 - 0.13 * frac, 1 - 0.13 * frac)

styles = getSampleStyleSheet()

h1_style = ParagraphStyle(
    'H1_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.0, leading=16.0,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=3,
    keepWithNext=True
)

h2_style = ParagraphStyle(
    'H2_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=9.5, leading=12.5,
    textColor=PRIMARY, spaceBefore=3, spaceAfter=2,
    keepWithNext=True
)

body_style = ParagraphStyle(
    'Body_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=9.0, leading=12.2,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=2.5
)

cell_style_left = ParagraphStyle(
    'CellL_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

cell_style_center = ParagraphStyle(
    'CellC_M', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

cell_header_style = ParagraphStyle(
    'CellH_M', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.8, leading=10.2,
    alignment=TA_CENTER, textColor=colors.white
)

fig_caption = ParagraphStyle(
    'FigCaption_M', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=7.8, leading=10.0,
    alignment=TA_JUSTIFY, textColor=MUTED, spaceBefore=1, spaceAfter=2
)

def _find_image(filename):
    p = os.path.join(DIR_FIG, filename)
    if os.path.exists(p):
        return p
    p_master = os.path.join(DIR_FIG, 'master_extracted_images', filename)
    if os.path.exists(p_master):
        return p_master
    return p

def generar_informe_mensual_reportlab():
    pdf_path = os.path.join(OUT_DIR_MENSUAL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36,
        title="Informe de Coyuntura Macroeconómica & Mercado de Capitales — Agosto 2026",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Estrategia de Inversión — FCE UNCUYO",
        creator="Federico Agustín Chillón — Lead Macro & Financial Strategist",
        keywords="Macroeconomía, Finanzas, Curva Soberana, Inflación, Riesgo Sistémico, Federico Agustín Chillón, UNCUYO"
    )

    elements = []

    # =============================================================
    # PÁGINA 1: PORTADA EJECUTIVA DE ALTA GAMA (GOLDMAN SACHS GIR / WALL ST STANDARD)
    # =============================================================
    # 1. Masthead Superior Institucional Simétrico
    elements.append(HRFlowable(width="100%", thickness=2.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))
    
    masthead_table = Table([
        [
            Paragraph("<font color='#0B3C5D' size=8.0><b>UNIVERSIDAD NACIONAL DE CUYO</b></font><br/><font color='#64748B' size=7.0>FACULTAD DE CIENCIAS ECONÓMICAS · OERU</font>", ParagraphStyle('MH_L', fontName='Georgia', alignment=TA_LEFT, leading=9.5)),
            Paragraph("<font color='#0B3C5D' size=8.0><b>MACROECONOMIC RESEARCH & STRATEGY</b></font><br/><font color='#64748B' size=7.0>DIVISIÓN DE ECONOMÍA APLICADA Y MERCADOS</font>", ParagraphStyle('MH_R', fontName='Georgia', alignment=TA_RIGHT, leading=9.5))
        ]
    ], colWidths=[266, 266])
    masthead_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(masthead_table)
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=3, spaceAfter=8))

    # 2. Pill Badge de Fecha y Tipo de Publicación
    pill_data = [
        [
            Paragraph("<font color='#0284C7'>●</font>&nbsp;&nbsp;<font color='#0369A1'><b>INFORME MENSUAL DE COYUNTURA · EDICIÓN INTEGRAL (VOL. IV)</b></font>", ParagraphStyle('PB_L', fontName='Georgia', fontSize=7.5, leading=9.5)),
            Paragraph("<font color='#64748B'><b>CIERRE DE MES · AGOSTO 2026</b></font>", ParagraphStyle('PB_R', fontName='Georgia', fontSize=7.5, leading=9.5, alignment=TA_RIGHT))
        ]
    ]
    t_pill = Table(pill_data, colWidths=[360, 172])
    t_pill.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#BAE6FD")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_pill)
    elements.append(Spacer(1, 8))

    # 3. Bloque de Título Monumental
    elements.append(Paragraph("INFORME DE COYUNTURA MACROECONÓMICA & MERCADO DE CAPITALES", ParagraphStyle('Cover_T', fontName='Georgia-Bold', fontSize=15.0, leading=18.0, textColor=PRIMARY, spaceAfter=3)))
    elements.append(Paragraph("Dinámica Inflacionaria, Transmisión de Política Monetaria, Curvas Soberanas y Microestructura Cambiaria en Argentina", ParagraphStyle('Cover_ST', fontName='Georgia', fontSize=9.0, leading=12.2, textColor=colors.HexColor("#475569"), spaceAfter=10)))

    # 4. Matriz Ejecutiva de los 4 Pilares Macroeconómicos (2x2 Grid con diseño Card Flotante)
    col_w = 262
    p1 = ("<b>1. RÉGIMEN MONETARIO & PRECIOS</b><br/>"
          "<font size=7.2 color='#64748B'>• IPC Nacional: <b>1,8% m/m</b> (35,4% i.a.) | Cuyo: <b>1,7% m/m</b><br/>"
          "• Inflación núcleo en 1,5% m/m con ancla fiscal consolidada.<br/>"
          "• Tasa real neutral de Taylor ex-ante: <b>+8,5% anual</b>.</font>")

    p2 = ("<b>2. RENTA FIJA & DEUDA SOBERANA</b><br/>"
          "<font size=7.2 color='#64748B'>• Curva Nelson-Siegel hard dollar: nivel &beta;<sub>0</sub> = <b>9,40%</b><br/>"
          "• Riesgo País (EMBI) en <b>680 pb</b>; GD35 rinde <b>11,2% TIR</b>.<br/>"
          "• Lecap corta S31O6 con TEM de <b>3,24% m/m</b> (carry atractivo).</font>")

    p3 = ("<b>3. MICROESTRUCTURA CAMBIARIA</b><br/>"
          "<font size=7.2 color='#64748B'>• Dólar CCL: <b>$1.596,59</b> | Brecha mayorista: <b>7,51%</b> (5,39% BNA)<br/>"
          "• Rofex Dic-26: TNA implícita <b>38,5%</b> (prob. salto: 24,5%)<br/>"
          "• Compresión de volatilidad implícita en tramos cortos.</font>")

    p4 = ("<b>4. ACTIVIDAD & RIESGO SISTÉMICO</b><br/>"
          "<font size=7.2 color='#64748B'>• EMAE: <b>+0,6% s.e.</b> m/m; ISARC Cuyo: <b>+0,9% s.e.</b><br/>"
          "• Ratio de Absorción PCA: <b>64,2%</b> (régimen resiliente &lt;75%)<br/>"
          "• Turbulencia de Mahalanobis: <b>4,12</b> (&chi;² crítico: 11,07).</font>")

    cell_p1 = Paragraph(p1, ParagraphStyle('P1', fontName='Georgia', fontSize=7.8, leading=10.5, textColor=DARK_TEXT))
    cell_p2 = Paragraph(p2, ParagraphStyle('P2', fontName='Georgia', fontSize=7.8, leading=10.5, textColor=DARK_TEXT))
    cell_p3 = Paragraph(p3, ParagraphStyle('P3', fontName='Georgia', fontSize=7.8, leading=10.5, textColor=DARK_TEXT))
    cell_p4 = Paragraph(p4, ParagraphStyle('P4', fontName='Georgia', fontSize=7.8, leading=10.5, textColor=DARK_TEXT))

    grid_matrix = Table([
        [cell_p1, cell_p2],
        [cell_p3, cell_p4]
    ], colWidths=[col_w, col_w])
    grid_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(grid_matrix)
    elements.append(Spacer(1, 9))

    # 5. Tarjeta de Tesis Central y Dictamen Estratégico (Con barra lateral Oxford Navy)
    tesis_text = (
        "<b>DIAGNÓSTICO EJECUTIVO & TESIS CENTRAL DE MERCADO</b><br/>"
        "La economía argentina transita una fase de consolidación de su ancla nominal y desaceleración inflacionaria "
        "(IPC en 1,8% m/m), respaldada por el equilibrio fiscal primario y financiero del Sector Público Nacional. "
        "En el frente financiero, la curva soberana en USD normaliza su pendiente forward instantánea con un EMBI en torno a 680 pb, "
        "mientras que la brecha cambiaria CCL se estabiliza en 7,51% y las métricas de acoplamiento multivariado "
        "(Ratio de Absorción en 64,2% y Turbulencia en 4,12) confirman un <b>régimen de mercado resiliente</b>. "
        "En este contexto, la estrategia de asignación de activos pondera un <b>40% en Lecaps cortas (carry trade)</b>, "
        "un <b>30% en Globales hard dollar (GD35/GD38 por convexidad)</b>, un <b>15% en Boncer</b>, un <b>10% en Bopreal Serie 3</b> "
        "y un <b>5% táctico en Renta Variable energética</b>."
    )
    t_tesis = Table([
        [Paragraph(tesis_text, ParagraphStyle('TesisP', fontName='Georgia', fontSize=8.5, leading=11.6, textColor=DARK_TEXT))]
    ], colWidths=[532])
    t_tesis.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 3.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_tesis)
    elements.append(Spacer(1, 10))

    # 6. Tarjeta de Autoría y Metadatos Institucionales de Cierre de Portada
    meta_box = [
        [
            Paragraph("<b>LEAD MACRO STRATEGIST</b><br/><font color='#0B3C5D' size=8.2><b>Federico Agustín Chillón</b></font><br/><font color='#64748B' size=6.8>Investigador & Estratega Financiero</font>", ParagraphStyle('M1', fontName='Georgia', fontSize=7.4, leading=9.8)),
            Paragraph("<b>FILIACIÓN INSTITUCIONAL</b><br/><font color='#0B3C5D' size=8.2><b>Facultad de Ciencias Económicas</b></font><br/><font color='#64748B' size=6.8>Universidad Nacional de Cuyo (UNCUYO)</font>", ParagraphStyle('M2', fontName='Georgia', fontSize=7.4, leading=9.8)),
            Paragraph("<b>ESPECIFICACIÓN TÉCNICA</b><br/><font color='#0B3C5D' size=8.2><b>Cierre Mensual · Agosto 2026</b></font><br/><font color='#64748B' size=6.8>Modelos Econométricos & 300 DPI HD</font>", ParagraphStyle('M3', fontName='Georgia', fontSize=7.4, leading=9.8))
        ]
    ]
    t_meta = Table(meta_box, colWidths=[177, 178, 177])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    # 4. Matriz Ejecutiva de los 4 Pilares Macroeconómicos
    pilar_tasas = (
        "<font color='#0B3C5D'><b>1. TASAS & ARBITRAJE EN ARS</b></font><br/>"
        "La tasa fija en Lecaps cortas (S31O6 en 2,95% TEM) otorga un premio de +95 pb reales ex-ante sobre la inflación esperada del REM (2,00%). Con un breakeven implícito de 2,86% mensual, la estrategia óptima maximiza exposición en el tramo corto para capturar el carry trade real sin riesgo de duration."
    )
    pilar_precios = (
        "<font color='#0B3C5D'><b>2. PRECIOS & CONVERGENCIA</b></font><br/>"
        "El IPC Nacional registró 2,2% MoM (Mendoza DEIE: 2,3%), traccionado por regulados (3,0%) y servicios (2,9%). El ancla cambiaria y el orden fiscal contienen a los bienes transables en 1,9% MoM. La Canasta Básica Total mendocina se ubicó en $963.000, con el RIPTE formal avanzando +2,4% en el año."
    )
    pilar_soberano = (
        "<font color='#0B3C5D'><b>3. CURVA SOBERANA EN USD</b></font><br/>"
        "El ajuste paramétrico Nelson-Siegel (R²=0,984) ubica el nivel asintótico β₀ en 9,40%. La compresión del riesgo país hacia 506 pb reduce el costo de fondeo y convalida extender duration en Globales largos (GD35/GD38), que ofrecen una convexidad superior a 33x ante compresión de spreads."
    )
    pilar_regional = (
        "<font color='#0B3C5D'><b>4. ACTIVIDAD Y CUYO (ISARC)</b></font><br/>"
        "El EMAE consolidó un alza interanual de +3,1%, liderado por minería e hidrocarburos (+14,2%). El Indicador Sintético Regional (ISARC) muestra a San Luis expandiéndose al +5,8% i.a. por tracción industrial y construcción (+14,2%), seguido por Mendoza (+3,4%) y San Juan (+2,1%)."
    )

    pilar_p_style = ParagraphStyle('PilP', fontName='Georgia', fontSize=7.2, leading=9.8, textColor=DARK_TEXT, alignment=TA_JUSTIFY)
    pilares_table_data = [
        [Paragraph(pilar_tasas, pilar_p_style), Paragraph(pilar_precios, pilar_p_style)],
        [Paragraph(pilar_soberano, pilar_p_style), Paragraph(pilar_regional, pilar_p_style)]
    ]
    t_pilares = Table(pilares_table_data, colWidths=[261, 261])
    t_pilares.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.6, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6.5),
        ('LEFTPADDING', (0,0), (-1,-1), 7.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 7.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINELEFT', (0,0), (0,0), 2.5, PRIMARY),
        ('LINELEFT', (1,0), (1,0), 2.5, SECONDARY),
        ('LINELEFT', (0,1), (0,1), 2.5, colors.HexColor("#0D5C46")),
        ('LINELEFT', (1,1), (1,1), 2.5, colors.HexColor("#722F37")),
    ]))
    elements.append(t_pilares)
    elements.append(Spacer(1, 10))

    # 5. Tesis Estratégica Central (Card Elegante)
    tesis_content = (
        "<font color='#0B3C5D'><b>TESIS ESTRATÉGICA PARA COMITÉS DE INVERSIÓN:</b></font> "
        "La combinación de superávit fiscal primario y absorción monetaria cuasifiscal mediante Lefi ($29,3 billones) mantiene ancladas las expectativas cambiarias y reduce la volatilidad implícita en Rofex (35,2% TNA). "
        "En este régimen de transición, la asignación táctica óptima consiste en capturar rendimientos reales en pesos en Lecaps cortas (S31O6) mientras se mantiene sobreponderación en bonos globales GD35/GD38 para maximizar el retorno total ante la normalización del crédito soberano internacional."
    )
    t_tesis_card = Table([[Paragraph(tesis_content, ParagraphStyle('TC_P', fontName='Georgia', fontSize=7.4, leading=10.2, textColor=SLATE, alignment=TA_JUSTIFY))]], colWidths=[532])
    t_tesis_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (-1,-1), 3.0, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 6.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6.0),
        ('LEFTPADDING', (0,0), (-1,-1), 8.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 8.0),
    ]))
    elements.append(t_tesis_card)
    elements.append(Spacer(1, 10))

    # 6. Bloque de Firma de Autor y Filiación Formal
    autor_signature_table = Table([
        [
            Paragraph("<font color='#0B3C5D' size=8.0><b>Federico Agustín Chillón</b></font><br/><font color='#64748B' size=7.0>Lead Quantitative Macro & Financial Strategist<br/>Facultad de Ciencias Económicas — Universidad Nacional de Cuyo</font>", ParagraphStyle('SigL', fontName='Georgia', leading=9.5)),
            Paragraph("<font color='#64748B' size=7.0><b>Repositorio Oficial & Pipelines:</b><br/>github.com/federicoagustinchillon-creador/coyuntura-macro<br/>Mendoza, Argentina · Agosto de 2026</font>", ParagraphStyle('SigR', fontName='Georgia', alignment=TA_RIGHT, leading=9.5))
        ]
    ], colWidths=[280, 252])
    autor_signature_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.6, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(autor_signature_table)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 2: ÍNDICE GENERAL INTERACTIVO (CON ENLACES) Y GLOSARIO
    # =============================================================
    elements.append(Paragraph("Índice General y Estructura del Informe", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))

    toc_entries = [
        ("CAT", "RESUMEN EJECUTIVO & ESCENARIOS", "", ""),
        ("MAIN", "Resumen Ejecutivo, Matriz de Escenarios y Asignación de Carteras", "3", "sec_exec"),
        ("CAT", "CUERPO DEL INFORME", "", ""),
        ("MAIN", "1. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones", "4", "sec_tactical"),
        ("MAIN", "2. Dinámica de Precios, Canastas Básicas y Salario Real", "5", "sec_prices"),
        ("SUB", "Cuadro 1. Índice de Precios al Consumidor (IPC INDEC y DEIE Mendoza)", "6", "sec_tab_ipc"),
        ("MAIN", "3. Nivel de Actividad Económica General (EMAE)", "7", "sec_emae"),
        ("MAIN", "4. Desagregación Sectorial y Producción en Cuyo (INV, Petróleo, Cemento)", "8", "sec_cuyo"),
        ("SUB", "4.1. Comparativo Regional: Índice Sintético de Actividad (Mendoza, San Juan, San Luis)", "9", "sec_regional_cuyo"),
        ("MAIN", "5. Balance del BCRA, Pasivos Cuasifiscales y Brecha de Taylor", "10", "sec_monetary"),
        ("MAIN", "6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel", "11", "sec_yield"),
        ("SUB", "Cuadro 2. Parámetros del modelo Nelson-Siegel y rendimientos de mercado", "11", "sec_yield"),
        ("MAIN", "7. Microestructura Cambiaria, Futuros Rofex y Probabilidades Implícitas", "12", "sec_fx"),
        ("MAIN", "8. Sector Financiero, Renta Variable y Radar de Balances", "13", "sec_equity"),
        ("CAT", "ANEXO & CIERRE", "", ""),
        ("MAIN", "9. Flash Normativo, Contexto Internacional y Referencias APA 7ma", "14", "sec_refs")
    ]

    toc_table_data = []
    for typ, text, page, anchor in toc_entries:
        if typ == "CAT":
            p_t = Paragraph(f"<b>{text}</b>", ParagraphStyle('TOCCat', fontName='Georgia-Bold', fontSize=7.2, leading=10, textColor=MUTED, spaceBefore=1, spaceAfter=1))
            toc_table_data.append([p_t, "", ""])
        elif typ == "MAIN":
            p_t = Paragraph(f'<a href="#{anchor}" color="#0B3C5D"><b>{text}</b></a>', ParagraphStyle('TOCMain', fontName='Georgia-Bold', fontSize=7.6, leading=10.5, textColor=PRIMARY))
            p_dots = Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", ParagraphStyle('TOCDots', fontName='Georgia', fontSize=6.8, textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER))
            p_p = Paragraph(f'<a href="#{anchor}" color="#0B3C5D"><b>{page}</b></a>', ParagraphStyle('TOCPage', fontName='Georgia-Bold', fontSize=7.6, leading=10.5, alignment=TA_RIGHT, textColor=PRIMARY))
            toc_table_data.append([p_t, p_dots, p_p])
        elif typ == "SUB":
            p_t = Paragraph(f'<a href="#{anchor}" color="#1E293B">{text}</a>', ParagraphStyle('TOCSub', fontName='Georgia', fontSize=7.2, leading=9.8, leftIndent=10, textColor=DARK_TEXT))
            p_dots = Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", ParagraphStyle('TOCDots', fontName='Georgia', fontSize=6.8, textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER))
            p_p = Paragraph(f'<a href="#{anchor}" color="#334155">{page}</a>', ParagraphStyle('TOCPageS', fontName='Georgia', fontSize=7.2, leading=9.8, alignment=TA_RIGHT, textColor=SLATE))
            toc_table_data.append([p_t, p_dots, p_p])

    toc_table = Table(toc_table_data, colWidths=[300, 182, 50])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.8),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(toc_table)
    elements.append(Spacer(1, 4))

    metodologia_box = Table([
        [Paragraph("<b>CRITERIOS METODOLÓGICOS, MODELOS ECONOMÉTRICOS Y FUENTES</b>", ParagraphStyle('MH', fontName='Georgia-Bold', fontSize=7.8, textColor=PRIMARY))],
        [Paragraph("• <b>Jerarquía por Importancia Relativa:</b> El análisis prioriza los componentes de mayor incidencia macroeconómica (precios regulados sobre estacionales, transables sobre no transables, y deuda soberana sobre derivados).<br/>• <b>Fuentes Oficiales Consolidadas:</b> Series provistas por INDEC, DEIE Mendoza, Banco Central de la República Argentina (BCRA), Instituto Nacional de Vitivinicultura (INV), Secretaría de Energía y Bolsas y Mercados Argentinos (ByMA).<br/>• <b>Modelos Aplicados:</b> Ajuste paramétrico continuo de curva spot y forward bajo Nelson-Siegel (1987), Regla de Taylor con tasa real ex-ante (1993) y cálculo de Breakeven Inflacionario implícito de mercado.", ParagraphStyle('MB', fontName='Georgia', fontSize=7.0, leading=9.2, textColor=SLATE))]
    ], colWidths=[532])
    metodologia_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER),
        ('LINELEFT', (0,0), (-1,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(metodologia_box)
    elements.append(Spacer(1, 4))

    glosario_data = [
        [Paragraph("<b>Abreviatura</b>", cell_header_style), Paragraph("<b>Definición / Concepto</b>", cell_header_style), Paragraph("<b>Uso en el Informe</b>", cell_header_style)],
        [Paragraph("<b>TEM / TNA</b>", cell_style_left), Paragraph("Tasa Efectiva Mensual / Tasa Nominal Anual.", cell_style_left), Paragraph("Rendimientos en letras del Tesoro (Lecaps).", cell_style_left)],
        [Paragraph("<b>Lefi</b>", cell_style_left), Paragraph("Letras Fiscales de Liquidez emitidas por el Tesoro.", cell_style_left), Paragraph("Instrumento de esterilización bancaria cuasifiscal.", cell_style_left)],
        [Paragraph("<b>EMAE</b>", cell_style_left), Paragraph("Estimador Mensual de Actividad Económica (INDEC).", cell_style_left), Paragraph("Indicador de ciclo y tendencia del PIB real.", cell_style_left)],
        [Paragraph("<b>ISARC</b>", cell_style_left), Paragraph("Indicador Sintético de Actividad Regional de Cuyo.", cell_style_left), Paragraph("Índice ponderado provincial (Vino, Petróleo, Cemento).", cell_style_left)],
        [Paragraph("<b>EMBI+</b>", cell_style_left), Paragraph("Emerging Markets Bond Index (J.P. Morgan).", cell_style_left), Paragraph("Riesgo país y spread soberano en USD.", cell_style_left)]
    ]
    t_glo = Table(glosario_data, colWidths=[75, 225, 232])
    t_glo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_glo)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 3: RESUMEN EJECUTIVO, MATRIZ DE ESCENARIOS Y CARTERAS
    # =============================================================
    elements.append(Paragraph("Resumen Ejecutivo, Matriz de Escenarios y Asignación Táctica", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El diagnóstico macroeconómico al cierre de agosto de 2026 confirma la vigencia y efectividad del ancla fiscal y monetaria. La convergencia inflacionaria hacia el 2% mensual (IPC INDEC: 2,2% MoM vs. Mendoza DEIE: 2,3% MoM) estuvo liderada por el reacomodamiento de <b>precios regulados (3,0% MoM)</b> y <b>servicios privados (2,9% MoM)</b>, que explicaron la mayor incidencia alcista, compensados por la estabilidad en <b>bienes transables (1,9% MoM)</b> y la <b>inflación núcleo (1,9% MoM)</b>. En el frente monetario, la tasa real ex-ante (+0,95% mensual TEM Lecap vs. REM) opera como barrera contra la dolarización de carteras, sustentada en la absorción del Tesoro mediante Lefi ($29,3 billones) y el equilibrio presupuestario primario.",
        body_style
    ))
    elements.append(Paragraph(
        "En el plano sociopolítico y distributivo, la estabilidad cambiaria convive con tensiones en el ingreso disponible: el salario real formal (RIPTE) alcanza 84,4 puntos (+2,4% acumulado en 2026), pero el sector no registrado enfrenta una pérdida de poder de compra superior al 18% respecto a 2023. La Canasta Básica Total en Mendoza ($963.000) exige ingresos crecientes para superar el umbral de pobreza, mientras el endeudamiento de los hogares en créditos de consumo exhibe una mora del 17,2%. A nivel soberano, la compresión del EMBI+ hacia 506 pb reduce el costo de fondeo y habilita la rotación de carteras hacia tramos medios-largos de Globales con elevado potencial de revalorización de capital.",
        body_style
    ))
    elements.append(Spacer(1, 2))

    elements.append(Paragraph("<b>Matriz de Escenarios Macroeconómicos a 12 Meses:</b>", h2_style))

    escenarios_table_data = [
        [
            Paragraph("<b>Escenario</b>", cell_header_style),
            Paragraph("<b>Prob.</b>", cell_header_style),
            Paragraph("<b>Dólar CCL (Dic-26)</b>", cell_header_style),
            Paragraph("<b>Inflación 2026</b>", cell_header_style),
            Paragraph("<b>TIR GD30 Esperada</b>", cell_header_style),
            Paragraph("<b>Estrategia Recomendada</b>", cell_header_style)
        ],
        [
            Paragraph("<b>Base (Continuidad)</b>", cell_style_left),
            Paragraph("60%", cell_style_center),
            Paragraph("$1.750 - $1.850", cell_style_center),
            Paragraph("28% - 32% anual", cell_style_center),
            Paragraph("9,50% (Upside +12%)", cell_style_center),
            Paragraph("Carry en Lecaps cortas (S31O6) + sobreponderar tramo GD35/GD38.", cell_style_left)
        ],
        [
            Paragraph("<b>Bull (Salida de Cepo)</b>", cell_style_left),
            Paragraph("25%", cell_style_center),
            Paragraph("$1.620 - $1.700", cell_style_center),
            Paragraph("20% - 25% anual", cell_style_center),
            Paragraph("7,80% (Upside +28%)", cell_style_center),
            Paragraph("Máxima exposición a Globales largos y acciones energéticas (YPF, PAMP).", cell_style_left)
        ],
        [
            Paragraph("<b>Bear (Shock Externo)</b>", cell_style_left),
            Paragraph("15%", cell_style_center),
            Paragraph("$1.950 - $2.150", cell_style_center),
            Paragraph("40% - 48% anual", cell_style_center),
            Paragraph("13,50% (Hedge)", cell_style_center),
            Paragraph("Dolarización de liquidez en Bopreal / Boncer tramo corto.", cell_style_left)
        ]
    ]

    t_esc = Table(escenarios_table_data, colWidths=[82, 35, 85, 75, 85, 170])
    t_esc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_esc)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Guía de Asignación Táctica de Carteras (Asset Allocation Recomendado):</b>", h2_style))
    carteras_data = [
        [Paragraph("<b>Perfil de Inversor</b>", cell_header_style), Paragraph("<b>Horizonte</b>", cell_header_style), Paragraph("<b>Composición Recomendada (% Cartera)</b>", cell_header_style), Paragraph("<b>Tesis de Rendimiento / Cobertura</b>", cell_header_style)],
        [Paragraph("<b>Conservador (Treasury)</b>", cell_style_left), Paragraph("30 - 60 días", cell_style_center), Paragraph("<b>70%</b> Lecap Corta (S31O6) + <b>30%</b> Boncer TZX26", cell_style_left), Paragraph("Captura de TEM 2,95% con mínima volatilidad en pesos.", cell_style_left)],
        [Paragraph("<b>Moderado (Institucional)</b>", cell_style_left), Paragraph("90 - 180 días", cell_style_center), Paragraph("<b>40%</b> Lecap S28N6 + <b>20%</b> TZX27 + <b>25%</b> GD35/GD38 + <b>15%</b> Bopreal 3", cell_style_left), Paragraph("Balance carry real positivo con potencial compresión USD.", cell_style_left)],
        [Paragraph("<b>Agresivo (Total Return)</b>", cell_style_left), Paragraph("+12 meses", cell_style_center), Paragraph("<b>20%</b> Lecaps + <b>45%</b> Globales GD35/GD38 + <b>35%</b> Equity (YPF, PAMP, TGS)", cell_style_left), Paragraph("Maximizar convexidad soberana e inversión RIGI energética.", cell_style_left)]
    ]
    t_cart = Table(carteras_data, colWidths=[105, 65, 210, 152])
    t_cart.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_cart)
    elements.append(Spacer(1, 2.5))

    # Termómetro y Semáforo de Presión Cambiaria / Soberana
    elements.append(Paragraph("<b>Termómetro de Presión Cambiaria y Semáforo de Riesgo Soberano:</b>", h2_style))
    termometro_data = [
        [Paragraph("<b>Variable / Indicador Clave</b>", cell_header_style), Paragraph("<b>Nivel Observado</b>", cell_header_style), Paragraph("<b>Estado / Semáforo</b>", cell_header_style), Paragraph("<b>Lectura de Mercado & Vulnerabilidad</b>", cell_header_style)],
        [Paragraph("Brecha Cambiaria CCL / Oficial", cell_style_left), Paragraph("5,39% (CCL $1.596)", cell_style_center), Paragraph("<b>Baja Presión</b>", cell_style_center), Paragraph("Oferta exportadora del blend 80/20 contiene la volatilidad financiera.", cell_style_left)],
        [Paragraph("Demanda de Hedge Rofex a 30d", cell_style_left), Paragraph("35,2% TNA Implícita", cell_style_center), Paragraph("<b>Estable</b>", cell_style_center), Paragraph("Curva de futuros alineada con el crawling peg sin prima de salto.", cell_style_left)],
        [Paragraph("Spread EMBI+ Argentina (J.P. Morgan)", cell_style_left), Paragraph("506 pb (-42 pb MoM)", cell_style_center), Paragraph("<b>En Compresión</b>", cell_style_center), Paragraph("Mejora en paridades soberanas anticipa retorno a mercados voluntarios.", cell_style_left)],
        [Paragraph("Absorción Bancaria vía Lefi (Tesoro)", cell_style_left), Paragraph("$29,3 Billones", cell_style_center), Paragraph("<b>Controlado</b>", cell_style_center), Paragraph("Esterilización no monetaria sustentada en superávit fiscal primario.", cell_style_left)]
    ]
    t_ter = Table(termometro_data, colWidths=[130, 85, 75, 242])
    t_ter.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#EFF6FF")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ter)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 4: 1. ARBITRAJE EN PESOS Y BREAKEVEN
    # =============================================================
    elements.append(Paragraph("1. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El mercado de deuda en pesos refleja una marcada preferencia por el carry trade de corto plazo. La curva de Lecaps (tasa fija) opera con TEMs de entre 2,95% (30 días) y 3,40% (360 días), mientras los títulos Boncer indexados por CER rinden tasas reales positivas de entre +1,10% y +2,30% anual. A partir de esta estructura, el <b>breakeven de inflación implícita</b> se sitúa en 2,86% mensual para el tramo corto y 3,21% para el tramo anualizado.",
        body_style
    ))
    elements.append(Paragraph(
        "Dado que las expectativas del REM proyectan una inflación mensual descendente hacia el 1,75%-2,00%, la tasa fija ofrece un premio de entre 86 y 146 pb mensuales sobre la inflación esperada. La estrategia táctica óptima consiste en maximizar exposición en Lecaps cortas (S31O6 / S28N6) para capturar el diferencial de rendimiento real sin asumir el riesgo de extensión de duration.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_1_rates.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_tactica_data = [
        [Paragraph("<b>Instrumento / Especie</b>", cell_header_style), Paragraph("<b>TNA / TEM</b>", cell_header_style), Paragraph("<b>Duration / Convex.</b>", cell_header_style), Paragraph("<b>Breakeven / TIR</b>", cell_header_style), Paragraph("<b>Tesis & Ponderación Táctica</b>", cell_header_style)],
        [Paragraph("Lecap S31O6 (Oct-26)", cell_style_left), Paragraph("35,4% TNA (2,95% TEM)", cell_style_center), Paragraph("68 días · Dur: 0,18", cell_style_center), Paragraph("BE: 2,86% MoM", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Máximo carry con riesgo tasa mínimo.", cell_style_left)],
        [Paragraph("Lecap S28N6 (Nov-26)", cell_style_left), Paragraph("36,6% TNA (3,05% TEM)", cell_style_center), Paragraph("96 días · Dur: 0,26", cell_style_center), Paragraph("BE: 2,94% MoM", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Captura tasa fija antes de recortes BCRA.", cell_style_left)],
        [Paragraph("Boncer TZX27 (Dic-27)", cell_style_left), Paragraph("CER + 1,10% TIR Real", cell_style_center), Paragraph("1,4 años · Dur: 1,35", cell_style_center), Paragraph("TIR Real: +1,10%", cell_style_center), Paragraph("<b>NEUTRAL</b> · Cobertura si regulados superan el 3,5% MoM.", cell_style_left)],
        [Paragraph("Bopreal Serie 3 (USD)", cell_style_left), Paragraph("8,40% TIR en USD", cell_style_center), Paragraph("1,8 años · Dur: 1,65", cell_style_center), Paragraph("Paridad: 88,5%", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Dolarización de excedentes corporativos.", cell_style_left)]
    ]
    t_tactica = Table(tabla_tactica_data, colWidths=[105, 95, 85, 75, 172])
    t_tactica.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_tactica)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 5: 2. PRECIOS Y SALARIOS (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("2. Dinámica de Precios, Canastas Básicas y Salario Real", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "La dinámica de precios de agosto confirmó la consolidación del sendero desinflacionario nacional (2,2% MoM) y provincial (Mendoza: 2,3% MoM). Por orden de incidencia relativa, los aumentos estuvieron encabezados por los <b>precios regulados (3,0% INDEC; 3,3% DEIE)</b> y los <b>servicios privados (2,9% MoM)</b>, explicados por actualizaciones en tarifas de energía eléctrica, gas de red y transporte interurbano en Cuyo. Como contrapartida, los <b>bienes transables (1,9% MoM)</b> y los <b>alimentos (1,8% MoM)</b> actuaron como anclas de convergencia.",
        body_style
    ))
    elements.append(Paragraph(
        "En el plano social, la valorización de las canastas en Mendoza sitúa la Canasta Básica Alimentaria (CBA) en $433.000 y la Total (CBT) en $963.000 para una familia tipo. Aunque el salario real registrado (RIPTE) acumula una mejora del 2,4% en el año, la heterogeneidad en el mercado laboral presiona el consumo de bienes no transables y sostiene la demanda de financiamiento para gastos corrientes.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_2_ipc.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_social_data = [
        [Paragraph("<b>Indicador Social / Canasta (Mendoza)</b>", cell_header_style), Paragraph("<b>Valor Ago-26</b>", cell_header_style), Paragraph("<b>Variación MoM</b>", cell_header_style), Paragraph("<b>Cobertura / Brecha de Ingresos</b>", cell_header_style)],
        [Paragraph("Canasta Básica Alimentaria (CBA Mendoza)", cell_style_left), Paragraph("$433.000", cell_style_center), Paragraph("+1,8% MoM", cell_style_center), Paragraph("Línea de Indigencia · Requiere 1,2 salarios mínimos informales.", cell_style_left)],
        [Paragraph("Canasta Básica Total (CBT Mendoza)", cell_style_left), Paragraph("$963.000", cell_style_center), Paragraph("+2,3% MoM", cell_style_center), Paragraph("Línea de Pobreza · Brecha del 18% frente a ingresos no registrados.", cell_style_left)],
        [Paragraph("Salario Real Formal (RIPTE)", cell_style_left), Paragraph("84,4 pts", cell_style_center), Paragraph("+0,3% MoM", cell_style_center), Paragraph("+2,4% acum. vs. Dic-2023 · Cobertura del 100% de la CBT.", cell_style_left)],
        [Paragraph("Mora en Créditos de Consumo (Fintech)", cell_style_left), Paragraph("17,2%", cell_style_center), Paragraph("+0,8 pp MoM", cell_style_center), Paragraph("Tensión en financiamiento de gastos corrientes en familias.", cell_style_left)]
    ]
    t_soc = Table(tabla_social_data, colWidths=[172, 75, 75, 210])
    t_soc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_soc)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 6: CUADRO 1 (TABLA IPC Y TRANSMISIÓN COMPLETA)
    # =============================================================
    elements.append(Paragraph("Cuadro 1. Índice de Precios al Consumidor (IPC) y Canales de Transmisión", h1_style))
    elements.append(Paragraph("<i>Variación mensual, acumulada e interanual según aperturas por orden de incidencia relativa. Agosto de 2026, en porcentaje.</i>", ParagraphStyle('ST', fontName='Georgia-Italic', fontSize=7.5, textColor=MUTED, spaceAfter=4)))

    tabla_ipc_data = [
        [
            Paragraph("<b>Apertura / Jurisdicción</b>", cell_header_style),
            Paragraph("<b>Mensual (Ago-26)</b>", cell_header_style),
            Paragraph("<b>Acum. 2026 (8 meses)</b>", cell_header_style),
            Paragraph("<b>Interanual (i.a.)</b>", cell_header_style)
        ],
        [Paragraph("<b>Precios Regulados (Mayor Incidencia)</b>", cell_style_left), Paragraph("3,0%", cell_style_center), Paragraph("29,1%", cell_style_center), Paragraph("48,4%", cell_style_center)],
        [Paragraph("Servicios (INDEC)", cell_style_left), Paragraph("2,9%", cell_style_center), Paragraph("24,8%", cell_style_center), Paragraph("41,2%", cell_style_center)],
        [Paragraph("Provincia de Mendoza (DEIE General)", cell_style_left), Paragraph("2,3%", cell_style_center), Paragraph("19,4%", cell_style_center), Paragraph("32,8%", cell_style_center)],
        [Paragraph("  Vivienda, agua, electricidad y gas (DEIE)", cell_style_left), Paragraph("3,3%", cell_style_center), Paragraph("33,2%", cell_style_center), Paragraph("54,1%", cell_style_center)],
        [Paragraph("  Transporte y comunicaciones (DEIE)", cell_style_left), Paragraph("2,7%", cell_style_center), Paragraph("26,4%", cell_style_center), Paragraph("43,8%", cell_style_center)],
        [Paragraph("Nivel General Nacional (INDEC)", cell_style_left), Paragraph("2,2%", cell_style_center), Paragraph("18,5%", cell_style_center), Paragraph("31,4%", cell_style_center)],
        [Paragraph("IPC Núcleo (INDEC)", cell_style_left), Paragraph("1,9%", cell_style_center), Paragraph("15,9%", cell_style_center), Paragraph("26,5%", cell_style_center)],
        [Paragraph("Bienes (INDEC)", cell_style_left), Paragraph("1,9%", cell_style_center), Paragraph("16,2%", cell_style_center), Paragraph("28,0%", cell_style_center)],
        [Paragraph("  Alimentos y bebidas (DEIE Mendoza)", cell_style_left), Paragraph("1,8%", cell_style_center), Paragraph("15,1%", cell_style_center), Paragraph("25,4%", cell_style_center)],
        [Paragraph("Estacionales (INDEC)", cell_style_left), Paragraph("1,4%", cell_style_center), Paragraph("12,4%", cell_style_center), Paragraph("21,0%", cell_style_center)]
    ]

    t_ipc = Table(tabla_ipc_data, colWidths=[232, 100, 100, 100])
    t_ipc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#FEE2E2")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#EFF6FF")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,7), (-1,7), colors.white),
        ('BACKGROUND', (0,8), (-1,8), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,9), (-1,9), colors.white),
        ('BACKGROUND', (0,10), (-1,10), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ipc)
    elements.append(Spacer(1, 2.5))
    elements.append(Paragraph("<i>Fuente:</i> INDEC y DEIE Mendoza. Ordenado por incidencia decreciente.", fig_caption))
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Canales de Transmisión y Elasticidad de Pass-Through a Precios:</b>", h2_style))
    tabla_passthrough_data = [
        [Paragraph("<b>Canal de Transmisión / Rubro</b>", cell_header_style), Paragraph("<b>Incidencia en IPC (pp)</b>", cell_header_style), Paragraph("<b>Elasticidad / Pass-Through</b>", cell_header_style), Paragraph("<b>Implicancia para Empresas y Consumo</b>", cell_header_style)],
        [Paragraph("Tarifas de Electricidad y Gas de Red", cell_style_left), Paragraph("+0,65 pp", cell_style_center), Paragraph("Directo (100% regulado)", cell_style_center), Paragraph("Aumento en costos fijos de PyMEs industriales y riego agrícola.", cell_style_left)],
        [Paragraph("Combustibles y Fletes Interurbanos", cell_style_left), Paragraph("+0,48 pp", cell_style_center), Paragraph("Rápido (60% a 30 días)", cell_style_center), Paragraph("Presión en logística de bodegas y distribución de alimentos.", cell_style_left)],
        [Paragraph("Alimentos Secos y Productos de Almacén", cell_style_left), Paragraph("+0,42 pp", cell_style_center), Paragraph("Moderado (anclado por FX)", cell_style_center), Paragraph("Migración del consumidor hacia segundas y terceras marcas.", cell_style_left)],
        [Paragraph("Indumentaria y Calzado", cell_style_left), Paragraph("+0,12 pp", cell_style_center), Paragraph("Bajo (competencia importada)", cell_style_center), Paragraph("Caída en márgenes comerciales por necesidad de liquidar stock.", cell_style_left)]
    ]
    t_pt = Table(tabla_passthrough_data, colWidths=[162, 85, 95, 190])
    t_pt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_pt)
    elements.append(Spacer(1, 2.5))

    analisis_pt_box = Table([
        [Paragraph("<b>EVALUACIÓN EMPÍRICA DE LA DISPERSIÓN DE PRECIOS RELATIVOS</b>", ParagraphStyle('PTH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph("La divergencia entre la variación de bienes (1,9% MoM) y servicios/regulados (3,0% MoM) ratifica que el proceso desinflacionario transita su fase de corrección de precios relativos. La estabilidad cambiaria funciona como ancla para los transables, mientras las tarifas absorben el retraso acumulado del período 2019-2023. Para las tesorerías corporativas, la estabilidad del tipo de cambio mayorista y la compresión del IPIM (1,4% MoM) permiten proyectar un alivio en costos de reposición hacia el cuarto trimestre de 2026.", ParagraphStyle('PTB', fontName='Georgia', fontSize=6.8, leading=9.0, textColor=SLATE))]
    ], colWidths=[532])
    analisis_pt_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (-1,-1), 2.5, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(analisis_pt_box)
    elements.append(Spacer(1, 2.5))

    # Conclusiones Microsectoriales de Fijación de Precios
    micro_pricing_box = Table([
        [Paragraph("<b>DIRECTRICES DE PRICING Y POLÍTICA DE STOCKS PARA EMPRESAS</b>", ParagraphStyle('MPH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph("• <b>Comercio Mayorista y Retail:</b> Se recomienda rotación rápida de inventarios sobre márgenes unitarios, evitando acumulación de stock apalancado a tasas reales del 35% TNA.<br/>• <b>Industria Agroalimentaria:</b> Aprovechar estabilidad en costos de granos para pactar compras a plazo fijo en ARS con descuento financiero superior al 3% mensual.<br/>• <b>Empresas de Servicios:</b> Incorporar cláusulas de indexación escalonadas en contratos corporativos basadas en 50% IPC Núcleo y 50% RIPTE para preservar el valor real de los honorarios.", ParagraphStyle('MPB', fontName='Georgia', fontSize=6.8, leading=9.0, textColor=DARK_TEXT))]
    ], colWidths=[532])
    micro_pricing_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('LINELEFT', (0,0), (-1,-1), 2.5, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(micro_pricing_box)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 7: 3. ACTIVIDAD EMAE (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("3. Estimador Mensual de Actividad Económica (EMAE)", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El Estimador Mensual de Actividad Económica (EMAE) creció 3,1% en la comparación interanual y avanzó 0,6% en su medición desestacionalizada respecto al mes previo. La tendencia-ciclo consolidó una tasa positiva de 0,4% mensual, ratificando la superación del piso de actividad registrado durante el primer trimestre de 2026. La reactivación económica exhibe un patrón asimétrico traccionado principalmente por los sectores transables y exportadores.",
        body_style
    ))
    elements.append(Paragraph(
        "Por orden de dinamismo, la <b>minería e hidrocarburos (+14,2% i.a.)</b> y el <b>agro (+8,5% i.a.)</b> encabezan la expansión, mientras que el <b>comercio minorista (-1,8% i.a.)</b> y la <b>industria manufacturera no vinculada a energía (-0,5% i.a.)</b> acumulan los mayores rezagos relativos. Este comportamiento responde a la recomposición gradual del ingreso disponible en un entorno de disciplina fiscal.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_emae_master.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_semaforo_data = [
        [Paragraph("<b>Sector / Rama de Actividad (INDEC)</b>", cell_header_style), Paragraph("<b>Variación i.a.</b>", cell_header_style), Paragraph("<b>Variación MoM Desest.</b>", cell_header_style), Paragraph("<b>Fase del Ciclo / Driver Principal</b>", cell_header_style)],
        [Paragraph("Explotación de Minas y Canteras (O&G)", cell_style_left), Paragraph("+14,2% i.a.", cell_style_center), Paragraph("+1,4% MoM", cell_style_center), Paragraph("<b>Expansión Fuerte</b> · Récord de shale oil y gasoductos.", cell_style_left)],
        [Paragraph("Agricultura, Ganadería y Caza", cell_style_left), Paragraph("+8,5% i.a.", cell_style_center), Paragraph("+0,8% MoM", cell_style_center), Paragraph("<b>Recuperación</b> · Cosecha récord y liquidación de granos.", cell_style_left)],
        [Paragraph("Intermediación Financiera y Seguros", cell_style_left), Paragraph("+4,2% i.a.", cell_style_center), Paragraph("+0,5% MoM", cell_style_center), Paragraph("<b>Crecimiento</b> · Expansión de créditos corporativos en ARS.", cell_style_left)],
        [Paragraph("Construcción y Despacho de Insumos", cell_style_left), Paragraph("+0,6% i.a.", cell_style_center), Paragraph("+0,3% MoM", cell_style_center), Paragraph("<b>Estabilización</b> · Impulso privado compensa freno en obra pública.", cell_style_left)],
        [Paragraph("Comercio Mayorista y Minorista", cell_style_left), Paragraph("-1,8% i.a.", cell_style_center), Paragraph("+0,1% MoM", cell_style_center), Paragraph("<b>Rezagado</b> · Recuperación lenta en ventas de consumo masivo.", cell_style_left)]
    ]
    t_sem = Table(tabla_semaforo_data, colWidths=[165, 75, 95, 197])
    t_sem.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,3), (-1,3), colors.white),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#FEE2E2")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sem)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 8: 4. SECTORES CUYO (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("4. Desagregación Sectorial y Producción en Mendoza y Cuyo", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "La estructura productiva de Mendoza exhibe desempeños asimétricos según orientación de mercado. En la industria vitivinícola, los despachos informados por el Instituto Nacional de Vitivinicultura (INV) alcanzaron 68,5 mil hectolitros (+3,2% MoM), impulsados en un 73% por <b>vinos fraccionados (50,1 mil hl)</b> de mayor valor agregado, frente a <b>18,4 mil hl a granel</b>.",
        body_style
    ))
    elements.append(Paragraph(
        "En hidrocarburos, la producción total en la cuenca cuyana alcanzó 212 mil m³ mensuales, explicada por <b>182 mil m³ de extracción convencional</b> y un aporte creciente de <b>30 mil m³ en Vaca Muerta mendocina</b> bajo proyectos adheridos al RIGI. Por su parte, los despachos de cemento portland (AFCP) operaron en 100,4 puntos base, reflejando reactivación en la obra privada.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_3_cuyo.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_cadenas_data = [
        [Paragraph("<b>Cadena de Valor / Complejo (Cuyo)</b>", cell_header_style), Paragraph("<b>Volumen Ago-26</b>", cell_header_style), Paragraph("<b>Participación %</b>", cell_header_style), Paragraph("<b>Impacto Fiscal, Empleo & Inversión</b>", cell_header_style)],
        [Paragraph("Vino Fraccionado (INV)", cell_style_left), Paragraph("50,1 mil hl", cell_style_center), Paragraph("73,1% del total", cell_style_center), Paragraph("Generador del 65% del empleo agroindustrial en el Oasis Central.", cell_style_left)],
        [Paragraph("Vino a Granel y Mostos (INV)", cell_style_left), Paragraph("18,4 mil hl", cell_style_center), Paragraph("26,9% del total", cell_style_center), Paragraph("Regulador de stocks y exportación de commoditized wine.", cell_style_left)],
        [Paragraph("Petróleo Convencional Cuenca Cuyana", cell_style_left), Paragraph("182 mil m³", cell_style_center), Paragraph("85,8% provincial", cell_style_center), Paragraph("Base de recaudación de regalías hidrocarburíferas para ATM.", cell_style_left)],
        [Paragraph("Vaca Muerta Mendocina (Malargüe)", cell_style_left), Paragraph("30 mil m³", cell_style_center), Paragraph("14,2% provincial", cell_style_center), Paragraph("Proyectos RIGI en fractura hidráulica con proyección duplicada a 2027.", cell_style_left)],
        [Paragraph("Cemento Portland (AFCP Cuyo)", cell_style_left), Paragraph("100,4 pts (Base 100)", cell_style_center), Paragraph("+0,6% MoM", cell_style_center), Paragraph("Tracción por obras residenciales y desarrollos inmobiliarios privados.", cell_style_left)]
    ]
    t_cad = Table(tabla_cadenas_data, colWidths=[155, 80, 85, 212])
    t_cad.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_cad)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 9: 4.1 COMPARATIVO REGIONAL CUYO (MENDOZA / SAN JUAN / SAN LUIS)
    # =============================================================
    elements.append(Paragraph("4.1. Comparativo Regional: Índice Sintético de Actividad (ISARC)", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "La sección anterior desagregó la producción de Mendoza; esta sección completa la lectura regional de Cuyo incorporando San Juan y San Luis a través del <b>Índice Sintético de Actividad Regional (ISARC)</b>, un índice compuesto propio (base 100 = enero 2024) que pondera nivel de actividad, industria manufacturera, construcción y empleo registrado por provincia. San Luis lidera el ritmo de expansión regional con <b>106,4 puntos (+5,8% i.a.)</b>, traccionado por una construcción que crece <b>+14,2% i.a.</b> al amparo de su régimen de promoción industrial, seguida por Mendoza en <b>104,8 puntos (+3,4% i.a.)</b> con la vitivinicultura como motor principal, y San Juan en <b>102,1 puntos (+2,1% i.a.)</b>, la de menor dinamismo relativo por la desaceleración de su construcción (-2,3% i.a.) pese a un sector minero-industrial en convergencia (+1,4% i.a.).",
        body_style
    ))
    elements.append(Paragraph(
        "La heterogeneidad intraregional es relevante para la asignación de riesgo crediticio provincial y para la lectura de recaudación de ingresos brutos: mientras Mendoza y San Luis exhiben empleo registrado en expansión (+1,2% y +3,9% i.a., respectivamente), San Juan crece a un ritmo marginal (+0,5% i.a.), consistente con una economía más concentrada en minería metalífera de ciclo de inversión más largo y menos intensiva en mano de obra formal por unidad de producto.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_3b_regional_cuyo.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("<b>Cuadro. Desagregación Provincial por Sector (Variación Interanual %):</b>", h2_style))
    regional_header = [Paragraph("<b>Provincia</b>", cell_header_style), Paragraph("<b>ISARC (nivel)</b>", cell_header_style),
                        Paragraph("<b>ISARC Var. i.a.</b>", cell_header_style), Paragraph("<b>Industria Manuf.</b>", cell_header_style),
                        Paragraph("<b>Construcción</b>", cell_header_style), Paragraph("<b>Empleo Registrado</b>", cell_header_style)]
    regional_rows = [
        ("Mendoza", 104.8, 3.4, 2.8, 5.1, 1.2),
        ("San Juan", 102.1, 2.1, 1.4, -2.3, 0.5),
        ("San Luis", 106.4, 5.8, 9.7, 14.2, 3.9),
    ]
    regional_data = [regional_header]
    heat_cmds_regional = []
    for i, (prov, isarc, isarc_ia, ind, con, emp) in enumerate(regional_rows, start=1):
        fila = [
            Paragraph(f"<b>{prov}</b>", cell_style_left),
            Paragraph(f"{isarc:.1f} pts", cell_style_center),
        ]
        for val in (isarc_ia, ind, con, emp):
            signo = "+" if val >= 0 else ""
            color = POS.hexval() if val > 0 else (NEG.hexval() if val < 0 else DARK_TEXT.hexval())
            fila.append(Paragraph(f'<font color="{color}"><b>{signo}{val:.1f}%</b></font>', cell_style_center))
        regional_data.append(fila)
        for col_idx, val in zip((2, 3, 4, 5), (isarc_ia, ind, con, emp)):
            heat_cmds_regional.append(('BACKGROUND', (col_idx, i), (col_idx, i), _heat_bg(val)))

    t_regional = Table(regional_data, colWidths=[80, 82, 90, 90, 90, 100])
    t_regional.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ] + heat_cmds_regional))
    elements.append(t_regional)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "<i>Fuentes: DEIE Mendoza, IPEC San Juan, IPEC San Luis. ISARC: índice compuesto de elaboración propia; celdas con intensidad de color proporcional a la magnitud de la variación interanual (verde: expansión, rojo: contracción).</i>",
        fig_caption
    ))

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 10: 5. BALANCE BCRA Y REGLA DE TAYLOR
    # =============================================================
    elements.append(Paragraph("5. Balance del BCRA, Pasivos Cuasifiscales y Brecha de Taylor", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El esquema monetario consolidó el saneamiento patrimonial del Banco Central mediante la total extinción de los pases pasivos remunerados ($0 B), transfiriendo la absorción de liquidez bancaria a las Letras Fiscales de Liquidez (Lefi) emitidas por el Tesoro Nacional ($29,3 billones). La Base Monetaria Ampliada se ubicó en $27,4 billones, manteniendo un estricto control sobre la expansión secundaria de dinero.",
        body_style
    ))
    elements.append(Paragraph(
        "Bajo una formulación de la Regla de Taylor con tasa real ex-ante (TEM Lecap 2,95% − REM 2,00% = +0,95% mensual), la tasa de política monetaria se sitúa 20 pb por encima de la tasa neutral estimada (r* = 0,75%). Esta brecha contractiva garantiza el anclaje de expectativas inflacionarias sin restringir la expansión del crédito comercial privado en el sistema financiero.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_4_monetary.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_rin_data = [
        [Paragraph("<b>Factor de Variación Monetaria / Balance</b>", cell_header_style), Paragraph("<b>Monto (ARS / USD)</b>", cell_header_style), Paragraph("<b>Efecto Neto</b>", cell_header_style), Paragraph("<b>Implicancia para la Estabilidad Financiera</b>", cell_header_style)],
        [Paragraph("Absorción Cuasifiscal vía Lefi (Tesoro)", cell_style_left), Paragraph("$29,3 Billones", cell_style_center), Paragraph("Contractivo", cell_style_center), Paragraph("Traslado del costo financiero al Tesoro con superávit primario.", cell_style_left)],
        [Paragraph("Base Monetaria Ampliada (Circulación + Encajes)", cell_style_left), Paragraph("$27,4 Billones", cell_style_center), Paragraph("Controlado", cell_style_center), Paragraph("Remonetización gradual en línea con la demanda transaccional.", cell_style_left)],
        [Paragraph("Pases Pasivos Remunerados BCRA", cell_style_left), Paragraph("$0,0 Billones", cell_style_center), Paragraph("Extinto", cell_style_center), Paragraph("Eliminación definitiva de la emisión por déficit cuasifiscal.", cell_style_left)],
        [Paragraph("Reservas Internacionales Netas (RIN FMI)", cell_style_left), Paragraph("USD -4.200 M", cell_style_center), Paragraph("En Recuperación", cell_style_center), Paragraph("Compras netas en el MLC compensadas por pagos de deuda soberana.", cell_style_left)]
    ]
    t_rin = Table(tabla_rin_data, colWidths=[172, 85, 75, 200])
    t_rin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_rin)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 11: 6. DEUDA SOBERANA Y MODELO NELSON-SIEGEL
    # =============================================================
    elements.append(Paragraph("6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El ajuste paramétrico de la curva soberana en moneda extranjera bajo el modelo Nelson-Siegel arrojó parámetros de nivel (β₀ = 9,40%), pendiente (β₁ = +5,60%), curvatura (β₂ = -3,20%) y parámetro de decaimiento τ = 2,40 (R² = 0,984 | RMSE = 14 bps). La curva spot presenta una pendiente positiva normalizada entre los tramos cortos (AL30 en 11,20%) y largos (GD38 en 9,70%), con la tasa forward instantánea f(t) anticipando convergencia de rendimientos hacia el 9,0% anual.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_5_sovereign.png"), width=532, height=295))
    elements.append(Spacer(1, 3))

    cuadro_2_data = [
        [
            Paragraph("<b>Parámetro / Especie</b>", cell_header_style),
            Paragraph("<b>Símbolo / Ticker</b>", cell_header_style),
            Paragraph("<b>Valor Observado</b>", cell_header_style),
            Paragraph("<b>Métricas de Ajuste & Duration</b>", cell_header_style)
        ],
        [Paragraph("Nivel de Largo Plazo", cell_style_left), Paragraph("β₀", cell_style_center), Paragraph("9,40%", cell_style_center), Paragraph("R² = 0,984 · RMSE = 14 bps", cell_style_center)],
        [Paragraph("Pendiente / Curvatura", cell_style_left), Paragraph("β₁ / β₂", cell_style_center), Paragraph("+5,60% / -3,20%", cell_style_center), Paragraph("Parámetro decaimiento τ = 2,40", cell_style_center)],
        [Paragraph("Bonar 2030 (Ley Local)", cell_style_left), Paragraph("AL30", cell_style_center), Paragraph("11,20% TIR", cell_style_center), Paragraph("Duration: 2,78 · Paridad: 69,8%", cell_style_center)],
        [Paragraph("Global 2038 (Ley NY)", cell_style_left), Paragraph("GD38", cell_style_center), Paragraph("9,70% TIR", cell_style_center), Paragraph("Duration: 5,81 · Paridad: 60,9%", cell_style_center)]
    ]
    t_c2 = Table(cuadro_2_data, colWidths=[165, 75, 95, 197])
    t_c2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), BG_CARD),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_c2)
    elements.append(Spacer(1, 3))

    tabla_stress_data = [
        [Paragraph("<b>Shock de Spread Soberano</b>", cell_header_style), Paragraph("<b>Retorno GD38 (Conv: 47,1)</b>", cell_header_style), Paragraph("<b>Retorno GD35 (Conv: 33,8)</b>", cell_header_style), Paragraph("<b>Retorno AL30 (Conv: 9,2)</b>", cell_header_style)],
        [Paragraph("Compresión -300 pb (Hacia 200 pb EMBI)", cell_style_left), Paragraph("<b>+19,55% en USD</b>", cell_style_center), Paragraph("<b>+16,67% en USD</b>", cell_style_center), Paragraph("+8,75% en USD", cell_style_center)],
        [Paragraph("Compresión -100 pb (Hacia 400 pb EMBI)", cell_style_left), Paragraph("<b>+6,05% en USD</b>", cell_style_center), Paragraph("<b>+5,22% en USD</b>", cell_style_center), Paragraph("+2,83% en USD", cell_style_center)],
        [Paragraph("Ampliación +100 pb (Hacia 600 pb EMBI)", cell_style_left), Paragraph("-5,57% en USD", cell_style_center), Paragraph("-4,88% en USD", cell_style_center), Paragraph("-2,73% en USD", cell_style_center)],
        [Paragraph("Ampliación +300 pb (Shock Externo)", cell_style_left), Paragraph("-15,31% en USD", cell_style_center), Paragraph("-13,63% en USD", cell_style_center), Paragraph("-7,93% en USD", cell_style_left)]
    ]
    t_str = Table(tabla_stress_data, colWidths=[172, 120, 120, 120])
    t_str.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#FEE2E2")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_str)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 12: 7. MICROESTRUCTURA CAMBIARIA, ROFEX Y RIESGO SISTÉMICO
    # =============================================================
    elements.append(Paragraph("7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El mercado cambiario finalizó agosto con el Dólar CCL en $1.596,59, el Dólar MEP en $1.532,33 y el Oficial BNA en $1.515,00 (brecha del 5,39% sobre el BNA y 7,51% sobre el mayorista A3500 de $1.485,00). La curva de futuros en Matba-Rofex registra una TNA implícita a 30 días del 35,2% y del 38,5% para diciembre de 2026, con una probabilidad neutral al riesgo de salto discreto del 16,8% a 90 días.",
        body_style
    ))
    elements.append(Paragraph(
        "En el plano cuantitativo de activos cruzados (Lecap, Boncer, GD30, CCL y Merval), el <b>Ratio de Absorción (AR)</b> derivado de los dos primeros componentes principales se ubica en <b>64,2%</b> (&Delta;AR = -0,40 desvíos), por debajo del umbral crítico de fragilidad del 75%. En paralelo, el <b>Índice de Turbulencia de Mahalanobis (<i>d<sub>t</sub></i>)</b> se sitúa en <b>4,12</b> frente al valor crítico Chi² al 95% de 11,07, confirmando un <b>régimen resiliente y desacoplado</b> donde la diversificación opera con normalidad.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_6_fx.png"), width=532, height=285))
    elements.append(Spacer(1, 3))

    tabla_hedge_data = [
        [Paragraph("<b>Posición / Vencimiento Rofex</b>", cell_header_style), Paragraph("<b>Precio Futuro (ARS)</b>", cell_header_style), Paragraph("<b>TNA Implícita %</b>", cell_header_style), Paragraph("<b>Prob. Salto Discreto</b>", cell_header_style), Paragraph("<b>Estrategia de Cobertura para Tesorerías</b>", cell_header_style)],
        [Paragraph("Ago-26 (30 días)", cell_style_left), Paragraph("$1.510,00", cell_style_center), Paragraph("35,2% TNA", cell_style_center), Paragraph("8,5%", cell_style_center), Paragraph("Carry trade en ARS sin cobertura ante crawling controlado.", cell_style_left)],
        [Paragraph("Dic-26 (180 días)", cell_style_left), Paragraph("$1.680,00", cell_style_center), Paragraph("38,5% TNA", cell_style_center), Paragraph("24,5%", cell_style_center), Paragraph("Cobertura preventiva (60%) ante eventual salida de cepo.", cell_style_left)],
        [Paragraph("Ago-27 (360 días)", cell_style_left), Paragraph("$1.920,00", cell_style_center), Paragraph("41,2% TNA", cell_style_center), Paragraph("34,0%", cell_style_center), Paragraph("Dolarización sintética mediante futuros + Lecaps cortas.", cell_style_left)]
    ]
    t_hdg = Table(tabla_hedge_data, colWidths=[110, 80, 75, 75, 192])
    t_hdg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_hdg)
    elements.append(Spacer(1, 2.5))

    # Scorecard de Riesgo Sistémico y Alerta Temprana (Kritzman & Li, 2010)
    scorecard_data = [
        [Paragraph("<b>Métrica Cuantitativa de Riesgo</b>", cell_header_style), Paragraph("<b>Valor Observado</b>", cell_header_style), Paragraph("<b>Umbral Crítico</b>", cell_header_style), Paragraph("<b>Diagnóstico de Régimen & Acción Preventiva</b>", cell_header_style)],
        [Paragraph("Ratio de Absorción (AR 2-PC)", cell_style_left), Paragraph("64,2%", cell_style_center), Paragraph("> 75,0% (Fragilidad)", cell_style_center), Paragraph("<b>Resiliente</b> · El riesgo no está concentrado; no requiere desarme de carry.", cell_style_left)],
        [Paragraph("Turbulencia de Mahalanobis (dt)", cell_style_left), Paragraph("4,12", cell_style_center), Paragraph("> 11,07 (Chi2 95%)", cell_style_center), Paragraph("<b>Normal</b> · Correlaciones cruzadas alineadas con la matriz histórica.", cell_style_left)],
        [Paragraph("Variación Estandarizada (Delta AR)", cell_style_left), Paragraph("-0,40 sigma", cell_style_center), Paragraph("> +1,50 sigma", cell_style_center), Paragraph("<b>Estable</b> · Sin aceleración de fragilidad en la ventana de 30 ruedas.", cell_style_left)]
    ]
    t_sc = Table(scorecard_data, colWidths=[140, 75, 95, 222])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#EFF6FF")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sc)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 13: 8. SECTOR FINANCIERO Y RENTA VARIABLE
    # =============================================================
    elements.append(Paragraph("8. Sector Financiero, Renta Variable y Radar de Balances", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "El índice S&P Merval cerró en 3.156.332 puntos (+1,30% semanal), impulsado por la solidez operativa del sector energético y bancario. En el segmento energético, <b>YPF (3,8x EV/EBITDA y margen operativo del 32,4%)</b>, <b>Pampa Energía (4,1x EV/EBITDA y Deuda Neta/EBITDA < 1,2x)</b> y <b>TGS (4,4x EV/EBITDA)</b> lideraron las preferencias del mercado gracias a la expansión de infraestructura de gasoductos y las inversiones al amparo del RIGI.",
        body_style
    ))
    elements.append(Paragraph(
        "Por su parte, las entidades financieras (Grupo Galicia, Banco Macro, BBVA Argentina) registraron avances semanales de entre 1,2% y 1,9%, favorecidas por el crecimiento del crédito corporativo y la estabilización de los márgenes de intermediación financiera en un entorno de tasas reales positivas.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_7_equity.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_equity_data = [
        [Paragraph("<b>Empresa / Ticker ByMA</b>", cell_header_style), Paragraph("<b>Múltiplo EV/EBITDA</b>", cell_header_style), Paragraph("<b>Margen EBITDA %</b>", cell_header_style), Paragraph("<b>Deuda Neta / EBITDA</b>", cell_header_style), Paragraph("<b>Catalizadores Estratégicos & RIGI</b>", cell_header_style)],
        [Paragraph("YPF S.A. (YPFD / NYSE)", cell_style_left), Paragraph("3,8x", cell_style_center), Paragraph("32,4%", cell_style_center), Paragraph("1,45x", cell_style_center), Paragraph("Liderazgo en Vaca Muerta, desinversión de campos maduros y proyecto GNL.", cell_style_left)],
        [Paragraph("Pampa Energía (PAMP)", cell_style_left), Paragraph("4,1x", cell_style_center), Paragraph("38,5%", cell_style_center), Paragraph("1,15x", cell_style_center), Paragraph("Generación eléctrica eficiente y récord de producción de shale gas.", cell_style_left)],
        [Paragraph("Transportadora Gas del Sur (TGSU2)", cell_style_left), Paragraph("4,4x", cell_style_center), Paragraph("42,1%", cell_style_center), Paragraph("0,85x", cell_style_center), Paragraph("Ampliación de capacidad de transporte regulado y exportación de líquidos.", cell_style_left)],
        [Paragraph("Grupo Financiero Galicia (GGAL)", cell_style_left), Paragraph("6,2x", cell_style_center), Paragraph("28,5%", cell_style_center), Paragraph("0,00x (Solvente)", cell_style_center), Paragraph("Consolidación bancaria tras compra de HSBC y reactivación del crédito comercial.", cell_style_left)]
    ]
    t_eq = Table(tabla_equity_data, colWidths=[120, 75, 75, 75, 187])
    t_eq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_eq)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 14: 9. FLASH NORMATIVO, CALENDARIO Y REFERENCIAS APA
    # =============================================================
    elements.append(Paragraph("9. Flash Normativo, Calendario Crítico y Referencias Bibliográficas", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "En el plano regulatorio, el BCRA ratificó el esquema de encajes no remunerados y absorción vía títulos públicos. En el contexto internacional, el rendimiento del bono del Tesoro de EE.UU. a 10 años osciló en 3,85%-3,95%, el índice DXY se ubicó en 102,4 puntos y el crudo WTI operó en USD 74/bbl, otorgando estabilidad a los términos de intercambio de las exportaciones energéticas argentinas.",
        body_style
    ))
    elements.append(Spacer(1, 2))

    tabla_eventos_data = [
        [Paragraph("<b>Fecha / Evento Crítico</b>", cell_header_style), Paragraph("<b>Organismo / Emisor</b>", cell_header_style), Paragraph("<b>Impacto Esperado de Mercado & Rollover</b>", cell_header_style)],
        [Paragraph("28 de Agosto de 2026: Licitación de Letras y Bonos", cell_style_left), Paragraph("Secretaría de Finanzas", cell_style_center), Paragraph("Rollover de vencimientos en ARS ($1,4 B); test de corte de TEM en Lecaps cortas.", cell_style_left)],
        [Paragraph("11 de Septiembre de 2026: Publicación IPC Agosto 2026", cell_style_left), Paragraph("INDEC / DEIE Mendoza", cell_style_center), Paragraph("Confirmación de convergencia mensual hacia el rango del 2% MoM.", cell_style_left)],
        [Paragraph("18 de Septiembre de 2026: Reunión de Política Monetaria FOMC", cell_style_left), Paragraph("Reserva Federal (FED)", cell_style_center), Paragraph("Definición de tasas globales e impacto en el DXY y deuda soberana emergente.", cell_style_left)]
    ]
    t_ev = Table(tabla_eventos_data, colWidths=[165, 105, 262])
    t_ev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ev)
    elements.append(Spacer(1, 2.5))

    # Directrices Estratégicas para Comités de Inversión y Tesorerías
    directrices_box = Table([
        [Paragraph("<b>DIRECTRICES ESTRATÉGICAS Y RECOMENDACIONES DE CIERRE DE MES</b>", ParagraphStyle('DCH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph("• <b>Gestión de Liquidez Corporativa (30-60 días):</b> Maximizar colocaciones en Lecaps cortas (S31O6 / S28N6) a TEM 2,95%-3,05%, complementadas con cauciones bursátiles activas para optimizar rendimientos diarios de caja.<br/>• <b>Estrategia Cambiaria y Comercio Exterior (90-180 días):</b> Mantener coberturas selectivas mediante futuros Matba-Rofex solo para compromisos rígidos de importación, aprovechando la compresión de tasas implícitas (35%-38% TNA).<br/>• <b>Posicionamiento Soberano en Moneda Extranjera (+12 meses):</b> Sobreponderar bonos globales GD35 y GD38 con paridades inferiores al 62%, capturando una aceleración en el retorno total ante convergencia de spreads hacia 400 pb EMBI.", ParagraphStyle('DCB', fontName='Georgia', fontSize=6.8, leading=8.8, textColor=DARK_TEXT))]
    ], colWidths=[532])
    directrices_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('LINELEFT', (0,0), (-1,-1), 2.5, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(directrices_box)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Referencias Bibliográficas (Normas APA 7ma edición):</b>", h2_style))

    refs = [
        "Asociación de Fabricantes de Cemento Portland. (2026). <i>Estadísticas mensuales de despacho de cemento portland</i>. AFCP.",
        "Ámbito Financiero. (2026, 21 de agosto). <i>Mercado financiero: bonos soberanos recortan pérdidas y descomprimen el riesgo país</i>. https://www.ambito.com",
        "Banco Central de la República Argentina. (2026). <i>Boletín Monetario Mensual y Relevamiento de Expectativas de Mercado (REM)</i>. BCRA.",
        "Clarín. (2026, 23 de agosto). <i>Dólar CCL hoy y cotizaciones financieras</i>. https://www.clarin.com",
        "Consultora 1816. (2026). <i>Estrategia macroeconómica y mercado de deuda soberana</i> [Informe de Research].",
        "Dal Poggetto, M. (2026). <i>Evaluación del programa monetario y esquema de reservas</i> [Nota Técnica]. Eco Go Consultores.",
        "Dirección de Estadísticas e Investigaciones Económicas de Mendoza. (2026). <i>Índice de Precios al Consumidor y Valorización de la Canasta Básica</i>. DEIE Mendoza.",
        "Fundación de Investigaciones Económicas Latinoamericanas. (2026). <i>Indicadores de actividad y coyuntura económica</i>. FIEL.",
        "Instituto Nacional de Estadística y Censos. (2026). <i>Índice de Precios al Consumidor y Estimador Mensual de Actividad Económica</i>. INDEC.",
        "Instituto Nacional de Vitivinicultura. (2026). <i>Estadísticas de comercialización y despacho vitivinícola</i>. INV.",
        "La Nación. (2026, 21 de agosto). <i>Riesgo país: variables determinantes y compresión hacia 500 pb</i>. https://www.lanacion.com.ar",
        "Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. <i>Journal of Business</i>, 60(4), 473-489.",
        "Romano Group. (2026). <i>Análisis de renta fija y dinámica cambiaria</i> [Informe Financiero].",
        "Taylor, J. B. (1993). Discretion versus policy rules in practice. <i>Carnegie-Rochester Conference Series on Public Policy</i>, 39, 195-214.",
        "TN. (2026, 21 de agosto). <i>Dólar oficial hoy y cotizaciones financieras</i>. https://tn.com.ar"
    ]

    ref_style = ParagraphStyle(
        'RefAPA_M', parent=styles['Normal'],
        fontName='Georgia', fontSize=7.4, leading=9.8,
        alignment=TA_JUSTIFY, leftIndent=14, firstLineIndent=-14,
        textColor=DARK_TEXT, spaceAfter=1.2
    )

    for r in refs:
        elements.append(Paragraph(r, ref_style))

    doc.build(elements, canvasmaker=ZeroWhitespaceCanvas)
    
    # Copiar a 07_Reportes_Ejecutivos_PDF
    consol_dest = os.path.join(OUT_DIR_CONSOL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    shutil.copy2(pdf_path, consol_dest)
    print(f"Masterpiece PDF re-built and synchronized: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_informe_mensual_reportlab()
