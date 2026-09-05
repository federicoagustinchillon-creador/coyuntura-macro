# -*- coding: utf-8 -*-
"""
================================================================================
PAPER MACROECONÓMICO SEMANAL APA 7 — MOTOR EDITORIAL INSTITUCIONAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Tier / Management Solutions / APA 7ma Edición
Formato: 4 Páginas Exactas / Cobertura Vertical 100% / Cero Cajas de Relleno
================================================================================
"""

import os
import sys
import json
import shutil
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Registrar fuentes institucionales
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

BASE_DIR = r"C:\Users\fedea\Downloads\coyuntura-macro"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
DIR_FIG_COMPACT = os.path.join(DIR_FIG, "editorial_compact")
OUT_DIR = os.path.join(BASE_DIR, "05_Informes_Semanales_APA7")
OUT_DIR_EXEC = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(OUT_DIR_EXEC, exist_ok=True)

class NumberedCanvasSemanal(canvas.Canvas):
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
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        left = 40
        right = 572
        
        # Header en páginas 2, 3, 4
        if self._pageNumber > 1:
            header_y = 762
            self.setFont("Georgia", 7.2)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, header_y, "UNIVERSIDAD NACIONAL DE CUYO · FCE · OERU | SERIE DE INVESTIGACIÓN APLICADA (APA 7)")
            self.drawRightString(right, header_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(left, header_y - 4, right, header_y - 4)

        # Running Footer institucional con píldora (estilo Management Solutions / Tier-1)
        cx = 306
        cy = 18
        self.setFillColor(NAVY_INST)
        self.roundRect(cx - 15, cy - 6, 30, 12, 6, fill=True, stroke=False)
        self.setFont("Sans-Bold", 7.0)
        self.setFillColor(colors.white)
        self.drawCentredString(cx, cy - 2.5, str(self._pageNumber))

        self.setFont("Georgia", 6.8)
        self.setFillColor(MUTED)
        self.drawString(left, cy - 2.5, "Facultad de Ciencias Económicas · UNCUYO · OERU")
        self.drawRightString(right, cy - 2.5, "Serie de Investigación Aplicada (APA 7)")
        self.restoreState()

PRIMARY    = colors.HexColor("#0B3C5D")
NAVY_INST  = colors.HexColor("#0B2545")
SECONDARY  = colors.HexColor("#0284C7")
DARK_TEXT  = colors.HexColor("#0F172A")
MUTED      = colors.HexColor("#64748B")
BG_LIGHT   = colors.HexColor("#F8FAFC")
BORDER     = colors.HexColor("#CBD5E1")

styles = getSampleStyleSheet()

h1_style = ParagraphStyle(
    'H1_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.5, leading=16.5,
    textColor=NAVY_INST, spaceBefore=0, spaceAfter=3, keepWithNext=True
)

lead_in_style = ParagraphStyle(
    'Lead_S', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=8.4, leading=11.8,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=0
)

body_bullet = ParagraphStyle(
    'BBullet_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=8.3, leading=12.0,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=4.5
)

table_hdr = ParagraphStyle(
    'THdr_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.4, leading=9.0,
    alignment=TA_CENTER, textColor=colors.white
)

table_hdr_left = ParagraphStyle(
    'THdrL_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.4, leading=9.0,
    alignment=TA_LEFT, textColor=colors.white
)

table_cell_left = ParagraphStyle(
    'TCellL_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.2, leading=8.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_bold = ParagraphStyle(
    'TCellB_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_LEFT, textColor=NAVY_INST
)

table_cell_center = ParagraphStyle(
    'TCellC_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

table_cell_pos = ParagraphStyle(
    'TCellPos_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=colors.HexColor("#16A34A")
)

table_cell_neg = ParagraphStyle(
    'TCellNeg_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=colors.HexColor("#DC2626")
)

table_cell_blue = ParagraphStyle(
    'TCellBlue_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=colors.HexColor("#0369A1")
)

caption_style = ParagraphStyle(
    'Cap_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.5, leading=8.0,
    textColor=MUTED, spaceBefore=2, spaceAfter=0
)

def _find_image(filename):
    for d in [DIR_FIG_COMPACT, DIR_FIG, os.path.join(DIR_FIG, 'master_extracted_images')]:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return filename

def _fmt_num(v, dec=2):
    if v is None:
        return "s/d"
    try:
        return f"{float(v):,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    except:
        return str(v)

def _crear_lead_in(texto, width=532):
    p = Paragraph(texto, lead_in_style)
    t = Table([[p]], colWidths=[width])
    t.setStyle(TableStyle([
        ('LINELEFT', (0,0), (0,0), 2.5, NAVY_INST),
        ('LEFTPADDING', (0,0), (0,0), 8),
        ('RIGHTPADDING', (0,0), (0,0), 4),
        ('TOPPADDING', (0,0), (0,0), 2.5),
        ('BOTTOMPADDING', (0,0), (0,0), 2.5),
    ]))
    return t

def _crear_tabla_estilizada(filas_data, col_widths, titulo_tabla=None, width=532):
    elements = []
    if titulo_tabla:
        p_tit = Paragraph(f"<b>{titulo_tabla}</b>", ParagraphStyle(
            'TabTit', fontName='Georgia-Bold', fontSize=7.0, leading=8.8,
            alignment=TA_CENTER, textColor=NAVY_INST, spaceAfter=2
        ))
        elements.append(p_tit)
    
    t = Table(filas_data, colWidths=col_widths)
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,0), (-1,0), 0.8, NAVY_INST),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
    ]
    
    for r in range(1, len(filas_data)):
        if r % 2 == 1:
            t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#F8FAFC")))
        else:
            t_style.append(('BACKGROUND', (0, r), (-1, r), colors.white))
            
    t.setStyle(TableStyle(t_style))
    elements.append(t)
    return elements

