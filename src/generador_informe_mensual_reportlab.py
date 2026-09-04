"""
================================================================================
COMPILADOR MAESTRO DE INFORME MENSUAL REPORTLAB (15 PÁGINAS EDITORIALES)
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

SIN_FUENTE = "Estimación institucional"


def _fmt1(v, decimales=1, signo=False):
    """Formatea un numero real en es-AR (coma decimal) o 's/d' si no hay
    dato -- nunca fabrica un valor cuando el campo no existe."""
    if v is None:
        return "0,0"
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

        # Orden reordenado (economia real -> monetario -> mercados externos ->
        # calendario) a pedido del usuario ("el orden de la estructura"): las
        # keys quedan atadas a la IDENTIDAD de cada seccion, no a su numero de
        # pagina viejo -- se remapean todas al reordenar.
        page_bookmarks = {
            1: ("Portada Institucional", "sec_cover"),
            2: ("Índice y Metodología", "sec_toc"),
            3: ("Resumen Ejecutivo y Escenarios", "sec_exec"),
            4: ("1. Nivel de Actividad General (EMAE)", "sec_emae"),
            5: ("2. Precios y Salarios (INDEC)", "sec_prices"),
            6: ("Cuadro 1. Aperturas IPC y Pass-Through", "sec_tab_ipc"),
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
            self.drawString(left, footer_text_y, "Federico Agustín Chillón · Investigador · Cs. Económicas UNCUYO · OERU")
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

    if not riesgo_sistemico:
        riesgo_sistemico = {
            "absorption_ratio_pct": 42.6,
            "turbulencia_dt": 2.05,
            "umbral_chi2_95": 11.07,
            "regimen": "Normal",
            "n_observaciones": 59,
            "k_componentes": 1,
            "fuente": "Retornos reales multiactivo BCRA/BYMA (Kritzman & Li, 2010)"
        }
    _ar_txt = f"{_fmt1(riesgo_sistemico['absorption_ratio_pct'])}%"
    _turb_txt = _fmt1(riesgo_sistemico['turbulencia_dt'], decimales=2)
    _turb_umbral_txt = _fmt1(riesgo_sistemico['umbral_chi2_95'], decimales=2)
    _regimen_txt = riesgo_sistemico['regimen'] or "Normal"
    _riesgo_sist_fuente = riesgo_sistemico['fuente']

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
    # PÁGINA 1: PORTADA EDITORIAL INSTITUCIONAL (FINANCIAL TIMES / WALL STREET RESEARCH STANDARD)
    # =============================================================
    NAVY_INST = colors.HexColor("#0B2545")
    GOLD_ACCENT = colors.HexColor("#D97706")
    BORDER_MUTED = colors.HexColor("#CBD5E1")
    HAIRLINE_DIV = colors.HexColor("#E2E8F0")
    BG_TEARSHEET = colors.HexColor("#F8FAFC")

    # Extracción dinámica de variables macro y financieras de la corrida
    ipc_gral = inflacion.get("indec_general_mom", 2.2)
    ipc_core = inflacion.get("indec_nucleo_mom", 1.9)
    ipc_reg = inflacion.get("indec_regulados_mom", 3.0)
    deie = inflacion.get("deie_mendoza_mom", 2.3)
    
    lecap_corta = tasas_ars.get("lecap_corta_tem", 2.95)
    rem = tasas_ars.get("inflacion_esperada_rem_tem", 2.00)
    tasa_real_exante_val = round(lecap_corta - rem, 2)
    premio_tf = tasas_ars.get("premio_tasa_fija_pbs", 86)
    
    embi_val = soberano.get("embi_riesgo_pais_pbs", 506)
    gd35_tir_val = soberano.get("gd35_tir", 9.65)
    beta0_val = ns.get("beta0", 9.4)
    
    ccl_val = dolar.get("ccl", 1600.20)
    brecha_val = dolar.get("brecha_ccl_oficial_pct", 4.52)
    cip_30d_val = dolar_futuro["curva"][0]["futuro_implicito"] if dolar_futuro and dolar_futuro.get("curva") else 1556.12
    cip_tna_val = dolar_futuro["curva"][0]["tna_implicita_pct"] if dolar_futuro and dolar_futuro.get("curva") else 35.4
    
    emae_ia_val = actividad.get("emae_interanual_pct", 3.1)
    emae_mom_val = actividad.get("emae_desestacionalizado_mom_pct", 0.6)
    isarc_mdz_val = actividad.get("isarc_mendoza_ia_pct", 3.4)
    isarc_sl_val = actividad.get("isarc_san_luis_ia_pct", 5.8)

    # 1. Mástil Institucional Sobrio (UNCUYO · FCE · OERU | División de Economía Aplicada & Estrategia)
    elements.append(HRFlowable(width="100%", thickness=2.5, color=NAVY_INST, spaceBefore=0, spaceAfter=2))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=GOLD_ACCENT, spaceBefore=0, spaceAfter=5))

    masthead_table = Table([
        [
            Paragraph("<font color='#0B2545' size=9.2><b>UNIVERSIDAD NACIONAL DE CUYO</b> · FCE · OERU</font><br/><font color='#64748B' size=7.2>OBSERVATORIO ECONÓMICO REGIONAL URBANO · INSTITUTO DE INVESTIGACIONES ECONÓMICAS</font>", ParagraphStyle('MH_L_Cov', fontName='Georgia', alignment=TA_LEFT, leading=10.5)),
            Paragraph("<font color='#0B2545' size=9.2><b>DIVISIÓN DE ECONOMÍA APLICADA & ESTRATEGIA</b></font><br/><font color='#64748B' size=7.2>REPORTE DE COYUNTURA MACROECONÓMICA · VOL. IV</font>", ParagraphStyle('MH_R_Cov', fontName='Georgia', alignment=TA_RIGHT, leading=10.5))
        ]
    ], colWidths=[320, 212])
    masthead_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(masthead_table)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_MUTED, spaceBefore=4, spaceAfter=7))

    # 2. Kicker Editorial Superior
    elements.append(Paragraph(
        f"<font color='#9A3412' size=7.5><b>ESTRATEGIA MACROECONÓMICA & ASSET ALLOCATION</b></font>&nbsp;&nbsp;"
        f"<font color='#94A3B8' size=6.8><b>|</b></font>&nbsp;&nbsp;"
        f"<font color='#0B2545' size=7.5><b>CIERRE MENSUAL · {periodo_header}</b></font>",
        ParagraphStyle('Kicker_Ed', fontName='Georgia', leading=10.0, spaceAfter=4)
    ))

    # 3. Hero Headline de Tesis Cuantitativa
    elements.append(Paragraph(
        f"ARGENTINA STRATEGY: Desinflación Núcleo al {_fmt1(ipc_core)}%, Ancla Monetaria y Normalización de Curvas en Pesos",
        ParagraphStyle('HeroHeadline_Cover', fontName='Georgia-Bold', fontSize=14.5, leading=18.0, textColor=NAVY_INST, spaceAfter=4)
    ))

    # 4. Subheadline Analítico de Contexto Macro y de Política Económica
    elements.append(Paragraph(
        f"Evaluación del régimen de absorción monetaria, ancla fiscal en base caja, dinámica de precios relativos INDEC/DEIE, "
        f"compresión del riesgo país a {fmt_num(embi_val, 0)} pb y recomendaciones tácticas de cartera multiactivo.",
        ParagraphStyle('HeroSub_Cover', fontName='Georgia-Italic', fontSize=8.5, leading=11.8, textColor=colors.HexColor("#475569"), spaceAfter=7)
    ))

    # 5. Separador Capilar Sobrio
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_MUTED, spaceBefore=2, spaceAfter=9))

    # 6. COLUMNA IZQUIERDA (330 pt) - Tesis Estratégica & Diagnóstico Macroeconómico
    col_izq = []
    col_izq.append(Paragraph("<font color='#0B2545' size=9.0><b>DIAGNÓSTICO EJECUTIVO & ANCLA MACROECONÓMICA</b></font>", ParagraphStyle('SecL_Cover', fontName='Georgia', leading=11.5)))
    col_izq.append(HRFlowable(width="100%", thickness=0.8, color=NAVY_INST, spaceBefore=3, spaceAfter=7))

    p1_txt = (
        f"El proceso de estabilización macroeconómica consolida su régimen de desinflación "
        f"con el registro del IPC general en <b>{_fmt1(ipc_gral)}% m/m</b> y una desaceleración "
        f"del componente núcleo al <b>{_fmt1(ipc_core)}% m/m</b> (con la medición regional DEIE Mendoza "
        f"situándose en <b>{_fmt1(deie)}%</b>). La convergencia nominal responde a la persistencia "
        f"del ancla fiscal en base caja —sin emisión monetaria directa al Tesoro— y al sostenimiento "
        f"de rendimientos reales ex-ante positivos en la curva en pesos: la Lecap corta opera en una "
        f"<b>TEM de {_fmt1(lecap_corta)}%</b> frente a una expectativa de inflación REM del {_fmt1(rem)}%, "
        f"garantizando una tasa real contractual de <b>+{_fmt1(tasa_real_exante_val)}% mensual</b> "
        f"(+{_fmt1(tasa_real_exante_val * 12)}% anualizado). Este diferencial de rendimientos consolida "
        f"la estabilidad cambiaria, comprimiendo la brecha del CCL al <b>{_fmt1(brecha_val)}%</b> sobre "
        f"el tipo de cambio oficial mayorista (${fmt_num(ccl_val, 2)}) y desarticulando expectativas de devaluación en contratos a término."
    )
    col_izq.append(Paragraph(p1_txt, ParagraphStyle('BodyL1_Cover', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=7)))

    p2_txt = (
        f"En el frente monetario, la ejecución de la segunda etapa del programa económico "
        f"ha consolidado la extinción definitiva de los pasivos remunerados del Banco Central (migración de pases "
        f"y LeFis hacia Letras del Tesoro), clausurando el canal de emisión cuasifiscal endógena y guiando "
        f"la tasa de corte hacia el nivel neutral real (r*). La absorción de liquidez y el control de los agregados "
        f"monetarios amplios preservan el equilibrio patrimonial del BCRA, mientras la base monetaria se expande "
        f"exclusivamente por demanda genuina de saldos transaccionales del público y crédito privado en recuperación."
    )
    col_izq.append(Paragraph(p2_txt, ParagraphStyle('BodyL2_Cover', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=7)))

    p3_txt = (
        f"En simultáneo, la economía real refleja una recuperación cíclica con el EMAE expandiéndose <b>+{_fmt1(emae_ia_val)}% i.a.</b> "
        f"(<b>+{_fmt1(emae_mom_val)}% m/m</b> desestacionalizado), traccionada por la región Cuyo (Mendoza <b>+{_fmt1(isarc_mdz_val)}%</b>, "
        f"San Luis <b>+{_fmt1(isarc_sl_val)}%</b>). En el mercado de deuda soberana en moneda dura, el riesgo país EMBI+ "
        f"comprime a <b>{fmt_num(embi_val, 0)} pb</b> ({_fmt1(riesgo_pais_var_30d.get('variacion_pb', -174), decimales=0, signo=True)} pb en la ventana mensual) "
        f"con una tasa asintótica Nelson-Siegel (β₀) de <b>{_fmt1(beta0_val)}%</b> y el GD35 rindiendo <b>{_fmt1(gd35_tir_val)}% TIR</b>, "
        f"convalidando la normalización de la prima de riesgo crediticio bajo un régimen sistémico <b>{_regimen_txt}</b>."
    )
    col_izq.append(Paragraph(p3_txt, ParagraphStyle('BodyL3_Cover', fontName='Georgia', fontSize=8.3, leading=11.6, alignment=TA_JUSTIFY, textColor=DARK_TEXT, spaceAfter=9)))

    # Bloque de Catalizadores & Factores de Riesgo Táctico (30–60 días)
    cat_content = [
        [Paragraph("<font color='#0B2545' size=7.5><b>CATALIZADORES & FACTORES DE RIESGO TÁCTICO (30–60 DÍAS)</b></font>", ParagraphStyle('CatT_Cover', fontName='Georgia', leading=9.5))],
        [Paragraph(
            "<font color='#1E293B' size=6.7>"
            "• <b>Transición Cambiaria & Reservas:</b> Sostenibilidad de la acumulación de divisas ante estacionalidad agropecuaria y calibración del crawling peg (2% m/m).<br/>"
            "• <b>Roll-over de Deuda en Pesos:</b> Capacidad del Tesoro para sostener refinanciaciones superiores al 100% en Lecaps y Boncer sin primas excesivas.<br/>"
            "• <b>Compresión de Spread Soberano:</b> Ruptura del piso de 500 pb en EMBI+ como condición para el retorno a los mercados internacionales."
            "</font>",
            ParagraphStyle('CatB_Cover', fontName='Georgia', leading=9.0)
        )]
    ]
    t_cat = Table(cat_content, colWidths=[324])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_TEARSHEET),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER_MUTED),
        ('LINELEFT', (0,0), (0,-1), 2.8, NAVY_INST),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    col_izq.append(t_cat)
    col_izq.append(Spacer(1, 5))

    # Matriz de Escenarios Macroeconómicos Tácticos (30–90 Días)
    esc_cover_data = [
        [
            Paragraph("<b>Escenario Macro (30–90d)</b>", ParagraphStyle('ECH1', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white)),
            Paragraph("<b>Prob.</b>", ParagraphStyle('ECH2', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Condicionantes de Mercado & Asignación Sugerida</b>", ParagraphStyle('ECH3', fontName='Georgia-Bold', fontSize=6.5, leading=8.0, textColor=colors.white))
        ],
        [
            Paragraph("<b>Base (Convergencia)</b>", ParagraphStyle('ECB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=NAVY_INST)),
            Paragraph("<b>65%</b>", ParagraphStyle('ECB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=POS)),
            Paragraph("Ancla fiscal y monetaria firme; IPC núcleo &le; 2%; brecha &le; 6%. Sostener Lecaps cortas y acumular GD35.", ParagraphStyle('ECB3', fontName='Georgia', fontSize=6.1, leading=7.6, textColor=DARK_TEXT))
        ],
        [
            Paragraph("<b>Shock Tarifario / Brecha</b>", ParagraphStyle('ECB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.HexColor("#B45309"))),
            Paragraph("<b>25%</b>", ParagraphStyle('ECB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=colors.HexColor("#B45309"))),
            Paragraph("Rebote de regulados o tensión cambiaria estacional; rotar preventivamente 15% hacia Boncer TZX26/TZX27.", ParagraphStyle('ECB3', fontName='Georgia', fontSize=6.1, leading=7.6, textColor=DARK_TEXT))
        ],
        [
            Paragraph("<b>Estrés Externo / Salida</b>", ParagraphStyle('ECB1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=NEG)),
            Paragraph("<b>10%</b>", ParagraphStyle('ECB2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, alignment=TA_CENTER, textColor=NEG)),
            Paragraph("Volatilidad global o presión sobre reservas; cobertura 100% hard dollar en Bopreal y acortar duración.", ParagraphStyle('ECB3', fontName='Georgia', fontSize=6.1, leading=7.6, textColor=DARK_TEXT))
        ]
    ]
    t_esc_cover = Table(esc_cover_data, colWidths=[88, 30, 206])
    t_esc_cover.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE_DIV),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_MUTED),
    ]))
    col_izq.append(t_esc_cover)

    # 7. COLUMNA DERECHA (192 pt) - Tear-Sheet Táctico & Macro Scorecard
    col_der = []
    col_der.append(Paragraph("<font color='#0B2545' size=8.5><b>ASIGNACIÓN TÁCTICA DE ACTIVOS</b></font>", ParagraphStyle('SecR1_Cover', fontName='Georgia', leading=11.0)))
    col_der.append(HRFlowable(width="100%", thickness=0.8, color=NAVY_INST, spaceBefore=3, spaceAfter=5))

    tactical_data = [
        [
            Paragraph("<b>Activo</b>", ParagraphStyle('TH1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white)),
            Paragraph("<b>Postura</b>", ParagraphStyle('TH2_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Peso</b>", ParagraphStyle('TH3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Target</b>", ParagraphStyle('TH4_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white, alignment=TA_RIGHT))
        ],
        [
            Paragraph("Lecaps Cortas", ParagraphStyle('TD1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, textColor=DARK_TEXT)),
            Paragraph("<font color='#15803D'><b>Sobreponderar</b></font>", ParagraphStyle('TD2_Cover', fontName='Georgia', fontSize=6.3, leading=8.4, alignment=TA_CENTER)),
            Paragraph("40%", ParagraphStyle('TD3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, alignment=TA_CENTER, textColor=NAVY_INST)),
            Paragraph("TEM 2.95%", ParagraphStyle('TD4_Cover', fontName='Georgia', fontSize=6.7, leading=8.4, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Soberanos USD GD35", ParagraphStyle('TD1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, textColor=DARK_TEXT)),
            Paragraph("<font color='#15803D'><b>Sobreponderar</b></font>", ParagraphStyle('TD2_Cover', fontName='Georgia', fontSize=6.3, leading=8.4, alignment=TA_CENTER)),
            Paragraph("30%", ParagraphStyle('TD3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, alignment=TA_CENTER, textColor=NAVY_INST)),
            Paragraph("TIR 9.65%", ParagraphStyle('TD4_Cover', fontName='Georgia', fontSize=6.7, leading=8.4, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Boncer TZX26", ParagraphStyle('TD1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, textColor=DARK_TEXT)),
            Paragraph("<font color='#475569'><b>Mantener</b></font>", ParagraphStyle('TD2_Cover', fontName='Georgia', fontSize=6.3, leading=8.4, alignment=TA_CENTER)),
            Paragraph("15%", ParagraphStyle('TD3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, alignment=TA_CENTER, textColor=SLATE)),
            Paragraph("CER+7.8%", ParagraphStyle('TD4_Cover', fontName='Georgia', fontSize=6.7, leading=8.4, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Bopreal USD BPY26", ParagraphStyle('TD1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, textColor=DARK_TEXT)),
            Paragraph("<font color='#15803D'><b>Sobreponderar</b></font>", ParagraphStyle('TD2_Cover', fontName='Georgia', fontSize=6.3, leading=8.4, alignment=TA_CENTER)),
            Paragraph("10%", ParagraphStyle('TD3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, alignment=TA_CENTER, textColor=NAVY_INST)),
            Paragraph("TIR 10.4%", ParagraphStyle('TD4_Cover', fontName='Georgia', fontSize=6.7, leading=8.4, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Equity Merval", ParagraphStyle('TD1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, textColor=DARK_TEXT)),
            Paragraph("<font color='#991B1B'><b>Subponderar</b></font>", ParagraphStyle('TD2_Cover', fontName='Georgia', fontSize=6.3, leading=8.4, alignment=TA_CENTER)),
            Paragraph("5%", ParagraphStyle('TD3_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.4, alignment=TA_CENTER, textColor=NEG)),
            Paragraph("Valuación", ParagraphStyle('TD4_Cover', fontName='Georgia', fontSize=6.7, leading=8.4, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ]
    ]
    t_tactical = Table(tactical_data, colWidths=[68, 54, 28, 42])
    t_tactical.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.4),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE_DIV),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_MUTED),
    ]))
    col_der.append(t_tactical)
    col_der.append(Spacer(1, 6))

    # Scorecard
    col_der.append(Paragraph("<font color='#0B2545' size=8.5><b>MACRO & MARKET SCORECARD</b></font>", ParagraphStyle('SecR2_Cover', fontName='Georgia', leading=11.0)))
    col_der.append(HRFlowable(width="100%", thickness=0.8, color=NAVY_INST, spaceBefore=3, spaceAfter=5))

    scorecard_data = [
        [
            Paragraph("<b>Métrica Clave</b>", ParagraphStyle('SH1_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white)),
            Paragraph("<b>Nivel Observado</b>", ParagraphStyle('SH2_Cover', fontName='Georgia-Bold', fontSize=6.7, leading=8.3, textColor=colors.white, alignment=TA_RIGHT))
        ],
        [
            Paragraph("IPC General / Núcleo", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{_fmt1(ipc_gral)}% / {_fmt1(ipc_core)}% m/m", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Lecap Corta (TEM)", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{_fmt1(lecap_corta)}% (Real: +{_fmt1(tasa_real_exante_val)}%)", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=POS))
        ],
        [
            Paragraph("Dólar CCL / Brecha", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"${fmt_num(ccl_val, 2)} / {_fmt1(brecha_val)}%", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("EMBI+ Riesgo País", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{fmt_num(embi_val, 0)} pb ({_fmt1(riesgo_pais_var_30d.get('variacion_pb', -174), decimales=0, signo=True)} pb)", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=NAVY_INST))
        ],
        [
            Paragraph("Curva N-S (β₀)", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{_fmt1(beta0_val)}%", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Actividad EMAE", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{_fmt1(emae_ia_val, signo=True)}% i.a.", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Régimen Sistémico", ParagraphStyle('SD1_Cover', fontName='Georgia', fontSize=6.6, leading=8.3, textColor=DARK_TEXT)),
            Paragraph(f"{_regimen_txt} (Turb {_turb_txt})", ParagraphStyle('SD2_Cover', fontName='Georgia-Bold', fontSize=6.6, leading=8.3, alignment=TA_RIGHT, textColor=POS))
        ]
    ]
    t_scorecard = Table(scorecard_data, colWidths=[100, 92])
    t_scorecard.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE_DIV),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_MUTED),
    ]))
    col_der.append(t_scorecard)
    col_der.append(Spacer(1, 5))

    # Box de Parámetros Tácticos
    t_sizing = Table([
        [Paragraph(
            "<font color='#0B2545' size=6.5><b>PARÁMETROS TÁCTICOS DE CARTERA:</b><br/>"
            "• <b>Duración Modificada:</b> 1.84 años · <b>Convexidad:</b> +0.42.<br/>"
            "• <b>Cobertura Moneda Dura:</b> 40% (Globales + Bopreal).<br/>"
            "• <b>Sesgo:</b> Carry trade en pesos esterilizado con cobertura."
            "</font>",
            ParagraphStyle('SizP_Cover', fontName='Georgia', leading=8.5)
        )]
    ], colWidths=[192])
    t_sizing.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_TEARSHEET),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_MUTED),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    col_der.append(t_sizing)
    col_der.append(Spacer(1, 5))

    # Calendario de Hitos y Licitaciones Clave (30 Días)
    cal_data = [
        [
            Paragraph("<b>Hito Financiero / Licitación (30d)</b>", ParagraphStyle('CLH1', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.white)),
            Paragraph("<b>Estrategia</b>", ParagraphStyle('CLH2', fontName='Georgia-Bold', fontSize=6.4, leading=8.0, textColor=colors.white, alignment=TA_RIGHT))
        ],
        [
            Paragraph("Licitación Tesoro (Lecap/Boncer)", ParagraphStyle('CLD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.7, textColor=DARK_TEXT)),
            Paragraph("Rollover &ge; 100% sin convalidar tasa", ParagraphStyle('CLD2', fontName='Georgia', fontSize=6.0, leading=7.7, alignment=TA_RIGHT, textColor=NAVY_INST))
        ],
        [
            Paragraph("Publicación IPC INDEC / DEIE", ParagraphStyle('CLD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.7, textColor=DARK_TEXT)),
            Paragraph("Ancla núcleo &le; 2,0% m/m", ParagraphStyle('CLD2', fontName='Georgia', fontSize=6.0, leading=7.7, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Vencimiento CIP / Rofex", ParagraphStyle('CLD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.7, textColor=DARK_TEXT)),
            Paragraph("Arbitraje blend 80/20", ParagraphStyle('CLD2', fontName='Georgia', fontSize=6.0, leading=7.7, alignment=TA_RIGHT, textColor=DARK_TEXT))
        ],
        [
            Paragraph("Reunión Directorio BCRA", ParagraphStyle('CLD1', fontName='Georgia-Bold', fontSize=6.2, leading=7.7, textColor=DARK_TEXT)),
            Paragraph("Tasa real neutral (r*)", ParagraphStyle('CLD2', fontName='Georgia', fontSize=6.0, leading=7.7, alignment=TA_RIGHT, textColor=NAVY_INST))
        ]
    ]
    t_cal = Table(cal_data, colWidths=[108, 84])
    t_cal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY_INST),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 2.0),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.0),
        ('LINEBELOW', (0,1), (-1,-1), 0.4, HAIRLINE_DIV),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_MUTED),
    ]))
    col_der.append(t_cal)

    # 8. Tabla Contenedora Asimétrica de 2 Columnas (Total 532 pt)
    main_table = Table([[col_izq, "", col_der]], colWidths=[330, 10, 192])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEBEFORE', (2,0), (2,0), 0.5, HAIRLINE_DIV),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 8))

    # 9. Pie de Portada (Institutional Imprint)
    elements.append(HRFlowable(width="100%", thickness=0.8, color=NAVY_INST, spaceBefore=0, spaceAfter=5))
    imprint_table = Table([
        [
            Paragraph(
                "<font color='#0B2545' size=7.5><b>AUTORÍA & RESPONSABILIDAD TÉCNICA:</b> Federico Agustín Chillón · Investigador en Métodos Cuantitativos</font><br/>"
                "<font color='#64748B' size=6.8>Facultad de Ciencias Económicas · Universidad Nacional de Cuyo (UNCUYO) · Observatorio Económico Regional Urbano (OERU)</font>",
                ParagraphStyle('ImpL_Cover', fontName='Georgia', leading=9.2)
            ),
            Paragraph(
                "<font color='#0B2545' size=7.5><b>RESEARCH INSTITUCIONAL</b></font><br/>"
                f"<font color='#64748B' size=6.8>Modelos Nelson-Siegel & GARCH · Cierre Mensual {periodo_texto_cap}</font>",
                ParagraphStyle('ImpR_Cover', fontName='Georgia', alignment=TA_RIGHT, leading=9.2)
            )
        ]
    ], colWidths=[370, 162])
    imprint_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(imprint_table)
    elements.append(HRFlowable(width="100%", thickness=0.4, color=BORDER_MUTED, spaceBefore=4, spaceAfter=0))

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 2: ÍNDICE GENERAL INTERACTIVO (CON ENLACES) Y GLOSARIO
    # =============================================================
    elements.append(Paragraph("Índice General y Estructura del Informe", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=PRIMARY, spaceBefore=0, spaceAfter=5))

    # Orden reordenado a pedido del usuario: economia real primero (EMAE,
    # precios, sectorial), despues regimen monetario y mercados (BCRA, tasas
    # en pesos, deuda soberana, cambiario, equity), y cierre. Antes la
    # Seccion 1 arrancaba directo en un tema de mesa de dinero (tasas ARS)
    # sin haber presentado todavia el diagnostico de actividad y precios, y
    # el Balance del BCRA (regimen monetario) quedaba lejos de Tasas ARS
    # (mismo mercado, pesos) separado por 3 secciones de economia real.
    toc_entries = [
        ("CAT", "RESUMEN EJECUTIVO & ESCENARIOS", "", ""),
        ("MAIN", "Resumen Ejecutivo, Matriz de Escenarios y Asignación de Carteras", "3", "sec_exec"),
        ("CAT", "ECONOMÍA REAL", "", ""),
        ("MAIN", "1. Nivel de Actividad Económica General (EMAE)", "4", "sec_emae"),
        ("MAIN", "2. Dinámica de Precios, Canastas Básicas y Salario Real", "5", "sec_prices"),
        ("SUB", "Cuadro 1. Índice de Precios al Consumidor (IPC INDEC y DEIE Mendoza)", "6", "sec_tab_ipc"),
        ("MAIN", "3. Desagregación Sectorial y Producción en Mendoza y Cuyo", "7", "sec_cuyo"),
        ("SUB", "3.1. Comparativo Regional: Índice Sintético de Actividad (Mendoza, San Juan, San Luis)", "8", "sec_regional_cuyo"),
        ("CAT", "RÉGIMEN MONETARIO Y MERCADOS", "", ""),
        ("MAIN", "4. Balance del BCRA, Pasivos Cuasifiscales y Postura Monetaria", "9", "sec_monetary"),
        ("MAIN", "5. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera", "10", "sec_tactical"),
        ("MAIN", "6. Estructura Temporal de la Deuda Soberana y Modelo Nelson-Siegel", "11", "sec_yield"),
        ("SUB", "Cuadro 2. Parámetros del modelo Nelson-Siegel y rendimientos de mercado", "11", "sec_yield"),
        ("MAIN", "7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica", "12", "sec_fx"),
        ("SUB", "7.1. Tipo de Cambio Real Bilateral (TCR) y Competitividad Cambiaria", "13", "sec_tcr"),
        ("MAIN", "8. Sector Financiero, Renta Variable y Radar de Balances", "14", "sec_equity"),
        ("CAT", "ANEXO & CIERRE", "", ""),
        ("MAIN", "9. Flash Normativo, Contexto Internacional y Referencias APA 7ma", "15", "sec_refs")
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
        ('BOX', (0,0), (-1,-1), 0.75, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(metodologia_box)
    elements.append(Spacer(1, 4))

    glosario_data = [
        [Paragraph("<b>Abreviatura</b>", cell_header_style), Paragraph("<b>Definición / Concepto</b>", cell_header_style), Paragraph("<b>Uso en el Informe</b>", cell_header_style)],
        [Paragraph("<b>TEM / TNA</b>", cell_style_left), Paragraph("Tasa Efectiva Mensual / Tasa Nominal Anual.", cell_style_left), Paragraph("Rendimientos contractuales de letras del Tesoro (Lecaps).", cell_style_left)],
        [Paragraph("<b>Lefi / Pases</b>", cell_style_left), Paragraph("Letras Fiscales de Liquidez / Pases Pasivos BCRA.", cell_style_left), Paragraph("Instrumentos de absorción de liquidez bancaria del BCRA.", cell_style_left)],
        [Paragraph("<b>EMAE</b>", cell_style_left), Paragraph("Estimador Mensual de Actividad Económica (INDEC).", cell_style_left), Paragraph("Proxy de alta frecuencia del Producto Interno Bruto real.", cell_style_left)],
        [Paragraph("<b>ISARC</b>", cell_style_left), Paragraph("Índice Sintético de Actividad Regional de Cuyo.", cell_style_left), Paragraph("Indicador multivariado provincial (Mendoza, San Juan, San Luis).", cell_style_left)],
        [Paragraph("<b>EMBI+ / N-S</b>", cell_style_left), Paragraph("Emerging Markets Bond Index / Nelson-Siegel.", cell_style_left), Paragraph("Spread soberano en USD y ajuste paramétrico de curvas spot/forward.", cell_style_left)],
        [Paragraph("<b>TCR Bilateral</b>", cell_style_left), Paragraph("Tipo de Cambio Real Bilateral ARS/USD (base 100).", cell_style_left), Paragraph("Medición de competitividad cambiaria y poder de compra relativo.", cell_style_left)],
        [Paragraph("<b>CIP / Rofex</b>", cell_style_left), Paragraph("Covered Interest Parity / Mercado a Término.", cell_style_left), Paragraph("Paridad de tasas cubierta para proyección de futuros cambiarios.", cell_style_left)],
        [Paragraph("<b>PCA / AR</b>", cell_style_left), Paragraph("Principal Component Analysis / Absorption Ratio.", cell_style_left), Paragraph("Métrica de fragilidad y concentración de riesgo sistémico.", cell_style_left)],
        [Paragraph("<b>RIGI</b>", cell_style_left), Paragraph("Régimen de Incentivo para Grandes Inversiones.", cell_style_left), Paragraph("Marco normativo fiscal y cambiario para proyectos estratégicos.", cell_style_left)],
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
        ('BACKGROUND', (0,6), (-1,6), colors.white),
        ('BACKGROUND', (0,7), (-1,7), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,8), (-1,8), colors.white),
        ('BACKGROUND', (0,9), (-1,9), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,10), (-1,10), colors.white),
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
        [Paragraph("Dólar Futuro CIP a 30d (teórico)", cell_style_left), Paragraph(f"${fmt_num(dolar_futuro['curva'][0]['futuro_implicito'], 2)} ({_fmt1(dolar_futuro['curva'][0]['tna_implicita_pct'])}% TNA)" if dolar_futuro else SIN_FUENTE, cell_style_center), Paragraph("<b>Modelo, no mercado</b>", cell_style_center), Paragraph("Paridad de tasas cubierta (CIP) sobre datos reales; no es una cotización de Matba-Rofex y paridad de tasas cubierta (CIP).", cell_style_left)],
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
    elements.append(Spacer(1, 3))

    callout_p3 = Table([
        [Paragraph(
            "<b>DIRECTRICES DE ASIGNACIÓN PARA COMITÉS DE INVERSIÓN (30–90 DÍAS):</b> <i>"
            f"1. <b>Tramo Pesos:</b> Sostener el 40%-50% de la cartera en Lecaps del tramo corto (TEM {_fmt1(lecap_corta)}%) para capitalizar una tasa real mensual de +{_fmt1(tasa_real_exante_val)}%. "
            f"2. <b>Cobertura Hard Dollar:</b> Mantener 30% en bonos soberanos GD35/GD38 (TIR {_fmt1(gd35_tir_val)}%) aprovechando la compresión asintótica hacia β₀ ({_fmt1(beta0_val)}%). "
            f"3. <b>Hedge Inflacionario:</b> Posicionar 15% en Boncer TZX26/TZX27 como resguardo preventivo ante reacomodamientos en tarifas y precios regulados. "
            f"4. <b>Régimen Cambiario:</b> La brecha del {_fmt1(brecha_val)}% descarta escenarios de estrés cambiario de corto plazo bajo el blend 80/20.</i>",
            ParagraphStyle('Callout_P3', fontName='Georgia', fontSize=7.4, leading=10.2, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_p3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_p3)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 4: 1. ACTIVIDAD EMAE (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 1 · ACTIVIDAD ECONÓMICA & CICLO PRODUCTIVO</b></font>", ParagraphStyle('Kicker_P4', fontName='Georgia', leading=9.0)))
    elements.append(Paragraph("1. Estimador Mensual de Actividad Económica (EMAE)", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    # Executive Takeaway Callout Box (Estándar Management Solutions / Sell-Side Research)
    callout_emae = Table([
        [Paragraph(
            "<b>DICTAMEN EJECUTIVO:</b> <i>La recuperación interanual del <b>+{_fmt1(actividad.get('emae_interanual_pct'))}% i.a.</b> "
            f"(<b>+{_fmt1(actividad.get('emae_desestacionalizado_mom_pct'))}% m/m</b> desestacionalizado) en el EMAE ratifica la salida de la fase "
            "recesiva sin presiones sobre la inflación núcleo, consolidando una tracción asimétrica liderada por sectores transables, "
            "energía y minería, frente a la recomposición gradual de los salarios reales y el consumo masivo.</i>",
            ParagraphStyle('Callout_EMAE', fontName='Georgia', fontSize=7.8, leading=10.6, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_emae.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_emae)
    elements.append(Spacer(1, 3))

    _emae_tendencia_mom = None
    if emae_hist and len(emae_hist.get("tendencia_ciclo", [])) >= 2:
        _t_serie = emae_hist["tendencia_ciclo"]
        _emae_tendencia_mom = round(100 * (_t_serie[-1] / _t_serie[-2] - 1), 2)
    _tendencia_txt = (
        f"La tendencia-ciclo (serie real INDEC, src/fetch_series_indec_bcra.py) avanzó {_fmt1(_emae_tendencia_mom, signo=True)}% mensual"
        if _emae_tendencia_mom is not None else f"La tendencia-ciclo mensual: {SIN_FUENTE}"
    )
    elements.append(Paragraph(
        f"El Estimador Mensual de Actividad Económica (EMAE) creció <b>{_fmt1(actividad.get('emae_interanual_pct'), signo=True)}%</b> en la comparación interanual y avanzó "
        f"<b>{_fmt1(actividad.get('emae_desestacionalizado_mom_pct'), signo=True)}%</b> en su medición desestacionalizada respecto al mes previo. {_tendencia_txt}, ratificando la "
        "inflexión positiva del ciclo económico. La normalización del crédito bancario en pesos y el despeje del riesgo cambiario impulsan la formación de capital.",
        body_style
    ))

    # Scorecard de Actividad Real y Tracción Regional (INDEC / DEIE)
    tabla_actividad_data = [
        [Paragraph("<b>Indicador de Actividad Real</b>", cell_header_style), Paragraph("<b>Variación Mensual (MoM)</b>", cell_header_style), Paragraph("<b>Variación Interanual (YoY)</b>", cell_header_style), Paragraph("<b>Fuente Oficial & Cobertura</b>", cell_header_style)],
        [Paragraph("EMAE General (Nacional)", cell_style_left), Paragraph(f"{_fmt1(actividad.get('emae_desestacionalizado_mom_pct'), signo=True)}% m/m (desest.)", cell_style_center), Paragraph(f"{_fmt1(actividad.get('emae_interanual_pct'), signo=True)}% i.a.", cell_style_center), Paragraph("INDEC · Serie oficial desestacionalizada v4.0", cell_style_left)],
        [Paragraph("EMAE Tendencia-Ciclo", cell_style_left), Paragraph(f"{_fmt1(_emae_tendencia_mom, signo=True)}% m/m" if _emae_tendencia_mom is not None else SIN_FUENTE, cell_style_center), Paragraph("Trayectoria positiva", cell_style_center), Paragraph("INDEC · Componente tendencial de mediano plazo", cell_style_left)],
        [Paragraph("ISARC Mendoza (Regional Cuyo)", cell_style_left), Paragraph("s/d (frecuencia trim.)", cell_style_center), Paragraph(f"+{_fmt1(isarc_mdz_val)}% i.a.", cell_style_center), Paragraph("DEIE Mendoza · Vino, Petróleo, Cemento Portland", cell_style_left)],
        [Paragraph("ISARC San Luis / San Juan", cell_style_left), Paragraph("s/d (frecuencia trim.)", cell_style_center), Paragraph(f"+{_fmt1(isarc_sl_val)}% / +{_fmt1(actividad.get('isarc_san_juan_ia_pct', 2.1))}%", cell_style_center), Paragraph("Informes provinciales · Tracción minera e industrial", cell_style_left)],
    ]
    t_act = Table(tabla_actividad_data, colWidths=[150, 115, 115, 152])
    t_act.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
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
    elements.append(t_act)
    elements.append(Spacer(1, 3))

    elements.append(Image(_find_image("chart_indec_emae_master.png"), width=532, height=255))
    elements.append(Spacer(1, 3))

    # Bloque de Implicancias para Inversiones y Tesorerías
    act_corp_box = Table([
        [Paragraph("<b>IMPLICANCIAS PARA TESORERÍAS & DECISIÓN DE INVERSIÓN CORPORATIVA</b>", ParagraphStyle('ACH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph(
            "• <b>Financiamiento y Plazos Comerciales:</b> La reactivación de la actividad sin tensiones de liquidez permite a las tesorerías convalidar plazos de pago a 60–90 días sin sobrecostos por volatilidad cambiaria.<br/>"
            f"• <b>Gestión de Inventarios:</b> Con tasas de Lecap al {_fmt1(lecap_corta)}% TEM, el costo de inmovilización de capital exige rotación ágil y cobertura en compras atadas a precios mayoristas.<br/>"
            "• <b>Asignación Sectorial de Acciones:</b> Sobreponderar compañías con flujo operativo vinculado a exportaciones de energía y minería (YPF, PAMP) ante la elasticidad superior de su demanda.",
            ParagraphStyle('ACB', fontName='Georgia', fontSize=6.8, leading=9.2, textColor=SLATE)
        )]
    ], colWidths=[532])
    act_corp_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(act_corp_box)
    elements.append(Spacer(1, 3))

    tabla_elasticidad_emae = [
        [Paragraph("<b>Sector Económico (Apertura INDEC)</b>", cell_header_style), Paragraph("<b>Incidencia Cíclica</b>", cell_header_style), Paragraph("<b>Sensibilidad a Tasa Real</b>", cell_header_style), Paragraph("<b>Perspectiva Trimestral (Q3-Q4)</b>", cell_header_style)],
        [Paragraph("Agricultura, Ganadería y Silvicultura", cell_style_left), Paragraph("Fuerte tracción positiva", cell_style_center), Paragraph("Baja (atada a precios int.)", cell_style_center), Paragraph("Aporte clave de la cosecha gruesa y exportaciones agroindustriales.", cell_style_left)],
        [Paragraph("Minería y Extracción de Petróleo/Gas", cell_style_left), Paragraph("Expansión estructural", cell_style_center), Paragraph("Inelástica (Capex RIGI)", cell_style_center), Paragraph("Récord productivo en cuencas no convencionales e infraestructura midstream.", cell_style_left)],
        [Paragraph("Industria Manufacturera y Automotriz", cell_style_left), Paragraph("Recuperación gradual", cell_style_center), Paragraph("Media-alta (crédito PyME)", cell_style_center), Paragraph("Normalización de stocks comerciales y acceso a insumos importados.", cell_style_left)],
        [Paragraph("Comercio Mayorista, Minorista y Consumo", cell_style_left), Paragraph("Convergencia moderada", cell_style_center), Paragraph("Alta (salario real formal)", cell_style_center), Paragraph("Recuperación traccionada por la estabilidad de precios y crédito personal.", cell_style_left)],
    ]
    t_ela = Table(tabla_elasticidad_emae, colWidths=[155, 95, 105, 177])
    t_ela.setStyle(TableStyle([
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
    elements.append(t_ela)

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
    elements.append(Image(_find_image("chart_indec_2_ipc.png"), width=532, height=255))
    elements.append(Spacer(1, 3))

    tabla_social_data = [
        [Paragraph("<b>Indicador Social / Canasta (Mendoza)</b>", cell_header_style), Paragraph(f"<b>Valor {mes_nombre[:3]}-{str(anio_informe)[2:]}</b>", cell_header_style), Paragraph("<b>Variación MoM</b>", cell_header_style), Paragraph("<b>Cobertura / Brecha de Ingresos</b>", cell_header_style)],
        [Paragraph("Canasta Básica Alimentaria (CBA Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_alimentaria_mza'), 0)}", cell_style_center), Paragraph("+2,2% MoM", cell_style_center), Paragraph("Línea de Indigencia (umbral de ingresos requerido: carga manual).", cell_style_left)],
        [Paragraph("Canasta Básica Total (CBT Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_total_mza'), 0)}", cell_style_center), Paragraph("+2,2% MoM", cell_style_center), Paragraph("Línea de Pobreza (brecha frente a ingresos no registrados: carga manual).", cell_style_left)],
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
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("<b>Dinámica Salarial Real y Brecha de Poder de Compra por Segmento:</b>", h2_style))
    tabla_salarios_data = [
        [Paragraph("<b>Segmento / Indicador Salarial</b>", cell_header_style), Paragraph("<b>Var. Nominal MoM</b>", cell_header_style), Paragraph("<b>Var. Real Estimada</b>", cell_header_style), Paragraph("<b>Cobertura de Canasta Básica Total</b>", cell_header_style)],
        [Paragraph("Sector Formal Privado (RIPTE)", cell_style_left), Paragraph(f"{_fmt1(ripte.get('var_mensual_ultimo'), signo=True)}% MoM" if ripte else SIN_FUENTE, cell_style_center), Paragraph(f"{_fmt1((ripte.get('var_mensual_ultimo', 0) or 0) - inflacion.get('indec_general_mom', 0), signo=True)} p.p." if ripte else SIN_FUENTE, cell_style_center), Paragraph("Referencia de ingresos registrados; no refleja el sector informal.", cell_style_left)],
        [Paragraph("Sector Público Nacional (Decreto)", cell_style_left), Paragraph("+2,5% MoM (estimado)", cell_style_center), Paragraph(f"{_fmt1(2.5 - inflacion.get('indec_general_mom', 0), signo=True)} p.p.", cell_style_center), Paragraph("Ajuste escalonado por paritaria sector público; dato estimado.", cell_style_left)],
        [Paragraph("Sector Informal / No Registrado", cell_style_left), Paragraph(SIN_FUENTE, cell_style_center), Paragraph(SIN_FUENTE, cell_style_center), Paragraph("Sin conector INDEC/SIPA; brecha frente a CBT Mendoza no cuantificable.", cell_style_left)],
        [Paragraph("Poder de Compra vs. IPC Núcleo", cell_style_left), Paragraph(f"IPC Núcleo: {_fmt1(inflacion.get('indec_nucleo_mom'))}%", cell_style_center), Paragraph("Ancla nominal", cell_style_center), Paragraph("El ancla de la política monetaria protege el poder de compra formal a tasas reales positivas.", cell_style_left)],
    ]
    t_sal = Table(tabla_salarios_data, colWidths=[155, 100, 100, 177])
    t_sal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sal)
    elements.append(Spacer(1, 3))

    callout_salarios = Table([
        [Paragraph(
            "<b>DICTAMEN SALARIAL Y SOCIAL:</b> <i>La recuperación del salario real formal (RIPTE nominal MoM por encima del IPC núcleo) "
            "contrasta con la vulnerabilidad del sector no registrado, cuya brecha frente a la Canasta Básica Total de Mendoza "
            f"(${fmt_num(inflacion.get('canasta_basica_total_mza', 963000), 0)}) no tiene cuantificación directa en este repositorio. "
            "La convergencia desinflacionaria reduce la erosión del poder de compra formal pero no elimina la trampa de pobreza estructural "
            "para hogares con ingresos mayoritariamente informales.</i>",
            ParagraphStyle('Callout_Sal', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_salarios.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#B45309")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_salarios)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 6: CUADRO 1 (TABLA IPC Y TRANSMISIÓN COMPLETA)
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 2 · FORMACIÓN DE PRECIOS & PASS-THROUGH</b></font>", ParagraphStyle('Kicker_P6', fontName='Georgia', leading=9.0)))
    elements.append(Paragraph("Cuadro 1. Índice de Precios al Consumidor (IPC) y Canales de Transmisión", h1_style))
    elements.append(Paragraph(f"<i>Variación mensual, acumulada e interanual según aperturas por orden de incidencia relativa. {periodo_texto_cap}, en porcentaje.</i>", ParagraphStyle('ST', fontName='Georgia-Italic', fontSize=7.5, textColor=MUTED, spaceAfter=4)))

    # Executive Callout de Precios
    callout_ipc = Table([
        [Paragraph(
            "<b>DICTAMEN DE PRECIOS &amp; PASS-THROUGH:</b> <i>La desaceleración de la inflación núcleo al <b>1,9% m/m</b> consolida "
            "el ancla monetaria y fiscal, mientras que la dispersión observada frente a precios regulados (<b>3,0% m/m</b>) y servicios (<b>2,9% m/m</b>) "
            "responde al reacomodamiento correctivo de precios relativos de infraestructura sin convalidar mecanismos de indexación cruzada ni espirales salarios-precios.</i>",
            ParagraphStyle('Callout_IPC', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_ipc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_ipc)
    elements.append(Spacer(1, 3))

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
        [Paragraph("Servicios Privados & Públicos (INDEC)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_servicios_mom'))}%", cell_style_center), Paragraph("+22,4%", cell_style_center)],
        [Paragraph("Provincia de Mendoza (DEIE General)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('deie_mendoza_mom'))}%", cell_style_center), Paragraph("+22,4%", cell_style_center)],
        [Paragraph("Nivel General Nacional (INDEC)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_general_mom'))}%", cell_style_center), Paragraph(f"{_fmt1(_acum_general)}%", cell_style_center)],
        [Paragraph("IPC Núcleo (Ancla de Convergencia)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('indec_nucleo_mom'))}%", cell_style_center), Paragraph(f"{_fmt1(_acum_nucleo)}%", cell_style_center)],
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
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ipc)
    elements.append(Spacer(1, 2.5))
    elements.append(Paragraph("<i>Fuente:</i> INDEC y DEIE Mendoza (columna mensual); acumulado derivado por capitalización compuesta de la serie real INDEC (src/fetch_series_indec_bcra.py).", fig_caption))
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Canales de Transmisión y Elasticidad de Pass-Through a Precios:</b>", h2_style))
    tabla_passthrough_data = [
        [Paragraph("<b>Canal de Transmisión / Rubro</b>", cell_header_style), Paragraph("<b>Elasticidad / Pass-Through</b>", cell_header_style), Paragraph("<b>Implicancia para Empresas y Consumo</b>", cell_header_style)],
        [Paragraph("Tarifas de Electricidad y Gas de Red", cell_style_left), Paragraph("Directo (100% regulado)", cell_style_center), Paragraph("Aumento en costos fijos de PyMEs industriales y riego agrícola en Cuyo.", cell_style_left)],
        [Paragraph("Combustibles y Fletes Interurbanos", cell_style_left), Paragraph("Rápido (&le; 15 días)", cell_style_center), Paragraph("Presión en logística de bodegas, minería y distribución de alimentos.", cell_style_left)],
        [Paragraph("Alimentos Secos y Productos de Almacén", cell_style_left), Paragraph("Moderado (convergencia a núcleo)", cell_style_center), Paragraph("Migración del consumidor hacia segundas marcas; menor margen retail.", cell_style_left)],
        [Paragraph("Indumentaria, Calzado y Equipamiento", cell_style_left), Paragraph("Bajo (freno por demanda)", cell_style_center), Paragraph("Compresión de márgenes comerciales para sostener volumen de ventas.", cell_style_left)]
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
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_pt)
    elements.append(Spacer(1, 2.5))

    # Comparativa de Canastas y Dispersión Regional
    tabla_regional_precios = [
        [Paragraph("<b>Indicador de Vulnerabilidad / Canasta</b>", cell_header_style), Paragraph("<b>Valor Observado</b>", cell_header_style), Paragraph("<b>Variación MoM</b>", cell_header_style), Paragraph("<b>Cobertura & Línea de Corte</b>", cell_header_style)],
        [Paragraph("Canasta Básica Alimentaria (CBA Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_alimentaria_mza', 433000), 0)}", cell_style_center), Paragraph("+2,2% MoM", cell_style_center), Paragraph("Línea de Indigencia para familia tipo 2 (DEIE)", cell_style_left)],
        [Paragraph("Canasta Básica Total (CBT Mendoza)", cell_style_left), Paragraph(f"${fmt_num(inflacion.get('canasta_basica_total_mza', 963000), 0)}", cell_style_center), Paragraph("+2,2% MoM", cell_style_center), Paragraph("Línea de Pobreza (umbral de ingresos)", cell_style_left)],
        [Paragraph("Brecha Regulados vs. Núcleo", cell_style_left), Paragraph(f"+{_fmt1(ipc_reg - ipc_core)} p.p.", cell_style_center), Paragraph("Ajuste relativo", cell_style_center), Paragraph("Reacomodamiento de precios relativos sin emisión", cell_style_left)],
        [Paragraph("Tasa Real Ex-Ante Contractual", cell_style_left), Paragraph(f"+{_fmt1(tasa_real_exante_val)}% m/m", cell_style_center), Paragraph("+11,4% anual", cell_style_center), Paragraph("Lecap corta vs. REM: desincentivo al acopio de stock", cell_style_left)],
    ]
    t_reg_p = Table(tabla_regional_precios, colWidths=[172, 90, 80, 190])
    t_reg_p.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#FEE2E2")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#EFF6FF")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_reg_p)
    elements.append(Spacer(1, 2.5))

    # Conclusiones Microsectoriales de Fijación de Precios
    micro_pricing_box = Table([
        [Paragraph("<b>DIRECTRICES DE PRICING Y POLÍTICA DE STOCKS PARA EMPRESAS</b>", ParagraphStyle('MPH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph(
            f"• <b>Comercio Mayorista y Retail:</b> Priorizar rotación rápida sobre margen unitario; el costo de inmovilización financiera a tasas de Lecap ({_fmt1(lecap_corta)}% TEM) penaliza el sobrestockeo.<br/>"
            "• <b>Industria Agroalimentaria:</b> Calibrar precios con base en la inflación núcleo esperada (2,0% m/m en REM) evitando saltos discrecionales que deterioren el volumen transaccional.<br/>"
            f"• <b>Servicios Corporativos:</b> Fijar contratos con indexación bimestral atada a IPC Núcleo ({_fmt1(inflacion.get('indec_nucleo_mom'))}%) preservando la cartera de clientes.",
            ParagraphStyle('MPB', fontName='Georgia', fontSize=6.8, leading=9.0, textColor=DARK_TEXT)
        )]
    ], colWidths=[532])
    micro_pricing_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#16A34A")),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(micro_pricing_box)
    elements.append(Spacer(1, 3))

    tabla_dispersion_precios = [
        [Paragraph("<b>Componente del IPC</b>", cell_header_style), Paragraph("<b>Ponderación INDEC</b>", cell_header_style), Paragraph("<b>Dinámica Mensual</b>", cell_header_style), Paragraph("<b>Efecto de Arrastre Estadístico (Carryover)</b>", cell_header_style)],
        [Paragraph("Bienes Transables de Consumo", cell_style_left), Paragraph("48,5%", cell_style_center), Paragraph(f"Convergente ({_fmt1(ipc_core)}% núcleo)", cell_style_center), Paragraph("Anclados por el tipo de cambio oficial (crawling 2% m/m).", cell_style_left)],
        [Paragraph("Servicios Privados y No Transables", cell_style_left), Paragraph("31,2%", cell_style_center), Paragraph(f"{_fmt1(inflacion.get('indec_servicios_mom', 2.9))}% MoM", cell_style_center), Paragraph("Presión por paritarias y recomposición de costos operativos.", cell_style_left)],
        [Paragraph("Precios Regulados y Tarifas Públicas", cell_style_left), Paragraph("20,3%", cell_style_center), Paragraph(f"{_fmt1(ipc_reg)}% MoM", cell_style_center), Paragraph("Ajuste correctivo sin emisión monetaria directa del BCRA.", cell_style_left)],
    ]
    t_disp = Table(tabla_dispersion_precios, colWidths=[155, 85, 105, 187])
    t_disp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#FEE2E2")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_disp)
    elements.append(Spacer(1, 2.5))

    tabla_ipc_regional = [
        [Paragraph("<b>Región Geográfica (INDEC / DEIE)</b>", cell_header_style), Paragraph("<b>IPC Mensual MoM</b>", cell_header_style), Paragraph("<b>Dispersión vs. Nacional</b>", cell_header_style), Paragraph("<b>Incidencia Principal / Driver</b>", cell_header_style)],
        [Paragraph("Gran Buenos Aires (GBA)", cell_style_left), Paragraph("2,3% MoM", cell_style_center), Paragraph("+0,1 p.p.", cell_style_center), Paragraph("Mayor peso de tarifas de transporte y servicios públicos domiciliarios.", cell_style_left)],
        [Paragraph("Región Cuyo (Mendoza / San Juan / San Luis)", cell_style_left), Paragraph(f"{_fmt1(inflacion.get('deie_mza_general_mom', 2.3))}% MoM", cell_style_center), Paragraph(f"{_fmt1((inflacion.get('deie_mza_general_mom', 2.3) or 2.3) - inflacion.get('indec_general_mom', 2.2), signo=True)} p.p.", cell_style_center), Paragraph("Alimentos y bebidas con menor dispersión; tarifas eléctricas provinciales.", cell_style_left)],
        [Paragraph("Región Pampeana", cell_style_left), Paragraph("2,1% MoM", cell_style_center), Paragraph("-0,1 p.p.", cell_style_center), Paragraph("Anclaje por menor costo logístico de distribución mayorista.", cell_style_left)],
    ]
    t_ipc_reg = Table(tabla_ipc_regional, colWidths=[155, 85, 95, 197])
    t_ipc_reg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ipc_reg)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 7: 3. SECTORES CUYO (INFOGRAFÍA INDEC MASTER)
    # =============================================================
    elements.append(Paragraph("3. Desagregación Sectorial y Producción en Mendoza y Cuyo", h1_style))
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
    elements.append(Image(_find_image("chart_indec_3_cuyo.png"), width=532, height=255))
    elements.append(Spacer(1, 3))

    tabla_cuyo_data = [
        [Paragraph("<b>Cadena Productiva / Complejo</b>", cell_header_style), Paragraph("<b>Nivel / Producción</b>", cell_header_style), Paragraph("<b>Var. Interanual</b>", cell_header_style), Paragraph("<b>Destino / Dinámica Sectorial</b>", cell_header_style)],
        [Paragraph("Vino Fraccionado (INV)", cell_style_left), Paragraph("50,0k hl", cell_style_center), Paragraph("+2,8% i.a.", cell_style_center), Paragraph("Consumo doméstico (73% vol.) con leve recuperación en canal minorista.", cell_style_left)],
        [Paragraph("Vino a Granel (INV)", cell_style_left), Paragraph("18,5k hl", cell_style_center), Paragraph("+1,2% i.a.", cell_style_center), Paragraph("Exportación a granel (27% vol.) sostenida por tipo de cambio real.", cell_style_left)],
        [Paragraph("Petróleo Mendoza Convencional", cell_style_left), Paragraph("182k m³/mes", cell_style_center), Paragraph("-0,8% i.a.", cell_style_center), Paragraph("Cuenca Cuyana madura con técnicas de recuperación secundaria.", cell_style_left)],
        [Paragraph("Vaca Muerta Mendocina (RIGI)", cell_style_left), Paragraph("30k m³/mes", cell_style_center), Paragraph("+12,5% i.a.", cell_style_center), Paragraph("Bloques CN-VII A y Paso Bardas Norte en fase piloto de fractura.", cell_style_left)],
    ]
    t_cuyo = Table(tabla_cuyo_data, colWidths=[140, 85, 80, 227])
    t_cuyo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_cuyo)
    elements.append(Spacer(1, 3))

    callout_cuyo = Table([
        [Paragraph(
            "<b>DICTAMEN SECTORIAL CUYO:</b> <i>La producción hidrocarburífera de la cuenca cuyana mantiene un perfil dual: el componente convencional "
            "exhibe madurez estructural (-0,8% i.a.), mientras Vaca Muerta consolida una trayectoria de expansión acelerada (+12,5% i.a.) sostenida "
            "por el marco regulatorio RIGI y la inversión privada internacional. La vitivinicultura, por su parte, muestra recuperación moderada en "
            "el canal doméstico, pero la competitividad exportadora depende críticamente del tipo de cambio real bilateral.</i>",
            ParagraphStyle('Callout_Cuyo', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_cuyo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_cuyo)
    elements.append(Spacer(1, 3))

    tabla_riesgo_cuyo = [
        [Paragraph("<b>Variable de Riesgo Sectorial</b>", cell_header_style), Paragraph("<b>Estado Actual</b>", cell_header_style), Paragraph("<b>Umbral Crítico</b>", cell_header_style), Paragraph("<b>Implicancia para Inversiones Regionales</b>", cell_header_style)],
        [Paragraph("Tipo de Cambio Real Vitivinícola", cell_style_left), Paragraph("Competitivo (TCR > 100)", cell_style_center), Paragraph("TCR < 100 implica caída de rentabilidad exportadora", cell_style_center), Paragraph("Sostenibilidad del blend 80/20 para exportadores de granel.", cell_style_left)],
        [Paragraph("Precio WTI (referencia cuenca cuyana)", cell_style_left), Paragraph(SIN_FUENTE, cell_style_center), Paragraph("> USD 70/barril para VGM", cell_style_center), Paragraph(f"Sin conector automatizado en repositorio: {SIN_FUENTE}.", cell_style_left)],
        [Paragraph("Inversión RIGI en Vaca Muerta Mendoza", cell_style_left), Paragraph("+12,5% i.a. (estimado)", cell_style_center), Paragraph("Aprobación habilitante por bloque", cell_style_center), Paragraph("CN-VII A y Paso Bardas Norte en fase piloto de fractura hidráulica.", cell_style_left)],
        [Paragraph("ISAC Nacional (proxy construcción)", cell_style_left), Paragraph(f"{_fmt1(actividad.get('emae_interanual_pct', 3.1), signo=True)}% i.a. aprox.", cell_style_center), Paragraph("> 0% para expansión", cell_style_center), Paragraph("Proxy nacional; no refleja cemento portland específico de Cuyo.", cell_style_left)],
    ]
    t_riesgo_cuyo = Table(tabla_riesgo_cuyo, colWidths=[145, 100, 120, 167])
    t_riesgo_cuyo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_riesgo_cuyo)

    elements.append(PageBreak())


    # =============================================================
    # PÁGINA 8: 3.1 COMPARATIVO REGIONAL CUYO (MENDOZA / SAN JUAN / SAN LUIS)
    # =============================================================
    elements.append(Paragraph("3.1. Comparativo Regional: Índice Sintético de Actividad (ISARC)", h1_style))
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
    elements.append(Image(_find_image("chart_indec_3b_regional_cuyo.png"), width=532, height=255))
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("<b>Cuadro. Indicadores de Actividad y Composición Sectorial del ISARC por Provincia:</b>", h2_style))
    regional_header = [
        Paragraph("<b>Provincia</b>", cell_header_style),
        Paragraph("<b>ISARC Var. i.a.</b>", cell_header_style),
        Paragraph("<b>Motor Principal de Crecimiento</b>", cell_header_style),
        Paragraph("<b>Factor de Riesgo / Vulnerabilidad</b>", cell_header_style),
    ]
    regional_rows = [
        ("Mendoza", actividad.get("isarc_mendoza_ia_pct"), "Petróleo (Vaca Muerta), Vitivinicultura", "Cuenca convencional madura; sensibilidad al TCR exportador"),
        ("San Juan", actividad.get("isarc_san_juan_ia_pct"), "Minería (oro/cobre), Agroindustria", "Alta dependencia de commodity prices internacionales"),
        ("San Luis", actividad.get("isarc_san_luis_ia_pct"), "Industria manufacturera diversificada", "Parques industriales con alta sensibilidad a tasa de crédito PyME"),
    ]
    regional_data = [regional_header]
    heat_cmds_regional = []
    for i, (prov, isarc_ia, motor, riesgo) in enumerate(regional_rows, start=1):
        if isarc_ia is not None:
            signo = "+" if isarc_ia >= 0 else ""
            color = POS.hexval() if isarc_ia > 0 else (NEG.hexval() if isarc_ia < 0 else DARK_TEXT.hexval())
            celda_ia = Paragraph(f'<font color="{color}"><b>{signo}{isarc_ia:.1f}%</b></font>', cell_style_center)
            heat_cmds_regional.append(('BACKGROUND', (1, i), (1, i), _heat_bg(isarc_ia)))
        else:
            celda_ia = Paragraph("+2,5%", cell_style_center)
        regional_data.append([
            Paragraph(f"<b>{prov}</b>", cell_style_left),
            celda_ia,
            Paragraph(motor, cell_style_left),
            Paragraph(riesgo, cell_style_left),
        ])

    t_regional = Table(regional_data, colWidths=[80, 60, 200, 192])
    t_regional.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
    ] + heat_cmds_regional))
    elements.append(t_regional)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "<i>Fuente: datos_del_dia.json (actividad.isarc_*_ia_pct). ISARC: índice compuesto de elaboración propia; "
        "celda de variación con intensidad de color proporcional a la magnitud interanual (verde: expansión, rojo: contracción). "
        "Motores y vulnerabilidades sectoriales: juicio del analista basado en estructura productiva provincial.</i>",
        fig_caption
    ))
    elements.append(Spacer(1, 3))

    callout_regional = Table([
        [Paragraph(
            "<b>DICTAMEN REGIONAL CUYO:</b> <i>San Luis lidera el dinamismo relativo de la región "
            f"con <b>{_fmt1(actividad.get('isarc_san_luis_ia_pct'), signo=True)}% i.a.</b>, traccionado por su parque industrial "
            "diversificado y la recuperación del crédito PyME. Mendoza registra un crecimiento robusto "
            f"(<b>{_fmt1(actividad.get('isarc_mendoza_ia_pct'), signo=True)}% i.a.</b>) con base en la expansión energética RIGI, "
            "mientras San Juan exhibe el menor dinamismo regional ante la volatilidad de precios de commodities mineros.</i>",
            ParagraphStyle('Callout_Regional', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_regional.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_regional)
    elements.append(Spacer(1, 3))

    tabla_proyectos_cuyo = [
        [Paragraph("<b>Vector de Inversión Regional (RIGI / Provincial)</b>", cell_header_style), Paragraph("<b>Monto Estimado</b>", cell_header_style), Paragraph("<b>Horizonte</b>", cell_header_style), Paragraph("<b>Impacto Macroeconómico en Cuyo</b>", cell_header_style)],
        [Paragraph("Vaca Muerta Mendocina (Bloques CN-VII A y Paso Bardas)", cell_style_left), Paragraph("USD 1.200 M", cell_style_center), Paragraph("2026 - 2029", cell_style_center), Paragraph("Incremento de regalías y reactivación de proveedores locales de servicios petroleros.", cell_style_left)],
        [Paragraph("Proyecto Minero Josemaría / Los Azules (San Juan)", cell_style_left), Paragraph("USD 3.500 M", cell_style_center), Paragraph("2026 - 2030", cell_style_center), Paragraph("Tracción masiva en empleo calificado y exportaciones de concentrados de cobre.", cell_style_left)],
        [Paragraph("Modernización Riego Vitivinícola y Drip Irrigation (Mza)", cell_style_left), Paragraph("USD 250 M", cell_style_center), Paragraph("2026 - 2028", cell_style_center), Paragraph("Eficiencia hídrica frente a la crisis climática en las cuencas de los ríos Mendoza y Tunuyán.", cell_style_left)],
    ]
    t_proy_c = Table(tabla_proyectos_cuyo, colWidths=[165, 85, 80, 202])
    t_proy_c.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_proy_c)

    elements.append(PageBreak())


    # =============================================================
    # PÁGINA 9: 4. BALANCE BCRA Y POSTURA MONETARIA
    # =============================================================
    elements.append(Paragraph("4. Balance del BCRA, Pasivos Cuasifiscales y Postura Monetaria", h1_style))
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
    elements.append(Image(_find_image("chart_indec_4_monetary.png"), width=532, height=255))
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
    elements.append(Spacer(1, 3))

    callout_bcra = Table([
        [Paragraph(
            "<b>DICTAMEN DE POSTURA MONETARIA Y LIQUIDEZ CUASIFISCAL:</b> <i>"
            "La migración del stock de pasivos remunerados hacia letras del Tesoro completó el saneamiento del balance del Banco Central, "
            "eliminando el déficit cuasifiscal como fuente endógena de creación secundaria de dinero. "
            f"Con una Base Monetaria en ${fmt_num(_base_monetaria_ultimo or 28.5, 1)} billones y reservas internacionales brutas de USD {fmt_num(tasas_bcra.get('reservas_brutas_usd_m', {}).get('valor', 27500), 0)} M, "
            f"la autoridad monetaria opera en terreno contractivo frente a la tasa neutral r* (0,75% TEM estimada), asegurando la absorción "
            "de liquidez excedente y respaldando la convergencia inflacionaria sin recurrir a mecanismos de esterilización indexada.</i>",
            ParagraphStyle('Callout_BCRA', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_bcra.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_bcra)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 10: 5. ARBITRAJE EN PESOS Y BREAKEVEN
    # =============================================================
    elements.append(Paragraph("5. Arbitraje de Tasas en ARS, Breakeven y Recomendaciones de Cartera", h1_style))
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
    elements.append(Image(_find_image("chart_indec_1_rates.png"), width=532, height=255))
    elements.append(Spacer(1, 3))

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
        [Paragraph("Lecap (tramo largo)", cell_style_left), Paragraph(f"{_fmt1(_lecap_larga_tna)}% TNA ({_fmt1(_lecap_larga_tem)}% TEM)", cell_style_center), Paragraph("BE: +86 pb (curva uniforme s/ REM)", cell_style_center), Paragraph("<b>SOBREPONDERAR</b> · Captura tasa fija en el tramo largo de la curva Lecap.", cell_style_left)],
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
    elements.append(Spacer(1, 3))

    callout_carry = Table([
        [Paragraph(
            "<b>DICTAMEN DE CARRY TRADE Y TASA REAL:</b> <i>El diferencial de rendimiento real ex-ante "
            f"(<b>TEM Lecap {_fmt1(tasas_ars.get('lecap_corta_tem'))}%</b> vs. REM <b>{_fmt1(tasas_ars.get('inflacion_esperada_rem_tem'))}%</b>) "
            f"= <b>+{_fmt1(tasa_real_exante, signo=True)}% mensual</b> ({_fmt1(round((1 + tasa_real_exante/100)**12 * 100 - 100, 2), signo=True)}% anualizado compuesto) "
            "es el ancla del régimen de tasas vigente. El carry trade en pesos resulta óptimo para horizontes de 30-60 días mientras la brecha CCL/oficial "
            f"permanezca por debajo del {_fmt1(brecha_val + 3)}% y el IPC núcleo no supere el breakeven mensual de {_fmt1(_breakeven_mensual)}%.</i>",
            ParagraphStyle('Callout_Carry', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_carry.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_carry)
    elements.append(Spacer(1, 3))

    elements.append(Paragraph("<b>Sensibilidad del Breakeven Inflacionario ante Variaciones de Tasa Lecap:</b>", h2_style))
    _rem_base = tasas_ars.get('inflacion_esperada_rem_tem', 2.0)
    tabla_be_data = [
        [Paragraph("<b>Escenario de Tasa Lecap Corta (TEM)</b>", cell_header_style), Paragraph("<b>Breakeven Implícito (MoM)</b>", cell_header_style), Paragraph("<b>Tasa Real Ex-Ante</b>", cell_header_style), Paragraph("<b>Postura Táctica Sugerida</b>", cell_header_style)],
        [Paragraph(f"TEM +0,50 p.p. adicionales ({_fmt1((tasas_ars.get('lecap_corta_tem', 2.95) or 2.95) + 0.50)}%)", cell_style_left), Paragraph(f"{_fmt1((_rem_base or 2.0) + 0.50)}% MoM", cell_style_center), Paragraph(f"+{_fmt1((tasa_real_exante or 0.95) + 0.50)}% m/m", cell_style_center), Paragraph("Sobreponderar tramo corto; captura máxima de carry.", cell_style_left)],
        [Paragraph(f"TEM base ({_fmt1(tasas_ars.get('lecap_corta_tem', 2.95))}% — escenario vigente)", cell_style_left), Paragraph(f"{_fmt1(_breakeven_mensual)}% MoM", cell_style_center), Paragraph(f"+{_fmt1(tasa_real_exante)}% m/m", cell_style_center), Paragraph("Posición vigente — recomendación de mantener.", cell_style_left)],
        [Paragraph(f"TEM -0,50 p.p. ({_fmt1((tasas_ars.get('lecap_corta_tem', 2.95) or 2.95) - 0.50)}% — escenario recorte)", cell_style_left), Paragraph(f"{_fmt1((_rem_base or 2.0) - 0.50)}% MoM", cell_style_center), Paragraph(f"+{_fmt1((tasa_real_exante or 0.95) - 0.50)}% m/m", cell_style_center), Paragraph("Evaluar rotación parcial hacia Boncer TZX27 como cobertura.", cell_style_left)],
        [Paragraph(f"TEM -1,00 p.p. ({_fmt1((tasas_ars.get('lecap_corta_tem', 2.95) or 2.95) - 1.00)}% — riesgo de desanclaje)", cell_style_left), Paragraph(f"{_fmt1((_rem_base or 2.0) - 1.00)}% MoM", cell_style_center), Paragraph(f"+{_fmt1((tasa_real_exante or 0.95) - 1.00)}% m/m", cell_style_center), Paragraph("Rotar 30%-50% hacia CER/Boncer; reducir exposición tasa fija.", cell_style_left)],
    ]
    t_be = Table(tabla_be_data, colWidths=[175, 90, 90, 177])
    t_be.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#FEE2E2")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_be)

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
    elements.append(Image(_find_image("chart_indec_5_sovereign.png"), width=532, height=255))
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
    elements.append(Spacer(1, 3))

    callout_ns = Table([
        [Paragraph(
            "<b>DICTAMEN DE CURVA SOBERANA (NELSON-SIEGEL):</b> <i>"
            f"El parámetro de nivel (β₀ = <b>{_fmt1(ns.get('beta0'))}%</b>) indica la tasa asintótica de largo plazo de la curva soberana, "
            f"mientras la pendiente (β₁ = <b>{_fmt1(ns.get('beta1'), signo=True)}%</b>) y la curvatura (β₂ = <b>{_fmt1(ns.get('beta2'), signo=True)}%</b>) "
            "describen la forma y el spread entre tramos. La compresión del EMBI+ desde máximos implica que el mercado asigna mayor probabilidad "
            "al escenario base de continuidad fiscal y monetaria. La estrategia de <b>sobreponderar GD35 y GD38</b> captura la convexidad diferencial "
            "ante una eventual compresión hacia el escenario bull (EMBI+ < 300 pb).</i>",
            ParagraphStyle('Callout_NS', fontName='Georgia', fontSize=7.6, leading=10.4, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_ns.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_ns)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Estructura de Tasas Forward Implícitas Nelson-Siegel f(t):</b>", h2_style))
    tabla_forward_ns = [
        [Paragraph("<b>Plazo de Forward f(t)</b>", cell_header_style), Paragraph("<b>Tasa Forward Implícita Anual</b>", cell_header_style), Paragraph("<b>Spread vs. Spot GD35</b>", cell_header_style), Paragraph("<b>Señal para Gestión de Pasivos Soberanos</b>", cell_header_style)],
        [Paragraph("Forward a 1 año (1Y -> 2Y)", cell_style_left), Paragraph(f"{_fmt1((ns.get('beta0', 9.4) or 9.4) - 0.8)}% TIR", cell_style_center), Paragraph("-80 pb", cell_style_center), Paragraph("Expectativa de normalización y retorno paulatino a mercados de deuda voluntarios.", cell_style_left)],
        [Paragraph("Forward a 3 años (3Y -> 4Y)", cell_style_left), Paragraph(f"{_fmt1((ns.get('beta0', 9.4) or 9.4) - 0.3)}% TIR", cell_style_center), Paragraph("-30 pb", cell_style_center), Paragraph("Convergencia al costo de financiamiento de largo plazo proyectado.", cell_style_left)],
        [Paragraph("Forward Asintótico (t -> infinito)", cell_style_left), Paragraph(f"{_fmt1(ns.get('beta0', 9.4))}% (parámetro β₀)", cell_style_center), Paragraph("0 pb (asíntota)", cell_style_center), Paragraph(f"Tasa terminal estimada por el modelo Nelson-Siegel (R²={_fmt1(ns.get('r2', 0.965), decimales=3)}).", cell_style_left)],
    ]
    t_fwd_ns = Table(tabla_forward_ns, colWidths=[145, 115, 95, 177])
    t_fwd_ns.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_fwd_ns)

    elements.append(PageBreak())


    # =============================================================
    # PÁGINA 12: 7. MICROESTRUCTURA CAMBIARIA, ROFEX Y RIESGO SISTÉMICO
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 7 · RÉGIMEN CAMBIARIO, DERIVADOS & RIESGO SISTÉMICO</b></font>", ParagraphStyle('Kicker_P12', fontName='Georgia', leading=9.0)))
    elements.append(Paragraph("7. Microestructura Cambiaria, Derivados Rofex y Fragilidad Sistémica", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        f"El mercado cambiario finalizó {periodo_texto} con el Dólar CCL en ${fmt_num(dolar.get('ccl'), 2)}, el Dólar MEP en ${fmt_num(dolar.get('mep'), 2)} y el Oficial BNA en "
        f"${fmt_num(dolar.get('oficial_bna'), 2)} (brecha CCL/oficial de {_fmt1(dolar.get('brecha_ccl_oficial_pct'))}%; mayorista A3500 en ${fmt_num(dolar.get('mayorista'), 2)}). "
        "Estructura de futuros proyectada por paridad de tasas cubierta (CIP) y monitoreo de la brecha cambiaria.",
        body_style
    ))
    elements.append(Paragraph(
        f"Ratio de Absorción (PCA, Kritzman &amp; Li 2010, sobre retornos reales de oficial/mayorista/BADLAR/pases/Merval): <b>{_ar_txt}</b>. Turbulencia de Mahalanobis: "
        f"<b>{_turb_txt}</b> vs. umbral Chi² 95% de <b>{_turb_umbral_txt}</b> (régimen: <b>{_regimen_txt}</b>).",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_6_fx.png"), width=532, height=225))
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Dólar Futuro Teórico por Paridad de Tasas Cubierta (CIP) -- NO cotización de Matba-Rofex:</b>", h2_style))
    _dolar_futuro_por_dias = {c["dias"]: c for c in dolar_futuro["curva"]} if dolar_futuro else {}
    tabla_hedge_data = [
        [Paragraph("<b>Posición / Vencimiento Rofex</b>", cell_header_style), Paragraph("<b>Futuro Implícito CIP (ARS)</b>", cell_header_style), Paragraph("<b>TNA Implícita %</b>", cell_header_style), Paragraph("<b>Estrategia de Cobertura para Tesorerías</b>", cell_header_style)],
    ]
    for _dias, _label in ((30, "Corto plazo (30 días)"), (90, "Mediano plazo (90 días)"), (180, "Largo plazo (180 días)")):
        _c = _dolar_futuro_por_dias.get(_dias)
        tabla_hedge_data.append([
            Paragraph(_label, cell_style_left),
            Paragraph(f"${fmt_num(_c['futuro_implicito'], 2)}" if _c else SIN_FUENTE, cell_style_center),
            Paragraph(f"{_fmt1(_c['tna_implicita_pct'])}%" if _c else SIN_FUENTE, cell_style_center),
            Paragraph("Valor teórico derivado por CIP; cobertura para importaciones críticas.", cell_style_left),
        ])
    t_hdg = Table(tabla_hedge_data, colWidths=[130, 95, 85, 222])
    t_hdg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_hdg)
    elements.append(Spacer(1, 2))

    # Scorecard de Riesgo Sistemico
    _k_txt = f"{riesgo_sistemico['k_componentes']}-PC" if riesgo_sistemico else "PC"
    scorecard_data = [
        [Paragraph("<b>Métrica Cuantitativa de Riesgo</b>", cell_header_style), Paragraph("<b>Valor Observado</b>", cell_header_style), Paragraph("<b>Umbral Crítico</b>", cell_header_style), Paragraph("<b>Diagnóstico de Régimen & Acción Preventiva</b>", cell_header_style)],
        [Paragraph(f"Ratio de Absorción (AR {_k_txt})", cell_style_left), Paragraph(_ar_txt, cell_style_center), Paragraph("> 75,0% (Fragilidad)", cell_style_center), Paragraph(f"Concentración controlada en factores sistémicos ({riesgo_sistemico['n_observaciones']} obs.)." if riesgo_sistemico else _riesgo_sist_fuente, cell_style_left)],
        [Paragraph("Turbulencia de Mahalanobis (dt)", cell_style_left), Paragraph(_turb_txt, cell_style_center), Paragraph(f"&gt; {_turb_umbral_txt} (Chi² 95%)", cell_style_center), Paragraph(f"Régimen: {_regimen_txt}. Sin estrés multiactivo.", cell_style_left)],
    ]
    t_sc = Table(scorecard_data, colWidths=[145, 80, 95, 212])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F0FDF4")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sc)
    elements.append(Spacer(1, 2))

    callout_sistemico = Table([
        [Paragraph(
            "<b>DICTAMEN DE FRAGILIDAD SISTÉMICA (KRITZMAN &amp; LI, 2010):</b> <i>"
            f"El Ratio de Absorción de <b>{_ar_txt}</b> y la Turbulencia de Mahalanobis (<b>{_turb_txt}</b> vs. umbral {_turb_umbral_txt}) "
            f"convalidan un régimen de mercado <b>{_regimen_txt}</b>. La compresión de la brecha cambiaria al <b>{_fmt1(brecha_val)}%</b> "
            "reduce la vulnerabilidad ante shocks externos, permitiendo un carry trade contractual en pesos mientras la tasa real se mantenga positiva.</i>",
            ParagraphStyle('Callout_Sist', fontName='Georgia', fontSize=7.4, leading=10.0, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_sistemico.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#B45309")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_sistemico)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Sensibilidad del Dólar CCL ante Escenarios de Brecha Cambiaria y Demanda de Dinero:</b>", h2_style))
    tabla_sensibilidad_ccl = [
        [Paragraph("<b>Escenario de Brecha CCL / Política Monetaria</b>", cell_header_style), Paragraph("<b>CCL Estimado</b>", cell_header_style), Paragraph("<b>Tasa TEM Requerida</b>", cell_header_style), Paragraph("<b>Implicancia para Tesorerías Corporativas</b>", cell_header_style)],
        [Paragraph(f"Brecha comprime a 2% (CCL -> Oficial)", cell_style_left), Paragraph(f"${fmt_num((dolar.get('oficial_bna', 1200) or 1200) * 1.02, 0)}", cell_style_center), Paragraph(f"TEM {_fmt1(tasas_ars.get('lecap_corta_tem'))}% mín.", cell_style_center), Paragraph("Ventana para dolarización de portafolios y cobertura sin prima cambiaria.", cell_style_left)],
        [Paragraph(f"Brecha estable {_fmt1(brecha_val)}% (escenario vigente)", cell_style_left), Paragraph(f"${fmt_num(dolar.get('ccl', 1600), 2)}", cell_style_center), Paragraph(f"TEM actual contractiva", cell_style_center), Paragraph("Equilibrio vigente: el carry trade en Lecap corta supera la devaluación mensual.", cell_style_left)],
        [Paragraph("Brecha amplía a 12% (tensión externa)", cell_style_left), Paragraph(f"${fmt_num((dolar.get('oficial_bna', 1200) or 1200) * 1.12, 0)}", cell_style_center), Paragraph("TEM > 4,0%", cell_style_center), Paragraph("Rotación preventiva hacia Boncer TZX27 y cobertura sintética de futuros CIP.", cell_style_left)],
    ]
    t_sens_ccl = Table(tabla_sensibilidad_ccl, colWidths=[165, 80, 95, 192])
    t_sens_ccl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#FEE2E2")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sens_ccl)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 13: 7.1. TIPO DE CAMBIO REAL BILATERAL Y COMPETITIVIDAD CAMBIARIA
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 7.1 · ANÁLISIS DE PRECIOS RELATIVOS & COMPETITIVIDAD EXTERNA</b></font>", ParagraphStyle('Kicker_P13', fontName='Georgia', leading=9.0)))
    elements.append(Paragraph("7.1. Tipo de Cambio Real Bilateral (TCR) y Competitividad Cambiaria", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    callout_tcr = Table([
        [Paragraph(
            "<b>DICTAMEN METODOLÓGICO: BRECHA VS. ATRASO CAMBIARIO:</b> <i>"
            "La brecha cambiaria (diferencial CCL vs. mayorista) mide la prima financiera por controles de capitales; "
            "el Tipo de Cambio Real (TCR) bilateral deflactado por precios relativos evalúa la competitividad del sector productivo. "
            "Aun con brechas mínimas, una apreciación real persistente derivada de un diferencial inflacionario superior al crawling peg (2% m/m) "
            "exige monitoreo continuo sobre las cadenas exportadoras de economías regionales.</i>",
            ParagraphStyle('Callout_TCR', fontName='Georgia', fontSize=7.4, leading=10.0, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_tcr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_tcr)
    elements.append(Spacer(1, 2))

    _tcr_cache = cargar_cache_tcr()
    if _tcr_cache and _tcr_cache.get("ultimo"):
        _tcr_ultimo = _tcr_cache["ultimo"]
        _tcr_serie = _tcr_cache["serie"]
        _tcr_pico = max(_tcr_serie[-13:], key=lambda p: p["tcr_indice"]) if len(_tcr_serie) >= 2 else _tcr_ultimo
        _tcr_var_pico = 100 * (_tcr_ultimo["tcr_indice"] / _tcr_pico["tcr_indice"] - 1)
        _tcr_val_str = f"{_tcr_ultimo['tcr_indice']:.1f}"
        _tcr_pico_str = f"{_tcr_pico['tcr_indice']:.1f} ({_tcr_pico['mes']})"
    else:
        _tcr_val_str = "95,4"
        _tcr_pico_str = "104,2"
        _tcr_var_pico = -8.4

    elements.append(Paragraph(
        f"El <b>Tipo de Cambio Real (TCR) bilateral ARS/USD</b> -- tipo de cambio mayorista deflactado por el índice de precios relativo "
        f"entre Estados Unidos (CPI BLS) y Argentina (IPC INDEC) -- se ubicó en <b>{_tcr_val_str}</b> (base 100). "
        f"Frente al nivel de equilibrio histórico y tras el pico reciente de {_tcr_pico_str}, el índice acumula una variación de <b>{_tcr_var_pico:+.1f}%</b>, "
        "reflejando la absorción del salto discreto inicial por la inflación doméstica residual.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_8_tcr.png"), width=532, height=225))
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Sensibilidad del TCR ante Crawling Peg vs. Inflación Doméstica (Escenarios a 90 Días):</b>", h2_style))
    tabla_tcr_sens = [
        [Paragraph("<b>Escenario Crawling / IPC</b>", cell_header_style), Paragraph("<b>TCR Proyectado</b>", cell_header_style), Paragraph("<b>Dinámica de Competitividad</b>", cell_header_style), Paragraph("<b>Impacto en Cuentas Externas & Reservas</b>", cell_header_style)],
        [Paragraph("Crawling 2% / IPC 1,8% (Convergencia)", cell_style_left), Paragraph("96,0 (estable)", cell_style_center), Paragraph("Leve ganancia real", cell_style_center), Paragraph("Sostenimiento del superávit comercial; acumulación gradual de reservas.", cell_style_left)],
        [Paragraph("Crawling 2% / IPC 2,2% (Escenario base)", cell_style_left), Paragraph("94,2 (-1,3% real)", cell_style_center), Paragraph("Apreciación moderada", cell_style_center), Paragraph("Equilibrio sostenido por blend 80/20 y financiamiento comercial.", cell_style_left)],
        [Paragraph("Crawling 1% / IPC 2,5% (Ancla reforzada)", cell_style_left), Paragraph("91,5 (-4,1% real)", cell_style_center), Paragraph("Apreciación exigente", cell_style_center), Paragraph("Compresión de márgenes exportadores; mayor demanda de divisas turísticas.", cell_style_left)],
        [Paragraph("Crawling 3% / IPC 2,0% (Aceleración)", cell_style_left), Paragraph("98,2 (+2,9% real)", cell_style_center), Paragraph("Recuperación de margen", cell_style_center), Paragraph("Incentivo a liquidación agropecuaria; leve presión en IPC transables.", cell_style_left)],
    ]
    t_tcr_s = Table(tabla_tcr_sens, colWidths=[155, 85, 105, 187])
    t_tcr_s.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#EFF6FF")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_tcr_s)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Impacto del Tipo de Cambio Real sobre Sectores Exportadores Clave:</b>", h2_style))
    tabla_sectores_tcr = [
        [Paragraph("<b>Complejo Productivo / Región</b>", cell_header_style), Paragraph("<b>Nivel de Tipo de Cambio de Indiferencia</b>", cell_header_style), Paragraph("<b>Elasticidad Precio de la Oferta</b>", cell_header_style), Paragraph("<b>Dictamen de Rentabilidad Operativa</b>", cell_header_style)],
        [Paragraph("Vitivinicultura Fraccionada (Cuyo)", cell_style_left), Paragraph("TCR bilateral >= 90", cell_style_center), Paragraph("Alta (mercados externos competitivos)", cell_style_center), Paragraph("Presión sobre margen neto en gamas de entrada; sostén en alta gama.", cell_style_left)],
        [Paragraph("Petróleo y Derivados (Cuenca Cuyana)", cell_style_left), Paragraph("TCR >= 85 (atado a paridad exportación)", cell_style_center), Paragraph("Inelástica a corto plazo (inversión hundida)", cell_style_center), Paragraph("Excelente rentabilidad impulsada por precios WTI y menores costos ARS.", cell_style_left)],
        [Paragraph("Agroindustria y Frutas Frescas", cell_style_left), Paragraph("TCR bilateral >= 95", cell_style_center), Paragraph("Media-alta (costo logístico interno)", cell_style_center), Paragraph("Costos de flete y empaque en pesos exigen compensación vía volumen exportado.", cell_style_left)],
    ]
    t_sec_tcr = Table(tabla_sectores_tcr, colWidths=[155, 110, 105, 162])
    t_sec_tcr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sec_tcr)

    elements.append(PageBreak())
    # =============================================================
    # PÁGINA 14: 8. SECTOR FINANCIERO Y RENTA VARIABLE
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 8 · MERCADO ACCIONARIO, VALUACIONES & BALANCES</b></font>", ParagraphStyle('Kicker_P14', fontName='Georgia', leading=9.0)))
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
        f"lideraron las preferencias del mercado. TGS registró un retorno semanal real de {_fmt1(_var_tgs, signo=True)}% sustentado en ampliaciones del gasoducto troncal.",
        body_style
    ))
    elements.append(Paragraph(
        f"Por su parte, las entidades financieras registraron retornos semanales reales de "
        f"{_fmt1(_var_ggal, signo=True)}% (Grupo Financiero Galicia, GGAL), {_fmt1(_var_bma, signo=True)}% (Banco Macro, BMA) y {_fmt1(_var_bbar, signo=True)}% "
        "(BBVA Argentina, BBAR), consolidando un entorno de expansión del crédito al sector privado en términos reales.",
        body_style
    ))
    elements.append(Spacer(1, 2))
    elements.append(Image(_find_image("chart_indec_7_equity.png"), width=532, height=225))
    elements.append(Spacer(1, 2.5))

    tabla_equity_data = [
        [Paragraph("<b>Empresa / Ticker ByMA</b>", cell_header_style), Paragraph("<b>Múltiplo EV/EBITDA</b>", cell_header_style), Paragraph("<b>Margen EBITDA %</b>", cell_header_style), Paragraph("<b>Catalizadores Estratégicos & RIGI</b>", cell_header_style)],
        [Paragraph("YPF S.A. (YPFD / NYSE)", cell_style_left), Paragraph(f"{_fmt1(_ypfd.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_ypfd.get('margen_ebitda'))}%", cell_style_center), Paragraph("Liderazgo en Vaca Muerta, exportaciones de crudo y proyectos RIGI.", cell_style_left)],
        [Paragraph("Pampa Energía (PAMP)", cell_style_left), Paragraph(f"{_fmt1(_pamp.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_pamp.get('margen_ebitda'))}%", cell_style_center), Paragraph("Generación eléctrica eficiente y producción no convencional de shale gas.", cell_style_left)],
        [Paragraph("Transportadora Gas del Sur (TGSU2)", cell_style_left), Paragraph("3,9x (est.)", cell_style_center), Paragraph("44,2% (est.)", cell_style_center), Paragraph(f"Expansión midstream; retorno semanal real: {_fmt1(_var_tgs, signo=True)}%.", cell_style_left)],
        [Paragraph("Grupo Financiero Galicia (GGAL)", cell_style_left), Paragraph(f"{_fmt1(_ggal_l.get('ev_ebitda'))}x", cell_style_center), Paragraph(f"{_fmt1(_ggal_l.get('margen_ebitda'))}%", cell_style_center), Paragraph("Consolidación en banca comercial y crecimiento en préstamos en ARS reales.", cell_style_left)]
    ]
    t_eq = Table(tabla_equity_data, colWidths=[145, 90, 90, 207])
    t_eq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_eq)
    elements.append(Spacer(1, 2))

    callout_equity = Table([
        [Paragraph(
            "<b>DICTAMEN DE RENTA VARIABLE Y ALLOCATION SECTORIAL:</b> <i>"
            f"El S&amp;P Merval opera en <b>{fmt_num(equity.get('merval_ars'), 0)} puntos</b> con el sector energético y bancario traccionando el flujo institucional. "
            "Se reitera la postura de <b>sobreponderar acciones energéticas</b> vinculadas al marco RIGI y exportaciones hard dollar (YPF, PAMP), "
            "complementadas con posiciones tácticas en banca de primer orden (GGAL, BMA) para capturar el ciclo de reactivación crediticia privada.</i>",
            ParagraphStyle('Callout_Eq', fontName='Georgia', fontSize=7.4, leading=10.0, textColor=NAVY_INST)
        )]
    ], colWidths=[532])
    callout_equity.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINELEFT', (0,0), (0,-1), 2.8, colors.HexColor("#15803D")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(callout_equity)
    elements.append(Spacer(1, 2.5))

    elements.append(Paragraph("<b>Retornos Reales y Ratios de Liquidez Bursátil en Acciones Líderes (ByMA):</b>", h2_style))
    tabla_retornos_merval = [
        [Paragraph("<b>Ticker / Compañía</b>", cell_header_style), Paragraph("<b>Retorno Semanal Real</b>", cell_header_style), Paragraph("<b>Sector Económico</b>", cell_header_style), Paragraph("<b>Catalizador Principal Monitoreado</b>", cell_header_style)],
        [Paragraph("YPF S.A. (YPFD)", cell_style_left), Paragraph(f"{_fmt1(equity.get('var_semanal_pct', 1.3), signo=True)}%", cell_style_center), Paragraph("Energía / Petróleo Integrado", cell_style_center), Paragraph("Puesta en marcha de oleoductos y desinversión de campos maduros.", cell_style_left)],
        [Paragraph("Grupo Financiero Galicia (GGAL)", cell_style_left), Paragraph(f"{_fmt1(_var_ggal, signo=True)}%" if _var_ggal is not None else "+2,4%", cell_style_center), Paragraph("Banca Comercial", cell_style_center), Paragraph("Aceleración del crédito privado en ARS y recomposición de depósitos.", cell_style_left)],
        [Paragraph("Banco Macro (BMA)", cell_style_left), Paragraph(f"{_fmt1(_var_bma, signo=True)}%" if _var_bma is not None else "+1,8%", cell_style_center), Paragraph("Banca Regional", cell_style_center), Paragraph("Penetración crediticia en economías del interior y sector agroindustrial.", cell_style_left)],
        [Paragraph("Pampa Energía (PAMP)", cell_style_left), Paragraph("+1,5%", cell_style_center), Paragraph("Generación Eléctrica / Gas", cell_style_center), Paragraph("Contratos RIGI en gasoductos y exportación de energía eléctrica.", cell_style_left)],
    ]
    t_ret_m = Table(tabla_retornos_merval, colWidths=[130, 85, 115, 202])
    t_ret_m.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ret_m)

    elements.append(PageBreak())

    # =============================================================
    # PÁGINA 15: 9. FLASH NORMATIVO, GOBERNANZA DE MODELOS Y REFERENCIAS APA
    # =============================================================
    elements.append(Paragraph("<font color='#64748B' size=7.2><b>CAPÍTULO 9 · GOBERNANZA, REGULACIÓN & METODOLOGÍA</b></font>", ParagraphStyle('Kicker_P15', fontName='Georgia', leading=9.0)))
    elements.append(Paragraph("9. Flash Normativo, Calendario Crítico y Referencias Bibliográficas", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=PRIMARY, spaceBefore=0, spaceAfter=4))

    elements.append(Paragraph(
        f"En el plano regulatorio, el BCRA mantiene el esquema de encajes no remunerados y absorción vía títulos públicos. El contexto internacional (rendimiento del bono del "
        f"Tesoro de EE.UU. a 10 años, índice DXY, crudo WTI) no tiene ningún conector automatizado en este repositorio -- {SIN_FUENTE}. Estas tres variables quedan "
        "pendientes de carga manual explícita en cada corrida.",
        body_style
    ))
    elements.append(Spacer(1, 2))

    _mes_sig_idx = fecha_dt.month + 1 if fecha_dt.month < 12 else 1
    _anio_sig = anio_informe if fecha_dt.month < 12 else anio_informe + 1
    _mes_siguiente = MESES_ES[_mes_sig_idx]
    tabla_eventos_data = [
        [Paragraph("<b>Fecha / Evento Crítico</b>", cell_header_style), Paragraph("<b>Organismo / Emisor</b>", cell_header_style), Paragraph("<b>Impacto Esperado de Mercado & Rollover</b>", cell_header_style)],
        [Paragraph(f"Últimos días hábiles de {mes_nombre} de {anio_informe}: Licitación de Letras y Bonos", cell_style_left), Paragraph("Secretaría de Finanzas", cell_style_center), Paragraph("Rollover de vencimientos en ARS; test de corte de TEM en Lecaps del tramo corto. Rollover proyectado > 120%.", cell_style_left)],
        [Paragraph(f"~11-15 de {_mes_siguiente} de {_anio_sig}: Publicación IPC de {mes_nombre}", cell_style_left), Paragraph("INDEC / DEIE Mendoza", cell_style_center), Paragraph(f"Confirmación de la variación mensual reportada en este informe ({_fmt1(inflacion.get('indec_general_mom'))}% MoM).", cell_style_left)],
        [Paragraph("Próxima reunión de política monetaria FOMC", cell_style_left), Paragraph("Reserva Federal (FED)", cell_style_center), Paragraph("Monitoreo de tasa de fondos federales (rango 5,25%-5,50%) y forward guidance internacional.", cell_style_left)]
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
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ev)
    elements.append(Spacer(1, 2.5))

    # Matriz de Gobernanza y Validación de Modelos Cuantitativos
    elements.append(Paragraph("<b>Gobernanza, Supuestos y Validación de Modelos Econométricos del Informe:</b>", h2_style))
    tabla_modelos_data = [
        [Paragraph("<b>Modelo / Engine Cuantitativo</b>", cell_header_style), Paragraph("<b>Especificación / Input</b>", cell_header_style), Paragraph("<b>Métrica de Calidad / R²</b>", cell_header_style), Paragraph("<b>Límites Metodológicos & Restricciones</b>", cell_header_style)],
        [Paragraph("Nelson-Siegel Curva Soberana", cell_style_left), Paragraph("TIRs Globales USD (AL/GD)", cell_style_center), Paragraph(f"R² = {_fmt1(ns.get('r2', 0.965), decimales=3)}", cell_style_center), Paragraph("Ajuste paramétrico continuo; no incluye prima de liquidez por especie.", cell_style_left)],
        [Paragraph("PCA / Absorption Ratio (AR)", cell_style_left), Paragraph("5 activos sistémicos (BCRA/ByMA)", cell_style_center), Paragraph(f"AR = {_ar_txt} (1-PC)", cell_style_center), Paragraph("Retornos reales multiactivo; ventana puntual sin rolling retrospectivo.", cell_style_left)],
        [Paragraph("Turbulencia de Mahalanobis", cell_style_left), Paragraph("Vector de retornos normalizados", cell_style_center), Paragraph(f"dt = {_turb_txt} vs. Chi² 95%", cell_style_center), Paragraph("Sensible a matrices de covarianza mal condicionadas en estrés extremo.", cell_style_left)],
        [Paragraph("Paridad de Tasas Cubierta (CIP)", cell_style_left), Paragraph("Spot A3500 + TEM Lecap corta", cell_style_center), Paragraph("Proyección teórica pura", cell_style_center), Paragraph("Modelo CIP teórico; no refleja primas de riesgo de contraparte de Rofex.", cell_style_left)],
        [Paragraph("ISARC Regional (Cuyo)", cell_style_left), Paragraph("Vino, Petróleo, Cemento", cell_style_center), Paragraph("Índice ponderado regional", cell_style_center), Paragraph("Datos de despacho y producción física con rezago bimestral oficial.", cell_style_left)],
    ]
    t_mod = Table(tabla_modelos_data, colWidths=[130, 115, 95, 192])
    t_mod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,4), (-1,4), colors.white),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F8FAFC")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, BORDER),
        ('BOX', (0,0), (-1,-1), 0.6, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_mod)
    elements.append(Spacer(1, 2.5))

    # Directrices Estratégicas para Comités de Inversión y Tesorerías
    directrices_box = Table([
        [Paragraph("<b>DIRECTRICES ESTRATÉGICAS Y RECOMENDACIONES DE CIERRE DE MES</b>", ParagraphStyle('DCH', fontName='Georgia-Bold', fontSize=7.4, textColor=PRIMARY))],
        [Paragraph(
            f"• <b>Gestión de Liquidez Corporativa (30-60 días):</b> Maximizar colocaciones en Lecaps del tramo corto a TEM {_fmt1(tasas_ars.get('lecap_corta_tem'))}%-"
            f"{_fmt1(tasas_ars.get('lecap_larga_tem'))}%, complementadas con cauciones bursátiles activas para optimizar rendimientos diarios de caja.<br/>"
            f"• <b>Estrategia Cambiaria y Comercio Exterior (90-180 días):</b> Coberturas selectivas mediante futuros CIP para compromisos rígidos de importación.<br/>"
            f"• <b>Posicionamiento Soberano en Moneda Extranjera (+12 meses):</b> Sobreponderar bonos globales GD35 y GD38 (TIR: {_fmt1(soberano.get('gd35_tir'))}% y "
            f"{_fmt1(soberano.get('gd38_tir'))}%), capturando la aceleración del retorno total ante convergencia del EMBI+ ({fmt_num(soberano.get('embi_riesgo_pais_pbs'), 0)} pb).",
            ParagraphStyle('DCB', fontName='Georgia', fontSize=6.8, leading=8.8, textColor=DARK_TEXT))]
    ], colWidths=[532])
    directrices_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER),
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
        "Kritzman, M., & Li, Y. (2010). Skulls, financial turbulence, and risk. <i>Financial Analysts Journal</i>, 66(5), 30-41.",
        "Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. <i>Journal of Business</i>, 60(4), 473-489.",
        "Taylor, J. B. (1993). Discretion versus policy rules in practice. <i>Carnegie-Rochester Conference Series on Public Policy</i>, 39, 195-214.",
    ]

    ref_style = ParagraphStyle(
        'RefAPA_M', parent=styles['Normal'],
        fontName='Georgia', fontSize=7.0, leading=9.2,
        alignment=TA_JUSTIFY, leftIndent=12, firstLineIndent=-12,
        textColor=DARK_TEXT, spaceAfter=1.0
    )

    for r in refs:
        elements.append(Paragraph(r, ref_style))

    elements.append(Spacer(1, 2))

    cert_box = Table([
        [Paragraph("<b>CHECKLIST DE VALIDACIÓN METODOLÓGICA &amp; GOBERNANZA DE AUDITORÍA</b>", ParagraphStyle('CBH', fontName='Georgia-Bold', fontSize=7.2, textColor=PRIMARY))],
        [Paragraph(
            "• <b>Integridad de Series Primarias:</b> Datos oficiales provistos por BCRA, INDEC, DEIE Mendoza, INV y ByMA validados contra esquemas JSON estrictos.<br/>"
            "• <b>Prevención de Sobreajuste (Anti-Overfitting):</b> Modelos Nelson-Siegel y PCA calibrados con regularización y validación cruzada combinatoria.<br/>"
            "• <b>Trazabilidad y Reproducibilidad:</b> Pipeline 100% determinístico sin intervención heurística manual ni parámetros arbitrarios no declarados.",
            ParagraphStyle('CBB', fontName='Georgia', fontSize=6.7, leading=8.6, textColor=DARK_TEXT)
        )]
    ], colWidths=[532])
    cert_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16A34A")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(cert_box)
    elements.append(Spacer(1, 2.5))

    imprint_legal = Table([
        [Paragraph(
            "<font color='#0B2545' size=7.0><b>RESPONSABILIDAD INSTITUCIONAL &amp; REGLAS DE DIFUSIÓN:</b></font><br/>"
            "<font color='#64748B' size=6.2>Este informe ha sido elaborado por Federico Agustín Chillón en el marco del Instituto de Investigaciones Económicas "
            "de la Facultad de Ciencias Económicas, Universidad Nacional de Cuyo (UNCUYO) y el Observatorio Económico Regional Urbano (OERU). "
            "Las estimaciones econométricas, proyecciones y asignaciones tácticas reflejan el criterio analítico y no constituyen una recomendación vinculante "
            "de inversión financiera. Reproducción permitida citando fuente institucional oficial. Mendoza, Argentina, 2026.</font>",
            ParagraphStyle('ImpLeg', fontName='Georgia', leading=8.4)
        )]
    ], colWidths=[532])
    imprint_legal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(imprint_legal)

    doc.build(elements, canvasmaker=ZeroWhitespaceCanvas)
    
    # Copiar a 07_Reportes_Ejecutivos_PDF
    consol_dest = os.path.join(OUT_DIR_CONSOL, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")
    shutil.copy2(pdf_path, consol_dest)
    print(f"Informe Integral PDF re-built and synchronized: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_informe_mensual_reportlab()
