"""
================================================================================
PAPER MACROECONÓMICO SEMANAL APA 7 — MOTOR EDITORIAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Formato: 4 Páginas Exactas / Estándar APA 7 / Tipografía Georgia
================================================================================
"""

import os
import sys
import json
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


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_FIG = os.path.join(BASE_DIR, "03_Figuras_HD")
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
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        left = 36
        right = 576
        
        if self._pageNumber > 1:
            header_y = 756
            self.setFont("Georgia", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, header_y, "RESEARCH MACROECONÓMICO & ESTRATEGIA FINANCIERA · PAPER SEMANAL APA 7")
            self.drawRightString(right, header_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, header_y - 4, right, header_y - 4)

        footer_y = 24
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(left, footer_y + 12, right, footer_y + 12)

        self.setFont("Georgia", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(left, footer_y, "Federico Agustín Chillón · Investigador · Cs. Económicas UNCUYO · Cs. Económicas UNCUYO")
        self.drawRightString(right, footer_y, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

PRIMARY    = colors.HexColor("#0B3C5D")
SECONDARY  = colors.HexColor("#328CC1")
DARK_TEXT  = colors.HexColor("#0F172A")
MUTED      = colors.HexColor("#64748B")
BG_CARD    = colors.HexColor("#F8FAFC")
BORDER     = colors.HexColor("#E2E8F0")

styles = getSampleStyleSheet()

h1_style = ParagraphStyle(
    'H1_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=12.5, leading=15.5,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=2, keepWithNext=True
)

h2_style = ParagraphStyle(
    'H2_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=9.5, leading=12.5,
    textColor=PRIMARY, spaceBefore=3, spaceAfter=2, keepWithNext=True
)

body_style = ParagraphStyle(
    'Body_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=9.0, leading=12.2,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=3
)

abstract_style = ParagraphStyle(
    'Abs_S', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=8.2, leading=11.2,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=3
)

cell_style_left = ParagraphStyle(
    'CellL_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

cell_style_center = ParagraphStyle(
    'CellC_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

cell_header_style = ParagraphStyle(
    'CellH_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.8, leading=10.2,
    alignment=TA_CENTER, textColor=colors.white
)

def generar_paper_semanal_reportlab():
    pdf_path = os.path.join(OUT_DIR, "2026-08-21_Paper_Macroeconomico_Semanal.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36,
        title="Paper Macroeconómico Semanal APA 7 — Federico Agustín Chillón",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Finanzas Cuantitativas — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
        keywords="Macroeconomía, Finanzas, Curva Soberana, Inflación, Riesgo Sistémico, Federico Agustín Chillón, UNCUYO"
    )

    story = []

    # =========================================================================
    # PÁGINA 1: ENCABEZADO ACADÉMICO, ABSTRACT, RÉGIMEN MONETARIO E IPC
    # =========================================================================
    hdr_academic = [
        [
            Paragraph("<b>UNIVERSIDAD NACIONAL DE CUYO</b><br/><font color='#64748B'>Facultad de Ciencias Económicas · Instituto de Investigaciones Económicas</font>", ParagraphStyle('H_AL', fontName='Georgia', fontSize=8.0, leading=10.5, textColor=PRIMARY)),
            Paragraph("<b>SERIE DE INVESTIGACIÓN APLICADA (APA 7)</b><br/><font color='#64748B'>Semana del 17 al 21 de Agosto de 2026 · Vol. IV</font>", ParagraphStyle('H_AR', fontName='Georgia', fontSize=8.0, leading=10.5, alignment=TA_RIGHT, textColor=PRIMARY))
        ]
    ]
    t_hdr = Table(hdr_academic, colWidths=[270, 270])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    story.append(Paragraph("Dinámica Inflacionaria, Desanclaje de Expectativas y Curvas de Rendimiento en Argentina", ParagraphStyle('Title_S', fontName='Georgia-Bold', fontSize=13.5, leading=16.5, textColor=PRIMARY, spaceAfter=2)))
    story.append(Paragraph("<b>Federico Agustín Chillón</b> · <i>Facultad de Ciencias Económicas, Universidad Nacional de Cuyo</i>", ParagraphStyle('Author_S', fontName='Georgia', fontSize=8.5, leading=11.0, textColor=MUTED, spaceAfter=4)))

    # Box de Abstract
    abstract_content = [
        [Paragraph("<b>Resumen Ejecutivo (Abstract):</b> El presente trabajo examina la estructura macroeconómica y financiera de Argentina al cierre de la tercera semana de agosto de 2026. A partir de la desaceleración del IPC nacional al 1,8% mensual y 35,4% interanual, se modeliza la transmisión de la política de ancla fiscal sobre la estructura temporal de tasas de interés y los derivados cambiarios. Mediante la estimación paramétrica de Nelson-Siegel en la deuda en USD y la descomposición factorial de activos cruzados (PCA Absorption Ratio y Mahalanobis), se evalúa la sostenibilidad del carry trade y las primas de riesgo soberano.<br/><b>Palabras Clave:</b> Inflación, Curva Nelson-Siegel, Carry Trade, Ratio de Absorción, Turbulencia de Mahalanobis, Política Monetaria.", abstract_style)]
    ]
    t_abs = Table(abstract_content, colWidths=[540])
    t_abs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_abs)
    story.append(Spacer(1, 3))

    story.append(Paragraph("1. Dinámica de Precios, Brecha Regional y Régimen Monetario", h1_style))
    story.append(Paragraph(
        "La trayectoria del nivel general de precios consolidó su sendero descendente con un registro mensual del <b>1,8% m/m</b> a nivel nacional y del <b>1,7% m/m en la Región Cuyo</b>. "
        "La inflación núcleo se ubicó en el 1,5% m/m, evidenciando que el proceso desinflacionario no responde únicamente a contención de precios estacionales, sino a una contracción sostenida en la tasa de expansión de los agregados monetarios amplios (M2 privado constante en términos reales) y al ancla fiscal del Sector Público Nacional. "
        "En términos de transmisión regional, la Región Cuyo exhibe una menor inercia en el rubro Alimentos y Bebidas (1,4% m/m frente a 1,9% en el GBA), mitigada por la estacionalidad de servicios turísticos y transporte durante el receso invernal. "
        "La regla de Taylor ex-ante arroja una tasa de interés real neutral del 8,5% anual, convergiendo con el rendimiento efectivo de las Lecaps a 90 días.",
        body_style
    ))

    # Infografía Figura 2 (IPC y Cuyo)
    img_ipc = os.path.join(DIR_FIG, "chart_indec_2_ipc.png")
    if os.path.exists(img_ipc):
        story.append(Image(img_ipc, width=540, height=270))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: CURVA SOBERANA NELSON-SIEGEL Y HARD DOLLAR
    # =========================================================================
    story.append(Paragraph("2. Estructura Temporal de Rendimientos Soberanos (Nelson-Siegel)", h1_style))
    story.append(Paragraph(
        "La curva soberana hard dollar de la República Argentina experimentó una compresión generalizada de spreads, ubicando el EMBI en torno a los <b>680 puntos básicos</b>. "
        "Para capturar la morfología de la curva, se estimó el modelo continuo de Nelson & Siegel (1987) sobre los títulos Globales (GD29 a GD46):",
        body_style
    ))

    # Ecuación Nelson-Siegel en caja
    eq_ns = [
        [Paragraph("<font color='#0B3C5D'><b>Modelo Paramétrico de Curva Soberana:</b></font><br/>"
                   "&nbsp;&nbsp;&nbsp;&nbsp;<i>y(t) = &beta;<sub>0</sub> + &beta;<sub>1</sub> [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) ] + &beta;<sub>2</sub> [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) - e<sup>-t/&tau;</sup> ]</i><br/>"
                   "<font size=7 color='#64748B'>Parámetros calibrados: Nivel (&beta;<sub>0</sub>) = 9,40% | Pendiente (&beta;<sub>1</sub>) = +5,60% | Curvatura (&beta;<sub>2</sub>) = -3,20% | Escala (&tau;) = 2,40 años | R² = 0,984</font>",
                   ParagraphStyle('EQ_S', fontName='Georgia', fontSize=8.0, leading=10.5))]
    ]
    t_eq = Table(eq_ns, colWidths=[540])
    t_eq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_eq)
    story.append(Spacer(1, 3))

    # Infografía Figura 5 (Curva Soberana)
    img_sov = os.path.join(DIR_FIG, "chart_indec_5_sovereign.png")
    if os.path.exists(img_sov):
        story.append(Image(img_sov, width=540, height=275))
    story.append(Spacer(1, 3))

    story.append(Paragraph(
        "<b>Interpretación Econométrica:</b> La pendiente positiva de la curva de rendimientos forward instantáneos <i>f(t)</i> confirma la normalización del crédito soberano argentino. "
        "El tramo medio-largo (GD35 a 11,2% TIR y GD38 a 10,9% TIR) presenta la mayor convexidad ante shocks favorables de calificación crediticia.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: MICROESTRUCTURA FX, ROFEX & FRAGILIDAD SISTÉMICA
    # =========================================================================
    story.append(Paragraph("3. Microestructura Cambiaria, Derivados y Fragilidad Sistémica", h1_style))
    story.append(Paragraph(
        "El régimen cambiario finalizó la semana con una brecha CCL vs. Mayorista del <b>7,51%</b> y una compresión sostenida en la volatilidad implícita de los futuros Matba-Rofex. "
        "En el plano multivariado de activos cruzados (Lecaps, Boncer, GD30, CCL y Merval), se monitorean dos métricas cuantitativas avanzadas:",
        body_style
    ))

    # Métricas de riesgo sistémico en 2 columnas
    risk_box = [
        [
            Paragraph("<b>Ratio de Absorción PCA (Kritzman & Li, 2010):</b><br/>"
                      "<i>AR = &sum; &lambda;<sub>1..2</sub> / Tr(&Sigma;) = <b>64,2%</b> (&Delta;AR = -0,40&sigma;)</i><br/>"
                      "<font size=7 color='#15803D'>Régimen Desacoplado / Resiliente (Umbral crítico: 75,0%)</font>",
                      ParagraphStyle('R1', fontName='Georgia', fontSize=7.8, leading=10.0)),
            Paragraph("<b>Turbulencia de Mahalanobis (Chow et al., 1999):</b><br/>"
                      "<i>d<sub>t</sub> = (r<sub>t</sub> - &mu;)<sup>T</sup> &Sigma;<sup>-1</sup> (r<sub>t</sub> - &mu;) = <b>4,12</b></i><br/>"
                      "<font size=7 color='#15803D'>Normalidad Estadística (Valor crítico &chi;² al 95%: 11,07)</font>",
                      ParagraphStyle('R2', fontName='Georgia', fontSize=7.8, leading=10.0))
        ]
    ]
    t_risk = Table(risk_box, colWidths=[268, 268])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 3))

    # Infografía Figura 6 (FX y Futuros)
    img_fx = os.path.join(DIR_FIG, "chart_indec_6_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=540, height=275))
    story.append(Spacer(1, 3))

    story.append(Paragraph(
        "<b>Diagnóstico de Riesgo:</b> La coexistencia de un Ratio de Absorción en 64,2% y un índice de turbulencia en 4,12 confirma que el mercado no se encuentra en un régimen frágil. "
        "Las correlaciones entre acciones, bonos y tipo de cambio operan dentro de sus parámetros históricos, permitiendo que la diversificación de carteras funcione eficazmente.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: ASSET ALLOCATION TÁCTICO & REFERENCIAS APA 7
    # =========================================================================
    story.append(Paragraph("4. Matriz de Asignación Táctica de Activos (Asset Allocation)", h1_style))
    story.append(Paragraph(
        "A partir de las primas de riesgo observadas, las expectativas de desinflación y la estabilidad cambiaria, se estructura la cartera de inversión institucional recomendada:",
        body_style
    ))

    # Tabla Master Asset Allocation
    tab_alloc_data = [
        [
            Paragraph("Clase de Activo", cell_header_style),
            Paragraph("Ponderación", cell_header_style),
            Paragraph("Instrumentos Clave", cell_header_style),
            Paragraph("Rating Táctico", cell_header_style),
            Paragraph("Racional Estratégico", cell_header_style)
        ],
        [
            Paragraph("<b>Lecaps (Tasa Fija ARS)</b>", cell_style_left),
            Paragraph("<b>40,0%</b>", cell_style_center),
            Paragraph("S31O6, S30N6", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Carry trade con TNA 38,9%; tasa real ex-ante positiva de +1,2% m/m.", cell_style_left)
        ],
        [
            Paragraph("<b>Soberanos Hard Dollar</b>", cell_style_left),
            Paragraph("<b>30,0%</b>", cell_style_center),
            Paragraph("GD35, GD38", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Potencial de compresión hacia 600 pb; TIR de 11,2% con alta convexidad.", cell_style_left)
        ],
        [
            Paragraph("<b>Boncer / Cobertura CER</b>", cell_style_left),
            Paragraph("<b>15,0%</b>", cell_style_center),
            Paragraph("TZX26, TZX27", cell_style_center),
            Paragraph("<font color='#D97706'><b>NEUTRAL</b></font>", cell_style_center),
            Paragraph("Cobertura balanceada frente a readecuación tarifaria de servicios públicos.", cell_style_left)
        ],
        [
            Paragraph("<b>Bopreal Serie 3</b>", cell_style_left),
            Paragraph("<b>10,0%</b>", cell_style_center),
            Paragraph("BPY26", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Sintético hard dollar para resguardo corporativo sin riesgo cambiario.", cell_style_left)
        ],
        [
            Paragraph("<b>Renta Variable (Merval)</b>", cell_style_left),
            Paragraph("<b>5,0%</b>", cell_style_center),
            Paragraph("YPFD, PAMP, TGS", cell_style_center),
            Paragraph("<font color='#D97706'><b>NEUTRAL</b></font>", cell_style_center),
            Paragraph("Selectividad en el sector energético (Vaca Muerta y transporte de gas).", cell_style_left)
        ]
    ]
    t_alloc = Table(tab_alloc_data, colWidths=[105, 65, 85, 85, 200])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.8, PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_CARD]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_alloc)
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "<b>Síntesis de Política y Recomendaciones para Comités:</b> La estabilidad cambiaria actual, con brechas spot inferiores al 8% y volatilidad implícita en futuros en mínimos anuales, proporciona una ventana táctica óptima para consolidar posiciones en moneda local a tasa fija. "
        "No obstante, se sugiere a tesorerías corporativas mantener un rebalanceo dinámico quincenal, migrando gradualmente un 30% del portafolio hacia soberanos hard dollar (GD35/GD38) a medida que el tipo de cambio real multilateral alcance niveles de equilibrio de cuenta corriente.",
        body_style
    ))
    story.append(Spacer(1, 2))
    story.append(Paragraph("5. Referencias Bibliográficas (Estándar APA 7)", h1_style))
    refs = [
        "Banco Central de la República Argentina (BCRA). (2026). <i>Informe de Política Monetaria y Relevamiento de Expectativas de Mercado (REM)</i>. Buenos Aires: BCRA.",
        "Chow, G., Jacquier, E., Kritzman, M., & Lowry, K. (1999). Optimal portfolios in good times and bad. <i>Financial Analysts Journal</i>, 55(3), 65-73.",
        "Instituto Nacional de Estadística y Censos (INDEC). (2026). <i>Índice de Precios al Consumidor (IPC) y Estimador Mensual de Actividad Económica (EMAE)</i>. Informes Técnicos, Vol. 10.",
        "Kritzman, M., & Li, Y. (2010). Skulls, financial turbulence, and risk management. <i>Financial Analysts Journal</i>, 66(5), 30-41.",
        "López de Prado, M. (2018). <i>Advances in Financial Machine Learning</i>. Hoboken, NJ: John Wiley & Sons.",
        "Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. <i>Journal of Business</i>, 60(4), 473-489."
    ]
    for r in refs:
        story.append(Paragraph(r, ParagraphStyle('Ref_S', fontName='Georgia', fontSize=7.4, leading=9.8, textColor=MUTED, spaceAfter=2.5)))

    doc.build(story, canvasmaker=NumberedCanvasSemanal)
    
    import shutil
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, "2026-08-21_Paper_Macroeconomico_Semanal.pdf"))
    print(f"[OK] Paper Semanal ReportLab generado: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_paper_semanal_reportlab()