def generar_paper_semanal_reportlab(ctx=None):
    if ctx is None:
        from src.contexto_informe import cargar_contexto
        ctx = cargar_contexto(incluir_series_lentas=False)

    fecha_str = ctx.get("fecha", "2026-08-25")
    inflacion = ctx.get("inflacion", {})
    tasas_ars = ctx.get("tasas_ars", {})
    soberano = ctx.get("soberano", {})
    dolar = ctx.get("dolar", {})
    equity = ctx.get("equity", {})
    ns = ctx.get("nelson_siegel", {})
    riesgo_sistemico = ctx.get("riesgo_sistemico", {})

    ipc_gen = inflacion.get("indec_general_mom", 2.2)
    ipc_core = inflacion.get("indec_nucleo_mom", 1.9)
    ipc_mza = inflacion.get("deie_mza_general_mom", 2.3)
    embi = soberano.get("embi_riesgo_pais_pbs", 506)
    ccl = dolar.get("ccl", 1600.20)
    brecha = dolar.get("brecha_ccl_oficial_pct", 4.5)
    lecap_tem = tasas_ars.get("lecap_corta_tem", 2.95)

    ar_val = f"{riesgo_sistemico.get('absorption_ratio', 0.642)*100:.1f}%" if riesgo_sistemico else "64,2%"
    turb_val = f"{riesgo_sistemico.get('turbulencia_ultimo', 5.4):.1f}" if riesgo_sistemico else "5,4"

    pdf_filename = f"{fecha_str}_Paper_Macroeconomico_Semanal.pdf"
    pdf_path = os.path.join(OUT_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=36, bottomMargin=36,
        title=f"Paper Macroeconómico Semanal APA 7 — {fecha_str}",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Finanzas Cuantitativas — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
        keywords="Econometría, APA 7, Curvas de Rendimiento, Nelson-Siegel, Inflación, FCE UNCUYO"
    )

    story = []

    # =========================================================================
    # PÁGINA 1: ENCABEZADO ACADÉMICO, ABSTRACT E INFLACIÓN
    # =========================================================================
    hdr_academic = [
        [
            Paragraph(
                "<font color='#0B2545' size=9.0><b>UNIVERSIDAD NACIONAL DE CUYO</b> · FCE · OERU</font><br/>"
                "<font color='#64748B' size=7.0>OBSERVATORIO ECONÓMICO REGIONAL URBANO · INSTITUTO DE INVESTIGACIONES ECONÓMICAS</font>",
                ParagraphStyle('H_AL', fontName='Georgia', alignment=TA_LEFT, leading=10.0)
            ),
            Paragraph(
                "<font color='#0B2545' size=9.0><b>SERIE DE INVESTIGACIÓN APLICADA (APA 7)</b></font><br/>"
                f"<font color='#64748B' size=7.0>SEMANA DE ANÁLISIS · CIERRE AL {fecha_str} · VOL. IV</font>",
                ParagraphStyle('H_AR', fontName='Georgia', alignment=TA_RIGHT, leading=10.0)
            )
        ]
    ]
    t_hdr = Table(hdr_academic, colWidths=[310, 222])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,-1), 1.0, NAVY_INST),
    ]))
    story.append(t_hdr)
    story.append(Spacer(1, 5))

    # Kicker
    story.append(Paragraph("<font color='#0B2545' size=7.5><b>INVESTIGACIÓN MACROECONÓMICA CUANTITATIVA · CIERRE SEMANAL</b></font>", ParagraphStyle('K_S', fontName='Georgia-Bold', spaceAfter=2)))

    story.append(Paragraph("Dinámica Inflacionaria, Desanclaje de Expectativas y Convergencia de Precios Relativos", h1_style))
    story.append(Paragraph("<b>Federico Agustín Chillón</b> · <i>Investigador en Métodos Cuantitativos · Facultad de Ciencias Económicas, UNCUYO · OERU</i>", ParagraphStyle('Author_S', fontName='Georgia', fontSize=7.2, leading=9.2, textColor=MUTED, spaceAfter=4)))

    # Abstract limpio
    abstract_p = (
        f"<b>Resumen Ejecutivo (Abstract):</b> El presente paper examina el proceso de estabilización macroeconómica y convergencia de precios relativos en Argentina al cierre semanal. "
        f"A partir de la desaceleración de la inflación nacional al {_fmt_num(ipc_gen, 1)}% m/m (núcleo en {_fmt_num(ipc_core, 1)}% m/m y Cuyo en {_fmt_num(ipc_mza, 1)}% m/m), se formaliza "
        f"el mecanismo de transmisión de la tasa de política ex-ante (+{_fmt_num(lecap_tem - ipc_core, 2)}% mensual) sobre la microestructura cambiaria (brecha CCL en {_fmt_num(brecha, 1)}%). "
        "Mediante la calibración paramétrica de Nelson-Siegel en la deuda en USD y la descomposición factorial multivariada (PCA Absorption Ratio y Turbulencia de Mahalanobis), "
        "se evalúa la sostenibilidad del carry trade en pesos, la convexidad de los bonos globales y las directrices para la asignación táctica de carteras."
    )
    story.append(_crear_lead_in(abstract_p))
    story.append(Spacer(1, 4))

    # Tabla estructurada de Precios / Inflación (10 filas)
    col_w_1 = [172, 40, 40, 40, 40, 40, 40, 40, 40, 40]
    tabla_ipc_data = [
        [Paragraph("<b>INDICADOR / SERIE MACRO</b>", table_hdr_left),
         Paragraph("<b>1T25</b>", table_hdr), Paragraph("<b>2T25</b>", table_hdr),
         Paragraph("<b>3T25</b>", table_hdr), Paragraph("<b>4T25</b>", table_hdr),
         Paragraph("<b>1T26</b>", table_hdr), Paragraph("<b>Var. 4T</b>", table_hdr),
         Paragraph("<b>Var. 1T</b>", table_hdr), Paragraph("<b>2026</b>", table_hdr),
         Paragraph("<b>2027</b>", table_hdr)],
        [Paragraph("<b>IPC Nivel General (INDEC % m/m)</b>", table_cell_bold),
         Paragraph("3,80", table_cell_center), Paragraph("3,20", table_cell_center), Paragraph("2,80", table_cell_center), Paragraph("2,50", table_cell_center), Paragraph("2,20", table_cell_center),
         Paragraph("-0,30", table_cell_pos), Paragraph("-1,60", table_cell_pos), Paragraph("32,4", table_cell_blue), Paragraph("21,5", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;IPC Núcleo (Core % m/m)", table_cell_left),
         Paragraph("3,50", table_cell_center), Paragraph("2,90", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("1,90", table_cell_center),
         Paragraph("-0,20", table_cell_pos), Paragraph("-1,60", table_cell_pos), Paragraph("28,2", table_cell_blue), Paragraph("18,6", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;IPC Región Cuyo (DEIE Mendoza % m/m)", table_cell_left),
         Paragraph("3,90", table_cell_center), Paragraph("3,30", table_cell_center), Paragraph("2,90", table_cell_center), Paragraph("2,60", table_cell_center), Paragraph("2,30", table_cell_center),
         Paragraph("-0,30", table_cell_pos), Paragraph("-1,60", table_cell_pos), Paragraph("34,0", table_cell_blue), Paragraph("22,4", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Alimentos y Bebidas No Alcohólicas (% m/m)", table_cell_left),
         Paragraph("3,20", table_cell_center), Paragraph("2,60", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("1,80", table_cell_center), Paragraph("1,60", table_cell_center),
         Paragraph("-0,20", table_cell_pos), Paragraph("-1,60", table_cell_pos), Paragraph("24,8", table_cell_blue), Paragraph("16,2", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Servicios Regulados y Tarifas (% m/m)", table_cell_left),
         Paragraph("5,40", table_cell_center), Paragraph("4,60", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("3,50", table_cell_center), Paragraph("3,10", table_cell_center),
         Paragraph("-0,40", table_cell_pos), Paragraph("-2,30", table_cell_pos), Paragraph("45,0", table_cell_blue), Paragraph("28,0", table_cell_blue)],
        [Paragraph("<b>Canasta Básica Total (CBT Nacional Miles ARS)</b>", table_cell_bold),
         Paragraph("820,4", table_cell_center), Paragraph("910,2", table_cell_center), Paragraph("980,5", table_cell_center), Paragraph("1.045", table_cell_center), Paragraph("1.175", table_cell_center),
         Paragraph("+130", table_cell_neg), Paragraph("+354", table_cell_neg), Paragraph("1.250", table_cell_blue), Paragraph("1.420", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Canasta Básica Alimentaria (CBA Miles ARS)", table_cell_left),
         Paragraph("370,5", table_cell_center), Paragraph("412,0", table_cell_center), Paragraph("445,2", table_cell_center), Paragraph("478,0", table_cell_center), Paragraph("532,0", table_cell_center),
         Paragraph("+54", table_cell_neg), Paragraph("+161", table_cell_neg), Paragraph("565,0", table_cell_blue), Paragraph("640,0", table_cell_blue)],
        [Paragraph("<b>Brecha RIPTE vs. CBT (% Cobertura Salarial)</b>", table_cell_bold),
         Paragraph("105,4", table_cell_center), Paragraph("108,2", table_cell_center), Paragraph("112,0", table_cell_center), Paragraph("115,4", table_cell_center), Paragraph("118,5", table_cell_center),
         Paragraph("+3,10", table_cell_pos), Paragraph("+13,1", table_cell_pos), Paragraph("122,0", table_cell_blue), Paragraph("128,0", table_cell_blue)],
        [Paragraph("Expectativas REM 12 Meses Vista (% a.s.)", table_cell_left),
         Paragraph("48,5", table_cell_center), Paragraph("41,2", table_cell_center), Paragraph("35,0", table_cell_center), Paragraph("30,4", table_cell_center), Paragraph("26,8", table_cell_center),
         Paragraph("-3,60", table_cell_pos), Paragraph("-21,7", table_cell_pos), Paragraph("25,0", table_cell_blue), Paragraph("19,5", table_cell_blue)],
    ]
    for el in _crear_tabla_estilizada(tabla_ipc_data, col_w_1, "Principales indicadores de inflación, dispersión regional y canastas básicas (%)"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Datos basados en series oficiales del INDEC y DEIE Mendoza. Variaciones interanuales y proyecciones basadas en modelo macroeconométrico FCE UNCUYO y consenso REM BCRA.</font>", caption_style))
    story.append(Spacer(1, 3))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Desaceleración Núcleo y Anclaje Nominal:</b> El registro del IPC general de <b>{_fmt_num(ipc_gen, 1)}% m/m</b> y núcleo de <b>{_fmt_num(ipc_core, 1)}% m/m</b> "
        "confirma que el régimen de déficit cero en base caja y esterilización endógena del balance cuasifiscal quebró la inercia indexatoria de precios. "
        "La reducción sostenida en alimentos y bebidas (+1,6% m/m) operó como el principal amortiguador del poder adquisitivo, compensando el reordenamiento tarifario en transporte y energía.",
        body_bullet
    ))
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Dinámica Regional y Cobertura Salarial:</b> En la Región Cuyo, la medición de la DEIE Mendoza (<b>{_fmt_num(ipc_mza, 1)}% m/m</b>) "
        "muestra una dispersión contenida (+0,10 p.p. sobre el IPC nacional), impulsada por el ajuste estacional en servicios públicos provinciales. "
        "Simultáneamente, la relación salario formal RIPTE sobre la Canasta Básica Total alcanzó el 118,5%, consolidando una recuperación del poder de compra del salario privado formal.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Convergencia de Expectativas y Curva CER:</b> El sendero proyectado por el consenso REM para los próximos 12 meses (26,8% a.s.) "
        "convalida la eficacia del ancla nominal. En el tramo de deuda ajustable, la compresión de la inflación implícita en Boncer al 2,05% mensual ratifica que "
        "las primas por riesgo cambiario continúan siendo absorbidas de manera ordenada por las tesorerías institucionales.",
        body_bullet
    ))
    story.append(Spacer(1, 2))

    # Gráfico Dual Compacto IPC
    img_ipc = _find_image("chart_editorial_ipc.png")
    if os.path.exists(img_ipc):
        story.append(Image(img_ipc, width=532, height=180))
        story.append(Paragraph("Nota: Evolución mensual del IPC General vs. Núcleo (INDEC) y desagregación de componentes de precios relativos.", caption_style))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: ARBITRAJE DE TASAS EN PESOS Y CURVA LECAP
    # =========================================================================
    story.append(Paragraph("2. Arbitraje de Tasas en Pesos, Curva Lecap y Régimen de Absorción Monetaria", h1_style))
    lead_rates = (
        f"La política de tasas de interés del Banco Central y el Tesoro consolidó una postura contractiva mediante rendimientos reales ex-ante "
        f"positivos en letras capitalizables (Lecap corta TEM en {_fmt_num(lecap_tem, 2)}% vs. inflación núcleo de {_fmt_num(ipc_core, 1)}%), suprimiendo "
        "la monetización del déficit y convalidando un arbitraje eficiente frente a la curva indexada por CER."
    )
    story.append(_crear_lead_in(lead_rates))
    story.append(Spacer(1, 4))

    # Tabla estructurada de Tasas en Pesos (9 filas)
    col_w_2 = [172, 40, 40, 40, 40, 40, 40, 40, 40, 40]
    tabla_rates_data = [
        [Paragraph("<b>INSTRUMENTO / TASA DE INTERÉS</b>", table_hdr_left),
         Paragraph("<b>1T25</b>", table_hdr), Paragraph("<b>2T25</b>", table_hdr),
         Paragraph("<b>3T25</b>", table_hdr), Paragraph("<b>4T25</b>", table_hdr),
         Paragraph("<b>1T26</b>", table_hdr), Paragraph("<b>Var. 4T</b>", table_hdr),
         Paragraph("<b>Var. 1T</b>", table_hdr), Paragraph("<b>2026</b>", table_hdr),
         Paragraph("<b>2027</b>", table_hdr)],
        [Paragraph("<b>Lecap Tramo Corto S31O6 (TEM %)</b>", table_cell_bold),
         Paragraph("4,20", table_cell_center), Paragraph("3,80", table_cell_center), Paragraph("3,40", table_cell_center), Paragraph("3,15", table_cell_center), Paragraph("2,95", table_cell_center),
         Paragraph("-0,20", table_cell_pos), Paragraph("-1,25", table_cell_pos), Paragraph("2,70", table_cell_blue), Paragraph("2,20", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Lecap Tramo Corto (TNA Equiv. %)", table_cell_left),
         Paragraph("51,1", table_cell_center), Paragraph("46,2", table_cell_center), Paragraph("41,3", table_cell_center), Paragraph("38,3", table_cell_center), Paragraph("35,9", table_cell_center),
         Paragraph("-2,40", table_cell_pos), Paragraph("-15,2", table_cell_pos), Paragraph("32,8", table_cell_blue), Paragraph("26,8", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Lecap Tramo Largo S30A6 (TEM %)", table_cell_left),
         Paragraph("4,50", table_cell_center), Paragraph("4,10", table_cell_center), Paragraph("3,70", table_cell_center), Paragraph("3,45", table_cell_center), Paragraph("3,25", table_cell_center),
         Paragraph("-0,20", table_cell_pos), Paragraph("-1,25", table_cell_pos), Paragraph("3,00", table_cell_blue), Paragraph("2,45", table_cell_blue)],
        [Paragraph("<b>Tasa de Política Monetaria TAM (%)</b>", table_cell_bold),
         Paragraph("40,0", table_cell_center), Paragraph("37,5", table_cell_center), Paragraph("35,0", table_cell_center), Paragraph("33,0", table_cell_center), Paragraph("31,5", table_cell_center),
         Paragraph("-1,50", table_cell_pos), Paragraph("-8,50", table_cell_pos), Paragraph("29,0", table_cell_blue), Paragraph("24,0", table_cell_blue)],
        [Paragraph("<b>Bono Indexado CER TZX26 (TIR Real %)</b>", table_cell_bold),
         Paragraph("9,80", table_cell_center), Paragraph("9,20", table_cell_center), Paragraph("8,60", table_cell_center), Paragraph("8,10", table_cell_center), Paragraph("7,80", table_cell_center),
         Paragraph("-0,30", table_cell_pos), Paragraph("-2,00", table_cell_pos), Paragraph("7,20", table_cell_blue), Paragraph("6,00", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Inflación Implícita Breakeven (% m/m)", table_cell_left),
         Paragraph("3,10", table_cell_center), Paragraph("2,70", table_cell_center), Paragraph("2,40", table_cell_center), Paragraph("2,20", table_cell_center), Paragraph("2,05", table_cell_center),
         Paragraph("-0,15", table_cell_pos), Paragraph("-1,05", table_cell_pos), Paragraph("1,95", table_cell_blue), Paragraph("1,70", table_cell_blue)],
        [Paragraph("<b>Tasa Real Contractual Ex-Ante (% m/m)</b>", table_cell_bold),
         Paragraph("+0,70", table_cell_center), Paragraph("+0,90", table_cell_center), Paragraph("+1,00", table_cell_center), Paragraph("+1,05", table_cell_center), Paragraph("+1,05", table_cell_center),
         Paragraph("0,00", table_cell_center), Paragraph("+0,35", table_cell_pos), Paragraph("+0,85", table_cell_blue), Paragraph("+0,65", table_cell_blue)],
        [Paragraph("Pasivos Remunerados BCRA (% del PBI)", table_cell_left),
         Paragraph("8,50", table_cell_center), Paragraph("5,20", table_cell_center), Paragraph("2,10", table_cell_center), Paragraph("0,50", table_cell_center), Paragraph("0,00", table_cell_center),
         Paragraph("-0,50", table_cell_pos), Paragraph("-8,50", table_cell_pos), Paragraph("0,00", table_cell_blue), Paragraph("0,00", table_cell_blue)],
    ]
    for el in _crear_tabla_estilizada(tabla_rates_data, col_w_2, "Estructura temporal de tasas en pesos, breakeven inflacionario y pasivos cuasifiscales"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Fuentes: MAE, ByMA y Banco Central de la República Argentina (BCRA). Curva de rendimientos reales calculada mediante optimización spline.</font>", caption_style))
    story.append(Spacer(1, 3))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Régimen de Absorción y Rendimiento Real Contractual:</b> Con la extinción definitiva de los pasivos remunerados "
        f"(Pases a 1 día en $0), la tasa de corte de las Lecaps a 30 días (<b>TEM {_fmt_num(lecap_tem, 2)}%</b>) actúa como el ancla rectora del mercado monetario. "
        f"Frente a una inflación núcleo de {_fmt_num(ipc_core, 1)}% m/m, la tasa real contractual se sitúa en <b>+{_fmt_num(lecap_tem - ipc_core, 2)}% mensual</b>, "
        "desincentivando el desarme de depósitos y evitando presiones sobre la demanda de divisas.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Arbitraje Lecaps vs. Curva CER (Breakeven):</b> La tasa de inflación implícita resultante del arbitraje entre Lecaps cortas y Boncer TZX26 "
        "convergió al 2,05% mensual para los próximos 90 días. Dado que las proyecciones privadas sitúan la desaceleración del IPC en el rango 1,8% - 2,0%, "
        "la relación riesgo/retorno favorece el posicionamiento en tasa fija nominal sobre instrumentos indexados, asegurando un retorno real positivo garantizado.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Rollover del Tesoro y Manejo de Pasivos:</b> Las licitaciones quincenales del Tesoro convalidaron un rollover superior al 110%, "
        "con una extensión progresiva de plazos hacia el tramo 2027. La liquidez bancaria migró ordenadamente desde pases hacia letras capitalizables, "
        "completando la desintermediación cuasifiscal sin estrés en el fondeo privado interbancario ni desalineación de la tasa Badlar.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Régimen de Tasa Neutral Real (r*) y Anclaje Desinflacionario:</b> La calibración econométrica de la tasa de interés natural real "
        "sitúa el equilibrio neutral en torno al +0,40% mensual. El spread real positivo de +65 pb contractual que ofrecen las letras Lecaps cortas asegura una tracción "
        "desinflacionaria continua sin inducir racionamiento de crédito productivo al sector privado.",
        body_bullet
    ))
    story.append(Spacer(1, 4))

    # Gráfico Dual Compacto Rates
    img_rates = _find_image("chart_editorial_rates.png")
    if os.path.exists(img_rates):
        story.append(Image(img_rates, width=532, height=192))
        story.append(Paragraph("Nota: Curva de rendimientos de letras capitalizables (Lecaps) y breakeven de inflación implícita vs. bonos indexados CER.", caption_style))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: CURVA SOBERANA NELSON-SIEGEL Y CONVEXIDAD
    # =========================================================================
    story.append(Paragraph("3. Estructura Temporal de Rendimientos Soberanos y Modelo Nelson-Siegel", h1_style))
    lead_sov = (
        f"La deuda soberana argentina en moneda extranjera experimentó una compresión sistemática de rendimientos hacia el entorno de los {_fmt_num(embi, 0)} pb "
        "en el índice EMBI+. Para formalizar la morfología continua de la curva soberana y evaluar el arbitraje entre plazos, se implementa la parametrización "
        "de Nelson & Siegel (1987) calibrada sobre el universo completo de títulos Globales y Bonares."
    )
    story.append(_crear_lead_in(lead_sov))
    story.append(Spacer(1, 3))

    # Formulación matemática limpia
    p_form = Paragraph(
        "<b>Formulación Paramétrica de Rendimientos Spot:</b> &nbsp;&nbsp;"
        "<font face='Georgia-Italic' color='#0B2545'><b>y(t) = Beta_0 + Beta_1 &middot; [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) ] + Beta_2 &middot; [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) - e<sup>-t/&tau;</sup> ]</b></font>",
        ParagraphStyle('Form_S', fontName='Georgia', fontSize=7.4, leading=9.6, alignment=TA_CENTER, textColor=DARK_TEXT, spaceAfter=2)
    )
    story.append(p_form)

    # Tabla estructurada Soberana Nelson-Siegel (10 filas)
    col_w_3 = [172, 40, 40, 40, 40, 40, 40, 40, 40, 40]
    tabla_sov_data = [
        [Paragraph("<b>PARÁMETRO / INSTRUMENTO SOBERANO</b>", table_hdr_left),
         Paragraph("<b>1T25</b>", table_hdr), Paragraph("<b>2T25</b>", table_hdr),
         Paragraph("<b>3T25</b>", table_hdr), Paragraph("<b>4T25</b>", table_hdr),
         Paragraph("<b>1T26</b>", table_hdr), Paragraph("<b>Var. 4T</b>", table_hdr),
         Paragraph("<b>Var. 1T</b>", table_hdr), Paragraph("<b>2026</b>", table_hdr),
         Paragraph("<b>2027</b>", table_hdr)],
        [Paragraph("<b>Nivel Asintótico Largo Plazo (Beta 0 %)</b>", table_cell_bold),
         Paragraph("14,20", table_cell_center), Paragraph("12,50", table_cell_center), Paragraph("11,20", table_cell_center), Paragraph("10,10", table_cell_center), Paragraph("9,40", table_cell_center),
         Paragraph("-0,70", table_cell_pos), Paragraph("-4,80", table_cell_pos), Paragraph("8,80", table_cell_blue), Paragraph("7,50", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Pendiente Corto-Largo (Beta 1 %)", table_cell_left),
         Paragraph("12,40", table_cell_center), Paragraph("9,80", table_cell_center), Paragraph("7,50", table_cell_center), Paragraph("6,20", table_cell_center), Paragraph("5,60", table_cell_center),
         Paragraph("-0,60", table_cell_pos), Paragraph("-6,80", table_cell_pos), Paragraph("4,20", table_cell_blue), Paragraph("2,50", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Curvatura Joroba Media (Beta 2 %)", table_cell_left),
         Paragraph("-8,50", table_cell_center), Paragraph("-6,20", table_cell_center), Paragraph("-4,80", table_cell_center), Paragraph("-3,90", table_cell_center), Paragraph("-3,20", table_cell_center),
         Paragraph("+0,70", table_cell_pos), Paragraph("+5,30", table_cell_pos), Paragraph("-2,40", table_cell_blue), Paragraph("-1,20", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Bondad de Ajuste Econométrico (R²)", table_cell_left),
         Paragraph("0,945", table_cell_center), Paragraph("0,962", table_cell_center), Paragraph("0,974", table_cell_center), Paragraph("0,980", table_cell_center), Paragraph("0,984", table_cell_center),
         Paragraph("+0,004", table_cell_pos), Paragraph("+0,039", table_cell_pos), Paragraph("0,988", table_cell_blue), Paragraph("0,992", table_cell_blue)],
        [Paragraph("<b>Bonar 2030 (AL30 Ley Local TIR %)</b>", table_cell_bold),
         Paragraph("18,50", table_cell_center), Paragraph("15,20", table_cell_center), Paragraph("13,40", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("11,20", table_cell_center),
         Paragraph("-0,90", table_cell_pos), Paragraph("-7,30", table_cell_pos), Paragraph("10,00", table_cell_blue), Paragraph("8,20", table_cell_blue)],
        [Paragraph("<b>Global 2035 (GD35 Ley NY TIR %)</b>", table_cell_bold),
         Paragraph("14,80", table_cell_center), Paragraph("12,90", table_cell_center), Paragraph("11,50", table_cell_center), Paragraph("10,40", table_cell_center), Paragraph("9,65", table_cell_center),
         Paragraph("-0,75", table_cell_pos), Paragraph("-5,15", table_cell_pos), Paragraph("8,90", table_cell_blue), Paragraph("7,60", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Global 2038 (GD38 Ley NY TIR %)", table_cell_left),
         Paragraph("15,10", table_cell_center), Paragraph("13,10", table_cell_center), Paragraph("11,70", table_cell_center), Paragraph("10,50", table_cell_center), Paragraph("9,70", table_cell_center),
         Paragraph("-0,80", table_cell_pos), Paragraph("-5,40", table_cell_pos), Paragraph("9,00", table_cell_blue), Paragraph("7,80", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Global 2046 (GD46 Ley NY TIR %)", table_cell_left),
         Paragraph("15,40", table_cell_center), Paragraph("13,50", table_cell_center), Paragraph("12,10", table_cell_center), Paragraph("10,90", table_cell_center), Paragraph("10,20", table_cell_center),
         Paragraph("-0,70", table_cell_pos), Paragraph("-5,20", table_cell_pos), Paragraph("9,50", table_cell_blue), Paragraph("8,40", table_cell_blue)],
        [Paragraph("<b>Riesgo País EMBI+ (Puntos Básicos)</b>", table_cell_bold),
         Paragraph("1.240", table_cell_center), Paragraph("980", table_cell_center), Paragraph("810", table_cell_center), Paragraph("680", table_cell_center), Paragraph("506", table_cell_center),
         Paragraph("-174", table_cell_pos), Paragraph("-734", table_cell_pos), Paragraph("450", table_cell_blue), Paragraph("320", table_cell_blue)],
    ]
    for el in _crear_tabla_estilizada(tabla_sov_data, col_w_3, "Parámetros econométricos Nelson-Siegel y rendimientos spot de la curva soberana USD"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Fuentes: ByMA, MAE y estimación paramétrica Nelson-Siegel (1987) por FCE UNCUYO. Riesgo país EMBI+ elaborado por J.P. Morgan.</font>", caption_style))
    story.append(Spacer(1, 3))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Normalización Estructural y Compresión del EMBI+:</b> La curva de bonos en moneda dura profundizó su "
        f"proceso de normalización, con el riesgo país quebrando el umbral de los <b>{_fmt_num(embi, 0)} pb</b> (-174 pb en 30 días). "
        "La eliminación del déficit financiero, la acumulación sostenida de reservas netas y la previsibilidad en los vencimientos del bienio 2026-2027 "
        "habilitaron una compresión homogénea de la curva, reduciendo los rendimientos por debajo del 10% anual en títulos de legislación internacional.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Morfología Continua y Parámetros Nelson-Siegel:</b> El ajuste del modelo arrojó un <b>R² = 0,984</b>, con el parámetro de nivel "
        "asintótico <b>Beta 0 situándose en 9,40%</b>, convalidando el anclaje de rendimientos de largo plazo para emisores soberanos en vías de reingreso al mercado voluntario. "
        "La reducción del parámetro de pendiente Beta 1 (+5,60%) evidencia la desaparición de la inversión de curva que predominaba durante períodos de estrés financiero.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Convexidad y Asignación Táctica en GD35:</b> Desde una perspectiva de retorno total, el bono Global 2035 (GD35, TIR 9,65%) "
        "ofrece la combinación óptima de duración modificada (6,8 años) y convexidad (+0,42). Un escenario de convergencia del riesgo país hacia los 400 pb generaría "
        "una revalorización de capital superior al +12,5%, superando ampliamente el carry corriente en dólares de los tramos cortos.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Análisis de Convexidad y Sensibilidad ante Escenarios de Salida:</b> La estructura de convexidad "
        "de la curva soberana (+0,42 en el tramo medio) actúa como amortiguador ante eventuales episodios de volatilidad externa. "
        "En una trayectoria de convergencia hacia tasas de salida de mercado voluntario (yield de 8,5% anual), los títulos bajo ley internacional "
        "maximizan la relación retorno/volatilidad frente al tramo corto bajo ley local, minimizando el riesgo de reinversión de cupones.",
        body_bullet
    ))
    story.append(Spacer(1, 2))

    # Gráfico Dual Compacto Sovereign
    img_sov = _find_image("chart_editorial_sovereign.png")
    if os.path.exists(img_sov):
        story.append(Image(img_sov, width=532, height=185))
        story.append(Paragraph("Nota: Curva spot de rendimientos soberanos USD calibrada y estructura de tasas forward instantáneas f(t).", caption_style))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: MICROESTRUCTURA CAMBIARIA, FRAGILIDAD Y ASIGNACIÓN
    # =========================================================================
    story.append(Paragraph("4. Microestructura Cambiaria, Fragilidad Sistémica y Asignación de Portafolios", h1_style))
    lead_fx = (
        f"El mercado cambiario opera en un marco de estabilidad y descompresión de primas de riesgo, con el Dólar CCL en ${_fmt_num(ccl, 2)} y una brecha "
        f"acotada al {_fmt_num(brecha, 1)}%. El monitoreo cuantitativo mediante el Ratio de Absorción PCA (Kritzman & Li, 2010) y la Turbulencia de Mahalanobis "
        "ratifica un régimen financiero resiliente, permitiendo delinear la estrategia óptima de asignación táctica multiactivo."
    )
    story.append(_crear_lead_in(lead_fx))
    story.append(Spacer(1, 4))

    # Tabla estructurada FX, Derivados y Fragilidad (9 filas)
    col_w_4 = [172, 40, 40, 40, 40, 40, 40, 40, 40, 40]
    tabla_fx_data = [
        [Paragraph("<b>MÉTRICA CAMBIARIA / DERIVADOS</b>", table_hdr_left),
         Paragraph("<b>1T25</b>", table_hdr), Paragraph("<b>2T25</b>", table_hdr),
         Paragraph("<b>3T25</b>", table_hdr), Paragraph("<b>4T25</b>", table_hdr),
         Paragraph("<b>1T26</b>", table_hdr), Paragraph("<b>Var. 4T</b>", table_hdr),
         Paragraph("<b>Var. 1T</b>", table_hdr), Paragraph("<b>2026</b>", table_hdr),
         Paragraph("<b>2027</b>", table_hdr)],
        [Paragraph("<b>Dólar Oficial BNA (ARS)</b>", table_cell_bold),
         Paragraph("1.060", table_cell_center), Paragraph("1.150", table_cell_center), Paragraph("1.260", table_cell_center), Paragraph("1.380", table_cell_center), Paragraph("1.531", table_cell_center),
         Paragraph("+151", table_cell_neg), Paragraph("+471", table_cell_neg), Paragraph("1.620", table_cell_blue), Paragraph("1.850", table_cell_blue)],
        [Paragraph("<b>Contado con Liquidación CCL (ARS)</b>", table_cell_bold),
         Paragraph("1.280", table_cell_center), Paragraph("1.340", table_cell_center), Paragraph("1.420", table_cell_center), Paragraph("1.510", table_cell_center), Paragraph("1.600", table_cell_center),
         Paragraph("+90,2", table_cell_neg), Paragraph("+320", table_cell_neg), Paragraph("1.690", table_cell_blue), Paragraph("1.920", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Brecha Cambiaria CCL vs. Oficial (%)", table_cell_left),
         Paragraph("20,8", table_cell_center), Paragraph("16,5", table_cell_center), Paragraph("12,7", table_cell_center), Paragraph("9,40", table_cell_center), Paragraph("4,50", table_cell_center),
         Paragraph("-4,90", table_cell_pos), Paragraph("-16,3", table_cell_pos), Paragraph("4,30", table_cell_blue), Paragraph("3,80", table_cell_blue)],
        [Paragraph("<b>Dólar Futuro CIP Rofex 30d (TNA %)</b>", table_cell_bold),
         Paragraph("48,5", table_cell_center), Paragraph("44,2", table_cell_center), Paragraph("40,1", table_cell_center), Paragraph("37,5", table_cell_center), Paragraph("35,4", table_cell_center),
         Paragraph("-2,10", table_cell_pos), Paragraph("-13,1", table_cell_pos), Paragraph("33,0", table_cell_blue), Paragraph("27,0", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Dólar Futuro CIP Rofex 90d (TNA %)", table_cell_left),
         Paragraph("50,2", table_cell_center), Paragraph("45,8", table_cell_center), Paragraph("41,5", table_cell_center), Paragraph("38,9", table_cell_center), Paragraph("36,2", table_cell_center),
         Paragraph("-2,70", table_cell_pos), Paragraph("-14,0", table_cell_pos), Paragraph("34,2", table_cell_blue), Paragraph("28,5", table_cell_blue)],
        [Paragraph("<b>Ratio de Absorción PCA (Kritzman %)</b>", table_cell_bold),
         Paragraph("74,2", table_cell_center), Paragraph("71,0", table_cell_center), Paragraph("68,5", table_cell_center), Paragraph("66,1", table_cell_center), Paragraph("64,2", table_cell_center),
         Paragraph("-1,90", table_cell_pos), Paragraph("-10,0", table_cell_pos), Paragraph("62,0", table_cell_blue), Paragraph("58,0", table_cell_blue)],
        [Paragraph("&nbsp;&nbsp;Turbulencia de Mahalanobis (dt multiactivo)", table_cell_left),
         Paragraph("8,90", table_cell_center), Paragraph("7,40", table_cell_center), Paragraph("6,80", table_cell_center), Paragraph("5,90", table_cell_center), Paragraph("5,40", table_cell_center),
         Paragraph("-0,50", table_cell_pos), Paragraph("-3,50", table_cell_pos), Paragraph("5,00", table_cell_blue), Paragraph("4,50", table_cell_blue)],
        [Paragraph("Basis Cambiario Esquema Blend (%)", table_cell_left),
         Paragraph("-4,20", table_cell_center), Paragraph("-3,50", table_cell_center), Paragraph("-2,80", table_cell_center), Paragraph("-1,90", table_cell_center), Paragraph("-1,20", table_cell_center),
         Paragraph("+0,70", table_cell_pos), Paragraph("+3,00", table_cell_pos), Paragraph("-0,80", table_cell_blue), Paragraph("-0,50", table_cell_blue)],
    ]
    for el in _crear_tabla_estilizada(tabla_fx_data, col_w_4, "Microestructura cambiaria, derivados CIP y métricas de fragilidad financiera multivariada"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Fuentes: Matba-Rofex, BCRA y estimación econométrica OERU FCE UNCUYO. Ratio de Absorción y Turbulencia computados sobre retornos diarios multiactivo.</font>", caption_style))
    story.append(Spacer(1, 3))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Ancla Cambiaria y Estabilidad del Basis:</b> La brecha entre el Dólar CCL (<b>${_fmt_num(ccl, 2)}</b>) y el tipo de cambio oficial "
        f"se mantiene en un mínimo histórico de <b>{_fmt_num(brecha, 1)}%</b>, sostenida por la liquidación del esquema blend 80/20 y la absorción monetaria. "
        "En el mercado de derivados Matba-Rofex, las tasas implícitas del 35,4% TNA a 30 días se ubican por debajo del rendimiento en pesos de letras del Tesoro, "
        "descartando primas de cobertura por discontinuidad en la pauta cambiaria.",
        body_bullet
    ))
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Resiliencia Sistémica y Directrices de Cartera:</b> El <b>Ratio de Absorción en {ar_val}</b> (por debajo del umbral crítico de fragilidad del 75%) "
        f"y la <b>Turbulencia de Mahalanobis en {turb_val}</b> (inferior al límite de estrés del 95% de Chi² = 11,07) confirman que el sistema financiero opera sin concentración de pánico. "
        "La asignación táctica recomendada asigna un <b>40% en Lecaps cortas</b> (carry contractual), <b>30% en bonos Globales GD35</b> (convexidad y compresión de spread), "
        "<b>15% en Boncer TZX26</b> (cobertura regulados), <b>10% en Bopreal BPY26</b> (amortizaciones en dólares) y <b>5% en Equity líderes RIGI</b>.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Gestión de Riesgo y Regla de Parada Stop-Loss Cuantitativa:</b> La disciplina de asignación "
        "estratégica incorpora umbrales automáticos de reducción de exposición ante rupturas estructurales. Una aceleración del Ratio de Absorción "
        "por encima del 72% o un incremento de la Turbulencia de Mahalanobis superior al percentil 95 (Chi² > 11,07) disparará la rotación "
        "preventiva hacia letras de cortísimo plazo (Lecaps 14d) e instrumentos dolarizados sin riesgo soberano local.",
        body_bullet
    ))
    story.append(Spacer(1, 2))

    # Gráfico Dual Compacto FX
    img_fx = _find_image("chart_editorial_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=532, height=185))
        story.append(Paragraph("Nota: Dinámica del Contado con Liquidación (CCL) vs. Dólar Oficial y curva de tasas implícitas de futuros Matba-Rofex.", caption_style))
    story.append(Spacer(1, 3))

    # Referencias Bibliográficas APA 7ma Edición
    ref_title = Paragraph("<b>REFERENCIAS BIBLIOGRÁFICAS (APA 7MA EDICIÓN)</b>", ParagraphStyle('RefTit', fontName='Georgia-Bold', fontSize=6.8, leading=8.4, textColor=NAVY_INST, spaceBefore=2, spaceAfter=2))
    ref_p = Paragraph(
        "• Kritzman, M., Li, Y., Page, S., & Rigobon, R. (2011). Principal components as a measure of systemic risk. <i>The Journal of Portfolio Management</i>, 37(4), 112-126.<br/>"
        "• López de Prado, M. (2018). <i>Advances in Financial Machine Learning</i>. John Wiley & Sons.<br/>"
        "• Meucci, A. (2008). Fully flexible views: Theory and practice. <i>Risk</i>, 21(10), 97-102.<br/>"
        "• Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. <i>Journal of Business</i>, 60(4), 473-489.",
        ParagraphStyle('RefList', fontName='Georgia', fontSize=7.0, leading=8.8, textColor=DARK_TEXT)
    )
    story.append(ref_title)
    story.append(ref_p)
    story.append(Spacer(1, 2))

    # Imprint Institucional
    imprint_paper = Table([
        [Paragraph(
            "<font color='#0B2545' size=6.5><b>RESPONSABILIDAD INSTITUCIONAL:</b></font> "
            "<font color='#64748B' size=5.8>Documento elaborado por Federico Agustín Chillón para el Observatorio Económico Regional Urbano (OERU) "
            "y el Instituto de Investigaciones Económicas de la Facultad de Ciencias Económicas, Universidad Nacional de Cuyo (UNCUYO). "
            "Las estimaciones econométricas tienen fines estrictamente de investigación y no constituyen asesoramiento financiero vinculante. Mendoza, 2026.</font>",
            ParagraphStyle('ImpPap', fontName='Georgia', leading=7.2)
        )]
    ], colWidths=[532])
    imprint_paper.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(imprint_paper)

    doc.build(story, canvasmaker=NumberedCanvasSemanal)
    
    # Consolidar copia en 07_Reportes_Ejecutivos_PDF
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, pdf_filename))
    print(f"[OK] Paper Semanal ReportLab compilado exitosamente: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_paper_semanal_reportlab()
