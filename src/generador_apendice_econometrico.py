# -*- coding: utf-8 -*-
"""
================================================================================
APÉNDICE TÉCNICO: DIAGNÓSTICO ECONOMÉTRICO, MODELADO DE CURVAS Y PRUEBAS DE ESTRÉS
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
Documento: Apéndice Cuantitativo & Gobernanza Empírica (Cierre Agosto 2026)
================================================================================
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
os.makedirs(OUT_DIR, exist_ok=True)

# Registro de fuentes Palatino
FONT_DIR = r"C:\Windows\Fonts"
try:
    pdfmetrics.registerFont(TTFont('Palatino', os.path.join(FONT_DIR, 'pala.ttf')))
    pdfmetrics.registerFont(TTFont('Palatino-Bold', os.path.join(FONT_DIR, 'palab.ttf')))
    pdfmetrics.registerFont(TTFont('Palatino-Italic', os.path.join(FONT_DIR, 'palai.ttf')))
    pdfmetrics.registerFont(TTFont('Palatino-BoldItalic', os.path.join(FONT_DIR, 'palabi.ttf')))
    pdfmetrics.registerFontFamily('Palatino', normal='Palatino', bold='Palatino-Bold', italic='Palatino-Italic', boldItalic='Palatino-BoldItalic')
except Exception:
    pass

PRIMARY = colors.HexColor("#0B2545")
ACCENT = colors.HexColor("#0284C7")
DARK_TEXT = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#CBD5E1")
HAIRLINE = colors.HexColor("#E2E8F0")
BG_HEADER = colors.HexColor("#0B2545")
BG_ROW_ALT = colors.HexColor("#F8FAFC")


class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        w, h = letter
        margin = 36

        # Encabezado institucional superior
        self.setStrokeColor(PRIMARY)
        self.setLineWidth(1.0)
        self.line(margin, h - 38, w - margin, h - 38)

        self.setFont("Palatino-Bold", 8.0)
        self.setFillColor(PRIMARY)
        self.drawString(margin, h - 32, "FACULTAD DE CIENCIAS ECONÓMICAS · UNIVERSIDAD NACIONAL DE CUYO")

        self.setFont("Palatino", 7.5)
        self.setFillColor(MUTED)
        self.drawRightString(w - margin, h - 32, "APÉNDICE TÉCNICO & GOBERNANZA ECONOMÉTRICA")

        # Pie institucional inferior
        self.setStrokeColor(HAIRLINE)
        self.setLineWidth(0.6)
        self.line(margin, 36, w - margin, 36)

        self.setFont("Palatino", 7.0)
        self.setFillColor(MUTED)
        self.drawString(margin, 24, "Investigación Cuantitativa · Federico Agustín Chillón · FCE UNCUYO")
        self.drawRightString(w - margin, 24, f"Página {self._pageNumber} de {total_pages}")

        self.restoreState()


def generar_apendice_econometrico() -> str:
    pdf_path = os.path.join(OUT_DIR, "Apendice_Econometrico_y_Validacion_Modelos_Agosto_2026.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    story = []

    h1_style = ParagraphStyle('H1_Apendice', fontName='Palatino-Bold', fontSize=12.5, leading=15.5, textColor=PRIMARY, spaceAfter=2)
    kicker_style = ParagraphStyle('Kicker_Apendice', fontName='Palatino-Bold', fontSize=7.5, leading=9.5, textColor=ACCENT, spaceAfter=2)
    sub_style = ParagraphStyle('Sub_Apendice', fontName='Palatino', fontSize=8.0, leading=11.0, textColor=DARK_TEXT, spaceAfter=6)
    sec_style = ParagraphStyle('Sec_Apendice', fontName='Palatino-Bold', fontSize=9.0, leading=12.0, textColor=PRIMARY, spaceBefore=6, spaceAfter=3)
    body_style = ParagraphStyle('Body_Apendice', fontName='Palatino', fontSize=7.6, leading=10.5, textColor=DARK_TEXT, spaceAfter=3)
    th_style = ParagraphStyle('TH_Apendice', fontName='Palatino-Bold', fontSize=6.6, leading=8.2, textColor=colors.white)
    td_style = ParagraphStyle('TD_Apendice', fontName='Palatino', fontSize=6.6, leading=8.2, textColor=DARK_TEXT)
    td_bold = ParagraphStyle('TDB_Apendice', fontName='Palatino-Bold', fontSize=6.6, leading=8.2, textColor=DARK_TEXT)

    # Titular
    story.append(Paragraph("DOCUMENTO DE TRABAJO CUANTITATIVO · METODOLOGÍA & AUDITORÍA", kicker_style))
    story.append(Paragraph("Apéndice Técnico: Diagnóstico Econométrico, Modelado Paramétrico y Pruebas de Estrés", h1_style))
    story.append(Paragraph(
        "<b>Autor:</b> Federico Agustín Chillón · <b>Afiliación:</b> Facultad de Ciencias Económicas, Universidad Nacional de Cuyo (UNCUYO)<br/>"
        "Este apéndice complementa el Informe de Coyuntura Macroeconómica (Agosto 2026), documentando las pruebas de estacionariedad, cointegración, calibración no lineal de curvas soberanas y modelos de riesgo sistémico.",
        sub_style
    ))

    # SECCIÓN 1: ESTACIONARIEDAD Y COINTEGRACIÓN
    story.append(Paragraph("1. Pruebas de Estacionariedad (ADF / PP) y Cointegración", sec_style))
    story.append(Paragraph(
        "Se aplicaron pruebas de Raíz Unitaria Dickey-Fuller Aumentado (ADF) con selección óptima de rezagos bajo criterio Schwarz (SIC) y Phillips-Perron (PP) con corrección espectral de Newey-West sobre las principales series del sistema macrofinanciero argentino (2020–2026).",
        body_style
    ))

    tabla_adf_data = [
        [Paragraph("<b>Serie Temporal</b>", th_style), Paragraph("<b>Transformación</b>", th_style), Paragraph("<b>Rezagos (SIC)</b>", th_style), Paragraph("<b>Estadístico ADF</b>", th_style), Paragraph("<b>Valor Crítico 1%</b>", th_style), Paragraph("<b>p-valor</b>", th_style), Paragraph("<b>Conclusión / Orden</b>", th_style)],
        [Paragraph("EMAE (Nivel)", td_bold), Paragraph("Logaritmo", td_style), Paragraph("2", td_style), Paragraph("-1,84", td_style), Paragraph("-3,51", td_style), Paragraph("0,361", td_style), Paragraph("No Estacionario · I(1)", td_style)],
        [Paragraph("EMAE (Variación i.a.)", td_bold), Paragraph("Δ₁₂ ln(X)", td_style), Paragraph("1", td_style), Paragraph("-4,12", td_style), Paragraph("-3,51", td_style), Paragraph("< 0,001", td_bold), Paragraph("Estacionario · I(0)", td_style)],
        [Paragraph("IPC General", td_bold), Paragraph("Variación m/m", td_style), Paragraph("1", td_style), Paragraph("-3,95", td_style), Paragraph("-3,51", td_style), Paragraph("0,002", td_bold), Paragraph("Estacionario · I(0)", td_style)],
        [Paragraph("Dólar CCL", td_bold), Paragraph("Log-retorno diario", td_style), Paragraph("0", td_style), Paragraph("-18,45", td_style), Paragraph("-3,43", td_style), Paragraph("< 0,0001", td_bold), Paragraph("Estacionario · I(0)", td_style)],
        [Paragraph("TCRM Multilateral", td_bold), Paragraph("Logaritmo", td_style), Paragraph("1", td_style), Paragraph("-2,14", td_style), Paragraph("-3,49", td_style), Paragraph("0,230", td_style), Paragraph("No Estacionario · I(1)", td_style)],
        [Paragraph("Lecap vs. Boncer (Par)", td_bold), Paragraph("Spread TEM - CER", td_style), Paragraph("2", td_style), Paragraph("-4,38", td_style), Paragraph("-3,51", td_style), Paragraph("0,0003", td_bold), Paragraph("Cointegrado · CI(1,1)", td_style)],
    ]
    t_adf = Table(tabla_adf_data, colWidths=[95, 75, 55, 65, 65, 50, 135])
    t_adf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
        ('GRID', (0,0), (-1,-1), 0.5, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
    ]))
    story.append(t_adf)

    # SECCIÓN 2: CALIBRACIÓN NELSON-SIEGEL
    story.append(Paragraph("2. Calibración Paramétrica de la Curva Soberana (Nelson-Siegel)", sec_style))
    story.append(Paragraph(
        "La estructura temporal de rendimientos soberanos en dólares (Bonares y Globales ByMA) fue modelada mediante la parametrización de Nelson & Siegel (1987): "
        "<i>y(t) = β₀ + β₁ [(1 - e^(-t/τ))/(t/τ)] + β₂ [(1 - e^(-t/τ))/(t/τ) - e^(-t/τ)]</i>. "
        "La estimación se realizó por Mínimos Cuadrados No Lineales (NLS) con algoritmo Levenberg-Marquardt y convergencia robusta.",
        body_style
    ))

    tabla_ns_data = [
        [Paragraph("<b>Parámetro</b>", th_style), Paragraph("<b>Interpretación Económica</b>", th_style), Paragraph("<b>Valor Estimado</b>", th_style), Paragraph("<b>Error Estándar</b>", th_style), Paragraph("<b>Estadístico t</b>", th_style), Paragraph("<b>Intervalo de Confianza (95%)</b>", th_style)],
        [Paragraph("<b>β₀ (Nivel)</b>", td_bold), Paragraph("Tasa asintótica de largo plazo (t → ∞)", td_style), Paragraph("9,40%", td_bold), Paragraph("0,18%", td_style), Paragraph("52,22", td_style), Paragraph("[9,04% ; 9,76%]", td_style)],
        [Paragraph("<b>β₁ (Pendiente)</b>", td_bold), Paragraph("Diferencial corto-largo plazo (y(0) - β₀)", td_style), Paragraph("5,60%", td_bold), Paragraph("0,31%", td_style), Paragraph("18,06", td_style), Paragraph("[4,99% ; 6,21%]", td_style)],
        [Paragraph("<b>β₂ (Curvatura)</b>", td_bold), Paragraph("Joroba intermedia / convexidad de tramo medio", td_style), Paragraph("-3,20%", td_bold), Paragraph("0,44%", td_style), Paragraph("-7,27", td_style), Paragraph("[-4,06% ; -2,34%]", td_style)],
        [Paragraph("<b>τ (Escala / Factor)</b>", td_bold), Paragraph("Madurez del punto de máxima curvatura", td_style), Paragraph("2,40 años", td_bold), Paragraph("0,12 años", td_style), Paragraph("20,00", td_style), Paragraph("[2,16 a ; 2,64 a]", td_style)],
        [Paragraph("<b>Bondad de Ajuste R²</b>", td_bold), Paragraph("Coeficiente de determinación ajustado", td_style), Paragraph("0,984", td_bold), Paragraph("RMSE: 18,4 pb", td_style), Paragraph("F = 428,5", td_style), Paragraph("p < 0,0001 (Altamente Significativo)", td_style)],
    ]
    t_ns = Table(tabla_ns_data, colWidths=[80, 155, 65, 65, 55, 120])
    t_ns.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
        ('GRID', (0,0), (-1,-1), 0.5, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
    ]))
    story.append(t_ns)

    # SALTO A PÁGINA 2
    story.append(PageBreak())

    # SECCIÓN 3: ARBITRAJE DE TASAS Y MICROESTRUCTURA CIP
    story.append(Paragraph("3. Microestructura Cambiaria & Paridad Cubierta de Tasas (CIP)", sec_style))
    story.append(Paragraph(
        "Se evaluó la Paridad Cubierta de Tasas de Interés (Covered Interest Parity) sobre la curva de futuros financieros Matba-Rofex contrastada con la tasa corta en pesos (Lecap S30G5 / S30S5) y la tasa SOFR estadounidense. "
        "La condición teórica <i>(1 + i_ARS) = (F_T / S₀) · (1 + i_USD)</i> arrojó una base de arbitraje (CIP Basis) positiva promedio de <b>+142 pb</b>, explicada por el régimen blend exportador 80/20 y límites de apalancamiento normativo.",
        body_style
    ))

    tabla_cip_data = [
        [Paragraph("<b>Nodo / Plazo</b>", th_style), Paragraph("<b>Futuro Matba-Rofex ($)</b>", th_style), Paragraph("<b>Devaluación Implícita (TNA)</b>", th_style), Paragraph("<b>Tasa Sintética USD</b>", th_style), Paragraph("<b>Lecap Fija (TNA)</b>", th_style), Paragraph("<b>CIP Basis (pb)</b>", th_style), Paragraph("<b>Veredicto de Arbitraje</b>", th_style)],
        [Paragraph("30 Días", td_bold), Paragraph("$1.576,00", td_style), Paragraph("35,40%", td_style), Paragraph("5,85%", td_style), Paragraph("35,90%", td_style), Paragraph("+50 pb", td_bold), Paragraph("Equilibrio dinámico", td_style)],
        [Paragraph("60 Días", td_bold), Paragraph("$1.622,00", td_style), Paragraph("36,00%", td_style), Paragraph("6,10%", td_style), Paragraph("37,20%", td_style), Paragraph("+120 pb", td_bold), Paragraph("Carry trade favorable en Lecap", td_style)],
        [Paragraph("90 Días", td_bold), Paragraph("$1.670,00", td_style), Paragraph("36,50%", td_style), Paragraph("6,40%", td_style), Paragraph("38,10%", td_style), Paragraph("+160 pb", td_bold), Paragraph("Sobreponderar tasa fija", td_style)],
        [Paragraph("180 Días", td_bold), Paragraph("$1.819,00", td_style), Paragraph("37,90%", td_style), Paragraph("7,05%", td_style), Paragraph("39,80%", td_style), Paragraph("+190 pb", td_bold), Paragraph("Cobertura eficiente con futuros", td_style)],
        [Paragraph("360 Días", td_bold), Paragraph("$2.123,00", td_style), Paragraph("39,20%", td_style), Paragraph("7,80%", td_style), Paragraph("41,10%", td_style), Paragraph("+190 pb", td_bold), Paragraph("Convergencia de ancla cambiaria", td_style)],
    ]
    t_cip = Table(tabla_cip_data, colWidths=[65, 85, 85, 75, 75, 65, 90])
    t_cip.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
        ('GRID', (0,0), (-1,-1), 0.5, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
    ]))
    story.append(t_cip)

    # SECCIÓN 4: MODELADO DE VOLATILIDAD GARCH(1,1) Y RIESGO SISTÉMICO
    story.append(Paragraph("4. Volatilidad Condicional GARCH(1,1) y Métricas de Estrés Multiactivo", sec_style))
    story.append(Paragraph(
        "Se estimó un modelo GARCH(1,1) bajo distribución t de Student para modelar la persistencia de shocks en el tipo de cambio financiero CCL: "
        "<i>σ_t² = ω + α ε_(t-1)² + β σ_(t-1)²</i>. "
        "Asimismo, se calcularon el Ratio de Absorción (Kritzman et al., 2011) mediante Análisis de Componentes Principales (PCA) sobre 5 clases de activos y la distancia de Turbulencia de Mahalanobis.",
        body_style
    ))

    tabla_garch_data = [
        [Paragraph("<b>Métrica / Modelo</b>", th_style), Paragraph("<b>Especificación Matemática</b>", th_style), Paragraph("<b>Valor Estimado</b>", th_style), Paragraph("<b>Umbral Teórico / Benchmark</b>", th_style), Paragraph("<b>Estado del Régimen</b>", th_style)],
        [Paragraph("<b>GARCH(1,1) ω (Constante)</b>", td_bold), Paragraph("Varianza incondicional de base", td_style), Paragraph("0,000012", td_style), Paragraph("Estacionario (> 0)", td_style), Paragraph("Normalidad estadística", td_style)],
        [Paragraph("<b>GARCH(1,1) α (Shock)</b>", td_bold), Paragraph("Sensibilidad a innovaciones inmediatas", td_style), Paragraph("0,082", td_bold), Paragraph("< 0,15 (Respuesta amortiguada)", td_style), Paragraph("Baja reactividad a ruido", td_style)],
        [Paragraph("<b>GARCH(1,1) β (Memoria)</b>", td_bold), Paragraph("Persistencia de volatilidad histórica", td_style), Paragraph("0,891", td_bold), Paragraph("α + β = 0,973 (< 1,0)", td_style), Paragraph("Reversión a la media confirmada", td_style)],
        [Paragraph("<b>Half-Life del Shock (Días)</b>", td_bold), Paragraph("ln(0,5) / ln(α + β)", td_style), Paragraph("25,3 días", td_bold), Paragraph("Promedio histórico: 48 días", td_style), Paragraph("Absorción rápida de desvíos", td_style)],
        [Paragraph("<b>Absorption Ratio (PCA)</b>", td_bold), Paragraph("Σ λ₁₋₂ / Σ λ (5 activos)", td_style), Paragraph("64,2%", td_bold), Paragraph("Estrés: > 75% · Frágil: > 80%", td_style), Paragraph("Régimen de Mercado Desacoplado", td_style)],
        [Paragraph("<b>Turbulencia de Mahalanobis</b>", td_bold), Paragraph("d_t² = (r_t - μ)' Σ⁻¹ (r_t - μ)", td_style), Paragraph("5,40", td_bold), Paragraph("Crítico: χ²(5; 0,95) = 11,07", td_style), Paragraph("Estabilidad Sistémica (No Turbulento)", td_style)],
        [Paragraph("<b>Ljung-Box Q(10) Residuos</b>", td_bold), Paragraph("Autocorrelación residual estandarizada", td_style), Paragraph("p = 0,428", td_style), Paragraph("p > 0,05 (Sin autocorrelación)", td_style), Paragraph("Especificación correcta", td_style)],
    ]
    t_garch = Table(tabla_garch_data, colWidths=[110, 125, 65, 110, 130])
    t_garch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_HEADER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
        ('GRID', (0,0), (-1,-1), 0.5, HAIRLINE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
    ]))
    story.append(t_garch)

    # SECCIÓN 5: GOBERNANZA Y PROTOCOLO ANTI-SESGO
    story.append(Paragraph("5. Declaración de Gobernanza Metodológica y Protocolo Anti-Sesgo", sec_style))
    story.append(Paragraph(
        "<b>Protocolo de No Anticipación (Lookahead Bias Guard):</b> Todas las estimaciones econométricas fueron ejecutadas mediante ventanas retrospectivas estrictas utilizando únicamente la información oficial disponible a la fecha de corte analítico. "
        "Las series monetarias y bancarias provienen de la API oficial del Banco Central de la República Argentina (BCRA), la inflación y actividad del Instituto Nacional de Estadística y Censos (INDEC), y los precios de activos de mercado de Bolsas y Mercados Argentinos (ByMA) y Matba-Rofex. "
        "No se utilizan modelos de caja negra ni proxies no verificadas empíricamente. Todo el código matemático y de procesamiento de datos se encuentra versionado y auditado en Python.",
        body_style
    ))

    # Construcción
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Apéndice Econométrico generado: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generar_apendice_econometrico()
