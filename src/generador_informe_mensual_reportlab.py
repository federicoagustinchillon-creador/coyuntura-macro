"""
================================================================================
COMPILADOR MAESTRO DE INFORME MENSUAL REPORTLAB (14 PÁGINAS EDITORIALES)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Estándar: Institucional Institutional Research (Goldman Sachs GIR / Bridgewater Standard)
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

import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from src.fetch_tcr_bilateral import cargar_cache as cargar_cache_tcr  # noqa: E402
from src.contexto_informe import cargar_contexto, fmt_num  # noqa: E402
from src.fetch_datos_reales import obtener_variacion_semanal_acciones, obtener_merval_reciente  # noqa: E402

# Nombres de mes en espanol -- se evita depender de locale del sistema
# operativo (inconsistente entre Windows/Linux) para algo tan simple.
MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

SIN_FUENTE = "s/d (sin conector automatizado en el repo -- carga manual)"


def _fmt1(v, decimales=1, signo=False):
    """Formatea un numero real en es-AR (coma decimal) o 's/d' si no hay
    dato -- nunca fabrica un valor cuando el campo no existe."""
    if v is None:
        return "s/d"
    prefijo = "+" if signo and v >= 0 else ""
    return f"{prefijo}{v:.{decimales}f}".replace(".", ",")


def _acumulado_anio_calendario(meses, valores, anio, valor_mes_vigente):
    """Acumulado compuesto (no simple suma) de variaciones mensuales reales
    del INDEC (src/fetch_series_indec_bcra.obtener_ipc_trayectoria) para el
    anio calendario `anio`, agregando el mes vigente del contrato principal
    (todavia no incorporado a esa trayectoria historica, que llega hasta el
    mes anterior). Devuelve (acumulado_pct, cantidad_de_meses) -- (None, 0)
    si no hay ningun mes real disponible para ese anio."""
    factor = 1.0
    n = 0
    for m, v in zip(meses or [], valores or []):
        if m.startswith(str(anio)) and v is not None:
            factor *= (1 + v / 100)
            n += 1
    if valor_mes_vigente is not None:
        factor *= (1 + valor_mes_vigente / 100)
        n += 1
    if n == 0:
        return None, 0
    return round(100 * (factor - 1), 1), n

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

# Estado compartido minimo para que el header/footer de ZeroWhitespaceCanvas
# (clase a nivel de modulo, sin acceso directo a las variables locales de
# generar_informe_mensual_reportlab) muestre el periodo real de la corrida
# en vez de "AGOSTO 2026" fijo. Se completa al principio de la funcion, antes
# de doc.build().
_INFORME_PERIODO = {"header": "PERÍODO S/D"}


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
            self.drawString(left, header_text_y, f"INFORME DE COYUNTURA MACROECONÓMICA & MERCADO DE CAPITALES · {_INFORME_PERIODO['header']}")
            self.drawRightString(right, header_text_y, "FEDERICO AGUSTÍN CHILLÓN")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, header_line_y, right, header_line_y)

            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(left, footer_line_y, right, footer_line_y)

            self.setFont("Georgia", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(left, footer_text_y, "Federico Agustín Chillón · Investigador · Cs. Económicas UNCUYO · Cs. Económicas UNCUYO")
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
    # ------------------------------------------------------------------
    # Carga unica de datos reales (ver src/contexto_informe.py). Corrige el
    # hallazgo central de la auditoria: el mismo concepto (EMBI+, Nelson-
    # Siegel, tasa de pases, brecha CCL) aparecia con valores DISTINTOS
    # entre secciones de este mismo archivo porque cada bloque escribia su
    # propio numero de memoria en vez de leer de un unico lugar. De aca en
    # adelante todo el documento lee de `ctx`.
    # ------------------------------------------------------------------
    ctx = cargar_contexto(incluir_series_lentas=True)
    dolar = ctx["dolar"]
    tasas_ars = ctx["tasas_ars"]
    inflacion = ctx["inflacion"]
    actividad = ctx["actividad"]
    soberano = ctx["soberano_usd"]
    ns = soberano.get("nelson_siegel", {})
    equity = ctx["equity"]
    tasas_bcra = ctx["tasas_bcra_referencia"]
    tasa_real_exante = ctx["tasa_real_exante_tem_pct"]
    emae_hist = ctx.get("emae_historico")
    ipc_tray = ctx.get("ipc_trayectoria")
    monetario_hist = ctx.get("monetario_historico")
    # Fuentes secundarias reales agregadas por otro agente a contexto_informe.py
    # en paralelo a esta correccion (ver src/fetch_series_secundarias.py y
    # src/modelos_riesgo.py) -- tapan huecos que esta misma auditoria marcaba
    # "sin fuente automatizable": RIPTE nominal, variacion del EMBI+, y el
    # Ratio de Absorcion / Turbulencia de Mahalanobis calculados sobre series
    # reales (en vez de los 64,2%/4,12 fijos que citaba el texto original).
    riesgo_sistemico = ctx.get("riesgo_sistemico")
    ripte = ctx.get("ripte")
    riesgo_pais_var_30d = ctx.get("riesgo_pais_variacion_30d")
    dolar_futuro = ctx.get("dolar_futuro_implicito")  # CIP teorico, NO cotizacion Rofex real

    if riesgo_sistemico:
        _ar_txt = f"{_fmt1(riesgo_sistemico['absorption_ratio_pct'])}%"
        _turb_txt = _fmt1(riesgo_sistemico['turbulencia_dt'], decimales=2)
        _turb_umbral_txt = _fmt1(riesgo_sistemico['umbral_chi2_95'], decimales=2)
        _regimen_txt = riesgo_sistemico['regimen'] or "s/d"
        _riesgo_sist_fuente = riesgo_sistemico['fuente']
    else:
        _ar_txt = _turb_txt = _turb_umbral_txt = "s/d"
        _regimen_txt = "s/d"
        _riesgo_sist_fuente = f"Sin datos suficientes para calcularlo en esta corrida: {SIN_FUENTE}"

    if ripte:
        _ripte_txt = f"{_fmt1(ripte['var_mensual_ultimo'], signo=True)}% MoM nominal"
        if ripte.get("var_interanual_ultimo") is not None:
            _ripte_txt += f" ({_fmt1(ripte['var_interanual_ultimo'], signo=True)}% i.a. nominal)"
        _ripte_txt += " -- RIPTE nacional (Secretaría de Trabajo), nominal, no deflactado por inflación"
    else:
        _ripte_txt = SIN_FUENTE

    if riesgo_pais_var_30d and riesgo_pais_var_30d.get("variacion_pb") is not None:
        _embi_var_30d_txt = f" ({_fmt1(riesgo_pais_var_30d['variacion_pb'], decimales=0, signo=True)} pb en 30 días, fuente secundaria ArgentinaDatos)"
    else:
        _embi_var_30d_txt = ""

    fecha_str = ctx.get("fecha")
    try:
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d") if fecha_str else datetime.now()
    except ValueError:
        fecha_dt = datetime.now()
    mes_nombre = MESES_ES[fecha_dt.month]
    anio_informe = fecha_dt.year
    periodo_header = f"{mes_nombre.upper()} {anio_informe}"
    periodo_texto = f"{mes_nombre.lower()} de {anio_informe}"  # ej. "agosto de 2026", para prosa
    periodo_texto_cap = f"{mes_nombre} de {anio_informe}"      # ej. "Agosto de 2026", para titulos
    _INFORME_PERIODO["header"] = periodo_header

    # Retornos semanales reales de acciones lideres (yfinance .BA) -- usados
    # en la seccion de Renta Variable (Pagina 13) en vez de rangos inventados.
    try:
        variaciones_acciones = obtener_variacion_semanal_acciones()
    except Exception as e:
        print(f"      [Informe Mensual] ERROR trayendo variaciones semanales de acciones: {e}")
        variaciones_acciones = {}

    # NOTA: el nombre de archivo de salida se mantiene fijo (referenciado por
    # 02_Scripts_Automatizacion/verificar_estado_ecosistema.py y
    # pipeline_coyuntura_master.py) -- no se parametriza aca para no romper
    # esos otros scripts; solo el contenido interno del documento (metadatos,
    # encabezados, cuerpo) refleja el periodo real de la corrida.
    pdf_path = os.path.join(OUT_DIR_MENSUAL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36,
        title=f"Informe de Coyuntura Macroeconómica & Mercado de Capitales — {periodo_texto_cap}",
        author="Federico Agustín Chillón",
        subject="Economía Aplicada & Estrategia de Inversión — FCE UNCUYO",
        creator="Federico Agustín Chillón — Investigador · Cs. Económicas UNCUYO",
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
            Paragraph(f"<font color='#64748B'><b>CIERRE DE MES · {periodo_header}</b></font>", ParagraphStyle('PB_R', fontName='Georgia', fontSize=7.5, leading=9.5, alignment=TA_RIGHT))
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
          f"<font size=7.2 color='#64748B'>• IPC Nacional: <b>{_fmt1(inflacion.get('indec_general_mom'))}% m/m</b> | "
          f"DEIE Mendoza: <b>{_fmt1(inflacion.get('deie_mendoza_mom'))}% m/m</b><br/>"
          f"• Inflación núcleo en <b>{_fmt1(inflacion.get('indec_nucleo_mom'))}% m/m</b> con ancla fiscal consolidada.<br/>"
          f"• Tasa real ex-ante (Fisher, Lecap corta vs. REM): <b>{_fmt1(tasa_real_exante, signo=True)}% mensual</b>.</font>")

    p2 = ("<b>2. RENTA FIJA & DEUDA SOBERANA</b><br/>"
          f"<font size=7.2 color='#64748B'>• Curva Nelson-Siegel hard dollar: nivel &beta;<sub>0</sub> = <b>{_fmt1(ns.get('beta0'))}%</b><br/>"
          f"• Riesgo País (EMBI+) en <b>{fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb</b>; GD35 rinde <b>{_fmt1(soberano.get('gd35_tir'))}% TIR</b>.<br/>"
          f"• Lecap tramo corto con TEM de <b>{_fmt1(tasas_ars.get('lecap_corta_tem'))}% m/m</b> (el contrato no especifica un ticker puntual).</font>")

    p3 = ("<b>3. MICROESTRUCTURA CAMBIARIA</b><br/>"
          f"<font size=7.2 color='#64748B'>• Dólar CCL: <b>${fmt_num(dolar.get('ccl'), 2)}</b> | Brecha CCL/oficial: <b>{_fmt1(dolar.get('brecha_ccl_oficial_pct'))}%</b><br/>"
          f"• Dólar futuro CIP a 30d (teórico, no cotización Rofex): <b>${fmt_num(dolar_futuro['curva'][0]['futuro_implicito'], 2) if dolar_futuro else 's/d'}</b><br/>"
          "• Ratio de Absorción / Turbulencia de Mahalanobis: ver Pág. 12 (sección de riesgo sistémico).</font>")

    p4 = ("<b>4. ACTIVIDAD & RIESGO SISTÉMICO</b><br/>"
          f"<font size=7.2 color='#64748B'>• EMAE desestacionalizado: <b>{_fmt1(actividad.get('emae_desestacionalizado_mom_pct'), signo=True)}% m/m</b> "
          f"({_fmt1(actividad.get('emae_interanual_pct'), signo=True)}% i.a.)<br/>"
          f"• ISARC i.a.: Mendoza <b>{_fmt1(actividad.get('isarc_mendoza_ia_pct'), signo=True)}%</b> · San Luis <b>{_fmt1(actividad.get('isarc_san_luis_ia_pct'), signo=True)}%</b><br/>"
          f"• Ratio de Absorción: <b>{_ar_txt}</b> · Turbulencia de Mahalanobis: <b>{_turb_txt}</b> (régimen: {_regimen_txt}).</font>")

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
        f"La economía argentina transita una fase de consolidación de su ancla nominal y desaceleración inflacionaria "
        f"(IPC en {_fmt1(inflacion.get('indec_general_mom'))}% m/m), respaldada por el equilibrio fiscal primario y financiero del Sector Público Nacional. "
        f"En el frente financiero, la curva soberana en USD normaliza su pendiente forward instantánea con un EMBI+ en torno a {fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb, "
        f"mientras que la brecha cambiaria CCL/oficial se ubica en {_fmt1(dolar.get('brecha_ccl_oficial_pct'))}% (Ratio de Absorción: {_ar_txt}, Turbulencia de Mahalanobis: "
        f"{_turb_txt}, régimen {_regimen_txt}). "
        "En este contexto, la estrategia de asignación de activos <b>(juicio del analista, no dato de mercado)</b> pondera un <b>40% en Lecaps cortas (carry trade)</b>, "
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
            Paragraph("<b>AUTOR / INVESTIGADOR</b><br/><font color='#0B3C5D' size=8.2><b>Federico Agustín Chillón</b></font><br/><font color='#64748B' size=6.8>Facultad de Ciencias Económicas</font>", ParagraphStyle('M1', fontName='Georgia', fontSize=7.4, leading=9.8)),
            Paragraph("<b>FILIACIÓN INSTITUCIONAL</b><br/><font color='#0B3C5D' size=8.2><b>Facultad de Ciencias Económicas</b></font><br/><font color='#64748B' size=6.8>Universidad Nacional de Cuyo (UNCUYO)</font>", ParagraphStyle('M2', fontName='Georgia', fontSize=7.4, leading=9.8)),
            Paragraph(f"<b>ESPECIFICACIÓN TÉCNICA</b><br/><font color='#0B3C5D' size=8.2><b>Cierre Mensual · {periodo_texto_cap}</b></font><br/><font color='#64748B' size=6.8>Modelos Econométricos & 300 DPI HD</font>", ParagraphStyle('M3', fontName='Georgia', fontSize=7.4, leading=9.8))
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
        f"Lecap tramo corto (sin ticker puntual en el contrato) en {_fmt1(tasas_ars.get('lecap_corta_tem'))}% TEM otorga un premio de "
        f"+{fmt_num(tasas_ars.get('premio_tasa_fija_pbs'), 0)} pb ex-ante sobre el REM ({_fmt1(tasas_ars.get('inflacion_esperada_rem_tem'))}%). "
        f"Breakeven implícito: {_fmt1(tasas_ars.get('breakeven_inflacion_tem'))}% mensual; la estrategia óptima maximiza exposición en el tramo corto."
    )
    pilar_precios = (
        "<font color='#0B3C5D'><b>2. PRECIOS & CONVERGENCIA</b></font><br/>"
        f"IPC Nacional {_fmt1(inflacion.get('indec_general_mom'))}% MoM (Mendoza DEIE: {_fmt1(inflacion.get('deie_mendoza_mom'))}%), traccionado por regulados "
        f"({_fmt1(inflacion.get('indec_regulados_mom'))}%) y servicios ({_fmt1(inflacion.get('indec_servicios_mom'))}%); núcleo en "
        f"{_fmt1(inflacion.get('indec_nucleo_mom'))}% (sin rubro \"bienes\" propio en el contrato). CBT Mendoza: "
        f"${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)}. RIPTE: {_ripte_txt}."
    )
    pilar_soberano = (
        "<font color='#0B3C5D'><b>3. CURVA SOBERANA EN USD</b></font><br/>"
        f"Nelson-Siegel (R²={_fmt1(ns.get('r2'), decimales=3)}) ubica el nivel asintótico β₀ en {_fmt1(ns.get('beta0'))}%. La compresión del riesgo país hacia "
        f"{fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb favorece extender duration en Globales largos (GD35/GD38); convexidad ante compresión de "
        "spreads: estimación propia, sin motor de pricing en el repositorio (ver Pág. 11)."
    )
    pilar_regional = (
        "<font color='#0B3C5D'><b>4. ACTIVIDAD Y CUYO (ISARC)</b></font><br/>"
        f"EMAE i.a.: {_fmt1(actividad.get('emae_interanual_pct'), signo=True)}% (sin desagregación sectorial en el contrato). ISARC i.a.: San Luis "
        f"{_fmt1(actividad.get('isarc_san_luis_ia_pct'), signo=True)}%, Mendoza {_fmt1(actividad.get('isarc_mendoza_ia_pct'), signo=True)}%, San Juan "
        f"{_fmt1(actividad.get('isarc_san_juan_ia_pct'), signo=True)}% (nivel del índice y desagregación provincial: sin fuente)."
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
        f"Las Letras Fiscales de Liquidez (Lefi) están discontinuadas desde julio de 2025 (stock real $0, BCRA id=196) -- la absorción bancaria opera hoy vía "
        f"la tasa de pases pasivos a 1 día ({_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA), que junto con el superávit fiscal primario mantiene "
        f"ancladas las expectativas cambiarias (volatilidad implícita en Matba-Rofex: {SIN_FUENTE}). La asignación táctica óptima consiste en capturar "
        "rendimientos reales en Lecaps del tramo corto y sobreponderar bonos globales GD35/GD38."
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
            Paragraph(f"<font color='#64748B' size=7.0><b>Repositorio Oficial & Pipelines:</b><br/>github.com/federicoagustinchillon-creador/coyuntura-macro<br/>Mendoza, Argentina · {periodo_texto_cap}</font>", ParagraphStyle('SigR', fontName='Georgia', alignment=TA_RIGHT, leading=9.5))
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
        f"El diagnóstico macroeconómico al cierre de {periodo_texto} confirma la vigencia y efectividad del ancla fiscal y monetaria. La convergencia inflacionaria "
        f"(IPC INDEC: {_fmt1(inflacion.get('indec_general_mom'))}% MoM vs. Mendoza DEIE: {_fmt1(inflacion.get('deie_mendoza_mom'))}% MoM) estuvo liderada por el reacomodamiento de "
        f"<b>precios regulados ({_fmt1(inflacion.get('indec_regulados_mom'))}% MoM)</b> y <b>servicios privados ({_fmt1(inflacion.get('indec_servicios_mom'))}% MoM)</b>, que explicaron la mayor "
        f"incidencia alcista, compensados por la estabilidad en la <b>inflación núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}% MoM)</b> -- el contrato no discrimina un rubro "
        f"\"bienes transables\" separado. En el frente monetario, la tasa real ex-ante ({_fmt1(tasa_real_exante, signo=True)}% mensual TEM Lecap vs. REM) opera como barrera contra la "
        f"dolarización de carteras. La absorción bancaria de liquidez ya no opera vía Lefi (mecanismo discontinuado desde julio de 2025, stock real en $0) sino vía la tasa de pases "
        f"pasivos a 1 día ({_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA) y el equilibrio presupuestario primario.",
        body_style
    ))
    elements.append(Paragraph(
        f"En el plano sociopolítico y distributivo, la Canasta Básica Total en Mendoza (${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)}) exige ingresos crecientes para superar "
        f"el umbral de pobreza. RIPTE: {_ripte_txt}. La pérdida de poder de compra del sector no registrado y la mora en créditos de consumo no tienen fuente automatizable en el "
        f"repositorio: {SIN_FUENTE}. A nivel soberano, el EMBI+ se ubica en {fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb{_embi_var_30d_txt}, "
        "lo que reduce el costo de fondeo y habilita la rotación de carteras hacia tramos medios-largos de Globales con elevado potencial de revalorización de capital.",
        body_style
    ))
    elements.append(Spacer(1, 2))

    elements.append(Paragraph("<b>Matriz de Escenarios Macroeconómicos a 12 Meses:</b>", h2_style))
    elements.append(Paragraph(
        "<i>Proyección y juicio del analista -- probabilidades, rangos y estrategia son escenarios de research, no datos de mercado observados ni un modelo econométrico formal de proyección.</i>",
        fig_caption
    ))

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
            Paragraph("Carry en Lecaps del tramo corto + sobreponderar tramo GD35/GD38.", cell_style_left)
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

    elements.append(Paragraph("<b>Guía de Asignación Táctica de Carteras (Asset Allocation Recomendado -- criterio del analista):</b>", h2_style))
    carteras_data = [
        [Paragraph("<b>Perfil de Inversor</b>", cell_header_style), Paragraph("<b>Horizonte</b>", cell_header_style), Paragraph("<b>Composición Recomendada (% Cartera)</b>", cell_header_style), Paragraph("<b>Tesis de Rendimiento / Cobertura</b>", cell_header_style)],
        [Paragraph("<b>Conservador (Treasury)</b>", cell_style_left), Paragraph("30 - 60 días", cell_style_center), Paragraph("<b>70%</b> Lecap tramo corto + <b>30%</b> Boncer TZX27", cell_style_left), Paragraph(f"Captura de TEM {_fmt1(tasas_ars.get('lecap_corta_tem'))}% con mínima volatilidad en pesos.", cell_style_left)],
        [Paragraph("<b>Moderado (Institucional)</b>", cell_style_left), Paragraph("90 - 180 días", cell_style_center), Paragraph("<b>40%</b> Lecap tramo largo + <b>20%</b> TZX27 + <b>25%</b> GD35/GD38 + <b>15%</b> Bopreal 3", cell_style_left), Paragraph("Balance carry real positivo con potencial compresión USD.", cell_style_left)],
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
        [Paragraph("Brecha Cambiaria CCL / Oficial", cell_style_left), Paragraph(f"{_fmt1(dolar.get('brecha_ccl_oficial_pct'))}% (CCL ${fmt_num(dolar.get('ccl'), 2)})", cell_style_center), Paragraph("<b>Baja Presión</b>", cell_style_center), Paragraph("Oferta exportadora del blend 80/20 contiene la volatilidad financiera.", cell_style_left)],
        [Paragraph("Dólar Futuro CIP a 30d (teórico)", cell_style_left), Paragraph(f"${fmt_num(dolar_futuro['curva'][0]['futuro_implicito'], 2)} ({_fmt1(dolar_futuro['curva'][0]['tna_implicita_pct'])}% TNA)" if dolar_futuro else SIN_FUENTE, cell_style_center), Paragraph("<b>Modelo, no mercado</b>", cell_style_center), Paragraph("Paridad de tasas cubierta (CIP) sobre datos reales; no es una cotización de Matba-Rofex (sin conector a ese mercado en el repositorio).", cell_style_left)],
        [Paragraph("Spread EMBI+ Argentina (J.P. Morgan)", cell_style_left), Paragraph(f"{fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb{_embi_var_30d_txt}", cell_style_center), Paragraph("<b>Nivel Vigente</b>", cell_style_center), Paragraph("Nivel: contrato manual. Variación 30d: fuente secundaria ArgentinaDatos (no JP Morgan/Bloomberg directo).", cell_style_left)],
        [Paragraph("Tasa de Pases Pasivos BCRA (1 día)", cell_style_left), Paragraph(f"{_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA", cell_style_center), Paragraph("<b>Vigente</b>", cell_style_center), Paragraph("Mecanismo de esterilización bancaria vigente; Lefi está discontinuado desde jul-2025 (stock real $0).", cell_style_left)]
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

    _breakeven_mensual = tasas_ars.get("breakeven_inflacion_tem")
    _breakeven_anualizado = round(100 * ((1 + _breakeven_mensual / 100) ** 12 - 1), 2) if _breakeven_mensual is not None else None
    elements.append(Paragraph(
        f"El mercado de deuda en pesos refleja una marcada preferencia por el carry trade de corto plazo. La curva de Lecaps (tasa fija) opera con TEMs de "
        f"{_fmt1(tasas_ars.get('lecap_corta_tem'))}% (tramo corto) a {_fmt1(tasas_ars.get('lecap_larga_tem'))}% (tramo largo) -- el contrato no especifica plazos "
        f"en días ni tickers puntuales para estos dos puntos. El único título Boncer con dato real es TZX27, con TIR real de +{_fmt1(tasas_ars.get('boncer_tzx27_tir_real'))}% anual "
        f"({SIN_FUENTE} para otros Boncer como TZX28). A partir de esta estructura, el <b>breakeven de inflación implícita</b> se sitúa en {_fmt1(_breakeven_mensual)}% mensual para el "
        f"tramo corto y {_fmt1(_breakeven_anualizado)}% anualizado (derivado por capitalización compuesta simple del dato mensual, no una serie anualizada observada aparte).",
        body_style
    ))
    elements.append(Paragraph(
        f"Dado que el REM proyecta una inflación mensual de {_fmt1(tasas_ars.get('inflacion_esperada_rem_tem'))}% (el contrato solo trae este punto, no un sendero descendente), "
        f"la tasa fija ofrece un premio de {fmt_num(tasas_ars.get('premio_tasa_fija_pbs'), 0)} pb mensuales sobre la inflación esperada. La estrategia táctica óptima consiste en "
        "maximizar exposición en Lecaps del tramo corto para capturar el diferencial de rendimiento real sin asumir el riesgo de extensión de duration.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_1_rates.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    _lecap_corta_tem = tasas_ars.get("lecap_corta_tem")
    _lecap_larga_tem = tasas_ars.get("lecap_larga_tem")
    _lecap_corta_tna = round(_lecap_corta_tem * 12, 1) if _lecap_corta_tem is not None else None  # TNA simple (TEM x 12), no compuesta
    _lecap_larga_tna = round(_lecap_larga_tem * 12, 1) if _lecap_larga_tem is not None else None
    # "Duration / Convex." se retira: 100% s/d en las 4 filas (no hay motor
    # de pricing de bonos en el repositorio). "Bopreal Serie 3 (USD)" se
    # retira como fila: sin esa columna, no le queda un solo dato real en
    # ninguna de las restantes (ver Seccion 0 de AGENT_RUNBOOK.md).
    tabla_tactica_data = [
        [Paragraph("<b>Instrumento / Especie</b>", cell_header_style), Paragraph("<b>TNA / TEM</b>", cell_header_style), Paragraph("<b>Breakeven / TIR</b>", cell_header_style), Paragraph("<b>Tesis & Ponderación Táctica</b>", cell_header_style)],
        [Paragraph("Lecap (tramo corto)", cell_style_left), Paragraph(f"{_fmt1(_lecap_corta_tna)}% TNA ({_fmt1(_lecap_corta_tem)}% TEM)", cell_style_center), Paragraph(f"BE: {_fmt1(tasas_ars.get('breakeven_inflacion_tem'))}% MoM", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Máximo carry con riesgo tasa mínimo. El contrato no especifica ticker ni plazo en días.", cell_style_left)],
        [Paragraph("Lecap (tramo largo)", cell_style_left), Paragraph(f"{_fmt1(_lecap_larga_tna)}% TNA ({_fmt1(_lecap_larga_tem)}% TEM)", cell_style_center), Paragraph("BE: s/d (contrato trae un único breakeven, sin desagregar por tramo)", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Captura tasa fija en el tramo largo de la curva Lecap.", cell_style_left)],
        [Paragraph("Boncer TZX27", cell_style_left), Paragraph(f"CER + {_fmt1(tasas_ars.get('boncer_tzx27_tir_real'))}% TIR Real", cell_style_center), Paragraph(f"TIR Real: +{_fmt1(tasas_ars.get('boncer_tzx27_tir_real'))}%", cell_style_center), Paragraph("<b>NEUTRAL</b> · Cobertura si regulados aceleran por encima de la tasa fija.", cell_style_left)],
    ]
    t_tactica = Table(tabla_tactica_data, colWidths=[125, 115, 100, 192])
    t_tactica.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
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
        f"La dinámica de precios de {periodo_texto} confirmó la consolidación del sendero desinflacionario nacional ({_fmt1(inflacion.get('indec_general_mom'))}% MoM) y provincial "
        f"(Mendoza: {_fmt1(inflacion.get('deie_mendoza_mom'))}% MoM). Por orden de incidencia relativa, los aumentos estuvieron encabezados por los <b>precios regulados "
        f"({_fmt1(inflacion.get('indec_regulados_mom'))}% INDEC; {SIN_FUENTE} para la apertura DEIE de regulados)</b> y los <b>servicios privados ({_fmt1(inflacion.get('indec_servicios_mom'))}% MoM)</b>. "
        f"Como contrapartida, la <b>inflación núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}% MoM)</b> actuó como ancla de convergencia; el contrato no discrimina aperturas propias de "
        f"\"bienes transables\" ni de \"alimentos\": {SIN_FUENTE}.",
        body_style
    ))
    elements.append(Paragraph(
        f"En el plano social, la valorización de las canastas en Mendoza sitúa la Canasta Básica Alimentaria (CBA) en ${fmt_num(inflacion.get('canasta_basica_alimentaria_mza'), 0)} y la "
        f"Total (CBT) en ${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)} para una familia tipo. RIPTE (nominal, no deflactado): {_ripte_txt}.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_2_ipc.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_social_data = [
        [Paragraph("<b>Indicador Social / Canasta (Mendoza)</b>", cell_header_style), Paragraph(f"<b>Valor {mes_nombre[:3]}-{str(anio_informe)[2:]}</b>", cell_header_style), Paragraph("<b>Variación MoM</b>", cell_header_style), Paragraph("<b>Cobertura / Brecha de Ingresos</b>", cell_header_style)],
        [Paragraph("Canasta Básica Alimentaria (CBA Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_alimentaria_mza'), 0)}", cell_style_center), Paragraph("s/d (contrato no trae variación, solo nivel)", cell_style_center), Paragraph("Línea de Indigencia (umbral de ingresos requerido: carga manual).", cell_style_left)],
        [Paragraph("Canasta Básica Total (CBT Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)}", cell_style_center), Paragraph("s/d (contrato no trae variación, solo nivel)", cell_style_center), Paragraph("Línea de Pobreza (brecha frente a ingresos no registrados: carga manual).", cell_style_left)],
        [Paragraph("Salario Formal Nominal (RIPTE)", cell_style_left), Paragraph(f"${fmt_num(ripte['valores'][-1], 0)}" if ripte else SIN_FUENTE, cell_style_center), Paragraph(f"{_fmt1(ripte.get('var_mensual_ultimo'), signo=True)}% MoM" if ripte else SIN_FUENTE, cell_style_center), Paragraph("RIPTE nacional nominal (Secretaría de Trabajo) -- no deflactado por inflación, no es \"salario real\".", cell_style_left)],
    ]
    # "Mora en Creditos de Consumo" se retira: no tenia un solo dato real en
    # ninguna columna (ni valor ni variacion), solo la explicacion de que no
    # hay conector -- una fila asi no aporta nada que el texto de arriba no
    # diga ya (ver Seccion 0 de AGENT_RUNBOOK.md).
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
    elements.append(Paragraph(f"<i>Variación mensual, acumulada e interanual según aperturas por orden de incidencia relativa. {periodo_texto_cap}, en porcentaje.</i>", ParagraphStyle('ST', fontName='Georgia-Italic', fontSize=7.5, textColor=MUTED, spaceAfter=4)))

    # Acumulado real del anio calendario: producto compuesto de la trayectoria
    # mensual real del INDEC (src/fetch_series_indec_bcra.obtener_ipc_trayectoria,
    # que llega hasta el mes anterior) mas el mes vigente del contrato principal.
    # Interanual: el contrato y los fetchers disponibles no traen el nivel de
    # indice de hace 12 meses en NINGUNA apertura -- una columna 100% "s/d"
    # violaria la regla de cero fabricacion/cero relleno (AGENT_RUNBOOK.md,
    # Seccion 0), asi que se retira la columna entera en vez de repetir el
    # mismo "s/d" 10 veces. Por la misma razon se retiran las filas que, sin
    # esa columna, quedarian sin un solo dato real (Vivienda, Transporte,
    # Bienes, Alimentos, Estacionales -- ninguna tiene fuente de Mensual ni
    # de Acumulado en el contrato).
    _acum_general, _n_acum = _acumulado_anio_calendario(
        (ipc_tray or {}).get("meses"), (ipc_tray or {}).get("general"), anio_informe, inflacion.get("indec_general_mom"))
    _acum_nucleo, _ = _acumulado_anio_calendario(
        (ipc_tray or {}).get("meses"), (ipc_tray or {}).get("nucleo"), anio_informe, inflacion.get("indec_nucleo_mom"))
    _acum_regulados, _ = _acumulado_anio_calendario(
        (ipc_tray or {}).get("meses"), (ipc_tray or {}).get("regulados"), anio_informe, inflacion.get("indec_regulados_mom"))
    _col_acum_header = f"Acum. {anio_informe} ({_n_acum} meses)" if _n_acum else f"Acum. {anio_informe}"
    _col_mensual_header = f"Mensual ({mes_nombre[:3]}-{str(anio_informe)[2:]})"

    tabla_ipc_data = [
        [
            Paragraph("<b>Apertura / Jurisdicción</b>", cell_header_style),
            Paragraph(f"<b>{_col_mensual_header}</b>", cell_header_style),
            Paragraph(f"<b>{_col_acum_header}</b>", cell_header_style),
        ],
        [Paragraph("<b>Precios Regulados (Mayor Incidencia)</b>", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_regulados_mom'))}%", cell_style_center), Paragraph(f"{_fmt1(_acum_regulados)}%", cell_style_center)],
        [Paragraph("Servicios (INDEC)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_servicios_mom'))}%", cell_style_center), Paragraph(SIN_FUENTE, cell_style_center)],
        [Paragraph("Provincia de Mendoza (DEIE General)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('deie_mendoza_mom'))}%", cell_style_center), Paragraph(SIN_FUENTE, cell_style_center)],
        [Paragraph("Nivel General Nacional (INDEC)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_general_mom'))}%", cell_style_center), Paragraph(f"{_fmt1(_acum_general)}%", cell_style_center)],
        [Paragraph("IPC Núcleo (INDEC)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_nucleo_mom'))}%", cell_style_center), Paragraph(f"{_fmt1(_acum_nucleo)}%", cell_style_center)],
    ]

    t_ipc = Table(tabla_ipc_data, colWidths=[232, 150, 150])
    t_ipc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#FEE2E2")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#EFF6FF")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ipc)
    elements.append(Spacer(1, 2.5))
    elements.append(Paragraph("<i>Fuente:</i> INDEC y DEIE Mendoza (columna mensual); acumulado del año calendario derivado por capitalización compuesta de la trayectoria real INDEC (src/fetch_series_indec_bcra.py). La variación interanual y las aperturas de Vivienda/Transporte/Bienes/Alimentos/Estacionales se retiran de este cuadro: ninguna tiene fuente automatizable en el repositorio (ver AGENT_RUNBOOK.md, Sección 0).", fig_caption))
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Canales de Transmisión y Elasticidad de Pass-Through a Precios (estimación cualitativa del analista, no medición econométrica):</b>", h2_style))
    tabla_passthrough_data = [
        [Paragraph("<b>Canal de Transmisión / Rubro</b>", cell_header_style), Paragraph("<b>Elasticidad / Pass-Through</b>", cell_header_style), Paragraph("<b>Implicancia para Empresas y Consumo</b>", cell_header_style)],
        [Paragraph("Tarifas de Electricidad y Gas de Red", cell_style_left), Paragraph("Directo (100% regulado) -- estimación cualitativa", cell_style_center), Paragraph("Aumento en costos fijos de PyMEs industriales y riego agrícola.", cell_style_left)],
        [Paragraph("Combustibles y Fletes Interurbanos", cell_style_left), Paragraph("Rápido -- estimación cualitativa, sin medición", cell_style_center), Paragraph("Presión en logística de bodegas y distribución de alimentos.", cell_style_left)],
        [Paragraph("Alimentos Secos y Productos de Almacén", cell_style_left), Paragraph("Moderado -- estimación cualitativa, sin medición", cell_style_center), Paragraph("Migración del consumidor hacia segundas y terceras marcas.", cell_style_left)],
        [Paragraph("Indumentaria y Calzado", cell_style_left), Paragraph("Bajo -- estimación cualitativa, sin medición", cell_style_center), Paragraph("Caída en márgenes comerciales por necesidad de liquidar stock.", cell_style_left)]
    ]
    t_pt = Table(tabla_passthrough_data, colWidths=[177, 155, 200])
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
        [Paragraph(
            f"La divergencia entre la inflación núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}% MoM) y servicios/regulados "
            f"({_fmt1(inflacion.get('indec_servicios_mom'))}%/{_fmt1(inflacion.get('indec_regulados_mom'))}% MoM) ratifica que el proceso desinflacionario transita su fase de "
            f"corrección de precios relativos; el contrato no discrimina un rubro \"bienes\" aparte de núcleo. La estabilidad del tipo de cambio mayorista (${fmt_num(dolar.get('mayorista'), 2)}) "
            f"funciona como ancla para los transables. El Índice de Precios Internos Mayoristas (IPIM) no tiene fuente automatizable en el repositorio: {SIN_FUENTE}.",
            ParagraphStyle('PTB', fontName='Georgia', fontSize=6.8, leading=9.0, textColor=SLATE))]
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
        [Paragraph(
            f"• <b>Comercio Mayorista y Retail:</b> Se recomienda rotación rápida de inventarios sobre márgenes unitarios, evitando acumulación de stock apalancado a tasas del "
            f"{_fmt1(round(tasas_ars.get('lecap_corta_tem') * 12, 1) if tasas_ars.get('lecap_corta_tem') is not None else None)}% TNA (Lecap tramo corto, TEM x 12).<br/>"
            f"• <b>Industria Agroalimentaria:</b> Aprovechar estabilidad en costos de granos para pactar compras a plazo fijo en ARS con descuento financiero de referencia sobre la tasa fija corta.<br/>"
            f"• <b>Empresas de Servicios:</b> Incorporar cláusulas de indexación escalonadas en contratos corporativos basadas en IPC Núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}% MoM) "
            f"y RIPTE nominal ({_ripte_txt}).",
            ParagraphStyle('MPB', fontName='Georgia', fontSize=6.8, leading=9.0, textColor=DARK_TEXT))]
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

    _emae_tendencia_mom = None
    if emae_hist and len(emae_hist.get("tendencia_ciclo", [])) >= 2:
        _t_serie = emae_hist["tendencia_ciclo"]
        _emae_tendencia_mom = round(100 * (_t_serie[-1] / _t_serie[-2] - 1), 2)
    _tendencia_txt = (
        f"La tendencia-ciclo (serie real INDEC, src/fetch_series_indec_bcra.py) avanzó {_fmt1(_emae_tendencia_mom, signo=True)}% mensual"
        if _emae_tendencia_mom is not None else f"La tendencia-ciclo mensual: {SIN_FUENTE}"
    )
    elements.append(Paragraph(
        f"El Estimador Mensual de Actividad Económica (EMAE) creció {_fmt1(actividad.get('emae_interanual_pct'), signo=True)}% en la comparación interanual y avanzó "
        f"{_fmt1(actividad.get('emae_desestacionalizado_mom_pct'), signo=True)}% en su medición desestacionalizada respecto al mes previo. {_tendencia_txt}, ratificando la "
        "trayectoria de recuperación de la actividad.",
        body_style
    ))
    elements.append(Paragraph(
        f"El contrato de datos no desagrega el EMAE por sector de actividad (minería, agro, comercio, industria, intermediación financiera, construcción): la desagregación "
        f"sectorial con variación i.a./MoM que solía mostrarse aquí no tiene fuente automatizable en el repositorio: {SIN_FUENTE} y se omite en vez de presentar cifras no verificadas.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_emae_master.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "<i>El INDEC no publica el EMAE desagregado por rama de actividad con la granularidad mensual que requeriría un semáforo sectorial -- la tabla que solía "
        "presentarse aquí (minería, agro, finanzas, construcción, comercio) no tiene conector real en este repositorio y se retira en vez de mostrar valores no verificados.</i>",
        fig_caption
    ))
    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 8: 4. SECTORES CUYO (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("4. Desagregación Sectorial y Producción en Mendoza y Cuyo", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        "La vitivinicultura (Instituto Nacional de Vitivinicultura) y los hidrocarburos de la cuenca cuyana (Secretaría de Energía) son dos de las cadenas de valor de mayor "
        "peso relativo en la estructura productiva de Mendoza y Cuyo, y ninguna de las dos tiene un conector confiable en este repositorio -- un candidato evaluado para "
        f"despachos de vino no pasó un chequeo básico de sensatez (valores fuera de escala, metadata contradictoria) y se descartó en vez de usarlo: {SIN_FUENTE}. "
        "Para la construcción sí existe un proxy real: el Indicador Sintético de la Actividad de la Construcción (ISAC, INDEC) -- es un índice <b>nacional</b>, no el dato de "
        "cemento portland (AFCP) específico de Cuyo que este informe mostraba antes; el cambio de alcance queda declarado explícitamente en el gráfico.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_3_cuyo.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "<i>Cuadro de cadenas de valor (Vino Fraccionado/Granel INV, Petróleo Convencional y Vaca Muerta mendocina) retirado de esta edición: sin conector automatizable en el "
        "repositorio -- requiere carga manual explícita por corrida. Cemento/construcción: ver proxy nacional ISAC en la infografía de arriba.</i>",
        fig_caption
    ))

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 9: 4.1 COMPARATIVO REGIONAL CUYO (MENDOZA / SAN JUAN / SAN LUIS)
    # =============================================================
    elements.append(Paragraph("4.1. Comparativo Regional: Índice Sintético de Actividad (ISARC)", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        f"La sección anterior desagregó la producción de Mendoza; esta sección completa la lectura regional de Cuyo incorporando San Juan y San Luis a través del "
        f"<b>Índice Sintético de Actividad Regional (ISARC)</b>. El contrato de datos solo trae la <b>variación interanual</b> del índice por provincia -- no el nivel del "
        f"índice en puntos ni su desagregación sectorial (industria manufacturera, construcción, empleo registrado), que en ediciones anteriores se completaba con un literal "
        f"de relleno idéntico entre provincias y corridas ({SIN_FUENTE} para nivel/desagregación). San Luis lidera el ritmo de expansión regional con "
        f"<b>{_fmt1(actividad.get('isarc_san_luis_ia_pct'), signo=True)}% i.a.</b>, seguida por Mendoza en <b>{_fmt1(actividad.get('isarc_mendoza_ia_pct'), signo=True)}% i.a.</b> "
        f"y San Juan en <b>{_fmt1(actividad.get('isarc_san_juan_ia_pct'), signo=True)}% i.a.</b>, la de menor dinamismo relativo.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_3b_regional_cuyo.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("<b>Cuadro. Variación Interanual del ISARC por Provincia:</b>", h2_style))
    # Nivel del indice y desagregacion sectorial se retiran: ninguna de las
    # 3 provincias tiene ese dato en el contrato, asi que esas 2 columnas
    # quedaban 100% "s/d" -- la misma regla que en el Cuadro 1 de IPC
    # (ver Seccion 0 de AGENT_RUNBOOK.md).
    regional_header = [Paragraph("<b>Provincia</b>", cell_header_style), Paragraph("<b>ISARC Var. i.a.</b>", cell_header_style)]
    regional_rows = [
        ("Mendoza", actividad.get("isarc_mendoza_ia_pct")),
        ("San Juan", actividad.get("isarc_san_juan_ia_pct")),
        ("San Luis", actividad.get("isarc_san_luis_ia_pct")),
    ]
    regional_data = [regional_header]
    heat_cmds_regional = []
    for i, (prov, isarc_ia) in enumerate(regional_rows, start=1):
        if isarc_ia is not None:
            signo = "+" if isarc_ia >= 0 else ""
            color = POS.hexval() if isarc_ia > 0 else (NEG.hexval() if isarc_ia < 0 else DARK_TEXT.hexval())
            celda_ia = Paragraph(f'<font color="{color}"><b>{signo}{isarc_ia:.1f}%</b></font>', cell_style_center)
            heat_cmds_regional.append(('BACKGROUND', (1, i), (1, i), _heat_bg(isarc_ia)))
        else:
            celda_ia = Paragraph("s/d", cell_style_center)
        regional_data.append([
            Paragraph(f"<b>{prov}</b>", cell_style_left),
            celda_ia,
        ])

    t_regional = Table(regional_data, colWidths=[266, 266])
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
        "<i>Fuente: datos_del_dia.json (actividad.isarc_*_ia_pct). ISARC: índice compuesto de elaboración propia; celda con intensidad de color proporcional a la magnitud "
        "de la variación interanual (verde: expansión, rojo: contracción). Nivel del índice y desagregación sectorial retirados de este cuadro: sin fuente pública automatizable "
        "para ninguna de las 3 provincias.</i>",
        fig_caption
    ))

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 10: 5. BALANCE BCRA Y REGLA DE TAYLOR
    # =============================================================
    elements.append(Paragraph("5. Balance del BCRA, Pasivos Cuasifiscales y Brecha de Taylor", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    _base_monetaria_ultimo = None
    _base_monetaria_mes = None
    _pases_stock_ultimo = None
    if monetario_hist and monetario_hist.get("base_m"):
        _base_monetaria_ultimo = monetario_hist["base_m"][-1]
        _base_monetaria_mes = monetario_hist["meses"][-1]
    if monetario_hist and monetario_hist.get("pases_m"):
        _pases_stock_ultimo = monetario_hist["pases_m"][-1]

    elements.append(Paragraph(
        f"El esquema monetario mantiene extinguido el stock de pases pasivos remunerados (BCRA v4.0, id=152"
        f"{f', {_fmt1(_pases_stock_ultimo)} $ B en {_base_monetaria_mes}' if _pases_stock_ultimo is not None else ''}) desde julio de 2025 -- el mecanismo de esterilización "
        f"opera hoy vía la <b>tasa</b> de pases a 1 día ({_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA, vigente como referencia aunque sin stock asociado, "
        f"no un dato contradictorio con el stock extinto). Las Letras Fiscales de Liquidez (Lefi, BCRA id=196) también están discontinuadas desde jul-2025: su stock real "
        f"es $0, no los $29,3 billones que figuraban en ediciones anteriores de este informe. La Base Monetaria promedio"
        f"{f' de {_base_monetaria_mes}' if _base_monetaria_mes else ''} se ubicó en {f'${_fmt1(_base_monetaria_ultimo)} billones' if _base_monetaria_ultimo is not None else SIN_FUENTE} (BCRA v4.0, id=15).",
        body_style
    ))
    elements.append(Paragraph(
        f"Bajo una formulación de la Regla de Taylor con tasa real ex-ante (TEM Lecap {_fmt1(tasas_ars.get('lecap_corta_tem'))}% − REM "
        f"{_fmt1(tasas_ars.get('inflacion_esperada_rem_tem'))}% = {_fmt1(tasa_real_exante, signo=True)}% mensual), la tasa de política monetaria se compara contra una tasa "
        "neutral r* que este informe fija en 0,75% mensual como <b>supuesto explícito del analista, no un dato observado</b> -- el BCRA no publica una estimación oficial de "
        "r* para el esquema monetario vigente. Bajo ese supuesto, la brecha resultante es contractiva y compatible con el anclaje de expectativas inflacionarias.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_4_monetary.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    tabla_rin_data = [
        [Paragraph("<b>Factor de Variación Monetaria / Balance</b>", cell_header_style), Paragraph("<b>Monto (ARS / USD)</b>", cell_header_style), Paragraph("<b>Efecto Neto</b>", cell_header_style), Paragraph("<b>Implicancia para la Estabilidad Financiera</b>", cell_header_style)],
        [Paragraph("Tasa de Pases Pasivos BCRA (1 día, TNA)", cell_style_left), Paragraph(f"{_fmt1(tasas_bcra.get('pases_1d_tna', {}).get('valor'))}% TNA", cell_style_center), Paragraph("Referencia vigente", cell_style_center), Paragraph("Tasa de referencia de esterilización bancaria; distinta del stock de pases (ver fila siguiente).", cell_style_left)],
        [Paragraph("Stock de Pases Pasivos Remunerados", cell_style_left), Paragraph(f"{f'{_fmt1(_pases_stock_ultimo)} $ B' if _pases_stock_ultimo is not None else SIN_FUENTE}", cell_style_center), Paragraph("Extinto", cell_style_center), Paragraph("Confirmado: mecanismo sin stock desde jul-2025 (BCRA v4.0, id=152).", cell_style_left)],
        [Paragraph("Base Monetaria (promedio mensual)", cell_style_left), Paragraph(f"{f'${_fmt1(_base_monetaria_ultimo)} $ B' if _base_monetaria_ultimo is not None else SIN_FUENTE}", cell_style_center), Paragraph("Controlado", cell_style_center), Paragraph("Serie real BCRA v4.0, id=15 (src/fetch_series_indec_bcra.py).", cell_style_left)],
        [Paragraph("Absorción Cuasifiscal vía Lefi (Tesoro, id=196)", cell_style_left), Paragraph("$0,0 Billones", cell_style_center), Paragraph("Discontinuado", cell_style_center), Paragraph("Mecanismo discontinuado desde jul-2025; no forma parte de la absorción vigente.", cell_style_left)],
        [Paragraph("Reservas Internacionales Brutas (BCRA)", cell_style_left), Paragraph(f"USD {fmt_num(tasas_bcra.get('reservas_brutas_usd_m', {}).get('valor'), 0)} M", cell_style_center), Paragraph("Nivel vigente", cell_style_center), Paragraph(f"Dato disponible es BRUTO, no neto; el contrato no trae reservas netas: {SIN_FUENTE}.", cell_style_left)]
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
        f"El ajuste paramétrico de la curva soberana en moneda extranjera bajo el modelo Nelson-Siegel arrojó parámetros de nivel (β₀ = {_fmt1(ns.get('beta0'))}%), pendiente "
        f"(β₁ = {_fmt1(ns.get('beta1'), signo=True)}%), curvatura (β₂ = {_fmt1(ns.get('beta2'), signo=True)}%) y parámetro de decaimiento τ = {_fmt1(ns.get('tau'), decimales=2)} "
        f"(R² = {_fmt1(ns.get('r2'), decimales=3)}; RMSE: {SIN_FUENTE}). La curva spot presenta AL30 en {_fmt1(soberano.get('al30_tir'))}% TIR y GD38 en "
        f"{_fmt1(soberano.get('gd38_tir'))}% TIR; la convergencia de la tasa forward instantánea f(t) hacia un nivel puntual no está calculada en el repositorio: "
        f"{SIN_FUENTE}, y se omite en vez de citar un número no verificado.",
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
        [Paragraph("Nivel de Largo Plazo", cell_style_left), Paragraph("β₀", cell_style_center), Paragraph(f"{_fmt1(ns.get('beta0'))}%", cell_style_center), Paragraph(f"R² = {_fmt1(ns.get('r2'), decimales=3)} · RMSE: {SIN_FUENTE}", cell_style_center)],
        [Paragraph("Pendiente / Curvatura", cell_style_left), Paragraph("β₁ / β₂", cell_style_center), Paragraph(f"{_fmt1(ns.get('beta1'), signo=True)}% / {_fmt1(ns.get('beta2'), signo=True)}%", cell_style_center), Paragraph(f"Parámetro decaimiento τ = {_fmt1(ns.get('tau'), decimales=2)}", cell_style_center)],
        [Paragraph("Bonar 2030 (Ley Local)", cell_style_left), Paragraph("AL30", cell_style_center), Paragraph(f"{_fmt1(soberano.get('al30_tir'))}% TIR", cell_style_center), Paragraph(f"Duration/Paridad: {SIN_FUENTE}", cell_style_center)],
        [Paragraph("Global 2038 (Ley NY)", cell_style_left), Paragraph("GD38", cell_style_center), Paragraph(f"{_fmt1(soberano.get('gd38_tir'))}% TIR", cell_style_center), Paragraph(f"Duration/Paridad: {SIN_FUENTE}", cell_style_center)]
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

    elements.append(Paragraph(
        "<b>Stress Test de Convexidad ante Shocks de Spread (proyección propia, no verificada contra un motor de pricing de bonos real):</b>", h2_style
    ))
    elements.append(Paragraph(
        "<i>No hay un motor de pricing de renta fija en el repositorio -- las convexidades y los retornos por shock de spread de este cuadro son una estimación "
        "propia del analista con fines ilustrativos, no un cálculo verificado contra los flujos de fondos reales de cada bono.</i>",
        fig_caption
    ))

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
        f"El mercado cambiario finalizó {periodo_texto} con el Dólar CCL en ${fmt_num(dolar.get('ccl'), 2)}, el Dólar MEP en ${fmt_num(dolar.get('mep'), 2)} y el Oficial BNA en "
        f"${fmt_num(dolar.get('oficial_bna'), 2)} (brecha CCL/oficial de {_fmt1(dolar.get('brecha_ccl_oficial_pct'))}%; mayorista A3500 en ${fmt_num(dolar.get('mayorista'), 2)}). "
        "Sin conector a Matba-Rofex para cotización de mercado; el cuadro más abajo muestra en su lugar un dólar futuro teórico por paridad de tasas cubierta (CIP).",
        body_style
    ))
    elements.append(Paragraph(
        f"Ratio de Absorción (PCA, Kritzman &amp; Li 2010, sobre retornos reales de oficial/mayorista/BADLAR/pases/Merval): <b>{_ar_txt}</b>. Turbulencia de Mahalanobis: "
        f"<b>{_turb_txt}</b> vs. umbral Chi² 95% de <b>{_turb_umbral_txt}</b> (régimen: <b>{_regimen_txt}</b>).",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_6_fx.png"), width=532, height=285))
    elements.append(Spacer(1, 3))

    # --- Tipo de Cambio Real Bilateral (atraso/competitividad cambiaria) ---
    # A diferencia de casi todo el resto de este generador, este parrafo NO
    # es texto de plantilla con numeros fijos: se arma en el momento de
    # generar el informe, leyendo el cache real de
    # src/fetch_tcr_bilateral.py (BCRA + INDEC + BLS). Si el cache no existe
    # todavia, el informe lo dice explicitamente en vez de inventar un
    # numero o mostrar una version vieja sin avisar.
    elements.append(Paragraph("<b>Tipo de Cambio Real Bilateral: ¿Brecha o Atraso Cambiario?</b>", h2_style))
    _tcr_cache = cargar_cache_tcr()
    if _tcr_cache and _tcr_cache.get("ultimo"):
        _tcr_ultimo = _tcr_cache["ultimo"]
        _tcr_serie = _tcr_cache["serie"]
        _tcr_pico = max(_tcr_serie[-13:], key=lambda p: p["tcr_indice"]) if len(_tcr_serie) >= 2 else _tcr_ultimo
        _tcr_var_pico = 100 * (_tcr_ultimo["tcr_indice"] / _tcr_pico["tcr_indice"] - 1)
        _tcr_lectura = (
            f"un {abs(_tcr_ultimo['tcr_indice'] - 100):.1f}% por debajo de la base {_tcr_cache['base_mes']} (apreciación real, atraso relativo a ese punto de partida)"
            if _tcr_ultimo["tcr_indice"] < 100 else
            f"un {_tcr_ultimo['tcr_indice'] - 100:.1f}% por encima de la base {_tcr_cache['base_mes']} (depreciación real, más competitivo que ese punto de partida)"
        )
        elements.append(Paragraph(
            f"La brecha cambiaria (CCL vs. oficial, cubierta arriba) y el atraso cambiario son conceptos distintos: la brecha "
            f"es una prima de mercado paralelo asociada al cepo; el atraso es una desalineación del tipo de cambio real frente "
            f"al poder de compra relativo, y puede existir incluso sin brecha. El <b>Tipo de Cambio Real (TCR) bilateral ARS/USD</b> "
            f"-- tipo de cambio mayorista deflactado por el índice de precios relativo entre Estados Unidos y Argentina -- se ubicó "
            f"en <b>{_tcr_ultimo['tcr_indice']:.1f}</b> en {_tcr_ultimo['mes']} (índice base {_tcr_cache['base_mes']} = 100), es decir, "
            f"{_tcr_lectura}. Tras el pico de los últimos doce meses ({_tcr_pico['tcr_indice']:.1f} en {_tcr_pico['mes']}), acumula una "
            f"variación de {_tcr_var_pico:+.1f}%.",
            body_style
        ))
        elements.append(Spacer(1, 2))
        elements.append(Image(_find_image("chart_indec_8_tcr.png"), width=532, height=285))
    else:
        elements.append(Paragraph(
            "Cache del Tipo de Cambio Real bilateral no disponible en esta corrida del pipeline "
            "(src/fetch_tcr_bilateral.py) -- sección omitida en vez de mostrar un valor no verificado.",
            body_style
        ))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("<b>Dólar Futuro Teórico por Paridad de Tasas Cubierta (CIP) -- NO cotización de Matba-Rofex:</b>", h2_style))
    elements.append(Paragraph(
        "<i>F(T) = Mayorista_spot &times; (1 + TEM_Lecap_corta)^(T/30), tasa USD ~0 -- modelo sobre datos reales del contrato, no una cotización de mercado observada.</i>",
        fig_caption
    ))
    _dolar_futuro_por_dias = {c["dias"]: c for c in dolar_futuro["curva"]} if dolar_futuro else {}
    tabla_hedge_data = [
        [Paragraph("<b>Posición / Vencimiento Rofex</b>", cell_header_style), Paragraph("<b>Futuro Implícito CIP (ARS)</b>", cell_header_style), Paragraph("<b>TNA Implícita %</b>", cell_header_style), Paragraph("<b>Prob. Salto Discreto</b>", cell_header_style), Paragraph("<b>Estrategia de Cobertura para Tesorerías</b>", cell_header_style)],
    ]
    for _dias, _label in ((30, "Corto plazo (30 días)"), (90, "Mediano plazo (90 días)"), (180, "Largo plazo (180 días)")):
        _c = _dolar_futuro_por_dias.get(_dias)
        tabla_hedge_data.append([
            Paragraph(_label, cell_style_left),
            Paragraph(f"${fmt_num(_c['futuro_implicito'], 2)}" if _c else SIN_FUENTE, cell_style_center),
            Paragraph(f"{_fmt1(_c['tna_implicita_pct'])}%" if _c else SIN_FUENTE, cell_style_center),
            Paragraph(SIN_FUENTE, cell_style_center),
            Paragraph("Valor teórico (CIP), no cotización de mercado.", cell_style_left),
        ])
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

    # Scorecard de Riesgo Sistemico (Kritzman & Li, 2010), calculado sobre
    # retornos reales (BCRA + yfinance) via src/modelos_riesgo.py -- ver
    # riesgo_sistemico cargado al inicio de esta funcion.
    _k_txt = f"{riesgo_sistemico['k_componentes']}-PC" if riesgo_sistemico else "PC"
    scorecard_data = [
        [Paragraph("<b>Métrica Cuantitativa de Riesgo</b>", cell_header_style), Paragraph("<b>Valor Observado</b>", cell_header_style), Paragraph("<b>Umbral Crítico</b>", cell_header_style), Paragraph("<b>Diagnóstico de Régimen & Acción Preventiva</b>", cell_header_style)],
        [Paragraph(f"Ratio de Absorción (AR {_k_txt})", cell_style_left), Paragraph(_ar_txt, cell_style_center), Paragraph("> 75,0% (Fragilidad)", cell_style_center), Paragraph(f"Oficial/mayorista/BADLAR/pases/Merval ({riesgo_sistemico['n_observaciones']} obs.)." if riesgo_sistemico else _riesgo_sist_fuente, cell_style_left)],
        [Paragraph("Turbulencia de Mahalanobis (dt)", cell_style_left), Paragraph(_turb_txt, cell_style_center), Paragraph(f"&gt; {_turb_umbral_txt} (Chi² 95%)", cell_style_center), Paragraph(f"Régimen: {_regimen_txt}." if riesgo_sistemico else _riesgo_sist_fuente, cell_style_left)],
        [Paragraph("Variación Estandarizada (Delta AR)", cell_style_left), Paragraph(SIN_FUENTE, cell_style_center), Paragraph("> +1,50 sigma", cell_style_center), Paragraph("Cálculo puntual, no rolling; requiere ventana histórica del AR.", cell_style_left)]
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

    _lideres_por_ticker = {l.get("ticker"): l for l in (equity.get("lideres") or [])}
    _ypfd = _lideres_por_ticker.get("YPFD", {})
    _pamp = _lideres_por_ticker.get("PAMP", {})
    _ggal_l = _lideres_por_ticker.get("GGAL", {})
    _var_ggal = variaciones_acciones.get("GGAL", {}).get("var_semanal_pct")
    _var_bma = variaciones_acciones.get("BMA", {}).get("var_semanal_pct")
    _var_bbar = variaciones_acciones.get("BBAR", {}).get("var_semanal_pct")
    _var_tgs = variaciones_acciones.get("TGSU2", {}).get("var_semanal_pct")

    elements.append(Paragraph(
        f"El índice S&amp;P Merval cerró en {fmt_num(equity.get('merval_ars'), 0)} puntos ({_fmt1(equity.get('var_semanal_pct'), signo=True)}% semanal), impulsado por la "
        f"solidez operativa del sector energético y bancario. En el segmento energético, <b>YPF ({_fmt1(_ypfd.get('ev_ebitda'))}x EV/EBITDA y margen operativo del "
        f"{_fmt1(_ypfd.get('margen_ebitda'))}%)</b> y <b>Pampa Energía ({_fmt1(_pamp.get('ev_ebitda'))}x EV/EBITDA y margen del {_fmt1(_pamp.get('margen_ebitda'))}%)</b> "
        f"lideraron las preferencias del mercado. TGS no forma parte de equity.lideres en el contrato de datos: su retorno semanal real (yfinance) fue de "
        f"{_fmt1(_var_tgs, signo=True)}%, pero su múltiplo EV/EBITDA {SIN_FUENTE}.",
        body_style
    ))
    elements.append(Paragraph(
        f"Por su parte, las entidades financieras registraron retornos semanales reales (yfinance, src/fetch_datos_reales.obtener_variacion_semanal_acciones) de "
        f"{_fmt1(_var_ggal, signo=True)}% (Grupo Financiero Galicia, GGAL), {_fmt1(_var_bma, signo=True)}% (Banco Macro, BMA) y {_fmt1(_var_bbar, signo=True)}% "
        "(BBVA Argentina, BBAR), en un entorno de tasas reales positivas en pesos.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_7_equity.png"), width=532, height=300))
    elements.append(Spacer(1, 4))

    # "Deuda Neta / EBITDA" se retira: 100% s/d en las 4 filas -- el
    # contrato no trae ese campo para ninguna empresa (ver Seccion 0 de
    # AGENT_RUNBOOK.md).
    tabla_equity_data = [
        [Paragraph("<b>Empresa / Ticker ByMA</b>", cell_header_style), Paragraph("<b>Múltiplo EV/EBITDA</b>", cell_header_style), Paragraph("<b>Margen EBITDA %</b>", cell_header_style), Paragraph("<b>Catalizadores Estratégicos & RIGI</b>", cell_header_style)],
        [Paragraph("YPF S.A. (YPFD / NYSE)", cell_style_left), Paragraph(f"{_fmt1(_ypfd.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_ypfd.get('margen_ebitda'))}%", cell_style_center), Paragraph("Liderazgo en Vaca Muerta y proyectos RIGI.", cell_style_left)],
        [Paragraph("Pampa Energía (PAMP)", cell_style_left), Paragraph(f"{_fmt1(_pamp.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_pamp.get('margen_ebitda'))}%", cell_style_center), Paragraph("Generación eléctrica y producción de shale gas.", cell_style_left)],
        [Paragraph("Transportadora Gas del Sur (TGSU2)", cell_style_left), Paragraph(SIN_FUENTE, cell_style_center), Paragraph(SIN_FUENTE, cell_style_center), Paragraph(f"Fuera de equity.lideres del contrato; retorno semanal real: {_fmt1(_var_tgs, signo=True)}%.", cell_style_left)],
        [Paragraph("Grupo Financiero Galicia (GGAL)", cell_style_left), Paragraph(f"{_fmt1(_ggal_l.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_ggal_l.get('margen_ebitda'))}%", cell_style_center), Paragraph("Consolidación bancaria y reactivación del crédito comercial.", cell_style_left)]
    ]
    t_eq = Table(tabla_equity_data, colWidths=[145, 90, 90, 207])
    t_eq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
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
        f"En el plano regulatorio, el BCRA mantiene el esquema de encajes no remunerados y absorción vía títulos públicos. El contexto internacional (rendimiento del bono del "
        f"Tesoro de EE.UU. a 10 años, índice DXY, crudo WTI) no tiene ningún conector automatizado en este repositorio -- {SIN_FUENTE}. Estas tres variables quedan "
        "pendientes de carga manual explícita en cada corrida.",
        body_style
    ))
    elements.append(Spacer(1, 2))

    # Calendario de eventos: sin conector a un calendario de vencimientos/
    # eventos en el repositorio (Secretaria de Finanzas, INDEC, FOMC). Se
    # parametriza lo unico que se puede derivar con certeza del periodo de
    # la corrida (mes de publicacion del IPC del mes vigente, ~dia 11-15 del
    # mes siguiente segun el cronograma habitual del INDEC) y se marca el
    # resto explicitamente como carga manual en vez de fechas fijas de una
    # corrida anterior.
    _mes_sig_idx = fecha_dt.month + 1 if fecha_dt.month < 12 else 1
    _anio_sig = anio_informe if fecha_dt.month < 12 else anio_informe + 1
    _mes_siguiente = MESES_ES[_mes_sig_idx]
    tabla_eventos_data = [
        [Paragraph("<b>Fecha / Evento Crítico</b>", cell_header_style), Paragraph("<b>Organismo / Emisor</b>", cell_header_style), Paragraph("<b>Impacto Esperado de Mercado & Rollover</b>", cell_header_style)],
        [Paragraph(f"Últimos días hábiles de {mes_nombre} de {anio_informe}: Licitación de Letras y Bonos (fecha exacta: carga manual)", cell_style_left), Paragraph("Secretaría de Finanzas", cell_style_center), Paragraph(f"Rollover de vencimientos en ARS; test de corte de TEM en Lecaps del tramo corto. Monto: {SIN_FUENTE}.", cell_style_left)],
        [Paragraph(f"~11-15 de {_mes_siguiente} de {_anio_sig}: Publicación IPC de {mes_nombre} (fecha exacta: carga manual, cronograma INDEC)", cell_style_left), Paragraph("INDEC / DEIE Mendoza", cell_style_center), Paragraph(f"Confirmación de la variación mensual reportada en este informe ({_fmt1(inflacion.get('indec_general_mom'))}% MoM).", cell_style_left)],
        [Paragraph("Próxima reunión de política monetaria FOMC (fecha exacta: carga manual, calendario de la Reserva Federal)", cell_style_left), Paragraph("Reserva Federal (FED)", cell_style_center), Paragraph(f"Sin conector al calendario de la FED en el repositorio: {SIN_FUENTE}.", cell_style_left)]
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
        [Paragraph(
            f"• <b>Gestión de Liquidez Corporativa (30-60 días):</b> Maximizar colocaciones en Lecaps del tramo corto a TEM {_fmt1(tasas_ars.get('lecap_corta_tem'))}%-"
            f"{_fmt1(tasas_ars.get('lecap_larga_tem'))}% (el contrato no especifica tickers puntuales), complementadas con cauciones bursátiles activas para optimizar "
            f"rendimientos diarios de caja.<br/>• <b>Estrategia Cambiaria y Comercio Exterior (90-180 días):</b> Coberturas selectivas mediante futuros Matba-Rofex solo para "
            f"compromisos rígidos de importación -- sin conector a Matba-Rofex en el repositorio para dimensionar la tasa implícita: {SIN_FUENTE}.<br/>"
            f"• <b>Posicionamiento Soberano en Moneda Extranjera (+12 meses):</b> Sobreponderar bonos globales GD35 y GD38 (TIR real: {_fmt1(soberano.get('gd35_tir'))}% y "
            f"{_fmt1(soberano.get('gd38_tir'))}%), capturando una eventual aceleración en el retorno total ante convergencia del EMBI+ (nivel actual: "
            f"{fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb) -- las paridades de mercado no tienen fuente automatizable: {SIN_FUENTE}.",
            ParagraphStyle('DCB', fontName='Georgia', fontSize=6.8, leading=8.8, textColor=DARK_TEXT))]
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
    print(f"Informe Integral PDF re-built and synchronized: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_informe_mensual_reportlab()
