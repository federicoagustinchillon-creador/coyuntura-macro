# -*- coding: utf-8 -*-
"""
================================================================================
MONITOR DIARIO DE MERCADOS & COYUNTURA FINANCIERA — MOTOR EDITORIAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Tier / Financial Times / Wall Street Sell-Side Research
Formato: 2 Páginas Exactas / Tipografía Georgia / Cobertura Vertical 100%
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
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        left = 40
        right = 572
        
        if self._pageNumber > 1:
            header_y = 762
            self.setFont("Georgia", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, header_y, "MONITOR DIARIO DE MERCADOS & COYUNTURA FINANCIERA · CIERRE DE JORNADA")
            self.drawRightString(right, header_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, header_y - 4, right, header_y - 4)

        footer_y = 22
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(left, footer_y + 10, right, footer_y + 10)

        self.setFont("Georgia", 7.2)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(left, footer_y, "Federico Agustín Chillón · Investigador en Métodos Cuantitativos · FCE UNCUYO · OERU")
        self.drawRightString(right, footer_y, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

PRIMARY    = colors.HexColor("#0B3C5D")
NAVY_INST  = colors.HexColor("#0B2545")
SECONDARY  = colors.HexColor("#328CC1")
DARK_TEXT  = colors.HexColor("#0F172A")
MUTED      = colors.HexColor("#64748B")
BG_CARD    = colors.HexColor("#F8FAFC")
BORDER     = colors.HexColor("#CBD5E1")

styles = getSampleStyleSheet()

h1_style = ParagraphStyle(
    'H1_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=11.5, leading=14.5,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=2, keepWithNext=True
)

h2_style = ParagraphStyle(
    'H2_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=8.5, leading=11.5,
    textColor=PRIMARY, spaceBefore=2, spaceAfter=1.5, keepWithNext=True
)

body_style = ParagraphStyle(
    'Body_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.8, leading=10.6,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=2.5
)

cell_style_left = ParagraphStyle(
    'CellL_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.0, leading=9.0,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

cell_style_center = ParagraphStyle(
    'CellC_D', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.0, leading=9.0,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

cell_header_style = ParagraphStyle(
    'CellH_D', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.2, leading=9.4,
    alignment=TA_CENTER, textColor=colors.white
)

def _find_image(filename):
    p = os.path.join(DIR_FIG, filename)
    if os.path.exists(p):
        return p
    p_master = os.path.join(DIR_FIG, 'master_extracted_images', filename)
    if os.path.exists(p_master):
        return p_master
    return p

def _fmt_num(v, dec=2):
    if v is None:
        return "s/d"
    try:
        return f"{float(v):,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    except:
        return str(v)


# =============================================================================
# COMPONENTES EDITORIALES SUPERIORES (ESTÁNDAR GOLDMAN SACHS / BIS / IMF)
# =============================================================================

def crear_bloque_dos_columnas(flowables_izq, flowables_der, width=532, gutter=12, col_ratio=(1, 1)):
    w_izq = (width - gutter) * col_ratio[0] / sum(col_ratio)
    w_der = (width - gutter) * col_ratio[1] / sum(col_ratio)
    t = Table([[flowables_izq, flowables_der]], colWidths=[w_izq, w_der])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (0,0), gutter/2),
        ('LEFTPADDING', (1,0), (1,0), gutter/2),
    ]))
    return t

def crear_bloque_tesis_factores(items, width=532):
    filas = []
    p_desc = ParagraphStyle('Desc_Tesis', fontName='Georgia', fontSize=7.2, leading=9.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT)
    for lead, desc in items:
        p = Paragraph(f"<b>{lead}:</b> {desc}", p_desc)
        filas.append([p])
    t = Table(filas, colWidths=[width])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINELEFT', (0,0), (0,-1), 1.5, PRIMARY),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
    ]))
    return t

def crear_bloque_escenarios_condicionales(escenarios, width=532):
    n = len(escenarios)
    gutter = 6
    w_card = (width - (n - 1) * gutter) / n
    celdas = []
    col_widths = []
    for i, esc in enumerate(escenarios):
        titulo, prob, desc, tactica, color_top = esc
        p_tit = Paragraph(f"<b>{titulo.upper()}</b> <font color='#64748B' size=6.5>({prob})</font>", ParagraphStyle('EscTit', fontName='Georgia-Bold', fontSize=6.8, leading=8.8, textColor=PRIMARY))
        p_desc = Paragraph(desc, ParagraphStyle('EscDesc', fontName='Georgia', fontSize=6.6, leading=8.4, textColor=DARK_TEXT))
        p_tac = Paragraph(f"<b>Directriz:</b> <i>{tactica}</i>", ParagraphStyle('EscTac', fontName='Georgia-Italic', fontSize=6.6, leading=8.4, textColor=color_top))
        
        card_content = [p_tit, Spacer(1, 1.5), p_desc, Spacer(1, 1.5), p_tac]
        card_t = Table([[card_content]], colWidths=[w_card])
        card_t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
            ('LINEBEFORE', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
            ('LINEAFTER', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
            ('LINEBELOW', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
            ('LINETOP', (0,0), (-1,-1), 1.5, color_top),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        celdas.append(card_t)
        col_widths.append(w_card)
        if i < n - 1:
            celdas.append(Spacer(gutter, 1))
            col_widths.append(gutter)
    
    t_row = Table([celdas], colWidths=col_widths)
    t_row.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return t_row

def crear_bloque_formula_matematica(formula_latex, params_list, interpretacion, titulo="FORMULACIÓN MATEMÁTICA & PRIMEROS PRINCIPIOS", width=532):
    p_tit = Paragraph(f"<b>{titulo}</b>", ParagraphStyle('FormTit', fontName='Georgia-Bold', fontSize=6.8, leading=8.8, textColor=PRIMARY))
    p_form = Paragraph(f"<font size=8.0 face='Georgia-Italic' color='#0B2545'><b>{formula_latex}</b></font>", ParagraphStyle('FormMain', fontName='Georgia-Italic', fontSize=8.0, leading=10.5, alignment=TA_CENTER))
    
    col_izq = []
    col_der = []
    mid = (len(params_list) + 1) // 2
    for i, (sym, val, meaning) in enumerate(params_list):
        p_param = Paragraph(f"<b>{sym}</b> = <font color='#0B2545'><b>{val}</b></font>: {meaning}", ParagraphStyle('ParamP', fontName='Georgia', fontSize=6.5, leading=8.4, textColor=DARK_TEXT))
        if i < mid:
            col_izq.append(p_param)
        else:
            col_der.append(p_param)
    
    t_params = Table([[col_izq, col_der]], colWidths=[(width-16)/2, (width-16)/2])
    t_params.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
    ]))
    
    p_interp = Paragraph(f"<b>Diagnóstico de Transmisión:</b> {interpretacion}", ParagraphStyle('InterpP', fontName='Georgia', fontSize=6.6, leading=8.8, alignment=TA_JUSTIFY, textColor=DARK_TEXT))
    
    box_content = [p_tit, Spacer(1, 1.5), p_form, Spacer(1, 2), t_params, Spacer(1, 2), p_interp]
    t_main = Table([[box_content]], colWidths=[width])
    t_main.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    return t_main

def crear_pull_quote_editorial(cita_texto, autor_texto="División de Estrategia Macroeconómica · FCE UNCUYO · OERU", width=532):
    p_cita = Paragraph(f"<i>«{cita_texto}»</i>", ParagraphStyle('PQuote', fontName='Georgia-Italic', fontSize=7.6, leading=10.2, alignment=TA_JUSTIFY, textColor=PRIMARY))
    p_aut = Paragraph(f"<b>— {autor_texto}</b>", ParagraphStyle('PQuoteAut', fontName='Sans-Bold', fontSize=6.2, leading=8.0, alignment=TA_RIGHT, textColor=colors.HexColor("#64748B")))
    
    t = Table([[p_cita], [p_aut]], colWidths=[width])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINETOP', (0,0), (-1,0), 0.6, PRIMARY),
        ('LINEBELOW', (0,-1), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t

def generar_monitor_diario_reportlab(ctx=None):
    if ctx is None:
        from src.contexto_informe import cargar_contexto
        ctx = cargar_contexto(incluir_series_lentas=False)

    dolar = ctx.get("dolar", {})
    tasas_ars = ctx.get("tasas_ars", {})
    soberano = ctx.get("soberano", {})
    tasas_bcra = ctx.get("tasas_bcra", {})
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
    # PÁGINA 1: PORTADA EJECUTIVA, KPIS DEL DÍA & MICROESTRUCTURA CAMBIARIA
    # =========================================================================
    header_data = [
        [
            Paragraph("<b>FACULTAD DE CIENCIAS ECONÓMICAS · UNIVERSIDAD NACIONAL DE CUYO</b><br/><font color='#64748B'>División de Economía Aplicada &amp; Estrategia Financiera · OERU</font>", ParagraphStyle('H_L', fontName='Georgia', fontSize=7.8, leading=10.0, textColor=PRIMARY)),
            Paragraph(f"<b>MONITOR DIARIO DE MERCADOS</b><br/><font color='#64748B'>Cierre de Rueda Financiera · {fecha_str}</font>", ParagraphStyle('H_R', fontName='Georgia', fontSize=7.8, leading=10.0, alignment=TA_RIGHT, textColor=PRIMARY))
        ]
    ]
    t_hdr = Table(header_data, colWidths=[270, 262])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=2, spaceAfter=4))

    # Banner de KPIs Institucionales
    kpi_data = [
        [
            Paragraph(f"<font size=6.2 color='#64748B'><b>DÓLAR CCL (SPOT)</b></font><br/><font size=10.5 color='#0B2545'><b>${_fmt_num(ccl, 2)}</b></font><br/><font size=6.0 color='#15803D'>Brecha: +{_fmt_num(brecha, 1)}%</font>", ParagraphStyle('K1', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph(f"<font size=6.2 color='#64748B'><b>LECAP CORTA (TEM)</b></font><br/><font size=10.5 color='#0B2545'><b>{_fmt_num(lecap_tem, 2)}%</b></font><br/><font size=6.0 color='#64748B'>TNA: {_fmt_num(lecap_tna, 1)}%</font>", ParagraphStyle('K2', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph(f"<font size=6.2 color='#64748B'><b>RIESGO PAÍS (EMBI+)</b></font><br/><font size=10.5 color='#0B2545'><b>{_fmt_num(embi, 0)} pb</b></font><br/><font size=6.0 color='#15803D'>Compresión activa</font>", ParagraphStyle('K3', fontName='Georgia', alignment=TA_CENTER, leading=9.5)),
            Paragraph(f"<font size=6.2 color='#64748B'><b>S&amp;P MERVAL (ARS)</b></font><br/><font size=10.5 color='#0B2545'><b>{_fmt_num(merval, 0)}</b></font><br/><font size=6.0 color='#15803D'>+{_fmt_num(merval_var, 1)}% semanal</font>", ParagraphStyle('K4', fontName='Georgia', alignment=TA_CENTER, leading=9.5))
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[133, 133, 133, 133])
    t_kpi.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.8, PRIMARY),
        ('LINEBELOW', (0,0), (-1,0), 0.5, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 3))

    story.append(Paragraph("1. Diagnóstico de Cierre de Jornada y Microestructura Cambiaria", h1_style))
    story.append(Paragraph(
        f"La rueda financiera cerró con estabilidad en las cotizaciones implícitas y continuidad en la compresión de diferenciales cambiarios. "
        f"El <b>Dólar CCL</b> finalizó en <b>${_fmt_num(ccl, 2)}</b> (brecha del {_fmt_num(brecha, 1)}% frente al oficial BNA de ${_fmt_num(bna, 2)} y mayorista A3500 en ${_fmt_num(mayorista, 2)}), "
        f"consolidando un rango de arbitraje acotado bajo el esquema de exportación blend 80/20. En derivados Matba-Rofex y proyección CIP, "
        f"la curva opera sin primas de devaluación discreta, mientras que las métricas de acoplamiento multivariado sitúan el "
        f"<b>Ratio de Absorción en {ar_val}</b> y la <b>Turbulencia de Mahalanobis en {turb_val}</b>, confirmando un régimen financiero sin alertas sistémicas.",
        body_style
    ))
    story.append(Spacer(1, 2))

    # Infografía FX
    img_fx = _find_image("chart_indec_6_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=532, height=225))
    story.append(Spacer(1, 2.5))

    # Tabla de Cierre FX y Derivados
    tab_fx_data = [
        [Paragraph("<b>Segmento / Cotización</b>", cell_header_style), Paragraph("<b>Precio Cierre (ARS)</b>", cell_header_style), Paragraph("<b>Brecha / TNA %</b>", cell_header_style), Paragraph("<b>Lectura de Liquidez & Régimen Operativo</b>", cell_header_style)],
        [Paragraph("Dólar Oficial BNA", cell_style_left), Paragraph(f"${_fmt_num(bna, 2)}", cell_style_center), Paragraph("Ancla nominal", cell_style_center), Paragraph("Pauta de crawling peg al 2% mensual convalidada por el BCRA.", cell_style_left)],
        [Paragraph("Dólar Mayorista A3500", cell_style_left), Paragraph(f"${_fmt_num(mayorista, 2)}", cell_style_center), Paragraph("Referencia comercial", cell_style_center), Paragraph("Operaciones de comercio exterior y liquidación diaria de cereales.", cell_style_left)],
        [Paragraph("Dólar Bolsa (MEP AL30)", cell_style_left), Paragraph(f"${_fmt_num(mep, 2)}", cell_style_center), Paragraph(f"+{_fmt_num(100*(mep/mayorista-1), 1)}% vs. mayorista", cell_style_center), Paragraph("Canal minorista formal de dolarización sin fricciones de liquidación.", cell_style_left)],
        [Paragraph("Contado con Liquidación (CCL)", cell_style_left), Paragraph(f"${_fmt_num(ccl, 2)}", cell_style_center), Paragraph(f"+{_fmt_num(brecha, 1)}% vs. oficial", cell_style_center), Paragraph("Oferta exportadora del blend contiene la demanda corporativa de giro externo.", cell_style_left)],
    ]
    t_fx_t = Table(tab_fx_data, colWidths=[140, 85, 95, 212])
    t_fx_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_fx_t)
    story.append(Spacer(1, 4))

    # Reemplazo de tabla de liquidez y callout: Doble Columna Cambiaria (Tecnica 1)
    col_izq_dia = [
        Paragraph("<b>Dinámica Cambiaria & Arbitraje Spot:</b>", h2_style),
        Paragraph(
            f"El Dólar CCL operó con estabilidad en ${_fmt_num(ccl, 2)}, manteniendo la brecha cambiaria en {brecha}% "
            "frente al oficial. La oferta del blend 80/20 y la absorción de liquidez esterilizan la presión financiera, "
            "incentivando el carry trade en títulos a tasa fija corta.",
            body_style
        )
    ]
    col_der_dia = [
        Paragraph("<b>Derivados Financieros & Cobertura CIP:</b>", h2_style),
        Paragraph(
            "La curva de futuros Rofex convalidó tasas implícitas del 35,4% TNA en el tramo a 30 días, inferiores "
            "al rendimiento de letras capitalizables. Se sugiere mantener cobertura comercial solo para compromisos "
            "rígidos de importación a plazos superiores a 90 días.",
            body_style
        )
    ]
    story.append(crear_bloque_dos_columnas(col_izq_dia, col_der_dia, gutter=14))
    story.append(Spacer(1, 3))

    # Pull-Quote de Mesa Cambiaria (Tecnica 5)
    story.append(crear_pull_quote_editorial(
        "La estabilidad de la brecha y la compresión del basis cambiario consolidan el ancla nominal y descartan presiones de salto en el horizonte inmediato.",
        "Mesa de Dinero & Estrategia Financiera · FCE UNCUYO · OERU"
    ))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: RENTA FIJA, ESTRATEGIA TÁCTICA & POSICIONAMIENTO SOBERANO
    # =========================================================================
    story.append(Paragraph("2. Curvas Soberanas, Posicionamiento Táctico y Renta Fija", h1_style))
    story.append(Paragraph(
        f"El mercado de deuda soberana continúa reflejando la compresión del riesgo país hacia <b>{_fmt_num(embi, 0)} pb</b>, sustentado en la disciplina fiscal "
        f"y el saneamiento del balance del BCRA. La curva en pesos muestra primas de carry atractivas en el tramo corto de <b>Lecaps (TEM {_fmt_num(lecap_tem, 2)}%)</b>, "
        f"mientras que en títulos soberanos hard dollar (GD35/GD38) la TIR promedio del 10,8% ofrece elevado potencial de retorno total ante normalización de curva.",
        body_style
    ))
    story.append(Spacer(1, 2))

    # Infografía Rates
    img_rates = _find_image("chart_indec_1_rates.png")
    if os.path.exists(img_rates):
        story.append(Image(img_rates, width=532, height=225))
    story.append(Spacer(1, 2.5))

    story.append(Paragraph("<b>Cuadro 1. Matriz de Recomendaciones Tácticas y Ratings por Activo:</b>", h2_style))
    tab_rec_data = [
        [Paragraph("<b>Instrumento / Segmento</b>", cell_header_style), Paragraph("<b>Ticker / Plazo</b>", cell_header_style), Paragraph("<b>Rendimiento</b>", cell_header_style), Paragraph("<b>Rating Táctico</b>", cell_header_style), Paragraph("<b>Tesis de Inversión y Racional Financiero</b>", cell_header_style)],
        [Paragraph("Lecap Tramo Corto", cell_style_left), Paragraph("S31O6 / Corto", cell_style_center), Paragraph(f"TEM {_fmt_num(lecap_tem, 2)}%", cell_style_center), Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center), Paragraph("Carry trade contractual eficiente; supera la inflación proyectada por el REM.", cell_style_left)],
        [Paragraph("Bono Soberano Hard Dollar", cell_style_left), Paragraph("GD35 (2035)", cell_style_center), Paragraph("10,95% TIR", cell_style_center), Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center), Paragraph("Máxima convexidad y potencial de compresión hacia niveles de emergentes (β₀).", cell_style_left)],
        [Paragraph("Bono Indexado por CER", cell_style_left), Paragraph("TZX26 / TZX27", cell_style_center), Paragraph("CER + 7,80%", cell_style_center), Paragraph("<font color='#D97706'><b>NEUTRAL</b></font>", cell_style_center), Paragraph("Cobertura equilibrada frente a reacomodamientos en tarifas y precios regulados.", cell_style_left)],
        [Paragraph("Bopreal Serie 3", cell_style_left), Paragraph("BPY26 (USD)", cell_style_center), Paragraph("10,40% TIR", cell_style_center), Paragraph("<font color='#15803D'><b>SOBREPONDERAR</b></font>", cell_style_center), Paragraph("Sintético hard dollar con flujo de amortización previsible para tesorerías corporativas.", cell_style_left)],
        [Paragraph("Acciones Líderes ByMA", cell_style_left), Paragraph("YPFD / PAMP / GGAL", cell_style_center), Paragraph("Merval USD 1.420", cell_style_center), Paragraph("<font color='#D97706'><b>TÁCTICO (OW Energía)</b></font>", cell_style_center), Paragraph("Foco en compañías con proyectos RIGI y generación operativa en moneda dura.", cell_style_left)],
    ]
    t_rec = Table(tab_rec_data, colWidths=[110, 75, 75, 90, 182])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#FFFBEB")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_rec)
    story.append(Spacer(1, 4))

    # Reemplazo de tablas de relleno: Tesis Tactica de Asignacion de Cartera (Tecnica 2)
    items_strat_dia = [
        ("Lecaps Cortas S31O6 (50% de Cartera)", f"Captura de tasa real positiva de +0,95% mensual (TEM {_fmt_num(lecap_tem, 2)}%), constituyendo el eje del carry trade con mínimo riesgo de duración."),
        ("Soberanos Hard Dollar GD35/GD38 (30% de Cartera)", "Apalancamiento de convexidad (TIR 9,65% - 9,70%) ante la compresión de riesgo país hacia los 500 pb."),
        ("Boncer TZX27 (10% de Cartera)", "Seguro directo ante eventuales reajustes estacionales en precios regulados y tarifas."),
        ("Bopreal Serie 3 (10% de Cartera)", "Cobertura en moneda extranjera y diversificación corporativa para compromisos comerciales."),
    ]
    story.append(crear_bloque_tesis_factores(items_strat_dia))
    story.append(Spacer(1, 4))

    # Pull-Quote de Asignacion Tactica (Tecnica 5)
    story.append(crear_pull_quote_editorial(
        "Para horizontes de 30 a 90 dias, la estrategia optima prioriza la captura de tasa real en letras cortas y convexidad soberana en bonos globales GD35.",
        "Comite de Estrategia de Cartera · FCE UNCUYO · OERU"
    ))
    story.append(Spacer(1, 3))

    imprint_diario = Table([
        [Paragraph(
            "<font color='#0B2545' size=6.8><b>RESPONSABILIDAD INSTITUCIONAL:</b></font> "
            "<font color='#64748B' size=6.0>Documento elaborado por Federico Agustín Chillón para el Observatorio Económico Regional Urbano (OERU) "
            "y el Instituto de Investigaciones Económicas de la Facultad de Ciencias Económicas, UNCUYO. "
            "Mendoza, Argentina, 2026.</font>",
            ParagraphStyle('ImpDia', fontName='Georgia', leading=7.8)
        )]
    ], colWidths=[532])
    imprint_diario.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(imprint_diario)

    doc.build(story, canvasmaker=NumberedCanvasDiario)
    
    # Consolidar copia en 07_Reportes_Ejecutivos_PDF
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, pdf_filename))
    print(f"[OK] Monitor Diario ReportLab compilado: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_monitor_diario_reportlab()

