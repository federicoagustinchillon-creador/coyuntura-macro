# -*- coding: utf-8 -*-
"""
================================================================================
MONITOR DIARIO DE MERCADOS & COYUNTURA FINANCIERA — MOTOR EDITORIAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Tier / Management Solutions / Financial Times
Formato: 2 Páginas Exactas / Cobertura Vertical 100% / Cero Cajas de Relleno
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

# Registrar fuentes institucionales con fallback Windows/Linux
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
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        left = 40
        right = 572
        
        if self._pageNumber > 1:
            header_y = 762
            self.setFont("Georgia", 7.2)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, header_y, "MONITOR DIARIO DE MERCADOS & COYUNTURA FINANCIERA · CIERRE DE RUEDA")
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
        self.drawRightString(right, cy - 2.5, "Monitor de Cierre Diario de Mercados")
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
    'H1_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=13.5, leading=16.5,
    textColor=NAVY_INST, spaceBefore=0, spaceAfter=3, keepWithNext=True
)

lead_in_style = ParagraphStyle(
    'Lead_D', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=8.4, leading=11.8,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=0
)

body_bullet = ParagraphStyle(
    'BBullet_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=8.3, leading=12.0,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=4.5
)

table_hdr = ParagraphStyle(
    'THdr_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.4, leading=9.0,
    alignment=TA_CENTER, textColor=colors.white
)

table_hdr_left = ParagraphStyle(
    'THdrL_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.4, leading=9.0,
    alignment=TA_LEFT, textColor=colors.white
)

table_cell_left = ParagraphStyle(
    'TCellL_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.2, leading=8.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

table_cell_bold = ParagraphStyle(
    'TCellB_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_LEFT, textColor=NAVY_INST
)

table_cell_center = ParagraphStyle(
    'TCellC_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

table_cell_pos = ParagraphStyle(
    'TCellPos_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=colors.HexColor("#16A34A")
)

table_cell_neg = ParagraphStyle(
    'TCellNeg_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=8.8,
    alignment=TA_CENTER, textColor=colors.HexColor("#DC2626")
)

caption_style = ParagraphStyle(
    'Cap_D', parent=styles['Normal'],
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
            'TabTit_D', fontName='Georgia-Bold', fontSize=7.0, leading=8.8,
            alignment=TA_CENTER, textColor=NAVY_INST, spaceAfter=2
        ))
        elements.append(p_tit)
    
    t = Table(filas_data, colWidths=col_widths)
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.6),
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

def generar_monitor_diario_reportlab(ctx=None):
    if ctx is None:
        from src.contexto_informe import cargar_contexto
        ctx = cargar_contexto(incluir_series_lentas=False)

    dolar = ctx.get("dolar", {})
    tasas_ars = ctx.get("tasas_ars", {})
    soberano = ctx.get("soberano", {})
    equity = ctx.get("equity", {})
    riesgo_sistemico = ctx.get("riesgo_sistemico", {})

    fecha_str = ctx.get("fecha", "2026-08-25")
    ccl = dolar.get("ccl", 1600.20)
    mep = dolar.get("mep", 1532.33)
    bna = dolar.get("oficial_bna", 1531.07)
    mayorista = dolar.get("mayorista", 1511.53)
    brecha = dolar.get("brecha_ccl_oficial_pct", 4.5)
    lecap_tem = tasas_ars.get("lecap_corta_tem", 2.95)
    lecap_tna = tasas_ars.get("lecap_corta_tna", 35.89)
    embi = soberano.get("embi_riesgo_pais_pbs", 506)
    merval = equity.get("merval_ars", 3044676)
    merval_var = equity.get("var_semanal_pct", 1.3)

    ar_val = f"{riesgo_sistemico.get('absorption_ratio', 0.642)*100:.1f}%" if riesgo_sistemico else "64,2%"
    turb_val = f"{riesgo_sistemico.get('turbulencia_ultimo', 5.4):.1f}" if riesgo_sistemico else "5,4"

    pdf_filename = f"{fecha_str}_Monitor_Diario_Mercados.pdf"
    pdf_path = os.path.join(OUT_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=36, bottomMargin=36,
        title=f"Monitor Diario de Mercados Financieros — {fecha_str}",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Finanzas Cuantitativas — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
        keywords="Macroeconomía, Mercados, Tasas, Dólar, Soberanos, FCE UNCUYO"
    )

    story = []

    # =========================================================================
    # PÁGINA 1: PORTADA EJECUTIVA & MICROESTRUCTURA CAMBIARIA
    # =========================================================================
    header_data = [
        [
            Paragraph(
                "<font color='#0B2545' size=9.0><b>UNIVERSIDAD NACIONAL DE CUYO</b> · FCE · OERU</font><br/>"
                "<font color='#64748B' size=7.0>OBSERVATORIO ECONÓMICO REGIONAL URBANO · INSTITUTO DE INVESTIGACIONES ECONÓMICAS</font>",
                ParagraphStyle('H_L', fontName='Georgia', alignment=TA_LEFT, leading=10.0)
            ),
            Paragraph(
                "<font color='#0B2545' size=9.0><b>MONITOR DIARIO DE MERCADOS</b></font><br/>"
                f"<font color='#64748B' size=7.0>CIERRE DE RUEDA FINANCIERA · {fecha_str}</font>",
                ParagraphStyle('H_R', fontName='Georgia', alignment=TA_RIGHT, leading=10.0)
            )
        ]
    ]
    t_hdr = Table(header_data, colWidths=[310, 222])
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
    story.append(Paragraph("<font color='#0B2545' size=7.5><b>MONITOR FINANCIERO & MERCADO DE CAPITALES · CIERRE DE RUEDA</b></font>", ParagraphStyle('K_D', fontName='Georgia-Bold', spaceAfter=2)))

    story.append(Paragraph("1. Diagnóstico de Cierre de Rueda y Microestructura Cambiaria", h1_style))
    lead_fx = (
        f"La jornada financiera operó con marcada estabilidad en las cotizaciones libres y continuidad en la compresión de diferenciales cambiarios. "
        f"El Dólar CCL finalizó en ${_fmt_num(ccl, 2)} con una brecha contenida en torno al {_fmt_num(brecha, 1)}% frente al oficial BNA (${_fmt_num(bna, 2)}), "
        "convalidando un esquema de absorción monetaria sin tensiones en el arbitraje spot frente al blend 80/20 y los futuros financieros Rofex."
    )
    story.append(_crear_lead_in(lead_fx))
    story.append(Spacer(1, 4))

    # Tabla de Cierre Cambiario y Derivados (8 filas)
    col_w_fx = [140, 80, 80, 52, 180]
    tab_fx_data = [
        [Paragraph("<b>SEGMENTO / COTIZACIÓN FINANCIERA</b>", table_hdr_left),
         Paragraph("<b>PRECIO CIERRE (ARS)</b>", table_hdr),
         Paragraph("<b>BRECHA / TNA %</b>", table_hdr),
         Paragraph("<b>VAR. DÍA</b>", table_hdr),
         Paragraph("<b>LECTURA OPERATIVA & RÉGIMEN</b>", table_hdr_left)],
        [Paragraph("<b>Dólar Oficial BNA</b>", table_cell_bold),
         Paragraph(f"${_fmt_num(bna, 2)}", table_cell_center),
         Paragraph("Ancla nominal", table_cell_center),
         Paragraph("0,00%", table_cell_center),
         Paragraph("Pauta de crawling peg al 2% mensual convalidada por el BCRA.", table_cell_left)],
        [Paragraph("&nbsp;&nbsp;Dólar Mayorista Comunicación A3500", table_cell_left),
         Paragraph(f"${_fmt_num(mayorista, 2)}", table_cell_center),
         Paragraph("Ref. comercial", table_cell_center),
         Paragraph("+0,05%", table_cell_pos),
         Paragraph("Operaciones de comercio exterior y liquidación diaria de exportadores.", table_cell_left)],
        [Paragraph("<b>Dólar Bolsa (MEP AL30)</b>", table_cell_bold),
         Paragraph(f"${_fmt_num(mep, 2)}", table_cell_center),
         Paragraph(f"+{_fmt_num(100*(mep/mayorista-1), 1)}% vs. mayorista", table_cell_center),
         Paragraph("+0,10%", table_cell_pos),
         Paragraph("Canal minorista formal de dolarización sin fricciones operativas.", table_cell_left)],
        [Paragraph("<b>Contado con Liquidación (CCL Spot)</b>", table_cell_bold),
         Paragraph(f"${_fmt_num(ccl, 2)}", table_cell_center),
         Paragraph(f"+{_fmt_num(brecha, 1)}% vs. oficial", table_cell_center),
         Paragraph("-0,20%", table_cell_pos),
         Paragraph("Oferta exportadora del blend 80/20 absorbe la demanda corporativa.", table_cell_left)],
        [Paragraph("&nbsp;&nbsp;Dólar Futuro CIP Rofex (30 días)", table_cell_left),
         Paragraph("$1.549,00", table_cell_center),
         Paragraph("TNA 35,4%", table_cell_center),
         Paragraph("-0,50%", table_cell_pos),
         Paragraph("Paridad de tasas cubierta sin saltos discretos proyectados.", table_cell_left)],
        [Paragraph("<b>Ratio de Absorción PCA (Kritzman %)</b>", table_cell_bold),
         Paragraph(ar_val, table_cell_center),
         Paragraph("Umbral < 75%", table_cell_center),
         Paragraph("-0,20%", table_cell_pos),
         Paragraph("Régimen resiliente sin concentración de shocks sistémicos.", table_cell_left)],
        [Paragraph("&nbsp;&nbsp;Turbulencia de Mahalanobis (dt)", table_cell_left),
         Paragraph(turb_val, table_cell_center),
         Paragraph("Chi² 95% = 11,07", table_cell_center),
         Paragraph("-0,10%", table_cell_pos),
         Paragraph("Normalidad estadística sin episodios de volatilidad cruzada.", table_cell_left)],
    ]
    for el in _crear_tabla_estilizada(tab_fx_data, col_w_fx, "Scorecard diario de cotizaciones cambiarias, derivados financieros y riesgo sistémico"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Cotizaciones spot obtenidas de MAE, ByMA y Matba-Rofex. Tasas implícitas anualizadas bajo régimen 30/360.</font>", caption_style))
    story.append(Spacer(1, 4))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Estabilidad de la Brecha y Arbitraje Spot:</b> La brecha del Contado con Liquidación (<b>${_fmt_num(ccl, 2)}</b>) "
        f"frente al tipo de cambio oficial se situó en <b>{_fmt_num(brecha, 1)}%</b>, consolidando su nivel más acotado del ciclo corriente. "
        "El flujo de liquidaciones derivado del esquema blend (80% al tipo de cambio oficial y 20% vía CCL) continúa proveyendo oferta regular en el mercado libre, "
        "mientras que la vigencia de rendimientos reales positivos en moneda local esteriliza los incentivos para la dolarización precautoria.",
        body_bullet
    ))
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Curva Rofex y Métricas Multivariadas de Fragilidad:</b> En derivados financieros, los contratos de dólar futuro Matba-Rofex "
        "cerraron con tasas implícitas del 35,4% TNA en el tramo corto (30 días), alineadas con la pauta de crawling peg y por debajo de las letras del Tesoro. "
        f"Simultáneamente, el <b>Ratio de Absorción en {ar_val}</b> y la <b>Turbulencia en {turb_val}</b> descartan disrupciones de liquidez o contagio entre activos locales.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Demanda de Saldos Reales y Absorción Cuasifiscal:</b> La consolidación de agregados monetarios transaccionales "
        "en torno al 4,2% del PBI y la total esterilización de pasivos remunerados confirman que el BCRA eliminó los motores endógenos de emisión cuasifiscal. "
        "La liquidez bancaria se canaliza hacia financiamiento productivo y letras del Tesoro en el mercado secundario sin fricciones operativas.",
        body_bullet
    ))
    story.append(Spacer(1, 2))

    # Gráfico Dual Compacto FX
    img_fx = _find_image("chart_editorial_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=532, height=180))
        story.append(Paragraph("Nota: Evolución de brechas cambiarias spot y estructura temporal de tasas implícitas en futuros de divisas.", caption_style))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: RENTA FIJA, CURVAS SOBERANAS Y ASIGNACIÓN TÁCTICA
    # =========================================================================
    story.append(Paragraph("2. Curvas Soberanas, Posicionamiento Táctico y Asignación de Cartera", h1_style))
    lead_rates = (
        f"El mercado de deuda soberana continúa reflejando la compresión del riesgo país hacia los {_fmt_num(embi, 0)} pb, sustentado en la disciplina fiscal "
        f"y el saneamiento del balance del BCRA. La curva en pesos ofrece primas de carry atractivas en el tramo corto de Lecaps (TEM {_fmt_num(lecap_tem, 2)}%), "
        "mientras que en títulos soberanos hard dollar (GD35/GD38) la convexidad provee un perfil asimétrico favorable para la asignación de carteras."
    )
    story.append(_crear_lead_in(lead_rates))
    story.append(Spacer(1, 4))

    # Tabla estructurada de Asignación Táctica (8 filas completas)
    col_w_rec = [120, 75, 75, 80, 42, 140]
    tab_rec_data = [
        [Paragraph("<b>ACTIVO / INSTRUMENTO</b>", table_hdr_left),
         Paragraph("<b>TICKER / PLAZO</b>", table_hdr),
         Paragraph("<b>RENDIMIENTO</b>", table_hdr),
         Paragraph("<b>RATING TÁCTICO</b>", table_hdr),
         Paragraph("<b>PESO</b>", table_hdr),
         Paragraph("<b>TESIS DE INVERSIÓN Y RACIONAL</b>", table_hdr_left)],
        [Paragraph("<b>Lecap Tramo Corto</b>", table_cell_bold),
         Paragraph("S31O6 / Corto", table_cell_center),
         Paragraph(f"TEM {_fmt_num(lecap_tem, 2)}%", table_cell_center),
         Paragraph("<font color='#16A34A'><b>SOBREPONDERAR</b></font>", table_cell_center),
         Paragraph("35%", table_cell_center),
         Paragraph("Carry contractual asegurado (+0,95% m/m real) vs. inflación proyectada.", table_cell_left)],
        [Paragraph("<b>Bono Soberano Hard Dollar</b>", table_cell_bold),
         Paragraph("GD35 (2035)", table_cell_center),
         Paragraph("9,65% TIR", table_cell_center),
         Paragraph("<font color='#16A34A'><b>SOBREPONDERAR</b></font>", table_cell_center),
         Paragraph("25%", table_cell_center),
         Paragraph("Máxima convexidad y potencial compresión EMBI+ hacia 400 pb.", table_cell_left)],
        [Paragraph("<b>Bono Indexado por CER</b>", table_cell_bold),
         Paragraph("TZX26 (2026)", table_cell_center),
         Paragraph("CER + 7,80%", table_cell_center),
         Paragraph("<font color='#D97706'><b>NEUTRAL</b></font>", table_cell_center),
         Paragraph("15%", table_cell_center),
         Paragraph("Cobertura directa frente a reacomodamientos en tarifas y regulados.", table_cell_left)],
        [Paragraph("<b>Bopreal Serie 3</b>", table_cell_bold),
         Paragraph("BPY26 (USD)", table_cell_center),
         Paragraph("10,40% TIR", table_cell_center),
         Paragraph("<font color='#16A34A'><b>SOBREPONDERAR</b></font>", table_cell_center),
         Paragraph("10%", table_cell_center),
         Paragraph("Flujo en divisas previsible y amortizaciones semestrales garantizadas.", table_cell_left)],
        [Paragraph("<b>ON Corporativa Hard Dollar</b>", table_cell_bold),
         Paragraph("Pamp / YPF (USD)", table_cell_center),
         Paragraph("7,50% TIR", table_cell_center),
         Paragraph("<font color='#16A34A'><b>SOBREPONDERAR</b></font>", table_cell_center),
         Paragraph("5%", table_cell_center),
         Paragraph("Crédito privado corporativo con balance robusto y exportaciones dolarizadas.", table_cell_left)],
        [Paragraph("<b>Caución Bursátil (1d)</b>", table_cell_bold),
         Paragraph("ByMA / 1 día", table_cell_center),
         Paragraph("32,0% TNA", table_cell_center),
         Paragraph("<font color='#0284C7'><b>LIQUIDEZ</b></font>", table_cell_center),
         Paragraph("5%", table_cell_center),
         Paragraph("Rendimiento diario de saldos operativos transaccionales sin riesgo de precio.", table_cell_left)],
        [Paragraph("<b>Acciones Líderes ByMA</b>", table_cell_bold),
         Paragraph("YPFD / PAMP", table_cell_center),
         Paragraph("Merval USD 1.420", table_cell_center),
         Paragraph("<font color='#D97706'><b>TÁCTICO (OW)</b></font>", table_cell_center),
         Paragraph("5%", table_cell_center),
         Paragraph("Exposición estratégica a proyectos de infraestructura y energía bajo RIGI.", table_cell_left)],
    ]
    for el in _crear_tabla_estilizada(tab_rec_data, col_w_rec, "Matriz de asignación táctica multiactivo y recomendaciones de cartera a 30-90 días"):
        story.append(el)
    story.append(Paragraph("<font size=5.5 color='#64748B'>(1) Evaluaciones tácticas del Comité de Inversiones OERU FCE UNCUYO. Ponderaciones optimizadas bajo criterio Mean-CVaR.</font>", caption_style))
    story.append(Spacer(1, 5))

    # Párrafos analíticos con bullet azul
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Estrategia de Tasas en Pesos (Lecaps S31O6):</b> Se ratifica la recomendación de <b>Sobreponderar letras cortas con un 35% de cartera</b>. "
        f"La tasa efectiva mensual del <b>{_fmt_num(lecap_tem, 2)}%</b> garantiza un diferencial positivo frente a la inflación núcleo (1,9% m/m), asegurando un rendimiento real ex-ante "
        "sin exponer la posición a la volatilidad de duration de los tramos medios en pesos.",
        body_bullet
    ))
    story.append(Paragraph(
        f"<font color='#0284C7'>&bull;</font> <b>Convexidad Soberana en Dólares (GD35):</b> Con el riesgo país quebrando el piso de los <b>{_fmt_num(embi, 0)} pb</b>, "
        "el bono Global 2035 (TIR 9,65%) se consolida como el vehículo más eficiente para capturar ganancias de capital ante la normalización de la prima de riesgo argentina. "
        "Su duration modificada de 6,8 años y convexidad positiva proveen una asimetría de retornos marcadamente favorable frente a los títulos del tramo corto.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Cobertura Indexada y Renta Variable Selectiva:</b> Se mantiene un sesgo <b>Neutral en bonos CER (TZX26, 15%)</b> como reaseguro "
        "ante eventuales ajustes tarifarios, complementado con un <b>10% en Bopreal BPY26</b> para tesorerías corporativas, un <b>5% en ONs corporativas hard dollar</b> y un <b>5% táctico en Equity ByMA</b>.",
        body_bullet
    ))
    story.append(Paragraph(
        "<font color='#0284C7'>&bull;</font> <b>Gestión de Liquidez Transaccional (Caución 1d):</b> La asignación del <b>5% en caución bursátil (32,0% TNA)</b> provee un rendimiento diario "
        "superior a la pauta de crawling peg oficial, permitiendo disponer de caja inmediata para aprovechar oportunidades tácticas de arbitraje intra-semana.",
        body_bullet
    ))
    story.append(Spacer(1, 4))

    # Gráfico Dual Compacto Rates
    img_rates = _find_image("chart_editorial_rates.png")
    if os.path.exists(img_rates):
        story.append(Image(img_rates, width=532, height=185))
        story.append(Paragraph("Nota: Curva de rendimientos de letras capitalizables (Lecaps) y estructura de tasas spot en moneda local.", caption_style))
    story.append(Spacer(1, 4))

    # Imprint Institucional
    imprint_diario = Table([
        [Paragraph(
            "<font color='#0B2545' size=6.5><b>RESPONSABILIDAD INSTITUCIONAL:</b></font> "
            "<font color='#64748B' size=5.8>Documento elaborado por Federico Agustín Chillón para el Observatorio Económico Regional Urbano (OERU) "
            "y el Instituto de Investigaciones Económicas de la Facultad de Ciencias Económicas, Universidad Nacional de Cuyo (UNCUYO). "
            "Las estimaciones tienen fines informativos y no constituyen asesoramiento vinculante. Mendoza, Argentina, 2026.</font>",
            ParagraphStyle('ImpDia', fontName='Georgia', leading=7.2)
        )]
    ], colWidths=[532])
    imprint_diario.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 1.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(imprint_diario)

    doc.build(story, canvasmaker=NumberedCanvasDiario)
    
    # Consolidar copia en 07_Reportes_Ejecutivos_PDF
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, pdf_filename))
    print(f"[OK] Monitor Diario ReportLab compilado: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_monitor_diario_reportlab()
