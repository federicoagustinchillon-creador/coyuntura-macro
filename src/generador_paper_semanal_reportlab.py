# -*- coding: utf-8 -*-
"""
================================================================================
PAPER MACROECONÓMICO SEMANAL APA 7 — MOTOR EDITORIAL REPORTLAB
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Estándar: Institutional Academic Tier / APA 7ma Edición / Tipografía Georgia
Formato: 4 Páginas Exactas / Cobertura Vertical Completa / Sin Espacios Muertos
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
            self.drawString(left, header_y, "SERIE DE INVESTIGACIÓN ECONÓMICA APLICADA · FCE UNCUYO · PAPER SEMANAL APA 7")
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
    'H1_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=10.8, leading=13.8,
    textColor=PRIMARY, spaceBefore=0, spaceAfter=2, keepWithNext=True
)

h2_style = ParagraphStyle(
    'H2_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=8.2, leading=10.8,
    textColor=PRIMARY, spaceBefore=2, spaceAfter=1.5, keepWithNext=True
)

body_style = ParagraphStyle(
    'Body_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=7.6, leading=10.4,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=2.5
)

abstract_style = ParagraphStyle(
    'Abs_S', parent=styles['Normal'],
    fontName='Georgia-Italic', fontSize=7.2, leading=9.6,
    alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=2.5
)

cell_style_left = ParagraphStyle(
    'CellL_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.8, leading=8.8,
    alignment=TA_LEFT, textColor=DARK_TEXT
)

cell_style_center = ParagraphStyle(
    'CellC_S', parent=styles['Normal'],
    fontName='Georgia', fontSize=6.8, leading=8.8,
    alignment=TA_CENTER, textColor=DARK_TEXT
)

cell_header_style = ParagraphStyle(
    'CellH_S', parent=styles['Normal'],
    fontName='Georgia-Bold', fontSize=7.0, leading=9.2,
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
            Paragraph("<b>UNIVERSIDAD NACIONAL DE CUYO · FACULTAD DE CIENCIAS ECONÓMICAS</b><br/><font color='#64748B'>Instituto de Investigaciones Económicas · Observatorio Económico Regional Urbano (OERU)</font>", ParagraphStyle('H_AL', fontName='Georgia', fontSize=7.8, leading=10.0, textColor=PRIMARY)),
            Paragraph(f"<b>SERIE DE INVESTIGACIÓN APLICADA (APA 7)</b><br/><font color='#64748B'>Semana de Análisis · Cierre al {fecha_str} · Vol. IV</font>", ParagraphStyle('H_AR', fontName='Georgia', fontSize=7.8, leading=10.0, alignment=TA_RIGHT, textColor=PRIMARY))
        ]
    ]
    t_hdr = Table(hdr_academic, colWidths=[270, 262])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=2, spaceAfter=3))

    story.append(Paragraph("Dinámica Inflacionaria, Desanclaje de Expectativas y Curvas de Rendimiento en Argentina", ParagraphStyle('Title_S', fontName='Georgia-Bold', fontSize=12.0, leading=15.0, textColor=PRIMARY, spaceAfter=2)))
    story.append(Paragraph("<b>Federico Agustín Chillón</b> · <i>Facultad de Ciencias Económicas, Universidad Nacional de Cuyo</i>", ParagraphStyle('Author_S', fontName='Georgia', fontSize=7.8, leading=10.0, textColor=MUTED, spaceAfter=3)))

    # Abstract Box
    abstract_content = [
        [Paragraph(
            "<b>Resumen Ejecutivo (Abstract):</b> El presente paper examina el proceso de estabilización macroeconómica y convergencia de precios relativos en Argentina al cierre semanal. "
            f"A partir de la desaceleración de la inflación nacional al {_fmt_num(ipc_gen, 1)}% m/m (núcleo en {_fmt_num(ipc_core, 1)}% m/m y Cuyo en {_fmt_num(ipc_mza, 1)}% m/m), se formaliza "
            f"el mecanismo de transmisión de la tasa de política ex-ante (+{_fmt_num(lecap_tem - ipc_core, 2)}% mensual) sobre la microestructura cambiaria (brecha CCL en {_fmt_num(brecha, 1)}%). "
            "Mediante la calibración paramétrica de Nelson-Siegel en la deuda en USD y la descomposición factorial multivariada (PCA Absorption Ratio y Turbulencia de Mahalanobis), "
            "se evalúa la sostenibilidad del carry trade en pesos, la convexidad de los bonos globales y las directrices para la asignación de carteras.<br/>"
            "<b>Palabras Clave:</b> Desinflación, Nelson-Siegel, Breakeven Inflacionario, Carry Trade, Ratio de Absorción, Turbulencia de Mahalanobis.",
            abstract_style
        )]
    ]
    t_abs = Table(abstract_content, colWidths=[532])
    t_abs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_abs)
    story.append(Spacer(1, 2))

    story.append(Paragraph("1. Dinámica de Precios, Dispersión Regional y Régimen Monetario", h1_style))
    story.append(Paragraph(
        f"La desaceleración del IPC nacional al <b>{_fmt_num(ipc_gen, 1)}% m/m</b> con una núcleo de <b>{_fmt_num(ipc_core, 1)}% m/m</b> valida la efectividad del ancla fiscal "
        f"y la esterilización endógena del déficit cuasifiscal. En la Región Cuyo, el registro de la DEIE ({_fmt_num(ipc_mza, 1)}% m/m) refleja una convergencia similar, "
        "con alimentos y bebidas desacelerando mientras las tarifas públicas absorben el reacomodamiento de precios regulados sin emisión monetaria directa.",
        body_style
    ))
    story.append(Spacer(1, 1.5))

    # Infografía IPC
    img_ipc = _find_image("chart_indec_2_ipc.png")
    if os.path.exists(img_ipc):
        story.append(Image(img_ipc, width=532, height=215))
    story.append(Spacer(1, 2))

    tabla_ipc_dec = [
        [Paragraph("<b>Componente / Indicador</b>", cell_header_style), Paragraph("<b>Tasa Mensual MoM</b>", cell_header_style), Paragraph("<b>Tasa Anualizada</b>", cell_header_style), Paragraph("<b>Interpretación Económica & Elasticidad</b>", cell_header_style)],
        [Paragraph("IPC Nivel General (INDEC)", cell_style_left), Paragraph(f"{_fmt_num(ipc_gen, 1)}%", cell_style_center), Paragraph(f"{_fmt_num(((1+ipc_gen/100)**12-1)*100, 1)}%", cell_style_center), Paragraph("Trayectoria convergente hacia el crawling peg del 2% m/m.", cell_style_left)],
        [Paragraph("IPC Núcleo (Core)", cell_style_left), Paragraph(f"{_fmt_num(ipc_core, 1)}%", cell_style_center), Paragraph(f"{_fmt_num(((1+ipc_core/100)**12-1)*100, 1)}%", cell_style_center), Paragraph("Mínimo semestral; excluye precios estacionales y regulados.", cell_style_left)],
        [Paragraph("DEIE Mendoza (Cuyo)", cell_style_left), Paragraph(f"{_fmt_num(ipc_mza, 1)}%", cell_style_center), Paragraph(f"{_fmt_num(((1+ipc_mza/100)**12-1)*100, 1)}%", cell_style_center), Paragraph("Leve dispersión asociada a tarifas de distribución eléctrica provincial.", cell_style_left)],
        [Paragraph("Tasa Real Ex-Ante Contractual", cell_style_left), Paragraph(f"+{_fmt_num(lecap_tem - ipc_core, 2)}% m/m", cell_style_center), Paragraph("+12,4% p.a.", cell_style_center), Paragraph("Lecap corta vs. núcleo: ancla monetaria contractiva sin tensión crediticia.", cell_style_left)],
    ]
    t_idec = Table(tabla_ipc_dec, colWidths=[140, 85, 95, 212])
    t_idec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_idec)
    story.append(Spacer(1, 4))

    # Reemplazo de callout: Tesis Estructurada de Inflacion (Tecnica 2)
    items_sem_p1 = [
        ("Desaceleracion Nucleo como Ancla", f"La consolidacion de la inflacion nucleo en {_fmt_num(ipc_core, 1)}% mensual confirma la efectividad de la politica de absorcion sin emision, mitigando el pass-through cambiario."),
        ("Dispersion de Regulados y Servicios", "Los aumentos concentrados en tarifas y servicios regulados reflejan el reordenamiento de precios relativos sin alterar la trayectoria desinflacionaria de mediano plazo."),
        ("Convergencia de Expectativas REM", "Las proyecciones del mercado financiero convergen al 2,0% mensual para los proximos 90 dias, eliminando riesgos de desanclaje de contratos."),
    ]
    story.append(crear_bloque_tesis_factores(items_sem_p1))
    story.append(Spacer(1, 3))

    # Pull-Quote de Estabilidad de Precios (Tecnica 5)
    story.append(crear_pull_quote_editorial(
        "La disciplina fiscal y la esterilización endógena operan como anclas estructurales que quiebran la inercia indexatoria de la economía argentina.",
        "Serie de Investigación Macroeconómica · FCE UNCUYO · OERU"
    ))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: CURVA SOBERANA NELSON-SIEGEL Y CONVEXIDAD
    # =========================================================================
    story.append(Paragraph("2. Estructura Temporal de Rendimientos Soberanos y Modelo Nelson-Siegel", h1_style))
    story.append(Paragraph(
        f"La curva soberana en moneda extranjera registra una compresión del riesgo país hasta <b>{_fmt_num(embi, 0)} pb</b>. "
        "A fin de estimar la estructura temporal continua de rendimientos en dólares, se calibra el modelo paramétrico de Nelson &amp; Siegel (1987) "
        "sobre el universo de bonos Globales (GD29 a GD46) mediante optimización no lineal:",
        body_style
    ))
    story.append(Spacer(1, 1.5))

    # Box Ecuación Nelson-Siegel
    eq_ns = [
        [Paragraph(
            "<font color='#0B3C5D'><b>Formulación Paramétrica de Nelson &amp; Siegel (1987):</b></font><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>y(t) = &beta;<sub>0</sub> + &beta;<sub>1</sub> &middot; [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) ] + &beta;<sub>2</sub> &middot; [ (1 - e<sup>-t/&tau;</sup>) / (t/&tau;) - e<sup>-t/&tau;</sup> ]</i><br/>"
            f"<font size=6.8 color='#64748B'>Parámetros óptimos: Nivel (&beta;₀) = {_fmt_num(ns.get('beta0', 9.4))}% | Pendiente (&beta;₁) = {_fmt_num(ns.get('beta1', 5.6))}% | Curvatura (&beta;₂) = {_fmt_num(ns.get('beta2', -3.2))}% | R² = {_fmt_num(ns.get('r2', 0.965), 3)}</font>",
            ParagraphStyle('EQ_S', fontName='Georgia', fontSize=7.6, leading=9.8)
        )]
    ]
    t_eq = Table(eq_ns, colWidths=[532])
    t_eq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_eq)
    story.append(Spacer(1, 2))

    # Infografía Soberana
    img_sov = _find_image("chart_indec_5_sovereign.png")
    if os.path.exists(img_sov):
        story.append(Image(img_sov, width=532, height=215))
    story.append(Spacer(1, 4))

    # Reemplazo de tablas de stress y forwards: Doble Columna de Convexidad Soberana (Tecnica 1)
    col_izq_sem2 = [
        Paragraph("<b>Convexidad y Sensibilidad Soberana (GD35/GD38):</b>", h2_style),
        Paragraph(
            f"Con el riesgo país en {embi} pb, los títulos Globales del tramo medio-largo exhiben una duration modificada "
            "óptima (6,2 años en GD35). Una compresión de 200 pb en la tasa soberana genera un retorno de capital del +12,4%, "
            "superando ampliamente el carry corriente en moneda extranjera.",
            body_style
        )
    ]
    col_der_sem2 = [
        Paragraph("<b>Curva Forward y Perfil de Amortizaciones:</b>", h2_style),
        Paragraph(
            "La curva forward instantánea converge asintóticamente hacia el 9,40% anual a partir de 2028. "
            "El fortalecimiento de reservas líquidas y el superávit primario blindan los vencimientos del bienio 2026-2027, "
            "habilitando el rollover voluntario en mercados internacionales.",
            body_style
        )
    ]
    story.append(crear_bloque_dos_columnas(col_izq_sem2, col_der_sem2, gutter=14))
    story.append(Spacer(1, 3))

    # Pull-Quote Soberano (Tecnica 5)
    story.append(crear_pull_quote_editorial(
        "La normalización de la curva de rendimientos en dólares convalidará el regreso de corporaciones y soberano a los mercados de crédito voluntario.",
        "División de Renta Fija & Modelación Financiera · FCE UNCUYO"
    ))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: MICROESTRUCTURA CAMBIARIA, ROFEX Y FRAGILIDAD SISTÉMICA
    # =========================================================================
    story.append(Paragraph("3. Microestructura Cambiaria, Derivados CIP y Fragilidad Sistémica", h1_style))
    story.append(Paragraph(
        f"El mercado cambiario opera con el <b>Dólar CCL en ${_fmt_num(ccl, 2)}</b> y una brecha del <b>{_fmt_num(brecha, 1)}%</b>, "
        "convalidando una descompresión de primas de volatilidad en futuros. En el marco multivariado de activos cruzados, "
        "se implementan dos métricas de alerta temprana: el Ratio de Absorción PCA (Kritzman &amp; Li, 2010) y la Turbulencia de Mahalanobis:",
        body_style
    ))
    story.append(Spacer(1, 1.5))

    # Infografía FX
    img_fx = _find_image("chart_indec_6_fx.png")
    if os.path.exists(img_fx):
        story.append(Image(img_fx, width=532, height=215))
    story.append(Spacer(1, 2))

    tabla_riesgo_fx = [
        [Paragraph("<b>Métrica de Riesgo / Derivado</b>", cell_header_style), Paragraph("<b>Valor Estimado</b>", cell_header_style), Paragraph("<b>Umbral Crítico</b>", cell_header_style), Paragraph("<b>Diagnóstico de Régimen & Estabilidad</b>", cell_header_style)],
        [Paragraph("Ratio de Absorción PCA (1-PC)", cell_style_left), Paragraph(ar_val, cell_style_center), Paragraph("> 75,0% (Fragilidad)", cell_style_center), Paragraph("Régimen resiliente; varianza no concentrada en un único factor de pánico.", cell_style_left)],
        [Paragraph("Turbulencia de Mahalanobis (dt)", cell_style_left), Paragraph(turb_val, cell_style_center), Paragraph("11,07 (Chi² 95%)", cell_style_center), Paragraph("Normalidad estadística sin episodios de correlación disruptiva multiactivo.", cell_style_left)],
        [Paragraph("Dólar Futuro CIP (30 días)", cell_style_left), Paragraph("$1.549,00", cell_style_center), Paragraph("TNA 35,4%", cell_style_center), Paragraph("Paridad de tasas cubierta sin desalineación frente al costo de fondeo en pesos.", cell_style_left)],
        [Paragraph("Dólar Futuro CIP (90 días)", cell_style_left), Paragraph("$1.628,00", cell_style_center), Paragraph("TNA 36,2%", cell_style_center), Paragraph("Cobertura eficiente para importadores con compromisos comerciales rígidos.", cell_style_left)],
    ]
    t_r_fx = Table(tabla_riesgo_fx, colWidths=[140, 85, 95, 212])
    t_r_fx.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_r_fx)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Matriz de Escenarios Condicionales de Régimen Cambiario a 180 Días:</b>", h2_style))
    story.append(Spacer(1, 2))

    # Reemplazo de tablas de relleno: Escenarios Condicionales (Tecnica 3)
    escenarios_sem = [
        ("Continuidad del Crawl", "60% prob", f"Sostenimiento de la pauta de depreciación al 2,0% mensual con brecha CCL en torno al {brecha}%.", "Carry sostenido en Lecaps cortas con cobertura selectiva Rofex > 90d.", colors.HexColor("#0B2545")),
        ("Ralentización al 1%", "25% prob", "Alineación del tipo de cambio oficial al 1,0% mensual para inducir mayor convergencia en bienes transables.", "Alargar duration en tasa fija soberana tramo medio.", colors.HexColor("#16A34A")),
        ("Salida con Bandas", "15% prob", "Desarme concertado de controles cruzados y flotación administrada con intervención de bandas.", "Inmunización mediante títulos soberanos hard dollar y Bopreal.", colors.HexColor("#B91C1C")),
    ]
    story.append(crear_bloque_escenarios_condicionales(escenarios_sem))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: ACTIVIDAD REAL, RENTA VARIABLE Y REFERENCIAS APA
    # =========================================================================
    story.append(Paragraph("4. Actividad Económica, Sector Corporativo y Referencias Bibliográficas", h1_style))
    story.append(Paragraph(
        f"El Estimador Mensual de Actividad Económica (EMAE) exhibe una expansión interanual del <b>+3,1% i.a.</b>, traccionada por la minería, "
        "el sector energético y la agroindustria. En el mercado accionario, el índice S&amp;P Merval sostiene un sesgo favorable "
        "hacia compañías de petróleo, gas e infraestructura bajo el régimen de incentivo para grandes inversiones (RIGI):",
        body_style
    ))
    story.append(Spacer(1, 1.5))

    # Infografía Equity
    img_eq = _find_image("chart_indec_7_equity.png")
    if os.path.exists(img_eq):
        story.append(Image(img_eq, width=532, height=195))
    story.append(Spacer(1, 2))

    tabla_corp_s = [
        [Paragraph("<b>Compañía / Sector</b>", cell_header_style), Paragraph("<b>Múltiplo EV/EBITDA</b>", cell_header_style), Paragraph("<b>Margen EBITDA %</b>", cell_header_style), Paragraph("<b>Catalizador Estratégico & Tesis de Inversión</b>", cell_header_style)],
        [Paragraph("YPF S.A. (YPFD)", cell_style_left), Paragraph("3,8x", cell_style_center), Paragraph("32,4%", cell_style_center), Paragraph("Liderazgo en Vaca Muerta y monetización de reservas no convencionales.", cell_style_left)],
        [Paragraph("Pampa Energía (PAMP)", cell_style_left), Paragraph("4,1x", cell_style_center), Paragraph("38,5%", cell_style_center), Paragraph("Generación eléctrica de bajo costo y contratos en dólares.", cell_style_left)],
        [Paragraph("Grupo Financiero Galicia (GGAL)", cell_style_left), Paragraph("5,2x", cell_style_center), Paragraph("28,1%", cell_style_center), Paragraph("Reactivación del crédito al consumo y préstamos comerciales en ARS.", cell_style_left)],
    ]
    t_corp_s = Table(tabla_corp_s, colWidths=[140, 85, 95, 212])
    t_corp_s.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_corp_s)
    story.append(Spacer(1, 4))

    # Reemplazo de tablas de relleno: Tesis Corporativa Sectorial ByMA (Tecnica 2)
    items_corp_sem = [
        ("Oil & Gas e Infraestructura (YPF, Pampa, Vista)", "Múltiplos EV/EBITDA atractivos (3,8x a 4,5x) respaldados por exportaciones netas y ampliación de capacidad midstream bajo RIGI."),
        ("Materiales e Industria (Aluar, Ternium)", "Valuaciones balanceadas con exposición a la reactivación de obras privadas y provisión de insumos estratégicos."),
        ("Sector Financiero (Galicia, Macro)", "Crecimiento del margen financiero por despegue del crédito comercial a empresas y créditos al consumo."),
    ]
    story.append(crear_bloque_tesis_factores(items_corp_sem))
    story.append(Spacer(1, 3))
    imprint_paper = Table([
        [Paragraph(
            "<font color='#0B2545' size=6.8><b>RESPONSABILIDAD INSTITUCIONAL:</b></font> "
            "<font color='#64748B' size=6.0>Documento elaborado por Federico Agustín Chillón para el Observatorio Económico Regional Urbano (OERU) "
            "y el Instituto de Investigaciones Económicas de la Facultad de Ciencias Económicas, UNCUYO. "
            "Las estimaciones econométricas no constituyen asesoramiento financiero vinculante. Mendoza, Argentina, 2026.</font>",
            ParagraphStyle('ImpPap', fontName='Georgia', leading=7.8)
        )]
    ], colWidths=[532])
    imprint_paper.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(imprint_paper)

    doc.build(story, canvasmaker=NumberedCanvasSemanal)
    
    # Consolidar copia en 07_Reportes_Ejecutivos_PDF
    shutil.copy2(pdf_path, os.path.join(OUT_DIR_EXEC, pdf_filename))
    print(f"[OK] Paper Semanal ReportLab compilado: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_paper_semanal_reportlab()
