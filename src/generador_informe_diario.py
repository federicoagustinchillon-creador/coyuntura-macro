"""
GENERADOR DEL MONITOR DIARIO DE MERCADOS Y COYUNTURA FINANCIERA (2 PÁGINAS TRADING DESK)
========================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — UNCUYO / OERU
Genera el monitor diario en 2 páginas institucionales con tipografía Georgia 9.2 pt,
paleta Oxford Navy / Deep Wine, análisis cuantitativo de cierre de mercados, flujos MULC,
arbitrajes de tasas y trade ideas ejecutables.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import win32com.client
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLOR_NAVY = RGBColor(12, 35, 64)       # Oxford Navy #0C2340
COLOR_WINE = RGBColor(114, 47, 55)      # Deep Wine #722F37
COLOR_CHARCOAL = RGBColor(15, 23, 42)   # Slate Charcoal #0F172A
COLOR_MUTED = RGBColor(100, 116, 139)   # Slate Gray #64748B
COLOR_FOREST = RGBColor(13, 92, 70)     # Forest Green #0D5C46
COLOR_OCHRE = RGBColor(180, 83, 9)      # Warm Amber #B45309

def set_cell_background(cell, fill_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_cell_margins(cell, top=50, bottom=50, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, top="CBD5E1", bottom="CBD5E1", left=None, right=None, sz="6"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for b_name, b_color in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if b_color:
            b_el = OxmlElement(f'w:{b_name}')
            b_el.set(qn('w:val'), 'single')
            b_el.set(qn('w:sz'), str(sz))
            b_el.set(qn('w:space'), '0')
            b_el.set(qn('w:color'), b_color)
            tcBorders.append(b_el)
        else:
            b_el = OxmlElement(f'w:{b_name}')
            b_el.set(qn('w:val'), 'none')
            tcBorders.append(b_el)
    tcPr.append(tcBorders)

def add_header_footer_diario(doc, fecha_str="21 de Agosto de 2026"):
    for i, section in enumerate(doc.sections):
        header = section.header
        p_hdr = header.paragraphs[0]
        p_hdr.text = f"MONITOR DIARIO DE MERCADOS & COYUNTURA · {fecha_str.upper()}\t\tFEDERICO AGUSTÍN CHILLÓN"
        p_hdr.runs[0].font.name = "Georgia"
        p_hdr.runs[0].font.size = Pt(7.8)
        p_hdr.runs[0].font.color.rgb = COLOR_MUTED
        
        footer = section.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.text = "Federico Agustín Chillón · Investigador · Cs. Económicas UNCUYO · FCE UNCUYO\t\tMonitor Flash Diario"
        p_ftr.runs[0].font.name = "Georgia"
        p_ftr.runs[0].font.size = Pt(7.8)
        p_ftr.runs[0].font.color.rgb = COLOR_MUTED

def add_body(doc, text, space_after=3.5, font_size=8.8):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    r.font.name = "Georgia"
    r.font.size = Pt(font_size)
    r.font.color.rgb = COLOR_CHARCOAL
    return p

def crear_cuadro_estrategia_desk(doc, titulo, tesis_str, detalles_str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(7.20)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=18, bottom=18, left=24, right=24)
    set_cell_borders(cell, top="0C2340", bottom="0C2340", left="0C2340", right="0C2340", sz="8")
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(2)
    r_tit = p.add_run(titulo.upper() + "\n")
    r_tit.font.name = "Georgia"; r_tit.font.size = Pt(8.2); r_tit.font.bold = True; r_tit.font.color.rgb = COLOR_NAVY
    
    r_f = p.add_run(tesis_str + "\n")
    r_f.font.name = "Georgia"; r_f.font.size = Pt(8.0); r_f.font.bold = True; r_f.font.color.rgb = COLOR_WINE
    
    r_exp = p.add_run(detalles_str)
    r_exp.font.name = "Georgia"; r_exp.font.size = Pt(7.8); r_exp.font.color.rgb = COLOR_CHARCOAL

def formatear_tabla_diaria(tabla, col_widths, headers, data_rows, font_size=7.4, alignments=None):
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tabla.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "0C2340")
        set_cell_margins(hdr_cells[i], top=16, bottom=16, left=18, right=18)
        set_cell_borders(hdr_cells[i], top="0C2340", bottom="0C2340", left=None, right=None)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        for run in p.runs:
            run.font.name = "Georgia"; run.font.size = Pt(font_size); run.font.bold = True; run.font.color.rgb = RGBColor(255, 255, 255)
            
    for r_idx, row_data in enumerate(data_rows):
        row_cells = tabla.add_row().cells
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=12, bottom=12, left=18, right=18)
            set_cell_borders(row_cells[c_idx], top="E2E8F0", bottom="E2E8F0", left=None, right=None)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
            
            if alignments and c_idx < len(alignments):
                p.alignment = alignments[c_idx]
            else:
                if c_idx == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                elif ('%' in str(val) or '$' in str(val) or any(c.isdigit() for c in str(val))) and not ('Sobreponderar' in str(val) or 'Neutral' in str(val) or 'Subponderar' in str(val) or 'Lecap' in str(val) or 'Boncer' in str(val) or 'Oficial' in str(val) or 'MEP' in str(val) or 'CCL' in str(val) or 'Rofex' in str(val) or 'AL30' in str(val) or 'GD30' in str(val) or 'Tramos' in str(val) or 'Adjudicación' in str(val) or 'Letras' in str(val)):
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
            for run in p.runs:
                run.font.name = "Georgia"; run.font.size = Pt(font_size)
                if 'Sobreponderar' in str(val):
                    run.font.bold = True; run.font.color.rgb = COLOR_FOREST
                elif 'Neutral' in str(val) or 'Mantener' in str(val):
                    run.font.bold = True; run.font.color.rgb = COLOR_OCHRE
                elif 'Subponderar' in str(val) or 'Reducir' in str(val):
                    run.font.bold = True; run.font.color.rgb = COLOR_WINE
                elif '+' in str(val) and '%' in str(val):
                    run.font.bold = True; run.font.color.rgb = COLOR_FOREST
                elif '-' in str(val) and '%' in str(val) and not ('USD' in str(val) or '2026' in str(val) or '$' in str(val)):
                    run.font.bold = True; run.font.color.rgb = COLOR_WINE
                else:
                    run.font.color.rgb = COLOR_CHARCOAL
                    
    for row in tabla.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = Inches(w)

def compilar_informe_diario(ruta_salida_docx: str, fecha_str="21 de Agosto de 2026"):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.50)
        section.bottom_margin = Inches(0.50)
        section.left_margin = Inches(0.65)
        section.right_margin = Inches(0.65)
        section.header_distance = Inches(0.30)
        section.footer_distance = Inches(0.30)
        section.different_first_page_header_footer = True
        
    add_header_footer_diario(doc, fecha_str)
    
    # -------------------------------------------------------------------------
    # PÁGINA 1: TABLERO DE CIERRE, FLUJOS MULC & MICROESTRUCTURA CAMBIARIA
    # -------------------------------------------------------------------------
    p_title = doc.add_paragraph()
    r_t = p_title.add_run("Monitor Diario de Mercados & Coyuntura Financiera")
    r_t.font.name = "Georgia"; r_t.font.size = Pt(13.5); r_t.font.bold = True; r_t.font.color.rgb = COLOR_NAVY
    p_title.paragraph_format.space_before = Pt(0); p_title.paragraph_format.space_after = Pt(1.5)
    
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(f"Cierre de Operaciones: {fecha_str} | Estrategia Cuantitativa & Trading Desk | FCE UNCUYO")
    r_sub.font.name = "Georgia"; r_sub.font.size = Pt(8.0); r_sub.font.italic = True; r_sub.font.color.rgb = COLOR_MUTED
    p_sub.paragraph_format.space_after = Pt(3.5)
    
    # Tablero de 4 Indicadores Clave
    t_kpi = doc.add_table(rows=1, cols=4)
    t_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    kpis = [
        ("DÓLAR CCL (CABLE)", "$1.596,59", "+0,42% 1D · Brecha 5,39%"),
        ("RIESGO PAÍS EMBI+", "506 pb", "-4 pb 1D · Compresión"),
        ("CAUCIÓN 1D (BYMA)", "32,50% TNA", "2,71% TEM · Liquidez"),
        ("S&P MERVAL (USD)", "3.156.332 pts", "+1,30% 1D · USD 1.976")
    ]
    for i, (k_t, k_v, k_s) in enumerate(kpis):
        cell = t_kpi.rows[0].cells[i]
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=12, bottom=12, left=16, right=16)
        set_cell_borders(cell, top="0C2340", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz="6")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        
        rt = p.add_run(k_t.upper() + "\n")
        rt.font.name = "Georgia"; rt.font.size = Pt(6.8); rt.font.bold = True; rt.font.color.rgb = COLOR_NAVY
        
        rv = p.add_run(k_v + "\n")
        rv.font.name = "Georgia"; rv.font.size = Pt(9.8); rv.font.bold = True; rv.font.color.rgb = COLOR_CHARCOAL
        
        rs = p.add_run(k_s)
        rs.font.name = "Georgia"; rs.font.size = Pt(6.6); rs.font.color.rgb = COLOR_MUTED
        
    for c in t_kpi.rows[0].cells: c.width = Inches(1.80)
    
    # 1. Microestructura Cambiaria
    h1 = doc.add_heading("1. Microestructura Cambiaria, Flujos en el MULC y Futuros Matba-Rofex", level=2)
    h1.paragraph_format.space_before = Pt(5); h1.paragraph_format.space_after = Pt(2)
    for r in h1.runs: r.font.name = "Georgia"; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = COLOR_NAVY
    
    add_body(doc, "La rueda cambiaria operó con fluidez en el Mercado Único y Libre de Cambios (MULC), registrando un volumen negociado de USD 380M en el segmento spot. El tipo de cambio mayorista de referencia (Com. 'A' 3500) cerró en $1.485,00 (+0,07% diario), convalidando la trayectoria del crawling peg administrado al 2% mensual. El Banco Central concluyó la sesión con compras netas por USD 85M, acumulando un saldo favorable de USD 950M en lo que va del mes.", space_after=2.5, font_size=8.2)
    add_body(doc, "En el segmento financiero, las cotizaciones bursátiles operaron con estabilidad: el Dólar MEP cerró en $1.532,33 (-0,15%), mientras que el Dólar Contado con Liquidación (CCL) finalizó en $1.596,59 (+0,42%), comprimiendo la brecha cambiaria al 5,39% frente a la cotización minorista del Banco Nación ($1.515,00) y al 7,51% sobre el mayorista.", space_after=2.5, font_size=8.2)
    add_body(doc, "En el mercado de futuros de Matba-Rofex, el interés abierto totalizó 1,25M contratos con una concentración del 72% en los vencimientos de agosto y septiembre. Las tasas nominales anuales implícitas oscilaron entre 35,20% (Sep-26) y 37,10% (Nov-26), reflejando una base de Paridad Cubierta (CIP Basis) neutral que descarta primas por salto cambiario discreto.", space_after=3.0, font_size=8.2)
    
    t_fx = doc.add_table(rows=1, cols=5)
    formatear_tabla_diaria(
        t_fx,
        col_widths=[1.90, 1.20, 1.10, 1.30, 1.70],
        headers=["Segmento / Activo", "Cierre Spot ($)", "Var. Diaria (%)", "Brecha Oficial (%)", "Volumen / TNA Impl."],
        data_rows=[
            ["Dólar Mayorista (A 3500)", "$1.485,00", "+0,07%", "0,00% (Base)", "USD 380M operado"],
            ["Dólar Oficial Minorista (BNA)", "$1.515,00", "0,00%", "+2,02%", "Referencia minorista"],
            ["Dólar MEP (Bolsa AL30)", "$1.532,33", "-0,15%", "+3,19%", "USD 120M operado"],
            ["Dólar CCL (Cable GD30)", "$1.596,59", "+0,42%", "+7,51%", "USD 95M operado"],
            ["Rofex Posición Sep-26", "$1.530,00", "-0,10%", "+3,03%", "35,20% TNA (620k contratos)"],
            ["Rofex Posición Nov-26", "$1.635,00", "-0,05%", "+10,10%", "37,10% TNA (410k contratos)"]
        ],
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
        font_size=7.0
    )
    
    fig_fx = os.path.join(BASE_DIR, "03_Figuras_HD", "master_extracted_images", "img_p11_1_13.png")
    if os.path.exists(fig_fx):
        p_pic = doc.add_paragraph()
        p_pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_pic.paragraph_format.space_before = Pt(3); p_pic.paragraph_format.space_after = Pt(0)
        p_pic.add_run().add_picture(fig_fx, width=Inches(7.20))
        
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # PÁGINA 2: RENTA FIJA SOBERANA, DESK CALLS & RESUMEN MONETARIO
    # -------------------------------------------------------------------------
    h2 = doc.add_heading("2. Renta Fija en ARS (LECAPS/BONCER) y Curva Soberana en Hard Dollar", level=2)
    h2.paragraph_format.space_before = Pt(0); h2.paragraph_format.space_after = Pt(2)
    for r in h2.runs: r.font.name = "Georgia"; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = COLOR_NAVY
    
    add_body(doc, "En el mercado en moneda local, las Letras del Tesoro (LECAPs) operaron con alto volumen y tasas efectivas mensuales (TEM) de 2,95% en la letra S31O6 (Oct-26) y 3,05% en la S28N6 (Nov-26), ofreciendo una prima real de +93 pb mensuales sobre las expectativas del REM. Los títulos ajustables por CER (BONCER) operaron estables con rendimientos reales de CER + 1,10% (TZX27) y CER + 2,30% (TZX28), convalidando un breakeven inflacionario implícito de 2,65% mensual.", space_after=2.5, font_size=8.2)
    add_body(doc, "En deuda hard dollar, los bonos soberanos extendieron su tendencia compradora: el riesgo país (EMBI+) retrocedió 4 pb hasta los 506 puntos básicos. Los títulos Globales bajo ley extranjera cotizaron al alza, con el GD30 cerrando en USD 69,80 (10,70% TIR) y el GD38 en USD 60,90 (9,70% TIR). El spread de legislación frente a los Bonares locales (AL30 en 11,20% TIR) se ubicó en 50 pb, abriendo ventanas de arbitraje táctico.", space_after=2.5, font_size=8.2)
    add_body(doc, "En el segmento monetario, la tasa de caución bursátil a 1 día en ByMA se ubicó en 32,50% TNA (2,71% TEM), permitiendo a las tesorerías estructurar operaciones de apalancamiento sintético sobre la curva de letras cortas capturando un carry neto superior a 24 pb mensuales libre de riesgo cambiario.", space_after=2.5, font_size=8.2)
    add_body(doc, "En el crédito corporativo privado, las Obligaciones Negociables (ONs) en hard dollar de emisores energéticos de primera línea (YPF, Pampa Energía, TGS) comprimieron sus rendimientos hacia la zona de 7,20% a 7,80% anual en el tramo 2028-2031, reflejando una sólida demanda de cobertura sin riesgo de crédito soberano.", space_after=2.5, font_size=8.2)
    add_body(doc, "La curva forward soberana proyecta tasas terminales en torno al 8,80% para vencimientos superiores a 10 años, convalidando el atractivo de los títulos con cupones step-up crecientes como el GD38 frente a los tramos cortos.", space_after=3.0, font_size=8.2)
    
    t_bon = doc.add_table(rows=1, cols=6)
    formatear_tabla_diaria(
        t_bon,
        col_widths=[1.40, 1.10, 1.00, 1.40, 1.00, 1.30],
        headers=["Ticker / Especie", "Precio ($ / USD)", "Var. 1D (%)", "TIR / TNA (%)", "Duration", "Tesis Desk"],
        data_rows=[
            ["Lecap S31O6", "$108,40", "+0,12%", "35,40% TNA (2,95% TEM)", "0,18 a.", "Sobreponderar"],
            ["Lecap S28N6", "$111,20", "+0,10%", "36,60% TNA (3,05% TEM)", "0,26 a.", "Sobreponderar"],
            ["Boncer TZX27", "$124,50", "+0,05%", "CER + 1,10% TIR Real", "1,35 a.", "Neutral"],
            ["Bonar 2030 (AL30)", "USD 67,50", "+0,45%", "11,20% TIR", "2,78 a.", "Sobreponderar"],
            ["Global 2030 (GD30)", "USD 69,80", "+0,50%", "10,70% TIR", "2,78 a.", "Sobreponderar"],
            ["Global 2038 (GD38)", "USD 60,90", "+0,65%", "9,70% TIR", "5,81 a.", "Sobreponderar"]
        ],
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
        font_size=7.0
    )
    
    # Cuadro de Estrategia Táctica Cuantitativa Desk Call
    crear_cuadro_estrategia_desk(
        doc,
        "Trade Call Cuantitativo de Mesa & Arbitraje de Spreads",
        "Estrategia 1: Carry en Lecap S31O6 (TNA 35,4% / TEM 2,95%) con Stop-Loss de Brecha al 8,5% | Estrategia 2: Arbitraje GD30 vs AL30",
        "• Carry Neto en ARS: La TEM de 2,95% frente al crawl del 2,00% genera un retorno esperado en USD de +0,93% mensual (+11,76% anualizado). Se recomienda fondear con caución a 1D (32,50% TNA) capturando un spread positivo de +290 bps.\n"
        "• Arbitraje de Legislación: El diferencial de 50 pb entre AL30 (11,20%) y GD30 (10,70%) presenta oportunidad de rotación táctica hacia AL30 con objetivo de compresión hacia 30 pb.\n"
        "• Convexidad Hard Dollar: Sobreponderar GD38 por su ratio de convexidad (37,2x) frente a caídas adicionales de tasa libre de riesgo global (UST10Y)."
    )
    
    # Monitor de Acciones Líderes y Cedears
    h3_eq = doc.add_heading("3. Monitor de Renta Variable Energética y Múltiplos Corporativos", level=2)
    h3_eq.paragraph_format.space_before = Pt(3); h3_eq.paragraph_format.space_after = Pt(2)
    for r in h3_eq.runs: r.font.name = "Georgia"; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = COLOR_NAVY
    
    t_eq_d = doc.add_table(rows=1, cols=5)
    formatear_tabla_diaria(
        t_eq_d,
        col_widths=[1.80, 1.20, 1.20, 1.30, 1.70],
        headers=["Compañía / Ticker", "Precio Cierre ($)", "Var. Diaria (%)", "EV/EBITDA", "Tesis Fundamental"],
        data_rows=[
            ["YPF S.A. (YPFD)", "$42.500", "+2,10%", "3,8x", "Sobreponderar · Vaca Muerta."],
            ["Pampa Energía (PAMP)", "$3.850", "+1,80%", "4,1x", "Sobreponderar · Generación."],
            ["Transportadora Gas Sur (TGSU2)", "$6.920", "+1,45%", "4,4x", "Sobreponderar · Infraestructura."],
            ["Grupo Financiero Galicia (GGAL)", "$6.450", "+0,85%", "1,4x P/BV", "Neutral · Crédito privado."],
            ["Banco Macro (BMA)", "$9.800", "+1,15%", "1,3x P/BV", "Sobreponderar · Solvencia."]
        ],
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
        font_size=7.0
    )
    
    # 4. Licitaciones del Tesoro y Drivers de la Próxima Rueda
    h4 = doc.add_heading("4. Licitaciones del Tesoro, Absorción Monetaria y Drivers de la Próxima Rueda", level=2)
    h4.paragraph_format.space_before = Pt(3); h4.paragraph_format.space_after = Pt(2)
    for r in h4.runs: r.font.name = "Georgia"; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = COLOR_NAVY
    
    t_lic = doc.add_table(rows=1, cols=4)
    formatear_tabla_diaria(
        t_lic,
        col_widths=[2.10, 1.50, 1.50, 2.10],
        headers=["Instrumento / Operación", "Monto Adjudicado / Stock", "Tasa de Corte / TNA", "Destino / Efecto Monetario"],
        data_rows=[
            ["Lecap S31O6 (Reapertura)", "$1,12 Billones", "35,40% TNA (2,95% TEM)", "Rollover y fijación de tasa."],
            ["Lecap S28N6 (Tramo Largo)", "$0,68 Billones", "36,60% TNA (3,05% TEM)", "Extensión de duration en pesos."],
            ["Letras Fiscales Lefi (BCRA)", "$29,30 Billones (Stock)", "35,00% TNA (2,91% TEM)", "Absorción sin emisión cuasifiscal ($0 B pases)."],
            ["Base Monetaria Ampliada", "$27,40 Billones (Stock)", "-", "Crecimiento acotado por demanda real."]
        ],
        alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
        font_size=7.0
    )
    
    add_body(doc, "• Drivers para la Rueda Siguiente: (1) Licitación quincenal de títulos en pesos de la Secretaría de Finanzas; (2) Publicación de balances corporativos del sector energético (YPF, PAMP); (3) Evolución del saldo comprador en el MULC; (4) Vencimiento de futuros Rofex y volumen en el tramo corto.", font_size=8.0, space_after=0)

    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida_docx)), exist_ok=True)
    doc.save(ruta_salida_docx)
    print("Monitor Diario DOCX generado:", ruta_salida_docx)
    return ruta_salida_docx

def compilar_y_exportar_informe_diario(ruta_docx: str, ruta_pdf: str, fecha_str="21 de Agosto de 2026"):
    compilar_informe_diario(ruta_docx, fecha_str)
    import pythoncom
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc_w = word.Documents.Open(os.path.abspath(ruta_docx), ReadOnly=True)
        doc_w.SaveAs(os.path.abspath(ruta_pdf), FileFormat=17)
        doc_w.Close(SaveChanges=False)
        print(f"Monitor Diario PDF exportado exitosamente: {ruta_pdf}")
    finally:
        word.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    d_docx = os.path.join(BASE_DIR, "04_Informes_Diarios", "2026-08-21_Monitor_Diario_Mercados.docx")
    d_pdf = d_docx.replace(".docx", ".pdf")
    compilar_y_exportar_informe_diario(d_docx, d_pdf)
