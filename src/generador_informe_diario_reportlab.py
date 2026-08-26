"""
================================================================================
MONITOR DIARIO DE MERCADOS & COYUNTURA FINANCIERA — MOTOR EDITORIAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Formato: 2 Páginas Exactas / Estándar Goldman Sachs GIR / Tipografía Georgia
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
OUT_DIR = os.path.join(BASE_DIR, "04_Informes_Diarios")
OUT_DIR_EXEC = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(OUT_DIR_EXEC, exist_ok=True)

class NumberedCanvasDiario(canvas.Canvas):
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
            self.drawString(left, header_y, "MONITOR DIARIO DE MERCADOS FINANCIEROS · CIERRE DE JORNADA")
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
    'H1_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.0, leading=16.0,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=2, keepWithNext=True
)

h2_style = ParagraphStyle(
    'H2_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=9.5, leading=12.5,
    textColor=PRIMARY, spaceBefore=3, spaceAfter=2, keepWithNext=True
)

body_style = ParagraphStyle(
    'Body_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=9.0, leading=12.2,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=3
)

cell_style_left = ParagraphStyle(
    'CellL_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

cell_style_center = ParagraphStyle(
    'CellC_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.5, leading=9.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

cell_header_style = ParagraphStyle(
    'CellH_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.8, leading=10.2,
    alignment=TA_CENTER, textColor=colors.white
)

def generar_monitor_diario_reportlab():
    pdf_path = os.path.join(OUT_DIR, "2026-08-21_Monitor_Diario_Mercados.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36,
        title="Monitor Diario de Mercados Financieros — Federico Agustín Chillón",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Finanzas Cuantitativas — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
        keywords="Macroeconomía, Finanzas, Curva Soberana, Inflación, Riesgo Sistémico, Federico Agustín Chillón, UNCUYO"
    )

    story = []

    # =========================================================================
    # PÁGINA 1: PORTADA EJECUTIVA, KPIS DEL DÍA & MICROESTRUCTURA CAMBIARIA
    # =========================================================================
    # Header institucional
    header_data = [
        [
            Paragraph("<b>FACULTAD DE CIENCIAS ECONÓMICAS</b><br/><font color='#64748B'>Universidad Nacional de Cuyo · OERU</font>", ParagraphStyle('H_L', fontName='Georgia', fontSize=8.0, leading=10.5, textColor=PRIMARY)),
            Paragraph("<b>MONITOR DIARIO DE MERCADOS</b><br/><font color='#64748B'>Viernes, 21 de Agosto de 2026 · Cierre</font>", ParagraphStyle('H_R', fontName='Georgia', fontSize=8.0, leading=10.5, alignment=TA_RIGHT, textColor=PRIMARY))
        ]
    ]
    t_hdr = Table(header_data, colWidths=[270, 270])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    story.append(Paragraph("1. Diagnóstico de Cierre de Jornada y Microestructura Cambiaria", h1_style))
    story.append(Paragraph(
        "La plaza financiera completó la rueda con un comportamiento mixto en el segmento de renta fija y una reducción en las brechas cambiarias implícitas. "
        "El <b>Dólar CCL (GD30 Cable)</b> cerró en <b>$1.596,59</b>, marcando una brecha del <b>7,51%</b> respecto al tipo de cambio mayorista A3500 ($1.485,00) y del 5,39% frente al minorista BNA ($1.515,00). "
        "En el mercado de derivados Matba-Rofex, las tasas implícitas reflejan una curva con pendiente positiva (TNA del 35,2% a 30 días y 38,5% para diciembre de 2026), "
        "mientras que los indicadores de acoplamiento multivariado ubican el <b>Ratio de Absorción en 64,2%</b> y la <b>Turbulencia de Mahalanobis en 4,12</b>, confirmando un régimen financiero estable sin estrés sistémico.",
        body_style
    ))

    # Tarjetas KPI Sintéticas del Día (Table 4 columns)
    kpi_data = [
        [
            Paragraph("<font size=6.8 color='#64748B'><b>DÓLAR CCL</b></font><br/><font size=11 color='#991B1B'><b>$1.596,59</b></font><br/><font size=6 color='#64748B'>Brecha BNA: +5,39%</font>", ParagraphStyle('K1', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph("<font size=6.8 color='#64748B'><b>LECAP S31O6 (TNA)</b></font><br/><font size=11 color='#0B3C5D'><b>38,90%</b></font><br/><font size=6 color='#64748B'>TEM: 3,24% m/m</font>", ParagraphStyle('K2', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph("<font size=6.8 color='#64748B'><b>RIESGO PAÍS (EMBI)</b></font><br/><font size=11 color='#0D9488'><b>680 pb</b></font><br/><font size=6 color='#64748B'>Mínimo semestral</font>", ParagraphStyle('K3', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph("<font size=6.8 color='#64748B'><b>S&P MERVAL (USD)</b></font><br/><font size=11 color='#D97706'><b>1.420 USD</b></font><br/><font size=6 color='#64748B'>+1,2% en la rueda</font>", ParagraphStyle('K4', fontName='Georgia', alignment=TA_CENTER, leading=9.5))
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[132, 132, 132, 132])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 4))

    # Infografía Figura 6 (FX Spot y Rofex)
    img_fx = os.path.join(DIR_FIG, "chart_indec_6_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=540, height=295))
    story.append(Spacer(1, 3))

    story.append(Paragraph(
        "<b>Lectura Estratégica:</b> La compresión del spread CCL-MEP hacia la zona del 4,1% convalida un flujo constante de liquidación por esquema blend y arbitraje de exportadores. "
        "En futuros, la tasa implícita del 35,2% en la posición corta se ubica por debajo de la tasa de política monetaria en términos efectivos, reduciendo el costo de cobertura cambiaria para importadores.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: RENTA FIJA, ESTRATEGIA TÁCTICA & POSICIONAMIENTO
    # =========================================================================
    story.append(Paragraph("2. Curvas Soberanas, Posicionamiento Táctico y Renta Fija", h1_style))
    story.append(Paragraph(
        "El tramo corto de la curva en pesos continúa dominado por las <b>Lecaps</b> con rendimientos del 38,5% al 39,2% TNA, ofreciendo un premio atractivo en términos de tasa real ex-ante (1,2% mensual sobre el sendero inflacionario proyectado). "
        "En la curva soberana en dólares, los títulos Globales (GD35 y GD38) operan con paridades del 68,5% y rendimientos del 11,2% TIR, consolidando un diferencial de legislación (spread GD vs AL) en mínimos históricos de 15 puntos básicos.",
        body_style
    ))

    story.append(Paragraph("Cuadro 1. Matriz de Recomendaciones Tácticas y Ratings por Activo", h2_style))
    tab_rec_data = [
        [
            Paragraph("Instrumento / Segmento", cell_header_style),
            Paragraph("Ticker / Plazo", cell_header_style),
            Paragraph("Rendimiento", cell_header_style),
            Paragraph("Rating Táctico", cell_header_style),
            Paragraph("Tesis de Inversión y Racional Financiero", cell_header_style)
        ],
        [
            Paragraph("<b>Lecap Tramo Corto</b>", cell_style_left),
            Paragraph("S31O6 (60d)", cell_style_center),
            Paragraph("38,90% TNA", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Carry trade eficiente en ARS; TEM de 3,24% supera la inflación proyectada.", cell_style_left)
        ],
        [
            Paragraph("<b>Bono Soberano USD</b>", cell_style_left),
            Paragraph("GD35 (2035)", cell_style_center),
            Paragraph("11,20% TIR", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Elevada convexidad ante continuidad de compresión de riesgo país hacia 600 pb.", cell_style_left)
        ],
        [
            Paragraph("<b>Bono CER / Boncer</b>", cell_style_left),
            Paragraph("TZX26 (CER+)", cell_style_center),
            Paragraph("CER + 7,80%", cell_style_center),
            Paragraph("<font color='#D97706'><b>NEUTRAL</b></font>", cell_style_center),
            Paragraph("Cobertura balanceada frente a volatilidad de precios regulados en tarifas.", cell_style_left)
        ],
        [
            Paragraph("<b>Bopreal Serie 3</b>", cell_style_left),
            Paragraph("BPY26", cell_style_center),
            Paragraph("10,40% TIR", cell_style_center),
            Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center),
            Paragraph("Sintético hard dollar de alta calidad crediticia para perfiles corporativos.", cell_style_left)
        ],
        [
            Paragraph("<b>Bono Soberano Corto</b>", cell_style_left),
            Paragraph("AL30", cell_style_center),
            Paragraph("12,80% TIR", cell_style_center),
            Paragraph("<font color='#991B1B'><b>SUBPONDERAR</b></font>", cell_style_center),
            Paragraph("Rotación hacia tramos largos (GD35/GD38) con mayor potencial de apreciación de capital.", cell_style_left)
        ]
    ]
    t_rec = Table(tab_rec_data, colWidths=[105, 75, 75, 85, 200])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.8, PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_CARD]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_rec)
    story.append(Spacer(1, 4))

    # Infografía Figura 1 (Tasas & Breakeven)
    img_rates = os.path.join(DIR_FIG, "chart_indec_1_rates.png")
    if os.path.exists(img_rates):
        story.append(Image(img_rates, width=540, height=275))
    story.append(Spacer(1, 3))

    story.append(Paragraph(
        "<b>Conclusión de Mesa:</b> Se recomienda sostener una asignación del <b>60% en activos en moneda local (Lecap corta)</b> para capitalizar el carry trade, "
        "complementada con un <b>40% en soberanos hard dollar (GD35/Bopreal)</b> para resguardo de capital ante eventuales ruidos en la salida de controles de capitales.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvasDiario)
    
    # Copiar al directorio ejecutivo
    import shutil
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, "2026-08-21_Monitor_Diario_Mercados.pdf"))
    print(f"[OK] Monitor Diario ReportLab generado: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_monitor_diario_reportlab()
